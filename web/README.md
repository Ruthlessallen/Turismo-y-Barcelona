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

`public/data/` es una copia de `data/exports/`. Se actualiza con:

```bash
python pipeline/export/export_mapa.py
cp -r data/exports/mapa data/exports/geo web/public/data/
```

## Qué hay

- `app/page.tsx` — el mapa y su panel
- `app/components/MapaBarrios.tsx` — coropletas por barrio (Leaflet, solo cliente)
- `app/lib/tipos.ts` — formas de lo que publica el export
