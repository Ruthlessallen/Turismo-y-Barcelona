# Restauración en el mapa: dónde están y a quién le cambia la clientela

**Fecha:** 2026-09-16 10:30
**Tipo:** Feature
**Requisitos:** M-06 (absorción), paso 1 y paso 4 de `web-checklist.md`

## Qué se hizo

Botón **Restauración** en el panel, con dos vistas en verde:

- **Dónde están** — 9.479 bares y restaurantes del censo, por barrio
- **Comensales que ganan o pierden** — turistas que duermen a menos de 200 m de esos locales, hoy
  frente a 2028

## El modelo: quién cena dónde

Cada turista alojado reparte su visita **a partes iguales** entre los locales que tiene a 200 m.
No es una afirmación sobre el turismo en general —quien duerme en Sants va a las Ramblas, y eso
pasa mucho— sino sobre las comidas ordinarias: el desayuno y la cena al volver. Nadie cruza la
ciudad tres veces al día para comer.

**El reparto es a partes iguales porque es lo único que el dato sostiene.** No sabemos qué bar
prefiere nadie, y ponderar por distancia dentro de 200 m sería inventar una preferencia con
decimales de precisión falsa.

**200 m y no otra cifra:** deja una mediana de 44 locales por hotel y solo 5 hoteles sin ninguno
—esos van al más cercano, sea cual sea la distancia, porque dejarlos fuera diría que sus turistas
no cenan. A 150 m son 7 hoteles huérfanos; a 400 m la «cercanía» deja de serlo.

**El barrio que cuenta es el del local, no el del hotel.** Un hotel pegado al límite alimenta bares
del barrio de al lado, y esa fuga es justo lo que un agregado por barrio del hotel no enseña.

## El hallazgo que cambió el diseño

**La barra de precio/ubicación no mueve la restauración, y no es un fallo.** La demanda (30.067
plazas) supera a la capacidad libre (27.008), así que los 757 hoteles se llenan en los cinco
escenarios: la barra decide **quién** va a cada hotel, no **cuántos** se llenan.

Verificado: `plazas_colocadas` y `hoteles_usados` son idénticos en los cinco escenarios.

La idea original era que la barra moviera también esta capa. Publicar cinco copias idénticas bajo
un control que no las mueve daría a entender una sensibilidad que no existe, así que el dato se
exporta una sola vez y el panel dice por qué la barra está de más aquí. Solo variaría con una
ocupación de partida más baja —en noviembre, al 55,6%, sobrarían plazas— y ahí sí decidiría la
preferencia del turista.

Lo que sí dice algo es **hoy frente a 2028**: 40 barrios pierden comensales y 25 ganan.

| Barrio | Locales | Hoy | En 2028 | Cambio |
|---|---|---|---|---|
| la Sagrada Família | 353 | 2.336 | 199 | **−2.137** |
| la Vila de Gràcia | 437 | 1.889 | 369 | −1.520 |
| Sant Antoni | 349 | 1.907 | 511 | −1.396 |
| el Raval | 410 | 1.432 | 2.687 | **+1.255** |
| el Barri Gòtic | 327 | 1.268 | 2.330 | +1.063 |

## Color

Verde para restauración, porque el azul ya significa «gana turistas» en la vista de saldo y el
mismo color no puede querer decir dos cosas.

Para el cambio, divergente **verde y morado**, no verde y rojo: verde-rojo es justo la pareja que
no distingue la mayoría de las personas daltónicas, y aquí el signo es toda la información.

## Qué cambió

| Archivo | Cambio |
|---|---|
| `gold/modelar_sustitucion.py` | `vecindad()` y `agregar_restauracion()`; nueva salida `restauracion_presion_2028.csv` |
| `export/export_mapa.py` | `exportar_restauracion_2028()` → `restauracion_2028.json` |
| `web/app/lib/tipos.ts` | `BarrioRestauracion` |
| `web/app/components/MapaBarrios.tsx` | Medidas `locales` y `cambio`, rampas verdes, tooltip propio |
| `web/app/page.tsx` | Botón de Restauración, detalle del barrio, leyendas |

## Verificación

```
modelar_sustitucion.py  → restauracion_presion_2028.csv (73 barrios; no varía por escenario)
export_mapa.py          → restauracion_2028 {'barrios': 73, 'ganan': 25, 'pierden': 40}
tsc --noEmit            → sin errores
```

En local, sin errores de consola: las dos vistas pintan, el detalle del barrio responde
(Diagonal Mar: 108 locales, 380 hoy, 998 en 2028, +618) y la nota de la barra aparece solo en
estas dos vistas.

**No se ha ejecutado el build de producción.**

## Aparte

Los tiles de CARTO devuelven «API KEY REQUIRED» en local. No viene de este cambio —el fondo del
mapa es el mismo de antes— pero hay que mirarlo antes de publicar.
