# La documentación cuenta el modelo que hay, no el que había

**Fecha:** 2026-10-04 13:30
**Tipo:** Documentación

## Por qué

El cambio de las 12:00 dejó la web contradiciéndose: el mapa decía «caben todos» y `/fuentes`
seguía diciendo «3.057 no caben en ningún escenario». Las dos páginas del mismo sitio, con cifras
incompatibles.

## Qué se actualizó

**`docs/fuentes.md`**

- La ocupación hotelera pasa a ser la de habitaciones (80,2% anual, 86,5% en julio), con el porqué
  al lado: la habitación es lo que limita, la plaza libre suele ser la segunda cama de una vendida.
- Sección nueva sobre la ocupación de Airbnb y las dos vías que la estiman.
- La tabla de los dos momentos sustituye a los «3.057 que no caben».
- «La plaza es la unidad comparable» se convierte en una tabla de **dos** unidades: la plaza para el
  precio y la habitación para la capacidad. El párrafo viejo no estaba mal —sigue siendo cierto del
  precio— pero leído solo daba a entender que la plaza mandaba en todo.

**`docs/supuestos.md`** — no estaba desfasado: es que **no cubría el modelo**. Sección F nueva, con
seis supuestos: la unidad, la ocupación en los dos lados, la estimación de Airbnb y su fragilidad,
la estacionalidad prestada, por qué dos momentos y no doce, y el que sostiene todo lo demás — que
el turista desplazado sigue viniendo a Barcelona.

**`web/app/fuentes/page.tsx`** — mismas correcciones, y dos límites nuevos en «Lo que esto no puede
decir»: que solo mide dos momentos, y que da por hecho que nadie se queda en casa.

## Verificación

```
tsc --noEmit  →  sin errores
pnpm build    →  ✓ Compiled successfully, 6 rutas ○ (Static)
```

En local, `/fuentes`: las 7 secciones, **cero apariciones** de 3.057, 27.010 o 12.490, y presentes
tanto la tabla de los dos momentos como las dos vías de la ocupación de Airbnb.
