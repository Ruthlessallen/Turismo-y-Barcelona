"""Genera `docs/diccionario.md`: cada fichero de `data/` con sus filas, columnas y quien lo produce.

    python pipeline/generar_diccionario.py

Se lee del dato y de `docs/linaje.md`, no se escribe a mano: asi no puede quedarse desfasado. Es la
guia para quien descargue el repositorio y quiera usar los ficheros sin leer el codigo.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
DATA = RAIZ / "data"
SALIDA = RAIZ / "docs" / "diccionario.md"
CAPAS = ["bronze", "gold", "exports"]
MAX_COLUMNAS = 40


def productores() -> dict[str, str]:
    """Nombre de fichero -> script que lo escribe, leido de la tabla de `linaje.md`."""
    ruta = RAIZ / "docs" / "linaje.md"
    salida: dict[str, str] = {}
    if not ruta.exists():
        return salida
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
        if len(celdas) == 4 and celdas[0].startswith("`"):
            for f in celdas[3].split("<br>"):
                salida[f.strip()] = celdas[0].strip("`")
    return salida


def describir(ruta: Path) -> tuple[str, str]:
    """(filas, columnas) de un fichero tabular o json."""
    try:
        if ruta.suffix == ".csv":
            d = pd.read_csv(ruta, low_memory=False)
            return f"{len(d):,}".replace(",", "."), ", ".join(map(str, d.columns[:MAX_COLUMNAS]))
        if ruta.suffix == ".json":
            j = json.loads(ruta.read_text(encoding="utf-8"))
            if isinstance(j, list):
                return f"{len(j):,}".replace(",", "."), "lista de " + (type(j[0]).__name__ if j else "vacío")
            return "—", ", ".join(list(j)[:MAX_COLUMNAS])
        if ruta.suffix == ".geojson":
            j = json.loads(ruta.read_text(encoding="utf-8"))
            return str(len(j["features"])), ", ".join(j["features"][0]["properties"]) if j["features"] else ""
    except Exception as e:  # un fichero ilegible no debe tirar el documento
        return "?", f"no legible ({e.__class__.__name__})"
    return "—", ""


def main() -> None:
    prod = productores()
    lineas = [
        "# Diccionario de datos", "",
        "Cada fichero de `data/` (salvo `raw/`, que no se versiona): filas, columnas y qué script lo",
        "produce. Generado por `pipeline/generar_diccionario.py`; no se edita a mano.", "",
    ]
    for capa in CAPAS:
        ficheros = sorted(p for p in (DATA / capa).rglob("*") if p.suffix in {".csv", ".json", ".geojson"})
        lineas += [f"## {capa}", "", "| Fichero | Filas | Lo produce | Columnas / claves |", "|---|---:|---|---|"]
        for p in ficheros:
            filas, cols = describir(p)
            nombre = p.relative_to(DATA / capa).as_posix()
            lineas.append(f"| `{nombre}` | {filas} | `{prod.get(p.name, '—')}` | {re.sub(r'[|]', '/', cols)} |")
        lineas.append("")
    SALIDA.write_text("\n".join(lineas), encoding="utf-8")
    print(f"Guardado en {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
