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
