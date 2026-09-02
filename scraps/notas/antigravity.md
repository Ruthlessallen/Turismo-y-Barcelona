# Resumen de avances del proyecto y decisiones del sistema

Este documento sintetiza las tareas, correcciones de errores, decisiones de arquitectura de datos y análisis normativos realizados en el repositorio **Turismo-BCN**.

---

## 1. Resolución de ruta dinámica y precarga de datos

### Diagnóstico del problema inicial
- Los cuadernos fallaban al ejecutarse en VS Code debido a diferencias en el directorio de trabajo actual (`cwd`). Mientras que el entorno Jupyter clásico ejecuta desde la carpeta del cuaderno (`pipeline/notebooks`), VS Code inicia el kernel desde la raíz del proyecto.
- La ejecución dinámica de operaciones `.merge()` dentro de la primera celda del cuaderno producía lentitud y duplicidad de lógica.

### Solución aplicada
- Se implementó un bucle dinámico de búsqueda del directorio raíz:
  ```python
  from pathlib import Path

  RAIZ = Path.cwd()
  while not (RAIZ / "data").exists() and RAIZ != RAIZ.parent:
    RAIZ = RAIZ.parent
  if not (RAIZ / "data").exists():
    RAIZ = Path("../..")
```
- Se trasladaron todas las transformaciones y cruces a scripts en `pipeline/transform/`, permitiendo que la celda 1 de cada cuaderno cargue directamente los archivos consolidados desde `data/processed/`.

---

## 2. Pipeline de transformación de datos

### `pipeline/transform/unificar_precios_y_censo.py`
- **Función**: `unificar_censo_con_precios()`
- **Qué hace**: Realiza el cruce entre el censo oficial del Registro de Turismo de Cataluña y las ofertas raspadas de hoteles.
- **Salida**: `data/processed/hoteles_unificados_y_precios.csv` (1.563 registros provinciales).

### `pipeline/transform/preparar_hoteles_bcn_analisis.py`
- **Función**: `preparar_dataset_hoteles_bcn()` y `map_cat(row)`
- **Qué hace**:
  1. Filtra los datos para el municipio de Barcelona.
  2. Consolida las coordenadas geográficas (`lat_final`, `lon_final`) combinando las del censo y las geocodificadas con el ICGC.
  3. Convierte las tarifas a precio por noche dividiendo entre 2.
  4. Asigna código postal y recupera el barrio mediante OpenData BCN y moda por código postal.
  5. Calcula la distancia euclídea aproximada a Plaça Catalunya (41.3870, 2.1700).
  6. Aplica el mapeo numérico continuo de categorías (`categoria_num`).
- **Salida**: `data/processed/hoteles_bcn_analisis_preparado.csv` (768 alojamientos en Barcelona ciudad).

---

## 3. Calidad de datos y auditoría de nulos

Se diagnosticó que los elevados porcentajes de nulos (~42% a 60%) observados inicialmente en los reportes del cuaderno 08 provenían de incluir variables crudas intermedias (`lat`, `lon`, `lat_geo`, `lon_geo`, `addresses_neighborhood_name`, `piso`, `puerta`).

Al auditar exclusivamente las variables finales consolidadas, la cobertura real en Barcelona es:
- **Código postal (`codigo_postal`)**: 99.87% cobertura (1 nulo).
- **Barrio (`barrio`)**: 99.74% cobertura (2 nulos).
- **Geolocalización (`lat_final` / `lon_final`)**: 97.66% cobertura (18 nulos).
- **Capacidad (`plazas` / `habitaciones`)**: 99.87% cobertura (1 nulo).
- **Categoría (`categoria_num`)**: **100% cobertura (0 nulos)**.
- **Precio por noche (`precio_noche`)**: 61.98% disponibilidad (476 con precio raspado directo, 292 pendientes de imputación).

---

## 4. Auditoría de licencias y marco normativo (Decreto 75/2020)

### Desglose de licencias por ámbito geográfico
- **`HB-` (Hoteles de Barcelona)**: Licencia de hospedaje hotelero. Hay 1.301 en la provincia y 754 en Barcelona ciudad.
- **`HCC-` (Hostales y residencias de la comarca)**: Hay 141 en la provincia y **0 en Barcelona ciudad**.
- **`ATB-` (Apartamentos turísticos de Barcelona)**: Hay 101 en la provincia y **13 en Barcelona ciudad** (los 88 restantes están en municipios como Castelldefels, L'Hospitalet, Sitges, Badalona, etc.).
- **`ATCC-` (Apartamentos turísticos comarcales)**: Hay 19 en la provincia y **0 en Barcelona ciudad**.

### Clasificación de categorías sin estrellas (`No aplica` y `Sense categoritzar`)
Según el **Decreto 75/2020 de turismo de Cataluña**:
1. **Apartamentos turísticos (`ATB-`)**: Figuran como `Sense categoritzar` al no usar estrellas. Se asignan a `categoria_num = 0.0` (13 alojamientos en Barcelona).
2. **Hostales y pensiones (`HB-` sin estrellas)**: Por ley en Cataluña, las estrellas se otorgan únicamente a hoteles/apariciohóteles. Hostales y pensiones no llevan estrellas, por lo que la administración registra su categoría como `No aplica`. Se asignan a `categoria_num = 0.5` (293 alojamientos en Barcelona).
   - Al inspeccionar la razón social y capacidad de estos 293 alojamientos, 88 incluyen explícitamente "Hostal" o "Pensión", 28 son "Residencias/Suites/Rooms", 24 son "Hoteles/Aparthoteles" y 148 son marcas familiares con una media reducida de 12 a 18 habitaciones.
3. **Hoteles con estrellas (`1.0` a `5.0`)**: Mapeados de 1 a 5 estrellas y Gran Luxe (462 alojamientos en Barcelona).

---

## 5. Cuadernos actualizados en la tubería

1. **`07_revision_hoteles_unificados_y_precios.ipynb`**:
   - Carga directa de `hoteles_unificados_y_precios.csv`.
   - Incorpora auditoría de licencias (`HB`, `HCC`, `ATB`, `ATCC`) provincial vs municipal.
   - Análisis detallado de razones sociales y normativa para establecimientos `No aplica`.
2. **`08_imputacion_precios_hoteles_bcn.ipynb`**:
   - Estructurado en 6 secciones exploratorias con 0 operaciones de `.merge()` en la celda 1.
   - Gráficos de dispersión, boxplots de outliers (IQR), histogramas de distribución real vs $\log(1 + \text{precio\_noche})$, matriz de correlaciones (Pearson/Spearman) y ANOVA $\eta^2$ (donde Código Postal explica un 17.5% de la varianza del precio y Barrio un 15.9%).
