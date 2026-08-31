# prototipos

Maquetas para verificar datos antes de llevarlos a la app de `web/`. No son la web: son el paso
previo, donde se comprueba que lo exportado se pinta como debe.

## mapa

```bash
python -m http.server 8777      # desde la raíz del proyecto
```

Y abrir `http://127.0.0.1:8777/prototipos/mapa/index.html`. Hay que servirlo, no abrir el fichero
directamente: `fetch` no funciona sobre `file://`.

Lee de `data/exports/`, que genera `pipeline/export_mapa.py` y `preparar_geometria_web.py`.

El panel lateral trae comprobaciones automáticas —puntos fuera de la provincia, cuántas
posiciones son deducidas, barrios y municipios sin datos— porque el prototipo existe justamente
para eso: para que un fallo de datos se vea en pantalla en vez de pasar desapercibido.
