"""Geocodifica los hoteles del registro que no tienen coordenada, contra el ICGC.

    python pipeline/sources/geocodificar_hoteles.py

Salida
    data/processed/hoteles_geocodificados.csv

Por qué hace falta: de los 754 hoteles de la ciudad, **309 no traen coordenada**. Open Data BCN
solo la aporta para los que aparecen en su fichero, y sin ella el cruce con cualquier fuente de
precios cae al emparejamiento por nombre, que es mucho más frágil — de los 208 hoteles que no
cruzan con precio, la mayoría son exactamente estos.

Fuente: geocodificador del Institut Cartogràfic i Geològic de Catalunya. Se eligió sobre las
alternativas por precisión y procedencia:

- **ICGC** — oficial catalán, capa `address` a nivel de portal. Para "Carrer Vila i Vilà 79"
  devuelve 41,3742 / 2,1685, el portal exacto.
- **Cartociudad** — oficial español, también válido; queda como alternativa si el ICGC falla.
- **Nominatim** — descartado: en esa misma dirección devolvió 41,4094, casi cuatro kilómetros al
  norte, porque emparejó con una vía en lugar de con el portal.

Toda coordenada devuelta se verifica dentro de la caja de Barcelona antes de aceptarse: un
geocodificador que no encuentra la dirección devuelve el centroide del municipio o de la comarca,
y eso pegaría todos los hoteles fallidos en el mismo punto sin que se note.
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
RUTA_HOTELES = RAIZ / "data" / "processed" / "hoteles_y_apartaments_unificados.csv"
RUTA_SALIDA = RAIZ / "data" / "processed" / "hoteles_geocodificados.csv"

ICGC = "https://eines.icgc.cat/geocodificador/cerca?text={consulta}&layers=address&size=1"

# Misma caja que en `cruzar_precios_hoteles.py`: si la respuesta cae fuera, no es la dirección.
BBOX = (41.32, 41.47, 2.05, 2.24)

# Un segundo entre llamadas. Son ~300 direcciones contra un servicio público y gratuito: no hay
# ninguna prisa que justifique castigarlo.
PAUSA = 1.0


def en_barcelona(lat: float, lon: float) -> bool:
    lat_min, lat_max, lon_min, lon_max = BBOX
    return lat_min <= lat <= lat_max and lon_min <= lon <= lon_max


def construir_direccion(fila: pd.Series) -> str:
    """`Carrer Vila i Vilà 79, Barcelona` a partir de las columnas del registro."""
    via = f"{fila.get('tipo_via') or ''} {fila.get('nombre_via') or ''}".strip()
    numero = str(fila.get("numero") or "").split("-")[0].strip()  # '2-4' → '2'
    return f"{via} {numero}, Barcelona".strip()


def geocodificar(direccion: str) -> tuple[float, float, str] | None:
    """Devuelve `(lat, lon, etiqueta)` o None si no hay resultado utilizable."""
    url = ICGC.format(consulta=urllib.parse.quote(direccion))
    peticion = urllib.request.Request(url, headers={"User-Agent": "Turismo-BCN/1.0"})
    try:
        with urllib.request.urlopen(peticion, timeout=30) as resp:
            datos = json.load(resp)
    except Exception:
        return None

    for rasgo in datos.get("features", []):
        lon, lat = rasgo.get("geometry", {}).get("coordinates", [None, None])[:2]
        if lat is None or not en_barcelona(lat, lon):
            continue
        return lat, lon, rasgo.get("properties", {}).get("label", "")
    return None


def main() -> None:
    hoteles = pd.read_csv(RUTA_HOTELES, dtype=str)
    ciudad = hoteles[(hoteles["tipo"] == "hotel") & (hoteles["municipio"] == "Barcelona")].copy()
    sin_coordenada = ciudad[ciudad["lat"].isna() | ciudad["lon"].isna()]

    print(f"Hoteles en la ciudad     : {len(ciudad):,}")
    print(f"  ya tienen coordenada   : {len(ciudad) - len(sin_coordenada):,}")
    print(f"  a geocodificar         : {len(sin_coordenada):,}")
    print(f"\nRitmo: una consulta por segundo, ~{len(sin_coordenada) * PAUSA / 60:.0f} minutos\n")

    filas, aciertos = [], 0
    for n, (_, h) in enumerate(sin_coordenada.iterrows(), 1):
        direccion = construir_direccion(h)
        resultado = geocodificar(direccion)
        if resultado:
            lat, lon, etiqueta = resultado
            aciertos += 1
        else:
            lat = lon = etiqueta = None

        filas.append({
            "licencia_id": h["licencia_id"],
            "nombre_comercial": h["nombre_comercial"],
            "direccion_consultada": direccion,
            "lat": lat,
            "lon": lon,
            "etiqueta_icgc": etiqueta,
            "geocodificado": resultado is not None,
        })
        if n % 25 == 0:
            print(f"  {n:4d}/{len(sin_coordenada)}  aciertos: {aciertos} ({aciertos / n:.0%})")
        time.sleep(PAUSA)

    d = pd.DataFrame(filas)
    RUTA_SALIDA.parent.mkdir(parents=True, exist_ok=True)
    d.to_csv(RUTA_SALIDA, index=False, encoding="utf-8")

    print(f"\n{'—' * 56}")
    print(f"Geocodificados: {int(d['geocodificado'].sum()):,} de {len(d):,} "
          f"({d['geocodificado'].mean():.1%})")
    print(f"Sin resultado : {int((~d['geocodificado']).sum()):,}")
    print(f"\nGuardado en {RUTA_SALIDA.relative_to(RAIZ)}")
    if (~d["geocodificado"]).any():
        print("\nEjemplos sin resultado:")
        for x in d.loc[~d["geocodificado"], "direccion_consultada"].head(6):
            print(f"  · {x}")


if __name__ == "__main__":
    main()
