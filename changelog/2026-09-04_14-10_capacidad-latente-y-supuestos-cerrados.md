# Capacidad latente, y dos supuestos cerrados por comprobación

**Fecha:** 2026-09-04 14:10
**Tipo:** Feature + Documentación
**Requisitos:** M-08 (oferta anunciada frente a licencias)

## Qué se hizo

Se pusieron a prueba dos criterios de la criba que hasta ahora se daban por buenos sin medir. Uno
se mantiene igual, el otro también, pero de él sale una cifra nueva que antes se perdía.

### 1. Capacidad latente: 293 viviendas, 1.534 plazas

El filtro de actividad descarta 876 anuncios sin reseñas desde septiembre de 2025. De ellos,
**293 (33%) tienen la licencia en el registro oficial**: existen, están vigentes, y la eliminación
de 2028 las alcanza igual que a las 6.834 activas. Simplemente no se anuncian hoy en Airbnb.

Antes desaparecían del análisis sin dejar rastro. La celda 43 del cuaderno las cuenta aparte, sin
tocar el denominador de nada, y las escribe en `data/gold/airbnb_capacidad_latente.csv`.

| Año de la última reseña | Viviendas | Plazas |
|---|---:|---:|
| 2025 | 131 | 665 |
| 2024 | 72 | 419 |
| 2023 | 25 | 142 |
| 2022 o antes | 65 | 308 |

Se concentran donde está el resto de la oferta: la Dreta de l'Eixample 43, la Sagrada Família 29,
el Poble Sec 20.

**Qué se puede afirmar y qué no.** Que la licencia existe y que la vivienda no está en Airbnb hoy.
No que esté vacía: puede estar en otra plataforma, en alquiler de temporada o en uso propio.

### 2. B5: quedarse con los de licencia vigente habría sido circular

Se evaluó sustituir el proxy de actividad por «tiene licencia vigente». El reparto lo desaconseja
solo:

| | Descartados por inactividad | Los 6.834 que entran |
|---|---:|---:|
| Declaran HUTB | 37% | 86% |
| Consta en el registro | 33% | 74% |

Readmitiría 293 con licencia y **ni uno sin licencia**, subiendo mecánicamente el porcentaje de
regulares — que es justo la cifra que el proyecto mide. El filtro decidiría quién entra usando la
misma variable cuyo reparto se quiere medir.

Aparte, el registro dice que la licencia existe, no que el piso se alquile: 239 de los 876 tienen
su última reseña en 2023 o antes.

### 3. B2: afinar por barrio no discrimina

Se evaluó rescatar las habitaciones sin HUTB cuyo anfitrión declara uno en otro anuncio **del mismo
barrio**. Cumplen 20, de 7 anfitriones. Pero esos anfitriones tienen carteras de 13 a 17 licencias
repartidas en 6 a 8 barrios: para ellos, coincidir de barrio **es casi seguro por azar**. El
criterio no discrimina, y se apoyaría además en la variable menos fiable del conjunto, porque la
asignación individual de barrio falla el 12%.

Son 20 sobre 6.834 (0,3%) y una licencia HUTB es de una vivienda, no de un anfitrión. Se mantiene
el criterio, ahora documentado como comprobado y descartado en vez de asumido.

## Qué se modificó

- `pipeline/notebooks/revisar_airbnb_v2.ipynb` — celda 43. Ejecutado entero: 43 de 43 celdas.
- `data/gold/airbnb_capacidad_latente.csv` — nuevo.
- `docs/supuestos.md` — B2 y B5 con la comprobación y su resultado.
- Regenerados `docs/linaje.md` y `docs/criba.md`.

## Por qué

Un supuesto documentado como «lo asumimos» y otro documentado como «lo medimos y sale esto» tienen
un valor muy distinto ante quien audite el trabajo. Los dos criterios siguen siendo los mismos; lo
que cambia es que ahora se sabe cuánto se pierde por mantenerlos.
