"""Restauracion de Barcelona ciudad, a partir del censo municipal y las terrazas.

**Por que el censo y no OSM.** OSM cuenta 7.430 locales de restauracion en la ciudad y el censo
municipal 10.100: OSM se deja un 26%. Se detecto al cruzar las terrazas con OSM, que daba un 93%
de locales con terraza y doce barrios por encima del 100% --Sant Andreu 242%--. Un porcentaje
imposible no acusa al numerador, acusa al denominador. La cifra del censo es ademas la que declara
el propio Ajuntament ("mas de diez mil" en su guia de 2025), y la que continua su serie historica
(9.359 en 2017). Ver `docs/observaciones-datos.md`.

OSM se sigue usando **fuera de la ciudad**, donde no hay alternativa.

Entradas
    data/raw/restauracion_hoteles_provincia/bcn_cens_comercial_restauracion_2024.csv
    data/raw/restauracion_hoteles_provincia/bcn_terrasses_restauracio_2026.csv

Salida
    data/gold/restauracion_bcn.csv

**El campo `terraza_acreditada` es asimetrico, y por eso se llama asi.** `True` significa que hay
una licencia de terraza en esa direccion o a menos de 10 m; `False` significa que no se ha
encontrado, no que no exista. El cruce recupera un 54% de los locales cuando la proporcion real
ronda el 63%, asi que alrededor de uno de cada siete `False` es en realidad una terraza que el
cruce no ve. La razon es que la coordenada de la terraza esta en la acera, no en la puerta del
local, y que el censo es de 2024 frente a unas terrazas de 2026.

Es la misma convencion que en las licencias de Airbnb: se nombra lo que se ha podido acreditar,
nunca lo que se afirma que no existe.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

RAIZ = Path(__file__).resolve().parents[2]
RAW = RAIZ / "data" / "raw" / "restauracion_hoteles_provincia"
RUTA_CENSO = RAW / "bcn_cens_comercial_restauracion_2024.csv"
RUTA_TERRAZAS = RAW / "bcn_terrasses_restauracio_2026.csv"
SALIDA = RAIZ / "data" / "gold" / "restauracion_bcn.csv"

# A 41,39 N un grado de longitud mide 83,4 km y uno de latitud 110,6: proyectar con un solo
# factor inflaria el eje este-oeste, que es justo el eje en que se estira la ciudad.
LAT0 = 41.39
RADIO_M = 10.0
# Una direccion con mas de tres locales de restauracion no identifica a ninguno: son centros
# comerciales y galerias. Sin este tope, `potosi 2` marcaba 51 locales con una sola licencia.
MAX_LOCALES_POR_DIRECCION = 3

PREFIJOS_VIA = (r"^(c|carrer|av|avinguda|avgda|pg|passeig|pl|placa|rbla|rambla|ctra|via|gv|trav|"
                r"travessera|ronda|bxda|baixada|ptge|passatge)\b\.?\s*")

# Se clasifica por palabra clave y no por igualdad exacta: los nombres de actividad del censo
# traen espacios dobles y acentos que no sobreviven a una comparacion literal --`Bars   /
# CIBERCAFÉ` mandaba los 4.273 bares al cajon de `otros` sin que nada lo delatara--. El orden
# importa: un bar musical es ocio nocturno antes que bar.
TIPOS = (
    ("ocio_nocturno", ("discoteca", "musical", "actuacio", "pub")),
    ("degustacion", ("xocolater", "gelater", "degustacio")),
    ("comida_rapida", ("take away", "rapid")),
    ("restaurante", ("restaurant",)),
    ("bar", ("bar", "cibercafe", "cafe")),
)


def clasificar_tipo(actividad: str) -> str:
    texto = unicodedata.normalize("NFKD", str(actividad).lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    for etiqueta, claves in TIPOS:
        if any(k in texto for k in claves):
            return etiqueta
    return "otros"


def normalizar_via(texto: str) -> str:
    """Deja el nombre de calle comparable entre los dos ficheros municipales."""
    if not isinstance(texto, str):
        return ""
    limpio = unicodedata.normalize("NFKD", texto.lower())
    limpio = "".join(c for c in limpio if not unicodedata.combining(c))
    limpio = re.sub(PREFIJOS_VIA, "", limpio)
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", limpio)).strip()


def partir_emplazamiento(texto: str) -> tuple[str, float]:
    """`AV. GAUDI, 46` -> (`gaudi`, 46). Los tramos `419-425` se quedan con el inicial."""
    coincide = re.match(r"^(.*?),\s*(\d+)", str(texto))
    if coincide:
        return normalizar_via(coincide.group(1)), float(coincide.group(2))
    return normalizar_via(texto), np.nan


def proyectar(lat, lon) -> np.ndarray:
    return np.c_[np.asarray(lon, dtype=float) * 111320 * np.cos(np.radians(LAT0)),
                 np.asarray(lat, dtype=float) * 110570]


def cargar_censo() -> pd.DataFrame:
    d = pd.read_csv(RUTA_CENSO, low_memory=False)
    # El censo agrupa restauracion y alojamiento bajo el mismo grupo de actividad. Los 764 de
    # alojamiento cuentan en el otro lado del analisis, con los hoteles.
    d = d[~d["Nom_Activitat"].str.contains("allotjament", case=False, na=False)].copy()
    d["tipo_local"] = d["Nom_Activitat"].map(clasificar_tipo)
    d["via"] = d["Nom_Via"].map(normalizar_via)
    d["num"] = pd.to_numeric(d["Num_Policia_Inicial"], errors="coerce")
    return d.reset_index(drop=True)


def cargar_terrazas() -> pd.DataFrame:
    t = pd.read_csv(RUTA_TERRAZAS, low_memory=False)
    t[["via", "num"]] = pd.DataFrame([partir_emplazamiento(x) for x in t["EMPLACAMENT"]],
                                     index=t.index)
    return t


def marcar_terrazas(censo: pd.DataFrame, terrazas: pd.DataFrame) -> pd.DataFrame:
    """Dos vias independientes, unidas: misma direccion, o una terraza a menos de 10 m.

    Coinciden en el 83% de los casos. Se suman porque fallan por motivos distintos --el callejero
    por nombres de via que no casan, la distancia por terrazas plantadas lejos del portal-- y
    juntas recuperan 9 puntos mas que cualquiera de las dos por separado.
    """
    d = censo.copy()
    # Un local dentro de un centro comercial, mercado o galeria no tiene terraza en via publica:
    # el portal puede tener licencia, pero no es suya.
    interior = (d["SN_CComercial"].eq("Si") | d["SN_Mercat"].eq("Si") | d["SN_Galeria"].eq("Si"))
    locales_en_direccion = d.groupby(["via", "num"])["ID_Global"].transform("size")

    direcciones = set(zip(terrazas["via"], terrazas["num"]))
    por_direccion = pd.Series([(v, n) in direcciones for v, n in zip(d["via"], d["num"])],
                              index=d.index)
    por_direccion &= locales_en_direccion.le(MAX_LOCALES_POR_DIRECCION)

    arbol = cKDTree(proyectar(terrazas["LATITUD"], terrazas["LONGITUD"]))
    cerca = arbol.query_ball_point(proyectar(d["Latitud"], d["Longitud"]), r=RADIO_M)
    por_distancia = pd.Series([len(v) > 0 for v in cerca], index=d.index)

    d["terraza_acreditada"] = (por_direccion | por_distancia) & ~interior
    d["terraza_por_direccion"] = por_direccion & ~interior
    d["terraza_por_distancia"] = por_distancia & ~interior
    d["en_interior"] = interior
    return d


def main() -> None:
    censo = cargar_censo()
    terrazas = cargar_terrazas()
    print(f"Censo de restauracion (sin alojamiento): {len(censo):,}")
    print(f"Licencias de terraza                   : {len(terrazas):,}")

    d = marcar_terrazas(censo, terrazas)

    columnas = {
        "ID_Global": "local_id", "Nom_Local": "nombre_comercial", "tipo_local": "tipo_local",
        "Nom_Activitat": "actividad_censo", "Nom_Barri": "barrio", "Nom_Districte": "distrito",
        "Codi_Barri": "codigo_barrio", "Nom_Via": "calle", "Num_Policia_Inicial": "numero",
        "Latitud": "latitud", "Longitud": "longitud",
        "SN_Oci_Nocturn": "ocio_nocturno", "SN_Obert24h": "abierto_24h",
        "SN_Servei_Degustacio": "servicio_degustacion", "SN_Mercat": "en_mercado",
        "SN_CComercial": "en_centro_comercial", "SN_Eix": "en_eje_comercial",
        "Nom_Eix": "nombre_eje", "Nom_Mercat": "nombre_mercado",
    }
    salida = d[list(columnas) + ["terraza_acreditada", "terraza_por_direccion",
                                 "terraza_por_distancia"]].rename(columns=columnas)
    for c in ("ocio_nocturno", "abierto_24h", "servicio_degustacion", "en_mercado",
              "en_centro_comercial", "en_eje_comercial"):
        salida[c] = salida[c].eq("Si")

    salida.to_csv(SALIDA, index=False, encoding="utf-8")

    esperado = (len(terrazas) - 620) / len(censo)   # 620 emplazamientos con mas de una licencia
    marcados = salida["terraza_acreditada"].mean()
    print()
    print(f"terraza_acreditada: {int(salida['terraza_acreditada'].sum()):,} "
          f"({marcados:.0%}); proporcion real esperada ~{esperado:.0%}")
    print(f"  -> alrededor de 1 de cada {round(1 / max(esperado - marcados, 1e-9) * esperado)} "
          f"`False` es una terraza que el cruce no ve")
    print()
    print("Por tipo de local:")
    print(salida.groupby("tipo_local")
          .agg(locales=("local_id", "size"), con_terraza=("terraza_acreditada", "sum"))
          .assign(pct=lambda x: (x.con_terraza / x.locales * 100).round(0))
          .sort_values("locales", ascending=False).to_string())
    print()
    print(f"Guardado en {SALIDA.relative_to(RAIZ)}  ({len(salida):,} locales, "
          f"{salida['barrio'].nunique()} barrios)")


if __name__ == "__main__":
    main()
