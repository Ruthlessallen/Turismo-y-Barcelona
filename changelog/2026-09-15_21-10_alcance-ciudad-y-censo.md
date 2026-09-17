# El alcance baja a la ciudad, y la restauración pasa al censo

**Fecha:** 2026-09-15 21:10
**Tipo:** Corrección de datos + alcance
**Requisitos:** M-06, M-08 · deja sin efecto M-07 (comparativa entre municipios)

## Cuatro decisiones

1. **Restauración: capa del mapa y página propia.** En el mapa tiene que poder verse frente al
   desplazamiento de turistas de 2028 — la restauración es quien los recibe.
2. **Comparativa entre municipios: descartada.** El alcance es la ciudad de Barcelona.
3. **Albergues: fuera.** Separar los `AJ` de los `HB-` añade una rama de verificación que no se
   puede cerrar, para 5 anuncios.
4. **Restauración: el censo, no OSM.** Confirmación de lo decidido el 2026-09-10.

## El fallo que esto destapó

`export_mapa.py` seguía publicando **OSM de toda la provincia** en `restauracion.json`, cinco días
después de haber decidido usar el censo. 14.501 puntos, con locales de Manresa, cuando el dato
acordado eran 9.479 de la ciudad.

No se notaba porque ninguna página consume todavía ese fichero. Es exactamente así como un dato
equivocado llega a producción: el export apunta a la fuente vieja, nadie lo mira porque aún no se
pinta, y el día que se pinta ya nadie recuerda que hubo una decisión distinta.

## Qué cambió en `export_mapa.py`

| Salida | Antes | Ahora |
|---|---|---|
| `restauracion.json` | OSM, provincia, 14.501 | Censo, ciudad, **9.479** |
| `hoteles.json` | Provincia, 1.214 | Ciudad, **750** |
| `apartaments_turistics.json` | Provincia, 84 | Ciudad, **13** |
| `vut_por_municipio.json` | 279 municipios | **Ya no se genera** |

El agregado por municipio se deja de publicar porque nadie lo consume y además invita a una
pregunta que el proyecto ha decidido no responder. El dato sigue en `bronze/vut_unificados.csv` por
si algún día se retoma.

Los puntos de restauración ganan `distrito` y pierden `cocina`: el censo no clasifica el tipo de
cocina, y el 67% de los de OSM lo traía vacío de todos modos.

**Nada de esto toca el modelo de sustitución**, que ya trabajaba solo con la ciudad: filtra por
`banda_plaza` no nula, y la banda solo llega a Barcelona.

## Verificación

```
export_mapa.py  →  restauracion  {'total': 9479, 'restaurante': 4429, 'bar': 4272, 'comida_rapida': 778}
                   hoteles       {'total': 755, 'con_punto': 750}
                   vut           {'total': 24075, 'barrios': 65}
```

`data/exports/mapa/*.json` copiado a `web/public/data/mapa/`. `vut_por_municipio.json` borrado de
ambos sitios.

**No se ha ejecutado el build de la web.** Ninguna página consume los ficheros que han cambiado.

## Documentación

- `docs/web-checklist.md` — las cuatro decisiones cerradas, alcance del paso 1 reescrito a la
  ciudad, y retirado el aviso de «bares y restaurantes sin integrar», que describía la fuente de OSM
- `docs/fuentes.md` — retirado el aviso de capa híbrida
- `docs/linaje.md` — regenerado
