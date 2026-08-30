# Checklist de la web interactiva

Guion de trabajo para la Fase 2 de `roadmap.md`. **No es un acuerdo cerrado ni una ficha de
feature**: es la lista que se va marcando, y cada bloque pasará por `/feature` cuando toque
construirlo.

Estado: **sin empezar.** Lo marcado ⚠️ depende de datos que todavía no tenemos.

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
- [ ] Filtro por municipio y barrio (`FilterBar`)
- [ ] Clustering por densidad — en Ciutat Vella los puntos se solapan (117 hoteles en un solo CP)
- [ ] Capa de zonas **PEUAT**, que enseña dónde no pueden abrir hoteles nuevos
- [ ] `StatTile` por categoría, con **plazas además de establecimientos**: un hotel de 400
      habitaciones y un VUT de 4 plazas no pesan igual

**Cifras disponibles:** 15.406 anuncios de Airbnb · 1.442 hoteles en la provincia (754 en la
ciudad) · 162.439 plazas y 84.759 habitaciones · 24.075 licencias VUT.

**Tres precisiones geográficas que no pueden pintarse igual:**

| Fuente | Precisión |
|---|---|
| Barcelona ciudad | coordenada real (`nivel_geo = coordenada`) |
| Resto de la provincia | solo municipio → coropleta, no puntos |
| Anuncios de Airbnb | coordenada **desplazada ~200 m** por Inside Airbnb |

Pintarlas con el mismo símbolo sería mentir sobre lo que sabemos. La leyenda debe distinguirlas.

**No mezclar VUT y AT en el mismo total.** Son figuras legales distintas y la eliminación de 2028
solo afecta a los VUT: los Apartaments Turístics siguen. Es el error más fácil de cometer en toda
la web.

⚠️ **Bares y restaurantes sin integrar.** La fuente está verificada pero falta clasificar la
actividad, que viene como texto libre (`BAR`, `RESTAURANT`), no como código estable.

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

- [ ] Embudo completo, con lo descartado en cada paso a la vista
- [ ] Desglose por situación: verificada / no declara / número imposible / plausible inexistente /
      otro régimen / se asume por el anfitrión
- [ ] Top barrios **por volumen y por tasa** — solo por volumen siempre gana el Eixample
- [ ] Concentración por anfitrión
- [ ] Mapa **agregado por barrio**, nunca por anuncio

**Cifras:** de 8.996 anuncios sujetos al régimen VUT, **399 no acreditan licencia** (258
anfitriones) y 274 más quedan aparte porque su anfitrión sí la acredita en otro anuncio. De los
399, **el 95,9% tiene reseñas en 2026** y el 92,6% de los huecos entre reseñas son de 31 días o
menos: no son anuncios dormidos.

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
- [ ] Restauración que quedaría afectada ⚠️

**El error que hay que evitar:** convertir plazas de VUT en plazas de hotel una a una. Los 8.490
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

- [ ] ¿Bares y restaurantes son una capa del mapa o merecen página propia?
- [ ] ¿La comparativa entre municipios va en el paso 1 o es Fase 3 (M-07)?
- [ ] Los `HB-` de hotel **sí serían verificables** contra el registro; los `AJ` de albergue no.
      Hoy se tratan igual: ¿conviene separarlos?
- [ ] Precio de hotel: hay 395 con precio real (52%, sesgado a grandes) y el ADR del INE, que es
      oficial pero agregado. ¿Cuál manda en la web?
