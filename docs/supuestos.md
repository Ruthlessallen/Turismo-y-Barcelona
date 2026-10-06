# Supuestos del análisis

Cada punto de esta lista es un sitio donde el resultado depende de una decisión nuestra y no del
dato. No son defectos: son las decisiones que hacen falta para poder decir algo. Lo que sí sería un
defecto es tomarlas y no dejarlas escritas.

El detalle y las comprobaciones que las respaldan están en `observaciones-datos.md` (verificaciones
manuales), `criba.md` (recuentos de cada filtro, generado del dato) y `data-model.md` (diccionario).

**Última revisión:** 2026-09-04, con la banda económica ya aplicada a los dos lados.

---

## A. Los que sostienen la comparación entre hoteles y Airbnb

### A1. La plaza es la unidad comparable **del precio**

Se divide entre la capacidad **declarada**, no entre los ocupantes reales. Un piso para cuatro con
una pareja dentro cuenta como cuatro plazas, igual que una habitación doble de hotel cuenta como
dos aunque duerma una persona. Es precio por plaza **disponible**, y se aplica igual a los dos
lados: es lo que hace la comparación válida.

**Ojo: esto vale para el precio, no para la capacidad.** Desde el 2026-10-04 el reparto de 2028 se
hace en **habitaciones**, no en plazas (ver F1). Son dos preguntas distintas y cada una tiene su
unidad; mezclarlas fue justo el error que hubo que corregir.

### A2. Los dos divisores

| | Precio de partida | Divisor | Mediana del divisor |
|---|---|---|---|
| Hotel | una habitación por noche | plazas / habitaciones | 1,94 |
| Airbnb | el anuncio entero por noche | `accommodates` | 4 |

Si la ratio de plazas por habitación estuviera mal, el eje hotelero se desplaza entero.

### A3. Los cortes 40 / 70 / 120 EUR por plaza valen para los dos mercados

No son los cuartiles de ninguno de los dos. Se eligieron para que ambos ocupen varias bandas: con
cuartiles comunes, el mercado barato se partiría por la mitad y el hotelero quedaría entero en la
banda alta. Cambiar los cortes cambia todo el reparto publicado.

### A4. La estacionalidad hotelera del INE sirve para corregir Airbnb

El volcado de Airbnb es del 24 de junio y se lleva a equivalente anual con el factor 1,188 de la
serie hotelera del INE, **porque no existe una serie estacional del alquiler turístico**. Es
razonable —los dos venden noches a los mismos visitantes— pero no está medido.

**Es el supuesto más frágil de la lista.** Si el alquiler turístico tuviera una estacionalidad más
plana que la hotelera, estaríamos abaratando Airbnb de más; si la tuviera más marcada, al revés.

### A5. El precio de Airbnb es la tarifa anunciada y se publica tal cual

De nuestros 6.834 anuncios, 6.743 traen cotización con el desglose completo. En **esas 6.743**,
`cleaning_fee`, `service_fee` y `taxes` vienen vacíos: Inside Airbnb no captura esos cargos.

No se corrige, y esa es la decisión. El dato no permite saber quién cobra la limpieza aparte y
quién la lleva ya incluida en la tarifa; aplicar un importe común a todos sería falso para los
segundos. El precio de hotel sí incluye todo salvo la tasa turística.

**Consecuencia asumida:** en las estancias cortas, que son las que compiten con el hotel, la banda
de Airbnb puede quedar por debajo de lo que se acaba pagando.

Sí viene relleno `discount_amount` en 594 de las 6.743: en esos casos el precio anunciado ya
incorpora un descuento aplicado.

---

## B. La criba de 15.406 a 4.985 (6.834 tras los seis primeros descartes)

Cada filtro es un supuesto sobre qué alcanza la eliminación de 2028. Los recuentos exactos están en
`criba.md`, generado del dato.

### B1. Los 901 de alojamiento reglado no son VUT

Se identifican por prefijo de licencia (HB, AJ, ATB, ATCC, HCC). Cuentan en el otro lado del
análisis, el de la oferta que absorbe.

### B2. Las 3.083 habitaciones que no declaran HUTB quedan fuera

No son lo que la ley elimina y no hay nada que las ligue a una licencia. **Sí entran** las
habitaciones que declaran un HUTB, porque un HUTB ampara la cesión del alojamiento completo y
usarlo para vender una habitación es una irregularidad propia.

**Comprobado si se podía afinar** (2026-09-04): de las 3.083, solo **173 (5,6%)** pertenecen a un
anfitrión que declara un HUTB en algún otro anuncio suyo, y se concentran en **23 anfitriones**.
De esas 173, **130 declaran una exención en su propio campo de licencia**: el anfitrión no ha
callado, ha dicho otra cosa. Arrastrarlas por lo que declara en otro anuncio sería sustituir su
declaración por una inferencia nuestra.

Quedan **40** donde el anfitrión calla en este anuncio y declara en otro. Se probó a afinar más,
exigiendo además que la habitación estuviera **en el mismo barrio** que un HUTB suyo: cumplen 20,
de **7 anfitriones**. Pero esos anfitriones tienen carteras de 13 a 17 licencias repartidas en 6 a
8 barrios, así que para ellos coincidir de barrio **es casi seguro por azar**: el criterio no
discrimina. Y se apoyaría en la variable menos fiable que tenemos, porque la asignación individual
de barrio falla el 12% (ver G1).

Se mantiene el criterio. El techo de lo que se ganaría es un 5,6% de ese grupo —20 anuncios sobre
6.834, el 0,3%—, para tres cuartas partes iría en contra de lo que el propio anuncio declara, y una
licencia HUTB es de una vivienda, no de un anfitrión.

### B3. Las 14 `Hotel room` quedan fuera declaren lo que declaren

Son habitaciones de establecimiento hotelero vendidas en la plataforma.

### B4. Las 1.848 estancias de 32 noches o más quedan fuera del ámbito

El Decret Llei 3/2023 define el uso turístico como cesión por un período de tiempo continuo *igual
o inferior a 31 días*. **31 noches sigue siendo uso turístico**; la exención empieza en 32. En
`observaciones-datos.md` está por qué esa frontera importa: la mitad de las exenciones declaradas
se apoyan en 31 noches, que no eximen.

### B5. Sin reseñas desde septiembre de 2025 se considera inactivo

**Es un proxy, no una medida.** Un proxy es una variable que se usa en lugar de la que interesa de
verdad, porque esa no está en el dato. Aquí interesa saber si el piso **se está alquilando**, y eso
Inside Airbnb no lo publica: lo que publica es la fecha de la última reseña. Se usa como sustituto
porque una reseña implica una estancia real.

Falla en las dos direcciones, y conviene saber cómo:

- **Falso inactivo:** un piso que se alquila pero cuyos huéspedes no reseñan. Una parte importante
  de las estancias no deja reseña, así que un piso con poca ocupación puede pasar un año sin
  ninguna estando activo. Se descartan 876 anuncios por esta vía y algunos estarán vivos.
- **Falso activo:** un anuncio con una reseña reciente que se retiró al día siguiente.

La alternativa —`availability_365`— es peor: un calendario abierto no prueba actividad, y un
anfitrión puede cerrarlo sin dejar de alquilar por otra vía.

**Y la otra alternativa, quedarse con los que tengan licencia vigente, sería circular.** Se probó
(2026-09-04) y el reparto lo desaconseja solo:

| | Descartados por inactividad | Los 6.834 que entran |
|---|---:|---:|
| Declaran HUTB | 37% | 86% |
| Consta en el registro | 33% | 74% |

Readmitiría 293 con licencia y **ni uno sin licencia**, subiendo mecánicamente el porcentaje de
regulares. El filtro decidiría quién entra usando la misma variable cuyo reparto queremos medir.
Aparte, el registro dice que la licencia existe, no que el piso se alquile: 239 de los 876 tienen
su última reseña en 2023 o antes.

**Lo que sí se hace** es contarlos aparte, sin tocar ningún denominador: la celda 43 del cuaderno
publica los 293 como **capacidad latente** en `gold/airbnb_capacidad_latente.csv`. Son viviendas
con licencia vigente que hoy no se anuncian, a las que la eliminación de 2028 alcanza igual y que
pueden volver al mercado. Antes desaparecían del análisis sin dejar rastro.

Llegan a la web agregadas por barrio en `airbnb_por_barrio.json`, en un objeto `latente` aparte de
`anuncios`: **no suman a la oferta anunciada**, porque no está anunciada. `recientes` separa las
203 que dejaron de anunciarse en 2024 o después de las licencias dormidas desde hace una década:
ante la pregunta de si esa vivienda puede volver al mercado, no son lo mismo.

**Revisión del 2026-10-05. Decisión: se mantiene el descarte.** Qué hay dentro de
los 876:

| | Anuncios | Plazas |
|---|---:|---:|
| Descartados por inactividad | 876 | 3.980 |
| De ellos, con licencia en el registro (la capacidad latente) | 293 | 1.534 |
| Sin licencia o sin acreditar | 583 | — |
| Con el calendario abierto (`availability_365` > 0) | 759 | — |
| Con alguna reseña en los últimos 12 meses | 172 | — |

Ninguno es un anuncio nuevo: todos tienen al menos una reseña, y la mediana de la última es
octubre de 2024. Lo que está en juego es poco: solo los **293 con licencia** son lo que la ley de
2028 elimina (+4,3 % sobre los 6.834 pisos de entonces). Los otros 583 no tienen licencia que eliminar. Esos 293
ya se publican aparte como capacidad latente, sin sumarlos a la oferta anunciada.

### B6. Los duplicados se deciden por licencia, no por nombre y coordenadas

Comprobado que la regla textual destruía 43 viviendas reales: mismo anfitrión, mismo nombre, mismo
precio y **licencias distintas** (HUTB-079007 / 079009 / 079012). Son pisos diferentes del mismo
edificio anunciados igual. La desduplicación por licencia los conserva.

### B7. Los pisos sin registro acreditado quedan fuera

**Decisión del 2026-10-06.** La eliminación de 2028 quita licencias. Un piso que no tiene ninguna
acreditada en el registro oficial no tiene licencia que perder: si sigue operando, lo hará fuera del
mercado legal, y no hay dato que diga que se vaya. Contarlo como turista que hay que realojar
inflaba el efecto. Son 1.849 de los 6.834 pisos (6.301 plazas, el 21 % de las plazas), el último
descarte del embudo (`gold/separar_sin_registro.py`). Detalle en C6.

**Qué cambia al quitarlos** (año medio):

| | Con los 6.834 | Con los 4.985 |
|---|---:|---:|
| Turistas por noche que se realojan | 11.516 | 9.102 |
| Habitaciones de hotel que absorben | 5.706 | 4.486 |
| Ocupación hotelera | 93,0 % | 90,2 % |
| Turistas nuevos en hoteles | +20,3 % | +16,0 % |
| Julio, sin sitio | 1.273 turistas | nadie |

**Lo que no se sabe.** «No consta» no es «es ilegal»: puede ser una licencia recién concedida que el
registro aún no recoge (C1). Y no hay dato de si estos pisos seguirán anunciándose. Para volver al
criterio anterior basta no ejecutar `separar_sin_registro.py` y reejecutar `revisar_airbnb_v2.ipynb`.

---

## C. Licencia

### C1. El registro oficial está completo y al día

Lo que no consta en él, no existe. Si el registro llevara retraso en las altas, parte de las
`licencia_sin_acreditar` serían licencias reales recién concedidas.

### C2. HUTB-80024 es el número más alto emitido

Los 889 anuncios que declaran un número por encima no pueden corresponder a una licencia real. De
ellos, 36 son compatibles con un error de tecleo y 853 tienen un dígito de más. Y **25 de esos
números aparecen en anuncios de anfitriones distintos** —hasta quince para el mismo número—, lo que
descarta el error independiente.

### C3. Un HUTB no ampara una habitación suelta

631 anuncios pasan a irregulares por **qué** venden, no por falta de licencia.

### C4. No se afirma que la licencia no exista

Lo que se mide es el **incumplimiento de declararla en la plataforma**. El campo lo rellena el
anfitrión, y no declarar no es carecer. Este supuesto es el que sostiene que el dashboard hable de
*sin licencia acreditada* y nunca de infracción.

---

### C5. Hay licencias sin ningún anuncio, y son la mitad de las plazas

El registro oficial (Open Data BCN, 2016–2026 T1) tiene 10.718 filas y **10.623 licencias únicas**,
con barrio, dirección, coordenadas y plazas (61.826 en total, mediana de 5 por licencia). **No trae
habitaciones.** La fecha de inicio solo se conoce de forma indirecta: el año del número de
expediente (2008–2026, concentrado en 2012–2014), que es el de la solicitud, no el del alta.

| Licencias únicas | Cuántas | Plazas del registro |
|---|---:|---:|
| Con anuncio entre los 4.985 pisos | 4.736 | 28.111 |
| Solo con anuncios que se descartan | 493 | 2.735 |
| **Sin ningún anuncio en Airbnb (junio 2026)** | **5.394** | **30.980** |

De ahí la diferencia entre las 23.766 plazas de los pisos analizados y las 61.826 del registro. Se cuenta en
la última tarjeta de la página `/airbnb`, junto a los datos del registro: 10 distritos (el Eixample,
4.870 licencias), licencias en vigor por trimestre (9.603 en 2018-T2, mínimo de 9.300 en 2022-T2,
10.730 en 2026-T1), el expediente más antiguo (2008) y el HUTB más alto emitido (80024). El modelo ya las
deja fuera: sin anuncio ni reseña no hay evidencia de actividad. Pueden estar en otras plataformas,
dormidas o ser licencias fantasma. **Cota superior, no calculada en la web:** si todas estuvieran
activas, serían hasta 30.980 plazas más. En las licencias que sí casan, Airbnb declara 23.888 plazas
frente a las 29.937 del registro (un 25 % menos).

### C6. 1.849 de los 6.834 pisos no tienen registro acreditado, y quedan fuera

Dentro de los 6.834 pisos (antes del último descarte), según lo que su anuncio dice de la licencia y
lo que el registro contesta (`motivo_estado`):

| Grupo | Pisos | Plazas |
|---|---:|---:|
| Con registro que consta (**se quedan**) | 4.985 | 23.766 |
| Dicen tener registro y no consta | 498 | 2.093 |
| — número imposible (por encima del HUTB-80024, o de relleno como 123456) | 334 | 1.447 |
| — número que no consta | 102 | 492 |
| — número válido, pero de una habitación o de un hotel | 62 | 154 |
| Deberían tenerlo y no lo declaran | 1.351 | 4.208 |
| — no declara nada | 342 | 1.236 |
| — declara exención | 373 | 1.263 |
| — habitación con un número que no consta | 400 | 812 |
| — anfitrión con licencias, ninguna de esta vivienda | 236 | 897 |

**«No consta» no es «es mentira».** Solo el número imposible lo es con seguridad. Un número que no
consta puede ser una licencia recién concedida que el registro aún no recoge (C1) o un error al
escribirlo.

**Qué se hace con ellos.** Los 1.849 salen del análisis (B7): no cuentan como turistas a realojar. Se
cuentan aparte, debajo de la tarjeta final de `/airbnb`, y siguen en
`gold/airbnb_excluidos_web.csv` con `motivo_exclusion = sin_registro_acreditado`.

---

## D. Precio de Airbnb

### D1. `price` es la tarifa diaria del anuncio entero

Verificado: coincide con `price_quote_price_per_night` (ratio 1,00 en 13.355 anuncios del volcado)
y `price_quote_raw` declara la moneda como EUR. No es una suposición.

### D2. Ocho precios imposibles se recortan, no se eliminan

Al quíntuplo de la mediana de su tramo de estancia. El anuncio existe, tiene su capacidad y su
barrio, y cuenta como oferta; lo que no vale es su precio. Máximo tras el recorte: 324,4 EUR/plaza.

### D3. 221 precios (3,2%) son estimados por modelo

LightGBM, error de 13,49 EUR por plaza (±0,41 en validación cruzada repetida) sobre una mediana de
61,5 —un 22% relativo—. **Ninguna estimación alcanza la banda más alta:** un ensemble de árboles
promedia hojas y no predice fuera de lo que vio. La columna `precio_plaza_es_estimado` permite
separarlos siempre.

### D4. El corte en 7 noches separa dos mercados

A partir de la séptima noche el precio por plaza cae a la mitad. El reparto es muy desigual: 6.061
anuncios en el tramo corto, 727 en el largo (28-31) y **solo 46 en el medio (7-27)**, que queda
prácticamente vacío.

---

## E. Hoteles

### E1. La imputación pesa mucho más que en Airbnb

**307 de 758 bandas hoteleras son estimadas, unos dos quintos, frente al 3,2% de Airbnb.** Es la
asimetría más importante entre los dos lados y debe acompañar a cualquier comparación de las dos
distribuciones.

### E2. La banda más barata no se puede imputar en hoteles

De 52 hoteles realmente por debajo de 100 EUR, el modelo acierta 2; los otros 50 los sitúa una
banda por encima. Solo 54 filas del entrenamiento bajan de ese umbral. Se publica esa banda
únicamente cuando es observada.

### E3. El precio raspado se valida contra el ADR oficial del INE

Desvíos de −3% a +12% por categoría, en la dirección esperada: el anunciado es mayor o igual que el
efectivamente cobrado.

### E4. Un hotel no tiene un precio, tiene un rango

Comprobado a mano sobre Hostemplo: de 138 a 219 EUR según habitación y fecha dentro de la misma
quincena. Un ±22% que pone suelo a lo que cualquier método puede lograr.

### E5. Cinco estimaciones sin apoyo suficiente

Marcadas en `apoyo_estimacion`: pensiones (6 estimadas con 2 ejemplos), residencias (3 con 4) y
apartaments turístics (5 con 8).

---

---

## F. El reparto de 2028

Añadidos el 2026-10-04, al corregir el modelo. Antes de esa fecha el reparto se hacía en plazas y
solo descontaba la ocupación del lado hotelero, lo que producía una escasez que el dato no sostiene.

### F1. Cada uno alquila una cosa distinta

Un hotel alquila **habitaciones**, sea de 1, 2 o 3 plazas. Un piso de Airbnb se alquila **entero**,
sea de 1, 2 o 3 dormitorios. La web no compara plazas con plazas ni habitaciones con dormitorios
como si fueran lo mismo: compara habitaciones de hotel con pisos enteros, y la noche de una con la
noche del otro. La plaza solo se usa para la banda de precio (A1), la única escala común.

**Supuesto abierto:** para saber cuántas habitaciones de hotel pide un piso se usan sus
dormitorios, pero lo correcto sería `ceil(grupo / 2)` y el tamaño real del grupo no está en el
dato (Airbnb publica la capacidad, no quién viene). Con otras reglas, las habitaciones pedidas en
un año medio van de 2.617 (parejas) a 6.175 (capacidad llena), frente a las 8.841 libres.

#### La habitación es la unidad de la capacidad

Una plaza libre de hotel suele ser la segunda cama de una habitación ya vendida: no se puede vender
aparte, y un grupo de cuatro no cabe en ella. Lo que limita a un hotel es la habitación.

Del lado de la vivienda se usa el dormitorio (`bedrooms`), que falta en el 2,8% de los anuncios y
ahí se deduce como `accommodates / 2`, la mediana observada en los que sí lo declaran.

**Las dos unidades son comparables sin corregir nada:** 1,88 plazas por habitación en nuestros
hoteles frente a 2,00 por dormitorio en Airbnb. Si esa ratio se separara, la comparación se
desplazaría entera.

### F2. Se descuenta la ocupación en los dos lados

| Lado | Ocupación | Procedencia |
|---|---|---|
| Hotel | 80,2% anual | INE, **por habitaciones** |
| Airbnb | 38,3% anual, y 48% como extremo alto | Estimada, ver F3 |

Descontarla solo en el lado hotelero comparaba una capacidad declarada con una ocupación real.

### F3. La ocupación de Airbnb se estima, y no hay dato oficial

Ninguna estadística pública dice cuántas noches se alquila un piso turístico. Dos vías
independientes:

| Vía | Qué supone | Resultado |
|---|---|---|
| Calendario, `(365 − availability_365) / 365` | nada | **38,3%** |
| Reseñas, `reseñas_12m / 0,50 × 3 noches / 365` | tasa de reseña y duración | 38,8% |

Se publica el 38,3% porque es el que no depende de suponer nada. **Es el supuesto más frágil de
esta sección**: con estancias de 4 noches la segunda vía da 48,6%, y a esa ocupación julio se
quedaría corto para unos 3.000 turistas en vez de 1.273.

### F4. La estacionalidad de Airbnb se toma de la hotelera

No existe una serie estacional del alquiler turístico, así que la ocupación de julio se escala con
el factor de la serie hotelera (×1,165). Mismo supuesto, y misma fragilidad, que A4.

### F5. Un año medio, no dos fechas

Hasta el 2026-10-04 se publicaban el año medio y julio. Se dejó solo el **año medio**: dos fechas a
la vez confundían más que aclaraban. Julio, la punta, sigue en `/mapa-anterior` y en el modelo
(`modelar_sustitucion.py`), pero la web nueva no lo enseña. Consecuencia asumida: en los picos del
verano habrá menos hueco en los hoteles de lo que dice el año medio (en julio, el modelo
anterior daba 1.273 turistas sin sitio).

### F6. El turista desplazado sigue viniendo

El modelo realoja a todos los que hoy duermen en esos pisos. **Nadie se queda en su casa ni se va a
otra ciudad.** Es el supuesto que hace que la pregunta tenga sentido, pero si parte de la demanda
simplemente no viniera, la escasez de julio se reduciría o desaparecería.

Y hay más fugas que ese realojo no recoge: los turistas que se irán a otros municipios, los pisos
que la ley no toca (apartamentos turísticos legales, estancias de 32 noches o más, viviendas sin
licencia que siguen operando) y la capacidad latente.

### F7. En restauración solo se mira a quien hoy cocina

Los bares y restaurantes ya tienen clientes y eso no se estima ni se va a estimar. El grupo que se
estudia es otro: el turista que hoy elige un piso para ahorrar cocinando, y que en un hotel (sin
cocina) tiene que salir a comer.

- **El turista de piso cuenta la mitad hoy y entero en 2028.** La mitad (`PESO_PISO_EN_RESTAURACION`)
  **es un supuesto, no un dato**, y de él sale por sí solo el aumento total (+7,4 %). Lo que sí
  informa el modelo es dónde sube y dónde baja: 4.479 locales ganan y 3.830 pierden.
- **El % es sobre estos clientes, no sobre los del local.** Los vecinos y el turista de hotel de
  siempre no están.
- **Radio de 200 m**, repartido a partes iguales entre los locales del radio. Probar 100, 300 y 500
  m costaría poco y no está hecho.
- **Sin plazas de los locales**: el censo no las trae.

### F8. Lo que absorbe un hotel se cuenta hotel a hotel

Para cada hotel y un radio de 0 a 500 m: pisos dentro, las habitaciones que piden (dormitorios ×
38,3–48 %) y las que le quedan libres (19,8 % de las suyas). Absorbe la menor de las dos cifras.
**Otros hoteles del mismo radio compiten por los mismos pisos**, así que los resultados de dos
hoteles vecinos no se pueden sumar.

### F9. Lo que factura un piso es un orden de magnitud

Ocupación (38,3–48 %) × 365 noches × precio de la noche del piso entero. El precio es el anunciado,
anualizado con el factor de estacionalidad (A4/A5). No hay dato de facturación, y 365 supone que el
anuncio está abierto todo el año. Total de los 4.985 pisos: **185–232 millones de euros al año.**

### F10. Cada turista elige hotel por su banda

Desde el 2026-10-05 es el reparto de la web (`gold/modelar_flujos_banda.py`); el reparto por
cercanía y precio de `modelar_sustitucion.py` solo alimenta a `/mapa-anterior`. El turista va a un
hotel de su banda, el más cercano con hueco; si no hay, a la siguiente banda más cara, y baja solo
como último recurso. La distancia no limita. La banda es la **por plaza**, la única comparable.

Supone la misma ocupación (80,2 %) en todas las bandas, y los pisos eligen en orden aleatorio con
semilla fija (con tres órdenes, la mediana va de 0,33 a 0,34 km). Hallazgo: los hoteles de banda €
tienen 57 habitaciones libres frente a 931 que piden los pisos baratos, así que solo el 45 %
encuentra hotel de su banda. Resultados completos en `fuentes.md` → 3.2.

### F11. Lo que no cubre la web sobre el precio, y la oferta nueva

La web no estima cuánto subirá el precio de los hoteles. Hay cuatro cosas que lo harían impreciso:
la estacionalidad existiría aunque Airbnb no se fuera; parte de los turistas se irá a otros
municipios; hay pisos que no entran en la ley; y los que más presión recibirían son los hoteles
baratos y los hostales, no el conjunto.

**Oferta nueva.** No hay un dataset de hoteles previstos. Lo recopilado de prensa
(`fuentes.md` → 2.9) son 315 habitaciones anunciadas, de las que **solo 189 son de obra nueva**; el
resto son reformas o cambios de gestión de hoteles que ya existen. Aun siendo todas nuevas y vacías,
cubrirían como mucho el 7,0 % de las 4.486 habitaciones que piden los pisos en un año medio. La
vigencia de la modificación del PEUAT que permite hoteles «singulares» no está verificada.

### F12. La estancia en pisos es de 3 noches

Para pasar de noches a turistas al año en los pisos (1,1–1,4 millones) se supone una estancia de 3
noches, la misma que usa el método de reseñas (F3). Con 4 noches serían 0,8–1,0 millones. El INE da
2,38 noches para los hoteles; para los pisos no hay dato.

### F13. Dos locales con el mismo nombre a menos de 10 m son uno

El censo comercial da de alta dos veces un local de esquina, uno por cada portal. Con el mismo
nombre normalizado (sin acentos ni signos) y a 10 m o menos, se queda uno: el de la visita más
reciente. Son 14 de 9.479 locales (`gold/preparar_restauracion_bcn.py`). **Es un umbral elegido**:
entre 10 y 40 m hay 11 pares con el mismo nombre que pueden ser locales distintos (30 m entre dos
AROMES, en Parellada y en Gran de Sant Andreu) y no se distinguen de un duplicado: se dejan. No se tocan los locales sin nombre.

### F14. El mapa de hoteles y los rankings de restauración

- **«Turistas más en 2028» por barrio:** lo que el reparto por banda lleva a los hoteles del barrio,
  dividido por lo que alojan hoy (plazas × 67,9 %). No es una ocupación: es el mismo cociente que el
  +16,0 % de toda la ciudad. Un barrio con pocos hoteles y muchos pisos puede salir con +30 % o más.
- **PEUAT:** se pintan las 12 zonas por su código. Qué códigos admiten hoteles nuevos no está
  verificado (`architecture.md`); según la prensa, las zonas 1 y 2 no.
- **Ranking de restauración en valor absoluto**, no en porcentaje. Los barrios que «menos ganan» son
  los que más pierden; en Can Baró o el Carmel pasan de unas pocas decenas de clientes a cero.
- **«Marca» es el rótulo**: el censo de la ciudad no trae CIF. Dos rótulos que el censo escribe de
  dos maneras (`STARBUCKS COFFEE`/`STARBUCKS`, `MC DONALDS`/`MCDONALDS`) se agrupan.

---

## G. Geolocalización

### G1. Las coordenadas de Airbnb vienen desplazadas hasta 150 m

Inside Airbnb las ofusca **de forma independiente por anuncio**, incluso dentro del mismo edificio.
Medido qué sobrevive:

| Uso | Veredicto |
|---|---|
| Recuento de anuncios por barrio | **Sirve** — Spearman 0,998, error del 1-2% en barrios grandes |
| Asignación de barrio a un anuncio concreto | **Falla el 12%** |
| Distancia entre dos anuncios | **Inservible** |

Por eso el punto de un piso en el mapa es una posición aproximada, no una dirección, y toda
cifra por barrio arrastra ese error.
