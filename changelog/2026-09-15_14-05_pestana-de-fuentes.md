# Pestaña de fuentes y método

**Fecha:** 2026-09-15 14:05
**Tipo:** Feature
**Requisitos:** transparencia de lo publicado

## Qué se hizo

Ruta nueva `/fuentes`, enlazada desde el panel del mapa. Siete secciones: qué ficheros lee de
verdad el navegador, las siete fuentes originales con su procedencia y su fecha, de dónde sale un
precio, las decisiones que mueven el resultado, el modelo de 2028, lo que nunca se publica y lo que
el análisis no puede decir.

El contenido sale de `docs/fuentes.md`, reescrito para leerse sin conocer el pipeline: sin rutas de
ficheros, sin nombres de columna y sin jerga de capas.

**Aquí es donde se dice el 41%.** El aviso de que cuatro de cada diez precios de hotel están
estimados por un modelo va en esta página, no en el mapa: en el mapa sería una nota al pie que nadie
lee, y aquí es una de las tres cosas que la página existe para contar.

Cada fuente lleva **quién la publica y de cuándo es**, siempre visibles bajo el título. Un dato sin
dueño es una afirmación sin dueño.

## Decisiones de la página

- **Es un componente de servidor.** No hay estado, no hay `fetch`, no hay interacción: nada que
  justifique bajar JavaScript al navegador para leer un texto.
- **El índice se genera de la misma lista que numera las secciones**, para que no puedan
  desincronizarse al añadir una.
- **Las tablas anchas se desbordan dentro de su propio contenedor**, no estrujan la columna. La
  página no tiene scroll horizontal a 375 px; comprobado.

## Verificación

Servidor de desarrollo en local, sin errores de consola:

```
GET /fuentes  →  las siete secciones renderizan
GET /         →  enlace "fuentes y método →" presente, href="/fuentes"
375 px        →  scrollWidth 375 = innerWidth, sin desbordamiento de página
```

**No se ha ejecutado el build de producción.**
