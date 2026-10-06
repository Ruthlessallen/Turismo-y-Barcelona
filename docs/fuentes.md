# Fuentes de los datos

De dónde sale cada número que se publica, quién lo publica, con qué fecha y licencia, qué le
hacemos por el camino y por qué. Está escrito para que cualquiera pueda rehacer el recorrido sin
preguntarnos nada.

Tres documentos lo complementan y no se repiten aquí:

| Documento | Qué añade |
|---|---|
| `linaje.md` | El grafo fichero → script → fichero, generado leyendo el código |
| `criba.md` | Cuántos registros cae en cada filtro, contados sobre el CSV final |
| `supuestos.md` | Las decisiones nuestras de las que depende el resultado |
| `observaciones-datos.md` | Comprobaciones manuales contra la fuente original |

**Última revisión:** 2026-09-15.

---

## 1. Qué lee la web, exactamente

La web es estática: el navegador solo descarga ficheros ya calculados. Todo lo demás ocurre
antes, en el pipeline, y queda en el repositorio.

| Fichero que pide el navegador | Qué contiene | Sale de |
|---|---|---|
| `/data/geo/barrios.geojson` | Los 73 barrios de la ciudad | ICGC / Inside Airbnb, vía `export/preparar_geometria_web.py` |
| `/data/mapa/puntos_pisos.json` | 6.834 pisos: posición, plazas, dormitorios, precio de la noche, banda | `export/export_mapa_limpio.py` |
| `/data/mapa/puntos_hoteles.json` | 750 hoteles: habitaciones, plazas, banda, titular | `export/export_mapa_limpio.py` |
| `/data/mapa/puntos_restaurantes.json` | 9.479 locales: demanda hoy y en 2028 | `export/export_mapa_limpio.py` |
| `/data/mapa/barrios_hoy.json` | Las cifras de cada uno de los 73 barrios | `export/export_mapa_limpio.py` |
| `/data/mapa/dashboard.json` | Las cifras de la portada | `export/export_mapa_limpio.py` |
| `/data/mapa/turistas.json` | Turistas en el conjunto de datos y lo que dice el INE | `export/export_mapa_limpio.py` |
| `/data/mapa/licencias.json` | Licencias del registro, y cuántas tienen anuncio y cuántos pisos no tienen registro | `export/export_mapa_limpio.py` |
| `/data/mapa/flujo.json` | Distancia recorrida, bandas de origen y destino, barrios que suben y bajan | `export/export_mapa_limpio.py` |
| `/data/mapa/hoteles_pagina.json` | Categorías, ocupación mensual, ocupación por banda y hoteles anunciados | `export/export_mapa_limpio.py` |
| `/data/mapa/sustitucion_2028.json`, `flujos_2028.json` | El reparto por barrio y escenario | `gold/modelar_sustitucion.py` — solo los lee `/mapa-anterior` |

Hay más capas exportadas (`hoteles.json`, `restauracion.json`, `vut_por_barrio.json`,
`airbnb_por_barrio.json`, `resumen.json`) que el pipeline genera y **ninguna página consume**.
Están listas para la página de hoteles, no publicadas.

---|---|---|
| `/data/geo/barrios.geojson` | Los 75 barrios de la ciudad | ICGC / Inside Airbnb, vía `export/preparar_geometria_web.py` |
| `/data/mapa/sustitucion_2028.json` | 64 barrios × 5 escenarios: quién sale, quién llega, quién no cabe | `gold/modelar_sustitucion.py` |
| `/data/mapa/flujos_2028.json` | 887 movimientos barrio → barrio, y el centroide de cada barrio | `gold/modelar_sustitucion.py` |

Hay más capas exportadas (`hoteles.json`, `restauracion.json`, `vut_por_barrio.json`,
`airbnb_por_barrio.json`, `resumen.json`) que el pipeline genera pero **ninguna página consume
todavía**. Están listas para las páginas de KPIs y rankings, no publicadas.

---

## 2. Las fuentes originales

### 2.1 Registre de Turisme de Catalunya — Generalitat

- **Qué aporta:** el censo oficial de alojamiento de toda la provincia: 27.180 registros, de los
  cuales 23.975 HUT (viviendas de uso turístico), 1.442 hoteles, 120 apartaments turístics, más
  càmpings, turisme rural y llars compartides.
- **Cómo se obtiene:** API abierta de Transparència
  `https://analisi.transparenciacatalunya.cat/resource/t2h3-cgys.json`, filtrada por
  `prov_ncia='Barcelona'`.
- **Fecha de la descarga:** 27-28 de agosto de 2026.
- **Es la única fuente con titular** (CIF y razón social), y por eso mismo la más delicada.
- **Lo que no trae:** coordenadas, y en el caso de los HUT tampoco plazas.

**Tratamiento de datos personales.** Entre los titulares hay personas físicas. `data/raw/` no se
versiona y no se publica. Además, `bronze/unificar_registros.py` detecta los DNI por su forma
(ocho dígitos y una letra) y los anula antes de que salgan de bronze — no se confía en que la
fuente los marque. Ningún fichero publicado contiene nombre, DNI ni dirección de un particular.

### 2.2 Open Data BCN — Ajuntament de Barcelona

- **Licencia:** Creative Commons Attribution 4.0.
- **Tres datasets:**

| Dataset | Qué aporta | Estado |
|---|---|---|
| Licencias HUT 2016–2026Q1 | Coordenadas reales y plazas de las VUT de la ciudad | Serie viva |
| Hoteles de la ciudad | Barrio y distrito de cada establecimiento | **Snapshot congelado en 2023**, no sirve como serie |
| Mapa PEUAT | 12 zonas de regulación urbanística | Actualizado 2022; no entra todavía en el modelo |

Open Data BCN y el Registre **no son duplicados**: cada uno tiene campos que el otro no. Se cruzan
primero por número de registro oficial (clave real: cruzan 443 de 446 en hoteles y 10.556 en VUT) y
solo lo que queda suelto por dirección normalizada, y únicamente cuando la correspondencia es 1:1.
Cualquier ambigüedad se deja sin cruzar y se marca.

### 2.3 Inside Airbnb — volcado del 24 de junio de 2026

- **Qué aporta:** 15.406 anuncios de la ciudad, con precio, capacidad declarada (`accommodates`),
  licencia declarada y reseñas.
- **URL:** `https://data.insideairbnb.com/spain/catalonia/barcelona/2026-06-24/`
- **Es un anuncio, no una vivienda, y no es el registro oficial.** Cubre lo que se comercializa en
  una plataforma concreta en un día concreto.
- **Coordenadas desplazadas a propósito** hasta 150 m por la propia fuente. El punto del mapa es
  esa posición desplazada, no la dirección real de la vivienda.
- **El símbolo `$` del CSV crudo es un artefacto de su exportador.** El precio es en euros.

De esos 15.406 se llega a **6.834 viviendas** aplicando seis filtros encadenados, cada uno con su
recuento en `criba.md`: alojamiento ya reglado (901), habitaciones sueltas sin licencia (3.083),
habitaciones de hotel (14), alquiler de temporada de más de 31 noches (1.848), anuncios sin reseñas
desde septiembre de 2025 (876) y repeticiones del mismo anuncio (1.850).

**El salto que hay que decir en voz alta:** el registro oficial de la ciudad tiene 10.623 licencias
únicas y 61.826 plazas. Nosotros movemos los turistas de 6.834 viviendas anunciadas hoy en Airbnb — y no sus 30.067
plazas declaradas, sino las **11.516 personas** que hay dentro una noche cualquiera, porque esos
pisos no se llenan los 365 días. Las que no se anuncian en Airbnb no están en el mapa.

### 2.4 INE — Encuesta de Ocupación Hotelera

- **Cómo se obtiene:** API pública `servicios.ine.es/wstempus`, tablas 2078 (viajeros y
  pernoctaciones), 46298 (ADR) y 2076 (establecimientos, plazas y ocupación), punto turístico
  Barcelona, últimos 60 meses.
- **Dos usos distintos:**
  1. **Ocupación de partida** — `Grado de ocupación por habitaciones`, media de los doce últimos
     meses: **80,2%**. Es lo que descuenta las habitaciones ya vendidas antes
     de repartir a nadie.

     Se usa la ocupación por habitaciones y no la de plazas, que es más baja (67,9%), porque **la
     habitación es lo que limita a un hotel**: una plaza libre suele ser la segunda cama de una
     habitación ya vendida, no se puede vender aparte, y un grupo de cuatro no cabe en ella. Las
     dos cifras salen de la misma encuesta y el mismo mes; miden cosas distintas.
  2. **Estacionalidad** — trece años de serie, lo que permite llevar el precio de una ventana
     concreta a equivalente anual.
- **Su límite:** es agregado por punto turístico. Sirve para el nivel de la ciudad, nunca para
  atribuir un precio a un establecimiento.

El ADR por categoría llega además por el Portal de Dades del Ajuntament (2013–2026).

### 2.5 Precios de hotel raspados

- **Qué son:** dos exportaciones de portales de reserva, del 29 de septiembre de 2026, para
  estancias del 29 de septiembre al 7 de octubre.
- **Procedencia declarada sin adornos:** salen de raspar portales cuyos términos lo prohíben. **No
  se versionan, no se republican y no se citan como fuente.** Sirven para entrenar el modelo en
  local. Lo que se publica es la **banda económica**, no el euro, y la referencia oficial citable
  es el ADR del INE.
- **El cruce con el censo se hace por fiabilidad decreciente** —coordenada a menos de 60 m, nombre
  idéntico, nombre contenido y cerca, nombre contenido y único, parecido literal alto— y todo cruce
  bajo umbral se marca `dudoso` en vez de descartarse en silencio. Un segundo pase resuelve el
  reparto como asignación global (`linear_sum_assignment`) para que **ninguna ficha se asigne a dos
  hoteles**.

### 2.6 Censo comercial del Ajuntament, 2024 — restauración

- **Qué aporta:** 9.479 locales de la ciudad, de tres categorías: restaurante (4.429), bar (4.272)
  y comida rápida / take away (778).
- **Por qué solo el censo:** OSM infravalora la restauración de Barcelona en un 26% (7.430 frente a
  10.100). El censo es trabajo de campo municipal.
- **Su fecha real:** la serie comercial termina en 2024 y el trabajo de campo se reparte entre 2023
  y 2024 (el 57% visitado en 2023). No existe censo equivalente de 2026; se comprobó.
- **Ya no hay capa híbrida.** Hasta el 2026-09-15 el export publicaba OSM de toda la provincia pese
  a que la decisión era usar el censo; desde esa fecha publica el censo y solo la ciudad. OSM queda
  fuera del análisis.

### 2.7 Geometría — ICGC

WFS de divisiones administrativas del Institut Cartogràfic i Geològic de Catalunya: 311 municipios
de la provincia y 947 de Catalunya, en WGS84. Los 75 barrios vienen del GeoJSON de Inside Airbnb.

Antes de llegar al navegador se **repara** (dos barrios traen una autointersección), se
**simplifica** con Douglas-Peucker sobre coordenadas proyectadas —no sobre grados— y se
**recortan** los atributos internos. Si la superficie total cambia más de un 1% tras simplificar,
el script falla: la tolerancia era demasiado agresiva.

### 2.8 Observatori del Turisme a Barcelona

Informes de perfil del turista 2025. **Son infografías, no tablas**: se transcribieron a mano
verificando visualmente sobre la página renderizada. No alimentan el modelo; sirven de contexto.

### 2.9 Hoteles anunciados — prensa

`data/bronze/hoteles_nuevos_bcn.csv`, **recopilado a mano el 2026-10-05** de Hosteltur, ON Economia
y EjePrime. **No es un registro oficial**: no existe un dataset de hoteles previstos. Cuatro
entradas, cada una con su enlace:

| Hotel | Habitaciones | Qué es |
|---|---:|---|
| ibis budget Barcelona Center (Carrer d'Àvila 66, 22@) | 189 | **Obra nueva**, abierto en julio de 2026 |
| UMA House Granados (Carrer del Rosselló 205) | 56 | Reforma del Allegro Barcelona, un hotel que ya existe |
| NH Barcelona Paral·lel | 70 | Cambio de gestión y reforma de un hotel que ya existe |
| Bestprice Maragall | sin dato (62 camas) | Abierto en junio de 2026; por confirmar |

Solo las dos con dirección conocida llevan coordenada (ICGC) y salen en el mapa con una
exclamación. **Casi todo lo anunciado es reforma o cambio de gestión**: de obra nueva hay 189
habitaciones, el 3,3 % de las 5.706 que piden los pisos en un año medio. Sobre el PEUAT, las
fuentes dicen que en 2022 el 22@ pasó a la zona 2 (no abre un hotel nuevo salvo que cierre otro) y
que en noviembre de 2023 se aprobó una modificación que permite proyectos «singulares»; **no se ha
verificado su vigencia**. Quedan fuera pistas sin ubicación ni habitaciones (Círculo Condal, Akeah)
y el Meininger de la Fira, que está en L'Hospitalet.

### 2.10 Descartadas

AENA y Port de Barcelona: ninguna respondió al verificarlas (timeout / 503). El volumen y el origen
de los turistas los cubre el OTB.

---

## 3. Dónde se transforma cada cosa, y por qué

El pipeline tiene cuatro capas y la regla es que **nada salta una capa**: raw se descarga y no se
toca, bronze limpia y tipa, gold decide, exports agrega para el navegador.

### 3.1 Las decisiones que más mueven el resultado

**Dos unidades, y cada una responde a una pregunta distinta.** Conviene no mezclarlas:

| Pregunta | Unidad | Por qué |
|---|---|---|
| ¿Cuánto cuesta? | **La plaza** | Un piso para cuatro a 221 € y una habitación doble a 64 € no se comparan; 54 € y 43 € por plaza, sí |
| ¿Cabe la gente? | **La habitación** | Una plaza libre de hotel suele ser la segunda cama de una habitación ya vendida: no se vende aparte, y un grupo de cuatro no cabe en ella |

En el precio se divide entre la capacidad **declarada**, no entre los ocupantes reales, y se aplica
igual a los dos lados. En la capacidad se usa la habitación de hotel frente al dormitorio de la
vivienda, que son comparables sin corregir nada: 1,88 plazas por habitación en nuestros hoteles
frente a 2,00 plazas por dormitorio en Airbnb.

**Se publica la banda, no el euro.** El mismo hotel se mueve un ±22% sobre su propia mediana en
quince días según el tipo de habitación y la fecha. El modelo de imputación tiene un 27% de error:
por debajo de la variación natural de lo que mide. Una banda aguanta donde un euro exacto miente.
Los cortes son 40 / 70 / 120 € por plaza, y no son los cuartiles de ningún mercado: se eligieron
para que hoteles y Airbnb ocupen varias bandas cada uno.

**El precio de Airbnb se publica tal cual se anuncia.** Inside Airbnb no captura limpieza, comisión
ni impuestos. No se corrige porque el dato no permite saber quién cobra la limpieza aparte y quién
la lleva incluida; aplicar un importe común a todos sería falso para los segundos. Consecuencia
asumida: en estancias cortas la banda de Airbnb puede quedar por debajo de lo que se acaba pagando.

**Un precio de hotel tiene dos procedencias posibles, y solo dos.** La columna publicada es
`origen_precio`:

| Valor | Cuántos | Qué significa |
|---|---|---|
| `observado` | 451 | Cruzado con los precios raspados |
| `estimado` | 312 | Calculado por el modelo |
| vacío | 800 | Sin precio: resto de la provincia, más 5 estimaciones sin apoyo suficiente |

**Airbnb no aporta ni un solo precio de hotel.** Lo único que cruza del lado Airbnb al hotelero es
la geometría de barrios. La comparación entre el precio de Google y el de Airbnb para cuatro
apartaments turístics fue una comprobación manual, no un camino de datos.

La capa de análisis distingue siete matices más (`metodo_cruce`, `apoyo_estimacion`,
`estimacion_fiable`, `mae_modelo_eur`…) y ahí es donde deben estar: sirven para auditar el cruce y
el modelo. Viven en `hoteles_bcn_precio_estimado.csv` y no se publican.

**41% de los precios de hotel están estimados por un modelo; 3% de los de Airbnb.** El modelo se
entrenó solo con la ciudad de Barcelona, así que los 795 establecimientos del resto de la provincia
salen **sin banda** — es la respuesta honesta, y aparecen en el mapa igualmente porque su ubicación
y su capacidad sí constan. El error se mide con validación cruzada repetida, no con una partición
única: una versión anterior anunciaba 40,6 € de error con 86 casos apartados y la validación
cruzada sobre los mismos datos daba 57 €. Y se publica el error **por segmento**, porque los
hoteles con precio tienen 58 habitaciones de mediana y los que hay que imputar, 13.

**La ocupación de Airbnb se estima, porque no existe el dato.** Ninguna estadística pública dice
cuántas noches se alquila un piso turístico. Se calcula por dos vías independientes:

| Vía | Qué supone | Resultado |
|---|---|---|
| Calendario | Nada: `(365 − noches disponibles) / 365` | **38,3%** |
| Reseñas | Que reseña la mitad de los huéspedes y que la estancia media es de 3 noches | 38,8% |

**Que dos métodos que no comparten supuestos den lo mismo es lo que la hace publicable.** Con
estancias de 4 noches la segunda sube al 48,6%, así que la horquilla honesta es 38-48% y se toma el
extremo bajo: es el que coincide con el calendario, que no supone nada.

Consecuencia: los 6.834 pisos no alojan a 30.067 personas cada noche, sino a **11.516**.

**La estacionalidad hotelera se aplica a Airbnb.** El volcado es del 24 de junio y se lleva a
equivalente anual con el factor 1,188 de la serie del INE, **porque no existe serie estacional del
alquiler turístico**. Es el supuesto más frágil de todos: si el alquiler turístico fuera más plano
que el hotelero, estaríamos abaratando Airbnb de más.

### 3.2 Lo que calcula la web, y cómo

Todo es **un año medio**. Se descartó enseñar también julio: dos fechas a la vez confundían más
que aclaraban. (`/mapa-anterior` y el modelo aún guardan las dos.)

**Cada uno alquila una cosa distinta.** Un hotel alquila habitaciones; un piso de Airbnb se
alquila entero, tenga 1 o 3 dormitorios. Por eso la web no compara plazas con plazas: compara
habitaciones de hotel con pisos enteros, y la noche de una con la noche del otro. La plaza solo se
usa para la banda de precio, que es la única escala común (ver 3.1).

**a) Cuántos pisos tiene cerca un hotel y cuántos puede absorber** (el radio de 0 a 500 m).
Un piso pide tantas habitaciones como dormitorios declara (una, si declara cero: es un estudio) y
solo las ocupa el 38,3–48 % de las noches. El hotel ofrece las que tiene sin vender: el 19,8 % de
sus habitaciones (ocupación del 80,2 % por habitaciones, INE). Absorbe lo menor de las dos cifras.
**Cada hotel por separado**: otros hoteles del mismo radio compiten por los mismos pisos, así que
no se pueden sumar.

| Un año medio, toda la ciudad | Habitaciones |
|---|---|
| Libres en los hoteles | 8.841 |
| Que piden los pisos | 5.706 |
| Sin sitio | nadie |

**b) Los restaurantes: solo se mira a quien hoy cocina.** Los locales ya tienen clientes y eso no
se estima. Se mira un solo grupo: el turista que hoy se aloja en un piso porque así ahorra,
cocinando, y que al pasar a un hotel —sin cocina— tiene que salir a comer. Cada turista alojado
reparte su demanda a partes iguales entre los locales a menos de 200 m de donde duerme.

- **Hoy**, el turista de piso cuenta la **mitad** (tiene cocina). **En 2028**, ya en un hotel,
  cuenta **entero**.
- **La mitad es un supuesto, no un dato** (`PESO_PISO_EN_RESTAURACION`). De él sale por sí solo el
  aumento total (62.462 → 68.240 clientes potenciales por noche, +9,2 %). **Lo que sí aporta el
  modelo es dónde**: 4.245 locales ganan y 4.326 pierden.
- El % de cada local es sobre estos clientes, **no sobre todos los suyos**: los vecinos y el
  turista de hotel de siempre no están.
- No hay plazas de los locales: el censo no las trae. Las sillas de terraza (127.482) se
  descartaron el 10 de septiembre.

**c) En qué hotel acaba cada turista: por banda.** No se mira si prefiere precio o ubicación:
se mira la banda directamente (`gold/modelar_flujos_banda.py`). Cada turista va a un hotel de **su
banda**, el más cercano con habitaciones libres. Si en su banda no queda sitio, va a la **siguiente
más cara**, y así hasta la más cara; solo después, y como último recurso, baja. La distancia no
limita: si el único hotel libre de su banda está al otro lado de la ciudad, va. La banda es la
**por plaza** en los dos lados, la única comparable. La capacidad es un límite duro.

Los pisos eligen en orden aleatorio con semilla fija: el orden decide quién se queda con las
habitaciones escasas de una banda, no cuántos caben. Con tres órdenes distintos la mediana de
distancia se mueve entre 0,37 y 0,38 km. Supone la misma ocupación del 80,2 % en todas las bandas, y
los hostales probablemente estén más llenos.

| Banda (por plaza) | Habitaciones libres en hoteles | Que piden los pisos |
|---|---|---|
| € | 57 | 1.629 |
| €€ | 1.392 | 2.967 |
| €€€ | 5.065 | 1.007 |
| €€€€ | 2.327 | 103 |

- **Los hoteles baratos son el cuello de botella.** Solo el **34 %** de los turistas encuentra hotel
  de su banda, el 46 % sube una banda y el 20 % sube dos o más. El volumen acaba en los €€€ (72 %),
  pero la **presión de precio** es de los €: 28 habitaciones pedidas por cada una libre.
- **Cuánto se alejan:** mediana de 0,37 km, media de 0,67, el 90 % a menos de 1,6 km, el 6,5 % a más
  de 2 km, máximo 7,3 km.
- **Qué barrios suben y bajan:** ganan turistas el Raval (+731 por noche), el Parc i la Llacuna del
  Poblenou (+451) y Hostafrancs (+286); pierden la Sagrada Família (−805, −63 %), la Vila de Gràcia
  (−604, −50 %) y Sant Antoni (−503, −29 %). Un barrio con muchos pisos y pocos hoteles pierde.
- **Ocupación hotelera:** pasa del 80,2 % al **93,0 %** en un año medio. Por banda, los € y los €€
  llegan al 100 %, los €€€ al 96,4 % y los €€€€ al 81,1 %.

**d) Qué recibe cada hotel.** El mapa enseña, para cada hotel, las habitaciones que tiene, las
ocupadas hoy (80,2 %), las ocupadas en 2028 (esas más las que recibe de los pisos según este
reparto) y de cuántos pisos le llegan. El radio de 0 a 500 m es aparte: cuenta los pisos que tiene
cerca (pisos, plazas y habitaciones), sin pasar por el reparto.

**e) Turistas en el conjunto de datos y frente al INE.** Hoteles: plazas × 67,9 % de ocupación =
**56.715 turistas por noche**, frente a **60.133 pernoctaciones por noche** del INE (ago 2025 –
jul 2026): un 6 % menos, que es lo esperable de un conjunto sin todos los hostales y pensiones.
Pisos: 11.516–14.432 por noche (38,3–48 %), 4,2–5,3 millones de pernoctaciones al año y, a **3
noches de estancia (supuesto)**, 1,4–1,8 millones de turistas. El INE: 9,2 millones de viajeros,
21,9 millones de pernoctaciones, 2,38 noches de estancia y 82 % de extranjeros. No mide pisos.
**En personas:** nuestros hoteles son 56.715 × 365 / 2,38 = **8,7 millones de viajeros** al año frente
a los 9,2 del INE, y los pisos, **entre el 17 y el 20 % de los turistas de nuestro conjunto de datos** (por noche:
11.516–14.432 en pisos frente a 56.715 en hoteles; no interviene la estancia). Lo que el INE cuenta
en personas, de dónde vienen y cuánto se quedan, nuestros datos no lo tienen: contamos camas y
noches.

**f) Licencias y pisos sin registro** (`licencias.json`, última tarjeta de `/airbnb`). Del registro
oficial de la ciudad (10.623 licencias únicas, 61.826 plazas) se cruzan por número de licencia con
los anuncios: 4.756 licencias están entre los 6.834 pisos, 473 solo con anuncios descartados y
**5.394 no tienen ningún anuncio** (30.980 plazas). Aparte, dentro de los 6.834 hay 1.849 pisos sin
registro acreditado (334 con un número imposible, 1.351 que no declaran licencia válida). Detalle y
cautelas en `supuestos.md` → C5 y C6. **Hoy esos 1.849 siguen contados** como turistas a realojar.

### 3.3 Lo que nunca sale del pipeline

- **Del piso, solo lo que pinta el mapa.** Es una decisión del proyecto (2026-10-04): cada piso
  sale como punto con su posición —ya desplazada hasta 150 m por la fuente y redondeada a 5
  decimales—, plazas, dormitorios, precio y banda. **Sin id, sin nombre del anuncio, sin anfitrión
  y sin número de licencia.** El anfitrión solo aparece agregado: por barrio si tiene 5 pisos o más en él, y en la portada los
  cinco con más pisos de la ciudad, siempre que tengan al menos 20 (Sweett, 265; AB Apartment
  Barcelona, 236…). `host_name` es el nombre público en Airbnb; un particular con pocos pisos nunca
  sale.
- **Del hotel, la sociedad titular** (razón social del Registre de Turisme), nunca una persona
  física: el marcador `No aplica` del registro se respeta y no se publica.
- **Nombres, DNI y datos de titulares particulares.**
- **Los precios raspados en crudo.**

Cada punto que sí se publica lleva su `precision`: `exacta` (registro oficial), `geocodificada`
(deducida de la dirección con el ICGC y verificada contra el polígono del municipio) o `desplazada`
(Inside Airbnb la mueve hasta 150 m). Pintarlas con el mismo símbolo daría a entender una precisión
que no tenemos.

---

## 4. Lo que este trabajo no puede decir

1. **No cubre las 10.623 licencias de la ciudad, cubre 6.834 viviendas anunciadas en Airbnb.**
   5.394 licencias, con 30.980 plazas, no tienen ningún anuncio y no están (`supuestos.md` → C5).
2. **No sabe qué quiere un turista.** Por eso la barra de precio-ubicación la mueve quien mira, y
   no hay un escenario "correcto" marcado.
3. **No predice qué harán los hoteles.** El modelo reparte a capacidad y precio de hoy. Si los
   precios suben al desaparecer la oferta alternativa —que es lo esperable— el reparto cambia.
4. **No mide meses.** Todo es un año medio. En los picos del verano habrá menos hueco en los hoteles.
5. **Un hotel no tiene un precio, tiene un rango.** Se publica una banda, nunca el euro. Un piso sí
   lleva el precio que anuncia.
6. **Lo que factura un piso es un orden de magnitud**: ocupación del 38,3–48 % × 365 noches × precio
   de la noche. No hay dato de facturación.
7. **No dice cuánto subirá el precio.** Depende de la estacionalidad (que existiría aunque Airbnb no
   se fuera), de los turistas que se vayan a otros municipios, de los pisos que no entran en la ley
   y de la oferta nueva que permita el PEUAT. Los hoteles baratos y los hostales son los que más
   presión de precio recibirían; no se cuantifica.

---

## 5. Cómo rehacerlo

```bash
python pipeline/sources/descargar_fuentes.py
python pipeline/sources/descargar_ine_barcelona.py
```

`data/raw/` no se versiona (≈90 MB redescargables, más los datos personales del Registre). El resto
del pipeline es determinista: `linaje.md` dice en qué orden corre cada script, y se regenera con
`python pipeline/generar_linaje.py` después de cualquier cambio, junto con
`python pipeline/generar_criba.py` para los recuentos.
