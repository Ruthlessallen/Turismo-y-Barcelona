# Mapa de la documentación

Si quieres saber **X**, abre **Y**. Una pregunta, un documento.

```
data/raw  →  data/bronze  →  data/gold  →  data/exports  →  web/
(descargas)  (limpio)        (tablas +      (JSON por        (Next.js,
 no en git                    modelo 2028)   barrio)          lee exports)
```

Los scripts viven en `pipeline/`, un directorio por capa de destino. Orden y reglas:
[`pipeline/README.md`](../pipeline/README.md) y [`data/README.md`](../data/README.md).

| Pregunta | Documento |
|---|---|
| ¿De qué fuente sale este dato y qué le hacemos? | [`fuentes.md`](fuentes.md) |
| ¿Qué hemos supuesto, y qué pasa si el supuesto falla? | [`supuestos.md`](supuestos.md) |
| ¿Qué contiene cada fichero de `data/`? | [`diccionario.md`](diccionario.md) *(generado)* |
| ¿Qué fichero alimenta a qué script? | [`linaje.md`](linaje.md) *(generado)* |
| ¿Cuántos registros caen en cada paso y por qué? | [`criba.md`](criba.md) *(generado)* |
| ¿Qué se comprobó a mano contra la fuente original? | [`observaciones-datos.md`](observaciones-datos.md) |
| ¿Qué hay en `data/raw/` y de dónde se baja? | [`../data/raw/README.md`](../data/raw/README.md) |
| ¿Qué falta por hacer? | [`web-checklist.md`](web-checklist.md) |
| ¿Qué se hizo en cada sesión? | [`../changelog/`](../changelog/README.md) |

Los tres generados no se editan a mano: `pipeline/generar_linaje.py`, `generar_criba.py` y
`generar_diccionario.py`. Las reglas para quien trabaja aquí están en [`../CLAUDE.md`](../CLAUDE.md).
