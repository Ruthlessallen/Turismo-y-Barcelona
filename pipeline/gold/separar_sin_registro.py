"""Saca de la lista de pisos los que no tienen registro acreditado.

    python pipeline/gold/separar_sin_registro.py

Entrada y salida (se reescriben las dos)
    data/gold/airbnb_para_web.csv        — se queda solo con los de `estado_licencia == con_licencia`
    data/gold/airbnb_excluidos_web.csv   — recibe el resto con `motivo_exclusion = sin_registro_acreditado`

**Por que existe (decision del 2026-10-06).** La eliminacion de 2028 quita licencias. Un piso que no
tiene ninguna acreditada en el registro oficial no tiene licencia que perder: si sigue operando, lo
hara fuera del mercado legal, y no hay dato que diga que se vaya. Contarlo como turista que hay que
realojar inflaba el efecto. Eran 1.849 de los 6.834 pisos, el 21 % de las plazas.

- **Dicen tener registro y no consta** (498): numero imposible (por encima del HUTB-80024, o de
  relleno), numero que no consta, o un numero valido pero de una habitacion o de un hotel.
- **Deberian tenerlo y no lo declaran** (1.351): no declara nada, declara exencion, anuncia una
  habitacion con un numero que no consta, o el anfitrion tiene licencias pero ninguna es de esa
  vivienda.

**No es una afirmacion de que sean ilegales.** «No consta» puede ser una licencia recien concedida
que el registro aun no recoge. Se separan por falta de prueba, no por prueba de lo contrario, y
siguen en `airbnb_excluidos_web.csv` con su `motivo_estado` para quien quiera recontar con otro
criterio. Para volver al criterio anterior basta ejecutar de nuevo `revisar_airbnb_v2.ipynb`, que
regenera los dos ficheros, y no ejecutar este script.

**Orden:** `revisar_airbnb_v2.ipynb` -> este script -> `modelar_sustitucion.py` -> exports.
Es idempotente: si ya se ejecuto, no encuentra nada que mover.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
GOLD = RAIZ / "data" / "gold"
EN_ALCANCE = "con_licencia"
MOTIVO = "sin_registro_acreditado"


def main() -> None:
    dentro = pd.read_csv(GOLD / "airbnb_para_web.csv", low_memory=False)
    fuera = pd.read_csv(GOLD / "airbnb_excluidos_web.csv", low_memory=False)

    sin = dentro["estado_licencia"] != EN_ALCANCE
    if not sin.any():
        print(f"Nada que mover: los {len(dentro):,} pisos ya tienen registro acreditado.")
        return

    mover = dentro[sin].copy()
    mover["motivo_exclusion"] = MOTIVO
    # Los excluidos tienen un subconjunto de las columnas: lo que sobra (precio por plaza anual,
    # banda...) no existe para ellos y no se inventa.
    mover = mover.reindex(columns=fuera.columns)

    pd.concat([fuera, mover], ignore_index=True).to_csv(
        GOLD / "airbnb_excluidos_web.csv", index=False, encoding="utf-8")
    dentro[~sin].to_csv(GOLD / "airbnb_para_web.csv", index=False, encoding="utf-8")

    plazas = pd.to_numeric(mover["accommodates"], errors="coerce").sum()
    print(f"Movidos {len(mover):,} pisos ({plazas:,.0f} plazas) a excluidos: {MOTIVO}")
    print(f"Quedan {int((~sin).sum()):,} pisos con registro acreditado")
    print(mover["motivo_estado"].value_counts().to_string())


if __name__ == "__main__":
    main()
