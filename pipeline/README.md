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

Los scripts que importan `geopandas` o `shapely` (`bronze/asignar_municipio.py`,
`gold/preparar_hoteles_bcn.py`, `export/*`) se ejecutan con el entorno `.venv`; el resto, con Python normal.

```bash
python pipeline/sources/descargar_fuentes.py
python pipeline/sources/descargar_ine_barcelona.py     # serie del INE (la web lee la ocupación de data/raw/ine)
python pipeline/sources/descargar_serie_vut.py         # serie trimestral de licencias
python pipeline/bronze/unificar_registros.py
python pipeline/bronze/reparar_geometria_municipios.py
python pipeline/sources/geocodificar_registros.py      # horas, reanudable
python pipeline/bronze/asignar_municipio.py            # verifica lo geocodificado
python pipeline/sources/geocodificar_hoteles.py
python pipeline/bronze/preparar_adr_por_categoria.py   # ADR oficial por categoría: el precio de hotel
python pipeline/bronze/unificar_airbnb.py
# y después, a mano: pipeline/notebooks/revisar_airbnb_v2.ipynb
python pipeline/gold/separar_sin_registro.py           # saca los pisos sin registro acreditado
python pipeline/gold/preparar_hoteles_bcn.py
python pipeline/gold/preparar_alojamientos_provincia.py
python pipeline/gold/preparar_restauracion_bcn.py
python pipeline/export/preparar_geometria_web.py
python pipeline/export/export_criba.py
python pipeline/export/export_mapa_limpio.py           # llama a gold/modelar_flujos_banda
python pipeline/generar_criba.py && python pipeline/generar_linaje.py && python pipeline/generar_diccionario.py
```

`gold/modelar_flujos_banda.py` no se ejecuta aparte: lo importa `export_mapa_limpio.py`. Las
ocupaciones del modelo (hotel 80,2 %, pisos 38,3 %) y el radio de 200 m viven en `gold/modelo.py`
y viajan a la web por `parametros.json`.

**El precio de hotel es el ADR del INE de su categoría** (`gold/bandas.py`): no hay precios por
hotel ni modelo de estimación. `preparar_alojamientos_provincia` va después de `preparar_hoteles_bcn`
porque es lo que lleva la banda al censo que lee el export.

## Notebooks

`notebooks/revisar_airbnb_v2.ipynb` es donde vive la limpieza de Airbnb: clasificación de licencias
contra el registro oficial, deduplicación, criba y construcción de `df_v2`, el conjunto que va a la
web. Lee `data/bronze/airbnb_anuncios.csv` y escribe `data/gold/airbnb_para_web.csv` y
`airbnb_excluidos_web.csv`, que consumen `separar_sin_registro.py`, `export/export_criba.py` y
`generar_criba.py`. **Después del notebook** se ejecuta `separar_sin_registro.py` (idempotente).

## Diagramas

Dos, porque la trazabilidad tiene dos preguntas y no se responden con el mismo dibujo.

`python pipeline/generar_criba.py` regenera `docs/criba.md`: **que le pasa a cada registro.**
Rombos de decision, cuantos caen por cada rama y adonde van. Los recuentos se leen de los CSV que
el pipeline acaba de producir.

`python pipeline/generar_linaje.py` regenera `docs/linaje.md`: **que fichero alimenta a que
script.**

Ninguno se edita a mano.
