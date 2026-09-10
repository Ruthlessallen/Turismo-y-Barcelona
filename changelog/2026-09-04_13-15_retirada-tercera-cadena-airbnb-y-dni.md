# Retirada de la tercera cadena de Airbnb y anulación de cuatro DNI

**Fecha:** 2026-09-04 13:15
**Tipo:** Fix + Refactor
**Requisitos:** M-08 (oferta anunciada frente a licencias) y política de datos personales de
`CLAUDE.md`

## Qué se hizo

Auditoría de todo lo versionado en `data/`, a raíz de la pregunta de si había subido algo que ya no
hiciera falta. Tres hallazgos, los tres corregidos.

### 1. Una tercera cadena de Airbnb, paralela y contradictoria

`data/gold/airbnb_situacion_licencia.csv` (5,5 MB, 15.406 anuncios) y `pipeline/gold/
auditar_licencias.py`, que lo produce, clasificaban la licencia con **seis estados** propios:

```
licencia_verificada 6.160 · sin_declarar 4.124 · exencion_declarada 2.960
licencia_no_encontrada 1.068 · licencia_otro_regimen 901 · hutb_no_verificable 193
```

No es la taxonomía de tres estados que publica la web —`con_licencia` / `sin_licencia` /
`licencia_sin_acreditar` sobre 6.834 anuncios—, va sobre otra criba y no contrasta contra el
registro oficial como hace `revisar_airbnb_v2.ipynb`. **Nada del pipeline lo consumía**: solo lo
leían los cuadernos exploratorios 03 y 06.

Es el mismo fallo que se corrigió retirando `preparar_airbnb_bcn.py` —dos cadenas de Airbnb en
paralelo, y el mapa publicando desde la que no mandaba— con un tercer superviviente que se había
pasado por alto. A `scraps`.

### 2. Un huérfano y una carpeta fuera de la arquitectura

`data/processed/hoteles_bcn_precios_a_revisar.csv`, sin ninguna referencia en el pipeline. Era lo
último que quedaba en `data/processed/`, carpeta que no forma parte de la arquitectura medallón
desde el 2026-09-02. La carpeta desaparece.

### 3. Cuatro DNI de persona física

Los `nif` de bronce son CIF de sociedad casi en su totalidad —8.721 de 8.726 en
`vut_unificados.csv`, 3.101 de 3.107 en `titulares.csv`—, que es dato mercantil público. Pero se
colaban **2 DNI de persona física en cada archivo**.

`unificar_registros.py` anulaba el NIF solo cuando la fuente escribía el marcador `"No aplica"`. El
marcador no siempre está puesto: unas pocas filas traen el DNI escrito. Ahora la **forma del
número** decide, que no depende de que la fuente se acuerde de marcarlo: un CIF de sociedad empieza
siempre por letra, un DNI son ocho dígitos y una letra.

Anulados también en los CSV ya generados. En `titulares.csv` quedan las dos filas con el NIF vacío
**a propósito**: `siguiente` sale de `max(mapa.values()) + 1`, así que borrarlas liberaría esos dos
enteros y la siguiente pasada se los daría a otro titular, rompiendo la estabilidad de `titular_id`.

## Lo que se comprobó y estaba bien

- **`data/exports/` limpio**: ni `nif`, ni `titular`, ni `direccion`, ni `host_id`. Todo agregado.
- `data/raw/` correctamente ignorado — solo viajan los dos README.
- `web/public/data/` no está duplicado en git.
- El resto de datasets de bronce y oro tienen todos consumidor declarado.

## Qué se modificó

- `pipeline/bronze/unificar_registros.py` — el DNI se detecta por forma, no por marcador.
- `data/bronze/vut_unificados.csv`, `data/bronze/titulares.csv` — 4 DNI anulados.
- `pipeline/README.md` — `auditar_licencias.py` fuera de la secuencia de ejecución.
- `.gitignore` — la nota citaba `data/processed/`, que ya no existe.
- Regenerados `docs/linaje.md` y `docs/criba.md`.

## Nota sobre la rama `scraps`

Un `git merge main` en `scraps` **borra la carpeta `scraps/`**: `main` la sacó del seguimiento en su
día, y el merge propaga esa eliminación. Los seis archivos que ya vivían allí se restauran en el
mismo commit que añade los tres nuevos. Conviene saberlo antes del próximo traslado.
