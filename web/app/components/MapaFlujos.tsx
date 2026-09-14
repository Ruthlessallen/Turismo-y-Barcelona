"use client";

import { useEffect, useMemo, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

export type Flujo = { origen: string; destino: string; turistas: number; km: number };
export type Centroides = Record<string, [number, number]>;

type Props = {
  geojson: GeoJSON.FeatureCollection | null;
  flujos: Flujo[];
  centroides: Centroides;
  barrioActivo: string | null;
  onBarrio: (barrio: string | null) => void;
  minimo: number;
};

const CENTRO: L.LatLngExpression = [41.397, 2.173];
const SALE = "#cf4a30";
const LLEGA = "#2f6fb5";

/**
 * Curva entre dos barrios, en vez de una recta.
 *
 * Con 891 flechas rectas, las que van y vienen entre los mismos dos barrios se superponen y se
 * leen como una sola. Curvando siempre hacia el mismo lado, la ida y la vuelta quedan separadas.
 */
function curva(a: [number, number], b: [number, number], arqueo = 0.3, pasos = 28): [number, number][] {
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

/** Punta de flecha en el extremo de destino, dibujada en píxeles para que no crezca con el zoom. */
function puntaDeFlecha(mapa: L.Map, puntos: [number, number][], tamano: number): L.LatLngExpression[] {
  const fin = mapa.latLngToLayerPoint(puntos[puntos.length - 1]);
  const previo = mapa.latLngToLayerPoint(puntos[puntos.length - 3] ?? puntos[0]);
  const angulo = Math.atan2(fin.y - previo.y, fin.x - previo.x);
  const abertura = 0.42;
  return [
    mapa.layerPointToLatLng(fin),
    mapa.layerPointToLatLng(
      L.point(fin.x - tamano * Math.cos(angulo - abertura), fin.y - tamano * Math.sin(angulo - abertura)),
    ),
    mapa.layerPointToLatLng(
      L.point(fin.x - tamano * Math.cos(angulo + abertura), fin.y - tamano * Math.sin(angulo + abertura)),
    ),
  ];
}

export default function MapaFlujos({
  geojson,
  flujos,
  centroides,
  barrioActivo,
  onBarrio,
  minimo,
}: Props) {
  const contenedor = useRef<HTMLDivElement>(null);
  const mapa = useRef<L.Map | null>(null);
  const capaBarrios = useRef<L.GeoJSON | null>(null);
  const capaFlechas = useRef<L.LayerGroup | null>(null);

  const visibles = useMemo(() => {
    const porVolumen = flujos.filter((f) => f.turistas >= minimo);
    if (!barrioActivo) return porVolumen;
    return porVolumen.filter((f) => f.origen === barrioActivo || f.destino === barrioActivo);
  }, [flujos, barrioActivo, minimo]);

  const maximo = useMemo(
    () => Math.max(...flujos.map((f) => f.turistas), 1),
    [flujos],
  );

  useEffect(() => {
    if (!contenedor.current || mapa.current) return;
    mapa.current = L.map(contenedor.current, { zoomControl: false }).setView(CENTRO, 13);
    L.control.zoom({ position: "bottomright" }).addTo(mapa.current);
    L.tileLayer("https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png", {
      attribution: "&copy; OpenStreetMap &copy; CARTO",
      maxZoom: 19,
    }).addTo(mapa.current);
    capaFlechas.current = L.layerGroup().addTo(mapa.current);
    return () => {
      mapa.current?.remove();
      mapa.current = null;
    };
  }, []);

  // Los barrios van debajo, en gris: aquí el protagonista es la flecha, no el relleno.
  useEffect(() => {
    if (!mapa.current || !geojson) return;
    capaBarrios.current?.remove();
    capaBarrios.current = L.geoJSON(geojson, {
      style: (feature) => {
        const nombre = feature?.properties?.barrio as string;
        const activo = barrioActivo === nombre;
        return {
          fillColor: activo ? "#ffe9c9" : "#ffffff",
          fillOpacity: activo ? 0.9 : 0.55,
          color: activo ? "#24231f" : "#d8d5cf",
          weight: activo ? 2 : 0.8,
        };
      },
      onEachFeature: (feature, layer) => {
        const nombre = feature.properties?.barrio as string;
        layer.bindTooltip(nombre, { sticky: true });
        layer.on("click", () => onBarrio(barrioActivo === nombre ? null : nombre));
      },
    }).addTo(mapa.current);
    capaBarrios.current.bringToBack();
  }, [geojson, barrioActivo, onBarrio]);

  useEffect(() => {
    const m = mapa.current;
    const capa = capaFlechas.current;
    if (!m || !capa) return;

    const pintar = () => {
      capa.clearLayers();
      // Todas las flechas de un barrio salen del mismo punto, así que con un arqueo único se
      // solapan cerca del centroide y diez parecen dos. Se abanican: cada una se comba un poco
      // distinto según su posición en la lista.
      const ordenadas = [...visibles].sort((x, y) => y.turistas - x.turistas);

      ordenadas.forEach((f, i) => {
        const a = centroides[f.origen];
        const b = centroides[f.destino];
        if (!a || !b) return;

        // Cuando hay un barrio seleccionado, el color dice si el turista sale de él o llega a él.
        const color = !barrioActivo ? "#8a8783" : f.origen === barrioActivo ? SALE : LLEGA;
        const grosor = 1 + (f.turistas / maximo) * 7;
        const arqueo = barrioActivo ? 0.16 + (i % 5) * 0.12 : 0.3;
        const puntos = curva(a, b, arqueo);

        const linea = L.polyline(puntos, {
          color,
          weight: grosor,
          opacity: barrioActivo ? 0.85 : 0.35,
          lineCap: "round",
        });
        linea.bindTooltip(
          `<b>${f.turistas.toLocaleString("es")} turistas</b><br>${f.origen} → ${f.destino}<br>` +
            `${f.km} km de media`,
          { sticky: true },
        );
        capa.addLayer(linea);
        capa.addLayer(
          L.polygon(puntaDeFlecha(m, puntos, 5 + grosor), {
            color,
            fillColor: color,
            fillOpacity: 0.9,
            weight: 0,
          }),
        );
      });
    };

    pintar();
    // Las puntas se calculan en píxeles, así que hay que rehacerlas cuando cambia el zoom.
    m.on("zoomend", pintar);
    return () => {
      m.off("zoomend", pintar);
    };
  }, [visibles, centroides, barrioActivo, maximo]);

  return <div ref={contenedor} className="h-full w-full" />;
}
