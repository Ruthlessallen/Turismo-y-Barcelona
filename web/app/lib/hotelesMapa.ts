/** Lo que comparten el mapa de hoteles y su página. Aparte del mapa porque este módulo no toca Leaflet. */

export type HotelesBarrio = {
  barrio: string; hoteles: number; habitaciones: number; hoy: number; nuevos: number; mas_pct: number | null;
};

const AZUL = ["#e6eff8", "#b7d0ea", "#6f9fd0", "#1f5fa8", "#123a6b"];
const CORTES = [5, 10, 15, 25];

/** El color según cuántos turistas más tendrán los hoteles del barrio en 2028. Sin hoteles, gris. */
export const clase = (mas: number | null) =>
  mas == null ? "#f3f1ec" : AZUL[CORTES.filter((c) => mas >= c).length];

export const LEYENDA = [
  { color: AZUL[0], texto: "menos de 5 %" }, { color: AZUL[1], texto: "5–10 %" },
  { color: AZUL[2], texto: "10–15 %" }, { color: AZUL[3], texto: "15–25 %" },
  { color: AZUL[4], texto: "25 % o más" }, { color: "#f3f1ec", texto: "sin hoteles" },
];
