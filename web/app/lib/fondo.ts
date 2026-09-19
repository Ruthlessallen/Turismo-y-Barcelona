import L from "leaflet";

/**
 * El fondo del mapa, compartido por los dos mapas para que no puedan divergir.
 *
 * **Por qué OpenStreetMap y no CARTO.** El fondo era `light_nolabels` de CARTO, que es más
 * discreto —sin etiquetas comerciales— pero su CDN empezó a devolver «API KEY REQUIRED» sin
 * avisar: en producción el mapa salía con los barrios flotando sobre nada. OSM no pide clave.
 *
 * **Lo que se pierde:** OSM trae etiquetas, carreteras y comercios, así que el fondo compite con
 * el color del barrio. Se compensa bajando la opacidad del fondo, no subiendo la del relleno: el
 * dato tiene que ganar al callejero, y aclarar el fondo es lo que menos altera los colores de la
 * escala.
 *
 * **La atribución no es decorativa.** OSM es ODbL: usar sus tiles obliga a citarlos, y por eso
 * viaja aquí junto a la URL en vez de dejarse a criterio de cada mapa.
 */
export function fondoDelMapa(mapa: L.Map): L.TileLayer {
  return L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    maxZoom: 19,
    opacity: 0.45,
    className: "fondo-atenuado",
  }).addTo(mapa);
}
