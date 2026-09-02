"""Descarga la serie trimestral de licencias VUT de Barcelona (Open Data BCN, 2018-T2 -> 2026-T1).

    python pipeline/sources/descargar_serie_vut.py

Salida
    data/raw/vut_trimestres/<AAAA>_<N>T.csv   — un fichero por trimestre, ya normalizado
    data/bronze/serie_vut_trimestral.csv   — stock, altas y bajas por trimestre

Cada fichero trimestral es una **foto del stock activo**, no un acumulado. Comprobado sobre
2018-T2 → 2019-T2: 9.509 expedientes en ambos, 94 bajas y 67 altas, y 9.603 − 94 + 67 = 9.576,
que es exactamente el total del trimestre siguiente. Por eso altas y bajas se pueden separar
cruzando por `N_EXPEDIENT`.

Dos peculiaridades de los ficheros, encontradas al leerlos:

1. **El esquema cambia con los años** — 16 columnas en 2018, 21 en 2026.
   `NUMERO_REGISTRE_GENERALITAT` (el número HUTB) no existe en los antiguos, así que hacia atrás
   solo se puede seguir el rastro por expediente.
2. **Hay cabeceras mal formadas** — la de 2018 declara 16 columnas pero las filas traen 17:
   `LONGITUD_X -LATITUD_Y` es un solo nombre para dos columnas. Y algunos ficheros traen BOM.
   De ahí que se detecte el número real de columnas en vez de fiarse de la cabecera.
"""

from __future__ import annotations

import csv
import io
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
DESTINO = RAIZ / "data" / "raw" / "vut_trimestres"
RUTA_SERIE = RAIZ / "data" / "bronze" / "serie_vut_trimestral.csv"

BASE = ("https://opendata-ajuntament.barcelona.cat/data/dataset/"
        "c748799e-1079-44b1-9e60-88d936a3fe70/resource/{}/download")

# Trimestre → id del recurso en CKAN. Sacados de `opendata_bcn_dataset_metadata.json`.
TRIMESTRES = {
    "2026_1T": "297cf7da-2b43-4c83-91e2-210bfe5c33e9",
    "2025_4T": "b31a81d8-d578-4ec4-8cce-4f3648a92975",
    "2025_3T": "6b4a2c03-f0c4-479c-b1e9-f0457133a4df",
    "2025_2T": "d92e7521-c94c-4f97-8a23-4b8b3c4825ec",
    "2025_1T": "6cd8682e-c59e-4b47-84f6-2cc15d3f4188",
    "2024_4T": "ca7bd0a5-286f-4e68-927b-ffa0c2d41907",
    "2024_3T": "57a71fe6-8201-4d41-bdf4-c6cf42e15894",
    "2024_2T": "73c610f1-4ca3-434f-b743-2efef28466e5",
    "2023_4T": "a3a8a7af-38ea-4bf2-ae1f-77b0d68defea",
    "2023_3T": "cb122e12-6b93-4575-8bd5-a3e860c895fc",
    "2023_2T": "effe4df7-b759-4746-82e9-c64572edb87e",
    "2023_1T": "c7d3f231-a27d-4f9f-adb3-dba9b0b9fbe9",
    "2022_4T": "fcd811e0-d04c-424b-a40c-97093bb33bf0",
    "2022_3T": "25b0e8f6-52e9-4194-964e-5ebe52179a48",
    "2022_2T": "4feb548e-8593-4664-86dc-0751fec3bc8c",
    "2022_1T": "1855ebc0-5e7e-442f-881c-da77f276259d",
    "2021_4T": "0178068f-9f2a-466e-9f3d-8c949425bec8",
    "2021_3T": "653311a1-ef92-4e27-9cad-a37c063d2b1f",
    "2021_2T": "09fb1838-e4ef-4b6a-8fee-b983680a642b",
    "2021_1T": "dff5efc2-4826-4fae-9ab0-b699c155bfbe",
    "2020_4T": "ee93f2db-b095-4349-bc88-088077035ff9",
    "2020_3T": "ec4c4aef-c9c0-44d6-8a66-b4aa862ef830",
    "2020_2T": "e811bd2b-ea35-41a0-846c-2f9519fde0e9",
    "2020_1T": "f0738f31-6c8e-458c-a8aa-74e29663a04d",
    "2019_4T": "cc7b17d6-7c84-4e69-b548-4526edf58c21",
    "2019_3T": "b525b85c-131b-4baf-9dde-8524901fb444",
    "2019_2T": "f0a59afd-fa9e-40c9-a284-9a6063707d70",
    "2019_1T": "05b76a7d-12c5-4d4f-a686-373320aac278",
    "2018_4T": "39291425-68c8-4fbb-a25e-b33429881d40",
    "2018_3T": "36aa786d-3896-4668-b6eb-8f0ff51038ab",
    "2018_2T": "a5149fbb-1937-4e5b-aab8-842b2e5624d3",
}


def decodificar(crudo: bytes) -> str:
    """Decodifica y normaliza los saltos de línea.

    Dos rarezas reales de estos ficheros: unos vienen en UTF-8 con BOM y otros en latin-1 (leer
    los primeros como latin-1 deja un `ï»¿` pegado al nombre de la primera columna), y el de
    2023-T1 separa las filas solo con `\\r`, así que sin normalizar se lee como una única línea
    gigante y la cabecera aparece fundida con el primer registro.
    """
    for codificacion in ("utf-8-sig", "latin-1"):
        try:
            texto = crudo.decode(codificacion)
            break
        except UnicodeDecodeError:
            continue
    return texto.replace("\r\n", "\n").replace("\r", "\n")


def leer_csv_tolerante(texto: str) -> pd.DataFrame:
    """Lee un CSV cuya cabecera puede declarar menos columnas de las que traen las filas."""
    cabecera = next(csv.reader(io.StringIO(texto)))
    cabecera = [c.strip().lstrip("﻿").lstrip("ï»¿") for c in cabecera]
    # Se mira el ancho real de las filas, no el de la cabecera: hay trimestres donde no coinciden.
    anchos = [len(f) for _, f in zip(range(500), csv.reader(io.StringIO(texto))) if f]
    n_real = max(anchos, default=len(cabecera))

    # Caso 1 (2018): `LONGITUD_X -LATITUD_Y` es un solo nombre para dos columnas.
    if len(cabecera) < n_real and "LONGITUD" in cabecera[-1].upper() and "LATITUD" in cabecera[-1].upper():
        cabecera = cabecera[:-1] + ["LONGITUD_X", "LATITUD_Y"]

    # Caso 2 (2020-T3): faltan nombres **en medio** — la cabecera declara 17 columnas y las filas
    # traen 19, sin `NUMERO_REGISTRE_GENERALITAT` ni `NUMERO_PLACES`, que en los datos van justo
    # antes de las coordenadas. Como las dos últimas columnas sí son fiablemente lon/lat, se
    # alinea por ambos extremos y los huecos quedan en el centro con nombre genérico.
    if len(cabecera) < n_real:
        faltan = n_real - len(cabecera)
        cabecera = cabecera[:-2] + [f"COLUMNA_SIN_NOMBRE_{i + 1}" for i in range(faltan)] + cabecera[-2:]

    # Algún trimestre (2020-T3) repite un nombre de columna, y pandas no admite duplicados.
    vistos: dict[str, int] = {}
    unicas = []
    for c in cabecera:
        if c in vistos:
            vistos[c] += 1
            unicas.append(f"{c}_{vistos[c]}")
        else:
            vistos[c] = 0
            unicas.append(c)

    # `on_bad_lines="skip"`: algún trimestre trae filas sueltas con un campo de más (una coma
    # dentro de un nombre de vía sin comillar). Se pierde esa fila, no el trimestre entero.
    return pd.read_csv(io.StringIO(texto), dtype=str, skiprows=1, names=unicas,
                       on_bad_lines="skip", engine="python")


def descargar_trimestre(clave: str, recurso: str) -> pd.DataFrame | None:
    """Descarga y descomprime un trimestre. Devuelve None si la fuente falla."""
    try:
        with urllib.request.urlopen(BASE.format(recurso), timeout=120) as resp:
            crudo = resp.read()
    except Exception as e:
        print(f"  {clave}: FALLO en la descarga ({e})")
        return None

    try:
        with zipfile.ZipFile(io.BytesIO(crudo)) as z:
            nombre = next(n for n in z.namelist() if n.lower().endswith(".csv"))
            texto = decodificar(z.read(nombre))
    except zipfile.BadZipFile:
        texto = decodificar(crudo)  # algunos recursos vienen sin comprimir

    filas_fichero = sum(1 for _ in io.StringIO(texto)) - 1
    d = leer_csv_tolerante(texto)
    perdidas = filas_fichero - len(d)
    if perdidas > filas_fichero * 0.01:
        print(f"  {clave}: AVISO — se descartaron {perdidas:,} de {filas_fichero:,} filas")
    if "N_EXPEDIENT" not in d.columns:
        print(f"  {clave}: sin columna N_EXPEDIENT, se descarta")
        return None

    DESTINO.mkdir(parents=True, exist_ok=True)
    d.to_csv(DESTINO / f"{clave}.csv", index=False, encoding="utf-8")
    print(f"  {clave}: {len(d):,} licencias  ({len(d.columns)} columnas)")
    return d


def construir_serie(trimestres: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Stock por trimestre, y altas/bajas frente al trimestre anterior."""
    orden = sorted(trimestres)  # las claves AAAA_NT ordenan bien alfabéticamente
    filas, previo = [], None
    for clave in orden:
        d = trimestres[clave]
        expedientes = set(d["N_EXPEDIENT"].dropna())
        fila = {
            "trimestre": clave,
            "anyo": int(clave[:4]),
            "stock": len(expedientes),
            "altas": len(expedientes - previo) if previo is not None else None,
            "bajas": len(previo - expedientes) if previo is not None else None,
        }
        if previo is not None:
            fila["variacion_neta"] = fila["altas"] - fila["bajas"]
        filas.append(fila)
        previo = expedientes
    return pd.DataFrame(filas)


def main() -> None:
    print(f"Descargando {len(TRIMESTRES)} trimestres de licencias VUT\n")
    datos = {}
    for clave, recurso in sorted(TRIMESTRES.items()):
        d = descargar_trimestre(clave, recurso)
        if d is not None:
            datos[clave] = d

    if not datos:
        raise SystemExit("No se descargó ningún trimestre.")

    serie = construir_serie(datos)
    RUTA_SERIE.parent.mkdir(parents=True, exist_ok=True)
    serie.to_csv(RUTA_SERIE, index=False, encoding="utf-8")

    print(f"\n{'—' * 56}\nSerie de {len(serie)} trimestres:\n")
    print(serie.to_string(index=False))
    primero, ultimo = serie.iloc[0], serie.iloc[-1]
    print(f"\n{primero['trimestre']} -> {ultimo['trimestre']}: "
          f"{primero['stock']:,} -> {ultimo['stock']:,} licencias "
          f"({ultimo['stock'] - primero['stock']:+,})")
    print(f"Altas acumuladas: {serie['altas'].sum():,.0f} | "
          f"bajas acumuladas: {serie['bajas'].sum():,.0f}")
    print(f"\nGuardado en {RUTA_SERIE.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
