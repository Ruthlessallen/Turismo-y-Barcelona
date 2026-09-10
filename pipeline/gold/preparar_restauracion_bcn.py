"""Restauracion de Barcelona ciudad a partir del censo comercial municipal.

Cada decision de este script se tomo mirando el dato en
`pipeline/notebooks/revisar_restauracion.ipynb`, que conserva las comprobaciones. Aqui va solo lo
que hay que ejecutar.

**Por que el censo municipal y no OSM.** OSM cuenta 7.430 locales de restauracion en la ciudad y el
censo 10.100: un 26% menos. La cifra del censo es la que declara el Ajuntament --"mas de diez mil"
en su guia de 2025-- y continua su serie historica (9.359 en 2017); la de OSM no es compatible con
ninguna cifra oficial. Ademas el fichero de OSM no trae fecha de cada elemento, asi que su
antiguedad es desigual y no medible. OSM se sigue usando **fuera de la ciudad**, donde no hay
alternativa.

**El censo es de 2024 y no hay nada mas nuevo.** La serie publicada es 2014, 2016, 2019, 2022 y
2024. Pero no es una foto de un dia: `fecha_revision` dice cuando se visito cada local, y el
trabajo de campo va de 2023 a 2024 --el 57% se visito en 2023--.

Entrada
    data/raw/restauracion_hoteles_provincia/bcn_cens_comercial_restauracion_2024.csv

Salida
    data/gold/restauracion_bcn.csv
"""

from __future__ import annotations

import unicodedata
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
ENTRADA = (RAIZ / "data" / "raw" / "restauracion_hoteles_provincia" /
           "bcn_cens_comercial_restauracion_2024.csv")
SALIDA = RAIZ / "data" / "gold" / "restauracion_bcn.csv"

# Restauracion de comidas y cenas. Quedan fuera, por decision y no por no ser restauracion, el
# ocio nocturno (387 locales: se bebe, no se cena) y las xocolateries/geladeries (148: no cubren
# una comida). Reincorporarlas es anadir una linea aqui.
#
# Las categorias NO se escriben literales: el censo las escribe con espacios dobles y acentos
# --`Bars   / CIBERCAFÉ`-- y una comparacion literal falla en silencio. Ya paso dos veces, dejando
# fuera los 4.273 bares sin que nada se quejara.
TIPOS = {"restaurants": "restaurante",
         "cibercafe": "bar",
         "take away": "comida_rapida"}

COLUMNAS = {
    "ID_Global": "local_id",
    "Nom_Local": "nombre",
    "tipo_local": "tipo_local",
    "Nom_Districte": "distrito",
    "Nom_Barri": "barrio",
    "Codi_Barri": "codigo_barrio",
    "Nom_Via": "calle",
    "Num_Policia_Inicial": "numero",
    "Direccio_Unica": "direccion",
    "Latitud": "latitud",
    "Longitud": "longitud",
    "Data_Revisio": "fecha_revision",
}

# El censo escribe 'SN' --sense nom-- donde no hay nombre. Como texto, haria que 56 locales se
# llamaran igual y cualquier recuento por nombre los agrupara como si fueran uno.
SIN_NOMBRE = "SN"


def sin_acentos(texto: object) -> str:
    limpio = unicodedata.normalize("NFKD", str(texto).lower())
    return "".join(c for c in limpio if not unicodedata.combining(c))


def buscar_categoria(censo: pd.DataFrame, clave: str) -> str:
    """Categoria del censo que contiene `clave`. Falla si no hay exactamente una.

    Es lo que impide que un cambio de acentuacion en el fichero vacie una categoria entera sin
    que el script se entere.
    """
    encontradas = [a for a in censo["Nom_Activitat"].unique() if clave in sin_acentos(a)]
    if len(encontradas) != 1:
        raise ValueError(f"'{clave}' encuentra {len(encontradas)} categorias: {encontradas}")
    return encontradas[0]


def seleccionar(censo: pd.DataFrame) -> pd.DataFrame:
    incluidos = {buscar_categoria(censo, clave): etiqueta for clave, etiqueta in TIPOS.items()}
    d = censo[censo["Nom_Activitat"].isin(incluidos)].copy()
    d["tipo_local"] = d["Nom_Activitat"].map(incluidos)
    return d


def normalizar(d: pd.DataFrame) -> pd.DataFrame:
    """Recorta al esquema, tipa y marca lo que el censo no llego a identificar."""
    r = d[list(COLUMNAS)].rename(columns=COLUMNAS)

    # 190 identificadores vienen entre llaves --{uuid}--, de dos dias de campo concretos y casi
    # todos en centros comerciales: un lote que entro por otra via. Y uno tiene un caracter de
    # mas. Sin normalizar, dos filas del mismo local pasan por distintas.
    r["local_id"] = r["local_id"].astype(str).str.strip("{}").str.lower().str[:36]

    r.loc[r["nombre"].astype(str).str.strip().str.upper().eq(SIN_NOMBRE), "nombre"] = pd.NA
    r["fecha_revision"] = pd.to_datetime(r["fecha_revision"], errors="coerce")

    # `Direccio_Unica` acaba en `LOC <numero>` cuando se sabe que local es, y en `LOC NA` cuando
    # solo se sabe que en ese portal hay un establecimiento. Son mercados y centros comerciales:
    # Els Encants tiene 10 asi, el Mercat de la Barceloneta 2. NO son duplicados, y borrarlos por
    # repetir direccion se cargaria 197 locales que existen.
    r["local_identificado"] = ~r["direccion"].astype(str).str.endswith("LOC NA")
    return r


def quitar_duplicados(r: pd.DataFrame) -> pd.DataFrame:
    """Dos visitas al mismo local: se conserva la mas reciente, que describe su estado actual.

    Solo se comparan los locales identificados. Entre los `LOC NA` la coincidencia de nombre y
    direccion es lo normal --son varios establecimientos del mismo portal, casi todos sin nombre--
    y no significa repeticion.
    """
    clave = ["nombre", "direccion", "tipo_local"]
    identificados = r[r["local_identificado"]]
    limpios = identificados.sort_values("fecha_revision").drop_duplicates(clave, keep="last")
    return pd.concat([limpios, r[~r["local_identificado"]]]).sort_index()


def main() -> None:
    censo = pd.read_csv(ENTRADA, low_memory=False)
    print(f"Censo comercial: {len(censo):,} locales")

    d = seleccionar(censo)
    print(f"Restauracion de comidas y cenas: {len(d):,}")

    r = normalizar(d)
    antes = len(r)
    r = quitar_duplicados(r)
    print(f"Duplicados retirados: {antes - len(r)}")

    if r["local_id"].duplicated().any():
        raise ValueError("quedan local_id repetidos")

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    r.to_csv(SALIDA, index=False, encoding="utf-8")

    print()
    print(r["tipo_local"].value_counts().to_string())
    print(f"{'TOTAL':<14} {len(r):>5,}")
    print()
    print(f"  barrios              : {r['barrio'].nunique()} de 73")
    print(f"  sin nombre           : {int(r['nombre'].isna().sum())}")
    print(f"  sin identificar      : {int((~r['local_identificado']).sum())}")
    print(f"  revisados en 2024    : {int(r['fecha_revision'].dt.year.eq(2024).sum()):,} "
          f"({r['fecha_revision'].dt.year.eq(2024).mean():.0%})")
    print()
    print(f"Guardado en {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
