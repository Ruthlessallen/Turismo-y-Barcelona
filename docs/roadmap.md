# Roadmap

Planificación de fases de desarrollo. No es un calendario con fechas exactas, sino una guía de
prioridades. Actualizar cuando algo pase de una fase a otra, o cuando se redefinan las prioridades.

---

## Fase 1 — Investigación y recolección de datos

Esta es la fase en la que arranca el proyecto. Antes de construir nada del dashboard hay que saber
si los datos que necesitamos existen de verdad, en qué forma, y si se pueden cruzar.

- [x] Alcance legal exacto — resuelto: Decret Llei 3/2023 (262 municipios de Catalunya, tope 10%)
      + política propia de "cero VUT" de Barcelona ciudad y varios municipios AMB. Ver
      `architecture.md` → Integraciones externas y `data-model.md` → `municipio`.
- [x] Fuente oficial de licencias VUT (ciudad) — **verificada con datos reales**: Open Data BCN,
      trae dirección + coordenadas + nº HUTB, histórico trimestral hasta 2026 Q1. Sin nombre de
      empresa/titular (ver punto pendiente más abajo). Falta verificar Registre de Turisme de
      Catalunya para el resto de la provincia
- [x] Fuente oficial de licencias y empresas hoteleras — **verificada**: Registre de Turisme de
      Catalunya (toda la provincia, estado actual + titular) + Idescat (serie histórica por
      municipio desde 1995, sin identidad individual). Entre las dos se cubre identidad y
      tendencia; Open Data BCN (ciudad) aporta las coordenadas. **Corrección 2026-08-28:** Open
      Data BCN no está parado desde 2023 — su metadata CKAN sí, pero los datos llegan a 2026-08-19
      y para altas recientes va por delante del Registre
- [x] **Nombre de empresa/titular de licencias VUT y hoteles — resuelto.** El Registre de Turisme
      de Catalunya trae `cif` + razón social (o nombre/apellidos si es persona física) para toda
      la provincia, Barcelona ciudad incluida. Correspondencia de numeración **confirmada al
      implementar**: las dos fuentes comparten el mismo código oficial (`HB-`/`HUTB-`), y cruzan
      443/446 en hoteles y 10.618 en VUT
- [x] Construcción hotelera futura — **sin dataset único, pero se encontró algo más útil**: el
      PEUAT (plan urbanístico) bloquea licencias hoteleras nuevas en gran parte de sus zonas.
      Confirmado como dataset real en Open Data BCN (`mapa-peuat`, GeoPackage, 12 zonas) — ver
      `data/raw/peuat/`. Eso importa más para [M-06] que una lista de proyectos anunciados en
      prensa. Falta la tabla de equivalencia código de zona ↔ regla (qué admite licencias nuevas)
- [x] Fuente oficial de licencias de bares/restaurantes — **verificada con datos reales**:
      Diputació de Barcelona da nombre + NIF + dirección + coordenadas + actividad para +200
      municipios (API correcta: `do.diba.cat/api/dataset/establiments/format/json`, no la que se
      probó la primera vez). Open Data BCN (ciudad) sigue como candidata sin verificar. Google
      Places API como fallback si hace falta
- [x] Fuente de entradas de turistas (M-04) — **decidido: OTB**, igual que M-05. Se descartan AENA
      y Port de Barcelona como fuentes dedicadas (ver "Descartado" más abajo)
- [x] Fuente de estadísticas turísticas generales — **decidido: OTB** (Observatori del Turisme a
      Barcelona), no Idescat/Egatur. Desagrega ciudad/región/total destino y tiene informe de
      "perfil del turista" con volumen y origen — que es lo que importa, no el formato exacto en
      que venga (PDF o tabla, se decide al implementar). Confirmado que existe con cifras reales
- [x] **Bonus encontrado**: LABturisme (Diputació) tiene un dashboard de Looker Studio con datos
      reales de toda la provincia, actualizado el mismo día — y a diferencia del Power BI de OTB,
      su texto sí se puede leer por automatización. Complementa a OTB, no lo sustituye (cubre el
      resto de la provincia con más detalle). Cambiar sus filtros interactivamente quedó pendiente
- [x] Fuente de geometría municipal — **verificada con datos reales**: ICGC vía WFS,
      `outputFormat=geojson` da GeoJSON real en WGS84 sin reproyectar. 947 municipios de Catalunya
      / 311 de la provincia de Barcelona (cifra oficial, cuadra) — ver `data/raw/geometria/`
- [x] Airbnb — **verificado con datos reales**: Inside Airbnb, [M-08] en `prd.md`. Descarga real
      probada (15.430 anuncios, snapshot 24/06/2026). El campo `license` trae el nº HUTB parseable
      en el 48% de los casos — cruce directo, mejor de lo esperado. Solo ciudad de Barcelona.
- [x] Booking — decidido: se deja aparte por ahora. Sin fuente abierta equivalente a Inside Airbnb,
      su ToS prohíbe el scraping, y el usuario ya hizo un scraper propio para Valencia una vez —
      si hace falta, se retoma como script puntual manual (no como parte del pipeline automático),
      después de ver cuánta cobertura falta tras el cruce Airbnb + licencias oficiales (M-08)
- [x] Por cada fuente candidata: formato verificado (ver `architecture.md`). Cadencia y cobertura
      temporal exacta pendiente de confirmar caso por caso al construir cada módulo de `pipeline/`
- [x] Descarga de muestra de cada fuente y contraste contra `data-model.md` — hecho para 7 de 9
      fuentes (todas menos AENA/Port de Barcelona, descartadas). Explorado en
      `pipeline/notebooks/01_exploracion_fuentes.ipynb`, ejecutado con datos reales
- [ ] **OTB**: los informes PDF son infografías, no tablas — `pdfplumber.extract_tables()` no las
      resuelve. Texto crudo en `data/raw/otb/*_texto_extraido.txt`; pendiente extracción por
      posición (palabras + coordenadas) o transcripción manual de las cifras clave
- [x] **Diputació**: filtro resuelto — va en la ruta (`camp-rel_municipi/<codi>/format/json`), no
      en query string. Confirmado además que Barcelona ciudad no participa en este censo (0
      registros), usa Open Data BCN aparte — no es un fallo, es el reparto real entre fuentes
- [x] Prueba de concepto de punta a punta — **hecha y superada**: `unificar_registros.py` cruza
      las dos fuentes para las dos categorías (VUT y hoteles+AT) de toda la provincia, no solo de
      un municipio. Salidas en `data/processed/`, 0 duplicados. Ver
      `changelog/2026-08-28_18-51_*` y `2026-08-28_19-40_*`

**Objetivo de validación:** confirmar que las seis categorías de datos existen en fuentes públicas
fiables, con cobertura temporal suficiente y a un nivel de detalle cruzable por municipio. Si
alguna fuente no existe o no es utilizable en la práctica, esto obliga a replantear el alcance del
proyecto — antes de construir nada más, no después.

---

## Fase 2 — Pipeline completo y dashboard público

Solo se planifica en detalle una vez cerrada la Fase 1: qué fuentes sobreviven a la validación
decide qué de esto es realista.

- [ ] Pipeline completo: las fuentes confirmadas, todos los municipios de la provincia, histórico
      de 5 años
- [ ] Frontend Next.js con los componentes de `design-system.md`: FilterBar, ChoroplethMap,
      ListingClusterMap, StatTile, TimeSeriesChart, ComparisonBarChart, OperatorTable,
      SourceFootnote
- [ ] Repo público en GitHub conectado a Vercel, primer despliegue
- [ ] Features MUST del PRD sin proyección todavía: M-01 a M-05

---

## Fase 3 — Proyección y comparativa territorial

La parte más especulativa y la que más valor añade sobre "solo mostrar datos históricos" — por eso
va después de tener el histórico funcionando y publicado, no antes.

- [ ] M-06 — estimación de absorción hotelera por proximidad: clusters de apartamentos sin
      licencia + qué % de más necesitarían asumir los hoteles cercanos, con la metodología visible
- [ ] M-07 — vista comparativa entre municipios de la provincia, para detectar desplazamiento de
      oferta turística fuera de la ciudad de Barcelona
- [ ] M-08 — mapa de clusters de oferta anunciada en Airbnb cruzada contra licencias oficiales por
      dirección (solo ciudad de Barcelona); depende de tener M-01 y el pipeline de Inside Airbnb
- [ ] S-01 — filtro por operador / concentración de mercado
- [ ] S-02 — exportación CSV de datos filtrados
- [ ] C-01 — señales de "zonas de mayor impacto"
- [ ] C-02 — referencias comparativas con otras ciudades que ya hayan limitado los pisos turísticos

---

## Descartado (con motivo)

| Funcionalidad | Motivo del descarte |
|---------------|---------------------|
| Publicar direcciones concretas como "sin licencia" en la web pública | Es un límite de publicación, no de análisis: el pipeline interno sí llega a nivel de dirección (M-08); lo que se publica se agrega en clusters sin resolución individual (`prd.md`, `design-system.md` → `ListingClusterMap`) |
| Datos en tiempo real / feeds en vivo | El proyecto trabaja con datos históricos y estadísticos publicados, con fecha de extracción documentada (`prd.md`) |
| Cuentas de usuario, login o roles | La web es de acceso público y abierto, sin gestión de usuarios (`prd.md`, `architecture.md`) |
| Streamlit como frontend | Sin despliegue nativo en Vercel/Netlify (necesita proceso persistente) y control visual limitado frente al design-system ya acordado — decisión registrada en `architecture.md` |
| AENA y Port de Barcelona como fuentes dedicadas de entradas | Ninguno de los dos respondió al verificar (timeout / 503) y el OTB ya cubre volumen y origen de turistas para "Destinació Barcelona" sin necesitar sumarlos a mano |
| Geocodificar la provincia fuera de la ciudad de Barcelona (API del Catastro) | La eliminación de licencias VUT ocurre en la ciudad, donde Open Data BCN ya da coordenadas reales. Fuera de ella basta municipio + código postal, que están al 100%. Se acepta trabajar a dos niveles (`nivel_geo`, ver `data-model.md`) en vez de invertir en geocodificación masiva de precisión que el análisis no necesita |
