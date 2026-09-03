# Una sola cadena de Airbnb, y el mapa publicando desde la correcta

**Fecha:** 2026-09-03 23:30
**Tipo:** Refactor + Fix
**Requisitos:** Apoyo a M-08 (anuncios sin licencia)

## Qué se hizo

Había **dos pipelines de Airbnb corriendo en paralelo**, con cribas distintas, y el mapa publicaba
desde el que no mandaba:

```
unificar_airbnb.py → airbnb_anuncios.csv → preparar_airbnb_bcn.py → airbnb_bcn.csv → EXPORT
raw                → revisar_airbnb_v2.ipynb → airbnb_para_web.csv → solo criba.md
```

El notebook, que es donde vive el criterio acordado —contraste contra el registro oficial, tres
estados de licencia, números imposibles—, alimentaba únicamente un diagrama. Lo que llegaba a la
web salía del script, con otros umbrales.

Ahora hay una sola cadena:

```
raw → unificar_airbnb.py → bronze/airbnb_anuncios.csv
    → notebooks/revisar_airbnb_v2.ipynb → gold/airbnb_para_web.csv + airbnb_excluidos_web.csv
    → export_mapa.py y generar_criba.py
```

## Qué se modificó

- `pipeline/bronze/unificar_airbnb.py` — añade `host_name`, que el notebook usa
- `pipeline/notebooks/revisar_airbnb_v2.ipynb` — lee bronze en vez del volcado crudo, e incorpora
  el precio por plaza y la banda económica que estaban en el script retirado
- `pipeline/export/export_mapa.py` — consume `airbnb_para_web.csv`; publica por barrio el reparto
  de `con_licencia` / `sin_licencia` / `licencia_sin_acreditar`
- `docs/criba.md` y `docs/linaje.md` regenerados
- **Retirados a `scraps/`**: `preparar_airbnb_bcn.py`, `airbnb_bcn.csv`, `airbnb_excluidos.csv` y
  `otb_perfil_turista_2025-11.csv`, que no lo leía ni escribía nadie

## Por qué

**El notebook no podía calcular precio por plaza** porque leía el volcado resumido de 19 columnas,
sin `accommodates`. Esa columna estaba en `bronze/airbnb_anuncios.csv` desde que se unieron los dos
volcados, pero el notebook nunca llegó a usarlo. Ahora sí: 6.613 de los 6.834 anuncios tienen
precio por plaza, el 96,8%.

**Dos cribas conviviendo acaban mal.** No es que una estuviera mal: es que producían cifras
distintas —7.284 frente a 6.834— sin que nada dijera cuál era cuál, y quien cogiera el fichero
equivocado no tenía forma de saberlo.

## Resultado

`df_v2`, 6.834 anuncios de uso turístico:

| Estado | Anuncios | % | Mediana €/plaza |
|---|---|---|---|
| Con licencia | 4.985 | 72,9% | 55,3 |
| Sin licencia | 1.351 | 19,8% | **33,7** |
| Licencia sin acreditar | 498 | 7,3% | 53,9 |

Los que no acreditan licencia son **casi un 40% más baratos por plaza** que los que sí. Es
coherente con lo visto antes: buena parte de esa oferta es más informal, no solo irregular en el
papel.
