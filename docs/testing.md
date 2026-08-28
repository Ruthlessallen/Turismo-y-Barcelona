# Estrategia de testing

Documento vivo. Actualizar cuando cambie el stack o las convenciones de testing. Los cambios deben
registrarse también en `changelog/`.

---

## Filosofía

El valor del proyecto está en que los datos publicados sean correctos y trazables, no en que la
interfaz sea vistosa: un gráfico bonito con un dato mal cruzado es peor que no publicarlo. Por eso
el foco de testing es la lógica de transformación del pipeline (parsing, cruce operador↔licencia,
agregación por municipio/periodo) y las reglas de integridad visual acordadas en
`design-system.md` (observado vs. proyectado, estado "sin datos"). Los flujos de `user-flows.md`
se cubren con E2E selectivos sobre el camino feliz y los casos de error ya documentados — no hace
falta más.

---

## Cuándo se escriben los tests

**Después de implementar, en una pasada propia.** No durante la planificación, y no a la vez que
el código.

El compromiso de que un requisito se va a validar se adquiere antes: es la tercera columna de la
tabla de cobertura de `docs/features/`. Pero el test en sí se escribe cuando el código ya existe,
leyéndolo. Es una diferencia de calendario pequeña con una consecuencia grande: un test escrito
antes que el código apunta a selectores, rutas y respuestas *imaginados*. Cuando luego no
coinciden con la realidad, casi nadie reescribe el test — se le van quitando aserciones hasta que
pasa, y acaba siendo un test que no comprueba nada pero que da luz verde. Escrito después, apunta
a lo que hay.

Reglas que se derivan de eso:

- **Antes de escribir una aserción, verifica que el selector existe en el código.** No lo
  supongas por el nombre del componente.
- **Si un elemento no tiene selector estable, añádele uno.** Meter un `data-testid` en el código
  es un cambio mínimo aceptable y preferible a colgar el test de una clase de estilos o de un
  texto que cambiará con el próximo ajuste de copy.
- **Cada "entonces" del criterio de aceptación necesita al menos una aserción.** Si el criterio
  define caso negativo, va su propio test.
- **Un test que falla no se arregla quitándole aserciones.** Si falla, o el código está mal o el
  criterio estaba mal escrito. Ambas cosas se corrigen donde toca; degradar el test para forzar el
  verde convierte la suite en decoración.
- **Los datos que crea un test los borra ese test.** Prefija lo que insertes para poder
  identificarlo y limpia al terminar, aunque el test falle a mitad.

---

## Stack de testing

El proyecto tiene dos motores (ver `architecture.md`), cada uno con su propio stack de testing:

| Tipo | Herramienta |
|------|-------------|
| Unitario — pipeline (Python) | pytest |
| Unitario/Integración — frontend (Next.js) | Vitest + Testing Library |
| E2E — frontend | Playwright |

---

## Qué testear

### Sí testear
- Transformaciones del pipeline: parsing y limpieza por fuente, cruce operador↔licencia,
  agregación por municipio/periodo (`data-model.md`).
- La regla de integridad observado/proyectado: ningún dato posterior a "hoy" se renderiza sin el
  marcado visual distinto que exige `design-system.md` — no es solo estético, es lo que evita que
  se confunda una proyección con un hecho.
- El estado "sin datos" ([M-01] negativo en `prd.md`): un municipio sin datos para la métrica
  activa muestra el estado explícito, nunca un cero.
- Los flujos [FLOW-01] a [FLOW-03] de `user-flows.md`, camino feliz y casos de error documentados.
- El tope de 5 municipios simultáneos en comparación ([FLOW-02]).

### No testear (o mockear)
- Estilos puramente visuales (valores exactos de sombra, color de pixel) — se revisan a ojo, no
  con aserciones.
- Disponibilidad de las fuentes externas en sí — se usan fixtures de datos de muestra guardadas en
  el repo, nunca una llamada real a la fuente oficial en un test.
- El contenido exacto de los datasets en producción (cambian con cada actualización) — la lógica
  de transformación se testea contra fixtures fijas, no contra el dataset real.

---

## Convenciones

- Pipeline: `test_<modulo>.py` junto al módulo que testea, con pytest.
- Frontend: `Componente.test.tsx` junto al componente.
- Fixtures de datos de muestra — pequeñas, no datasets completos — en `pipeline/tests/fixtures/`.
  Nunca commitear un dataset real completo como fixture.

---

## Cobertura objetivo

Sin porcentaje global objetivo. El criterio es el de `CLAUDE.md` → "Ciclo de trabajo de una
feature": cada requisito MUST/SHOULD de `prd.md` tiene su fila en la tabla de cobertura de la
ficha de feature correspondiente, con ruta de test o motivo de "no verificable por interfaz". La
lógica de `pipeline/transform/` es la que más lo necesita, al ser la base de todo lo demás.

---

## Cómo correr los tests

```bash
# Frontend — todos los tests
pnpm test

# Frontend — modo watch
pnpm test:watch

# Frontend — E2E
pnpm test:e2e

# Pipeline (Python)
pytest pipeline/
```
