# web

Dashboard público. Next.js 15 (App Router) + Tailwind 4 + Leaflet.

## Arrancar

```bash
corepack pnpm@11 --dir web install
corepack pnpm@11 --dir web dev
```

`pnpm` no está instalado globalmente en esta máquina y `corepack enable` necesita permisos de
administrador, así que se invoca por `corepack pnpm@11`. La versión va fijada a la 11 porque es la
que pide `CLAUDE.md`.

`pnpm-workspace.yaml` aprueba el script de instalación de `unrs-resolver`, el resolvedor nativo del
eslint de Next: pnpm 11 aborta la instalación entera mientras quede sin decidir.

## Los datos

`public/data/` es una copia de lo que lee la web, no de todo `data/exports/`:

```bash
python pipeline/export/export_mapa.py && python pipeline/export/export_mapa_limpio.py
cd data/exports/mapa && cp barrios_hoy.json dashboard.json criba_airbnb.json licencias.json flujo.json   turistas.json hoteles_pagina.json restauracion_pagina.json puntos_*.json   sustitucion_2028.json flujos_2028.json restauracion_2028.json hoteles.json ../../../web/public/data/mapa/
cp ../geo/barrios.geojson ../geo/peuat.geojson ../../../web/public/data/geo/
```

## Rutas

| Ruta | Qué es |
|---|---|
| `/` | Resumen: cifras de hoteles y Airbnb, barrios que ganan y pierden |
| `/mapa` | Mapa de tres capas (Airbnb, hoteles con radio, restauración) |
| `/airbnb` | Embudo de 15.406 anuncios a 4.985 viviendas, tarjeta a tarjeta, y el registro |
| `/hoteles` | INE, ocupación por banda, mapa de barrios con el PEUAT, hoteles anunciados |
| `/restauracion` | Marcas, locales y barrios que ganan o pierden clientes |
| `/turistas` | Adónde van los turistas de los pisos; viajeros frente al INE |
| `/fuentes` | De dónde sale cada cifra, decisiones y límites |
| `/mapa-anterior`, `/flujos` | El modelo anterior (reparto por precio y cercanía). No están en el menú |

## Código

- `app/components/` — `Graficos` (barras, columnas, matriz, tarjetas), `MapaLimpio`, `MapaHoteles`,
  `Nav`; `MapaBarrios` y `MapaFlujos` solo los usa lo anterior.
- `app/lib/` — `tiposMapa` (formas de los JSON y cálculos del hotel), `hotelesMapa`, `peuat`, `fondo`
  (capa base OSM); `tipos` y `flechas` solo para lo anterior.
