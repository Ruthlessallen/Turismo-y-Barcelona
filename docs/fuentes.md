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

La web es estática: el navegador solo descarga tres ficheros. Todo lo demás ocurre antes, en el
pipeline, y queda en el repositorio.

| Fichero que pide el navegador | Qué contiene | Sale de |
|---|---|---|
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
- **Coordenadas desplazadas a propósito** hasta 150 m por la propia fuente. Por eso ningún anuncio
  se publica como punto: se agrega por barrio.
- **El símbolo `$` del CSV crudo es un artefacto de su exportador.** El precio es en euros.

De esos 15.406 se llega a **6.834 viviendas** aplicando seis filtros encadenados, cada uno con su
recuento en `criba.md`: alojamiento ya reglado (901), habitaciones sueltas sin licencia (3.083),
habitaciones de hotel (14), alquiler de temporada de más de 31 noches (1.848), anuncios sin reseñas
desde septiembre de 2025 (876) y repeticiones del mismo anuncio (1.850).

**El salto que hay que decir en voz alta:** el registro oficial tiene 24.075 licencias y 61.899
plazas. Nosotros movemos 30.067 turistas, los de 6.834 viviendas anunciadas hoy en Airbnb. Las que
no se anuncian en Airbnb no están en el mapa. La web lo advierte en el mapa de flechas.

### 2.4 INE — Encuesta de Ocupación Hotelera

- **Cómo se obtiene:** API pública `servicios.ine.es/wstempus`, tablas 2078 (viajeros y
  pernoctaciones), 46298 (ADR) y 2076 (establecimientos, plazas y ocupación), punto turístico
  Barcelona, últimos 60 meses.
- **Dos usos distintos:**
  1. **Ocupación de partida** — `Grado de ocupación por plazas`, media de los doce últimos meses
     (67,9%). Es lo que descuenta las plazas hoteleras ya ocupadas antes de repartir a nadie.
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

### 2.9 Descartadas

AENA y Port de Barcelona: ninguna respondió al verificarlas (timeout / 503). El volumen y el origen
de los turistas los cubre el OTB.

---

## 3. Dónde se transforma cada cosa, y por qué

El pipeline tiene cuatro capas y la regla es que **nada salta una capa**: raw se descarga y no se
toca, bronze limpia y tipa, gold decide, exports agrega para el navegador.

### 3.1 Las decisiones que más mueven el resultado

**La plaza es la unidad comparable.** Un piso entero para cuatro a 221 € y una habitación doble a
64 € no se pueden comparar; 54 € y 43 € por plaza sí. Se divide entre la capacidad **declarada**,
no entre los ocupantes reales, y se aplica igual a los dos lados.

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

**La estacionalidad hotelera se aplica a Airbnb.** El volcado es del 24 de junio y se lleva a
equivalente anual con el factor 1,188 de la serie del INE, **porque no existe serie estacional del
alquiler turístico**. Es el supuesto más frágil de todos: si el alquiler turístico fuera más plano
que el hotelero, estaríamos abaratando Airbnb de más.

### 3.2 El modelo de 2028

Cada VUT que cierra busca alojamiento reglado. Cada hotel recibe una nota:

```
utilidad = w × cercanía + (1 − w) × parecido_de_precio
```

- **`w` no se estima, y es deliberado.** Se intentó estimarlo con la demanda actual de Airbnb y no
  funciona: la distancia al centro no predice la demanda (p = 0,48, R² = 0,001) y el coeficiente
  del precio sale **positivo**, que es causalidad inversa y no sensibilidad al precio. Además un
  turista alemán y uno andaluz no tienen la misma sensibilidad y ningún dato disponible los
  distingue. Se precalculan cinco valores de `w` y la web deja elegir: la barra del mapa es eso.
- **Los hoteles no están vacíos.** Se descuenta la ocupación real del INE (67,9%). Quedan 27.010
  plazas libres para 30.067 turistas: **3.057 no caben en ningún escenario**. En noviembre, con
  ocupación del 55,6%, cabrían todos; en julio, al 79,1%, no cabrían 12.490.
- **Se usa la ocupación media anual, no la mensual**, porque los precios del proyecto son
  equivalentes anuales. Cruzar precio anual con ocupación de julio mezclaría dos escalas de tiempo.
- **El reparto va de la VUT más cara a la más barata.** Hace falta un orden para que el resultado
  sea determinista, y **no es neutral**: quien paga menos se queda sin sitio. Está dicho aquí
  porque cambia quién aparece en el mapa como "sin sitio".
- **La capacidad es un límite duro.** Un hotel de 200 plazas no absorbe 500.
- **La distancia se mide en kilómetros, no en grados.** A 41,39° N un grado de longitud mide 83 km
  y uno de latitud 111: mezclarlos deformaría el mapa a favor del este-oeste.
- **Los flujos por debajo de 20 turistas no se publican.** Dos o tres personas entre dos barrios no
  dicen nada y llenan el mapa de rayas.

La segmentación por precio **no está impuesta, emerge**: el 82% de las plazas VUT de banda `€€€€`
acaba en hoteles de 4-5 estrellas, y ninguna plaza `€` o `€€` llega a un 5 estrellas.

### 3.3 Lo que nunca sale del pipeline

- **Ningún dato a nivel de vivienda o dirección individual.** Un hotel o un restaurante es un
  establecimiento abierto al público y se publica como punto; una VUT es una vivienda y un anuncio
  de Airbnb también, y esos se agregan siempre por barrio o municipio. No es una precaución de
  estilo: es la línea que separa analizar un mercado de señalar domicilios.
- **Nombres, DNI y datos de titulares particulares.**
- **Los precios raspados en crudo.**

Cada punto que sí se publica lleva su `precision`: `exacta` (registro oficial), `geocodificada`
(deducida de la dirección con el ICGC y verificada contra el polígono del municipio) o `desplazada`
(Inside Airbnb la mueve hasta 150 m). Pintarlas con el mismo símbolo daría a entender una precisión
que no tenemos.

---

## 4. Lo que este trabajo no puede decir

1. **No cubre las 24.075 licencias, cubre 6.834 viviendas anunciadas en Airbnb.** Lo que no se
   anuncia allí no está.
2. **No sabe qué quiere un turista.** Por eso la barra de precio-ubicación la mueve quien mira, y
   no hay un escenario "correcto" marcado.
3. **No predice qué harán los hoteles.** El modelo reparte a capacidad y precio de hoy. Si los
   precios suben al desaparecer la oferta alternativa —que es lo esperable— el reparto cambia.
4. **No mide meses.** Todo es equivalente anual, con la salvedad de las cifras de julio y noviembre
   que se dan aparte como contexto.
5. **Un hotel no tiene un precio, tiene un rango.** Se publica una banda precisamente por eso.

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
