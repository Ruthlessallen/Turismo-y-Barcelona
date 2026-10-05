/** Formas de lo que publica `pipeline/export/export_mapa_limpio.py`. */

/**
 * [lat, lon, plazas, dormitorios, precio de la noche del piso entero, precio por plaza,
 *  banda por plaza, origen del precio, barrio, habitaciones que pide el piso]
 *
 * La última es la regla del modelo: los dormitorios, y uno si el anuncio declara cero (un estudio).
 */
export type Piso = [number, number, number | null, number | null, number | null,
  number | null, string | null, string | null, string, number | null];

export type Hotel = {
  nom: string | null; titular: string | null; cat: string | null; barrio: string | null;
  lat: number; lon: number;
  plazas: number | null; hab: number | null;
  /** Solo bandas, nunca el euro: por habitación (100/175/300) y por plaza (40/70/120). */
  banda_hab: string | null; banda: string | null; origen: string | null;
};

export type Restaurante = {
  nom: string | null; tipo: string | null; barrio: string | null; dir: string | null;
  lat: number; lon: number;
  /** Clientes potenciales hoy: turistas por noche a menos de 200 m (los de piso cuentan la mitad). */
  tur: number | null;
  /** Lo mismo en 2028: los turistas de piso duermen en hoteles y cuentan enteros. */
  tur28: number | null;
  /** Cambio porcentual entre hoy y 2028. Nulo si hoy no tiene turistas cerca. */
  mas: number | null;
};

export type BarrioHoy = {
  barrio: string;
  pisos: number; plazas_pisos: number;
  hoteles: number; plazas_hoteles: number;
  restaurantes: number; alta: number;
  /** [ocupación 38,3 %, ocupación 48 %]: la de los pisos no es un dato oficial, es un rango. */
  turistas_pisos: [number, number];
  /** Ocupación por plazas del INE, 67,9 %. */
  turistas_hoteles: number;
  /** Habitaciones de hotel: lo que el hotel alquila. El piso se alquila entero, así que cuenta 1. */
  habitaciones_hoteles: number;
  /** Mediana de la noche del piso entero. El hotel solo tiene banda, no euro. */
  precio_pisos: number | null;
  /** La banda de los pisos es por plaza (única que tienen); la del hotel, por habitación. */
  banda_pisos: string | null;
  banda_hoteles: string | null;
  /** Quién reúne más hoteles (sociedad titular) y más pisos (anfitrión según Airbnb, desde 5). */
  operador_hoteles: { nom: string; n: number } | null;
  operador_pisos: { nom: string; n: number } | null;
  /** Nombre comercial que más locales repite en el barrio. No es la empresa: el censo no la trae. */
  marca: { nom: string; locales: number } | null;
  /** Clientes potenciales de los locales del barrio, hoy y en 2028. */
  demanda_hoy: number;
  demanda_2028: number;
  /** [38,3 %, 48 %] × 365 noches × precio de la noche. Orden de magnitud, no facturación real. */
  facturacion_pisos: [number, number];
};

export type DatosMapa = {
  geo: GeoJSON.FeatureCollection;
  barrios: BarrioHoy[];
  pisos: Piso[];
  hoteles: Hotel[];
  restaurantes: Restaurante[];
};

export type ModoAlojamiento = "puntos" | "barrios";
export type TipoBarrio = "pisos" | "hoteles";
export type ColorRestaurante = "hoy" | "cambio";
export type Capas = { airbnb: boolean; hoteles: boolean; restauracion: boolean };

/** Lo que el panel enseña: un barrio, o un hotel con su radio. */
export type Foco = { tipo: "barrio"; nombre: string } | { tipo: "hotel"; hotel: Hotel } | null;

export const COLOR = { piso: "#e8710a", hotel: "#1f5fa8", restaurante: "#7b3fa0" } as const;

/**
 * Ocupaciones del proyecto. La de los pisos es un rango estimado (calendario 38,3 %, reseñas
 * 38,8 %, y 48 % como extremo alto); la del hotel es la oficial del INE por habitaciones.
 */
export const OCUPACION = {
  pisoBaja: 0.383, pisoAlta: 0.48, hotelAnio: 0.802, hotelJulio: 0.865,
} as const;

export const n = (v: number | null | undefined) =>
  v == null ? "—" : v.toLocaleString("es", { useGrouping: "always" });

/** Metros entre dos puntos. Plano local: a 41° de latitud el error a 500 m es despreciable. */
export function distanciaM(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const dy = (lat2 - lat1) * 111_320;
  const dx = (lon2 - lon1) * 111_320 * Math.cos((41.39 * Math.PI) / 180);
  return Math.hypot(dx, dy);
}

/**
 * Qué pasa alrededor de un hotel: cuántos pisos hay a menos de `radio` metros, cuántas habitaciones
 * pedirían y cuántas puede absorber el hotel.
 *
 * **Este hotel solo.** Otros hoteles del mismo radio compiten por los mismos pisos, así que la suma
 * de lo que absorbe cada uno puede contar dos veces a un mismo turista. Lo que sí responde es
 * cuánto de lo que tiene alrededor cabría en este hotel.
 */
export function analisisHotel(h: Hotel, pisos: Piso[], radio: number) {
  let cerca = 0, plazas = 0, habitaciones = 0;
  for (const p of pisos) {
    if (distanciaM(h.lat, h.lon, p[0], p[1]) <= radio) {
      cerca++;
      plazas += p[2] ?? 0;
      habitaciones += p[9] ?? 1;
    }
  }
  const total = h.hab ?? 0;
  const libres = { anio: total * (1 - OCUPACION.hotelAnio), julio: total * (1 - OCUPACION.hotelJulio) };
  const piden: [number, number] = [habitaciones * OCUPACION.pisoBaja, habitaciones * OCUPACION.pisoAlta];
  const absorbe = (libre: number): [number, number] => [Math.min(libre, piden[0]), Math.min(libre, piden[1])];
  return {
    cerca, plazas, piden, libres,
    turistas: [plazas * OCUPACION.pisoBaja, plazas * OCUPACION.pisoAlta] as [number, number],
    absorbe: { anio: absorbe(libres.anio), julio: absorbe(libres.julio) },
  };
}
