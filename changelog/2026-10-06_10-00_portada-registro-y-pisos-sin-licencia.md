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

## Importante: siguen contados

Esos 1.849 pisos **siguen dentro de los 6.834** y del modelo. Solo con los 4.985 con registro serían
9.102 turistas por noche (11.516 ahora) y una ocupación hotelera del 90,2 % (93,0 % ahora). Está
calculado, no publicado.

## Corregido en el camino

Un error propio en el export: una variable pisaba a otra y el primer tramo de la barra de licencias
salía con 0 plazas. Detectado al mirar la página; corregido antes de subir.

## Documentación

`supuestos.md` (C5 ampliado, C6 nuevo), `fuentes.md` (3.2 f, privacidad, qué lee la web), la
página `/fuentes` (privacidad y porcentaje), `CLAUDE.md`, `README.md`, `data/README.md` y
`web-checklist.md`.
