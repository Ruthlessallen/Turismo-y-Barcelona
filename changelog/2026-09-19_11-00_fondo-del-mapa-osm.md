# El fondo del mapa pasa a OpenStreetMap

**Fecha:** 2026-09-19 11:00
**Tipo:** Corrección

## Qué pasaba

El CDN de CARTO empezó a devolver «API KEY REQUIRED» para `light_nolabels`. En producción el mapa
salía con los barrios flotando sobre el vacío: cargaba 1 tile de 12.

## Qué se hizo

El fondo pasa a los tiles de OpenStreetMap, que no piden clave, y se extrae a
`web/app/lib/fondo.ts` porque estaba duplicado en los dos mapas y podían divergir.

**Lo que se pierde, y cómo se compensa.** `light_nolabels` era deliberadamente discreto —sin
etiquetas comerciales, porque el mapa habla de barrios, no de negocios—. OSM trae calles, nombres y
comercios, así que compite con el color del barrio. Se compensa bajando la opacidad del fondo a
0,45, **no subiendo la del relleno**: el dato tiene que ganar al callejero, y aclarar el fondo es lo
que menos altera los colores de la escala.

La atribución viaja en la misma función que la URL: OSM es ODbL y usar sus tiles obliga a citarlos,
así que no puede quedar a criterio de cada mapa.

## Verificación

En local, a 1400x820:

```
/mapa    → 12 de 12 tiles cargados desde tile.openstreetmap.org, 75 barrios pintados
/flujos  → 20 de 20 tiles cargados
pnpm build → ✓ Compiled successfully, sin avisos, las 6 rutas ○ (Static)
```

Se quita además un `import Link` sin usar en `fuentes/page.tsx`, que era el único aviso del build.

## Queda por decidir

**El uso de los tiles de OSM tiene una política.** Su fundación los sirve gratis pero pide que no
se les use como CDN de una aplicación con tráfico: si el sitio crece, lo correcto es pasar a un
proveedor con plan propio (CARTO con clave, Mapbox, Stadia) o servir tiles propios. Para un
proyecto personal con visitas contadas está dentro de lo que toleran; conviene no olvidarlo si esto
se difunde.
