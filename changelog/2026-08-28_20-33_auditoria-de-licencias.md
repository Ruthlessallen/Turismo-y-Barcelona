# Auditoría de licencias: cruce de la oferta anunciada contra el registro oficial

**Fecha:** 2026-08-28 20:33
**Tipo:** Feature
**Requisitos:** Avance sustancial de M-08 (falta el mapa de clusters y la agregación para publicar)

## Qué se hizo

El cruce que da sentido al proyecto: contrastar lo que se anuncia en Airbnb contra el registro
oficial de licencias VUT, para estimar qué parte de la oferta opera sin licencia acreditada.

- `pipeline/notebooks/03_auditoria_licencias.ipynb` — el análisis, con su razonamiento y sus
  límites explícitos.
- `pipeline/transform/auditar_licencias.py` — el mismo criterio como script reutilizable.
- `data/processed/airbnb_situacion_licencia.csv` — 15.406 anuncios clasificados.

## El resultado

De 15.406 anuncios, **8.996 están sujetos al régimen VUT** (vivienda completa, estancia ≤ 31
noches). El resto son habitaciones o alquileres de temporada, con otro régimen legal.

| Situación | Anuncios | % de los sujetos |
|---|---|---|
| Licencia verificada en el registro | 6.006 | 66,8% |
| Exención declarada | 1.029 | 11,4% |
| No declara nada | 1.366 | 15,2% |
| Declara una licencia que no existe | 521 | 5,8% |
| Licencia de otro régimen (hotel, albergue, AT) | 74 | 0,8% |
| **Candidatos sin licencia válida** | **1.887** | **21,0%** |

### La cifra tiene capas — y conviene enseñarlas todas

1.887 es el **techo**, no la conclusión. Dos matices lo reducen:

| | Anuncios |
|---|---|
| Candidatos (techo) | 1.887 |
| — sin reseñas o anteriores a 2025 (posibles anuncios inactivos aún publicados) | 830 |
| — con estancia mínima de **exactamente 31 noches** (justo en la frontera legal) | 828 |
| **= Núcleo: activos y fuera de la frontera** | **727** |

Los dos grupos se solapan, por eso no restan aritméticamente. El **núcleo de 727** es la cifra más
defendible; el 1.887 solo es honesto si se acompaña de estos matices.

**Números imposibles.** De las licencias declaradas que no constan, **889 tienen un número por
encima del último emitido por la Generalitat** (HUTB-80024): aparecen valores como `987654`,
`990666`, `995187`. Ahí no cabe explicarlo como error de tecleo. Entre los candidatos, 395 están
en ese caso.

**Concentración.** 1.030 de los candidatos pertenecen a **46 anfitriones con 5 o más anuncios**
cada uno, mientras que la mayoría de anfitriones (unos 590) tiene un solo anuncio. Son dos
fenómenos distintos y conviene no mezclarlos al contarlos.

**La frontera de las 31 noches.** 828 candidatos fijan la estancia mínima en exactamente 31
noches — el último valor que sigue dentro del régimen VUT; con una noche más quedarían exentos
como alquiler de temporada. Un solo operador (Ukio, alquiler flexible por meses) concentra 588
anuncios ahí, de los cuales 236 declaran exención de temporada y 352 no declaran nada, todos con
mínimo de 31. Que ese patrón sea deliberado o una lectura distinta de la norma no puede deducirse
de estos datos; lo que sí puede decirse es dónde está la línea legal.

**El reverso.** Solo el **49,1%** de las licencias VUT de la ciudad (5.233 de 10.654) aparecen
anunciadas en Airbnb. No es indicio de nada irregular — pueden estar en otras plataformas,
alquiladas por temporadas o vacías —, pero dimensiona cuánto del parque legal es visible aquí.

## Tres errores encontrados, y lo que costaba cada uno

### 1. La sección regional no solo lleva HUTB
También aparecen licencias de otros regímenes: **670 hoteles (`HB-`), 203 albergues (`AJ`) y 28
apartamentos turísticos (`ATB-`)**. El parser inicial solo buscaba `HUTB` y trataba el resto como
"no declara nada": **74 anuncios perfectamente acreditados** contaban como candidatos. Corregido
con la categoría `licencia_otro_regimen`.

### 2. Un anuncio publicado no es un anuncio activo
**830 de los candidatos no tienen ninguna reseña o la última es anterior a 2025**, y ninguno tiene
reseñas en los últimos 12 meses. Pueden ser altas recientes o anuncios inactivos que siguen
publicados; no hay forma de distinguirlos con certeza desde los datos. No se excluyen, pero ahora
se marcan (`actividad_reciente`): sin ese matiz la cifra sobreestima la oferta en circulación.

### 3. El error que casi cambia el titular

El campo `license` contiene **dos** números y confundirlos altera el resultado por completo:

```
Spain - National registration number
ESFCTU000008058000039706000000000000000HUTB-002062349   ← incrusta el HUTB + dígitos de control
Barcelona - Regional registration number
HUTB-002062                                             ← el número real
```

Una expresión regular que busque `HUTB-\d+` en todo el campo captura el nacional y produce un
HUTB inexistente. En la primera versión del análisis eso elevaba las licencias "no encontradas"
del **14,8% al 36,2%**. El script lee únicamente la sección regional, y el notebook documenta la
trampa para que no se repita.

## Decisiones de método que sostienen la cifra

- **Se acota el universo antes de contar.** Solo se consideran candidatos los anuncios sujetos al
  régimen VUT. Contar habitaciones privadas o alquileres de 32+ noches como irregulares sería
  sencillamente incorrecto: se rigen por otra norma.
- **"Candidato", nunca "infractor".** El campo lo rellena el anfitrión, sin validación técnica: una
  licencia real mal escrita cae en el mismo grupo. Coherente con el WON'T de `docs/prd.md`.
- **Se distingue lo imposible de lo dudoso.** Un número por encima del máximo emitido es
  cualitativamente distinto de uno que simplemente no aparece, y se marca aparte
  (`fuera_de_rango`).
- **El detalle se queda en `data/processed/`.** Las coordenadas ya vienen ofuscadas ~200 m por
  Inside Airbnb; la agregación por barrio para lo que se publica es tarea de `export.py`.

## Por qué no se cruza por dirección

Sería lo natural para rescatar candidatos cuya licencia existe pero está mal transcrita. **No es
viable con estos datos**, y conviene que quede escrito:

- Inside Airbnb **desplaza cada coordenada un punto aleatorio en un radio de ~200 m**, justamente
  para impedir identificar la vivienda. En el Eixample ese radio abarca varias manzanas y decenas
  de licencias.
- Inside Airbnb **no publica dirección**, solo esa coordenada ofuscada y el barrio.

Un cruce espacial permitiría decir "hay 40 licencias cerca", nunca "esta es su licencia" — y
afirmar lo segundo sería precisamente lo que prohíbe `docs/prd.md`. La vía practicable es la
inversa: **agregar por barrio y comparar volúmenes**, que sí está en el notebook y muestra barrios
donde se anuncia bastante más de lo registrado.

## Límites que deben acompañar a cualquier publicación de estas cifras

- Solo cubre **Airbnb**. Booking y el resto quedan fuera (ver `docs/roadmap.md`).
- El snapshot es del **24/06/2026**; el registro oficial se consultó el 28/08/2026. Dos meses de
  desfase explican parte de las discrepancias.
- **Nada a nivel de vivienda concreta**: el cruce es agregado, y el dashboard nunca debe permitir
  resolver un anuncio individual (ver `design-system.md` → `ListingClusterMap`).

## Pendiente

- Mapa de clusters con la columna `situacion` (la parte visual de M-08).
- Agregación por barrio en `export.py` para lo que se publique.
- Tests de `leer_licencia`: el caso del número nacional frente al regional es el ejemplo obvio.
