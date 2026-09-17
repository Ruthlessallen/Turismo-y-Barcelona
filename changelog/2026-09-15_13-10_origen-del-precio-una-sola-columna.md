# El origen del precio, en una sola columna

**Fecha:** 2026-09-15 13:10
**Tipo:** Refactor de datos
**Requisitos:** M-06 (absorción hotelera), integridad de lo publicado

## Por qué

Parecía que el precio de un hotel llegaba por tres o cuatro caminos distintos —Airbnb, raspado,
modelo, imputación— y no había forma de saber cuál mandaba. Se comprobó contra el dato y **son
dos**: raspado y modelo. "ML" e "imputación" son lo mismo, y **Airbnb no aporta ni un solo precio
de hotel**: lo único que cruza de ese lado es la geometría de barrios en `preparar_hoteles_bcn.py`.
La comparación Google-vs-Airbnb de cuatro apartaments turístics fue una comprobación manual
(`observaciones-datos.md`), no un camino de datos.

Lo confuso no era el pipeline: eran **siete columnas describiendo la procedencia de un número** —
`origen_precio` (con otros valores), `metodo_cruce`, `precio_es_estimado`, `apoyo_estimacion`,
`estimacion_fiable`, `modelo_precio`, `mae_modelo_eur`.

## Qué se hizo

### `gold/alojamientos_reglados.csv`

`precio_es_estimado` y `apoyo_estimacion` se sustituyen por **`origen_precio`**:

| Valor | Cuántos |
|---|---|
| `observado` | 451 |
| `estimado` | 312 |
| vacío | 800 |

Los siete matices siguen intactos en `hoteles_bcn_precio_estimado.csv`, que es su sitio: sirven
para auditar el cruce y el modelo, no para leer un mapa.

### El corte de las estimaciones sin apoyo sube a gold

Las 5 estimaciones con `apoyo_estimacion = escaso` pierden precio y banda en
`preparar_alojamientos_provincia.py`, no en `export_mapa.py`. Estaba bien resuelto pero en el sitio
equivocado: dependía de que el export se acordara, y cualquier consumidor nuevo del CSV se lo
saltaba sin enterarse.

**Efecto:** 763 establecimientos con banda en vez de 768.

### Lo que arrastró aguas abajo

Cinco hoteles menos con banda cambian el reparto de 2028:

| | Antes | Ahora |
|---|---|---|
| Plazas regladas | 84.314 | 84.058 |
| Plazas libres tras ocupación | 27.092 | 27.010 |
| Sin sitio | 2.975 | **3.057** |
| Flujos publicados | 891 | 887 |
| Julio (ocupación 79,1%) | 12.437 | **12.490** |

Actualizados los números escritos a mano en `web/app/page.tsx` y en `docs/fuentes.md`.

## Verificación

Ejecutados en este orden, todos sin error:

```
preparar_alojamientos_provincia.py  → origen del precio: {nan: 800, 'observado': 451, 'estimado': 312}
modelar_sustitucion.py              → 320 filas, 887 flujos, sin sitio 3.057
export_mapa.py                      → con_banda 758, observada 451, estimada 307
```

(La diferencia entre 763 con banda en gold y 758 en el export son los 5 sin coordenada: el export
solo publica lo que tiene punto.)

`data/exports/mapa/*.json` copiado a `web/public/data/mapa/`.

**No se ha ejecutado el build de la web.**

## Documentación

- `docs/data-model.md` — tabla publicable actualizada, con el porqué de la columna única
- `docs/fuentes.md` — tabla de procedencias y la aclaración de que Airbnb no da precios de hotel
- `docs/linaje.md` y `docs/criba.md` — regenerados

## Queda pendiente

La web todavía **no enseña** que el 41% de los precios de hotel está estimado frente al 3% de
Airbnb. La columna ya viaja en `hoteles.json` como `origen`; falta el distintivo visual.
