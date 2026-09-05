# Supuestos del análisis

Cada punto de esta lista es un sitio donde el resultado depende de una decisión nuestra y no del
dato. No son defectos: son las decisiones que hacen falta para poder decir algo. Lo que sí sería un
defecto es tomarlas y no dejarlas escritas.

El detalle y las comprobaciones que las respaldan están en `observaciones-datos.md` (verificaciones
manuales), `criba.md` (recuentos de cada filtro, generado del dato) y `data-model.md` (diccionario).

**Última revisión:** 2026-09-04, con la banda económica ya aplicada a los dos lados.

---

## A. Los que sostienen la comparación entre hoteles y Airbnb

### A1. La plaza es la unidad comparable

Se divide entre la capacidad **declarada**, no entre los ocupantes reales. Un piso para cuatro con
una pareja dentro cuenta como cuatro plazas, igual que una habitación doble de hotel cuenta como
dos aunque duerma una persona. Es precio por plaza **disponible**, y se aplica igual a los dos
lados: es lo que hace la comparación válida.

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

## B. La criba de 15.406 a 6.834

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

Se mantiene el criterio. El techo de lo que se ganaría afinando es un 5,6% de ese grupo, y para
tres cuartas partes iría en contra de lo que el propio anuncio declara.

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

### B6. Los duplicados se deciden por licencia, no por nombre y coordenadas

Comprobado que la regla textual destruía 43 viviendas reales: mismo anfitrión, mismo nombre, mismo
precio y **licencias distintas** (HUTB-079007 / 079009 / 079012). Son pisos diferentes del mismo
edificio anunciados igual. La desduplicación por licencia los conserva.

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

## F. Geolocalización

### F1. Las coordenadas de Airbnb vienen desplazadas hasta 150 m

Inside Airbnb las ofusca **de forma independiente por anuncio**, incluso dentro del mismo edificio.
Medido qué sobrevive:

| Uso | Veredicto |
|---|---|
| Recuento de anuncios por barrio | **Sirve** — Spearman 0,998, error del 1-2% en barrios grandes |
| Asignación de barrio a un anuncio concreto | **Falla el 12%** |
| Distancia entre dos anuncios | **Inservible** |

Por eso el mapa publica agregados por barrio y nunca puntos individuales.
