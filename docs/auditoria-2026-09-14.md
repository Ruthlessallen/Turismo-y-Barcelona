# Auditoría de los datos que enseña la web

**Fecha:** 2026-09-14
**Alcance:** de la web hasta la fuente, y el modelo por dentro.
**Script:** reproducible en `scripts/auditar_web.py`

## Resultado

**43 comprobaciones. 1 fallo real, corregido. 1 falso positivo, explicado.**

## 1. La web lee lo que hay en `data/exports`

Los cuatro ficheros de `web/public/data/mapa/` son **byte a byte idénticos** a los de
`data/exports/mapa/`. No hay copias viejas.

## 2. `exports` cuadra con `gold`

Mismos escenarios, mismo número de barrios y mismo número de flujos en los cinco escenarios. La
suma de `salen` del JSON coincide con la del CSV dentro del redondeo a entero.

## 3. Conservación: no se pierde ni se inventa ningún turista

En los cinco escenarios:

- `suma(salen)` = 30.067 = total de plazas VUT
- `suma(llegan) + suma(sin_sitio)` = 30.067

## 4. El aforo se respeta

Ningún barrio recibe más turistas que su capacidad hotelera libre, en ninguno de los cinco
escenarios.

## 5. Los flujos cuadran con los totales

Lo que sale de un barrio hacia fuera coincide con la suma de sus flechas, menos lo recortado por el
mínimo de 20 turistas:

| Barrio | Salen fuera | En flechas | Recortado |
|---|---:|---:|---:|
| la Sagrada Família | 2.067 | 2.029 | 39 |
| la Dreta de l'Eixample | 1.900 | 1.869 | 31 |
| el Raval | 272 | 215 | 57 |

## 6. Las dos escalas de precio son la misma

VUT y hoteles están los dos en **euros por plaza y noche, equivalente anual**. Comprobado que el
precio anual de la VUT es el de junio dividido por 1,188.

```
VUT    mediana 51,8 EUR/plaza
hotel  mediana 77,8 EUR/plaza
```

**Asimetría que debe estar en la web:** el 3,2% de los precios VUT son estimados por modelo, frente
al **41,3% de los hoteleros**.

## 7. La ocupación sale del INE

67,87%, media de julio de 2025 a junio de 2026 de *Grado de ocupación por plazas. Barcelona*.
Coincide con la que usa el modelo hasta la cuarta cifra decimal.

## 8. El modelo elige lo que dice elegir

- Con `w = 1`, el destino es **siempre** el hotel más cercano. Comprobado en los 6.834.
- Con `w = 0`, el destino es el de precio más parecido en 6.801 de 6.834.

**Los 33 restantes no son un fallo: son empates de coma flotante.** El hotel elegido y el
teóricamente óptimo se diferencian como mucho en **1,42 × 10⁻¹⁴ euros**. Son dos hoteles que cuestan
exactamente lo mismo y el desempate cae de un lado u otro según el orden de operaciones.

## 9. Las cifras de la web salen del dato

| La web dice | El dato dice |
|---|---|
| 27.092 plazas libres | 27.090 |
| 2.975 no caben | 2.975 |
| ocupación del 68% | 67,9% |
| se mueven 0,48 km | 0,48 km |
| pagan de más 24 € | 24,0 € |
| 6.834 viviendas / 30.067 plazas | 6.834 / 30.067 |

## 10. El fallo que había, corregido

`plazas_que_llegan` **incluye a los turistas del propio barrio**, y el panel lo rotulaba «Llegan
desde otros barrios». En la Dreta de l'Eixample eso enseñaba 4.888 donde de fuera llegan 1.780.

Corregido: el panel resta `se_quedan` para «Llegan desde otros barrios» y añade una línea aparte
con el total que ocupa hoteles del barrio.

El panel de `/flujos` no tenía este problema: calcula los suyos desde los flujos entre barrios, que
ya excluyen el propio.

## Lo que la auditoría NO cubre

Esto comprueba que **el cálculo hace lo que dice hacer**, no que el supuesto sea cierto. Siguen en
pie las limitaciones de `docs/supuestos.md`:

- El peso entre precio y ubicación **no está medido**: lo elige quien mira
- Se supone que **todos los hoteles están igual de llenos**: el INE no publica ocupación por
  establecimiento
- El turno de reparto va de la VUT más cara a la más barata, y **eso decide quién se queda sin
  sitio**: las 2.975 son todas de la banda `€`
- Son las plazas **anunciadas en Airbnb**, no las 61.899 del registro oficial
