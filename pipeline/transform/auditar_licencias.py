"""Clasifica la oferta anunciada en Airbnb según su situación de licencia.

Implementa el cruce de [M-08] en `docs/prd.md`: contrastar lo anunciado contra el registro
oficial de licencias VUT. El análisis exploratorio que justifica cada decisión de este script
está en `pipeline/notebooks/03_auditoria_licencias.ipynb`.

Entradas
    data/raw/airbnb/insideairbnb_barcelona_<fecha>_listings.csv
    data/processed/vut_unificados.csv   (generado por unificar_registros.py)

Salida
    data/processed/airbnb_situacion_licencia.csv

Tres cautelas que condicionan todo el diseño:

1. **El campo `license` contiene dos números distintos.** El nacional incrusta el HUTB y le
   añade dígitos de control: `ESFCTU...HUTB-002062349` frente al real `HUTB-002062`. Buscar
   `HUTB-\\d+` en todo el campo captura el equivocado y multiplica por dos las licencias dadas
   por inválidas (36,2% en vez de 14,8%). Solo se lee la sección regional de Barcelona.

2. **No toda la oferta necesita licencia VUT.** Una habitación en vivienda habitual o un
   alquiler de 32+ noches se rigen por otro régimen. Contar sus anuncios como irregulares sería
   sencillamente incorrecto, así que `sujeto_a_vut` acota el universo antes de contar nada.

3. **Declarar no es tener, y no declarar no es carecer.** El campo lo rellena el anfitrión. El
   resultado se etiqueta como *candidato*, nunca como infracción (ver WON'T en `docs/prd.md`).
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
DIR_AIRBNB = RAIZ / "data" / "raw" / "airbnb"
RUTA_VUT = RAIZ / "data" / "processed" / "vut_unificados.csv"
RUTA_SALIDA = RAIZ / "data" / "processed" / "airbnb_situacion_licencia.csv"

# Solo la sección regional lleva el número bueno (ver cautela 1 en el docstring).
PATRON_REGIONAL = re.compile(
    r"Barcelona\s*-\s*Regional registration number\s*(?:<br\s*/?>)*\s*([^<]*)", re.I
)
PATRON_HUTB = re.compile(r"^HUTB[-\s]*(\d+)", re.I)
PATRON_EXENCION = re.compile(r"^Exempt\s*-?\s*", re.I)

# Umbral legal del régimen VUT: a partir de 32 noches es alquiler de temporada.
MAX_NOCHES_VUT = 31


def leer_licencia(texto: object) -> tuple[int | None, str | None]:
    """Extrae `(numero_hutb, motivo_exencion)` del campo `license` de Inside Airbnb.

    Devuelve `(None, None)` cuando el anuncio no declara nada en la sección regional.
    """
    if not isinstance(texto, str):
        return None, None
    encontrado = PATRON_REGIONAL.search(texto)
    if not encontrado:
        return None, None

    valor = encontrado.group(1).strip()
    if PATRON_EXENCION.match(valor):
        return None, PATRON_EXENCION.sub("", valor).strip().lower() or "sin especificar"

    hutb = PATRON_HUTB.match(valor)
    return (int(hutb.group(1)) if hutb else None), None


def cargar_licencias_oficiales() -> tuple[set[str], int]:
    """Devuelve el conjunto de licencias VUT vigentes y el número más alto emitido.

    El máximo sirve para separar un posible error de tecleo de un número que la Generalitat
    todavía no ha llegado a emitir: por encima de él, la licencia no puede existir.
    """
    vut = pd.read_csv(RUTA_VUT, dtype=str)
    validas = vut.loc[vut["licencia_id"].str.match(r"^HUTB-\d+$", na=False), "licencia_id"]
    if validas.empty:
        raise ValueError(f"No se encontraron licencias HUTB en {RUTA_VUT}")
    numeros = validas.str.split("-").str[1].astype(int)
    return set(validas), int(numeros.max())


def localizar_airbnb() -> Path:
    """Toma el snapshot de Inside Airbnb más reciente disponible en `data/raw/airbnb/`."""
    candidatos = sorted(DIR_AIRBNB.glob("insideairbnb_barcelona_*_listings.csv"))
    if not candidatos:
        raise FileNotFoundError(
            f"No hay snapshot de Inside Airbnb en {DIR_AIRBNB}. "
            "Ejecuta primero: python pipeline/sources/descargar_fuentes.py airbnb"
        )
    return candidatos[-1]


def clasificar(anuncios: pd.DataFrame, oficiales: set[str], num_maximo: int) -> pd.DataFrame:
    """Añade las columnas de situación de licencia al conjunto de anuncios."""
    leido = anuncios["license"].apply(leer_licencia)
    anuncios["hutb_num"] = [r[0] for r in leido]
    anuncios["exencion"] = [r[1] for r in leido]
    anuncios["hutb"] = anuncios["hutb_num"].apply(
        lambda n: f"HUTB-{int(n):06d}" if pd.notna(n) else None
    )
    anuncios["licencia_existe"] = anuncios["hutb"].isin(oficiales)

    # Un número por encima del último emitido no puede corresponder a ninguna licencia real,
    # así que no se explica como error de transcripción.
    anuncios["fuera_de_rango"] = (
        anuncios["hutb_num"].notna()
        & ~anuncios["licencia_existe"]
        & (anuncios["hutb_num"] > num_maximo)
    )

    def situacion(fila: pd.Series) -> str:
        if pd.notna(fila["hutb"]):
            return "licencia_verificada" if fila["licencia_existe"] else "licencia_no_encontrada"
        if pd.notna(fila["exencion"]):
            return "exencion_declarada"
        return "sin_declarar"

    anuncios["situacion"] = anuncios.apply(situacion, axis=1)

    # Acota el universo: solo la vivienda completa de estancia corta necesita licencia VUT.
    anuncios["sujeto_a_vut"] = (anuncios["room_type"] == "Entire home/apt") & (
        anuncios["minimum_nights"] <= MAX_NOCHES_VUT
    )

    # La conclusión operativa. "Candidato", nunca "infractor": el campo lo rellena el anfitrión
    # y una licencia real mal escrita cae exactamente aquí.
    anuncios["candidato_sin_licencia"] = anuncios["sujeto_a_vut"] & anuncios["situacion"].isin(
        ["sin_declarar", "licencia_no_encontrada"]
    )
    return anuncios


def informe(anuncios: pd.DataFrame, num_maximo: int) -> None:
    """Resumen por pantalla, con las cifras que van al changelog."""
    sujetos = anuncios[anuncios["sujeto_a_vut"]]
    candidatos = anuncios[anuncios["candidato_sin_licencia"]]

    print(f"\nAnuncios analizados        : {len(anuncios):,}")
    print(f"Sujetos al régimen VUT     : {len(sujetos):,}")
    print("\nSituación de los sujetos a VUT:")
    for etiqueta, n in sujetos["situacion"].value_counts().items():
        print(f"  {etiqueta:24s}: {n:6,}  ({n / len(sujetos):5.1%})")

    print(f"\nCandidatos sin licencia    : {len(candidatos):,} ({len(candidatos) / len(sujetos):.1%} de los sujetos)")
    print(f"  con número imposible     : {int(candidatos['fuera_de_rango'].sum()):,}  (por encima de HUTB-{num_maximo})")
    print(
        f"\nNúmeros imposibles en todo el conjunto: {int(anuncios['fuera_de_rango'].sum()):,} "
        "(incluye anuncios no sujetos al régimen VUT)"
    )

    por_host = candidatos.groupby("host_id").size()
    if not por_host.empty:
        grandes = por_host[por_host >= 5]
        print(f"\nAnfitriones con candidatos : {len(por_host):,}")
        print(f"  con 5 o más anuncios     : {len(grandes):,}  → {grandes.sum():,} anuncios")


def main() -> None:
    ruta_airbnb = localizar_airbnb()
    print(f"Snapshot   : {ruta_airbnb.name}")
    anuncios = pd.read_csv(ruta_airbnb)

    oficiales, num_maximo = cargar_licencias_oficiales()
    print(f"Licencias oficiales VUT: {len(oficiales):,} (máximo emitido: HUTB-{num_maximo})")

    anuncios = clasificar(anuncios, oficiales, num_maximo)
    informe(anuncios, num_maximo)

    columnas = [
        "id", "name", "host_id", "host_name", "calculated_host_listings_count",
        "neighbourhood_group", "neighbourhood", "latitude", "longitude",
        "room_type", "minimum_nights", "price", "availability_365", "number_of_reviews",
        "license", "hutb", "exencion", "licencia_existe", "fuera_de_rango",
        "situacion", "sujeto_a_vut", "candidato_sin_licencia",
    ]
    salida = anuncios[[c for c in columnas if c in anuncios]]

    # Las coordenadas vienen ya ofuscadas ~200 m por Inside Airbnb, y aquí se conservan tal
    # cual: el detalle se queda en `data/processed/`. La agregación por barrio o distrito para
    # lo que se publica es responsabilidad de `pipeline/export.py` (ver docs/data-model.md).
    RUTA_SALIDA.parent.mkdir(parents=True, exist_ok=True)
    salida.to_csv(RUTA_SALIDA, index=False, encoding="utf-8")
    print(f"\nGuardado en {RUTA_SALIDA.relative_to(RAIZ)}  ({len(salida):,} filas)")


if __name__ == "__main__":
    main()
