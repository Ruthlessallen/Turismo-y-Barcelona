<h1 align="center">Turismo-BCN</h1>

<p align="center">
  Qué puede pasar en el turismo de la provincia de Barcelona cuando desaparezcan las ~10.000
  licencias de pisos turísticos de la ciudad — datos cruzados, no intuición.
</p>

---

## Qué es esto

Barcelona elimina progresivamente sus licencias de vivienda de uso turístico (VUT), con horizonte
2028. Este proyecto cruza oferta turística (apartamentos, hoteles, bares/restaurantes) con demanda
(entradas por aeropuerto y puerto, estadísticas turísticas) en toda la provincia de Barcelona,
2021–2031, para entender si esa oferta la absorben los hoteles, se desplaza a otros municipios, o
simplemente desaparece.

Es una web pública, sin cuentas ni login — código y datos abiertos en este repositorio. Detalle
completo en [`docs/prd.md`](docs/prd.md).

## Estado actual

**En desarrollo — fase de investigación y recolección de datos.** Todavía no hay pipeline ni
dashboard: el primer objetivo es confirmar que las fuentes de datos necesarias existen y son
utilizables. Ver [`docs/roadmap.md`](docs/roadmap.md) → Fase 1.

## Requisitos previos

- Node.js + pnpm v11 (frontend)
- Python 3.11+ (pipeline de datos)

## Variables de entorno

Copia `.env.example` a `.env.local` y rellena lo que aplique. Todavía no hay variables de fuentes
de datos definidas — se añaden según se confirme cada fuente (ver `docs/roadmap.md` → Fase 1).

## Instalación y desarrollo

```bash
# Frontend (cuando exista, ver "Estado actual")
pnpm install
pnpm dev

# Pipeline de datos / notebooks de exploración
python -m venv .venv
.venv/Scripts/activate       # Windows; en Linux/Mac: source .venv/bin/activate
pip install -r pipeline/requirements.txt
jupyter lab pipeline/notebooks/
```

*(`web/` todavía no tiene código. `pipeline/` tiene un primer notebook de exploración de las
fuentes verificadas — ver `pipeline/notebooks/01_exploracion_fuentes.ipynb`.)*

## Estructura de carpetas

```
data/         → datos crudos, procesados y exportados (ver docs/architecture.md)
pipeline/     → recolección y ETL en Python
web/          → dashboard en Next.js
docs/         → documentación viva del proyecto
changelog/    → registro de cambios
mejoras/      → ideas futuras no implementadas
```

## Cómo contribuir

Este repo sigue el protocolo de [`CLAUDE.md`](CLAUDE.md): toda sesión de trabajo (humana o con
agente) lee `docs/` antes de tocar código, cada feature se acuerda en una ficha
(`docs/features/`) antes de construirse, y cada cambio importante deja registro en `changelog/`.

## Licencia

MIT — ver [`LICENSE`](./LICENSE).
