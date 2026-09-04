# La banda económica llega al mapa

**Fecha:** 2026-09-02 21:15
**Tipo:** Fix + Feature
**Requisitos:** Apoyo a M-06 (absorción hotelera)

## Qué se hizo

`export_mapa.py` publicaba el precio leyendo `data/bronze` directamente: llegaba al navegador el
valor crudo de la ventana raspada de finales de septiembre, sin corregir de temporada, sin banda
económica y **sin decir si estaba medido o estimado**.

Se añade `pipeline/gold/preparar_alojamientos_provincia.py` →
`data/gold/alojamientos_reglados.csv`, que une el censo provincial con lo que el análisis dedujo, y
el export pasa a leer solo de ahí.

| | Antes | Ahora |
|---|---|---|
| Puntos con precio | 430, crudo de septiembre | 758 con banda |
| Distingue medido de estimado | no | **sí** (`estimado`, `apoyo`) |
| Corregido de temporada | no | sí |
| Estimaciones sin respaldo | se publicaban | **5 suprimidas** |

De los 758: 451 observados y 307 estimados. Las 5 estimaciones con `apoyo_estimacion = escaso`
salen sin banda ni precio — pensiones y apartaments turístics con menos de diez ejemplos
comparables en el entrenamiento.

## Qué se modificó

- `pipeline/gold/preparar_alojamientos_provincia.py` (nuevo)
- `pipeline/export/export_mapa.py` — `exportar_hoteles()` lee gold y emite `banda`, `estimado`,
  `apoyo` y `barrio` en cada punto
- `data/README.md` — la regla de lectura entre capas
- `pipeline/README.md` — orden de ejecución
- `docs/data-model.md` — la tabla nueva

## Por qué

**La regla que faltaba escrita.** Cada script escribía en su capa, pero nada decía de cuál puede
leer. Queda fijada en `data/README.md`:

> Lo que lleve un juicio derivado se lee de `gold`. Solo puede leerse de `bronze` lo que el script
> se limita a agregar sin interpretarlo.

No es purismo: el fallo no era el número que publicaba el mapa, era que el mapa **no podía
distinguir un dato de una suposición**. Las VUT y la restauración siguen leyéndose de bronze, y es
correcto — el export solo las cuenta por barrio o municipio.

**Por qué no había una tabla gold provincial.** `hoteles_bcn.csv` cubre solo la ciudad, así que el
export no tenía de dónde leer los 1.563 establecimientos de la provincia sin bajar a bronze. Esa
ausencia era la que hacía que la regla se incumpliera sin que nadie lo notara.

**La banda no se extiende fuera de la ciudad.** Los 795 establecimientos del resto de la provincia
salen con `banda_precio` nula. El raspado cubrió la ciudad y el modelo se entrenó con ella;
aplicarlo al Maresme o al Vallès sería inventar. El mapa los pinta igual: su ubicación y su
capacidad sí constan.
