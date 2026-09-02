"""Modulo de evaluacion de modelos e imputacion de precios de hoteles en Barcelona ciudad.

Este script utiliza un modelo de regresion Gradient Boosting y vecinos comparables en escala logaritmica,
incorporando barrio (cobertura 99.7%), categoria oficial por estrellas, capacidad y grupo hotelero,
para imputar el precio por noche final en los hoteles sin precio raspado.
"""

from __future__ import annotations

from pathlib import Path
import pandas as pd
import numpy as np

from sklearn.model_selection import KFold, cross_validate
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.neighbors import KNeighborsRegressor

# Rutas del proyecto
RAIZ = Path(__file__).resolve().parents[2]
RUTA_PREPARADOS = RAIZ / "data" / "processed" / "hoteles_bcn_preparados.csv"
RUTA_SALIDA_IMPUTADO = RAIZ / "data" / "processed" / "hoteles_bcn_con_precio_imputado.csv"


def evaluar_modelos_barrio_logaritmicos(df: pd.DataFrame) -> tuple[pd.DataFrame, HistGradientBoostingRegressor, list[str]]:
    """Evalua modelos de regresion incorporando el barrio y caracteristicas en escala logaritmica.

    Args:
        df (pd.DataFrame): DataFrame de hoteles de Barcelona con precios conocidos y barrio enriquecido.

    Returns:
        tuple[pd.DataFrame, HistGradientBoostingRegressor, list[str]]:
            - DataFrame resumen con R² logaritmico y MAE en Euros reales.
            - Modelo HistGradientBoostingRegressor ajustado sobre todos los datos de entrenamiento.
            - Lista de nombres de las columnas de caracteristicas utilizadas.
    """
    # Filtrar precios conocidos excluyendo anomalias extremas de raspado (>1500 €/noche)
    df_ml = df[df["precio_noche"].notna() & (df["precio_noche"] < 1500)].copy()

    # Preparar variables cuantitativas
    df_ml["cat_num_clean"] = df_ml["categoria_num"].fillna(0.0)
    df_ml["habs_clean"] = df_ml["habitaciones"].fillna(df_ml["habitaciones"].median())
    df_ml["plazas_clean"] = df_ml["plazas"].fillna(df_ml["plazas"].median())

    X_num = df_ml[["cat_num_clean", "habs_clean", "plazas_clean"]].copy()
    X_cat = pd.get_dummies(df_ml[["barrio", "grupo_hotelero"]], drop_first=True)
    X = pd.concat([X_num, X_cat], axis=1)
    feature_names = list(X.columns)

    y_real = df_ml["precio_noche"].values
    y_log = np.log1p(y_real)

    kf = KFold(n_splits=5, shuffle=True, random_state=42)

    modelos = {
        "HistGradientBoosting Regressor (barrio log)": HistGradientBoostingRegressor(random_state=42),
        "Random Forest Regressor (barrio log)": RandomForestRegressor(n_estimators=150, random_state=42),
    }

    filas_resumen = []
    for nombre, modelo in modelos.items():
        cv_log = cross_validate(modelo, X, y_log, cv=kf, scoring=["r2"])
        r2_log = float(cv_log["test_r2"].mean())

        # Calcular MAE en Euros reales revirtiendo la escala logaritmica
        mae_eur_list = []
        for train_idx, val_idx in kf.split(X):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train_log = y_log[train_idx]
            y_val_real = y_real[val_idx]

            modelo.fit(X_train, y_train_log)
            pred_log = modelo.predict(X_val)
            pred_eur = np.expm1(pred_log)
            mae_eur_list.append(np.mean(np.abs(pred_eur - y_val_real)))

        mae_real = float(np.mean(mae_eur_list))
        filas_resumen.append({"Modelo": nombre, "R2_logaritmico": round(r2_log, 3), "MAE_euros_noche": round(mae_real, 2)})

    df_resumen = pd.DataFrame(filas_resumen)

    # Entrenar modelo principal HistGradientBoosting sobre todos los datos filtrados
    hgb_optimo = HistGradientBoostingRegressor(random_state=42)
    hgb_optimo.fit(X, y_log)

    return df_resumen, hgb_optimo, feature_names


def ejecutar_imputacion_final() -> pd.DataFrame:
    """Ejecuta el flujo de evaluacion e imputacion de precios de hoteles en Barcelona por barrio y categoria.

    Returns:
        pd.DataFrame: DataFrame procesado con precios reales e imputados guardado en CSV.
    """
    df = pd.read_csv(RUTA_PREPARADOS, dtype={"codigo_postal": str})

    df_resumen, hgb_model, feature_names = evaluar_modelos_barrio_logaritmicos(df)
    print("=== RESULTADOS DE EVALUACIÓN DE MODELOS CON BARRIO ===")
    print(df_resumen.to_string(index=False))

    # Construir matriz de caracteristicas completa para todo el dataset de Barcelona
    df["cat_num_clean"] = df["categoria_num"].fillna(0.0)
    df["habs_clean"] = df["habitaciones"].fillna(df["habitaciones"].median())
    df["plazas_clean"] = df["plazas"].fillna(df["plazas"].median())

    X_full_num = df[["cat_num_clean", "habs_clean", "plazas_clean"]].copy()
    X_full_cat = pd.get_dummies(df[["barrio", "grupo_hotelero"]], drop_first=True)
    X_full = pd.concat([X_full_num, X_full_cat], axis=1)

    # Alinear columnas con la matriz de entrenamiento
    X_full = X_full.reindex(columns=feature_names, fill_value=0)

    # Predecir precios por noche en escala logaritmica y convertir a Euros
    df["precio_noche_pred"] = np.expm1(hgb_model.predict(X_full)).round(2)
    df["precio_noche_final"] = df["precio_noche"].fillna(df["precio_noche_pred"])
    df["es_imputado"] = df["precio_noche"].isna()

    # Guardar resultado final
    df.to_csv(RUTA_SALIDA_IMPUTADO, index=False, encoding="utf-8")
    print(f"\nDataset final guardado en: {RUTA_SALIDA_IMPUTADO}")
    print(f"Total hoteles BCN: {len(df)} | Precios reales: {(~df['es_imputado']).sum()} | Precios imputados: {df['es_imputado'].sum()}")

    return df


if __name__ == "__main__":
    ejecutar_imputacion_final()
