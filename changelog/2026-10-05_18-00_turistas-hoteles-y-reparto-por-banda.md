# Páginas de turistas y hoteles, y el reparto por banda pasa a oficial

**Fecha:** 2026-10-05 18:00
**Tipo:** Funcionalidad

## Por qué

Tras ver el prototipo de flujos por banda, se decidió que es la regla de la web: el turista va a su
banda y, si no hay hueco, a la siguiente más cara. Con ella salen los gráficos de flujo y lo que
recibe cada hotel, y hacía falta una página donde contar cuántos turistas entran en juego frente al
INE y otra para los hoteles.

## Qué cambia

- **`gold/modelar_flujos_banda.py` sustituye al reparto por cercanía y precio** en la web
  (`modelar_sustitucion.py` solo alimenta ya a `/mapa-anterior`). Un solo reparto alimenta al hotel,
  a los restaurantes y a los gráficos. Los restaurantes: 4.245 locales ganan y 4.326 pierden (antes
  4.147 y 4.444); el total, +9,2 %, no cambia porque sale del supuesto de cocina.
- **Mapa, punto de hotel:** habitaciones, ocupadas hoy, ocupadas en 2028 y cuántos pisos absorbe.
  Se quita la línea «Solo este hotel, sin contar a los vecinos»: ya no aplica, el reparto es global.
- **Mapa, hoteles anunciados:** punto azul con exclamación (dos, los que tienen dirección).
- **`/turistas` (nueva):** turistas en el conjunto de datos, lo que dice el INE, cuánto se alejan
  (mediana 0,37 km), de qué banda sale cada uno y a cuál llega, y los barrios que suben y bajan.
- **`/hoteles` (nueva):** ocupación hoy y en 2028 (80,2 % → 93,0 %), por banda y mes a mes,
  habitaciones por categoría y hoteles anunciados con su fuente.
- **Portada:** añade la banda económica de Airbnb (por plaza), junto a la de los hoteles (por
  habitación).
- **Nav:** Hoteles y Turistas.
- **Hoteles anunciados:** `data/bronze/hoteles_nuevos_bcn.csv`, de prensa, a mano. 189
  habitaciones de obra nueva; el resto son reformas o cambios de gestión.

## Decisiones

- Se mantiene el descarte de los pisos sin reseña desde septiembre de 2025.
- La estancia de los pisos se supone de 3 noches para pasar de pernoctaciones a turistas al año.

## Documentación

`fuentes.md` (nueva 2.9 y 3.2 reescrita), la página `/fuentes`, `supuestos.md` (F10–F12),
`web-checklist.md` y `roadmap.md`.
