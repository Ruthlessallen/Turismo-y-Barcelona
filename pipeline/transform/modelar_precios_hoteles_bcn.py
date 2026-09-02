"""Estima el precio por noche de los alojamientos de Barcelona que no lo tienen raspado.

    python pipeline/transform/modelar_precios_hoteles_bcn.py

Entrada
    data/processed/hoteles_bcn.csv

Salidas
    data/processed/hoteles_bcn_precio_estimado.csv   — el dataset con `precio_noche_final`
    data/processed/modelos_precio_comparativa.csv    — qué obtuvo cada modelo y optimizador
    data/processed/precio_error_por_segmento.csv     — dónde acierta y dónde no
    data/processed/precio_cobertura_entrenamiento.csv — qué se estima sin ejemplos comparables

Compara siete modelos afinados con dos buscadores, mide el error del ganador con validación
cruzada repetida, y lo desglosa por segmento antes de imputar nada.

**El error se mide con validación cruzada repetida, no con una partición única.** Una versión
anterior apartaba 86 casos de prueba y anunciaba 40,6 € de error; la validación cruzada sobre los
mismos datos daba 57 €. Con 86 filas el resultado depende demasiado de cuáles tocaron: no era un
modelo mejor, era una partición afortunada. Aquí se repite el reparto cinco veces y se informa la
media y el rango, porque un número sin dispersión invita a creérselo más de lo que aguanta.

**La geografía va solo en `lat`/`lon`.** El dataset trae además barrio, distrito, código postal y
distancia al centro, y las cinco dicen casi lo mismo: hay una mediana de un código postal por
barrio y de dos barrios por código postal. Quedarse con las cinco no mejora el error —56,6 € frente
a 57,2 € con solo `lat`/`lon`, que es ruido— pero sí destroza la lectura de importancias: al
barajar una variable las demás cubren el hueco y todas parecen irrelevantes. Medida por bloques la
ubicación vale 19 € de error; medida variable a variable parecía valer 4.

**El objetivo va en logaritmo y el error se informa en euros.** Los precios tienen la cola larga a
la derecha —de 77 € a 717 € entre los percentiles 1 y 99— y en esa escala un modelo persigue los
caros y descuida a los baratos.

**La codificación de categorías ocurre dentro del `Pipeline`**, ajustada solo con los pliegues de
entrenamiento. Codificar por fuera y luego alinear columnas deja a los niveles no compartidos
leídos como la categoría de referencia sin que nada lo delate.

**Antes de imputar se comprueba a quién se imputa.** Los 430 con precio tienen 58 habitaciones de
mediana; los 338 sin precio, 13. Un error medio global no dice nada sobre los segundos, así que se
publica el error por segmento y no solo el agregado.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import optuna
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.base import clone
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.ensemble import (ExtraTreesRegressor, GradientBoostingRegressor,
                              HistGradientBoostingRegressor, RandomForestRegressor)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.model_selection import (KFold, RandomizedSearchCV, RepeatedKFold, cross_val_predict,
                                     cross_val_score)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBRegressor

optuna.logging.set_verbosity(optuna.logging.WARNING)

RAIZ = Path(__file__).resolve().parents[2]
PROC = RAIZ / "data" / "processed"
ENTRADA = PROC / "hoteles_bcn.csv"
SALIDA = PROC / "hoteles_bcn_precio_estimado.csv"
SALIDA_COMPARATIVA = PROC / "modelos_precio_comparativa.csv"
SALIDA_SEGMENTOS = PROC / "precio_error_por_segmento.csv"
SALIDA_COBERTURA = PROC / "precio_cobertura_entrenamiento.csv"

SEMILLA = 42

# Se modela el equivalente anual, no el precio de septiembre. El objetivo del modelo tiene que ser
# la misma magnitud que la banda que se publica: entrenar sobre precio de temporada alta y corregir
# la prediccion despues arrastraria el factor a un sitio donde ya no se puede comprobar contra nada.
OBJETIVO = "precio_noche_anual"

NUMERICAS = ["estrellas", "plazas", "habitaciones", "lat", "lon"]
CATEGORICAS = ["tipo_alojamiento", "subtipo", "cadena", "tamano"]
COLUMNAS = NUMERICAS + CATEGORICAS

# Cortes de tamaño. No son estadísticos: separan la pensión del hotel urbano y del gran hotel, que
# es donde cambia el modelo de negocio y con él la forma de fijar precio.
CORTES_TAMANO = [0, 15, 40, 100, np.inf]
NOMBRES_TAMANO = ["muy_pequeno", "pequeno", "mediano", "grande"]

# Bandas económicas, al estilo del €–€€€€ de los buscadores. Los cortes no son cuartiles: los
# cuartiles de Barcelona caen en 142/174/222, bandas de 32 € que son más estrechas que el error
# del modelo y que además nadie sabe leer. Estos separan el alojamiento económico del urbano
# corriente, del alto y del lujo, y el modelo acierta la banda exacta un 65,6% de las veces
# —frente al 45,7% de decir siempre la mayoritaria— y cae en la correcta o la contigua un 93%.
CORTES_BANDA = [100, 175, 300]
ETIQUETAS_BANDA = ["€", "€€", "€€€", "€€€€"]

# Un precio por encima de este múltiplo de la mediana de su categoría no se cree. Es relativo a la
# categoría y no absoluto para no penalizar a un cinco estrellas por ser caro: lo que delata a un
# valor es ser imposible *dentro de su clase*, no en el conjunto.
FACTOR_ATIPICO = 5.0


def preprocesado() -> ColumnTransformer:
    """Imputa, escala y codifica.

    `min_frequency=5` agrupa los niveles con menos de cinco casos. Con 430 filas etiquetadas, una
    columna por nivel raro deja al modelo memorizando dos o tres ejemplos en vez de aprender nada.
    """
    numerico = Pipeline([("imputar", SimpleImputer(strategy="median")),
                         ("escalar", StandardScaler())])
    categorico = Pipeline([
        ("imputar", SimpleImputer(strategy="constant", fill_value="desconocido")),
        ("codificar", OneHotEncoder(handle_unknown="ignore", min_frequency=5,
                                    sparse_output=False))])
    return ColumnTransformer([("num", numerico, NUMERICAS), ("cat", categorico, CATEGORICAS)])


def envolver(modelo) -> TransformedTargetRegressor:
    """Preprocesado y modelo en un estimador, con el objetivo transformado dentro de cada pliegue."""
    return TransformedTargetRegressor(
        regressor=Pipeline([("preparar", preprocesado()), ("modelo", modelo)]),
        func=np.log1p, inverse_func=np.expm1)


def catalogo_modelos() -> dict:
    """Siete familias distintas, con la rejilla de cada una.

    Los modelos van con `n_jobs=1`: quien paraleliza es el buscador, repartiendo pliegues entre
    núcleos. Si además cada modelo reclama todos los núcleos, los procesos se pelean por los mismos
    y el conjunto tarda más que en serie.

    RandomForest y ExtraTrees no extrapolan —promedian hojas, así que nunca predicen por encima del
    máximo visto en el entrenamiento— y el Ridge está para cubrir ese flanco.
    """
    return {
        "Ridge": (Ridge(), {"modelo__alpha": [0.01, 0.1, 1.0, 10.0, 100.0, 300.0]}),
        "RandomForest": (
            RandomForestRegressor(random_state=SEMILLA, n_jobs=1),
            {"modelo__n_estimators": [300, 600],
             "modelo__max_depth": [None, 8, 14, 20],
             "modelo__min_samples_leaf": [1, 2, 4, 8],
             "modelo__max_features": ["sqrt", 0.3, 0.6]}),
        "ExtraTrees": (
            ExtraTreesRegressor(random_state=SEMILLA, n_jobs=1),
            {"modelo__n_estimators": [300, 600],
             "modelo__max_depth": [None, 10, 18],
             "modelo__min_samples_leaf": [1, 2, 4, 8],
             "modelo__max_features": ["sqrt", 0.3, 0.6]}),
        "GradientBoosting": (
            GradientBoostingRegressor(random_state=SEMILLA),
            {"modelo__n_estimators": [200, 400, 700],
             "modelo__learning_rate": [0.02, 0.05, 0.1],
             "modelo__max_depth": [2, 3, 4],
             "modelo__subsample": [0.7, 1.0]}),
        "HistGradientBoosting": (
            HistGradientBoostingRegressor(random_state=SEMILLA),
            {"modelo__learning_rate": [0.02, 0.05, 0.1],
             "modelo__max_iter": [200, 400, 700],
             "modelo__max_leaf_nodes": [7, 15, 31],
             "modelo__min_samples_leaf": [5, 10, 20],
             "modelo__l2_regularization": [0.0, 1.0]}),
        "XGBoost": (
            XGBRegressor(random_state=SEMILLA, n_jobs=1, tree_method="hist", verbosity=0),
            {"modelo__n_estimators": [300, 600, 900],
             "modelo__learning_rate": [0.02, 0.05, 0.1],
             "modelo__max_depth": [2, 3, 5],
             "modelo__subsample": [0.7, 1.0],
             "modelo__colsample_bytree": [0.6, 1.0],
             "modelo__reg_lambda": [1.0, 5.0]}),
        "LightGBM": (
            LGBMRegressor(random_state=SEMILLA, n_jobs=1, verbose=-1),
            {"modelo__n_estimators": [300, 600, 900],
             "modelo__learning_rate": [0.02, 0.05, 0.1],
             "modelo__num_leaves": [7, 15, 31],
             "modelo__min_child_samples": [5, 10, 20],
             "modelo__subsample": [0.7, 1.0],
             "modelo__reg_lambda": [0.0, 5.0]}),
    }


class BusquedaOptuna:
    """Adaptador que le da a Optuna la interfaz de los buscadores de sklearn.

    Se muestrea de la **misma** rejilla con `suggest_categorical`: lo que se compara es la
    estrategia de búsqueda, no quién tenía más sitio donde buscar.
    """

    def __init__(self, estimador, rejilla: dict, cv, n_pruebas: int = 60):
        self.estimador, self.rejilla, self.cv, self.n_pruebas = estimador, rejilla, cv, n_pruebas

    def fit(self, X, y):
        def objetivo(prueba: optuna.Trial) -> float:
            elegidos = {k: prueba.suggest_categorical(k, list(v)) for k, v in self.rejilla.items()}
            return -cross_val_score(clone(self.estimador).set_params(**elegidos), X, y, cv=self.cv,
                                    scoring="neg_mean_absolute_error", n_jobs=-1).mean()

        estudio = optuna.create_study(direction="minimize",
                                      sampler=optuna.samplers.TPESampler(seed=SEMILLA))
        estudio.optimize(objetivo, n_trials=self.n_pruebas, show_progress_bar=False)
        self.best_params_ = estudio.best_params
        self.best_score_ = -estudio.best_value
        self.best_estimator_ = clone(self.estimador).set_params(**estudio.best_params).fit(X, y)
        return self


def buscadores(estimador, rejilla: dict, cv) -> dict:
    """Dos estrategias de búsqueda.

    En la comparación anterior GridSearch, RandomizedSearch y Optuna coincidieron en el óptimo en
    cinco de los siete modelos: las rejillas son pequeñas y la búsqueda aleatoria las agota igual.
    GridSearch se llevaba más de la mitad del tiempo total sin dar un resultado distinto, así que
    se queda fuera. HalvingRandom también: afinaba peor de forma sistemática por descartar
    candidatos con muy pocos datos.
    """
    rejilla = {f"regressor__{k}": v for k, v in rejilla.items()}
    return {
        "RandomizedSearch": RandomizedSearchCV(
            estimador, rejilla, n_iter=40, random_state=SEMILLA,
            scoring="neg_mean_absolute_error", cv=cv, n_jobs=-1, refit=True),
        "Optuna": BusquedaOptuna(estimador, rejilla, cv),
    }


def preparar_variables(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    d["tamano"] = pd.cut(d["habitaciones"], bins=CORTES_TAMANO, labels=NOMBRES_TAMANO,
                         right=True).astype(object)
    return d


def recortar_atipicos(d: pd.DataFrame) -> pd.DataFrame:
    """Recorta los precios imposibles al límite, en vez de borrar la fila.

    `Attica21 Barcelona Mar` figuraba a 4.090 €/noche siendo un cuatro estrellas de 75
    habitaciones, cuando sus vecinos de distrito y categoría están entre 648 y 928 €. Esa fila
    sola aportaba 13 € de los 56 de error, y era además la causa de que el error variase entre 35
    y 96 € según el reparto de pliegues: no fallaba el modelo, fallaba el dato.

    Se recorta y no se elimina porque el establecimiento existe, tiene sus plazas y sus
    habitaciones, y cuenta para el mercado igual que los demás. Lo que no vale es su precio, y
    llevarlo al límite de lo creíble conserva la fila con el resto de su información intacta.
    """
    d = d.copy()
    mediana_categoria = d.groupby(d["estrellas"].fillna(-1))[OBJETIVO].transform("median")
    techo = mediana_categoria * FACTOR_ATIPICO
    recortados = d[OBJETIVO] > techo
    d["precio_recortado"] = recortados.fillna(False)
    if recortados.any():
        print(f"\nPrecios recortados al techo de su categoría ({FACTOR_ATIPICO:.0f}x la mediana):")
        for _, f in d[recortados].iterrows():
            print(f"  {str(f['nombre_comercial'])[:34]:36s} {f[OBJETIVO]:8.0f} -> "
                  f"{techo[f.name]:6.0f} EUR")
        d.loc[recortados, OBJETIVO] = techo[recortados]
    return d


def asignar_banda(precio: pd.Series) -> pd.Series:
    """Banda económica al estilo €–€€€€."""
    return pd.Series(np.where(precio.isna(), None,
                              np.take(ETIQUETAS_BANDA, np.digitize(precio.fillna(0),
                                                                   CORTES_BANDA))),
                     index=precio.index)


def acierto_de_banda(real: np.ndarray, pred: np.ndarray) -> None:
    """Cuánto acierta el modelo en lo que de verdad se publica.

    El error en euros no es la métrica que importa si lo que va a la web es una banda: un hotel de
    150 € estimado en 175 € falla por 25 € y acierta la banda. Y al revés, fallar por 5 € junto a
    una frontera cuesta una banda entera.

    Se compara contra decir siempre la banda mayoritaria, que es el listón real: con bandas
    desiguales, un acierto alto puede venir de que casi todo cae en la misma.
    """
    br, bp = np.digitize(real, CORTES_BANDA), np.digitize(pred, CORTES_BANDA)
    mayoritaria = pd.Series(br).value_counts(normalize=True).max()
    print("\n=== Acierto de banda económica (lo que se publica) ===")
    print(f"  banda exacta        : {(br == bp).mean():.1%}  "
          f"(decir siempre la mayoritaria daría {mayoritaria:.1%})")
    print(f"  banda exacta o vecina: {(np.abs(br - bp) <= 1).mean():.1%}")
    tabla = pd.crosstab(pd.Series([ETIQUETAS_BANDA[i] for i in br], name="real"),
                        pd.Series([ETIQUETAS_BANDA[i] for i in bp], name="estimada"))
    print(tabla.to_string())


def cobertura_de_entrenamiento(d: pd.DataFrame) -> pd.DataFrame:
    """Qué se está estimando sin haber visto nada parecido.

    Un modelo predice para cualquier fila que se le pase, tenga o no ejemplos comparables. Donde
    no los hay la predicción sale igual, sin ninguna señal de que es una extrapolación: la única
    forma de saberlo es contar cuántos casos con precio real sostienen cada segmento.

    Esta tabla es la que dice de qué alojamientos conviene buscar precio por otra vía en lugar de
    estimarlo.
    """
    filas = []
    for nombre, columnas in (("tipo", ["tipo_alojamiento"]),
                             ("tipo x tamaño", ["tipo_alojamiento", "tamano"]),
                             ("estrellas", ["estrellas"]),
                             ("subtipo", ["subtipo"])):
        for valor, g in d.groupby(columnas, dropna=False):
            con = int(g[OBJETIVO].notna().sum())
            sin = int(g[OBJETIVO].isna().sum())
            if sin == 0:
                continue
            filas.append({
                "corte": nombre,
                "segmento": " / ".join(str(v) for v in
                                       (valor if isinstance(valor, tuple) else (valor,))),
                "a_estimar": sin, "con_precio_real": con,
                "apoyo": round(con / (con + sin), 2),
                "veredicto": ("SIN APOYO" if con == 0 else
                              "APOYO ESCASO" if con < 10 else
                              "apoyo justo" if con < 30 else "suficiente")})
    return pd.DataFrame(filas).sort_values(["corte", "a_estimar"], ascending=[True, False])


def error_por_segmento(d: pd.DataFrame, real: np.ndarray, pred: np.ndarray) -> pd.DataFrame:
    """Error fuera de muestra desglosado.

    Un error medio de 57 € puede repartirse de muchas formas, y la que importa es si el modelo
    funciona en los segmentos que hay que imputar. Las predicciones vienen de `cross_val_predict`:
    a cada alojamiento lo predice un modelo que no lo vio al entrenar.

    El sesgo va aparte del error absoluto porque responden a preguntas distintas: el MAE dice
    cuánto se falla y el sesgo hacia dónde. Un segmento con sesgo positivo grande está recibiendo
    precios sistemáticamente altos, y eso no se ve en el MAE.
    """
    t = d.copy()
    t["real"], t["pred"] = real, pred
    t["error"] = np.abs(t["pred"] - t["real"])
    filas = []
    for nombre, columna in (("tamaño", "tamano"), ("estrellas", "estrellas"),
                            ("tipo", "tipo_alojamiento"), ("distrito", "distrito")):
        for valor, g in t.groupby(columna, dropna=False):
            if len(g) < 5:
                continue
            filas.append({
                "corte": nombre, "segmento": str(valor), "n": len(g),
                "precio_mediano": round(float(g["real"].median()), 1),
                "MAE_eur": round(float(g["error"].mean()), 1),
                "MAPE_pct": round(float((g["error"] / g["real"]).mean() * 100), 1),
                "sesgo_eur": round(float((g["pred"] - g["real"]).mean()), 1)})
    return pd.DataFrame(filas)


def comparar_global_contra_segmentado(d, X, y, mejor, global_pred, cv) -> None:
    """¿Conviene un modelo por segmento en vez de uno solo?

    Un bosque ya parte por estrellas y por tamaño: la predicción de un hotel concreto sale de las
    hojas donde cayeron los suyos, no de una media global. La pregunta es si aislar cada segmento
    en su propio modelo mejora eso, o si pesa más perder lo que cada segmento aprende de los demás.
    Con 430 filas repartidas en cuatro tamaños lo segundo es lo esperable, pero se mide en vez de
    suponerlo.
    """
    print("\n=== Modelo único frente a un modelo por segmento ===")
    print(f"  modelo único, error global: {np.mean(np.abs(global_pred - y)):.1f} EUR\n")
    for columna in ("tamano", "tipo_alojamiento"):
        acumulado, total = 0.0, 0
        for valor, idx in d.groupby(columna, dropna=False).groups.items():
            pos = d.index.get_indexer(idx)
            if len(pos) < 40:   # menos de 40 filas no dan ni para cinco pliegues honestos
                continue
            propio = cross_val_predict(clone(mejor), X.iloc[pos], y[pos], n_jobs=-1,
                                       cv=KFold(5, shuffle=True, random_state=SEMILLA))
            mae_propio = float(np.mean(np.abs(propio - y[pos])))
            mae_global = float(np.mean(np.abs(global_pred[pos] - y[pos])))
            veredicto = "mejor" if mae_propio < mae_global else "peor"
            print(f"  {columna}={str(valor)[:18]:18s} n={len(pos):3d}  "
                  f"propio {mae_propio:5.1f}  global {mae_global:5.1f}  -> el propio es {veredicto}")
            acumulado += mae_propio * len(pos)
            total += len(pos)
        if total:
            glob = float(np.mean(np.abs(global_pred - y)))
            print(f"    ponderado sobre {total} segmentables: por segmento "
                  f"{acumulado / total:.1f} EUR frente a {glob:.1f} EUR del único\n")


def main() -> None:
    d = preparar_variables(pd.read_csv(ENTRADA, dtype={"codigo_postal": str}, low_memory=False))
    d = recortar_atipicos(d)
    etiquetados = d[d[OBJETIVO].notna()].reset_index(drop=True)
    X = etiquetados[COLUMNAS]
    y = etiquetados[OBJETIVO].astype(float).to_numpy()
    print(f"Alojamientos de Barcelona: {len(d)} | con precio {len(etiquetados)} | "
          f"a estimar {int(d[OBJETIVO].isna().sum())}")

    cv = KFold(5, shuffle=True, random_state=SEMILLA)
    base = float(np.median(y))
    print(f"Referencia (mediana constante = {base:.0f} EUR): "
          f"MAE {np.mean(np.abs(y - base)):.1f} EUR")

    resultados = []
    print(f"\n{'modelo':22s} {'optimizador':18s} {'MAE_cv':>8s}")
    print("-" * 50)
    for nombre, (modelo, rejilla) in catalogo_modelos().items():
        for nombre_buscador, buscador in buscadores(envolver(modelo), rejilla, cv).items():
            buscador.fit(X, y)
            resultados.append({"modelo": nombre, "optimizador": nombre_buscador,
                               "MAE_cv_eur": round(-buscador.best_score_, 2),
                               "mejores_parametros": str(buscador.best_params_),
                               "_estimador": buscador.best_estimator_})
            print(f"{nombre:22s} {nombre_buscador:18s} {-buscador.best_score_:8.1f}")

    comparativa = pd.DataFrame(resultados).sort_values("MAE_cv_eur")
    ganador = comparativa.iloc[0]
    mejor = clone(ganador["_estimador"])
    print(f"\nGana {ganador['modelo']} con {ganador['optimizador']}")
    print(f"  {ganador['mejores_parametros']}")
    comparativa.drop(columns="_estimador").to_csv(SALIDA_COMPARATIVA, index=False,
                                                  encoding="utf-8")

    # Cinco repartos distintos: la dispersión entre ellos es el margen de la estimación.
    repetida = -cross_val_score(mejor, X, y, scoring="neg_mean_absolute_error", n_jobs=-1,
                                cv=RepeatedKFold(n_splits=5, n_repeats=5, random_state=SEMILLA))
    print("\n=== Error con validación cruzada repetida (5 pliegues x 5 repeticiones) ===")
    print(f"  MAE {repetida.mean():.1f} EUR  (desviación {repetida.std():.1f}; "
          f"peor pliegue {repetida.max():.1f}, mejor {repetida.min():.1f})")
    print(f"  sobre una mediana de {base:.0f} EUR = "
          f"{repetida.mean() / base:.0%} de error relativo")

    pred = cross_val_predict(mejor, X, y, cv=cv, n_jobs=-1)
    segmentos = error_por_segmento(etiquetados, y, pred)
    segmentos.to_csv(SALIDA_SEGMENTOS, index=False, encoding="utf-8")
    print("\n=== Error fuera de muestra por segmento ===")
    for corte in segmentos["corte"].unique():
        print(f"\n  -- por {corte} --")
        print(segmentos[segmentos["corte"] == corte].drop(columns="corte").to_string(index=False))

    acierto_de_banda(y, pred)
    comparar_global_contra_segmentado(etiquetados, X, y, mejor, pred, cv)

    cobertura = cobertura_de_entrenamiento(d)
    cobertura.to_csv(SALIDA_COBERTURA, index=False, encoding="utf-8")
    print("\n=== Qué se estima sin ejemplos comparables ===")
    for corte in cobertura["corte"].unique():
        t = cobertura[cobertura["corte"] == corte].drop(columns="corte")
        if (t["veredicto"] != "suficiente").any():
            print(f"\n  -- por {corte} --")
            print(t.to_string(index=False))

    mejor.fit(X, y)
    d["precio_noche_estimado"] = np.round(mejor.predict(d[COLUMNAS]), 2)
    d["precio_es_estimado"] = d[OBJETIVO].isna()
    d["precio_noche_final"] = d[OBJETIVO].fillna(d["precio_noche_estimado"])
    d["banda_precio"] = asignar_banda(d["precio_noche_final"])
    d["modelo_precio"] = f"{ganador['modelo']}+{ganador['optimizador']}"
    d["mae_modelo_eur"] = round(float(repetida.mean()), 1)

    # Marca las estimaciones que descansan en pocos ejemplos, para que la web pueda no publicarlas.
    apoyo = (d[d[OBJETIVO].notna()].groupby(["tipo_alojamiento", "tamano"], dropna=False)
             .size().rename("apoyo"))
    d["apoyo_entrenamiento"] = (d.set_index(["tipo_alojamiento", "tamano"]).index.map(apoyo)
                                .fillna(0).astype(int))
    d["estimacion_fiable"] = ~d["precio_es_estimado"] | (d["apoyo_entrenamiento"] >= 10)
    d["apoyo_estimacion"] = np.select(
        [~d["precio_es_estimado"], d["apoyo_entrenamiento"] == 0,
         d["apoyo_entrenamiento"] < 10, d["apoyo_entrenamiento"] < 30],
        ["observado", "sin_apoyo", "escaso", "justo"], default="suficiente")
    d.to_csv(SALIDA, index=False, encoding="utf-8")

    print(f"\nBandas: {d['banda_precio'].value_counts().reindex(ETIQUETAS_BANDA).to_dict()}")
    no_fiables = int((~d["estimacion_fiable"]).sum())
    print(f"Estimaciones marcadas como poco fiables: {no_fiables}")
    print(f"Apoyo de cada estimacion: {d['apoyo_estimacion'].value_counts().to_dict()}")

    est = d.loc[d["precio_es_estimado"], "precio_noche_final"]
    obs = d.loc[~d["precio_es_estimado"], "precio_noche_final"]
    print(f"\nObservado: n={len(obs)} mediana {obs.median():.0f} EUR "
          f"[{obs.quantile(.1):.0f}-{obs.quantile(.9):.0f}]")
    print(f"Estimado : n={len(est)} mediana {est.median():.0f} EUR "
          f"[{est.quantile(.1):.0f}-{est.quantile(.9):.0f}]")
    print(f"\nGuardado en {SALIDA.relative_to(RAIZ)}")
    print(f"           {SALIDA_SEGMENTOS.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
