# data/raw — datos crudos de las fuentes

> **Esta carpeta no se versiona.** Solo se sube este README. Para reconstruirla:
>
> ```bash
> python pipeline/sources/descargar_fuentes.py
> ```
>
> Dos motivos para excluirla del repo:
> 1. **Datos personales.** El Registre de Turisme incluye nombre y apellidos de 844 titulares
>    persona física junto a la dirección de su propiedad. Son públicos en origen, pero
>    republicarlos aquí sería una distribución distinta. Lo derivado (`data/processed/`) sí se
>    versiona: el pipeline ya lo genera sin esos campos.
> 2. **Peso.** Son ~90 MB perfectamente redescargables.
>
> Los PDF de OTB son la excepción: el script no los baja, porque son infografías que requieren
> transcripción manual (ver más abajo).

Ficheros descargados el 27-28/08/2026 para verificar las fuentes candidatas de
`docs/architecture.md` (Fase 1 de `docs/roadmap.md`).

## vut/
- `opendata_bcn_hut_2016-2026Q1.csv` — Open Data BCN, licencias VUT de la ciudad de Barcelona
  (dirección, coordenadas, nº HUTB, plazas). Serie base, no el trimestre más reciente por separado.
- `opendata_bcn_dataset_metadata.json` — metadatos del dataset (todos los recursos trimestrales
  disponibles, licencia CC BY 4.0), vía API CKAN.

## hoteles/
- `opendata_bcn_hotels_snapshot.csv` — Open Data BCN, hoteles de la ciudad de Barcelona. **Snapshot
  único, sin actualizar desde 2023** — no sirve como serie histórica (ver `architecture.md`).
- `opendata_bcn_dataset_metadata.json` — metadatos del dataset.

## airbnb/
- `insideairbnb_barcelona_2026-06-24_listings.csv` — Inside Airbnb, 15.430 anuncios de la ciudad de
  Barcelona a fecha del snapshot. El campo `license` trae el nº HUTB en ~48% de los casos (ver
  `data-model.md` → `oferta_airbnb`).
- `insideairbnb_barcelona_2026-06-24_reviews.csv` — 1.033.523 reseñas (`listing_id` + fecha), de
  11.822 anuncios, entre 2010 y julio de 2026. Sirve para estimar duraciones de estancia a partir
  del hueco entre reseñas consecutivas. Se eligió la versión ligera sobre `data/reviews.csv.gz`
  (133 MB) porque aquella añade nombre del huésped y texto del comentario: datos personales que no
  hacen falta.

## registre_turisme/
- `muestra_5_registros.json` — la primera muestra de 5 filas que se usó solo para comprobar la
  estructura del dato la primera vez, no es el dataset real. Se conserva de referencia.
- `completo_provincia_barcelona_27180.json` — **descarga real completa** de la provincia de
  Barcelona (`$where=prov_ncia='Barcelona'`), 27.180 registros: 23.975 HUT, 1.442 hoteles, 831
  llars compartides, 734 turisme rural, 120 Apartaments Turístics, 78 càmpings.
- `hut_provincia_barcelona.csv` — solo `Habitatges d'ús turístic` (23.975 filas) — esto es
  `licencia_vut` en `data-model.md`, ya filtrado y listo.
- `hoteles_y_apartaments_turistics_provincia_barcelona.csv` — `Hotels` + `Apartaments Turístics`
  juntos (1.562 filas) — esto es `licencia_hotel` en `data-model.md` (ver el campo `tipo` para
  distinguirlos).
- Todos traen **CIF/razón social del titular**, dirección y plazas — es la fuente que resuelve el
  hueco de "empresa titular" que no tenían Open Data BCN.

## peuat/
- `opendata_bcn_mapa_peuat.gpkg` — Open Data BCN, mapa de zonas del PEUAT. Verificado: capa de
  polígonos con 12 zonas (`ZE1`, `ZE2`, `ZE3A`, `ZE3B`, zona de exclusión...), más granular que las
  4 zonas de las que habla la prensa. GeoPackage — se convierte a GeoJSON al montar el pipeline
  (con GDAL/`ogr2ogr` o una librería equivalente; no se ha convertido todavía).
- `opendata_bcn_dataset_metadata.json` — metadatos del dataset.

## restauracion_hoteles_provincia/
- `diba_cens_activitats_muestra_1000.json` — Diputació de Barcelona, censo de actividades (API
  `do.diba.cat/api/dataset/establiments/format/json`). Trae nombre comercial + **NIF + razón
  social** + dirección + coordenadas + actividad (texto libre: "BAR", "RESTAURANT", etc., no un
  código estable — hay que clasificar por texto o por `codi_nace`). 42.050 registros en total en
  la fuente completa, cubre 200+ municipios. Actualizado a diario.
- `diba_dataset_metadata.json` — metadatos del dataset (CC0/CC BY según la vista, verificar cuál
  aplica de verdad al usarlo).

## geometria/
- `icgc_municipis_provincia_barcelona.geojson` — **311 municipios**, ya filtrados a la provincia de
  Barcelona (coincide con la cifra oficial). GeoJSON real en WGS84, listo para mapa web sin
  reproyectar.
- `icgc_municipis_catalunya_completa.geojson` — los 947 municipios de toda Catalunya (sin filtrar),
  útil para poner en contexto el Decret Llei 3/2023. Fuente: WFS del ICGC
  (`geoserveis.icgc.cat/.../divisions-administratives/wfs`, `outputFormat=geojson`).

## otb/
- `otb_perfil_turista_2025-11.pdf` y `otb_perfil_turista_region_2025_anual.pdf` — informes reales
  del Observatori del Turisme a Barcelona. **Son infografías, no tablas** — `pdfplumber` no las
  extrae bien automáticamente. Se renderizaron 3 páginas como imagen (`pagina4_ciutat.png`,
  `pagina5_regio.png`, `pagina6_destinacio.png`) y se transcribió a mano verificando visualmente.
  El resultado limpio está en `data/processed/otb_perfil_turista_2025-11.csv`.
- `otb_perfil_turista_2025-11_texto_extraido.txt` — texto crudo de `extract_text()`, de referencia.

## Descartado (ver `docs/roadmap.md`)
AENA y Port de Barcelona — ninguno respondió al verificar (timeout / 503). Se sustituyen por OTB,
que ya cubre volumen y origen de turistas.
