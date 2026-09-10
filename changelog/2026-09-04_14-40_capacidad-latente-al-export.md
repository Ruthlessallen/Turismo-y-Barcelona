# La capacidad latente llega a la web

**Fecha:** 2026-09-04 14:40
**Tipo:** Feature
**Requisitos:** M-08 (oferta anunciada frente a licencias)

## Qué se hizo

Las 293 viviendas con licencia vigente y sin actividad reciente ya existían en
`gold/airbnb_capacidad_latente.csv`, pero `export_mapa.py` no las miraba y no llegaban al
frontend. Ahora se publican.

### Dónde van

En `airbnb_por_barrio.json`, dentro de un objeto `latente` **al lado de `anuncios`, nunca dentro**:

```json
{
  "barrio": "la Dreta de l'Eixample",
  "anuncios": 1015,
  "latente": { "viviendas": 43, "plazas": 217, "recientes": 31 }
}
```

Y el agregado de ciudad en `resumen.json`:

```json
"capacidad_latente": { "viviendas": 293, "plazas": 1534, "recientes": 203, "barrios": 38 }
```

Comprobado que las 293 del CSV cuadran con la suma de los 64 barrios del JSON.

### Por qué `recientes` va aparte

Separa las **203** que dejaron de anunciarse en 2024 o después de las licencias dormidas desde hace
una década. Ante la pregunta de si esa vivienda puede volver al mercado no son lo mismo, y un único
número de 293 las mezclaría sin que el lector pudiera deshacer la mezcla.

### Por qué no suma a `anuncios`

Porque no es oferta anunciada. Sumarla afirmaría que hay 7.127 pisos turísticos en Airbnb, y lo que
hay son 6.834 anunciados más 293 con la licencia viva que hoy no se anuncian. Son dos hechos
distintos y el JSON los mantiene separados para que el frontend decida si los junta y cómo.

## Qué se modificó

- `pipeline/export/export_mapa.py` — lee `airbnb_capacidad_latente.csv`, agrega por barrio, añade
  `latente` a cada fila y `capacidad_latente` al resumen.
- `data/exports/mapa/airbnb_por_barrio.json` y `resumen.json` — regenerados.
- `docs/supuestos.md` — B5 recoge dónde acaban publicadas.

## Granularidad

Se mantiene la regla de `prd.md`: el export es agregado por barrio. Comprobado que las filas
publicadas no contienen `id`, `host_id`, `host_name` ni coordenadas.
