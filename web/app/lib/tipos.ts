/** Formas de lo que publica `pipeline/export/export_mapa.py`. */

/** Una fila de `sustitucion_2028.json`: un barrio dentro de un escenario. */
export type BarrioSustitucion = {
  barrio: string;
  /** Plazas VUT que desaparecen de este barrio. */
  salen: number;
  /** Plazas que este barrio absorbe en sus hoteles. */
  llegan: number;
  /** De las que salen, las que encuentran hotel en el mismo barrio. */
  se_quedan: number;
  /** Plazas de este barrio que no encuentran sitio en toda la ciudad. */
  sin_sitio: number;
  /** llegan − salen. Negativo: el barrio pierde alojamiento turístico. */
  saldo: number;
  km: number | null;
  sobrecoste: number | null;
};

export type TotalesEscenario = {
  escenario: string;
  w: number;
  plazas_colocadas: number;
  plazas_sin_sitio: number;
  km_mediano: number;
  sobrecoste_mediano: number;
  hoteles_usados: number;
  ocupacion_partida: number;
  plazas_regladas: number;
  plazas_vut: number;
};

export type Sustitucion = {
  escenarios: Record<string, BarrioSustitucion[]>;
  totales: TotalesEscenario[];
};

/**
 * Una fila de `restauracion_2028.json`.
 *
 * **No hay una versión por escenario, y es a propósito.** La demanda supera a la capacidad
 * hotelera libre, así que todos los hoteles se llenan elija lo que elija el turista: la barra
 * mueve quién va a qué hotel, no cuántos hoteles se llenan.
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
