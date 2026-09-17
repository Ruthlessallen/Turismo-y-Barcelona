# Navegación entre secciones, y el índice pasa a ser el resumen

**Fecha:** 2026-09-16 14:30
**Tipo:** Feature
**Requisitos:** estructura del sitio

## La estructura acordada

| Ruta | Qué es |
|---|---|
| `/` | Resumen: las cifras generales y por dónde seguir |
| `/mapa` | El mapa de 2028, con sus capas |
| `/airbnb` | El embudo de anuncios a viviendas |
| `/fuentes` | Fuentes, decisiones y límites |
| `/hoteles` | **Pendiente**, no existe todavía |

`/flujos` se queda **fuera del nav** a propósito: es una vista del mapa, no una sección, y se llega
desde él.

## El nav va en el layout, no en cada página

El alto lo reparte el layout: nav fijo arriba y el contenido ocupa lo que queda. Eso es lo que
permite que el mapa se quede quieto —nunca scrollea— mientras una página de texto sí puede. Cada
página decide qué hacer con `h-full`, pero **ninguna vuelve a medir la ventana por su cuenta**, que
era el camino directo a que el nav empujara el mapa fuera de pantalla.

La sección activa se marca con `aria-current="page"`, no solo con color.

## El índice

El mapa estaba en `/` y se mueve a `/mapa`. La portada nueva lee `resumen.json` —el mismo fichero
que ya producía el export— y no inventa ninguna cifra:

- **Cuatro cifras de hoy:** 24.075 licencias, 15.406 anuncios, 755 hoteles, 9.479 locales.
- **Tres bloques de lo que desaparece:** el embudo a 6.834, los 3.057 que no caben, los 40 barrios
  que pierden comensales. Cada uno enlaza a donde se puede mirar de cerca.
- **Un aviso antes de nada:** que esto no cubre las 24.075 licencias sino las 6.834 anunciadas en
  Airbnb, y que el reparto de 2028 es un modelo con supuestos.

Ese aviso va **arriba y en la portada**, no escondido en `/fuentes`: es la primera página que verá
quien llegue, y la que más fácil se cita fuera de contexto.

## Títulos

`layout.tsx` pasa a una plantilla `%s · Barcelona sin pisos turísticos`. Como `/mapa` y `/airbnb`
son componentes de cliente y no pueden exportar `metadata`, cada uno gana un `layout.tsx` de
segmento que solo sirve para eso.

## Verificación

```
tsc --noEmit  →  sin errores
```

En local, sin errores de consola:

| Ruta | Título | Sección activa | Scroll de documento |
|---|---|---|---|
| `/` | Barcelona sin pisos turísticos | Resumen | — |
| `/mapa` | El mapa · … | El mapa | no |
| `/airbnb` | Airbnb · … | Airbnb | no |
| `/fuentes` | Fuentes y método · … | Fuentes | sí, es una página de texto |

El mapa sigue montando (`.leaflet-container` presente) y la portada muestra las cifras reales del
`resumen.json`.

**No se ha ejecutado el build de producción.**

## Queda

`/hoteles`. El dato está listo —750 hoteles con banda, procedencia del precio, plazas y
habitaciones— pero la página no existe, así que **no se ha puesto en el nav**: un enlace que lleva
a un 404 es peor que una sección que todavía no está.
