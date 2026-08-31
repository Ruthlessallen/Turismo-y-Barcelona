"""Deja la geometría lista para el navegador: repara, simplifica y recorta atributos.

    python pipeline/transform/preparar_geometria_web.py

Salidas
    data/exports/geo/municipios.geojson   — 311 municipios de la provincia
    data/exports/geo/barrios.geojson      — 75 barrios de la ciudad
    data/exports/geo/peuat.geojson        — 12 zonas del PEUAT

Tres cosas que hay que hacer antes de que un mapa web pueda usar estos ficheros:

**Reparar.** Dos barrios traen una autointersección —comparten un vértice mal montado— y una
geometría inválida rompe tanto el dibujado como cualquier operación de punto dentro de polígono.

**Simplificar.** El fichero municipal pesa 13,7 MB, que en un móvil son varios segundos de espera
antes de ver nada. A la escala en que se mira una provincia, la precisión submétrica del ICGC no
aporta: dos vértices separados por 20 m caen en el mismo píxel. Se simplifica con Douglas-Peucker
sobre coordenadas proyectadas, no sobre grados, porque un grado de longitud y uno de latitud no
miden lo mismo y la tolerancia saldría deformada.

**Recortar atributos.** El GeoJSON del ICGC arrastra identificadores internos que no se usan y que
viajan en cada respuesta.

`preserve_topology=True` evita que la simplificación abra huecos entre municipios vecinos o
convierta un polígono en algo degenerado. Y el resultado se comprueba: si la superficie total
cambia más de un 1%, la tolerancia era demasiado agresiva.
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd

RAIZ = Path(__file__).resolve().parents[2]
DESTINO = RAIZ / "data" / "exports" / "geo"

# Metros. Los municipios se ven a escala de provincia y admiten más simplificación que los
# barrios, que se miran con zoom de ciudad.
TOLERANCIA_MUNICIPIOS = 25
TOLERANCIA_BARRIOS = 5
TOLERANCIA_PEUAT = 5

# Proyectado en metros para Cataluña: la simplificación necesita distancias reales.
CRS_METRICO = 25831

FUENTES = {
    "municipios": (
        RAIZ / "data" / "processed" / "municipios_provincia_barcelona.geojson",
        {"NOMMUNI": "municipio", "CODIMUNI": "codi_ine", "CODICOMAR": "codi_comarca"},
        TOLERANCIA_MUNICIPIOS,
    ),
    "barrios": (
        RAIZ / "data" / "raw" / "geometria" / "insideairbnb_barrios_barcelona.geojson",
        {"neighbourhood": "barrio", "neighbourhood_group": "distrito"},
        TOLERANCIA_BARRIOS,
    ),
    "peuat": (
        RAIZ / "data" / "raw" / "peuat" / "peuat_zonas.geojson",
        {"ZE": "zona"},
        TOLERANCIA_PEUAT,
    ),
}


def preparar(ruta: Path, columnas: dict[str, str], tolerancia: int) -> gpd.GeoDataFrame:
    g = gpd.read_file(ruta)
    invalidas = int((~g.geometry.is_valid).sum())
    if invalidas:
        # `buffer(0)` rehace el polígono resolviendo autointersecciones sin mover los vértices.
        g["geometry"] = g.geometry.buffer(0)
        print(f"    reparadas {invalidas} geometrías inválidas")

    disponibles = {k: v for k, v in columnas.items() if k in g.columns}
    g = g[list(disponibles) + ["geometry"]].rename(columns=disponibles)

    metrico = g.to_crs(CRS_METRICO)
    area_antes = metrico.area.sum()
    metrico["geometry"] = metrico.geometry.simplify(tolerancia, preserve_topology=True)
    desvio = abs(metrico.area.sum() - area_antes) / area_antes
    print(f"    simplificado a {tolerancia} m | superficie alterada: {desvio:.2%}")
    if desvio > 0.01:
        print("    AVISO: más de un 1% de superficie alterada, la tolerancia es agresiva")

    return metrico.to_crs(4326)


def main() -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)
    for nombre, (ruta, columnas, tolerancia) in FUENTES.items():
        if not ruta.exists():
            print(f"  {nombre}: falta {ruta.relative_to(RAIZ)}, se omite")
            continue
        print(f"  {nombre}:")
        g = preparar(ruta, columnas, tolerancia)
        salida = DESTINO / f"{nombre}.geojson"
        g.to_file(salida, driver="GeoJSON")
        antes = ruta.stat().st_size / 1e6
        despues = salida.stat().st_size / 1e6
        print(f"    {len(g)} polígonos | {antes:.1f} MB → {despues:.1f} MB "
              f"({(1 - despues / antes):.0%} menos)\n")
    print(f"Guardado en {DESTINO.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
