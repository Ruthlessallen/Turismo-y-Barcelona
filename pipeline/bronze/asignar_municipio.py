"""Asigna municipio y barrio a cualquier fichero con coordenadas, por punto dentro de polígono.

    python pipeline/bronze/asignar_municipio.py

Salidas
    data/bronze/geocodificacion_verificada.csv     — geocodificaciones con su veredicto

**Verifica las geocodificaciones del ICGC.** Un geocodificador que no encuentra una dirección
no siempre falla: a veces devuelve un punto plausible pero equivocado, y eso no se detecta
contando aciertos. Comparar el municipio del polígono con el que ya constaba en el registro es
una comprobación independiente — si no coinciden, la coordenada está mal aunque el servicio la
diera por buena.

Todo es offline: los 311 polígonos municipales del ICGC y los 75 barrios de Barcelona ya están
descargados. Sin llamadas de red y en segundos.
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
# La versión reparada, no la cruda: el export WFS del ICGC trae los anillos mal anidados y con
# ella ningún punto de Barcelona caía dentro de Barcelona (ver reparar_geometria_municipios.py).
RUTA_MUNICIPIOS = RAIZ / "data" / "bronze" / "municipios_provincia_barcelona.geojson"
RUTA_BARRIOS = RAIZ / "data" / "raw" / "geometria" / "insideairbnb_barrios_barcelona.geojson"
RUTA_GEOCODIFICADO = RAIZ / "data" / "bronze" / "geocodificacion_icgc.csv"

SALIDA_VERIFICACION = RAIZ / "data" / "bronze" / "geocodificacion_verificada.csv"


def como_puntos(d: pd.DataFrame, lat: str, lon: str) -> gpd.GeoDataFrame:
    """Convierte un DataFrame con lat/lon en puntos georreferenciados en WGS84."""
    d = d.copy()
    d[lat] = pd.to_numeric(d[lat], errors="coerce")
    d[lon] = pd.to_numeric(d[lon], errors="coerce")
    validos = d[lat].notna() & d[lon].notna()
    return gpd.GeoDataFrame(
        d[validos],
        geometry=gpd.points_from_xy(d.loc[validos, lon], d.loc[validos, lat]),
        crs="EPSG:4326",
    )


def asignar(puntos: gpd.GeoDataFrame, poligonos: gpd.GeoDataFrame,
            columnas: dict[str, str]) -> pd.DataFrame:
    """Une cada punto con el polígono que lo contiene."""
    unido = gpd.sjoin(puntos, poligonos[list(columnas) + ["geometry"]],
                      how="left", predicate="within")
    # Un punto justo sobre el borde puede caer en dos polígonos y duplicar la fila.
    unido = unido[~unido.index.duplicated(keep="first")]
    return unido.rename(columns=columnas).drop(columns=["index_right"], errors="ignore")


def verificar_geocodificacion(municipios: gpd.GeoDataFrame) -> None:
    if not RUTA_GEOCODIFICADO.exists():
        print("\n(no hay geocodificaciones que verificar todavía)")
        return

    d = pd.read_csv(RUTA_GEOCODIFICADO)
    hechos = d[d["geocodificado"] == True]  # noqa: E712
    print(f"\n=== Verificación de {len(hechos):,} geocodificaciones ===")

    puntos = como_puntos(hechos, "lat", "lon")
    con_muni = asignar(puntos, municipios, {"NOMMUNI": "municipio_poligono"})
    salida = pd.DataFrame(con_muni.drop(columns="geometry"))

    # El municipio del registro y el del polígono deben coincidir. Que no coincidan significa que
    # el geocodificador devolvió un punto en otro pueblo: la dirección existe en varios sitios, o
    # resolvió por aproximación. En ambos casos esa coordenada no sirve.
    norm = lambda s: s.astype(str).str.strip().str.lower()  # noqa: E731
    salida["municipio_coincide"] = norm(salida["municipio"]) == norm(salida["municipio_poligono"])

    ok = int(salida["municipio_coincide"].sum())
    print(f"  el municipio coincide : {ok:,} ({ok / len(salida):.1%})")
    print(f"  NO coincide           : {len(salida) - ok:,}  <- coordenada sospechosa")

    salida.to_csv(SALIDA_VERIFICACION, index=False, encoding="utf-8")
    print(f"  -> {SALIDA_VERIFICACION.relative_to(RAIZ)}")

    fallos = salida[~salida["municipio_coincide"]]
    if len(fallos):
        print("\n  ejemplos de discrepancia (registro -> polígono):")
        for _, f in fallos.head(6).iterrows():
            print(f"    {str(f['municipio'])[:24]:26s} -> {str(f['municipio_poligono'])[:24]:26s}"
                  f" {str(f['direccion_consultada'])[:40]}")


def main() -> None:
    municipios = gpd.read_file(RUTA_MUNICIPIOS)
    barrios = gpd.read_file(RUTA_BARRIOS)
    print(f"Geometría: {len(municipios)} municipios | {len(barrios)} barrios de la ciudad")

    verificar_geocodificacion(municipios)


if __name__ == "__main__":
    main()
