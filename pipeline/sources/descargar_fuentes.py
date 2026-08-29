"""Descarga las fuentes de datos verificadas a `data/raw/`.

`data/raw/` no se versiona (ver `.gitignore`): son ~90 MB redescargables, y el Registre de
Turisme incluye nombre y apellidos de titulares persona física. Este script reconstruye esa
carpeta desde cero para que el proyecto siga siendo reproducible sin cargar esos datos al repo.

    python pipeline/sources/descargar_fuentes.py           # todo
    python pipeline/sources/descargar_fuentes.py vut peuat # solo algunas

Las fuentes, su formato y sus peculiaridades están documentadas en
`docs/architecture.md` → Integraciones externas.
"""

from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
CRUDO = RAIZ / "data" / "raw"

# Descargas directas: (destino relativo a data/raw, URL, encoding de origen).
# `encoding` distinto de None fuerza una reconversión a UTF-8 al guardar.
DESCARGAS: dict[str, list[tuple[str, str, str | None]]] = {
    "vut": [
        (
            "vut/opendata_bcn_hut_2016-2026Q1.csv",
            "https://opendata-ajuntament.barcelona.cat/data/dataset/c748799e-1079-44b1-9e60-88d936a3fe70/"
            "resource/b32fa7f6-d464-403b-8a02-0292a64883bf/download",
            None,
        ),
    ],
    "hoteles": [
        # Ojo: el portal sirve este CSV en UTF-16. Se reconvierte a UTF-8 al guardar, porque
        # tal cual no lo abren bien ni pandas ni la mayoría de editores.
        (
            "hoteles/opendata_bcn_hotels_snapshot.csv",
            "https://opendata-ajuntament.barcelona.cat/data/dataset/88efe464-2bcd-4794-85b0-8b0bbfd9e4c0/"
            "resource/9bccce1b-0b9d-4cc6-94a7-459cb99450de/download",
            "utf-16",
        ),
    ],
    "peuat": [
        (
            "peuat/opendata_bcn_mapa_peuat.gpkg",
            "https://opendata-ajuntament.barcelona.cat/data/dataset/b4a20b5f-a8df-41bc-ad74-4e8b0507b897/"
            "resource/607e9139-d1e6-46af-a7a2-3baa0b5f6016/download/basepeuat_.gpkg",
            None,
        ),
    ],
    "airbnb": [
        (
            "airbnb/insideairbnb_barcelona_2026-06-24_listings.csv",
            "https://data.insideairbnb.com/spain/catalonia/barcelona/2026-06-24/visualisations/listings.csv",
            None,
        ),
        # Solo `listing_id` + fecha. La versión detallada (`data/reviews.csv.gz`, 133 MB) añade
        # nombre del huésped y texto del comentario: datos personales que no hacen falta para
        # estimar duraciones de estancia a partir del hueco entre reseñas consecutivas.
        (
            "airbnb/insideairbnb_barcelona_2026-06-24_reviews.csv",
            "https://data.insideairbnb.com/spain/catalonia/barcelona/2026-06-24/visualisations/reviews.csv",
            None,
        ),
    ],
}

# Registre de Turisme (Socrata). Se descarga filtrado a la provincia y partido por categoría,
# que es como lo consume `unificar_registros.py`.
SOCRATA = "https://analisi.transparenciacatalunya.cat/resource/t2h3-cgys.json"
CATEGORIAS_REGISTRE = {
    "registre_turisme/hut_provincia_barcelona.csv": ["Habitatges d'ús turístic"],
    "registre_turisme/hoteles_y_apartaments_turistics_provincia_barcelona.csv": [
        "Hotels", "Apartaments Turístics",
    ],
}

# Geometría municipal (WFS del ICGC). `outputFormat=geojson` devuelve WGS84 directamente:
# no hace falta reproyectar ni convertir con GDAL.
WFS_ICGC = (
    "https://geoserveis.icgc.cat/servei/catalunya/divisions-administratives/wfs"
    "?service=WFS&version=2.0.0&request=GetFeature"
    "&typeName=divisions_administratives_wfs:divisions_administratives_municipis_5000"
    "&outputFormat=geojson"
)


def descargar(url: str, destino: Path, encoding: str | None = None) -> None:
    """Descarga un fichero, reconvirtiendo a UTF-8 si la fuente usa otra codificación."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=120) as resp:
        datos = resp.read()
    if encoding:
        destino.write_text(datos.decode(encoding), encoding="utf-8")
    else:
        destino.write_bytes(datos)
    print(f"  OK {destino.relative_to(RAIZ)}  ({len(datos) / 1_000_000:.1f} MB)")


def descargar_registre() -> None:
    """Descarga el Registre de Turisme filtrado por provincia y lo parte por categoría."""
    import pandas as pd

    consulta = urllib.parse.urlencode({"$where": "prov_ncia='Barcelona'", "$limit": 50000})
    with urllib.request.urlopen(f"{SOCRATA}?{consulta}", timeout=180) as resp:
        registros = json.load(resp)
    print(f"  Registre de Turisme: {len(registros):,} registros de la provincia")

    df = pd.DataFrame(registros)
    for destino, tipos in CATEGORIAS_REGISTRE.items():
        sub = df[df["tipus_establiment"].isin(tipos)]
        ruta = CRUDO / destino
        ruta.parent.mkdir(parents=True, exist_ok=True)
        sub.to_csv(ruta, index=False, encoding="utf-8")
        print(f"  OK {ruta.relative_to(RAIZ)}  ({len(sub):,} filas)")


def descargar_geometria() -> None:
    """Descarga los límites municipales y guarda además el recorte de la provincia."""
    import pandas as pd  # noqa: F401  (geopandas lo necesita disponible)
    import geopandas as gpd

    ruta_completa = CRUDO / "geometria" / "icgc_municipis_catalunya_completa.geojson"
    descargar(WFS_ICGC, ruta_completa)

    gdf = gpd.read_file(ruta_completa)
    provincia = gdf[gdf["NOMPROV"] == "Barcelona"]
    ruta_prov = CRUDO / "geometria" / "icgc_municipis_provincia_barcelona.geojson"
    provincia.to_file(ruta_prov, driver="GeoJSON")
    print(f"  OK {ruta_prov.relative_to(RAIZ)}  ({len(provincia)} municipios)")


ESPECIALES = {"registre_turisme": descargar_registre, "geometria": descargar_geometria}


def main() -> None:
    disponibles = list(DESCARGAS) + list(ESPECIALES)
    pedidas = sys.argv[1:] or disponibles
    desconocidas = [f for f in pedidas if f not in disponibles]
    if desconocidas:
        raise SystemExit(f"Fuente desconocida: {desconocidas}. Opciones: {disponibles}")

    for fuente in pedidas:
        print(f"\n{fuente}")
        try:
            if fuente in ESPECIALES:
                ESPECIALES[fuente]()
            else:
                for destino, url, enc in DESCARGAS[fuente]:
                    descargar(url, CRUDO / destino, enc)
        except Exception as e:  # una fuente caída no debe abortar el resto
            print(f"  FALLO en {fuente}: {e}")

    print(
        "\nListo. Los informes de OTB no se descargan aquí: son PDF con infografías que "
        "requieren transcripción manual (ver data/raw/README.md)."
    )


if __name__ == "__main__":
    main()
