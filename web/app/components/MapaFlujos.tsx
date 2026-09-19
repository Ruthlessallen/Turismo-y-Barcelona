"use client";

import { useEffect, useMemo, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

import { dibujarFlechas, type Centroides, type Flujo } from "@/app/lib/flechas";
import { fondoDelMapa } from "@/app/lib/fondo";

export type { Centroides, Flujo };

type Props = {
  geojson: GeoJSON.FeatureCollection | null;
  flujos: Flujo[];
  centroides: Centroides;
  barrioActivo: string | null;
  onBarrio: (barrio: string | null) => void;
  minimo: number;
};

const CENTRO: L.LatLngExpression = [41.397, 2.173];

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

  const maximo = useMemo(() => Math.max(...flujos.map((f) => f.turistas), 1), [flujos]);

  useEffect(() => {
    if (!contenedor.current || mapa.current) return;
    mapa.current = L.map(contenedor.current, { zoomControl: false }).setView(CENTRO, 13);
    L.control.zoom({ position: "bottomright" }).addTo(mapa.current);
    fondoDelMapa(mapa.current);
    capaFlechas.current = L.layerGroup().addTo(mapa.current);
    return () => {
      mapa.current?.remove();
      mapa.current = null;
    };
  }, []);

  // Los barrios van debajo, en blanco: aquí el protagonista es la flecha, no el relleno.
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

    const pintar = () =>
      dibujarFlechas(m, capa, { flujos: visibles, centroides, barrioActivo, maximo });

    pintar();
    // Las puntas se calculan en píxeles, así que hay que rehacerlas cuando cambia el zoom.
    m.on("zoomend", pintar);
    return () => {
      m.off("zoomend", pintar);
    };
  }, [visibles, centroides, barrioActivo, maximo]);

  return <div ref={contenedor} className="h-full w-full" />;
}
