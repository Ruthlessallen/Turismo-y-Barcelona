# Mapa de la documentación

Si quieres saber **X**, abre **Y**. Una pregunta, un documento.

## Cómo está montado el proyecto

```
data/raw  →  data/bronze  →  data/gold  →  data/exports  →  web/
(descargas)  (limpio)        (tablas +      (JSON por        (Next.js,
 no en git                    modelo 2028)   barrio)          lee exports)
```

Los scripts viven en `pipeline/`, un directorio por capa de destino (`sources/`, `bronze/`,
`gold/`, `export/`). Orden y reglas de cada capa: [`pipeline/README.md`](../pipeline/README.md) y
[`data/README.md`](../data/README.md).

## Datos: de dónde sale cada cifra

| Pregunta | Documento |
|---|---|
| ¿De qué fuente sale este número y qué le hacemos? (versión pública) | [`fuentes.md`](fuentes.md) |
| ¿Qué hemos supuesto, y qué pasa si el supuesto falla? | [`supuestos.md`](supuestos.md) |
| ¿Qué columnas tiene cada tabla? | [`data-model.md`](data-model.md) |
| ¿Qué fichero alimenta a qué script? | [`linaje.md`](linaje.md) *(generado)* |
| ¿Cuántos registros caen en cada paso y por qué? | [`criba.md`](criba.md) *(generado)* |
| ¿Qué comprobamos a mano contra la fuente original? | [`observaciones-datos.md`](observaciones-datos.md) |
| ¿Qué hay en `data/raw/` y de dónde se baja? | [`../data/raw/README.md`](../data/raw/README.md) |

`linaje.md` y `criba.md` no se editan a mano: se regeneran con
`pipeline/generar_linaje.py` y `pipeline/generar_criba.py`.

## Producto y construcción

| Pregunta | Documento |
|---|---|
| ¿Qué construimos y para quién? | [`prd.md`](prd.md) |
| ¿Qué stack y qué estructura de carpetas? | [`architecture.md`](architecture.md) |
| ¿Cómo debe verse y sentirse la web? | [`design-system.md`](design-system.md) |
| ¿Qué recorridos hace un usuario? | [`user-flows.md`](user-flows.md) |
| ¿Cómo se prueba? | [`testing.md`](testing.md) |
| ¿En qué fase estamos? | [`roadmap.md`](roadmap.md) |
| ¿Qué falta por hacer en la web? | [`web-checklist.md`](web-checklist.md) |
| ¿Qué se acordó construir en una feature concreta? | [`features/`](features/README.md) |

## Historial

| Pregunta | Documento |
|---|---|
| ¿Qué se hizo en cada sesión y por qué? | [`../changelog/`](../changelog/README.md) |
| ¿Qué ideas hay aparcadas? | [`../mejoras/backlog.md`](../mejoras/backlog.md) |
| ¿Qué se comprobó el 14 de septiembre? | [`auditoria-2026-09-14.md`](auditoria-2026-09-14.md) |

## Reglas para quien trabaja aquí

Están en [`../CLAUDE.md`](../CLAUDE.md): `pnpm` y nunca `npm`, sin claves en el repo, sin datos a
nivel de vivienda en `data/exports/`, y nada destructivo sin confirmar.
