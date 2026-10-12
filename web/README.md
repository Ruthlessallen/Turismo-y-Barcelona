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

`public/data/` es una copia de `data/exports/`. Tras regenerar los exports:

```bash
cp data/exports/mapa/*.json web/public/data/mapa/
cp data/exports/geo/*.geojson web/public/data/geo/
node scripts/verificar-datos.mjs        # comprueba que la copia está al día y que las cifras cuadran
```

## Rutas

| Ruta | Qué es |
|---|---|
| `/` | Resumen: cifras de hoteles y Airbnb, barrios que ganan y pierden |
| `/mapa` | Mapa de tres capas (Airbnb, hoteles con radio, restauración) |
| `/airbnb` | Embudo de anuncios a viviendas con registro, tarjeta a tarjeta, y el registro |
| `/hoteles` | INE, ocupación por banda, mapa de barrios con el PEUAT, hoteles anunciados |
| `/restauracion` | Marcas, locales y barrios que ganan o pierden clientes |
| `/turistas` | Adónde van los turistas de los pisos; viajeros frente al INE |
| `/fuentes` | De dónde sale cada cifra, decisiones y límites |

## Código

- `app/components/` — `Graficos` (barras, columnas, matriz, tarjetas), `MapaLimpio`, `MapaHoteles`, `Nav`.
- `app/lib/` — `tiposMapa` (formas de los JSON, `Parametros` y cálculos del hotel), `hotelesMapa`,
  `peuat`, `fondo` (capa base OSM).
- `/fuentes` es un componente de servidor: lee los JSON al construir, así sus cifras no se escriben a mano.
