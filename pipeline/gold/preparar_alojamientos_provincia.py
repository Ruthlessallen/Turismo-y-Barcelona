"""Tabla publicable de alojamiento reglado de toda la provincia, con su banda economica.

    python pipeline/gold/preparar_alojamientos_provincia.py

Entradas
    data/bronze/hoteles_y_apartaments_unificados.csv   — censo del Registre, 1.563 establecimientos
    data/bronze/geocodificacion_verificada.csv         — ICGC verificado contra poligono
    data/gold/hoteles_bcn.csv                          — barrio, categoría y ADR oficial, solo ciudad

Salida
    data/gold/alojamientos_reglados.csv

**Por que existe esta tabla.** Un export antiguo publicaba el precio leyendo directamente de bronze,
sin banda ni correccion de temporada: la web recibia el precio crudo de una ventana de septiembre y
no habia forma de distinguir un precio medido de uno estimado. La regla de la capa lo impedia y aun
asi ocurria, porque no existia una tabla gold que cubriera la provincia entera — `hoteles_bcn` es
solo la ciudad.

**Que anade sobre bronze.** El censo provincial trae el establecimiento; esta tabla le pega lo que
el analisis ha deducido: coordenada utilizable, precio por noche, banda economica, y sobre todo
**si ese precio es observado o estimado y con cuanto respaldo**. Sin esas dos ultimas columnas la
web no puede cumplir lo que promete en `docs/web-checklist.md`, que es no dar por sabido un precio
que se ha imputado.

**Un precio, dos procedencias, una columna.** `origen_precio` vale `observado` (451, del cruce con
los precios raspados) o `estimado` (317, del modelo), y esta vacia donde no hay precio. Airbnb no
interviene: no aporta ni un solo precio de hotel, solo la geometria de barrios en
`preparar_hoteles_bcn.py`. Los siete matices que usa el analisis para auditar el cruce y el modelo
se quedan en `hoteles_bcn_precio_estimado.csv`, que es su sitio.

**La banda solo llega a la ciudad de Barcelona.** Los 795 establecimientos del resto de la
provincia se quedan sin precio: el raspado cubrio la ciudad y el modelo se entreno con ella, asi
que extenderlo al Maresme o al Valles seria inventar. Salen con `banda_precio` nula, que es la
respuesta honesta, y el mapa los pinta igual porque su ubicacion y su capacidad si constan.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from bandas import por_habitacion, por_plaza

RAIZ = Path(__file__).resolve().parents[2]
BRONZE = RAIZ / "data" / "bronze"
GOLD = RAIZ / "data" / "gold"
SALIDA = GOLD / "alojamientos_reglados.csv"

COLUMNAS = ["licencia_id", "nombre_comercial", "tipo", "municipio", "codi_ine", "barrio",
            "categoria", "estrellas", "tipo_alojamiento", "plazas", "habitaciones", "titular_id",
            "lat", "lon", "precision", "precio_noche_final", "banda_precio",
            "precio_plaza", "banda_plaza", "origen_precio", "categoria_ine"]


def completar_coordenadas(d: pd.DataFrame) -> pd.DataFrame:
    """Coordenada oficial donde la hay, geocodificada verificada donde no.

    `precision` viaja con el punto porque no todas valen lo mismo: `exacta` viene del registro y
    `geocodificada` es una deduccion de la direccion que ademas ya paso el control de que cae en su
    municipio. Pintarlas con el mismo simbolo daria a entender una precision que no se tiene.
    """
    d = d.copy()
    for c in ("lat", "lon"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d["precision"] = np.where(d["lat"].notna(), "exacta", None)

    geo = pd.read_csv(BRONZE / "geocodificacion_verificada.csv", dtype={"licencia_id": str},
                      low_memory=False)
    geo = geo[geo["municipio_coincide"] == True]  # noqa: E712
    geo = geo[["licencia_id", "lat", "lon"]].drop_duplicates("licencia_id")

    d = d.merge(geo, on="licencia_id", how="left", suffixes=("", "_geo"))
    falta = d["lat"].isna() & d["lat_geo"].notna()
    d.loc[falta, ["lat", "lon"]] = d.loc[falta, ["lat_geo", "lon_geo"]].values
    d.loc[falta, "precision"] = "geocodificada"
    return d.drop(columns=["lat_geo", "lon_geo"])


def main() -> None:
    censo = pd.read_csv(BRONZE / "hoteles_y_apartaments_unificados.csv", dtype=str,
                        low_memory=False)
    print(f"Censo provincial: {len(censo)} establecimientos")

    # Un registro de Open Data BCN sin correspondencia en el Registre se queda sin `tipo`. Viene
    # del fichero de hoteles del Ajuntament, asi que hotel es.
    censo["tipo"] = censo["tipo"].fillna("hotel")
    for c in ("plazas", "habitaciones", "titular_id"):
        censo[c] = pd.to_numeric(censo[c], errors="coerce")

    d = completar_coordenadas(censo)

    ciudad = pd.read_csv(GOLD / "hoteles_bcn.csv", dtype={"licencia_id": str}, low_memory=False)
    d = d.merge(
        ciudad[["licencia_id", "barrio", "estrellas", "tipo_alojamiento", "categoria_ine",
                "precio_noche", "origen_precio"]],
        on="licencia_id", how="left").rename(columns={"precio_noche": "precio_noche_final"})

    # La banda por habitación sale del ADR de la categoría. Por plaza, ese mismo ADR entre las
    # plazas por habitación de la categoría (mediana), para que todos los hoteles de una categoría
    # compartan banda: lo que se publica es la categoría, no un precio por hotel.
    d["banda_precio"] = por_habitacion(d["precio_noche_final"])
    por_hab = (d["plazas"] / d["habitaciones"]).where(d["habitaciones"] > 0)
    d["precio_plaza"] = (d["precio_noche_final"]
                         / por_hab.groupby(d["categoria_ine"]).transform("median")).round(2)

    # La banda por plaza es la unica escala en la que un hotel y un piso de Airbnb se comparan.
    d["banda_plaza"] = por_plaza(d["precio_plaza"])

    d[COLUMNAS].to_csv(SALIDA, index=False, encoding="utf-8")

    con_banda = d["banda_precio"].notna()
    print(f"  con coordenada  : {d['lat'].notna().sum():,} ({d['lat'].notna().mean():.1%})")
    print(f"  con banda       : {con_banda.sum():,} (solo ciudad de Barcelona)")
    print(f"  sin banda       : {(~con_banda).sum():,} (resto de la provincia, sin categoria INE)")
    print(f"\n  por tipo  : {d['tipo'].value_counts().to_dict()}")
    print(f"  por banda (habitacion): {d['banda_precio'].value_counts().to_dict()}")
    print(f"  por banda (plaza)     : {d['banda_plaza'].value_counts().to_dict()}")
    print(f"  precio/plaza mediano  : {d['precio_plaza'].median():.0f} EUR")
    print(f"  origen del precio     : {d['origen_precio'].value_counts(dropna=False).to_dict()}")
    print(f"\nGuardado en {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
