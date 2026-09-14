"use client";

import { useEffect, useMemo, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

import { dibujarFlechas, type Centroides, type Flujo } from "@/app/lib/flechas";
import type { BarrioSustitucion } from "@/app/lib/tipos";

/** Qué pinta el color del barrio. */
export type Medida = "saldo" | "sin_sitio" | "se_quedan";

type Props = {
  geojson: GeoJSON.FeatureCollection | null;
  datos: Record<string, BarrioSustitucion>;
  medida: Medida;
  barrioActivo: string | null;
  onBarrio: (barrio: string | null) => void;
  /** Flechas encima de las coropletas. Vacío si la capa está apagada. */
  flujos?: Flujo[];
  centroides?: Centroides;
};

const CENTRO: L.LatLngExpression = [41.397, 2.173];

/**
 * Escala divergente para el saldo: el barrio gana o pierde turistas, y el cero importa.
 * Nunca un arcoíris — dos tonos y un gris en medio, que es lo único que deja ver el signo.
 */
const PIERDE = ["#fde8e4", "#f7b7a8", "#ea7a63", "#cf4a30"];
const GANA = ["#e2ecf7", "#a8c8e8", "#6fa2d4", "#2f6fb5"];
const NEUTRO = "#eeece7";

/** Secuencial de un solo tono para magnitudes sin signo. */
const SECUENCIAL = ["#f4efe6", "#e5d5b8", "#d4b184", "#bd8850", "#9c5f27"];

function colorPara(valor: number, medida: Medida, tope: number): string {
  if (!valor) return NEUTRO;
  if (medida === "saldo") {
    const escala = valor < 0 ? PIERDE : GANA;
    const fuerza = Math.min(Math.abs(valor) / tope, 1);
    return escala[Math.min(Math.floor(fuerza * escala.length), escala.length - 1)];
  }
  const fuerza = Math.min(valor / tope, 1);
  return SECUENCIAL[Math.min(Math.floor(fuerza * SECUENCIAL.length), SECUENCIAL.length - 1)];
}

export default function MapaBarrios({
  geojson,
  datos,
  medida,
  barrioActivo,
  onBarrio,
  flujos = [],
  centroides = {},
}: Props) {
  const contenedor = useRef<HTMLDivElement>(null);
  const mapa = useRef<L.Map | null>(null);
  const capa = useRef<L.GeoJSON | null>(null);
  const capaFlechas = useRef<L.LayerGroup | null>(null);

  // El tope se recalcula con la medida: si no, al cambiar de columna el color deja de decir nada.
  const tope = useMemo(() => {
    const valores = Object.values(datos).map((d) => Math.abs(d[medida] ?? 0));
    return Math.max(...valores, 1);
  }, [datos, medida]);

  const maximoFlujo = useMemo(() => Math.max(...flujos.map((f) => f.turistas), 1), [flujos]);

  useEffect(() => {
    if (!contenedor.current || mapa.current) return;
    mapa.current = L.map(contenedor.current, { zoomControl: false }).setView(CENTRO, 13);
    L.control.zoom({ position: "bottomright" }).addTo(mapa.current);
    // Fondo sin etiquetas comerciales: el mapa habla de barrios, no de negocios.
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

  useEffect(() => {
    if (!mapa.current || !geojson) return;
    capa.current?.remove();

    capa.current = L.geoJSON(geojson, {
      style: (feature) => {
        const nombre = feature?.properties?.barrio as string;
        const d = datos[nombre];
        const activo = barrioActivo === nombre;
        return {
          fillColor: d ? colorPara(d[medida] ?? 0, medida, tope) : "#f5f4f1",
          fillOpacity: d ? 0.85 : 0.35,
          color: activo ? "#24231f" : "#ffffff",
          weight: activo ? 2.5 : 1,
        };
      },
      onEachFeature: (feature, layer) => {
        const nombre = feature.properties?.barrio as string;
        const d = datos[nombre];
        layer.bindTooltip(
          d
            ? `<b>${nombre}</b><br>${d.salen.toLocaleString("es")} turistas se quedan sin piso<br>` +
                `${d.se_quedan.toLocaleString("es")} encuentran hotel aquí<br>` +
                `${d.sin_sitio.toLocaleString("es")} sin sitio en la ciudad`
            : `<b>${nombre}</b><br>sin viviendas turísticas`,
          { sticky: true },
        );
        layer.on({
          click: () => onBarrio(barrioActivo === nombre ? null : nombre),
          mouseover: (e) => (e.target as L.Path).setStyle({ weight: 2.5, color: "#24231f" }),
          mouseout: (e) =>
            (e.target as L.Path).setStyle(
              barrioActivo === nombre
                ? { weight: 2.5, color: "#24231f" }
                : { weight: 1, color: "#ffffff" },
            ),
        });
      },
    }).addTo(mapa.current);
    // Las coropletas se acaban de añadir, así que taparían las flechas si no se mandan al fondo.
    capa.current.bringToBack();
  }, [geojson, datos, medida, tope, barrioActivo, onBarrio]);

  useEffect(() => {
    const m = mapa.current;
    const cf = capaFlechas.current;
    if (!m || !cf) return;

    // Sobre las coropletas hace falta más opacidad que sobre el mapa en blanco de `/flujos`:
    // con 0,35 la flecha se pierde dentro del relleno del barrio.
    const pintar = () =>
      dibujarFlechas(m, cf, {
        flujos,
        centroides,
        barrioActivo,
        maximo: maximoFlujo,
        opacidad: barrioActivo ? 0.95 : 0.6,
      });

    pintar();
    m.on("zoomend", pintar);
    return () => {
      m.off("zoomend", pintar);
    };
  }, [flujos, centroides, barrioActivo, maximoFlujo]);

  return <div ref={contenedor} className="h-full w-full" />;
}
