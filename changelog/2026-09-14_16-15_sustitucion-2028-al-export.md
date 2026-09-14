# El escenario de 2028 llega al mapa

**Fecha:** 2026-09-14 16:15
**Tipo:** Feature
**Requisitos:** M-06 (absorción hotelera)

## Qué se hizo

`pipeline/gold/modelar_sustitucion.py` reparte las 30.067 plazas VUT entre el alojamiento reglado
cuando la licencia desaparece, y `export_mapa.py` lo publica agregado por barrio en
`data/exports/mapa/sustitucion_2028.json`.

### El resultado: no caben

```
plazas regladas   84.314
ocupadas hoy      57.222   (67,9%, INE, media de 12 meses)
LIBRES            27.092
plazas VUT        30.067
                  ─────────
SIN SITIO          2.975    (10%)
```

**Los 762 hoteles se llenan** y 2.975 plazas se quedan fuera de Barcelona. Y el número **no cambia
con el escenario**: compiten todas por las mismas 27.092 plazas libres, así que lo que cambia es
quién se queda dentro y a qué precio, no cuántos caben.

### Los cinco escenarios

| Escenario | km medianos | Sobrecoste |
|---|---:|---:|
| solo_precio | 2,32 | 22,8 € |
| sobre_todo_precio | 0,63 | 22,0 € |
| equilibrio | 0,48 | 24,0 € |
| sobre_todo_barrio | 0,40 | 27,0 € |
| solo_barrio | 0,35 | **33,4 €** |

Con la ocupación real, **«pagar lo mismo» deja de ser una opción**: en el escenario de solo precio
el sobrecoste sigue siendo de 22,8 €/plaza porque los hoteles baratos se agotan. Con hoteles vacíos
era de 0,1 €.

### Por qué cinco valores y no una barra continua

El navegador no puede resolver 5,2 millones de pares VUT-hotel. Se precalculan cinco pasos y la
barra de la web se mueve entre ellos.

## Decisiones que quedan escritas en el código

**El peso no se estima, y es deliberado.** Se intentó con la demanda actual de Airbnb y no funciona:
la distancia al centro no la predice (p = 0,48, R² de 0,001) y el coeficiente del precio sale
positivo, que es causalidad inversa y no sensibilidad al precio. Además un turista alemán y uno
andaluz no tienen la misma sensibilidad al precio, y ningún dato disponible los distingue.

**La ocupación es la media anual, no mensual.** Los precios del proyecto son equivalentes anuales
—hoteles y Airbnb corregidos de estacionalidad—, así que cruzarlos con una ocupación mensual
mezclaría dos escalas de tiempo. En agosto el resultado sería mucho peor; en noviembre, mejor.

**Se supone que todos los hoteles están igual de llenos.** El INE no publica ocupación por
establecimiento ni por categoría.

**El turno va de la VUT más cara a la más barata.** Hace falta un orden para que el reparto sea
determinista. No es neutral: las 2.975 plazas sin sitio son **todas de la banda `€`**.

## Verificado

- Las 30.067 plazas de origen cuadran con la suma de los 64 barrios del JSON
- El export no publica `id`, `host_id`, coordenadas ni direcciones: solo agregados por barrio
- `sustitucion_2028.csv`: 320 filas (64 barrios × 5 escenarios)

## Qué debe explicarse en la web

1. El peso lo elige quien mira, no está medido
2. Con la barra en el medio **no pesan al 50%**: mandan más los kilómetros, porque casi todos los
   hoteles cuestan parecido (medido: solo el 2% acaba en el hotel de precio más similar)
3. La ocupación es media anual
4. Son las plazas anunciadas en Airbnb (30.067), no las 61.899 del registro oficial
