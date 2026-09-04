# Datos

Organizados en capas, cada una con una regla de entrada. La regla importa más que el nombre: lo que
distingue una capa de otra es **qué se le permite contener**, no en qué orden se generó.

```
raw/      descargas tal cual salieron de la fuente
bronze/   limpio, tipado, una fila por entidad
gold/     transformado: lo que responde preguntas
exports/  JSON que consume la web
```

## raw — lo que se descargó

Ficheros tal como los devolvió la fuente, sin tocar una coma. Si hay que reprocesar todo desde
cero, se hace desde aquí.

**Nada del pipeline escribe en `raw`.** Un derivado guardado aquí deja de tener origen conocido y
alguien acabará leyéndolo creyendo que es la fuente. Ya pasó: `enriquecer_hoteles_con_booking.py`
dejaba una copia en `raw/hoteles/`, otro script la leía congelada, y las mejoras de
geocodificación no llegaban al resultado final sin que nada lo delatara.

Está en `.gitignore`: son cientos de megas y contienen direcciones de 24.000 viviendas.

## bronze — limpio, pero sin interpretar

Una fila por entidad, tipos correctos, duplicados resueltos, coordenadas verificadas. Aquí ocurren
la unificación de fuentes, la geocodificación y los cruces de identidad.

Lo que **no** puede haber: agregados, clasificaciones de negocio, nada estimado. Si una columna
responde a una pregunta en vez de describir un hecho, no es bronze.

## gold — transformado y publicable

Lo que responde a las preguntas del proyecto: la situación de licencia de cada anuncio, el precio
por hotel con su banda económica. Es lo que consumen los cuadernos, los exports y la web.

`gold/calidad/` guarda **informes sobre los datos**, no datos: cuánto acierta el modelo, qué
segmentos se estiman sin ejemplos comparables. Separados a propósito, para que nadie los publique
creyendo que son una tabla más.

## Qué capa puede leer cada script

Cada script escribe en la capa que le da nombre. Sobre **qué puede leer**, la regla es:

> **Lo que lleve un juicio derivado se lee de `gold`.** Precio, banda económica, situación de
> licencia, cualquier cosa estimada o clasificada. Solo puede leerse de `bronze` lo que el script
> se limita a agregar sin interpretarlo.

No es purismo. `export_mapa.py` leía el precio de bronze y publicaba el valor crudo de una ventana
de septiembre: sin corregir de temporada, sin banda, y sin decir si estaba medido o estimado. El
fallo no era el número, era que el mapa no podía distinguir un dato de una suposición. Existiendo
`gold/alojamientos_reglados.csv`, esa confusión ya no puede volver a colarse.

Las VUT y la restauración sí se leen de bronze, y es correcto: el export solo las cuenta por barrio
o municipio, no las clasifica ni les atribuye nada.

## exports — para el navegador

JSON ya recortado y simplificado, generado desde `gold`. Nunca lleva datos a nivel de vivienda:
hoteles y restaurantes salen como puntos porque son establecimientos abiertos al público; las VUT
y los anuncios de Airbnb, solo agregados por barrio o municipio.
