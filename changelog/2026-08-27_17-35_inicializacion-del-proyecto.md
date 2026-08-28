# Inicialización del proyecto

**Fecha:** 2026-08-27 17:35
**Tipo:** Configuración
**Requisitos:** Ninguno

## Qué se hizo

Se convirtió el scaffold de `project-template` en el repositorio real de Turismo-BCN. Se completó
la documentación de `docs/` (prd, design-system, architecture, data-model, roadmap, user-flows,
testing; `business.md` se descartó por no aplicar — no hay monetización) y se ejecutó el checklist
de inicialización de `CLAUDE.md`.

Decisiones de fondo tomadas durante la documentación: dashboard público sin cuentas (Next.js +
Vercel para el frontend, Python + DuckDB para el pipeline de datos, sin base de datos en
producción), alcance de provincia de Barcelona con ventana 2021–2031, y paleta de datos tomada de
la skill `dataviz` en vez de definida a mano.

## Qué se modificó

- `README.md` — reescrito para el proyecto real, sin referencias a la plantilla.
- `CLAUDE.md` — placeholders rellenos (descripción, stack, estructura de carpetas, convenciones,
  "Qué NO hacer"); borrada la sección de inicialización y las referencias a `.template/` en el
  arranque.
- `LICENSE` — copyright actualizado a Ruth López Pellicer, 2026.
- `.env.example` — recortado al stack real (sin `DATABASE_URL` ni `AUTH_SECRET`; fuentes de datos
  pendientes de confirmar).
- `changelog/README.md`, `mejoras/backlog.md`, `docs/features/README.md`,
  `.claude/commands/changelog.md` — quitadas las referencias a la plantilla y a `.template/`.
- `docs/business.md` — eliminado (no aplica).
- `.template/` y `.claude/commands/init-proyecto.md` — eliminados.

## Por qué

El scaffold de `project-template` solo tiene sentido durante el arranque. Con la documentación del
proyecto completa, el repo pasa a describirse a sí mismo — Turismo-BCN — en vez de describir la
plantilla de la que partió.
