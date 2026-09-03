"""Tabla publicable de la oferta anunciada en Airbnb, con precio por plaza y banda economica.

    python pipeline/gold/preparar_airbnb_bcn.py

Entradas
    data/bronze/airbnb_anuncios.csv            — anuncios con capacidad y precio por plaza
    data/gold/airbnb_situacion_licencia.csv    — que declara cada anuncio sobre su licencia
    data/bronze/adr_estacionalidad.csv         — factor de temporada, para el equivalente anual

Salida
    data/gold/airbnb_bcn.csv

Pone la oferta de Airbnb en la **misma escala** que el alojamiento reglado, que es lo que permite
preguntar adonde puede ir quien se quede sin su piso turistico en 2028. Sin esa escala comun la
comparacion no existe: 221 EUR de un piso para cuatro y 174 EUR de una habitacion de hotel no
dicen nada enfrentados.

**El volcado es del 24 de junio y se corrige de temporada.** Junio esta un 19,8% por encima de la
media anual segun la serie del INE. Comparar un Airbnb de junio con un hotel ya llevado a
equivalente anual atribuiria a Airbnb una carestia que es del calendario.

**Y ahi va una suposicion que conviene tener presente:** se aplica a Airbnb la estacionalidad
**hotelera**, porque no existe una serie de estacionalidad para el alquiler turistico. Es
razonable —los dos venden noches a los mismos visitantes en la misma ciudad— pero no esta medido.
Si la estacionalidad de Airbnb fuese mas plana, esta correccion lo abarataria de mas.

**Que no se publica.** Ni el anuncio ni su ubicacion salen a `data/exports`: una VUT es una
vivienda, y las coordenadas de Inside Airbnb ya vienen desplazadas hasta 200 m a proposito. Esta
tabla existe para agregarse por barrio, no para senalar pisos.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from bandas import por_plaza

RAIZ = Path(__file__).resolve().parents[2]
BRONZE = RAIZ / "data" / "bronze"
GOLD = RAIZ / "data" / "gold"
SALIDA = GOLD / "airbnb_bcn.csv"

# Mes del volcado de Inside Airbnb.
MES_VOLCADO = 6

# El decreto define el uso turistico como cesion por un periodo "igual o inferior a 31 dies".
# Igual O INFERIOR: un anuncio cuyo minimo son 31 noches puede alojar una estancia de 31 noches,
# que es uso turistico y necesita licencia. Solo a partir de 32 queda fuera del alcance de la ley.
NOCHES_USO_TURISTICO = 31

PATRON_REGIONAL = re.compile(
    r"Barcelona\s*-\s*Regional registration number\s*(?:<br\s*/?>)*\s*([^<]*)", re.I)

COLUMNAS = ["id", "host_id", "host_perfil", "neighbourhood_group", "neighbourhood", "room_type",
            "property_type", "accommodates", "bedrooms", "minimum_nights", "uso_turistico",
            "borde_31_noches", "licencia_regional", "vivienda_id", "anuncios_de_la_vivienda",
            "es_repeticion", "precio_anuncio", "precio_por_plaza", "precio_plaza_anual",
            "banda_plaza", "factor_temporada", "number_of_reviews_ltm", "availability_365",
            "license", "situacion", "sujeto_a_vut", "sin_licencia", "actividad_reciente"]


def factor_de_junio() -> float:
    """Cuanto pesa el mes del volcado sobre la media del año.

    Se promedian las cuatro categorias oficiales en vez de elegir una: la de "1 y 2 estrellas y
    estrellas de plata" seria la mas parecida al mercado de Airbnb por precio, pero esa semejanza
    es una suposicion sobre la que no hay dato, y el promedio no privilegia ninguna lectura. Las
    cuatro rondan 1,16-1,20 en junio, asi que la eleccion cambia poco.
    """
    est = pd.read_csv(BRONZE / "adr_estacionalidad.csv")
    return float(est.loc[est["mes"] == MES_VOLCADO, "factor"].mean())


def marcar_repeticiones(d: pd.DataFrame) -> pd.DataFrame:
    """Senala los anuncios que son la misma vivienda, sin borrarlos.

    El discriminante es la licencia declarada, no que las filas se parezcan: hay 903 filas
    identicas en host, barrio, tipo, capacidad y precio, y una parte son habitaciones distintas
    del mismo hostel, que son oferta real y no duplicados.

    **Solo se aplica a las HUTB.** Una vivienda de uso turistico es, por definicion, una vivienda:
    dos anuncios con el mismo HUTB son el mismo piso —530 licencias aparecen repetidas, con 1.028
    filas de mas—. En cambio un hotel (`HB`) promedia 3,66 anuncios por licencia y un albergue
    (`AJ`) 4,72, porque publican sus habitaciones por separado y cada una es oferta distinta.

    No se eliminan filas: `es_repeticion` marca las que no son la primera de su vivienda, y quien
    cuente oferta filtra por esa columna. Borrarlas perderia el numero de veces que un mismo piso
    esta anunciado, que es informacion sobre como opera ese titular.
    """
    d = d.copy()
    d["licencia_regional"] = d["license"].map(
        lambda t: (lambda m: m.group(1).strip() if m else None)(PATRON_REGIONAL.search(str(t))))

    es_hutb = d["licencia_regional"].str.match(r"^HUTB", na=False)
    d["vivienda_id"] = np.where(es_hutb, d["licencia_regional"], "anuncio:" + d["id"].astype(str))
    d["anuncios_de_la_vivienda"] = d.groupby("vivienda_id")["id"].transform("size")
    # La primera por id: cualquier criterio estable sirve, lo que importa es que sea reproducible.
    d["es_repeticion"] = d.sort_values("id").duplicated("vivienda_id") & es_hutb
    d["es_repeticion"] = d["es_repeticion"].reindex(d.index).fillna(False)
    return d


def perfil_del_anfitrion(d: pd.DataFrame) -> pd.Series:
    """Si un anfitrion acredita licencia en unos anuncios y en otros no.

    Importa porque cambia como se lee un anuncio sin licencia. Quien no acredita ninguna puede ser
    un particular que desconoce el tramite; quien acredita en trescientos anuncios y no en ciento
    diecisiete sabe perfectamente cual es el tramite. Son 163 anfitriones que concentran el 25% de
    la oferta turistica, con una mediana de siete anuncios cada uno.
    """
    turistico = d[d["uso_turistico"]]
    con = turistico["situacion"].eq("licencia_verificada").groupby(turistico["host_id"]).sum()
    sin = (turistico["situacion"]
           .isin(["sin_declarar", "licencia_no_encontrada", "hutb_no_verificable"])
           .groupby(turistico["host_id"]).sum())
    perfil = pd.Series("sin_anuncios_turisticos", index=con.index, dtype=object)
    perfil[(con > 0) & (sin == 0)] = "solo_con_licencia"
    perfil[(con == 0) & (sin > 0)] = "solo_sin_licencia"
    perfil[(con > 0) & (sin > 0)] = "mixto"
    return d["host_id"].map(perfil)


def main() -> None:
    a = pd.read_csv(BRONZE / "airbnb_anuncios.csv", low_memory=False)
    print(f"Anuncios: {len(a):,}")

    licencias = pd.read_csv(GOLD / "airbnb_situacion_licencia.csv", low_memory=False)
    a = a.merge(
        licencias[["id", "situacion", "sujeto_a_vut", "sin_licencia", "actividad_reciente"]],
        on="id", how="left")

    a["uso_turistico"] = a["minimum_nights"] <= NOCHES_USO_TURISTICO
    a["borde_31_noches"] = a["minimum_nights"] == NOCHES_USO_TURISTICO
    a = marcar_repeticiones(a)
    a["host_perfil"] = perfil_del_anfitrion(a)

    factor = factor_de_junio()
    a["factor_temporada"] = round(factor, 3)
    a["precio_plaza_anual"] = (a["precio_por_plaza"] / factor).round(2)
    a["banda_plaza"] = por_plaza(a["precio_plaza_anual"])

    a[COLUMNAS].to_csv(SALIDA, index=False, encoding="utf-8")

    con = a["banda_plaza"].notna()
    print(f"  factor de temporada (junio): {factor:.3f}")
    print(f"  uso turistico (<=31 noches): {int(a['uso_turistico'].sum()):,} "
          f"| fuera de la ley (>=32): {int((~a['uso_turistico']).sum()):,}")
    print(f"  en el borde de 31 noches   : {int(a['borde_31_noches'].sum()):,}")
    print(f"  repeticiones de una HUTB   : {int(a['es_repeticion'].sum()):,} "
          f"-> viviendas distintas {a.loc[~a['es_repeticion']].shape[0]:,}")
    print(f"  perfil del anfitrion       : {a['host_perfil'].value_counts().to_dict()}")
    print(f"  con precio por plaza       : {int(con.sum()):,} ({con.mean():.1%})")
    print(f"\n  reparto por banda: {a['banda_plaza'].value_counts().reindex(['€','€€','€€€','€€€€']).to_dict()}")

    print("\n  mediana de precio por plaza y noche, equivalente anual:")
    print(a[con].groupby("room_type")["precio_plaza_anual"].agg(["size", "median"]).round(1)
          .sort_values("size", ascending=False).to_string())

    print("\n  por situacion de licencia:")
    print(a[con].groupby("situacion")["precio_plaza_anual"]
          .agg(["size", "median"]).round(1).sort_values("size", ascending=False).to_string())

    print(f"\nGuardado en {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
