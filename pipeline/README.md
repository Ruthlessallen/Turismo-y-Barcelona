# Pipeline

Un directorio por capa de destino: cada script escribe en la capa que le da nombre.

```
sources/  → data/raw      todo lo que toca la red
bronze/   → data/bronze   limpieza, unificación, cruces de identidad
gold/     → data/gold     transformación con criterio de negocio
export/   → data/exports  recorte y simplificación para el navegador
```

`sources/` se define por tocar la red, no por lo que produce: geocodificar es una llamada a un
servicio externo, cuesta horas y hay que poder reanudarla, así que vive con las descargas aunque
su salida sea un derivado.

## Orden de ejecución

```bash
python pipeline/sources/descargar_fuentes.py
python pipeline/bronze/unificar_registros.py
python pipeline/bronze/reparar_geometria_municipios.py
python pipeline/sources/geocodificar_registros.py      # horas, reanudable
python pipeline/bronze/asignar_municipio.py            # verifica lo geocodificado
python pipeline/bronze/cruzar_precios_hoteles.py
python pipeline/bronze/enriquecer_hoteles_con_booking.py
python pipeline/bronze/preparar_adr_por_categoria.py
python pipeline/bronze/unificar_airbnb.py
python pipeline/gold/auditar_licencias.py
python pipeline/gold/preparar_hoteles_bcn.py
python pipeline/bronze/rescatar_precios_hoteles.py     # segundo pase del cruce
python pipeline/gold/preparar_hoteles_bcn.py           # recoge lo rescatado
python pipeline/gold/modelar_precios_hoteles_bcn.py
python pipeline/gold/preparar_airbnb_bcn.py
python pipeline/gold/preparar_alojamientos_provincia.py
python pipeline/export/preparar_geometria_web.py
python pipeline/export/export_mapa.py
```

`preparar_alojamientos_provincia` va al final de `gold` porque necesita el precio ya estimado: es
lo que lleva la banda economica desde la ciudad al censo provincial para que el export la publique.

`preparar_hoteles_bcn` aparece dos veces a propósito. El rescate de precios necesita saber a quién
le falta, así que se ejecuta después; y su resultado hay que recogerlo. No es circular —el rescate
solo devuelve pares de licencia y precio— y es idempotente: la segunda vuelta no encuentra nada
nuevo que hacer.

## Notebooks

`notebooks/revisar_airbnb_v2.ipynb` es donde vive la limpieza de Airbnb: clasificación de licencias
contra el registro oficial, deduplicación, criba y construcción de `df_v2`, el conjunto que va a la
web. Sus salidas son `data/gold/airbnb_para_web.csv` y `data/gold/airbnb_excluidos_web.csv`.

**Su criterio y el de `pipeline/gold/preparar_airbnb_bcn.py` todavía no coinciden**: el script del
pipeline aplica sus propios umbrales y produce `airbnb_bcn.csv`. Mientras no converjan, el que
alimenta la web es el del notebook, y es el que describe `docs/criba.md`.

## Diagramas

Dos, porque la trazabilidad tiene dos preguntas y no se responden con el mismo dibujo.

`python pipeline/generar_criba.py` regenera `docs/criba.md`: **que le pasa a cada registro.**
Rombos de decision, cuantos caen por cada rama y adonde van. Los recuentos se leen de los CSV que
el pipeline acaba de producir.

`python pipeline/generar_linaje.py` regenera `docs/linaje.md`: **que fichero alimenta a que
script.**

Ninguno se edita a mano.

## Linaje

`python pipeline/generar_linaje.py` regenera `docs/linaje.md`: un diagrama Mermaid y una tabla de
qué lee y qué escribe cada script, construidos recorriendo el AST del código.

**Ejecutarlo después de cualquier cambio de rutas.** No se edita a mano: un diagrama dibujado
describe el pipeline del día en que se dibujó, y este describe el que hay.

Lo que no alcanza a ver queda listado en el propio documento —rutas que se componen en tiempo de
ejecución, como las de `unificar_registros.py` y `preparar_geometria_web.py`—, para que el hueco se
vea en vez de pasar por completo.
