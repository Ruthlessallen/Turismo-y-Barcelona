# Checklist de la web interactiva

Guion de trabajo para la Fase 2 de `roadmap.md`. **No es un acuerdo cerrado ni una ficha de
feature**: es la lista que se va marcando, y cada bloque pasará por `/feature` cuando toque
construirlo.

Estado (2026-09-15): **tres páginas en pie**, ninguna de las cuales estaba en esta lista — el
recorrido de cinco pasos se planteó antes de que existiera el modelo de sustitución.

| Ruta | Qué es | Paso al que corresponde |
|---|---|---|
| `/` | Mapa de sustitución 2028: coropleta de saldo y de «sin sitio», con flechas opcionales | 4, convertido en mapa |
| `/flujos` | Mapa dedicado a los movimientos entre barrios | 4 |
| `/fuentes` | Fuentes, decisiones, límites del análisis | cubre el «hay que decirlo en la página» del bloque de precios |
| `/` → Restauración | Densidad de locales y cambio de comensales, en verde | 4 |
| `/airbnb` | El embudo de 15.406 anuncios a 6.834 viviendas, con barra | 3 |

Los pasos 1, 2, 3 y 5 siguen sin empezar. Lo marcado ⚠️ depende de datos que todavía no tenemos.

---

## La regla que ordena toda la web

Cada cifra es **medida** o **proyectada**, nunca las dos cosas, y se ve a simple vista cuál es cuál.
`design-system.md` ya lo exige como regla de integridad, no de estilo.

- **Medido** — sale de una fuente, con su fecha y su enlace.
- **Proyectado** — sale de un cálculo con supuestos, y los supuestos se enseñan al lado del
  resultado. Si el lector no puede ver de qué depende un número, ese número no se publica.

Una proyección con los supuestos a la vista es un argumento. Sin ellos es una invención con
aspecto de dato.

---

## El recorrido: cinco pasos

El mapa **no es la web**: es un componente del paso 1. La web cuenta una secuencia.

| Paso | Qué responde | Naturaleza |
|---|---|---|
| 1 · Qué hay hoy | La foto de la oferta turística | medido |
| 2 · Qué desaparece en 2028 | Las ~10.000 licencias VUT | medido |
| 3 · **Qué NO desaparece** | La oferta que ya opera sin licencia | medido |
| 4 · Quién puede absorberlo | Capacidad hotelera y su límite legal | medido + proyectado |
| 5 · Qué pasa con el precio | El mecanismo de presión sobre la tarifa | proyectado |

**El paso 3 es el eje.** Es el hallazgo propio del proyecto y lo que no está contando nadie más:
eliminar 10.000 licencias no elimina la oferta, porque una parte ya opera sin depender de ellas.

---

## 1 · Qué hay hoy

- [ ] Mapa con tres capas conmutables: **apartamentos turísticos**, **hoteles**, **bares y
      restaurantes**
- [ ] Filtro por barrio (`FilterBar`)
- [ ] Clustering por densidad — en Ciutat Vella los puntos se solapan (117 hoteles en un solo CP)
- [ ] Capa de zonas **PEUAT**, que enseña dónde no pueden abrir hoteles nuevos
- [ ] `StatTile` por categoría, con **plazas además de establecimientos**: un hotel de 400
      habitaciones y un VUT de 4 plazas no pesan igual

**Alcance: la ciudad de Barcelona** (decidido 2026-09-15). Desde esa fecha el export publica solo
la ciudad: 750 hoteles, 13 apartaments turístics y 9.479 locales de restauración. El resto de la
provincia se queda en `data/gold`, sin publicar.

**Cifras disponibles:** 15.406 anuncios de Airbnb · 24.075 licencias VUT · 84.058 plazas regladas
en la ciudad.

**Dos precisiones geográficas que no pueden pintarse igual:**

| Fuente | Precisión |
|---|---|
| Hoteles y restauración | coordenada real, o deducida de la dirección y verificada |
| Anuncios de Airbnb | coordenada **desplazada hasta 150 m** por Inside Airbnb |

Pintarlas con el mismo símbolo sería mentir sobre lo que sabemos. La leyenda debe distinguirlas.

**No mezclar VUT y AT en el mismo total.** Son figuras legales distintas y la eliminación de 2028
solo afecta a los VUT: los Apartaments Turístics siguen. Es el error más fácil de cometer en toda
la web.

**Bares y restaurantes: resuelto.** 9.479 locales del censo comercial municipal —4.429
restaurantes, 4.272 bares, 778 de comida rápida— clasificados por categoría del propio censo, no
por texto libre. El aviso anterior describía la fuente de OSM, que ya no se usa.

---

## 2 · Qué desaparece en 2028

- [ ] Serie del parque legal por trimestre, **2018-T2 → 2026-T1** (`TimeSeriesChart`)
- [ ] **Altas y bajas** por trimestre, no solo el stock: el saldo neto esconde el movimiento
- [ ] Serie por barrio y distrito, con mapa temporal

**Dato que rompe el relato habitual:** las licencias **no están congeladas**. Caen hasta 9.300 en
2022-T2 y desde entonces suben a **10.730** — un neto de **+1.127 desde 2018**, con 2.048 altas y
921 bajas. El PEUAT bloquea licencias *hoteleras*, no estas.

Merece explicación en la propia página: que el parque crezca hasta el año anterior a su
eliminación es parte de la historia.

---

## 3 · Qué NO desaparece ← el eje

Traslada el embudo del notebook 03. Cada cifra **por anuncios y por anfitriones**: un anfitrión con
300 pisos y 300 anfitriones con uno cada uno describen mercados distintos.

- [x] ~~Embudo completo, con lo descartado en cada paso a la vista~~ **Hecho 2026-09-16**, en
      `/airbnb`: barra de 0 a 6 filtros, con los anuncios y las plazas que quedan en cada paso y el
      porqué de cada descarte. De 15.406 / 56.420 plazas a 6.834 / 30.067.
- [ ] Desglose por situación: verificada / no declara / número imposible / plausible inexistente /
      otro régimen / se asume por el anfitrión
- [ ] Top barrios **por volumen y por tasa** — solo por volumen siempre gana el Eixample
- [ ] Concentración por anfitrión
- [ ] Mapa **agregado por barrio**, nunca por anuncio

**Hay dos cifras y no se contradicen: cuentan universos distintos.** Conviene tener las dos a mano
antes de publicar ninguna.

**399 — el embudo estrecho del notebook 03.** Son los anuncios que hoy venden, no acreditan
licencia y no tienen a quién agarrarse. Se llega ahí descartando en cadena: los 901 que declaran
otro régimen (hotel o albergue), los de anfitriones que sí acreditan licencia en otro anuncio, los
de estancia mínima superior a 31 noches, y los que no tienen ninguna reseña en 2026. Lo que queda
se reparte en tres categorías excluyentes:

| Categoría | Anuncios | Qué es |
|---|---|---|
| No declara nada | 220 | Campo vacío (132) o con texto sin licencia legible (88) |
| Número imposible | 146 | Por encima del más alto emitido por la Generalitat |
| Plausible pero inexistente | 33 | Dentro del rango emitido, pero no consta |

Es la cifra fuerte para publicar, porque cada descarte le quita una objeción posible.

**1.351 — el recuento sin descartes**, sobre las 6.834 viviendas de `airbnb_para_web.csv`:

| `estado_licencia` | Anuncios |
|---|---|
| `con_licencia` — consta en el registro oficial | 4.985 |
| `sin_licencia` | 1.351 |
| `licencia_sin_acreditar` | 498 |

Los 1.351 `sin_licencia`, por motivo:

| Motivo | Anuncios |
|---|---|
| HUTB que no consta, y además anuncia una habitación | 400 |
| No declara nada | 342 |
| Número por encima del máximo emitido | 311 |
| Anfitrión con HUTB, pero nada liga esta vivienda a ninguna | 236 |
| Número que no consta en el registro | 102 |
| Número de relleno (123456, 000000 y similares) | 23 |

La diferencia entre 1.351 y 399 **es** el conjunto de descartes: es decir, la mayor parte de los
`sin_licencia` o bien no vende hoy, o bien tiene un anfitrión que acredita licencia en otro
anuncio, o bien se acoge a la estancia larga. Si se publican los 1.351 hay que explicar eso al
lado; si no, la cifra invita a una lectura que el dato no sostiene.

De los 399, el **95,9% tiene reseñas en 2026** y el 92,6% de los huecos entre reseñas son de 31
días o menos: no son anuncios dormidos.

**Reglas que no se negocian aquí:**

- Se dice **"sin licencia acreditada"**, nunca "ilegal" ni "infractor". Describe lo observado —que
  el anuncio no acredita una licencia válida—, no una situación legal. El campo lo rellena el
  anfitrión sin validación: una licencia real mal escrita cae en el mismo grupo.
- **Nada resoluble a nivel de vivienda** — ni mapa, ni tabla, ni tooltip.
- Los criterios de exclusión se explican **en la página**, no en un anexo: sin ellos la cifra no
  significa nada.
- El umbral de 31 noches se explica bien: mide **cada cesión por separado**, no el acumulado anual.

---

## 4 · Quién puede absorberlo

- [ ] Capacidad hotelera frente a las plazas que se liberan
- [ ] **Habitaciones necesarias, no plazas** — ver abajo
- [ ] El límite del PEUAT sobre el mapa: en 3 de sus 4 zonas no se conceden licencias nuevas
- [x] ~~Restauración que quedaría afectada~~ **Hecho 2026-09-16.** Botón de Restauración en el
      mapa, con las dos vistas: dónde están los 9.479 locales y cuántos comensales gana o pierde
      cada barrio. 40 barrios pierden y 25 ganan; la Sagrada Família pierde 2.137 y el Raval gana
      1.255. Cada turista reparte su visita a partes iguales entre los locales a menos de 200 m de
      donde duerme.

**La barra no mueve nada en un año medio, y conviene saberlo antes de diseñar sobre ella.**
Medido el 2026-09-16: con la ocupación media del INE (67,9%) quedan 27.008 plazas libres para
30.067 turistas, así que los 757 hoteles se llenan en los cinco escenarios y la barra solo decide
**quién** va a cada hotel. En noviembre, al 55,6%, sobran plazas: ahí sí cambian los hoteles que se
llenan (730 frente a 745) y 26 barrios ven moverse su restauración, hasta 1.719 turistas.

Se decidió **no** añadir selector de temporada (2026-09-16). Queda anotado por si el paso 5 lo pide.

**Decidido 2026-09-15: el mapa sigue repartiendo plazas; las habitaciones van al dashboard.**
`modelar_sustitucion.py` trata las 84.058 plazas regladas como un depósito y va restando, y así se
queda. El cálculo de habitaciones necesarias —que es el del párrafo de abajo— se publica como cifra
propia en el dashboard de KPIs, no como una segunda versión del mapa.

El motivo de no mezclarlos: pasar el reparto a habitaciones obliga a suponer cómo se parte cada
grupo de viajeros entre habitaciones, y esa suposición tiene su propio coste. Como cifra agregada,
en cambio, la conversión es directa y se entiende sola.

**El aviso original:** convertir plazas de VUT en plazas de hotel una a una. Los 8.490
anuncios sujetos a VUT suman **40.015 plazas**, pero con una capacidad mediana de 4 personas por
piso y **1,88 plazas por habitación** de hotel, harían falta **27.151 habitaciones**, no 21.285.
Un grupo de 6 no cabe en una habitación: necesita tres.

La capacidad puede pesar más que el precio en la sustitución.

---

## 5 · Qué pasa con el precio

- [ ] Serie de ADR y viajeros del INE, mensual **2020-12 → 2026-06**
- [ ] La comparación capacidad vs precio, que es el argumento central
- [ ] Escenario 2028 con los supuestos visibles y ajustables

**El dato que sostiene el argumento** — capacidad plana, precio disparado:

| Año | Plazas hoteleras | Viajeros | ADR medio |
|---|---|---|---|
| 2022 | 83.176 | 7,6 M | 139 € |
| 2023 | 85.096 | 8,3 M | 161 € |
| 2024 | 86.591 | 8,4 M | 175 € |
| 2025 | 87.471 | 9,1 M | 176 € |
| 2026 | 87.506 | — | 193 € |

**+5% de capacidad en cuatro años frente a +39% de tarifa.** Ese es el mecanismo, ya medido.

**Sobre la elasticidad, y por qué hay que ser honesto con ella:** la correlación cruda entre
presión (viajeros por plaza) y ADR es +0,90, pero se desploma al quitar efectos —+0,80 sin la
recuperación pos-COVID, **+0,32** desestacionalizada. Lo primero era recuperación, lo segundo era
agosto. La elasticidad que queda es **+0,48**: el precio sube *menos* que proporcionalmente a la
presión.

Publicar el +0,90 sería engañoso. Se publica el +0,48 y se explica por qué es más bajo de lo que
parecía.

---

## Lo que NO se puede responder, y hay que decirlo

- **El % de oferta sin licencia en años pasados.** Inside Airbnb solo publica el snapshot actual
  y el archivo de montera34 se corta en 2019-03. Y aunque hubiera snapshots, habría que cruzarlos
  contra el registro **de su trimestre**, porque una licencia dada de baja hoy figura como
  inexistente.
- **La probabilidad de que un anuncio siga tras 2028.** No es medible. Lo que sí se puede decir, y
  es más fuerte: 399 anuncios operan hoy sin acreditar licencia, así que su actividad no depende de
  tenerla.
- **Cuánto subirá el precio en euros.** El mecanismo se puede enseñar; la magnitud exacta no, con
  una elasticidad estimada sobre 42 meses de una sola ciudad.
- ⚠️ **Serie histórica de hoteles.** Open Data BCN sirve un snapshot único. El INE sí da plazas
  mensuales agregadas desde 2020, que cubre parte del hueco.

---

## Pendiente de decidir

- [x] ~~¿Bares y restaurantes son una capa del mapa o merecen página propia?~~
      **Resuelto 2026-09-15: las dos cosas.** Capa conmutable en el mapa, y página propia. En el
      mapa, además, tienen que poder verse frente al desplazamiento de turistas de 2028: la
      restauración no está ahí de adorno, es quien recibe a esos turistas.
- [x] ~~¿La comparativa entre municipios va en el paso 1 o es Fase 3 (M-07)?~~
      **Resuelto 2026-09-15: descartada.** El alcance es la ciudad de Barcelona. `export_mapa.py`
      dejó de publicar `vut_por_municipio.json` y filtra los hoteles a la ciudad.
- [x] ~~Los `HB-` de hotel **sí serían verificables** contra el registro; los `AJ` de albergue no.
      Hoy se tratan igual: ¿conviene separarlos?~~
      **Resuelto 2026-09-15: solo hoteles.** Separar los albergues añade una rama de verificación
      que no se puede cerrar, para 5 anuncios. Se quedan como están.
- [x] ~~¿La capa de restauración es el censo o OSM?~~
      **Resuelto: el censo**, confirmado 2026-09-15. OSM se deja fuera un 26% de la restauración de
      Barcelona; el censo es de 2023-2024 pero completo, y se eligió cobertura sobre actualidad.
      `export_mapa.py` seguía leyendo OSM de bronze desde aquella decisión hasta hoy.
- [x] ~~Precio de hotel: hay 395 con precio real y el ADR del INE. ¿Cuál manda en la web?~~
      **Resuelto 2026-09-02: mandan los dos, para cosas distintas.** El raspado da la posición
      relativa de cada hotel; el ADR del INE da el nivel oficial y la estacionalidad. Contrastados
      por categoría coinciden con desvíos de −3% a +12%, así que el raspado queda validado y el ADR
      corrige su sesgo de fecha. Hoy son 451 con precio observado (58,7%).

---

## Cómo se presenta el precio: los tres estados del dato

**Decidido 2026-09-02.** La web nunca da a entender que conoce el precio de un alojamiento cuando
lo ha estimado. Cada cifra de precio llega marcada con su procedencia, y la marca es visible sin
tener que abrir ninguna ficha:

| Estado | Qué es | Cuántos |
|---|---|---|
| **Observado** | Precio raspado y cruzado con el registro oficial | 451 de 763 |
| **Transformado** | Ese mismo precio llevado a equivalente anual con la estacionalidad del INE | los mismos 451 |
| **Estimado** | Predicción del modelo para quien no tiene precio | 312 |

En el dato viajan como una sola columna, `origen_precio` (`observado` / `estimado` / vacío). Los
siete matices que usa el análisis para auditar el cruce y el modelo se quedan en
`hoteles_bcn_precio_estimado.csv` — ver `data-model.md`.

**Se publica la banda, no el euro.** No es una simplificación de diseño: un mismo hotel varía un
±22% según la habitación y el día —comprobado sobre Hostemplo, ver `observaciones-datos.md`— así
que un número exacto afirmaría una precisión que la magnitud no tiene. La banda aguanta donde el
euro no: el modelo acierta la banda exacta un 65% y la exacta o contigua un 99%.

**Hay que decirlo en la página, no solo en una nota al pie.** El texto tiene que explicar que no
existe una fuente pública de precio medio por noche y establecimiento, que por eso se trabaja con
bandas, y que una parte de ellas son estimadas. Que el usuario sepa qué está mirando es parte del
resultado, no un descargo de responsabilidad.

**La banda `€` se publica también cuando es estimada.** Decidido 2026-09-15, revierte la regla
anterior: si el modelo dice que un alojamiento baja de 100 €, se marca `€` como cualquier otra
banda. Son 2 casos en banda por habitación y 5 en banda por plaza.

La regla anterior —`€` solo si era observada— nacía de que el modelo acierta 2 de los 52
alojamientos que de verdad bajan de 100 €. Pero eso describe **el error del modelo en el extremo
barato**, y a un modelo que falla en un tramo no se le responde escondiendo el tramo: se responde
diciendo que ese precio está estimado, que es justo lo que ya hace `origen_precio`. Callar la banda
baja de dos hoteles no los encarece, y deja un hueco que el lector no puede interpretar.

**Las 5 estimaciones sin apoyo no se publican.** Pensiones, residencias y apartaments turístics con
menos de diez ejemplos comparables en el entrenamiento. Un hueco es más honesto que un número que
nadie puede contradecir. **Esto sigue en pie**, y desde 2026-09-15 el corte ocurre en
`preparar_alojamientos_provincia.py` y no en el export, para que ningún consumidor del CSV pueda
saltárselo.

La diferencia entre las dos reglas: una escondía un número por **desconfiar de su valor**, la otra
lo esconde porque **no hay con qué sostenerlo**. Solo la segunda es un problema del dato.

**Airbnb hereda las mismas reglas**, con un problema añadido: el precio del anuncio no es
comparable con el de una habitación de hotel. Un piso entero para cuatro a 221 € y una habitación
a 64 € solo se comparan **por plaza** — 54 € y 43 €. La banda de Airbnb se construye sobre precio
por plaza y noche, y se dice cuál es la unidad.
