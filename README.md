<h1 align="center">Turismo-BCN</h1>

<p align="center">
  Qué pasa en Barcelona cuando desaparezcan las licencias de pisos turísticos en 2028:
  cuántos turistas cambian de alojamiento, adónde van y a quién beneficia.
</p>

---

## Qué es

Web pública, sin cuentas, con código y datos abiertos. Cruza los pisos turísticos con licencia
(Airbnb), los hoteles y los bares y restaurantes de la **ciudad de Barcelona** para estimar, en un
año medio, adónde irían los turistas de los pisos y cómo cambia la demanda de cada hotel y barrio.

| Página | Qué responde |
|---|---|
| Resumen | Cifras de hoteles y Airbnb; barrios que ganan y pierden turistas |
| El mapa | Dónde está cada piso, hotel y restaurante; qué absorbe cada hotel en un radio de 0 a 500 m |
| Airbnb | De 15.406 anuncios a 4.985 viviendas con registro, y qué licencias no vemos |
| Hoteles | Ocupación por banda, PEUAT, hoteles anunciados |
| Restauración | Marcas con más locales; locales y barrios que ganan o pierden clientes |
| Turistas | Distancia y bandas del realojo; viajeros frente al INE |
| Fuentes | De dónde sale cada cifra, supuestos y límites |

Es un modelo con supuestos, no una predicción: están todos en [`docs/supuestos.md`](docs/supuestos.md).

## Arquitectura

```
data/raw → data/bronze → data/gold → data/exports → web/public/data → web (Next.js)
 descargas   limpio       tablas y     JSON por        copia             páginas
 (no en git)              modelo       página          publicada
```

- `pipeline/` — Python, un directorio por capa (`sources`, `bronze`, `gold`, `export`).
- `web/` — Next.js 15 + Tailwind 4 + Leaflet, sitio estático.
- `docs/` — documentación; empieza por [`docs/README.md`](docs/README.md).

## Puesta en marcha

```bash
# Web
corepack pnpm@11 --dir web install
corepack pnpm@11 --dir web dev          # http://localhost:3000

# Pipeline (Python 3.11+)
python -m venv .venv && .venv/Scripts/activate     # Linux/Mac: source .venv/bin/activate
pip install -r pipeline/requirements.txt
```

El orden de ejecución del pipeline está en [`pipeline/README.md`](pipeline/README.md) y cómo
actualizar los datos de la web en [`web/README.md`](web/README.md). Los datos crudos no se
versionan (llevan datos personales): se bajan con `pipeline/sources/descargar_fuentes.py`.

## Reglas del repo

Ver [`CLAUDE.md`](CLAUDE.md): `pnpm` y nunca `npm`, sin claves en el repo, y qué se publica de cada
piso (solo posición desplazada, plazas, dormitorios, precio y banda; nunca nombre, anfitrión ni licencia).

## Licencia

MIT — ver [`LICENSE`](./LICENSE).
