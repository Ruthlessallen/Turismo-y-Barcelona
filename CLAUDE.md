# CLAUDE.md

Referencia para cualquier agente que trabaje en este proyecto. Léelo entero antes de cambiar nada.

## El proyecto

**Turismo-BCN:** dashboard público que estima qué pasa en la **ciudad de Barcelona** cuando
desaparezcan las licencias de pisos turísticos (VUT) en 2028: adónde van los turistas, cómo cambia
la ocupación de cada hotel y la demanda de la restauración. No cubre la provincia.

**Estado:** web en pie (resumen, mapa, Airbnb, hoteles, restauración, turistas, fuentes). Lo que
falta está en `docs/web-checklist.md`.

## Antes de empezar

1. Lee `docs/README.md`: dice qué documento responde a cada pregunta.
2. Las cifras derivadas viven en **un solo sitio**: los JSON de `data/exports/mapa/`
   (`parametros.json` para las ocupaciones). No las escribas a mano en la web ni en la documentación:
   léelas del JSON o remite a él.

## Stack

- Web: Next.js 15 (App Router) + Tailwind 4 + Leaflet, sitio estático en Vercel.
- Pipeline: Python (pandas; geopandas/shapely en `.venv`), arquitectura medallón
  `raw → bronze → gold → exports → web/public/data`.
- Gestor de paquetes: **pnpm 11** vía `corepack pnpm@11`. Nunca `npm` ni `yarn`.

## Estructura

```
data/       raw (no en git) · bronze · gold · exports      → data/README.md y docs/diccionario.md
pipeline/   sources · bronze · gold · export               → pipeline/README.md
web/        app/ (rutas), app/components, app/lib, public/data (copia de data/exports)
docs/       fuentes, supuestos, diccionario/linaje/criba (generados), observaciones, checklist
changelog/  una entrada por cambio importante
scraps/     basura local, ignorada por git: lo que se retira va aquí antes de borrarse
```

## Convenciones

- Comentarios y documentación en español; identificadores como ya están en el código.
- Python: PEP 8 y type hints en funciones públicas. Los scripts son idempotentes.

## Qué NO hacer

- No usar `npm` ni `yarn`.
- No escribir claves ni tokens reales en `.mcp.json` ni en ningún fichero versionado.
- No dar por hecho lo que no has ejecutado: si no has visto pasar el build o la comprobación, di que no.
- **Privacidad.** De cada piso solo se exporta lo que pinta el mapa: posición (ya desplazada hasta
  150 m por la fuente), plazas, dormitorios, precio y banda. **Nunca** id, nombre del anuncio,
  anfitrión ni número de licencia. El anfitrión solo sale agregado: por barrio desde 5 pisos y, en la
  portada, los cinco con más pisos y al menos 20 (`docs/fuentes.md` → 4). Del hotel, la sociedad titular.
- **El hotel no tiene precio propio:** su banda sale del ADR del INE de su categoría. No reintroducir
  precios recogidos de portales de reserva (sus términos no permiten redistribuirlos).
- No mezclar datos observados y proyectados sin marcarlo visualmente.
- No commitear un dataset real completo como fixture de test.
- No añadir una fuente de datos sin documentarla antes en `docs/fuentes.md`.

## Límites de ejecución

1. **Todo se prueba en local** (`localhost`). Sin app levantada, el veredicto es «no verificado».
2. **Desplegar no es tuyo:** prepáralo y explícalo; el botón lo pulsa el usuario.
3. **Los secretos no se imprimen ni se pasan por la línea de comandos.** Van por variable de entorno.
4. **Nada destructivo sin confirmación:** borrar, reescribir historial, vaciar datos. Mira antes de sobrescribir.

## Protocolo de cambios

Tras un cambio importante:

1. Entrada en `changelog/` (formato en `changelog/README.md`).
2. Regenera lo generado si el cambio lo deja viejo: `python pipeline/generar_criba.py`,
   `generar_linaje.py`, `generar_diccionario.py`.
3. Actualiza `docs/fuentes.md` / `docs/supuestos.md` si cambia una fuente o una decisión, y
   `README.md` si cambia cómo se instala o usa.
4. Comprobaciones: `node scripts/verificar-datos.mjs` y, en `web/`: `tsc --noEmit`, `eslint`, `next build`.
5. «Commitea» significa commit **y** push.

## MCPs

Configurarlos es decisión del usuario: pregunta, no instales. Fuente oficial o nada; enseña el
comando exacto antes de ejecutarlo; la clave real nunca va en `.mcp.json`, solo `${VARIABLE}`.

## Ideas aparcadas

Las que no entran ahora se anotan en `mejoras/backlog.md`.
