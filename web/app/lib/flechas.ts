import L from "leaflet";

export type Flujo = { origen: string; destino: string; turistas: number; km: number };
export type Centroides = Record<string, [number, number]>;

export const SALE = "#cf4a30";
export const LLEGA = "#2f6fb5";
export const NEUTRA = "#8a8783";

/**
 * Curva entre dos barrios, en vez de una recta.
 *
 * Con flechas rectas, la ida y la vuelta entre los mismos dos barrios se superponen y se leen como
 * una sola. Curvando siempre hacia el mismo lado quedan separadas.
 */
export function curva(
  a: [number, number],
  b: [number, number],
  arqueo = 0.3,
  pasos = 28,
): [number, number][] {
  const [lat1, lon1] = a;
  const [lat2, lon2] = b;
  // Punto de control desplazado perpendicularmente al segmento: `arqueo` es cuánto se comba.
  const mx = (lat1 + lat2) / 2 + (lon2 - lon1) * arqueo;
  const my = (lon1 + lon2) / 2 - (lat2 - lat1) * arqueo;

  return Array.from({ length: pasos + 1 }, (_, i) => {
    const t = i / pasos;
    const u = 1 - t;
    return [
      u * u * lat1 + 2 * u * t * mx + t * t * lat2,
      u * u * lon1 + 2 * u * t * my + t * t * lon2,
    ] as [number, number];
  });
}

/** Punta en el extremo de destino, calculada en píxeles para que no crezca con el zoom. */
export function puntaDeFlecha(
  mapa: L.Map,
  puntos: [number, number][],
  tamano: number,
): L.LatLngExpression[] {
  const fin = mapa.latLngToLayerPoint(puntos[puntos.length - 1]);
  const previo = mapa.latLngToLayerPoint(puntos[puntos.length - 3] ?? puntos[0]);
  const angulo = Math.atan2(fin.y - previo.y, fin.x - previo.x);
  const abertura = 0.42;
  return [
    mapa.layerPointToLatLng(fin),
    mapa.layerPointToLatLng(
      L.point(
        fin.x - tamano * Math.cos(angulo - abertura),
        fin.y - tamano * Math.sin(angulo - abertura),
      ),
    ),
    mapa.layerPointToLatLng(
      L.point(
        fin.x - tamano * Math.cos(angulo + abertura),
        fin.y - tamano * Math.sin(angulo + abertura),
      ),
    ),
  ];
}

type Opciones = {
  flujos: Flujo[];
  centroides: Centroides;
  barrioActivo: string | null;
  maximo: number;
  /** Opacidad de la línea. Sobre coropletas hace falta más que sobre el mapa en blanco. */
  opacidad?: number;
};

/**
 * Pinta las flechas en `capa`. La usan los dos mapas, para que no haya dos versiones del mismo
 * dibujo que se separen con el tiempo.
 */
export function dibujarFlechas(mapa: L.Map, capa: L.LayerGroup, opciones: Opciones): void {
  const { flujos, centroides, barrioActivo, maximo, opacidad } = opciones;
  capa.clearLayers();

  // Todas las flechas de un barrio salen del mismo punto, así que con un arqueo único se solapan
  // cerca del centroide y diez parecen dos. Se abanican según su posición en la lista.
  const ordenadas = [...flujos].sort((x, y) => y.turistas - x.turistas);

  ordenadas.forEach((f, i) => {
    const a = centroides[f.origen];
    const b = centroides[f.destino];
    if (!a || !b) return;

    const color = !barrioActivo ? NEUTRA : f.origen === barrioActivo ? SALE : LLEGA;
    const grosor = 1 + (f.turistas / maximo) * 7;
    const arqueo = barrioActivo ? 0.16 + (i % 5) * 0.12 : 0.3;
    const puntos = curva(a, b, arqueo);

    const linea = L.polyline(puntos, {
      color,
      weight: grosor,
      opacity: opacidad ?? (barrioActivo ? 0.85 : 0.35),
      lineCap: "round",
    });
    linea.bindTooltip(
      `<b>${f.turistas.toLocaleString("es")} turistas</b><br>${f.origen} → ${f.destino}<br>` +
        `${f.km} km de media`,
      { sticky: true },
    );
    capa.addLayer(linea);
    capa.addLayer(
      L.polygon(puntaDeFlecha(mapa, puntos, 5 + grosor), {
        color,
        fillColor: color,
        fillOpacity: 0.9,
        weight: 0,
      }),
    );
  });
}
