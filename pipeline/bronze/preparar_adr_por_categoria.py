"""Convierte el ADR oficial por categoría a formato largo.

    python pipeline/bronze/preparar_adr_por_categoria.py

Entrada
    data/raw/ine/portaldades_adr_por_categoria_2013_2026.csv   — Portal de Dades del Ajuntament

Salidas
    data/bronze/adr_por_categoria.csv    — una fila por mes y categoría
    data/bronze/adr_estacionalidad.csv   — factor de cada mes frente a la media de su año (lo lee el notebook de Airbnb)

**Qué es el ADR.** Ingreso medio por habitación ocupada de la Encuesta de Ocupación Hotelera del
INE: precio cobrado, no anunciado. Es el único precio de hotel que usa el proyecto: la banda
económica de cada hotel sale del ADR de su categoría (ver `bandas.py`).

**Las categorías no se corresponden una a una.** El INE agrupa "1 y 2 estrellas de oro y estrellas
de plata": las de plata son hostales y pensiones, que en el Registre figuran como "No aplica".
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
ENTRADA = RAIZ / "data" / "raw" / "ine" / "portaldades_adr_por_categoria_2013_2026.csv"
SALIDA = RAIZ / "data" / "bronze" / "adr_por_categoria.csv"
SALIDA_ESTACIONAL = RAIZ / "data" / "bronze" / "adr_estacionalidad.csv"

# La estacionalidad se estima solo desde aqui: el patron cambio tras la pandemia (ver estacionalidad).
PRIMER_ANYO = 2022

MESES = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
         "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}



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


def main() -> None:
    largo = a_formato_largo(leer_ancho())
    largo.to_csv(SALIDA, index=False, encoding="utf-8")
    estacionalidad(largo).to_csv(SALIDA_ESTACIONAL, index=False, encoding="utf-8")
    ultimo = largo["fecha"].max()
    print(f"Serie oficial: {largo['fecha'].min():%Y-%m} a {ultimo:%Y-%m}, "
          f"{largo['categoria_oficial'].nunique()} categorías")
    print(f"Guardado en {SALIDA.relative_to(RAIZ)} ({len(largo)} filas)")


if __name__ == "__main__":
    main()
