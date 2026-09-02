"""Consolida y prepara de forma anticipada todas las variables numéricas y geográficas de los hoteles de Barcelona.

Entrada:
    data/processed/hoteles_unificados_y_precios.csv
    data/processed/hoteles_geocodificados.csv
    data/raw/hoteles/opendata_bcn_hotels_snapshot.csv

Salida:
    data/processed/hoteles_bcn_analisis_preparado.csv
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd


def map_cat(row: pd.Series) -> float:
    """Mapea la categoría oficial o tipo de establecimiento a un valor numérico continuo.

    Asigna:
    - 5.0: Gran Luxe / 5 estrellas
    - 4.5: 4 estrellas superior
    - 4.0: 4 estrellas
    - 3.0: 3 estrellas
    - 2.0: 2 estrellas
    - 1.0: 1 estrella
    - 0.5: Hostales, pensiones y hoteles sin estrellas ('No aplica')
    - 0.0: Apartamentos turísticos (licencias ATB/ATCC, 'Sense categoritzar')

    Args:
        row (pd.Series): Fila del DataFrame con campos 'categoria', 'tipo' y 'licencia_id'.

    Returns:
        float: Valor numérico equivalente de la categoría (0.0 a 5.0).
    """
    c = str(row.get("categoria", "")).lower() if pd.notna(row.get("categoria")) else ""
    t = str(row.get("tipo", "")).lower() if pd.notna(row.get("tipo")) else ""
    lic = str(row.get("licencia_id", "")).lower() if pd.notna(row.get("licencia_id")) else ""

    if "gran luxe" in c or "5 estrelles" in c:
        return 5.0
    if "4 estrelles superior" in c:
        return 4.5
    if "4 estrelles" in c:
        return 4.0
    if "3 estrelles" in c:
        return 3.0
    if "2 estrelles" in c:
        return 2.0
    if "1 estrella" in c:
        return 1.0
    if "apartament" in t or "atb" in lic or "atcc" in lic or "sense categoritzar" in c:
        return 0.0
    if "no aplica" in c:
        return 0.5
    return 0.5


def preparar_dataset_hoteles_bcn() -> pd.DataFrame:
    """Prepara y guarda el dataset consolidado de hoteles de Barcelona con todas sus variables precalculadas.

    Realiza el filtrado del municipio de Barcelona, la consolidación de coordenadas exactas,
    la asignación de barrios y códigos postales, la conversión de precios por noche, el mapeo de
    categorías numéricas (0.0 = Apartamentos Turísticos, 0.5 = Hostales/Pensiones) y el cálculo de
    la distancia al centro de la ciudad.

    Returns:
        pd.DataFrame: DataFrame de los hoteles de Barcelona listo para su análisis.
    """
    raiz = Path.cwd()
    while not (raiz / "data").exists() and raiz != raiz.parent:
        raiz = raiz.parent
    if not (raiz / "data").exists():
        raiz = Path("../..")

    ruta_unif_prec = raiz / "data" / "processed" / "hoteles_unificados_y_precios.csv"
    ruta_geo = raiz / "data" / "processed" / "hoteles_geocodificados.csv"
    ruta_od = raiz / "data" / "raw" / "hoteles" / "opendata_bcn_hotels_snapshot.csv"
    ruta_salida = raiz / "data" / "processed" / "hoteles_bcn_analisis_preparado.csv"

    df_unif_prec = pd.read_csv(ruta_unif_prec)
    df_geo = pd.read_csv(ruta_geo)
    df_od = pd.read_csv(ruta_od)

    df = df_unif_prec[df_unif_prec["municipio"] == "Barcelona"].copy()

    df = df.merge(
        df_geo[["licencia_id", "lat", "lon"]],
        on="licencia_id",
        how="left",
        suffixes=("", "_geo"),
    )
    df["lat_final"] = df["lat"].fillna(df["lat_geo"])
    df["lon_final"] = df["lon"].fillna(df["lon_geo"])

    df["precio_noche"] = df["precio"] / 2.0

    df["codigo_postal"] = (
        df["codigo_postal"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(5)
    )

    df_od["licencia_id"] = df_od["name"].str.extract(r"([HA]B-\d{6})")
    df = df.merge(
        df_od[["licencia_id", "addresses_neighborhood_name"]],
        on="licencia_id",
        how="left",
    )
    cp_to_barrio = (
        df.groupby("codigo_postal")["addresses_neighborhood_name"]
        .agg(lambda x: x.mode()[0] if not x.mode().empty else np.nan)
        .to_dict()
    )
    df["barrio"] = df["addresses_neighborhood_name"].fillna(
        df["codigo_postal"].map(cp_to_barrio)
    )

    df["categoria_num"] = df.apply(map_cat, axis=1)

    df["distancia_centro_km"] = (
        np.sqrt((df["lat_final"] - 41.3870) ** 2 + (df["lon_final"] - 2.1700) ** 2)
        * 111.0
    )

    df.to_csv(ruta_salida, index=False, encoding="utf-8")
    print(f"Dataset consolidado de Barcelona guardado en: {ruta_salida}")
    print(f"Total registros en Barcelona: {len(df)}")
    print(f"Desglose de categoria_num:")
    print(df["categoria_num"].value_counts(dropna=False).sort_index())

    return df


if __name__ == "__main__":
    preparar_dataset_hoteles_bcn()
