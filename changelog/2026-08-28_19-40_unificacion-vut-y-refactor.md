# Unificación de VUT y refactor del script a dos categorías

**Fecha:** 2026-08-28 19:40
**Tipo:** Feature
**Requisitos:** Ninguno cerrado todavía (apoya M-01, M-02, M-06 y M-08)

## Qué se hizo

Se extendió `pipeline/transform/unificar_registros.py` para cubrir también las **viviendas de uso
turístico (VUT/HUT)**, además de hoteles y apartamentos turísticos. El script pasó de ser
específico de hoteles a estar dirigido por configuración (`PERFILES`), con el mismo método para
ambas categorías y las diferencias declaradas en un solo sitio.

```bash
python unificar_registros.py          # ambas categorías
python unificar_registros.py vut      # solo una
```

### Resultado VUT

| Método | Filas |
|---|---|
| `codigo_registro` (cruce exacto por `HUTB-xxxxxx`) | 10.618 |
| `direccion` | 0 |
| `solo_registre` (pendiente geocodificar) | 13.357 |
| `solo_opendata` | 100 |
| **Total** | **24.075**, 0 duplicados |

10.718 filas con coordenadas (44,5%) y 10.619 con plazas.

### Resultado hoteles (sin cambios de fondo)

1.563 filas, 0 duplicados, 446 con coordenadas. Se confirmó además que nuestra copia de Open Data
BCN está al día: al redescargarla no había ni altas ni bajas.

## Qué se modificó

- `pipeline/transform/unificar_registros.py` — refactor a perfiles + correcciones (abajo).
- `data/processed/vut_unificados.csv` — nuevo.
- `data/processed/hoteles_y_apartaments_unificados.csv` — regenerado, con columna nueva.
- `docs/architecture.md` — corregido lo de Open Data BCN (ver changelog anterior).

## Diferencias reales entre las dos categorías

No es el mismo problema con otro fichero; hubo que resolver tres asimetrías:

1. **Dónde vive el código.** En hoteles va incrustado en el campo `name` y hay que sacarlo con
   regex; en VUT tiene columna propia (`NUMERO_REGISTRE_GENERALITAT`).
2. **Qué aporta cada fuente.** En hoteles, Open Data BCN solo añade coordenadas. **En VUT añade
   también las plazas**, porque el Registre de Turisme no publica capacidad para HUT — sin cruzar,
   ese dato no existe para ningún VUT.
3. **Piso y puerta son obligatorios en VUT.** En un mismo portal pueden convivir decenas de
   viviendas turísticas, así que calle+número no identifica nada: la clave de dirección incluye
   piso y puerta cuando el perfil lo pide (`usa_piso_puerta`). Sin esto, el cruce por dirección
   habría sido masivamente ambiguo.

## Errores encontrados y corregidos

- **Códigos con espacios internos.** La fuente no es homogénea: aparecen `HUTB- 077183` y
  `HUTB-016458  ` (espacio tras el guion, espacios finales). Sin normalizar quedaban fuera del
  cruce por pura tipografía. Corregido con `normalizar_codigo`, aplicado a **ambos lados**:
  recuperó **53 cruces** (10.565 → 10.618).
- **Huérfanos sin piso ni puerta.** Las filas que solo existen en Open Data BCN perdían esos dos
  campos al incorporarse al resultado. Corregido: ahora 98 conservan piso y 83 puerta.
- **Un código con formato ajeno.** `1-2017-0046170-1` no sigue el patrón `HUTB-nnnn` — es un
  número de expediente colado en la columna de registro. Se conserva tal cual, sin forzarlo.

## Casos para revisión manual (VUT)

### Los 100 que solo están en Open Data BCN
96 no traen número de registro en la fuente (reciben `licencia_id` sintético `OPENDATA-<expediente>`)
y 4 traen un `HUTB-` que no consta en el Registre. Son mayoritariamente altas que el Registre aún no
recoge, coherente con lo ya verificado en hoteles: **Open Data BCN va por delante en altas
recientes**.

### Por qué el cruce por dirección da 0 — y por qué está bien
Tras la pasada por código solo quedan **32 filas del Registre en Barcelona ciudad** sin cruzar,
frente a 100 huérfanos de Open Data BCN. Se comprobó que no se solapan: son propiedades
genuinamente distintas, no el mismo piso escrito de dos formas. El 0 no es un fallo del
normalizador, es que la pasada por código ya capturó todo lo capturable.

### 8.073 VUT comparten coordenada con otro
Es el 75% de los geocodificados, y es esperable: Open Data BCN geocodifica a nivel de portal, y en
un mismo edificio puede haber muchas viviendas turísticas. **Está marcado en la nueva columna
`coordenada_compartida`.** Consecuencia para [M-06] y [M-08]: al agrupar por proximidad estos
puntos son indistinguibles entre sí, así que cualquier recuento de *unidades por punto del mapa*
debe hacerse por licencia, nunca por coordenada. Para sumar plazas no supone problema.

## Nueva columna en ambas salidas

`coordenada_compartida` (booleano): marca las filas que comparten coordenada exacta con otra. En
hoteles son 11 (verificadas una a una en el changelog anterior); en VUT, 8.073.

## Pendiente

- Geocodificar las filas `solo_registre` (13.357 en VUT, 1.117 en hoteles), todas fuera de la
  ciudad de Barcelona. La API del Catastro está verificada como viable pero el paso "referencia
  catastral → coordenadas" sigue sin resolver (ver `docs/roadmap.md`).
- Tests de las funciones de normalización (`normalizar_via`, `clave_direccion`, `normalizar_codigo`,
  `primer_numero`), según `docs/testing.md`. El bug de los espacios habría sido un caso de test
  evidente.
