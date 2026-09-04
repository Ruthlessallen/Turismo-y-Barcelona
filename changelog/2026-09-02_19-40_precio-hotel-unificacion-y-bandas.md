# Precio por hotel: un solo pipeline, anclaje oficial y banda económica

**Fecha:** 2026-09-02 19:40
**Tipo:** Refactor + Feature + Fix
**Requisitos:** Apoyo a M-06 (absorción hotelera) — la banda económica es la variable de
sustitución entre alojamiento reglado y VUT

## Qué se hizo

Se unifican en dos scripts los cuatro que construían el dataset de hoteles de Barcelona por
caminos distintos, se ancla el precio contra la estadística oficial y se publica una banda
económica por establecimiento.

### 1. Un solo preparador

`preparar_hoteles_bcn.py` sustituye a `preparar_hoteles_bcn_analisis.py` y
`preparar_hoteles_bcn_imputacion.py`, que producían el mismo dataset de 768 filas sin coincidir:
**306 de 768 discrepaban en la categoría** y una rama perdía 322 coordenadas que la otra sí tenía.

| | Antes (rama de imputación) | Ahora |
|---|---|---|
| Coordenadas | 446 | **763** (99,3%) |
| Barrio | por moda del CP | **763 por punto en polígono** |
| `categoria_num` nula | 306 | — (sustituida por `estrellas` + `tipo_alojamiento`) |
| Cadenas detectadas | 104 en 16 grupos | **132 en 25 grupos** |

### 2. Rescate de precios en segundo pase

`rescatar_precios_hoteles.py` recupera hoteles que el primer cruce dejó fuera. Resuelve el
emparejamiento como **asignación global** (`linear_sum_assignment`), no por vecino más cercano:
cada ficha se usa como mucho una vez.

**451 de 768 con precio observado (58,7%)**, frente a 430. De los 21 rescatados, 14 automáticos y
7 aprobados a mano — cuatro de estos últimos eran cambios de marca que ninguna regla detectaba
(`Hosteria Grau` → `Eco Boutique Hostal Grau`, `HOTEL BRICK (antigo Hotel Climent)` → `Hotel Brick
Barcelona`).

### 3. Anclaje contra el ADR oficial

`preparar_adr_por_categoria.py` incorpora la tarifa media diaria del INE por categoría, 2013-2026.
El raspado queda validado contra una fuente independiente:

| Categoría | Mediana raspada | ADR septiembre | Desvío |
|---|---|---|---|
| 1-2 estrellas y plata | 155 € | 139 € | +12% |
| 3 estrellas | 161 € | 163 € | −1% |
| 4 estrellas | 210 € | 194 € | +8% |
| 5 estrellas | 351 € | 362 € | −3% |

Y aporta la estacionalidad: **septiembre está un 16% sobre la media anual**, así que se añade
`precio_noche_anual`. La corrección mueve de banda a 124 hoteles, todos hacia abajo.

### 4. Modelo de imputación

`modelar_precios_hoteles_bcn.py` compara 7 modelos × 2 buscadores (antes 2 modelos y ningún
optimizador), sobre `precio_noche_anual`.

**MAE 41,1 € ± 8,3**, un 27% sobre la mediana de 150 €, frente a los 58,5 € de predecir siempre la
mediana. Banda exacta 65,2% y banda exacta o vecina **98,9%**.

## Qué se modificó

**Nuevos**
- `pipeline/transform/preparar_hoteles_bcn.py`
- `pipeline/transform/rescatar_precios_hoteles.py`
- `pipeline/transform/preparar_adr_por_categoria.py`
- `pipeline/transform/modelar_precios_hoteles_bcn.py`
- `docs/observaciones-datos.md`
- `data/raw/ine/portaldades_adr_por_categoria_2013_2026.csv`

**Sustituidos** (pendientes de mover a `scraps/`)
- `preparar_hoteles_bcn_analisis.py`, `preparar_hoteles_bcn_imputacion.py`,
  `imputar_precios_hoteles_bcn.py`, `unificar_precios_y_censo.py`

## Por qué

### Errores corregidos

**El precio estaba a la mitad.** Los scripts anteriores aplicaban `precio / 2.0` sobre una columna
que ya venía por noche: Google devuelve `nightly` y Booking trae `precio_noche_eur` calculado sobre
su estancia de dos noches. La mediana hotelera de Barcelona quedaba en 86 € en vez de 174 €, y el
modelo entrenaba sobre ese objetivo.

**La categoría no es una escala.** Hostales y apartaments turístics figuraban como 0,5 y 0,0 de una
variable continua de estrellas, lo que afirma que un AT vale menos que un hostal y este menos que
una estrella. Además el modelo hacía `fillna(0.0)`, dejando indistinguibles los 293 hostales de los
13 AT. Ahora van `estrellas` —nula donde no aplica— y `tipo_alojamiento` como categórica.

**Codificación desalineada.** `get_dummies(drop_first=True)` se calculaba por separado sobre el
subconjunto con precio y sobre el total: si el nivel descartado no coincidía, esos alojamientos
quedaban a cero y el modelo los leía como la categoría de referencia, sin que nada lo delatara. La
codificación vive ahora dentro del `Pipeline`.

**Distancia al centro con geometría plana.** `sqrt(dlat² + dlon²) × 111` da por hecho que un grado
de longitud mide lo mismo que uno de latitud. A 41,4° son 83 km y no 111: el eje este-oeste salía
inflado un tercio, justo el eje en que se estira la ciudad. Sustituido por haversine.

**Un error medido sobre una partición afortunada.** Una versión intermedia apartaba 86 casos y
anunciaba 40,6 € de error cuando la validación cruzada sobre los mismos datos daba 57 €. Se informa
ahora con validación cruzada repetida y su dispersión.

**Dos filas valían 13 € de error.** `Attica21 Barcelona Mar` figuraba a 4.090 €/noche siendo un
cuatro estrellas de 75 habitaciones. Recortando los atípicos al quíntuplo de la mediana de su
categoría, el MAE bajó de 56,3 a 43,1 € y la desviación entre pliegues de 18,7 a 7,0: la
inestabilidad no era del modelo, era de esas dos filas cayendo en un pliegue u otro.

### Limitaciones que quedan documentadas

**La banda `€` no se puede imputar.** De 52 hoteles realmente por debajo de 100 €, el modelo acierta
2; los otros 50 los sitúa en `€€`. Solo 54 filas del entrenamiento bajan de ese umbral y el modelo
aplasta hacia el centro. La columna `precio_es_estimado` permite publicar `€` solo cuando es
observado.

**Cinco estimaciones sin apoyo suficiente**, marcadas en `apoyo_estimacion`: pensiones (6 por
estimar con 2 ejemplos), residencias (3 con 4) y apartaments turístics (5 con 8).

**Un hotel no tiene un precio.** Comprobado a mano sobre Hostemplo: 138 a 219 € según habitación y
fecha dentro de la misma quincena, un ±22% que pone suelo a lo que cualquier método puede lograr
(ver `docs/observaciones-datos.md`).
