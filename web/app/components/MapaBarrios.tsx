"use client";

import { useEffect, useMemo, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

import { dibujarFlechas, type Centroides, type Flujo } from "@/app/lib/flechas";
import type { BarrioRestauracion, BarrioSustitucion } from "@/app/lib/tipos";

/** Qué pinta el color del barrio. Las dos últimas leen de `restauracion`, no de `datos`. */
export type Medida = "saldo" | "sin_sitio" | "se_quedan" | "locales" | "cambio";

const MEDIDAS_RESTAURACION: Medida[] = ["locales", "cambio"];

type Props = {
  geojson: GeoJSON.FeatureCollection | null;
  datos: Record<string, BarrioSustitucion>;
  restauracion?: Record<string, BarrioRestauracion>;
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

/** Restauración: verde, para que nunca se confunda con el azul de «gana turistas». */
const VERDE = ["#e8f0e4", "#c3ddb9", "#93c088", "#5d9e5a", "#2f7a3e"];

/**
 * Divergente del cambio de comensales: verde gana, morado pierde.
 * Verde y morado se distinguen en las tres formas de daltonismo comunes; verde y rojo no.
 */
const PIERDE_COMENSALES = ["#e6dcea", "#c3a7cf", "#9a6fae", "#6f3f8a"];
const GANA_COMENSALES = ["#d8ead2", "#a8cf9c", "#6fae6b", "#2f7a3e"];

function colorPara(valor: number, medida: Medida, tope: number): string {
  if (!valor) return NEUTRO;
  if (medida === "saldo" || medida === "cambio") {
    const negativa = medida === "saldo" ? PIERDE : PIERDE_COMENSALES;
    const positiva = medida === "saldo" ? GANA : GANA_COMENSALES;
    const escala = valor < 0 ? negativa : positiva;
    const fuerza = Math.min(Math.abs(valor) / tope, 1);
    return escala[Math.min(Math.floor(fuerza * escala.length), escala.length - 1)];
  }
  const rampa = medida === "locales" ? VERDE : SECUENCIAL;
  const fuerza = Math.min(valor / tope, 1);
  return rampa[Math.min(Math.floor(fuerza * rampa.length), rampa.length - 1)];
}

const n = (v: number) => Math.round(v).toLocaleString("es");

function textoTooltip(
  nombre: string,
  medida: Medida,
  d?: BarrioSustitucion,
  r?: BarrioRestauracion,
): string {
  if (MEDIDAS_RESTAURACION.includes(medida)) {
    if (!r) return `<b>${nombre}</b><br>sin locales de restauración`;
    const signo = r.cambio > 0 ? "+" : "";
    return (
      `<b>${nombre}</b><br>${n(r.locales)} bares y restaurantes<br>` +
      `hoy duermen cerca ${n(r.hoy)} de estos turistas<br>` +
      `en 2028, ${n(r.en_2028)} (${signo}${n(r.cambio)})`
    );
  }
  if (!d) return `<b>${nombre}</b><br>sin viviendas turísticas`;
  return (
    `<b>${nombre}</b><br>${n(d.salen)} turistas se quedan sin piso<br>` +
    `${n(d.se_quedan)} encuentran hotel aquí<br>` +
    `${n(d.sin_sitio)} sin sitio en la ciudad`
  );
}

export default function MapaBarrios({
  geojson,
  datos,
  restauracion = {},
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

  // De qué tabla sale el número que se pinta. Restauración cubre 73 barrios y sustitución 64:
  // son universos distintos y por eso no pueden compartir el mismo registro.
  const valorDe = useMemo(() => {
    const deRestauracion = MEDIDAS_RESTAURACION.includes(medida);
    return (barrio: string): number | null => {
      const fila = deRestauracion ? restauracion[barrio] : datos[barrio];
      if (!fila) return null;
      return (fila as Record<string, unknown>)[medida] as number;
    };
  }, [datos, restauracion, medida]);

  // El tope se recalcula con la medida: si no, al cambiar de columna el color deja de decir nada.
  const tope = useMemo(() => {
    const fuente = MEDIDAS_RESTAURACION.includes(medida) ? restauracion : datos;
    const valores = Object.values(fuente).map((d) =>
      Math.abs(((d as Record<string, unknown>)[medida] as number) ?? 0),
    );
    return Math.max(...valores, 1);
  }, [datos, restauracion, medida]);

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
        const valor = valorDe(nombre);
        const activo = barrioActivo === nombre;
        return {
          fillColor: valor === null ? "#f5f4f1" : colorPara(valor, medida, tope),
          fillOpacity: valor === null ? 0.35 : 0.85,
          color: activo ? "#24231f" : "#ffffff",
          weight: activo ? 2.5 : 1,
        };
      },
      onEachFeature: (feature, layer) => {
        const nombre = feature.properties?.barrio as string;
        layer.bindTooltip(textoTooltip(nombre, medida, datos[nombre], restauracion[nombre]), {
          sticky: true,
        });
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
  }, [geojson, datos, restauracion, valorDe, medida, tope, barrioActivo, onBarrio]);

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
