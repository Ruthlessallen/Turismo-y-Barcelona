# Página de restauración, mapa de hoteles con el PEUAT y portada retocada

**Fecha:** 2026-10-06 18:00
**Tipo:** Funcionalidad

## Restaurantes repetidos

`SUSHI SAMBA` salía dos veces en Sant Gervasi - la Bonanova. No eran duplicados literales: el censo
lo da de alta dos veces, una por cada portal de un edificio de esquina (Artesa de Segre 11 y Ciutat
de Balaguer 35, a 6 m), con identificador y dirección distintos. `preparar_restauracion_bcn.py`
retira ahora, con el mismo nombre a 10 m o menos, el de la visita más antigua: **14 locales**
(9.479 → 9.465). Efecto: restaurantes con clientes de turistas 61.266 → 65.817 (+7,4 %), 4.479 locales
ganan y 3.830 pierden.

## Páginas

- **`/restauracion` (nueva):** las 10 marcas con más locales, los 5 locales que más ganan clientes en
  2028 y los 5 barrios que más y los 5 que menos, en valor absoluto.
- **`/hoteles`:** se quita la primera sección (su +80 → 90 % chocaba con el +16 % de la portada: no
  es lo mismo, ocupación frente a turistas). Entran las cifras del INE (de `/turistas`, sin las dos
  barras de pernoctaciones). **Mapa anclado a la derecha:** barrios pintados por turistas de más en
  2028, hoteles por barrio y las 12 zonas del PEUAT con interruptor; debajo, los hoteles anunciados.
- **`/turistas`:** sube «adónde van los turistas de los pisos»; se quitan la primera sección, las
  barras de pernoctaciones y los barrios que ganan y pierden (están en la portada).
- **`/airbnb`:** los datos del registro se ven desde la primera tarjeta, debajo.
- **Portada:** KPIs centrados, con el tono oscuro de cada color (azul de los hoteles, naranja de
  Airbnb); ganan y pierden en verde y rojo desaturados, con la cifra de hoy al pasar el ratón; plazas
  a la derecha de titulares y anfitriones.

## Decisiones y cautelas

- Verde y rojo, y no verde y morado como antes: el signo también va en la posición de la barra y en
  el «+» o «−» de la cifra, por si el color no se distingue.
- **PEUAT:** no está verificado qué códigos de zona admiten hoteles nuevos; el mapa lo dice.
- Las marcas son rótulos, no empresas (el censo no trae CIF).

## Documentación

`fuentes.md` (2.6, 3.2), página `/fuentes`, `supuestos.md` (F13, F14), `data-model.md`,
`web-checklist.md`, `roadmap.md`, `CLAUDE.md` y `README.md`.
