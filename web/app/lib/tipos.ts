/** Formas de lo que publica `pipeline/export/export_mapa.py`. */

/**
 * Una fila de `sustitucion_2028.json`: un barrio, dentro de un escenario, dentro de un momento.
 *
 * **Son turistas, no plazas.** El reparto se hace en habitaciones —que es lo que limita a un
 * hotel: una plaza suelta es la segunda cama de una habitación ya vendida— pero se publica la
 * persona, que es lo que se entiende.
 */
export type BarrioSustitucion = {
  barrio: string;
  /** Turistas que se quedan sin piso en este barrio. */
  salen: number;
  /** Turistas que este barrio absorbe en sus hoteles. */
  llegan: number;
  /** De los que salen, los que encuentran hotel en el mismo barrio. */
  se_quedan: number;
  /** Turistas de este barrio que no encuentran sitio en toda la ciudad. */
  sin_sitio: number;
  /** Habitaciones de hotel que ocupan los que llegan. */
  habitaciones: number;
  /** llegan − salen. Negativo: el barrio pierde turistas alojados. */
  saldo: number;
  km: number | null;
  sobrecoste: number | null;
};

export type TotalesEscenario = {
  momento: string;
  etiqueta: string;
  escenario: string;
  w: number;
  turistas_colocados: number;
  turistas_sin_sitio: number;
  habitaciones_sin_sitio: number;
  km_mediano: number;
  sobrecoste_mediano: number;
  hoteles_usados: number;
  /** Ocupación hotelera **por habitaciones** del INE, no por plazas. */
  ocupacion_hotel: number;
  /** Ocupación estimada de los anuncios de Airbnb. No es un dato oficial: no existe. */
  ocupacion_airbnb: number;
  habitaciones_hotel: number;
  habitaciones_libres: number;
  turistas_a_realojar: number;
};

export type MomentoSustitucion = {
  escenarios: Record<string, BarrioSustitucion[]>;
  totales: TotalesEscenario[];
};

export type Sustitucion = { momentos: Record<string, MomentoSustitucion> };

/**
 * Los dos momentos que se publican.
 *
 * No es un capricho: en un año medio sobran habitaciones de hotel y no se queda nadie fuera, y en
 * julio faltan. Publicar solo la media anual escondía el problema; publicar solo julio lo
 * extendería a doce meses.
 */
export const MOMENTOS = [
  { id: "anio_medio", etiqueta: "Un año medio" },
  { id: "julio", etiqueta: "Julio, la punta" },
] as const;

export type IdMomento = (typeof MOMENTOS)[number]["id"];

/**
 * Una fila de `restauracion_2028.json`.
 *
 * **No hay una versión por escenario, y es a propósito.** El reparto sobre los bares lo decide
 * dónde está el hotel, no qué prefiere el turista, así que basta con el escenario de equilibrio.
 * Sí hay una versión por momento: en julio se mueve más gente que en un mes corriente.
 */
export type BarrioRestauracion = {
  barrio: string;
  /** Locales de restauración del barrio, del censo comercial municipal. */
  locales: number;
  /** Turistas de estas viviendas que hoy duermen a menos de 200 m de esos locales. */
  hoy: number;
  /** Los mismos turistas, ya realojados en hoteles, a menos de 200 m de esos locales. */
  en_2028: number;
  /** en_2028 − hoy. Negativo: al barrio le llegan menos comensales que ahora. */
  cambio: number;
  por_local_hoy: number;
  por_local_2028: number;
};

export type BarrioAirbnb = {
  barrio: string;
  distrito: string;
  anuncios: number;
  con_licencia: number;
  sin_licencia: number;
  sin_acreditar: number;
  precio_plaza_mediano: number | null;
  bandas: Record<string, number>;
  latente: { viviendas: number; plazas: number; recientes: number };
};

/**
 * Los cinco pasos de la barra, en orden.
 *
 * No es una barra continua: el navegador no puede resolver los 5,2 millones de pares
 * VUT-hotel, así que el reparto viene precalculado en estos cinco puntos.
 */
export const ESCENARIOS = [
  { id: "solo_precio", etiqueta: "Solo el precio", w: 0 },
  { id: "sobre_todo_precio", etiqueta: "Sobre todo el precio", w: 0.25 },
  { id: "equilibrio", etiqueta: "Las dos cosas", w: 0.5 },
  { id: "sobre_todo_barrio", etiqueta: "Sobre todo el barrio", w: 0.75 },
  { id: "solo_barrio", etiqueta: "Solo el barrio", w: 1 },
] as const;

export type IdEscenario = (typeof ESCENARIOS)[number]["id"];
