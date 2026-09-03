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
