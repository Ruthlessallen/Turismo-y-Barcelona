# Portada con barrios y anfitriones, registro oficial y pisos sin licencia

**Fecha:** 2026-10-06 10:00
**Tipo:** Funcionalidad

## Qué cambia

- **Portada:** los cinco barrios que más ganan y los cinco que más pierden turistas en 2028 (los
  mismos de `/turistas`) y los cinco anfitriones con más pisos (Sweett 265, AB Apartment Barcelona
  236, Stay Unique 132, Habitat Apartments 109, Ukio 107). Solo anfitriones con 20 pisos o más.
- **`/turistas`:** se quita la tabla de «lo que el INE cuenta y nosotros no». La tarjeta de pisos
  decía «de los viajeros de hoteles y pisos»: pasa a «de los turistas se alojan en pisos, según
  nuestro dataset» y se calcula por noche con nuestros propios datos, 17–20 %, sin el INE ni la
  estancia.
- **`/airbnb`, bajo la tarjeta de licencias sin anuncio:** dos bloques.
  - El registro oficial: 10.623 licencias, 61.826 plazas, licencias por distrito, licencias en
    vigor por trimestre, desde cuándo y el HUTB más alto emitido.
  - Pisos sin registro válido dentro de los 6.834: 498 dicen tener registro y no consta (334 con
    número imposible) y 1.351 deberían tenerlo y no lo declaran. 1.849 pisos, 6.301 plazas, el 21 %.
- La tarjeta de `/airbnb` ahora scrollea dentro de sí misma cuando el contenido no cabe.

## Decisión posterior: los pisos sin registro salen del modelo

Esa misma mañana se decidió quitarlos: la ley quita licencias, y estos 1.849 pisos (6.301 plazas) no
tienen ninguna acreditada. Si siguen operando, será fuera del mercado legal.

- `gold/separar_sin_registro.py` (nuevo, idempotente) los mueve de `airbnb_para_web.csv` a
  `airbnb_excluidos_web.csv` con `motivo_exclusion = sin_registro_acreditado`. Es el séptimo y último
  descarte del embudo: **15.406 → 4.985**.
- **Efecto, un año medio:** 9.102 turistas por noche (antes 11.516), 4.486 habitaciones de hotel
  absorbidas (5.706), ocupación hotelera 90,2 % (93,0 %), turistas nuevos en hoteles +16,0 %
  (+20,3 %), facturación 185–232 M€ (222–278), restaurantes +7,5 % (+9,2 %), con 4.409 locales que
  ganan y 3.718 que pierden. **En julio ya no falta sitio** (antes, 1.273 turistas).
- `/airbnb`: la tarjeta final se queda en la barra de plazas y sus tres leyendas; el registro
  oficial y los pisos sin registro pasan **debajo** de la tarjeta, con la página ya con scroll.
- Textos con la cifra vieja corregidos en `/fuentes`, `/flujos`, `/mapa-anterior` y los `.md`.
- Para volver atrás: no ejecutar `separar_sin_registro.py` y reejecutar el notebook.

## Sobre los anfitriones

Se había escrito que «un particular nunca sale». Era exagerado: el nombre es el público en Airbnb y
el umbral es una cautela nuestra. Reescrito en `/fuentes` y `fuentes.md`.

## Corregido en el camino

Un error propio en el export: una variable pisaba a otra y el primer tramo de la barra de licencias
salía con 0 plazas. Detectado al mirar la página; corregido antes de subir.

## Documentación

`supuestos.md` (C5 ampliado, C6 nuevo), `fuentes.md` (3.2 f, privacidad, qué lee la web), la
página `/fuentes` (privacidad y porcentaje), `CLAUDE.md`, `README.md`, `data/README.md` y
`web-checklist.md`.
