# Airbnb con desglose, panel del hotel y limpieza del repo

**Fecha:** 2026-10-07 16:00
**Tipo:** Funcionalidad y mantenimiento

- **`/airbnb`:** cada tarjeta lleva el desglose de lo que se descarta (`desglose` y `partida` en
  `criba_airbnb.json`), todo en naranja y con tarjeta de tamaño fijo. Las dos últimas: licencias sin
  anuncio y licencias por distrito. Los datos ya no van debajo.
- **Panel del hotel (`/mapa`):** barra apilada de sus habitaciones (ocupadas hoy, absorbe, libres),
  barra de lo que piden los pisos del radio y gráfico lineal de lo que piden según el radio.
- **Limpieza:** README raíz y de `web/` reescritos; `pipeline/README.md` con el orden real; se quitan
  de `web/public/data/mapa/` cinco JSON que ninguna página lee; avisos en `auditoria` y `prd`.
- **Revisión:** `tsc`, `eslint` y compilación de todo el Python sin errores. No verificado a ojo: las
  tarjetas con desglose y el panel nuevo (las capturas del navegador se colgaban).
