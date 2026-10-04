# La unidad pasa a la habitación, y la escasez se mide en dos momentos

**Fecha:** 2026-10-04 12:00
**Tipo:** Corrección de modelo
**Requisitos:** M-06 (absorción hotelera)

## El error que se corrige

El modelo descontaba la ocupación real **a los hoteles y no a los pisos turísticos**. Comparaba
30.067 plazas de Airbnb, como si estuvieran llenas las 365 noches, contra las plazas de hotel que
quedaban libres descontado un 67,9% de ocupación. De ahí salían los «3.057 que no caben», que no se
sostienen: era la misma magnitud medida de dos formas distintas.

Además usaba la **plaza** como unidad. Una plaza libre de hotel suele ser la segunda cama de una
habitación ya vendida: no se puede vender aparte, y un grupo de cuatro no cabe en ella. Lo que
limita a un hotel es la habitación.

## Lo que se mide ahora

**La unidad es la habitación, en los dos lados.** Airbnb aporta `bedrooms`, que solo falta en el
2,8% de los anuncios; donde falta se deduce de `accommodates / 2`, la mediana observada. Los dos
lados son comparables sin corregir nada: 2,00 plazas por dormitorio en Airbnb frente a 1,88 por
habitación en nuestros hoteles.

**La ocupación hotelera es la del INE por habitaciones, no por plazas**: 80,2% frente al 67,9% que
usábamos. Son la misma encuesta y el mismo mes; miden cosas distintas.

**La ocupación de Airbnb se estima, porque no existe dato oficial.** Dos vías independientes:

| Vía | Resultado |
|---|---|
| Calendario, `(365 − availability_365) / 365` | 38,3% |
| Reseñas, `reseñas_12m / 0,50 × 3 noches / 365` | 38,8% |

Que coincidan es lo que la hace publicable. Con estancias de 4 noches la segunda sube al 48,6%, así
que la horquilla honesta es 38-48% y se toma el extremo bajo, que es el que no depende de suponer
ni tasa de reseña ni duración.

## Dos momentos, no uno

| | Habitaciones libres | Piden | Sin sitio |
|---|---|---|---|
| Un año medio | 8.841 | 5.706 | **0 turistas** |
| Julio, la punta | 6.028 | 6.647 | **1.273 turistas** |

**La conclusión cambia de signo.** En un año medio la ciudad absorbe a todos los turistas de los
pisos turísticos y le sobran habitaciones. Falla en la punta del verano, y falla por habitaciones,
no por camas. Publicar solo la media anual escondía el problema; publicar solo julio lo extendería
a doce meses.

**Efecto lateral:** ahora la barra de precio/ubicación mueve algo en el año medio —el recorrido
mediano va de 2,30 km a 0,22 km— porque al sobrar habitaciones la preferencia decide a qué hotel se
va cada uno. Antes no movía nada, porque los hoteles se saturaban en todos los escenarios.

## Qué cambió

| Archivo | Cambio |
|---|---|
| `gold/modelar_sustitucion.py` | Reparto en habitaciones, ocupación en los dos lados, bucle por momento |
| `export/export_mapa.py` | `sustitucion_2028.json`, `flujos_2028.json` y `restauracion_2028.json` anidan por momento |
| `web/app/lib/tipos.ts` | `MOMENTOS`, `MomentoSustitucion`, columnas renombradas a turistas |
| `web/app/mapa/page.tsx` | Selector de momento y panel reescrito |
| `web/app/flujos/page.tsx` | Selector de momento |
| `web/app/page.tsx` | «Caben, salvo en julio» en lugar de «3.057 turistas no caben» |

Las columnas pasan de `plazas_que_salen` a `turistas_que_salen`: se reparten habitaciones pero se
publica la persona, que es lo que se entiende, y el nombre tenía que decir cuál de las dos es.

## Verificación

```
modelar_sustitucion.py → 640 filas (64 barrios x 5 escenarios x 2 momentos), 848 flujos
export_mapa.py         → sustitucion_2028 {'momentos': 2, 'sin_sitio_anio_medio': 0,
                          'sin_sitio_julio': 1273, 'turistas_a_realojar': 11516}
tsc --noEmit           → sin errores
pnpm build             → ✓ Compiled successfully, 6 rutas ○ (Static)
```

En local: `/mapa` pinta los 75 barrios y el panel dice «Caben todos» en año medio; la portada da
11.516 personas y 1.273 sin sitio en julio.

## Queda

`docs/fuentes.md` y `docs/supuestos.md` siguen contando el modelo viejo —plazas, 67,9%, 3.057 sin
sitio— y hay que reescribirlos antes de que nadie los lea como si fueran lo que hace el código.
