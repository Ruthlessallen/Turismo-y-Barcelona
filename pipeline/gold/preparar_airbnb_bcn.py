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

from pathlib import Path

import pandas as pd

from bandas import por_plaza

RAIZ = Path(__file__).resolve().parents[2]
BRONZE = RAIZ / "data" / "bronze"
GOLD = RAIZ / "data" / "gold"
SALIDA = GOLD / "airbnb_bcn.csv"

# Mes del volcado de Inside Airbnb.
MES_VOLCADO = 6

COLUMNAS = ["id", "host_id", "neighbourhood_group", "neighbourhood", "room_type", "property_type",
            "accommodates", "bedrooms", "minimum_nights", "precio_anuncio", "precio_por_plaza",
            "precio_plaza_anual", "banda_plaza", "factor_temporada", "number_of_reviews_ltm",
            "availability_365", "license", "situacion", "sujeto_a_vut", "sin_licencia",
            "actividad_reciente"]


def factor_de_junio() -> float:
    """Cuanto pesa el mes del volcado sobre la media del año.

    Se promedian las cuatro categorias oficiales en vez de elegir una: la de "1 y 2 estrellas y
    estrellas de plata" seria la mas parecida al mercado de Airbnb por precio, pero esa semejanza
    es una suposicion sobre la que no hay dato, y el promedio no privilegia ninguna lectura. Las
    cuatro rondan 1,16-1,20 en junio, asi que la eleccion cambia poco.
    """
    est = pd.read_csv(BRONZE / "adr_estacionalidad.csv")
    return float(est.loc[est["mes"] == MES_VOLCADO, "factor"].mean())


def main() -> None:
    a = pd.read_csv(BRONZE / "airbnb_anuncios.csv", low_memory=False)
    print(f"Anuncios: {len(a):,}")

    licencias = pd.read_csv(GOLD / "airbnb_situacion_licencia.csv", low_memory=False)
    a = a.merge(
        licencias[["id", "situacion", "sujeto_a_vut", "sin_licencia", "actividad_reciente"]],
        on="id", how="left")

    factor = factor_de_junio()
    a["factor_temporada"] = round(factor, 3)
    a["precio_plaza_anual"] = (a["precio_por_plaza"] / factor).round(2)
    a["banda_plaza"] = por_plaza(a["precio_plaza_anual"])

    a[COLUMNAS].to_csv(SALIDA, index=False, encoding="utf-8")

    con = a["banda_plaza"].notna()
    print(f"  factor de temporada (junio): {factor:.3f}")
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
