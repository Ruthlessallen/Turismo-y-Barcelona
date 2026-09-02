"""Convierte el ADR oficial por categoría a formato largo y lo contrasta con los precios raspados.

    python pipeline/transform/preparar_adr_por_categoria.py

Entradas
    data/raw/ine/portaldades_adr_por_categoria_2013_2026.csv   — Portal de Dades del Ajuntament
    data/processed/hoteles_bcn.csv                             — precios raspados ya cruzados

Salidas
    data/processed/adr_por_categoria.csv    — la serie en formato largo, una fila por mes y categoría
    data/processed/adr_estacionalidad.csv   — factor de cada mes frente a la media de su año

**Qué es el ADR y qué no.** Es el ingreso medio por habitación ocupada, de la Encuesta de Ocupación
Hotelera del INE. Es precio **cobrado**, no anunciado, y solo sobre habitaciones que se vendieron:
un hotel con la mitad vacía no arrastra el ADR hacia abajo. Nuestro raspado es lo contrario, precio
anunciado con independencia de que alguien reserve. Por eso no son la misma magnitud y no se
sustituyen — pero sí se comprueban el uno al otro, y el ADR aporta dos cosas que el raspado no
tiene: nivel oficial por categoría y trece años de estacionalidad.

**Para qué sirve aquí.** Los precios raspados corresponden a estancias del 29 de septiembre al 7 de
octubre de 2026: una sola ventana. Sin saber cuánto se aparta esa ventana de un mes corriente, la
banda económica que salga de ahí hereda el sesgo de la fecha sin avisar. La estacionalidad de la
serie oficial es lo que permite decir si septiembre está caro o barato respecto al año.

**Las categorías no se corresponden una a una.** El INE agrupa "1 y 2 estrellas de oro y estrellas
de plata": las de plata son hostales y pensiones, que en el Registre figuran como "No aplica" y
aquí quedaron en `sin_estrellas`. Así que esa banda oficial cubre a la vez nuestros hoteles de 1 y
2 estrellas y buena parte de los sin estrellas, y es la única forma de anclar un segmento que no
tiene categoría propia en la estadística.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
ENTRADA = RAIZ / "data" / "raw" / "ine" / "portaldades_adr_por_categoria_2013_2026.csv"
HOTELES = RAIZ / "data" / "processed" / "hoteles_bcn.csv"
SALIDA = RAIZ / "data" / "processed" / "adr_por_categoria.csv"
SALIDA_ESTACIONAL = RAIZ / "data" / "processed" / "adr_estacionalidad.csv"

MESES = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
         "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}

# A qué categoría oficial pertenece cada valor de `estrellas` del Registre. Los 4,5 —"4 estrelles
# superior"— van con los de 4: la estadística no distingue el superior.
BANDA_OFICIAL = {
    "1 and 2 gold stars and silver stars": [1.0, 2.0],
    "3 gold stars": [3.0],
    "4 gold stars": [4.0, 4.5],
    "5 gold stars": [5.0],
}

# La estacionalidad se estima solo desde aquí: el patrón cambió tras la pandemia (ver estacionalidad).
PRIMER_ANYO = 2022

# Los meses que cubre el raspado: estancias del 29-09 al 07-10 de 2026.
MESES_RASPADO = [9, 10]


def leer_ancho() -> pd.DataFrame:
    """El portal exporta con `;`, coma decimal y `-` donde no hay dato."""
    d = pd.read_csv(ENTRADA, sep=";", decimal=",", na_values=["-", ""], encoding="utf-8-sig")
    d = d.rename(columns={d.columns[0]: "categoria_oficial"})
    return d.dropna(subset=["categoria_oficial"])


def a_formato_largo(d: pd.DataFrame) -> pd.DataFrame:
    largo = d.melt(id_vars="categoria_oficial", var_name="periodo", value_name="adr")
    partes = largo["periodo"].str.extract(r"([A-Za-z]{3})\s*(\d{4})")
    largo["mes"] = partes[0].map(MESES)
    largo["anyo"] = pd.to_numeric(partes[1], errors="coerce")
    largo = largo.dropna(subset=["mes", "anyo", "adr"])
    largo["anyo"] = largo["anyo"].astype(int)
    largo["mes"] = largo["mes"].astype(int)
    largo["fecha"] = pd.to_datetime(dict(year=largo["anyo"], month=largo["mes"], day=1))
    return largo[["categoria_oficial", "fecha", "anyo", "mes", "adr"]].sort_values(
        ["categoria_oficial", "fecha"])


def estacionalidad(largo: pd.DataFrame) -> pd.DataFrame:
    """Cuánto se aparta cada mes de la media de su propio año.

    Se normaliza dentro del año y no sobre toda la serie porque el nivel de precios ha subido mucho
    en trece años: comparar un septiembre de 2014 con la media de 2013-2026 mezclaría estacionalidad
    con inflación. Dividiendo por la media del año, cada valor dice solo cuánto pesa ese mes.

    Solo cuenta de 2022 en adelante. No por la inflación —la normalización dentro del año ya la
    cancela— sino porque el patrón cambió: comparando 2013-2019 con 2022-2026, febrero cae un
    13,7%, enero un 8,7%, agosto un 4,7%, y junio sube un 6,4%. La temporada alta se ha ensanchado
    hacia las estaciones intermedias y agosto ha perdido peso. La forma general se mantiene —las
    dos series correlacionan 0,94— pero usar el periodo viejo metería un invierno más caro del que
    hoy existe. Septiembre, que es el mes que nos toca corregir, apenas se movió: 1,145 a 1,137.

    2020 y 2021 quedan fuera por el mismo motivo con más razón: con los hoteles cerrados o al 20%
    de ocupación, esos meses no describen ninguna temporada.
    """
    d = largo[largo["anyo"] >= PRIMER_ANYO].copy()
    d["factor"] = d["adr"] / d.groupby(["categoria_oficial", "anyo"])["adr"].transform("mean")
    return (d.groupby(["categoria_oficial", "mes"])["factor"]
            .agg(factor="median", anyos="size").reset_index())


def contrastar(largo: pd.DataFrame, estacional: pd.DataFrame) -> None:
    """Compara lo raspado con lo oficial, categoría a categoría."""
    h = pd.read_csv(HOTELES, low_memory=False)
    h = h[h["precio_noche"].notna()]
    ultimo = largo["fecha"].max()
    print(f"\nSerie oficial: {largo['fecha'].min():%Y-%m} a {ultimo:%Y-%m}, "
          f"{largo['categoria_oficial'].nunique()} categorías")

    print("\n=== Raspado (29 sep - 7 oct 2026) frente al ADR oficial ===")
    print(f"{'categoría oficial':38s} {'n':>4s} {'raspado':>9s} {'ADR jul-26':>11s} "
          f"{'ADR sep típ.':>13s} {'desvío':>8s}")
    filas = []
    for banda, estrellas in BANDA_OFICIAL.items():
        propios = h[h["estrellas"].isin(estrellas)]["precio_noche"]
        serie = largo[largo["categoria_oficial"] == banda]
        if not len(propios) or not len(serie):
            continue
        ultimo_adr = float(serie.loc[serie["fecha"].idxmax(), "adr"])
        # ADR de septiembre estimado: último dato x factor de septiembre / factor de su mes
        f = estacional[estacional["categoria_oficial"] == banda].set_index("mes")["factor"]
        mes_ultimo = int(serie.loc[serie["fecha"].idxmax(), "mes"])
        adr_sep = ultimo_adr * f.get(9, 1.0) / f.get(mes_ultimo, 1.0)
        mediana = float(propios.median())
        filas.append({"categoria_oficial": banda, "n_raspado": len(propios),
                      "mediana_raspada": round(mediana, 1),
                      "adr_ultimo": round(ultimo_adr, 1),
                      "adr_septiembre_estimado": round(adr_sep, 1),
                      "desvio_pct": round((mediana / adr_sep - 1) * 100, 1)})
        print(f"{banda[:36]:38s} {len(propios):4d} {mediana:9.0f} {ultimo_adr:11.0f} "
              f"{adr_sep:13.0f} {(mediana / adr_sep - 1) * 100:7.0f}%")

    sin_estrellas = h[h["estrellas"].isna()]["precio_noche"]
    if len(sin_estrellas):
        print(f"\n  (los {len(sin_estrellas)} sin estrellas —hostales y pensiones— median "
              f"{sin_estrellas.median():.0f} EUR; la estadística los mete en la banda de "
              f"'estrellas de plata', junto a los de 1 y 2)")

    print("\n=== Estacionalidad: cuánto pesa cada mes sobre la media del año ===")
    tabla = estacional.pivot(index="mes", columns="categoria_oficial", values="factor").round(3)
    tabla.columns = [c[:14] for c in tabla.columns]
    print(tabla.to_string())
    sep = estacional[estacional["mes"] == 9]["factor"].median()
    print(f"\n  Septiembre está un {(sep - 1) * 100:+.0f}% sobre la media anual: "
          f"lo raspado en esa ventana sobreestima el año en esa proporción.")


def main() -> None:
    largo = a_formato_largo(leer_ancho())
    largo.to_csv(SALIDA, index=False, encoding="utf-8")
    estacional = estacionalidad(largo)
    estacional.to_csv(SALIDA_ESTACIONAL, index=False, encoding="utf-8")
    contrastar(largo, estacional)
    print(f"\nGuardado en {SALIDA.relative_to(RAIZ)} ({len(largo)} filas)")
    print(f"           {SALIDA_ESTACIONAL.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
