"""Repara los polígonos municipales del ICGC, que vienen con los anillos mal anidados.

    python pipeline/transform/reparar_geometria_municipios.py

Salida
    data/processed/municipios_provincia_barcelona.geojson

El problema: el export WFS del ICGC mete **todas** las partes de un municipio como anillos de un
único polígono, en vez de como polígonos separados del MultiPolygon. GeoJSON define el primer
anillo como exterior y el resto como agujeros, así que la lectura resulta absurda. En Barcelona, el
anillo 0 es un fragmento de 30 × 20 m y la frontera real —uno de los otros 33 anillos— se
interpreta como un hueco: el área sale **−101,8 km²** cuando la ciudad tiene 101,4.

El efecto práctico era que ningún punto de Barcelona caía dentro de Barcelona, así que la
asignación de municipio por polígono fallaba justo donde se concentran los datos.

La reparación reconstruye cada geometría a partir de sus anillos: se ordenan por tamaño y un
anillo cuenta como agujero solo si está contenido en otro mayor; si no, es una parte
independiente. Es lo que el fichero quería decir.

**Cada resultado se valida contra `AREAM5000`**, el área que el propio ICGC publica como
atributo. Tener esa referencia es lo que permite afirmar que la reparación es correcta en vez de
suponerlo: si el área reconstruida coincide con la declarada, la geometría es la buena.
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import MultiPolygon, Polygon
from shapely.geometry.polygon import orient

RAIZ = Path(__file__).resolve().parents[2]
ENTRADA = RAIZ / "data" / "raw" / "geometria" / "icgc_municipis_provincia_barcelona.geojson"
SALIDA = RAIZ / "data" / "processed" / "municipios_provincia_barcelona.geojson"

# Margen al comparar el área reconstruida con la que declara el ICGC. Un 2% absorbe la diferencia
# entre su cálculo y el nuestro sin dejar pasar una geometría realmente mal montada.
TOLERANCIA = 0.02


def anillos(geometria) -> list:
    """Todos los anillos de la geometría, sin distinguir exterior de agujero."""
    partes = geometria.geoms if geometria.geom_type == "MultiPolygon" else [geometria]
    salida = []
    for parte in partes:
        salida.append(parte.exterior)
        salida.extend(parte.interiors)
    return salida


def reconstruir(geometria):
    """Rearma la geometría decidiendo por contención qué anillo es agujero y qué anillo es parte."""
    candidatos = [Polygon(a) for a in anillos(geometria)]
    candidatos = [p for p in candidatos if p.is_valid or not p.buffer(0).is_empty]
    if not candidatos:
        return geometria

    # De mayor a menor: un anillo solo puede ser agujero de otro más grande que él.
    candidatos.sort(key=lambda p: p.area, reverse=True)

    partes: list[Polygon] = []
    for p in candidatos:
        contenedor = next((q for q in partes if q.contains(p.representative_point())), None)
        if contenedor is None:
            partes.append(p)
        else:
            # Es un agujero del que lo contiene: se le resta.
            partes[partes.index(contenedor)] = contenedor.difference(p)

    partes = [orient(p, sign=1.0) for p in partes if not p.is_empty]
    if not partes:
        return geometria
    return partes[0] if len(partes) == 1 else MultiPolygon(
        [g for p in partes for g in (p.geoms if p.geom_type == "MultiPolygon" else [p])])


def main() -> None:
    g = gpd.read_file(ENTRADA)
    print(f"Municipios: {len(g)}")

    area_declarada = pd.to_numeric(g["AREAM5000"], errors="coerce")
    area_original = g.to_crs(25831).area / 1e6
    malos_antes = ((area_original - area_declarada).abs() > area_declarada * TOLERANCIA).sum()
    print(f"  geometrías que no cuadran con AREAM5000: {malos_antes} "
          f"({malos_antes / len(g):.1%})")

    g["geometry"] = g["geometry"].apply(reconstruir)
    g["geometry"] = g["geometry"].buffer(0)  # limpia autointersecciones residuales

    area_nueva = g.to_crs(25831).area / 1e6
    desvio = (area_nueva - area_declarada).abs() / area_declarada
    malos_despues = int((desvio > TOLERANCIA).sum())
    print(f"  tras reparar                           : {malos_despues} "
          f"({malos_despues / len(g):.1%})")

    bcn = g["NOMMUNI"] == "Barcelona"
    print(f"\nBarcelona: {area_nueva[bcn].iloc[0]:.1f} km² reconstruidos "
          f"frente a {area_declarada[bcn].iloc[0]:.1f} declarados")

    if malos_despues:
        print("\nMunicipios que siguen sin cuadrar:")
        for _, f in g.loc[desvio > TOLERANCIA, ["NOMMUNI"]].head(8).iterrows():
            i = f.name
            print(f"  {f['NOMMUNI'][:28]:30s} {area_nueva[i]:8.2f} km² vs {area_declarada[i]:8.2f}")

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    g.to_file(SALIDA, driver="GeoJSON")
    print(f"\nGuardado en {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
