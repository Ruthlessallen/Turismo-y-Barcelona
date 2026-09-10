# Restauración de Barcelona: capa gold desde el censo municipal

**Fecha:** 2026-09-10 18:30
**Tipo:** Feature
**Requisitos:** apoyo a M-07 (oferta de restauración)

## Qué se hizo

`data/gold/restauracion_bcn.csv`: **9.479 locales** de Barcelona ciudad, del censo comercial
municipal de 2024. Producido por `pipeline/gold/preparar_restauracion_bcn.py`, con cada decisión
tomada mirando el dato en `pipeline/notebooks/revisar_restauracion.ipynb`.

Esta vez en el orden acordado: primero revisar en el cuaderno, decidir, y solo entonces escribir el
script. La versión anterior se hizo al revés y acabó en `scraps`.

### El alcance: comidas y cenas

| Tipo | Locales |
|---|---:|
| restaurante | 4.429 |
| bar | 4.272 |
| comida_rapida | 778 |
| **total** | **9.479** |

Fuera **por decisión, no por no ser restauración**: ocio nocturno (387 — se bebe, no se cena) y
xocolateries/geladeries (148). Reincorporarlas es una línea.

Fuera por no serlo: `altres` (6, administraciones de lotería), `Altres (VENDING)` (4, tiendas 24h),
`serveis de menjar i begudes` (74, cajón de sastre donde 73 no tienen ni nombre) y los 764 de
alojamiento, que cuentan con los hoteles.

### El esquema: identidad, nombre, dónde y dirección

12 columnas. Dos entran sin estar en esa lista: `tipo_local`, porque distinguir bar de restaurante
es la razón de haber elegido esas tres categorías y sin ella el filtro no se puede deshacer; y
`fecha_revision`, porque es la fecha del dato.

### Tres cosas que parecían duplicados y solo una lo era

**190 identificadores venían entre llaves** —`{uuid}` en vez de `uuid`—, de dos días de campo
concretos y casi todos en centros comerciales, más uno con un carácter de más. Sin normalizar, dos
filas del mismo local pasan por distintas y el duplicado no se ve.

**197 filas (2,1%) tienen la dirección acabada en `LOC NA`**: el censo sabe que en ese portal hay un
establecimiento pero no cuál. Son mercados y centros comerciales — Pg Potosí 2 con 48, Els Encants
con 10, el Mercat de la Barceloneta con 2. **No son duplicados**: borrarlos por repetir dirección y
nombre se cargaría 197 locales que existen. Se conservan marcados con `local_identificado`.

**Solo 2 duplicados reales**, mismo local visitado dos veces: `THREE MARKS COFFEE` (2021 y 2023) y
`DgUSt` (dos veces el mismo día). Se conserva la visita más reciente. El de THREE MARKS explica
además la única fila con fecha de 2021 del conjunto: no era un local antiguo, era la copia vieja.

## Verificado

- 9.479 `local_id` únicos tras normalizar
- Cero nulos salvo los 56 sin nombre (0,6%)
- **73 barrios y 10 distritos**, los de la ciudad entera
- Coordenadas reales, sin ofuscar, ninguna fuera de Barcelona
- El script reproduce exactamente lo que da el cuaderno

## Por qué el censo y no OSM

OSM cuenta 7.430 locales en la ciudad frente a los 10.100 del censo: **un 26% menos**. La cifra del
censo es la que declara el Ajuntament («más de diez mil», guía 2025) y continúa su serie (9.359 en
2017); la de OSM no cuadra con ninguna cifra oficial. Y el fichero de OSM no trae fecha por
elemento, así que su antigüedad es desigual **y no medible**.

El censo tampoco es una foto de un día —el trabajo de campo va de 2023 a 2024, con el 57% visitado
en 2023—, pero eso viene por local en `fecha_revision` y se puede medir.

OSM se mantiene fuera de la ciudad, donde no hay alternativa.

## El mismo fallo, tres veces

Comparar las categorías del censo por igualdad literal **falla en silencio**: el fichero escribe
`Bars   / CIBERCAFÉ` con espacios dobles y acento, y los 4.273 bares se caen sin que nada se queje.
Pasó en el script retirado y volvió a pasar en la primera versión del cuaderno.

Ahora las categorías se buscan por palabra clave y `buscar_categoria()` **lanza excepción** si una
clave no encuentra exactamente una coincidencia. Prefiero que reviente a que mienta.

## Qué queda abierto

**La capa es híbrida**: censo dentro de la ciudad, OSM fuera. `export_mapa.py` sigue publicando OSM
para todo, y antes de tocarlo hay que decidir cómo se explica en la web que ciudad y provincia usen
fuentes distintas.
