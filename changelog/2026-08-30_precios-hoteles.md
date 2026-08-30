# Precios de hotel: cruce con el registro oficial y auditoría del emparejamiento

**Fecha:** 2026-08-30
**Tipo:** Feature
**Requisitos:** Apoyo a M-06 (absorción hotelera) — el precio es una de las variables de sustitución

## Qué se hizo

`pipeline/transform/cruzar_precios_hoteles.py` cruza precios raspados con el registro oficial y
**mide si el emparejamiento es fiable**. Ese es el objetivo del script: un precio pegado al hotel
equivocado es peor que no tener precio, porque no se nota. Por eso el informe es de calidad de
cruce antes que de estadística de precios.

Resultado con la primera tanda real (Google Hotels vía Apify, 1.523 fichas):

| Método | Hoteles | Fiabilidad |
|---|---|---|
| Coordenada (<60 m + nombre parecido) | 330 | alta |
| Nombre único en toda la ciudad | 133 | alta |
| Nombre contenido + <150 m | 29 | alta |
| Parecido literal ≥0,85 | 42 | revisar |
| **Sin cruce** | **220** | — |

**395 hoteles con precio fiable, el 52% del parque de la ciudad.**

| Categoría | Hoteles | Precio mediano |
|---|---|---|
| No aplica | 80 | 140 € |
| 1 estrella | 26 | 144 € |
| 3 estrellas | 90 | 158 € |
| 2 estrellas | 25 | 165 € |
| 4 estrellas | 109 | 195 € |
| 4 estrellas superior | 29 | 244 € |
| 5 estrellas | 19 | 325 € |
| Gran luxe | 17 | 370 € |

Que el precio suba de forma casi monótona con la categoría oficial es la señal de que el
emparejamiento funciona: son dos fuentes independientes y coinciden.

## El problema de fondo: las dos fuentes no nombran igual

El registro guarda el **nombre administrativo**, casi siempre una palabra — `Goya`, `Lirio`,
`Comercio`. El portal muestra la **marca comercial completa** — `Casa Lirio by Blossom Hotels`.
`SequenceMatcher` penaliza esa diferencia de longitud y da parecidos de 0,3 en pares que son el
mismo hotel:

| Registro | Raspado | Similitud literal |
|---|---|---|
| `Lirio` | Casa **Lirio** by Blossom Hotels | 0,33 |
| `HOTEL CONDAL` | Hotel **Condal** Barcelona I ... Las Ramblas | 0,22 |
| `Moderno` | Hotel **Moderno** BCN Free Breakfast... | 0,32 |

La solución fue **comprobar contención en vez de parecido**: si todas las palabras distintivas del
registro aparecen dentro del nombre raspado, es el mismo hotel. Con dos condiciones que la acotan:

- **Contención + proximidad** (<150 m), y solo si hay **un único** candidato cerca.
- **Contención + unicidad**: si `ABREVADERO` aparece en una sola ficha de las 1.523, no hay
  ambigüedad que resolver. Es la única vía para los hoteles sin coordenada en nuestro registro.
- Se exige que la palabra más larga tenga **4 letras o más**: con `SOL` o `MAR` cualquier nombre
  contendría a cualquiera.

Efecto: los sin cruce bajan de 298 a **220**, y los precios fiables suben de 342 a **395**.

## Lo que NO se hizo, y por qué

**No se relajó el umbral de parecido literal.** 75 de los fallos tienen una ficha a menos de 60 m,
y bajar el umbral de 0,55 a 0,40 recuperaría 33 cruces. Pero hay **117 hoteles en un solo código
postal de Ciutat Vella**: dos establecimientos a 40 m con nombres distintos son probablemente dos
hoteles distintos. Mejor 395 fiables que 430 con basura dentro.

**No se descarta nada en silencio.** Todo cruce sospechoso queda en la salida marcado `dudoso`,
con su método y su similitud, para poder revisarlo.

## Comprobación nueva: fichas compartidas

53 hoteles del registro comparten ficha raspada con otro. Casos como `LIMONAIA 1`, `LIMONAIA 2` y
`LIMONAIA 3` apuntando a un solo `Hotel Limonaia`: o el registro tiene tres licencias para un
mismo edificio, o el cruce ha juntado hoteles distintos. En ambos casos el precio no puede
atribuirse a uno solo, así que se marcan como dudosos y quedan fuera de las medias.

## El sesgo de los 220 que faltan — importante

La ausencia **no es aleatoria**. Los que no cruzan son los pequeños:

- Mediana de **14 habitaciones**, frente a **46** en los que sí cruzaron
- **129 de 220 sin categoría de estrellas**: hostales y pensiones

Google indexa y muestra los hoteles grandes; los pequeños quedan fuera. Consecuencia directa para
M-06: **la mediana de 174 € probablemente sobreestima el precio del parque real**, y son
precisamente los alojamientos baratos —los que sustituirían a un VUT barato— los que faltan.

## Descartado por el camino: Google Places

Se probó primero la Places API (New) de Google con 10 hoteles. Devolvió `rating` en los 10, así que
la llamada funcionaba, pero `priceLevel`, `priceRange` y los campos `serves*` vinieron **vacíos en
todos**. Verificado después contra la referencia oficial: no existe ningún campo de tarifa por
noche ni de habitación. Los precios que Google muestra en Maps vienen de Hotel Ads, un producto de
anunciantes que no se expone por API.

Sí sirve, en cambio, para `rating` y `userRatingCount` de los 754, gratis dentro de la cuota.

## Límites

- **Es el precio de una estancia concreta**: 29/09–01/10 de 2026, 2 noches, 2 adultos. No es una
  media anual. Para eso harían falta varias tandas repartidas por el año.
- **Cobertura del 52%**, sesgada hacia hoteles grandes.
- **Procedencia:** raspado de un portal de reservas, cuyos términos lo prohíben. Sirve para
  explorar y modelar en local; **para publicar cifras hace falta una fuente citable** — el ADR del
  INE (operación IRSH) es la referencia oficial, aunque solo agregada.

## Pendiente

- Repetir en varias fechas para tener rango en vez de un punto.
- Recuperar a mano los hoteles grandes que fallaron por nombre distinto (`Eurostars Cristal
  Palace`, `INTERNACIONAL RAMBLAS ATIRAM HOTEL`).
- Revisar `COLÓN` → `Hotel Regencia Colon`: puede ser el mismo o dos hoteles que comparten palabra.
- Geocodificar los 309 hoteles de la ciudad sin coordenada — es lo que más subiría la cobertura.
