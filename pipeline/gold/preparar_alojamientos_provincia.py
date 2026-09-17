"""Tabla publicable de alojamiento reglado de toda la provincia, con su banda economica.

    python pipeline/gold/preparar_alojamientos_provincia.py

Entradas
    data/bronze/hoteles_y_apartaments_unificados.csv   — censo del Registre, 1.563 establecimientos
    data/bronze/geocodificacion_verificada.csv         — ICGC verificado contra poligono
    data/gold/hoteles_bcn_precio_estimado.csv          — precio y banda, solo ciudad de Barcelona

Salida
    data/gold/alojamientos_reglados.csv

**Por que existe esta tabla.** `export_mapa.py` publicaba el precio leyendo directamente de bronze,
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

from bandas import por_plaza, precio_por_plaza_hotel

RAIZ = Path(__file__).resolve().parents[2]
BRONZE = RAIZ / "data" / "bronze"
GOLD = RAIZ / "data" / "gold"
SALIDA = GOLD / "alojamientos_reglados.csv"

COLUMNAS = ["licencia_id", "nombre_comercial", "tipo", "municipio", "codi_ine", "barrio",
            "categoria", "estrellas", "tipo_alojamiento", "plazas", "habitaciones", "titular_id",
            "lat", "lon", "precision", "precio_noche_final", "banda_precio",
            "precio_plaza", "banda_plaza", "origen_precio"]


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


def resolver_origen(d: pd.DataFrame) -> pd.DataFrame:
    """Colapsa a una sola columna de que sabemos del precio: `observado`, `estimado` o nada.

    La capa de analisis distingue siete matices (`origen_precio`, `metodo_cruce`,
    `precio_es_estimado`, `apoyo_estimacion`, `estimacion_fiable`, `modelo_precio`,
    `mae_modelo_eur`) y esa granularidad es correcta ahi: sirve para auditar el cruce y el modelo.
    Publicarla entera es otra cosa — obliga a quien lee el mapa a reconstruir a mano si el precio
    esta medido o inventado a partir de columnas que se contradicen en apariencia. Aqui solo
    sobrevive esa pregunta, que es la unica que cambia como hay que leer el numero. El detalle
    sigue intacto en `hoteles_bcn_precio_estimado.csv`.

    Las estimaciones sin ejemplos comparables (`apoyo_estimacion == "escaso"`) pierden el precio y
    la banda aqui, no en el export. Un hueco es mas honesto que un numero que nadie puede
    contradecir, y si el corte vive en gold ningun consumidor futuro puede saltarselo por olvido.
    """
    d = d.copy()
    sin_apoyo = d["apoyo_estimacion"].eq("escaso")
    d.loc[sin_apoyo, ["precio_noche_final", "banda_precio"]] = np.nan

    estimado = d["precio_es_estimado"].astype("boolean")
    d["origen_precio"] = np.where(
        d["banda_precio"].isna(), None,
        np.where(estimado.fillna(False), "estimado", "observado"))
    return d.drop(columns=["precio_es_estimado", "apoyo_estimacion"])


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

    ciudad = pd.read_csv(GOLD / "hoteles_bcn_precio_estimado.csv", dtype={"licencia_id": str},
                         low_memory=False)
    d = d.merge(
        ciudad[["licencia_id", "barrio", "estrellas", "tipo_alojamiento", "precio_noche_final",
                "banda_precio", "precio_es_estimado", "apoyo_estimacion"]],
        on="licencia_id", how="left")

    d = resolver_origen(d)

    # La banda por plaza es la unica escala en la que un hotel y un piso de Airbnb se comparan.
    # `banda_precio` sigue siendo por habitacion, que es lo que paga quien reserva y lo que mide
    # la estadistica oficial: son dos preguntas distintas y las dos columnas conviven.
    d["precio_plaza"] = precio_por_plaza_hotel(d["precio_noche_final"], d["plazas"],
                                               d["habitaciones"])
    d["banda_plaza"] = por_plaza(d["precio_plaza"])

    d[COLUMNAS].to_csv(SALIDA, index=False, encoding="utf-8")

    con_banda = d["banda_precio"].notna()
    print(f"  con coordenada  : {d['lat'].notna().sum():,} ({d['lat'].notna().mean():.1%})")
    print(f"  con banda       : {con_banda.sum():,} (solo ciudad de Barcelona)")
    print(f"  sin banda       : {(~con_banda).sum():,} (resto de la provincia, sin precio raspado)")
    print(f"\n  por tipo  : {d['tipo'].value_counts().to_dict()}")
    print(f"  por banda (habitacion): {d['banda_precio'].value_counts().to_dict()}")
    print(f"  por banda (plaza)     : {d['banda_plaza'].value_counts().to_dict()}")
    print(f"  precio/plaza mediano  : {d['precio_plaza'].median():.0f} EUR")
    print(f"  origen del precio     : {d['origen_precio'].value_counts(dropna=False).to_dict()}")
    print(f"\nGuardado en {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
