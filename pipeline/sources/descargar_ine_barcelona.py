"""Descarga las series del INE para Barcelona: viajeros, plazas y tarifa media diaria (ADR).

    python pipeline/sources/descargar_ine_barcelona.py

Salida
    data/raw/ine/<serie>.json              — respuesta cruda de la API
    data/processed/serie_ine_barcelona.csv — las tres series alineadas por mes

Sirven para lo que no se puede improvisar: **estimar cómo responde el precio a la presión de la
demanda con datos reales**, en vez de suponer una elasticidad. Con viajeros (demanda), plazas
(oferta) y ADR (precio) en la misma serie mensual, la relación histórica es observable.

Por qué el INE y no un portal de reservas: es estadística oficial, citable en un dashboard
público, y cubre el sector entero en vez de la muestra que un scraper alcance.

La API es abierta y sin clave, pero **exige `User-Agent`**: sin él devuelve 403.

Límite que condiciona su uso: el dato es **agregado por punto turístico**, no por hotel. Sirve
para el nivel y la tendencia de la ciudad, nunca para atribuir un precio a un establecimiento.
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
DESTINO = RAIZ / "data" / "raw" / "ine"
RUTA_SERIE = RAIZ / "data" / "processed" / "serie_ine_barcelona.csv"

API = "https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/{tabla}?tip=AM&nult={n}"

# Barcelona es el punto turístico 563 en las tres tablas (verificado 2026-08-30).
PUNTO_BARCELONA = "Barcelona"

TABLAS = {
    "viajeros_pernoctaciones": ("2078", "Viajeros y pernoctaciones por puntos turísticos"),
    "adr": ("46298", "Tarifa media diaria (ADR) por puntos turísticos"),
    "plazas_ocupacion": ("2076", "Establecimientos, plazas, ocupación y personal"),
}

# 60 meses = cinco años, que es el horizonte del proyecto (ver docs/prd.md).
MESES = 72


def pedir(tabla: str) -> list[dict]:
    """Una tabla completa del INE. El User-Agent no es opcional: sin él responde 403."""
    peticion = urllib.request.Request(
        API.format(tabla=tabla, n=MESES), headers={"User-Agent": "Turismo-BCN/1.0"}
    )
    with urllib.request.urlopen(peticion, timeout=180) as resp:
        return json.load(resp)


def filtrar_barcelona(series: list[dict]) -> list[dict]:
    """Se queda con las series cuyo nombre menciona Barcelona.

    El INE identifica cada serie por un nombre compuesto ("Barcelona. Viajeros. Total.") en vez de
    por campos separados, así que el filtro es por texto.
    """
    return [s for s in series if PUNTO_BARCELONA in s.get("Nombre", "")]


def a_filas(series: list[dict], etiqueta: str) -> pd.DataFrame:
    """Aplana la estructura del INE (una serie con su lista de datos) a filas mes × valor."""
    filas = []
    for s in series:
        for d in s.get("Data", []):
            filas.append({
                "fuente": etiqueta,
                "serie": s.get("Nombre", "").strip(),
                "unidad": s.get("T3_Unidad"),
                "anyo": d.get("Anyo"),
                "periodo": d.get("T3_Periodo"),
                "provisional": d.get("T3_TipoDato") == "Provisional",
                "fecha": d.get("Fecha"),
                "valor": d.get("Valor"),
            })
    d = pd.DataFrame(filas)
    if not d.empty:
        # La fecha llega en ISO con desfase horario ("2026-07-01T00:00:00.000+02:00"), y como el
        # desfase cambia entre verano e invierno pandas la rechaza sin `utc=True`.
        d["fecha"] = pd.to_datetime(d["fecha"], utc=True, errors="coerce")
        d["mes"] = d["fecha"].dt.to_period("M").astype(str)
        d = d.sort_values(["serie", "fecha"])
    return d


def main() -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)
    trozos = []

    for clave, (tabla, descripcion) in TABLAS.items():
        print(f"{clave} (tabla {tabla}) — {descripcion}")
        try:
            crudo = pedir(tabla)
        except Exception as e:
            print(f"  FALLO: {e}")
            continue

        (DESTINO / f"{clave}.json").write_text(
            json.dumps(crudo, ensure_ascii=False), encoding="utf-8")

        bcn = filtrar_barcelona(crudo)
        print(f"  {len(crudo)} series en la tabla | {len(bcn)} de Barcelona")
        d = a_filas(bcn, clave)
        if not d.empty:
            print(f"  {len(d):,} observaciones | {d['mes'].min()} → {d['mes'].max()}")
            for nombre in d["serie"].unique()[:6]:
                print(f"     · {nombre[:76]}")
            trozos.append(d)

    if not trozos:
        raise SystemExit("No se obtuvo ninguna serie. Revisa la conectividad con el INE.")

    serie = pd.concat(trozos, ignore_index=True)
    RUTA_SERIE.parent.mkdir(parents=True, exist_ok=True)
    serie.to_csv(RUTA_SERIE, index=False, encoding="utf-8")
    print(f"\nGuardado en {RUTA_SERIE.relative_to(RAIZ)} ({len(serie):,} filas)")


if __name__ == "__main__":
    main()
