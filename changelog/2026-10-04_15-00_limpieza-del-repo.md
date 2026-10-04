# Limpieza del repo y mapa de la documentación

**Fecha:** 2026-10-04 15:00
**Tipo:** Mantenimiento

## Por qué

Tras un mes sin tocar el proyecto, había restos de plantilla, un script roto y una definición de
bandas duplicada.

## Qué desaparece

- `web/public/{next,vercel,globe,file,window}.svg`: iconos del starter de Next, sin ninguna referencia.
- `docs/criba.svg` y `docs/criba-1.svg` (byte a byte idénticos) y `docs/linaje-1.svg`: ningún
  documento ni script los usa; los generadores escriben `.md`, no SVG.
- `scripts/auditar_web.py`: fallaba con `KeyError: 'escenarios'` desde que el JSON se anida por momento.

## Qué cambia

- `pipeline/gold/modelar_precios_hoteles_bcn.py` ya no tiene sus propios cortes de banda ni
  `asignar_banda()`: importa `CORTES_HABITACION`, `ETIQUETAS` y `por_habitacion` de `bandas.py`,
  que es la definición única que el propio módulo declara. Los cortes son los mismos (100/175/300).
  **No se ha vuelto a ejecutar el modelo de precios** (reentrena con Optuna): comprobado solo que el
  fichero parsea y que `por_habitacion` etiqueta bien los cortes.
- `docs/README.md`: índice de una página — «si quieres saber X, abre Y».

## Se queda, a propósito

`restauracion.json`, `hoteles.json`, `airbnb_por_barrio.json` y `vut_por_barrio.json`: nadie los lee
hoy, pero son los datos de las páginas pendientes (`/hoteles`, dashboard).
