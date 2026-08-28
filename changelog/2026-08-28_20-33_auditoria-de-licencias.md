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
| No declara nada | 1.440 | 16,0% |
| Declara una licencia que no existe | 521 | 5,8% |
| **Candidatos sin licencia válida** | **1.961** | **21,8%** |

**Números imposibles.** De las 1.068 licencias declaradas que no constan (sobre el total de
anuncios), **889 tienen un número por encima del último emitido por la Generalitat** (HUTB-80024):
aparecen valores como `987654`, `990666`, `995187`. Ahí no cabe explicarlo como error de tecleo.
Entre los 1.961 candidatos, 395 están en ese caso.

**Concentración.** 1.092 de los candidatos pertenecen a **56 anfitriones con 5 o más anuncios**
cada uno. Más de la mitad del fenómeno no son particulares despistados.

**El reverso.** Solo el **49,1%** de las licencias VUT de la ciudad (5.233 de 10.654) aparecen
anunciadas en Airbnb. No es indicio de nada irregular — pueden estar en otras plataformas,
alquiladas por temporadas o vacías —, pero dimensiona cuánto del parque legal es visible aquí.

## El error que casi cambia el titular

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
