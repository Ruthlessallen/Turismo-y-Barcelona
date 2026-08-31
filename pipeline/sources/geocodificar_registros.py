"""Geocodifica contra el ICGC los registros de VUT y hoteles que no traen coordenada.

    python pipeline/sources/geocodificar_registros.py            # todo
    python pipeline/sources/geocodificar_registros.py --ciudad   # solo Barcelona ciudad

Salida
    data/processed/geocodificacion_icgc.csv

Generaliza `geocodificar_hoteles.py`, que resolvía solo los hoteles de la ciudad, a los 14.474
registros sin coordenada de los dos registros. Todos tienen vía y número, así que todos son
geocodificables.

Tres decisiones de diseño, y el motivo de cada una:

**Primero la ciudad, luego la provincia.** Los 354 registros de Barcelona son el 2,4% del total y
salen en seis minutos; el resto tarda horas. Ordenarlo así deja utilizable lo que desbloquea el
mapa de ciudad sin esperar a la provincia entera.

**Guardado incremental.** Con miles de llamadas, un corte de red a mitad no puede costar todo lo
hecho. El fichero se reescribe cada 50 registros.

**Reanudable.** Al arrancar se lee lo ya guardado y esos registros no se vuelven a consultar. Es
lo que permite parar y seguir sin castigar dos veces a un servicio público gratuito.

La coordenada devuelta se verifica dentro de la provincia antes de aceptarse: un geocodificador
que no encuentra la dirección suele devolver el centroide del municipio o algo peor, y eso pegaría
todos los fallos en el mismo punto sin que se note en el recuento.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
RUTA_VUT = RAIZ / "data" / "processed" / "vut_unificados.csv"
RUTA_HOTELES = RAIZ / "data" / "processed" / "hoteles_y_apartaments_unificados.csv"
RUTA_SALIDA = RAIZ / "data" / "processed" / "geocodificacion_icgc.csv"

ICGC = "https://eines.icgc.cat/geocodificador/cerca?text={consulta}&layers=address&size=1"

# La provincia entera, no solo la ciudad: aquí se geocodifica también Sitges o Calella.
BBOX_PROVINCIA = (41.05, 42.35, 0.85, 3.15)
BBOX_CIUDAD = (41.32, 41.47, 2.05, 2.24)

PAUSA = 1.0        # un segundo entre llamadas: es un servicio público y gratuito
CADA = 50          # cada cuántos registros se vuelca el fichero


def dentro(lat: float, lon: float, caja: tuple) -> bool:
    lat_min, lat_max, lon_min, lon_max = caja
    return lat_min <= lat <= lat_max and lon_min <= lon <= lon_max


def construir_direccion(fila: pd.Series) -> str:
    """`Carrer Balmes 129, Barcelona` a partir de las columnas del registro."""
    via = f"{fila.get('tipo_via') or ''} {fila.get('nombre_via') or ''}".strip()
    numero = str(fila.get("numero") or "").split("-")[0].strip()  # '2-4' → '2'
    municipio = str(fila.get("municipio") or "").strip()
    return f"{via} {numero}, {municipio}".strip(" ,")


def geocodificar(direccion: str) -> tuple[float, float, str] | None:
    """Devuelve `(lat, lon, etiqueta)` o None si no hay resultado dentro de la provincia."""
    url = ICGC.format(consulta=urllib.parse.quote(direccion))
    peticion = urllib.request.Request(url, headers={"User-Agent": "Turismo-BCN/1.0"})
    try:
        with urllib.request.urlopen(peticion, timeout=30) as resp:
            datos = json.load(resp)
    except Exception:
        return None

    for rasgo in datos.get("features", []):
        coords = rasgo.get("geometry", {}).get("coordinates", [])
        if len(coords) < 2:
            continue
        lon, lat = coords[0], coords[1]
        if not dentro(lat, lon, BBOX_PROVINCIA):
            continue
        return lat, lon, rasgo.get("properties", {}).get("label", "")
    return None


def pendientes(solo_ciudad: bool) -> pd.DataFrame:
    """Registros sin coordenada de ambos ficheros, con la ciudad primero."""
    trozos = []
    for origen, ruta in (("vut", RUTA_VUT), ("hotel_at", RUTA_HOTELES)):
        d = pd.read_csv(ruta, dtype=str)
        d = d[pd.to_numeric(d["lat"], errors="coerce").isna()].copy()
        d["origen"] = origen
        trozos.append(d)

    d = pd.concat(trozos, ignore_index=True)
    d["es_ciudad"] = d["municipio"] == "Barcelona"
    if solo_ciudad:
        d = d[d["es_ciudad"]]
    # La ciudad primero: es lo que desbloquea el mapa de detalle.
    return d.sort_values("es_ciudad", ascending=False).reset_index(drop=True)


def main() -> None:
    solo_ciudad = "--ciudad" in sys.argv
    d = pendientes(solo_ciudad)

    ya = pd.DataFrame()
    if RUTA_SALIDA.exists():
        ya = pd.read_csv(RUTA_SALIDA, dtype={"licencia_id": str})
        hechos = set(ya["licencia_id"])
        d = d[~d["licencia_id"].isin(hechos)]
        print(f"Reanudando: {len(ya):,} ya geocodificados")

    print(f"Pendientes: {len(d):,}  ({int(d['es_ciudad'].sum()):,} en la ciudad)")
    print(f"Tiempo estimado: {len(d) * PAUSA / 3600:.1f} h\n")

    filas = ya.to_dict("records") if len(ya) else []
    aciertos = int(ya["geocodificado"].sum()) if len(ya) else 0

    for n, (_, r) in enumerate(d.iterrows(), 1):
        direccion = construir_direccion(r)
        res = geocodificar(direccion)
        if res:
            aciertos += 1
        filas.append({
            "licencia_id": r["licencia_id"],
            "origen": r["origen"],
            "municipio": r["municipio"],
            "direccion_consultada": direccion,
            "lat": res[0] if res else None,
            "lon": res[1] if res else None,
            "etiqueta_icgc": res[2] if res else None,
            "geocodificado": res is not None,
            "en_ciudad": bool(res and dentro(res[0], res[1], BBOX_CIUDAD)),
        })

        if n % CADA == 0 or n == len(d):
            pd.DataFrame(filas).to_csv(RUTA_SALIDA, index=False, encoding="utf-8")
            print(f"  {n:6,}/{len(d):,}  aciertos: {aciertos:,} "
                  f"({aciertos / (len(filas)):.0%})", flush=True)
        time.sleep(PAUSA)

    final = pd.DataFrame(filas)
    final.to_csv(RUTA_SALIDA, index=False, encoding="utf-8")
    print(f"\n{'—' * 56}")
    print(f"Geocodificados: {int(final['geocodificado'].sum()):,} de {len(final):,} "
          f"({final['geocodificado'].mean():.1%})")
    print(f"Guardado en {RUTA_SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
