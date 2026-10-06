"use client";

import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

import { fondoDelMapa } from "@/app/lib/fondo";
import { GRUPOS_PEUAT, grupoPeuat } from "@/app/lib/peuat";
import { clase, type HotelesBarrio } from "@/app/lib/hotelesMapa";
import { n } from "@/app/lib/tiposMapa";

type Props = {
  barrios: GeoJSON.FeatureCollection;
  peuat: GeoJSON.FeatureCollection;
  datos: HotelesBarrio[];
  verPeuat: boolean;
};

const ZOOM_CIFRAS = 13;

export default function MapaHoteles({ barrios, peuat, datos, verPeuat }: Props) {
  const contenedor = useRef<HTMLDivElement>(null);
  const capas = useRef<{ mapa: L.Map; peuat: L.GeoJSON } | null>(null);

  useEffect(() => {
    if (!contenedor.current) return;
    const mapa = L.map(contenedor.current, { zoomControl: true, preferCanvas: true, scrollWheelZoom: false });
    fondoDelMapa(mapa);
    const porBarrio = Object.fromEntries(datos.map((d) => [d.barrio, d]));

    const cifras = L.layerGroup();
    const capaBarrios = L.geoJSON(barrios, {
      style: (f) => {
        const d = porBarrio[f?.properties.barrio as string];
        return { weight: 1, color: "#6b6860", opacity: 0.8, fillColor: clase(d?.mas_pct ?? null), fillOpacity: 0.8 };
      },
      onEachFeature: (f, capa) => {
        const d = porBarrio[f.properties.barrio as string];
        capa.bindTooltip(
          `<b>${f.properties.barrio}</b><br>` + (d
            ? `${n(d.hoteles)} hoteles · ${n(d.habitaciones)} habitaciones<br>` +
              (d.mas_pct == null ? "sin dato" : `+${n(Math.round(d.mas_pct))} % turistas en 2028`)
            : "sin hoteles"),
          { sticky: true });
        if (!d) return;
        const centro = (capa as L.Polygon).getBounds().getCenter();
        L.marker(centro, {
          interactive: false,
          icon: L.divIcon({
            className: "", iconSize: [0, 0],
            html: `<div class="etq-barrio" style="transform:translate(-50%,-50%)">` +
              `<span class="h">${n(d.hoteles)}</span>` +
              `<span class="r" style="background:#24231f">${d.mas_pct == null ? "—" : "+" + n(Math.round(d.mas_pct)) + "%"}</span></div>`,
          }),
        }).addTo(cifras);
      },
    }).addTo(mapa);
    mapa.fitBounds(capaBarrios.getBounds());

    const capaPeuat = L.geoJSON(peuat, {
      style: (f) => {
        const g = GRUPOS_PEUAT.find((x) => x.id === grupoPeuat(f?.properties.zona as string))!;
        return { weight: 2.5, color: g.color, dashArray: g.dash, fill: false, opacity: 0.95 };
      },
      onEachFeature: (f, capa) => capa.bindTooltip(`PEUAT · ${f.properties.zona}`, { sticky: true }),
      interactive: false,
    });

    const ajustar = () => (mapa.getZoom() >= ZOOM_CIFRAS ? cifras.addTo(mapa) : cifras.remove());
    mapa.on("zoomend", ajustar);
    ajustar();
    capas.current = { mapa, peuat: capaPeuat };
    return () => { mapa.remove(); capas.current = null; };
  }, [barrios, peuat, datos]);

  useEffect(() => {
    const c = capas.current;
    if (!c) return;
    if (verPeuat) c.peuat.addTo(c.mapa);
    else c.peuat.remove();
  }, [verPeuat, barrios, peuat, datos]);

  return <div ref={contenedor} className="h-full w-full" />;
}
