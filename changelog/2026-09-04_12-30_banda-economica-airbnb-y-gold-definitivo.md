# Banda económica de Airbnb y cierre del gold

**Fecha:** 2026-09-04 12:30
**Tipo:** Feature + Fix
**Requisitos:** M-06 (absorción hotelera) y M-08 (oferta anunciada frente a licencias)

## Qué se hizo

`data/gold/airbnb_para_web.csv` queda cerrado como el dataset definitivo de Airbnb para la web:
6.834 viviendas de uso turístico, las **6.834 con banda económica** (antes 6.613, un 96,8%).

### Banda económica sobre el precio completo

La celda 33 ponía banda solo sobre los precios observados. Las celdas nuevas 41 y 42 la rehacen
sobre `precio_plaza_final`, que ya incorpora los 221 estimados por el modelo, y enfrentan el
resultado a los 767 establecimientos reglados en la misma escala.

| Banda | Reglado (767) | VUT en Airbnb (6.834) |
|---|---:|---:|
| € | 1,8% | 26,8% |
| €€ | 32,9% | 50,2% |
| €€€ | **53,6%** | 20,9% |
| €€€€ | 11,7% | 2,2% |

Mediana por plaza y noche, equivalente anual: **77,7 € el reglado, 51,8 € la VUT**. El **84% de las
VUT está por debajo de la mediana reglada**, y la banda `€` es casi enteramente suya: 1.831
viviendas frente a 14 establecimientos reglados. Solo el 3% de las bandas descansa en un precio
estimado, y ninguna estimación alcanza `€€€€` — el modelo no llega a los extremos.

### La unidad, verificada

Las dos fuentes son **precio por noche y por plaza disponible**, no por ocupante. Comprobado sobre
el volcado: `price` coincide con `price_quote_price_per_night` (ratio 1,00 en 13.355 anuncios) y
`price_quote_raw` declara `"currency": "EUR"` en 13.380 cotizaciones — la moneda deja de ser una
suposición y pasa a estar probada.

### Limitación declarada, no corregida

`cleaning_fee` viene **vacío en las 13.662 cotizaciones**: Inside Airbnb no lo captura. Como en
Airbnb la limpieza es un cargo por estancia, en las de 1 noche —3.540 cotizaciones, el grupo mayor—
pesa mucho más que en las de 31. El precio de hotel sí incluye todo salvo la tasa turística.

**No se corrige, y esa es la decisión.** El dato no permite saber quién cobra la limpieza aparte y
quién la lleva ya dentro de la tarifa; aplicar un importe común a todos sería falso para los
segundos. Se publica la tarifa anunciada tal cual, con la limitación escrita: en estancias cortas,
que son las que compiten con el hotel, la banda de Airbnb puede quedar por debajo de lo que se
acaba pagando.

## Qué se modificó

**`pipeline/notebooks/revisar_airbnb_v2.ipynb`**
- Celdas 41 y 42: banda sobre el precio completo y comparación con el alojamiento reglado.
- Tres rutas relativas (`data/raw/...`) pasan a `RAIZ`: el cuaderno solo se ejecutaba a mano desde
  la raíz del repo, y `nbconvert` sitúa el directorio de trabajo en la carpeta del cuaderno.
- `kernelspec` anotado (`turismo-bcn`).

**Entorno**
- Kernel `turismo-bcn` registrado desde `.venv`. El `python3` del entorno arrancaba `"python"` a
  secas —el del sistema, sin LightGBM— y además un `python3` de nivel de usuario le ganaba la
  precedencia. Ninguno de los dos tenía las dependencias del modelo.

**`docs/data-model.md`**
- La ficha `oferta_airbnb` describía un esquema previsto cuyos nombres de campo ya no eran los del
  CSV real (`listing_id`, `tipo_propiedad`, `metodo_match`...). Sustituida por el diccionario de
  las 43 columnas que existen, agrupado en identificación, alojamiento, licencia y precio.

**Regenerados**: `docs/criba.md`, `docs/linaje.md`, `data/exports/mapa/`.

## Por qué

**El cuaderno nunca se había ejecutado entero de una tirada.** Se construyó celda a celda en
sesiones interactivas, y eso ocultaba tres dependencias del estado del intérprete. Ejecutado ahora
de principio a fin: 42 de 42 celdas, sin errores.

**Un anuncio que parecía sobrar y no sobra.** El único `Shared room` es una cama de albergue
(`GG Hostel`, 14 plazas, 4,5 €/plaza) que declara un HUTB. La primera lectura fue excluirlo por
coherencia con la regla de las habitaciones de hotel. Es al revés: la celda 32 admite a propósito
las habitaciones que declaran HUTB, porque un HUTB ampara la cesión del alojamiento completo y
usarlo para vender una cama es exactamente la irregularidad que el criterio quiere conservar
visible. Se queda.
