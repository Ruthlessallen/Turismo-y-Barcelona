"""Unifica el censo provincial de hoteles con los precios raspados en un único archivo CSV procesado.

Entrada:
    data/processed/hoteles_y_apartaments_unificados.csv
    data/processed/hoteles_con_precio.csv

Salida:
    data/processed/hoteles_unificados_y_precios.csv
"""

from __future__ import annotations

from pathlib import Path
import pandas as pd


def unificar_censo_con_precios() -> pd.DataFrame:
    """Combina el censo unificado de establecimientos con la capa de precios raspados.

    Lee los archivos procesados de establecimientos y precios, realiza un cruce
    por 'licencia_id' conservando todos los registros del censo provincial y guarda
    el DataFrame consolidado en la carpeta data/processed.

    Returns:
        pd.DataFrame: DataFrame unificado con datos administrativos y de precios.
    """
    # Determinación dinámica de la raíz del proyecto
    raiz = Path.cwd()
    while not (raiz / "data").exists() and raiz != raiz.parent:
        raiz = raiz.parent
    if not (raiz / "data").exists():
        raiz = Path("../..")

    ruta_unif = raiz / "data" / "processed" / "hoteles_y_apartaments_unificados.csv"
    ruta_prec = raiz / "data" / "processed" / "hoteles_con_precio.csv"
    ruta_salida = raiz / "data" / "processed" / "hoteles_unificados_y_precios.csv"

    # Carga de datasets procesados
    df_unif = pd.read_csv(ruta_unif)
    df_prec = pd.read_csv(ruta_prec)

    # Cruce de información por licencia_id
    columnas_precio = [
        "licencia_id",
        "precio",
        "moneda",
        "estrellas_raspadas",
        "puntuacion",
        "metodo_cruce",
        "similitud",
    ]
    df_completo = df_unif.merge(
        df_prec[columnas_precio],
        on="licencia_id",
        how="left",
    )

    # Guardar resultado consolidado en la carpeta processed
    df_completo.to_csv(ruta_salida, index=False, encoding="utf-8")
    print(f"Archivo guardado en: {ruta_salida}")
    print(f"Total registros: {len(df_completo)}")
    print(f"Establecimientos con precio: {df_completo['precio'].notna().sum()}")

    return df_completo


if __name__ == "__main__":
    unificar_censo_con_precios()
