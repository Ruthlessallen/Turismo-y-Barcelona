"""Une los dos volcados de Inside Airbnb en una tabla por anuncio, con capacidad y precio por plaza.

    python pipeline/bronze/unificar_airbnb.py

Entradas
    data/raw/airbnb/insideairbnb_barcelona_2026-06-24_listings.csv          — resumen, 19 columnas
    data/raw/airbnb/insideairbnb_barcelona_2026-06-24_listings_detalle.csv.gz — detalle, 90

Salida
    data/bronze/airbnb_anuncios.csv

**Por que hacia falta.** El pipeline solo leia el resumen, que no trae capacidad. Sin `accommodates`
no se puede comparar un anuncio con una habitacion de hotel: un piso entero para cuatro a 221 EUR y
una habitacion privada a 64 EUR no son el mismo producto, y ponerlos en la misma escala diria que
el piso es tres veces mas caro cuando por plaza son 54 EUR frente a 43 EUR.

**La capacidad se toma de `accommodates`, no de `beds` ni `bedrooms`.** Es la unica de las tres sin
un solo nulo en los 15.293 anuncios del detalle; `beds` tiene 2.447 huecos y `bedrooms` 2.562.
Ademas es lo que el anfitrion declara que caben, que es justo el denominador que interesa: cuantas
personas se alojan por ese precio.

**Sobre la moneda.** Inside Airbnb exporta el precio con un simbolo `$` en todos sus volcados, sea
cual sea la ciudad; su diccionario de datos lo define como precio diario **en moneda local**, que
en Barcelona es el euro. El simbolo es un artefacto de su exportador, no una conversion. Queda
dicho aqui porque un lector que abra el CSV crudo vera `$409.00` y puede concluir otra cosa.

**Los dos ficheros no cubren lo mismo.** El resumen trae 15.406 anuncios y el detalle 15.293: hay
113 que solo estan en el resumen. Se conservan todos —el resumen manda como base— y esos 113 se
quedan sin capacidad, marcados por tenerla nula, en vez de desaparecer sin dejar rastro.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
RAW = RAIZ / "data" / "raw" / "airbnb"
BRONZE = RAIZ / "data" / "bronze"
SALIDA = BRONZE / "airbnb_anuncios.csv"

RESUMEN = RAW / "insideairbnb_barcelona_2026-06-24_listings.csv"
DETALLE = RAW / "insideairbnb_barcelona_2026-06-24_listings_detalle.csv.gz"

DEL_DETALLE = ["accommodates", "bedrooms", "beds", "bathrooms_text", "property_type",
               "review_scores_rating", "host_is_superhost", "instant_bookable"]

COLUMNAS = ["id", "name", "host_id", "host_name", "calculated_host_listings_count", "neighbourhood_group",
            "neighbourhood", "latitude", "longitude", "room_type", "property_type",
            "accommodates", "bedrooms", "beds", "minimum_nights", "precio_anuncio",
            "precio_por_plaza", "availability_365", "number_of_reviews",
            "number_of_reviews_ltm", "last_review", "review_scores_rating", "license"]


def a_numero(serie: pd.Series) -> pd.Series:
    """`$409.00` -> 409.0. El separador de miles tambien viaja en el texto."""
    return pd.to_numeric(
        serie.astype(str).str.replace(r"[^\d.]", "", regex=True).replace("", np.nan),
        errors="coerce")


def comparar_precios(d: pd.DataFrame) -> None:
    """Los dos volcados traen precio. Si no coinciden, uno de los dos esta desactualizado.

    Es la unica verificacion cruzada disponible sobre el precio de Airbnb: no hay fuente externa
    con la que contrastarlo, como si la habia para los hoteles con el ADR del INE.
    """
    ambos = d["precio_resumen"].notna() & d["precio_detalle"].notna()
    if not ambos.any():
        return
    # Un euro de margen, no igualdad exacta: el resumen redondea a entero y el detalle guarda
    # centimos, asi que comparar al centimo declara discrepante el 64% de los anuncios cuando la
    # diferencia maxima entre los dos volcados es de 0,50 EUR.
    diferencia = (d.loc[ambos, "precio_resumen"] - d.loc[ambos, "precio_detalle"]).abs()
    print(f"  precio en ambos volcados : {ambos.sum():,} anuncios, "
          f"coinciden {(diferencia < 1).mean():.1%} (diferencia maxima "
          f"{diferencia.max():.2f} EUR, solo redondeo)")
    if (diferencia >= 1).any():
        discrepan = d[ambos][diferencia >= 1]
        print(f"    AVISO: {len(discrepan):,} difieren en mas de un euro. Ejemplos:")
        for _, f in discrepan.head(3).iterrows():
            print(f"      id {f['id']}: resumen {f['precio_resumen']:.2f} "
                  f"vs detalle {f['precio_detalle']:.2f}")


def main() -> None:
    resumen = pd.read_csv(RESUMEN, low_memory=False)
    detalle = pd.read_csv(DETALLE, low_memory=False)
    print(f"Resumen {len(resumen):,} anuncios | detalle {len(detalle):,}")

    columnas_detalle = ["id"] + [c for c in DEL_DETALLE if c in detalle.columns]
    d = resumen.merge(detalle[columnas_detalle + ["price"]].rename(
        columns={"price": "precio_detalle_txt"}), on="id", how="left")
    print(f"  sin ficha de detalle     : {int(d['accommodates'].isna().sum()):,}")

    d["precio_resumen"] = a_numero(d["price"])
    d["precio_detalle"] = a_numero(d["precio_detalle_txt"])
    comparar_precios(d)

    # El detalle es el volcado completo y manda; el resumen cubre los 113 que le faltan.
    d["precio_anuncio"] = d["precio_detalle"].fillna(d["precio_resumen"])

    d["accommodates"] = pd.to_numeric(d["accommodates"], errors="coerce")
    plazas = d["accommodates"].where(d["accommodates"] > 0)
    d["precio_por_plaza"] = (d["precio_anuncio"] / plazas).round(2)

    d[COLUMNAS].to_csv(SALIDA, index=False, encoding="utf-8")

    print(f"\n  con precio               : {int(d['precio_anuncio'].notna().sum()):,} "
          f"({d['precio_anuncio'].notna().mean():.1%})")
    print(f"  con capacidad            : {int(plazas.notna().sum()):,} "
          f"({plazas.notna().mean():.1%})")
    print(f"  con precio y capacidad   : {int(d['precio_por_plaza'].notna().sum()):,}")

    tabla = (d[d["precio_por_plaza"].notna()]
             .groupby("room_type")
             .agg(anuncios=("id", "size"), precio_anuncio=("precio_anuncio", "median"),
                  plazas=("accommodates", "median"), por_plaza=("precio_por_plaza", "median"))
             .round(1).sort_values("anuncios", ascending=False))
    print("\n  mediana por tipo de anuncio:")
    print(tabla.to_string())
    print(f"\nGuardado en {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
