# Afina el criterio de candidatos: actividad real, anfitrión y duración de estancia

**Fecha:** 2026-08-29
**Tipo:** Refinement
**Requisitos:** M-08 (continúa `2026-08-28_20-33_auditoria-de-licencias.md`)

## Qué cambia

Tres criterios nuevos reducen los candidatos de **1.698 a 399**, y se incorpora una fuente que
faltaba para medir duraciones de estancia.

### 1. Solo cuenta la oferta con clientes

Un anuncio sin reservas recientes no describe oferta en circulación: la licencia que le falte no
dice nada sobre el mercado. Se exige reseña dentro del año del snapshot, así que **2025 y anteriores
quedan fuera** aunque el anuncio siga publicado. Descarta 1.025 anuncios.

### 2. El anfitrión que ya acredita licencia va aparte

Un anfitrión puede tener licencia verificada en unos anuncios y no en otros. Quien ya ha declarado
una válida conoce el trámite, así que la falta apunta más a un descuido al rellenar el campo que a
operar al margen del registro. Se separa en su propia categoría (`candidato_host_con_licencia`):
**274 anuncios de 109 anfitriones**.

### 3. Se descarga el fichero de reseñas

`visualisations/reviews.csv` — 1.033.523 reseñas con `listing_id` y fecha. Se eligió sobre
`data/reviews.csv.gz` (133 MB) porque aquella añade nombre del huésped y texto del comentario:
datos personales que no hacen falta.

## El resultado

| Grupo | Anuncios | Anfitriones |
|---|---|---|
| Sujetos al régimen VUT | 8.996 | |
| — sin licencia acreditada | 1.698 | |
| — descartados por falta de actividad en 2026 | 1.025 | |
| **A · el anfitrión acredita en otro anuncio suyo** | **274** | 109 |
| **B · no acredita en ninguno → CANDIDATOS** | **399** | 258 |

Categorías excluyentes dentro de cada grupo:

| | A: anuncios / anfitriones | B: anuncios / anfitriones |
|---|---|---|
| No declara nada | 40 / 27 | 220 / 126 |
| Número imposible (>HUTB-80024) | 165 / 56 | 146 / 109 |
| Número plausible pero inexistente | 69 / 45 | 33 / 24 |

Los anfitriones no suman entre categorías: uno puede tener anuncios en varias.

**Del grupo B, 355 (89%) tienen su última reseña desde marzo de 2026.**

## La duración de las estancias, por fin medible

El snapshot no trae duraciones, pero el fichero de reseñas sí trae fechas. **El hueco entre reseñas
consecutivas de un mismo anuncio es un techo de la estancia intermedia**: incluye la estancia más
los días vacíos hasta el siguiente huésped, y si alguien no reseña, dos estancias se cuentan como
una. El sesgo infla los huecos, así que el porcentaje de estancias cortas es un **suelo**.

Sobre los 355, en los últimos 24 meses (11.078 huecos en 307 anuncios):

| Hueco | Huecos | % |
|---|---|---|
| 1–3 días | 3.514 | 31,7% |
| 4–7 | 3.789 | 34,2% |
| 8–14 | 2.049 | 18,5% |
| 15–31 | 910 | 8,2% |
| 32–60 | 397 | 3,6% |
| 61–120 | 201 | 1,8% |
| 120+ | 218 | 2,0% |

**El 92,6% de los huecos son de 31 días o menos.**

### El alojamiento "para estudiantes"

Dos operadores del grupo se presentan como residencia de estudiantes y declaran no ser para
turistas. El régimen legal no depende de a quién se alquile sino de cuánto dura cada cesión:

| Operador | Anuncios | Mínimo de noches | Huecos medidos | Mediana | ≤31 días |
|---|---|---|---|---|---|
| BLAU Student Housing | 5 | 3 | 665 | **1 día** | 98,6% |
| La Fabrica &Co | 10 | 2, 3 y 31 | 346 | **2 días** | 91,6% |

Un hueco mediano de uno o dos días implica reseñas casi diarias en el mismo estudio: rotación de
estancias cortas, no alojamiento de curso académico — un estudiante que se queda un cuatrimestre
deja una reseña cada varios meses. El dato no dice si los huéspedes son estudiantes; solo cuánto
duran las cesiones, que es lo que determina el régimen.

## Precisión sobre el umbral de 31 días

Se aclaró un punto que se prestaba a confusión: **la norma mide cada cesión por separado, no el
acumulado anual**. Alquilar 31 días doce veces al año son doce estancias turísticas y exige
licencia; un solo inquilino 40 días seguidos, no. No existe un umbral de días al año que saque una
vivienda del régimen turístico.

En consecuencia, **el único dato del snapshot que acredita la exención es `minimum_nights >= 32`**:
si la plataforma no deja reservar menos, ninguna estancia puede ser turística. `minimum_nights <= 31`
no prueba que haya estancias cortas, solo que están permitidas — y eso basta para generar la
obligación.

## Qué se descartó y por qué

**Rescatar erratas comparando números a un dígito de distancia.** De los 234 números inválidos del
grupo A, 8 están a un dígito de una licencia del propio anfitrión y 95 a un dígito de una licencia
ajena. Los segundos no acreditan nada: con 22.801 licencias emitidas, coincidir por un dígito con
una cualquiera es esperable por azar. Y el titular tiene el deber de declarar la licencia
correctamente, así que la proximidad no se usa como atenuante.

## Límites que siguen vigentes

- **"Candidato", nunca "infractor".** El campo lo rellena el anfitrión sin validación técnica: una
  licencia real mal escrita cae en el mismo grupo.
- El hueco entre reseñas es un techo, no la duración de ninguna estancia concreta.
- Solo cubre Airbnb; el snapshot es de junio de 2026 y el registro se consultó en agosto.
- Nada a nivel de vivienda: las coordenadas vienen desplazadas ~200 m.
