# Restauración de Barcelona: el censo municipal sustituye a OSM, con terraza acreditada

**Fecha:** 2026-09-06 01:20
**Tipo:** Feature + Fix
**Requisitos:** apoyo a M-07 (oferta de restauración)

## Qué se hizo

Nace `pipeline/gold/preparar_restauracion_bcn.py`, la primera capa `gold` de restauración. Produce
`data/gold/restauracion_bcn.csv`: **10.100 locales de Barcelona ciudad**, del censo municipal, con
una marca de terraza cruzada contra el registro de licencias de vía pública.

### 1. OSM se deja uno de cada cuatro locales de la ciudad

| Fuente | Locales de restauración en Barcelona |
|---|---:|
| OSM (cartografía voluntaria) | 7.430 |
| Censo municipal 2024, sin alojamiento | **10.100** |
| Diferencia | **2.670 — un 26%** |

**Cómo se detectó.** Al cruzar las terrazas con OSM salía que el 93% de los locales tendrían
terraza, y doce barrios pasaban del 100% (Sant Andreu 242%). Un porcentaje imposible no acusa al
numerador: acusa al denominador. Con el censo, la cifra baja al 69% y solo quedan tres barrios
diminutos por encima del 100%, explicables por los 620 emplazamientos con más de una licencia y por
el desfase 2024-2026.

**Confirmado contra fuente externa.** El Ajuntament declara "más de diez mil" en su guía de 2025, y
su censo de 2017 daba 9.359: 10.100 continúa la serie, 7.430 no es compatible con ninguna cifra
oficial.

OSM se mantiene **fuera de la ciudad**, donde no hay alternativa.

### 2. `terraza_acreditada`, asimétrico a propósito

Ninguno de los dos ficheros municipales trae identificador del otro. Se construye el vínculo por
dos vías, que fallan por motivos distintos y por eso se suman:

| Método | Marcados | Por qué falla |
|---|---:|---|
| Misma dirección (vía + número) | 4.731 (47%) | nombres de vía que no casan entre ficheros |
| Terraza a menos de 10 m | 4.728 (47%) | la terraza se planta en la acera, no en el portal |
| **Unión** | **5.454 (54%)** | |

La proporción real ronda el **63%**. El cruce llega al 54%, así que **uno de cada siete `False` es
en realidad una terraza que el cruce no ve**. De ahí el nombre: `terraza_acreditada`, no
`tiene_terraza` — la misma convención que en las licencias de Airbnb, donde se nombra lo que se ha
podido acreditar y nunca lo que se afirma que no existe.

**Dos filtros contra falsos positivos.** Una dirección con más de tres locales de restauración no
identifica a ninguno: sin ese tope, `potosí 2` marcaba 51 locales con una sola licencia y
`diagonal 208` marcaba 30. Y un local dentro de un centro comercial, mercado o galería no tiene
terraza en vía pública aunque su portal la tenga. Quedan 12 marcados en direcciones compartidas y
ninguno en interior.

### 3. Validación independiente

El resultado reproduce el mapa regulatorio sin conocerlo. Los cinco barrios con menos terraza por
local, frente al 54% de media:

| Barrio | Con terraza |
|---|---:|
| el Barri Gòtic | 19% |
| el Bon Pastor | 21% |
| la Vila de Gràcia | 21% |
| el Raval | 35% |
| Sant Pere, Santa Caterina i la Ribera | 36% |

Cuatro de los cinco están en las zonas con **moratoria de nuevas licencias por saturación**
—Ciutat Vella y Gràcia—. El dato recupera solo la lista de zonas restringidas.

## Qué se descartó, y por qué

**Rellenar `tipo_cocina` con el censo: imposible.** Falta en el 67% de los registros de OSM, y
ninguna fuente disponible lo tiene. Lo más fino del censo municipal es tipo de local (*Restaurants*,
*Bars/Cibercafé*, *Take away*); el censo de la Diputació igual (`BAR`, `BAR-RESTAURANT`). Ninguna
distingue un japonés de un italiano.

**Rellenar los nombres: se podía, no se hace.** Calibrado contra los 7.079 locales de OSM que sí
tienen nombre, a menos de 8 m y con candidato único, **el 25% es un negocio distinto**: el censo es
de 2024 y OSM de 2026. De los 351 sin nombre en la ciudad se rellenarían 142, con ~36 falsos que no
se pueden marcar porque no hay nombre con el que contrastar.

## Qué se modificó

**Nuevos**
- `pipeline/gold/preparar_restauracion_bcn.py`
- `data/gold/restauracion_bcn.csv` — 10.100 locales, 73 barrios, 20 columnas

**Actualizados**
- `docs/architecture.md` — las dos fuentes municipales, verificadas y con sus límites
- `docs/observaciones-datos.md` — cinco observaciones nuevas
- `docs/linaje.md` — regenerado

## Un fallo que casi pasa desapercibido

La primera versión clasificaba el tipo de local comparando el nombre de actividad por igualdad
exacta. El censo escribe `Bars   / CIBERCAFÉ`, con espacios dobles y acento, y **los 4.273 bares
caían al cajón de `otros` sin que nada lo delatara**: el script terminaba bien y el CSV salía
completo. Se detectó solo porque `otros` tenía 4.357 filas, un número absurdo. Ahora se clasifica
por palabra clave sobre el texto normalizado.

## Qué queda abierto

**La capa de restauración pasa a ser híbrida** —censo dentro de la ciudad, OSM fuera— y eso todavía
no está resuelto en el export: `export_mapa.py` sigue publicando OSM para todo. Hay que decidir cómo
se explica en la web que ciudad y provincia usan fuentes distintas antes de tocarlo.
