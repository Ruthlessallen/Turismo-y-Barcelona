# Precio de hotel = ADR del INE por categoría; limpieza del repo y de la documentación

**Fecha:** 2026-10-12 12:00
**Tipo:** Cambio de método + limpieza

- **Precio de hotel.** Se retiran los precios raspados de portales (Google, Booking), su cruce y el
  modelo de estimación. Cada hotel recibe el **ADR del INE de su categoría** (media de 12 meses) y de
  ahí salen sus bandas. Hostales y pensiones van con «1–2 estrellas» (supuesto); apartaments
  turístics y «sense categoritzar» quedan sin banda. Resultado: ningún hotel cae en la banda €.
  `/hoteles`, `/mapa` (popup, tooltip, panel), portada y `/fuentes` se adaptan. Código: `gold/bandas.py`,
  `gold/preparar_hoteles_bcn.py`, `gold/preparar_alojamientos_provincia.py`,
  `bronze/preparar_adr_por_categoria.py`.
- **Una sola fuente para las ocupaciones.** Nuevo `gold/modelo.py` (80,2 %, 38,3 %, 200 m) y
  `parametros.json` para la web. La ocupación ya no está escrita a mano en el exportador ni en la web.
- **`/fuentes` lee los JSON al construir**: sus cifras no se repiten a mano. Se quitan las cifras
  del modelo que duplicaban a las otras páginas. PEUAT revisado (reglas por zona según prensa y
  despachos; subzonas y propuesta de 2023 sin verificar).
- **Panel de barrio:** la ocupación se limita al 100 %.
- **Retirado a `scraps/` (ignorado por git):** `/mapa-anterior` y `/flujos` con sus componentes y
  datos, `export_mapa.py` (queda `export_criba.py`), `modelar_sustitucion.py`, la cadena de precios
  raspados, 10 notebooks de exploración, `prototipos/`, exports y CSV huérfanos.
- **Documentación:** se conservan `fuentes`, `supuestos`, `observaciones-datos`, `web-checklist` y los
  generados (`criba`, `linaje`, nuevo `diccionario`). Se retiran PRD, arquitectura, modelo de datos,
  diseño, flujos, tests, roadmap, auditoría y fichas. `CLAUDE.md` y los READMEs se reescriben.
- **Comprobaciones:** `scripts/verificar-datos.mjs` y `.github/workflows/comprobaciones.yml`
  (sustituyen a la verificación de fichas de features).
