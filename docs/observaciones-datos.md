# Observaciones sobre los datos

Comprobaciones hechas a mano contra la fuente original, que no caben en el código pero condicionan
cómo hay que leer los resultados. Cada entrada dice qué se miró, qué se encontró y qué implica.

No son datos del pipeline: nada de esto entra en ningún CSV. Sirven para saber cuánto vale lo que
sí entra.

---

## Un hotel no tiene un precio, tiene un rango

**Fecha de la comprobación:** 2026-09-02
**Establecimiento:** Hostemplo (ATB-000089), la Sagrada Família — 10 habitaciones, 20 plazas
**Fuente:** consulta manual en el portal de reservas

Precios por noche encontrados en la misma quincena:

| Fecha | Habitación | Precio/noche |
|---|---|---|
| 20-21 sept | Individual | 138 € |
| 20-21 sept | Doble | 163 € |
| 22-23 sept | Doble | 179 € |
| 22-23 sept | Triple | 219 € |
| 29 sept – 1 oct | Doble | 196 € (393 € por dos noches) |

Mediana 179 €, media 179 €.

**Qué implica.** El mismo establecimiento se mueve entre 138 y 219 € en quince días, un ±22% sobre
su propia mediana, por dos causas que se suman: el tipo de habitación y la fecha concreta.

Eso pone un suelo a lo que cualquier método puede lograr. El modelo de imputación tiene un error
del 27% sobre una mediana de 150 €; comparado con cero suena mal, pero la magnitud que intenta
estimar varía por sí sola un ±22% según qué día y qué habitación se consulte. No estamos lejos del
límite de lo que un número único por hotel puede decir.

**Por qué se publica la banda y no el euro.** Hostemplo cae en `€€` con 138 €, con 179 € y con
196 €. La banda aguanta donde el precio exacto no: la granularidad de lo que se publica tiene que
corresponderse con la precisión de lo que se mide, y aquí esa precisión es de banda.

**Nota sobre las fuentes automáticas.** Para este mismo hotel, Airbnb daba 148 € y el emparejamiento
laxo de Google 244 €. Los dos son reales y los dos están en los extremos: una consulta única captura
un punto del rango, no su centro. Lo que le faltaría a los precios raspados no es cobertura de
hoteles, es **cobertura de fechas** — varias consultas por establecimiento en días distintos, que es
lo que da una distribución en vez de un punto.

**Qué no se hizo.** No se metió el valor a mano en `hoteles_bcn.csv`. Un dato verificado que entra
por un camino distinto al del resto queda sin trazabilidad y nadie recuerda después de dónde salió;
el hotel sigue con precio estimado por el modelo y marcado como tal.

---

## Los apartaments turístics de Airbnb miden otra cosa

**Fecha:** 2026-09-02
**Fuente:** Inside Airbnb, volcado del 2026-06-24, cruzado por número de licencia ATB

Cuatro apartaments turístics tienen precio por las dos vías, y no coinciden:

| Establecimiento | Google (finales sept) | Airbnb (24 junio) | Desvío |
|---|---|---|---|
| Monturiol Apartaments | 179 € | 160 € | −11% |
| Silver | 144 € | 182 € | +26% |
| DV Apartamentos | 134 € | 170 € | +27% |
| Midtown Apartments | 284 € | 418 € | +47% |

**Qué implica.** Coinciden en orden de magnitud, lo que confirma que el emparejamiento acertó de
establecimiento — es la única verificación externa que tiene el rescate de precios.

Las diferencias tienen dos causas identificadas y ninguna es un error: la **fecha** —junio y
septiembre son meses distintos, con factores 1,19 y 1,16 sobre la media anual— y sobre todo la
**unidad**. Midtown figura en el censo con 30 habitaciones y en Airbnb aparece como piso entero para
6 plazas: ese +47% no compara lo mismo. Al normalizar por plaza, estos aparthoteles salen a 70-91 €
frente a los 54 € de mediana del piso entero corriente en Airbnb, que es coherente con que sean
establecimientos reglados y no viviendas particulares.

**Consecuencia para el trabajo con Airbnb.** Comparar hotel con apartamento exige normalizar por
plaza. El precio del anuncio no vale: 221 € de un piso para cuatro y 64 € de una habitación no son
comparables, pero 54 € y 43 € por plaza sí.

---

## Números de licencia ATB que no pueden existir

**Fecha:** 2026-09-02
**Fuente:** campo `license` de Inside Airbnb

Entre las 12 licencias ATB distintas que los anuncios declaran aparecen **ATB-003211, ATB-004230 y
ATB-038768**. El registro de apartaments turístics de Barcelona ciudad llega hasta ATB-000276.

Pertenece a la auditoría de licencias, no al trabajo de precios, pero queda anotado aquí porque
salió mientras se buscaban precios y conviene no perderlo.


---

## La mitad de las exenciones se apoyan en 31 noches, que no eximen

**Fecha:** 2026-09-02
**Fuente:** `minimum_nights` de Inside Airbnb, volcado del 2026-06-24

| Situación declarada | Anuncios | Exactamente 31 noches | 32 o más |
|---|---|---|---|
| Exención declarada | 2.960 | **1.478 (49,9%)** | 1.482 (50,1%) |
| Sin declarar | 4.124 | 1.144 (27,7%) | 1.350 (32,7%) |

**Por qué importa.** El Decret Llei 3/2023 define el uso turístico como la cesión por un *«període
de temps continu igual o inferior a 31 dies»*. Igual **o inferior**: una estancia de 31 noches
sigue siendo uso turístico y sigue necesitando licencia. Solo a partir de 32 queda fuera.

La mitad de los anuncios que declaran estar exentos fijan su mínimo exactamente en 31, es decir,
una noche por debajo de lo que les eximiría. No se puede distinguir desde el dato si es una
lectura equivocada de la norma —«31 días es un mes, luego es alquiler de temporada»— o una
colocación deliberada en el borde. Lo que sí se puede afirmar es que esa exención no les ampara.

**Efecto sobre el precio.** Es lo que explica que la oferta sin licencia salga a mitad de precio:
pisos enteros de cuatro plazas con licencia verificada están en 54,7 €/plaza y los de `sin_declarar`
en 26,7 €. No son el mismo producto compitiendo por el mismo cliente; los segundos son alquiler de
temporada, con precio por noche de mensualidad. Al comparar oferta turística hay que separarlos, o
la banda económica de Airbnb saldrá artificialmente barata.


---

## El umbral de exención de Airbnb está una noche por debajo del que exige la ley

**Fecha:** 2026-09-02
**Fuente:** `minimum_nights` y `license` de Inside Airbnb, volcado del 2026-06-24

Distribución de la estancia mínima entre los 2.960 anuncios que declaran *«Exempt - seasonal
rental»* en el campo de licencia de Barcelona:

| Estancia mínima | Anuncios |
|---|---|
| Menos de 31 noches | **0** |
| Exactamente 31 | **1.478** |
| Exactamente 32 | **1.397** |
| 33 a 365, dispersas | 85 |

**Hay un suelo duro en 31 y libertad por encima.** Ningún anuncio con la exención declarada baja de
31 noches, mientras que por encima aparecen 33, 35, 40, 45, 60, 90, 120, 180 y 365 con la
dispersión que cabría esperar de decisiones individuales. Un suelo sin dispersión por debajo y con
dispersión por encima es la firma de un límite impuesto por el formulario, no de miles de
anfitriones coincidiendo en el mismo número.

**Y el umbral está mal.** El Decret Llei 3/2023 define el uso turístico como cesión por un período
*«igual o inferior a 31 dies»*: una estancia de 31 noches es uso turístico y necesita licencia. La
exención empieza en 32. Los 1.478 que se apoyan en 31 declaran una exención que no les ampara.

**Los dos picos dicen quién sabe dónde está la frontera.** 1.478 en 31 —el mínimo que el
formulario permite— y 1.397 en 32 —el mínimo que la ley realmente exime—, casi mitad y mitad. Quien
pone 32 conoce la norma; quien pone 31 se ha fiado de la plataforma.

**Qué se puede afirmar y qué no.** Se puede afirmar que el suelo de 31 no lo fija el anfitrión: la
ausencia total de valores inferiores no se explica por decisiones independientes. No se puede
demostrar desde el dato que Airbnb lo bloquee en su formulario, solo que los datos son consistentes
con eso y difíciles de explicar de otro modo. Confirmarlo exigiría abrir el formulario de
declaración de licencia de un anuncio de Barcelona.

**Corrección de una lectura anterior.** Una versión previa de esta nota atribuía la coincidencia a
«una regla aprendida circulando entre gestores». Era una inferencia mal fundada: al mirar la
distribución completa —y no solo los que quedan dentro del alcance de la ley— el suelo en 31 con
dispersión libre por encima apunta a la plataforma, no a los anfitriones.

**Efecto en el recuento.** Los 1.478 que se apoyan en 31 quedan **dentro** del conjunto sujeto a la
eliminación de 2028, marcados con `borde_31_noches`. Aceptar la exención tal como se declara habría
restado casi mil quinientas viviendas del alcance.


---

## Los 262 sin precio no son un fallo del dato, son tres cosas distintas

**Fecha:** 2026-09-02
**Fuente:** cruce de `precio_anuncio`, `last_review` y `availability_365` sobre los 7.327 anuncios
sujetos a la ley

Tras las exclusiones quedan 262 anuncios sin precio, el 3,6%. Repartidos por el mes de su última
reseña, no se distribuyen al azar:

| Último comentario | Registros | % cuyo anfitrión sí cotiza en otro anuncio | Disponibilidad mediana |
|---|---|---|---|
| 2026-06 | 89 | 87% | 124 días |
| 2026-05 | 40 | 82% | 86 días |
| 2026-04 | 19 | 79% | 20 días |
| 2026-01 a 2026-03 | 30 | 55-100% | 0-52 días |
| 2025-07 a 2025-12 | 49 | 50-100% | 0-18 días |
| Sin reseñas nunca | 35 | 26% | 313 días |

**148 son recientes y con calendario abierto.** Abril a junio de 2026, disponibilidad de 20 a 124
días, y en el 80-87% de los casos su anfitrión sí publica precio en otro anuncio. La lectura más
probable es que estuvieran ocupados o bloqueados el día del volcado: Airbnb no muestra tarifa
cuando no hay noches vendibles en la ventana consultada. Es un artefacto de la foto, no una
carencia del anuncio.

**35 no han tenido nunca una reseña** y ofrecen 313 días. Solo el 26% tiene un anfitrión que cotice
en otro sitio, lo que encaja con anuncios recién publicados que aún no han fijado tarifa.

**79 son de 2025 con disponibilidad de 0 a 20 días.** Estos sí parecen apagados. Pasaron el filtro
de actividad por tener alguna reseña dentro de los doce meses, pero su calendario cerrado dice otra
cosa.

**Qué se hizo con ellos (2026-09-02).** Primero recuperar, después descartar:

1. **La deduplicación se corrigió para conservar la copia que sí cotiza.** Conservaba la primera
   por `id`, y en 21 viviendas eso dejaba dentro la copia muda mientras tiraba la que tenía precio
   — el mismo piso, el dato disponible, y perdido por el criterio de desempate. El orden es ahora:
   que tenga precio, que su última reseña sea más reciente, y el `id` como desempate.
2. **Se excluyen 67**: 48 cuya última reseña es de 2025 o antes, y 19 de 2026 cuyo anfitrión no
   tiene ningún otro anuncio del que deducir tarifa.
3. **Se conservan 189**: 154 de 2026 con anfitrión que cotiza en otros anuncios —calendario
   abierto, probablemente ocupados el día del volcado— y 35 sin reseñas nunca, que ofrecen 313 días
   de mediana y son publicaciones recientes.

La cobertura de precio entre los sujetos a la ley pasa del 96,4% al **97,4%**.

---

## 631 anuncios usan una licencia de vivienda entera para vender una habitación

**Fecha:** 2026-09-02
**Fuente:** cruce del prefijo de `licencia_regional` con `room_type`

| Licencia declarada | Piso entero | Habitación privada |
|---|---|---|
| HUTB | 6.519 | **631** |
| HB (hotel) | 53 | 556 |
| AJ (albergue) | 0 | 107 |
| Sin declarar | 4.250 | 3.073 |

Un HUTB ampara la cesión del **habitatge sencer**. Los 556 de `HB` y los 107 de `AJ` vendiendo
habitaciones son normales —un hotel y un albergue publican sus habitaciones por separado— pero 631
anuncios declaran una licencia de vivienda de uso turístico y anuncian una habitación suelta.

Quedan fuera del recuento de VUT por no ser cesión entera, así que no afectan a la cifra de
viviendas que la ley elimina. Se anota aquí porque pertenece a la auditoría de licencias, no al
trabajo de precios: es una licencia usada para una actividad distinta de la que ampara.


---

## Los tres estados de licencia, y por qué no son dos

**Fecha:** 2026-09-03
**Fuente:** `revisar_airbnb_revisado.ipynb`, celdas 29 y 30

Sobre los 15.406 anuncios, cada uno cae en uno de tres estados. La frontera entre ellos es **qué
sabemos**, no qué sospechamos:

| Estado | Anuncios | Qué significa |
|---|---|---|
| `con_licencia` | 7.005 | Declara una licencia que consta en el Registre, o una de establecimiento reglado |
| `sin_licencia` | 8.284 | No acredita licencia utilizable |
| `licencia_sin_acreditar` | 117 | No declara, pero su anfitrión acredita hotel o albergue en otros anuncios |

**Por qué existe el tercer estado.** Un hotel y un albergue publican sus habitaciones por separado
bajo una **única** licencia, así que un anuncio suyo sin declarar encaja con ella. No vale el mismo
razonamiento con HUTB: cada una ampara **una vivienda**, y que un titular tenga veinte no dice nada
sobre el piso veintiuno. Por eso los 1.427 anuncios cuyo anfitrión tiene HUTB en otros sitios van a
`sin_licencia`, no a `licencia_sin_acreditar`.

### Dentro de `sin_licencia` hay cinco situaciones

| Motivo | Anuncios |
|---|---|
| No declara nada | 3.640 |
| Declara exención | 2.123 |
| Anfitrión con HUTB, pero nada liga esta vivienda | 1.427 |
| **Número imposible: por encima de HUTB-80024** | **889** |
| Número que no consta en el registro | 203 |
| Número de relleno (123456, 000000) | 2 |

**Los números imposibles son el caso más sólido del grupo.** El registro de Barcelona tiene 10.654
licencias y la mayor es **HUTB-80024**. Un anuncio que declara un número por encima de ese techo no
se ha equivocado al teclear: ha rellenado el campo para que pareciera cumplimentado.

**Un fallo que costó encontrar ese techo.** El primer cálculo daba un máximo de HUTB-1.201.700.461.701
y la regla no se disparaba nunca. La causa: `vut_unificados.csv` trae, además de los HUTB, 95
entradas `OPENDATA-01-2018-0509` y una `1-2017-0046170-1`; al quitar los guiones sin filtrar antes,
esa última producía el falso techo. Filtrando a `^HUTB-\d+$` quedan los 10.654 reales.

### El conjunto que va a la web

**6.377 viviendas** — cesión entera, estancia de 31 noches o menos, con reseñas desde 09/2025, y
excluido el alojamiento reglado:

| Estado | Viviendas | % |
|---|---|---|
| Con licencia | 4.985 | 78,2% |
| **Sin licencia** | **1.380** | **21,6%** |
| Licencia sin acreditar | 12 | 0,2% |

### La nota que debe acompañar a estas cifras

> `sin_licencia` significa que el anuncio **no acredita** la licencia que Barcelona obliga a
> declarar en la plataforma. Es exactamente lo que dice el dato: que no consta.
>
> Que la licencia no exista es otra cosa, y este dato no la mide: un campo mal rellenado y una
> vivienda sin licencia se ven igual desde aquí.
>
> Lo que sí se puede afirmar: estas viviendas se anuncian para uso turístico, tienen huéspedes
> recientes y no acreditan licencia. Es un incumplimiento de la obligación de declarar, y
> probablemente indique irregularidad, pero no la demuestra.

### Lo que se retiró y por qué

Las dos últimas celdas del notebook original medían distancias entre anuncios —`<150 m` y
coincidencia GPS exacta— para vincular pisos al mismo edificio. Se eliminaron: Inside Airbnb
desplaza cada anuncio hasta 150 m de forma **independiente**, así que dos pisos del mismo portal
superan ese umbral el 41% de las veces. Y aunque las coordenadas fueran exactas, la distancia
tampoco distinguiría «la misma vivienda declarada dos veces» de «otra vivienda del mismo bloque».
