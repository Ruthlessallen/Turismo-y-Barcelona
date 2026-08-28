# Unificación de hoteles y apartamentos turísticos en un solo registro

**Fecha:** 2026-08-28 18:51
**Tipo:** Feature
**Requisitos:** Ninguno cerrado todavía (apoya M-02 y M-06; falta geocodificar el resto de la provincia)

## Qué se hizo

Primer script del pipeline: `pipeline/transform/unificar_registros.py`, que fusiona las dos fuentes
de hoteles y apartamentos turísticos en un único registro sin duplicados y sin perder filas.

Las dos fuentes no eran duplicados a eliminar, sino complementarias (decisión ya recogida en
`docs/data-model.md`): el Registre de Turisme cubre toda la provincia y trae CIF/razón social del
titular pero no coordenadas; Open Data BCN solo cubre la ciudad y está parado desde 2023, pero sí
trae coordenadas reales.

**Hallazgo que simplificó el cruce:** ambas fuentes comparten el número de registro oficial
(`HB-xxxxxx`), aunque Open Data BCN lo lleva incrustado en el campo `name` en vez de en columna
propia. Extrayéndolo con regex, **443 de 446 filas cruzan de forma exacta**, sin necesidad de
matching difuso. Solo 3 filas necesitaron la pasada por dirección.

Estrategia final, en dos pasadas:
1. **Cruce exacto por número de registro** — 443 filas.
2. **Cruce por dirección normalizada**, solo para lo que quedó suelto y únicamente cuando la
   correspondencia es 1:1 — 2 filas. Normaliza acentos, tipo de vía (cada fuente lo escribe
   distinto) y rangos de número ("10 - 11" → "10").

Resultado: 1.563 filas, 0 duplicados, 446 con coordenadas reales (28,5%). Las 1.117 restantes son
de fuera de la ciudad de Barcelona y quedan pendientes de geocodificar.

## Qué se modificó

- `pipeline/transform/unificar_registros.py` — nuevo.
- `data/processed/hoteles_y_apartaments_unificados.csv` — nuevo, salida del script.

## Por qué

Sin unificar, cualquier análisis de oferta hotelera (M-02) o de absorción por proximidad (M-06)
tendría que decidir sobre la marcha qué fuente usar para cada campo, con riesgo de contar dos veces
el mismo hotel. El script lo resuelve una vez y deja el criterio escrito en código.

## Decisiones de diseño que conviene no perder

- **Ninguna fila se descarta.** Lo que no cruza se conserva marcado en `metodo_match`
  (`codigo_registro` / `direccion` / `solo_registre` / `solo_opendata`), de modo que el origen de
  cada dato es auditable. Un hotel presente solo en Open Data BCN recibe un `licencia_id`
  sintético (`OPENDATA-<id>`) en vez de fingir una licencia que no consta en el registro oficial.
- **Los cruces ambiguos se rechazan a propósito.** Si una dirección normalizada apunta a más de un
  establecimiento en cualquiera de los dos lados, no se cruza: es preferible una fila sin
  coordenadas que una fusión incorrecta.
- **Aviso de nombres dispares.** El cruce por dirección compara además los nombres comerciales y
  avisa por consola si no se parecen. Saltó en un caso real (`45 Times Barcelona Hotel` vs
  `Hotel BLESS Barcelona`, ambos en Plaça Catalunya 10): se verificó que la dirección es correcta
  en ambas fuentes, así que la coordenada asignada es válida; la discrepancia es de nombre
  (probable cambio de marca en el mismo edificio). El match se conserva y queda marcado en
  `similitud_nombre`.
- **Dos guardas anti-duplicado** que abortan el script si fallan: claves repetidas antes del cruce,
  y `licencia_id` repetidos en el resultado. La segunda detectó un error real durante el
  desarrollo.

---

## Casos para revisión manual

Tres grupos, por orden de importancia. Ninguno bloquea el uso del dataset, pero conviene tenerlos
presentes antes de calcular proximidad en [M-06].

### 1. Las 3 filas que no cruzaron por número de registro

Son las 3 entradas de Open Data BCN cuyo campo `name` no lleva el código incrustado. Dos se
rescataron por dirección; una se quedó fuera:

| Licencia | Nombre (Registre) | Nombre (Open Data BCN) | Dirección | Método | Similitud |
|---|---|---|---|---|---|
| `HB-004976` | ANTIGA CASA BUENAVISTA | Hotel Antiga Casa Buenavista | Ronda de Sant Antoni 84 | `direccion` | 1.00 ✅ |
| `HB-004805` | 45 Times Barcelona Hotel | Hotel BLESS Barcelona | Plaça Catalunya 10-11 | `direccion` | 0.00 ⚠️ |
| `OPENDATA-99400784517` | *(no consta)* | Hotel Ibis Budget Barcelona Center | Carrer d'Àvila 66 | `solo_opendata` | — |

**El caso `HB-004805` — VERIFICADO, el cruce es correcto.** El aviso saltó porque los nombres no
comparten ninguna palabra, pero la búsqueda externa lo confirma: Palladium Hotel Group abrió
**"45 Times Barcelona Hotel" el 15/11/2024 en Plaça Catalunya**, bajo su concepto de "hoteles
efímeros" — una marca temporal que **por diseño pasa después a la cartera BLESS Collection
Hotels**. Es literalmente el mismo hotel con el nombre previsto de antemano. El cruce se mantiene
y el `similitud_nombre = 0.0` queda como recordatorio de que un nombre distinto no implica un
establecimiento distinto.

**El caso `Hotel Ibis Budget Barcelona Center` — es una alta nueva, no un cierre.** Confirmado:
abrió en **julio de 2026** en Carrer d'Àvila 66 (Poblenou, 22@), 189 habitaciones, el mayor ibis
budget de la Península. En Open Data BCN la fila se creó el **2026-07-09**, coincidiendo con la
apertura. No está en el Registre de Turisme: **es el Registre el que va por detrás**, no un hotel
desaparecido. Se conserva con `licencia_id` sintético.

### 2. Once filas comparten coordenada exacta con otra

**No es un fallo de la unificación**: las 11 vienen de la pasada 1 (cruce exacto por código), así
que cada una recibió la coordenada de *su propia* fila de Open Data BCN. Es la fuente la que
geocodifica a nivel de portal o edificio, de modo que establecimientos contiguos o en la misma
finca caen en el mismo punto.

| Licencias | Establecimientos | Dirección | Caso (verificado externamente 2026-08-28) |
|---|---|---|---|
| `HB-000053` / `HB-000480` | Continental / Toledano | Rambla 138 | **Confirmado**: dos hoteles reales y distintos en el mismo edificio — el Toledano ocupa plantas concretas (2ª y 4ª) dentro del inmueble del Continental |
| `HB-004639` / `HB-004640` / `HB-004641` | Casa Maca Guest House 3 / 4 / (base) | Bruc 146 | **Confirmado**: es una única guest house de 5 habitaciones en un edificio modernista de 1910, con **tres licencias** a su nombre. El caso más claro de que licencia ≠ establecimiento |
| `HB-004668` / `HB-004690` | Hotel Brummell / Brummell | Nou de la Rambla 174 y 176 | Hotel de 20 habitaciones en el 174; el 176 es una segunda licencia contigua (el operador tiene varios proyectos en la zona) |
| `HB-004050` / `HB-004507` | Acta Splendid / AinB | Muntaner 2 y 4 | Portales contiguos, operadores distintos |
| `HB-004704` / `HB-004767` | Serennia Exclusive Rooms / Hotel Boutique 2015 | Ronda Universitat 9 | Misma finca, dos licencias |

**Por qué importa para [M-06]:** al agrupar por proximidad, estos puntos son indistinguibles entre
sí. Para *sumar capacidad* no supone ningún problema (las plazas se agregan igual). Sí lo supondría
si en algún momento se contara "número de establecimientos por punto del mapa", o si se dedujera
densidad a partir de puntos únicos: ahí hay que agrupar por licencia, no por coordenada.

### 3. Nota de método

El caso `Casa Maca` (3 licencias, misma dirección, mismo operador) es el mismo patrón que ya se
documentó para la cadena Catalonia en `docs/prd.md` → [S-01], pero a nivel de finca en vez de
sociedad: **una licencia no equivale a un establecimiento físico**. Conviene no dar por hecho que
contar licencias es contar hoteles.

---

### 4. Corrección sobre Open Data BCN

Al investigar los casos anteriores salió un error en la documentación previa: `architecture.md`
daba Open Data BCN por **parado desde 2023**, basándose en el campo `metadata_modified` del portal
CKAN. **Es falso.** Los registros de dentro llegan hasta el 2026-08-19 y **118 de 446 filas se
modificaron en 2026**. Lo que está obsoleto es la metadata del portal, no los datos.

Esto invierte parte del criterio inicial: para **altas recientes**, Open Data BCN puede ir *por
delante* del Registre de Turisme (el ibis budget está en uno y no en el otro; el rebranding a BLESS
se registró el 2026-08-19). El Registre sigue siendo la fuente principal por cobertura provincial y
por traer titular, pero ya no se puede describir Open Data BCN como una foto fija. Corregido en
`docs/architecture.md`.

---

## Pendiente

- **Aplicar el mismo script a los VUT.** Comprobado que la clave funciona igual de bien:
  `NUMERO_REGISTRE_GENERALITAT` (Open Data BCN) ↔ `n_mero_inscripci` (Registre) dan **10.556
  cruces exactos**, con 67 huérfanos en Open Data BCN y 94 en el Registre. Es la continuación
  natural de este trabajo.
- Geocodificar las 1.117 filas sin coordenadas (provincia fuera de la ciudad). La API del Catastro
  está verificada como viable pero el paso "referencia catastral → coordenadas" aún no está
  resuelto (ver `docs/roadmap.md`).
- Tests: este script todavía no tiene. Las funciones de normalización (`normalizar_via`,
  `clave_direccion`, `primer_numero`) son las candidatas claras, según `docs/testing.md`.
