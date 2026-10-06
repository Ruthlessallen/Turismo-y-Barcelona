"use client";

import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

import { fondoDelMapa } from "@/app/lib/fondo";
import {
  COLOR, OCUPACION, distanciaM, n,
  type BarrioHoy, type Capas, type HotelNuevo, type ColorRestaurante, type DatosMapa, type Hotel,
  type ModoAlojamiento, type Piso, type Restaurante, type TipoBarrio,
} from "@/app/lib/tiposMapa";

type Props = {
  datos: DatosMapa;
  capas: Capas;
  vista: ModoAlojamiento;
  tipoBarrio: TipoBarrio;
  colorRestaurante: ColorRestaurante;
  radio: number;
  hotelActivo: Hotel | null;
  onHotel: (hotel: Hotel) => void;
  seleccionado: string | null;
  onBarrio: (barrio: string) => void;
};

const CENTRO: L.LatLngExpression = [41.397, 2.173];
const ZOOM_CIFRAS = 14;

/** Rampas de un solo tono, claro a oscuro: el orden de la intensidad es el de la cifra. */
const NARANJA = ["#fdf0e1", "#f9d3a8", "#f3ad62", "#e8710a", "#a84a00"];
const AZUL = ["#e6eff8", "#b7d0ea", "#6f9fd0", "#1f5fa8", "#123a6b"];

/** Demanda hoy: de claro a oscuro. */
const MORADO = { sin: "#d9c9e3", media: "#a77bc0", alta: "#5b1f7a" };

/**
 * Cambio en 2028: verde gana clientes, morado los pierde, gris no cambia.
 * Verde y morado se distinguen en las tres formas de daltonismo comunes; verde y rojo no.
 */
export const CAMBIO = {
  sin: "#e3e0da", gana: "#2f7a3e", ganaPoco: "#6fae6b", igual: "#cfcac0",
  pierdePoco: "#a77bc0", pierde: "#5b1f7a",
} as const;

function colorCambio(r: Restaurante): string {
  if (!r.tur) return CAMBIO.sin;
  const m = r.mas ?? 0;
  if (m >= 50) return CAMBIO.gana;
  if (m >= 10) return CAMBIO.ganaPoco;
  if (m > -10) return CAMBIO.igual;
  if (m > -50) return CAMBIO.pierdePoco;
  return CAMBIO.pierde;
}

/** Escala de raíz: un barrio con 700 pisos no deja a todos los demás en el color más claro. */
function clase(valor: number, tope: number, colores: string[]): string {
  if (!valor || !tope) return "#f3f1ec";
  const fuerza = Math.sqrt(valor / tope);
  return colores[Math.min(Math.floor(fuerza * colores.length), colores.length - 1)];
}

const escapar = (t: string | null | undefined) =>
  (t ?? "").replace(/[&<>"']/g, (c) => "&#" + c.charCodeAt(0) + ";");

const fila = (k: string, v: string) =>
  `<div style="display:flex;justify-content:space-between;gap:12px"><span style="color:#52514e">${k}</span><b>${v}</b></div>`;

const nota = (t: string) => `<div style="color:#52514e;margin-top:3px">${t}</div>`;

const euros = (v: number) => `${n(Math.round(v))} €`;

function popupPiso(p: Piso): string {
  const [, , plazas, dorm, precioPiso, precioPlaza, banda, origen, barrio, , noches] = p;
  // Orden de magnitud: ocupación x 365 noches x precio de la noche. No es facturación real.
  const fact = precioPiso == null
    ? "—"
    : `${euros(precioPiso * (noches ?? 365 * OCUPACION.pisoBaja))} – ${euros(precioPiso * 365 * OCUPACION.pisoAlta)}`;
  return `<div style="min-width:230px"><b style="color:${COLOR.piso}">Piso turístico</b>
    <div style="color:#52514e;margin-bottom:4px">${escapar(barrio)}</div>
    ${fila("Precio de la noche del piso", precioPiso == null ? "—" : euros(precioPiso))}
    ${fila("Plazas", n(plazas))}${fila("Dormitorios", n(dorm))}
    ${fila("Banda (por plaza)", `${banda ?? "—"} · ${precioPlaza == null ? "—" : n(precioPlaza) + " €/plaza"}`)}
    ${fila("Factura al año (aprox.)", fact)}
    ${origen === "estimado" ? nota("Precio estimado, no observado.") : ""}</div>`;
}

function popupHotel(h: Hotel): string {
  return `<div style="min-width:220px"><b style="color:${COLOR.hotel}">${escapar(h.nom) || "Hotel"}</b>
    <div style="color:#52514e;margin-bottom:4px">${escapar(h.cat)} · ${escapar(h.barrio)}</div>
    ${h.titular ? fila("Titular", escapar(h.titular)) : ""}
    ${fila("Banda (por habitación)", h.banda_hab ?? "—")}
    ${fila("Habitaciones", n(h.hab))}${fila("Plazas", n(h.plazas))}
    ${h.origen === "estimado" ? nota("Precio estimado, no observado.") : ""}</div>`;
}

function popupNuevo(h: HotelNuevo): string {
  return `<div style="min-width:230px"><b style="color:${COLOR.hotel}">! ${escapar(h.nombre)}</b>
    <div style="color:#52514e;margin-bottom:4px">${escapar(h.marca)} · ${escapar(h.categoria)}</div>
    ${fila("Habitaciones", n(h.habitaciones))}${fila("Apertura", escapar(h.apertura))}
    ${nota(escapar(h.tipo))}
    ${nota(`<a href="${escapar(h.url)}" target="_blank" rel="noopener">${escapar(h.fuente)}</a>`)}</div>`;
}

function popupRestaurante(r: Restaurante): string {
  const cambio = r.mas == null ? "—" : `${r.mas > 0 ? "+" : ""}${n(r.mas)} %`;
  return `<div style="min-width:220px"><b style="color:${COLOR.restaurante}">${escapar(r.nom) || "Local"}</b>
    <div style="color:#52514e;margin-bottom:4px">${escapar(r.tipo)} · ${escapar(r.barrio)}</div>
    ${r.dir ? `<div style="margin-bottom:3px">${escapar(r.dir)}</div>` : ""}
    ${fila("Clientes hoy", `${n(r.tur)} / noche`)}
    ${fila("En 2028", `${n(r.tur28)} / noche`)}
    ${fila("Cambio", cambio)}
    </div>`;
}

export default function MapaLimpio({
  datos, capas, vista, tipoBarrio, colorRestaurante, radio, hotelActivo, onHotel,
  seleccionado, onBarrio,
}: Props) {
  const contenedor = useRef<HTMLDivElement>(null);
  const mapa = useRef<L.Map | null>(null);
  const dentro = useRef<{
    barrios: Record<string, L.Path>;
    pisos: { m: L.CircleMarker; p: Piso }[];
    restaurantes: { m: L.CircleMarker; r: Restaurante }[];
    gPisos: L.LayerGroup;
    gHoteles: L.LayerGroup;
    gRestaurantes: L.LayerGroup;
    anillo: L.Circle;
    alta: number;
  } | null>(null);

  const alClicBarrio = useRef(onBarrio);
  alClicBarrio.current = onBarrio;
  const alClicHotel = useRef(onHotel);
  alClicHotel.current = onHotel;

  const porBarrio = useRef<Record<string, BarrioHoy>>({});
  porBarrio.current = Object.fromEntries(datos.barrios.map((b) => [b.barrio, b]));

  // Montaje: el mapa y las capas se crean una vez; el resto de efectos solo las encienden.
  useEffect(() => {
    if (!contenedor.current || mapa.current) return;
    const m = L.map(contenedor.current, { center: CENTRO, zoom: 12, preferCanvas: true });
    mapa.current = m;
    fondoDelMapa(m);

    const barrios: Record<string, L.Path> = {};
    const cifras = L.layerGroup();
    L.geoJSON(datos.geo, {
      style: { weight: 1.5, color: "#6b6860", opacity: 0.85, fillColor: "#f3f1ec", fillOpacity: 0 },
      onEachFeature: (f, capa) => {
        const nombre = f.properties.barrio as string;
        barrios[nombre] = capa as L.Path;
        capa.on("click", () => alClicBarrio.current(nombre));
        const b = porBarrio.current[nombre];
        if (!b) return;
        const centro = (capa as L.Polygon).getBounds().getCenter();
        L.marker(centro, {
          // Con tantos puntos encima, la cifra es el sitio más fácil donde pulsar el barrio.
          interactive: true,
          keyboard: false,
          icon: L.divIcon({
            className: "",
            iconSize: [0, 0],
            html:
              `<div class="etq-barrio" style="transform:translate(-50%,-50%)">` +
              `<span class="p">${n(b.pisos)}</span><span class="h">${n(b.hoteles)}</span>` +
              `<span class="r">${n(b.restaurantes)}</span></div>`,
          }),
        }).on("click", () => alClicBarrio.current(nombre)).addTo(cifras);
      },
    }).addTo(m);

    // «Demanda alta»: el quintil superior de los locales que tienen algún turista a 200 m.
    const conTuristas = datos.restaurantes
      .map((r) => r.tur ?? 0).filter((t) => t > 0).sort((a, b) => a - b);
    const alta = conTuristas[Math.floor(conTuristas.length * 0.8)] ?? Infinity;

    const abrir = (e: L.LeafletMouseEvent, html: string) => {
      L.DomEvent.stopPropagation(e);
      L.popup().setLatLng(e.latlng).setContent(html).openOn(m);
    };

    const restaurantes = datos.restaurantes.map((r) => ({
      r,
      m: L.circleMarker([r.lat, r.lon], { radius: 3, weight: 0.5, color: "#fff", fillOpacity: 0.85 })
        .bindTooltip(`${r.nom ?? "Local"} · ${n(r.tur)} → ${n(r.tur28)} clientes/noche`,
          { direction: "top" })
        .on("click", (e) => abrir(e, popupRestaurante(r))),
    }));
    const pisos = datos.pisos.map((p) => ({
      p,
      m: L.circleMarker([p[0], p[1]], {
        radius: 3.5, weight: 0.6, color: "#fff", fillColor: COLOR.piso, fillOpacity: 0.9,
      }).bindTooltip(`Piso · ${p[4] == null ? "—" : n(p[4]) + " €/noche"} · ${n(p[2])} plazas`,
        { direction: "top" }).on("click", (e) => abrir(e, popupPiso(p))),
    }));
    const hoteles = datos.hoteles.map((h) =>
      L.circleMarker([h.lat, h.lon], {
        radius: 6, weight: 1, color: "#fff", fillColor: COLOR.hotel, fillOpacity: 0.95,
      }).bindTooltip(`${h.nom ?? "Hotel"} · banda ${h.banda_hab ?? "—"} · ${n(h.hab)} hab.`,
        { direction: "top" })
        .on("click", (e) => { abrir(e, popupHotel(h)); alClicHotel.current(h); }));

    // Hoteles anunciados: el mismo azul, con una exclamación para distinguirlos de los abiertos.
    const nuevos = datos.nuevos.filter((h) => h.lat != null && h.lon != null).map((h) =>
      L.marker([h.lat as number, h.lon as number], {
        icon: L.divIcon({
          className: "",
          iconSize: [22, 22],
          html: `<div class="hotel-nuevo">!</div>`,
        }),
      }).bindTooltip(`${h.nombre} · ${n(h.habitaciones)} hab. · ${h.apertura}`, { direction: "top" })
        .on("click", (e) => abrir(e, popupNuevo(h))));

    const anillo = L.circle([0, 0], {
      radius: 0, color: COLOR.hotel, weight: 2, dashArray: "6 4", fillColor: COLOR.hotel,
      fillOpacity: 0.07, interactive: false,
    });

    dentro.current = {
      barrios, pisos, restaurantes, anillo, alta,
      gPisos: L.layerGroup(pisos.map((x) => x.m)),
      gHoteles: L.layerGroup([...hoteles, ...nuevos]),
      gRestaurantes: L.layerGroup(restaurantes.map((x) => x.m)),
    };

    const ajustarCifras = () => {
      if (m.getZoom() >= ZOOM_CIFRAS) cifras.addTo(m);
      else cifras.remove();
    };
    m.on("zoomend", ajustarCifras);
    ajustarCifras();

    return () => {
      m.remove();
      mapa.current = null;
      dentro.current = null;
    };
  }, [datos]);

  // Qué capas se ven y cómo se colorea el barrio. Se vuelven a añadir al final los puntos de
  // alojamiento para quedar por encima de los bares: en un mismo lienzo manda el orden de alta.
  useEffect(() => {
    const m = mapa.current, d = dentro.current;
    if (!m || !d) return;
    const puntos = vista === "puntos";

    const clave = tipoBarrio === "pisos" ? "pisos" : "hoteles";
    const tope = Math.max(...datos.barrios.map((b) => b[clave]));
    const colores = tipoBarrio === "pisos" ? NARANJA : AZUL;
    for (const [nombre, capa] of Object.entries(d.barrios)) {
      const b = porBarrio.current[nombre];
      capa.setStyle(puntos
        ? { fillOpacity: 0 }
        : { fillColor: clase(b ? b[clave] : 0, tope, colores), fillOpacity: 0.78 });
    }

    d.gPisos.remove(); d.gHoteles.remove(); d.gRestaurantes.remove(); d.anillo.remove();
    if (capas.restauracion) d.gRestaurantes.addTo(m);
    if (puntos && capas.airbnb) d.gPisos.addTo(m);
    if (puntos && capas.hoteles) d.gHoteles.addTo(m);
    if (puntos && capas.hoteles && hotelActivo) d.anillo.addTo(m);
  }, [capas, vista, tipoBarrio, datos, hotelActivo]);

  // Color de los bares: demanda de hoy o cambio en 2028.
  useEffect(() => {
    const d = dentro.current;
    if (!d) return;
    for (const { m, r } of d.restaurantes) {
      m.setStyle({
        fillColor: colorRestaurante === "cambio"
          ? colorCambio(r)
          : !r.tur ? MORADO.sin : r.tur >= d.alta ? MORADO.alta : MORADO.media,
      });
    }
  }, [colorRestaurante, datos]);

  // El hotel elegido y su radio: se dibuja el círculo y se marcan los pisos de dentro.
  useEffect(() => {
    const d = dentro.current;
    if (!d) return;
    if (!hotelActivo) {
      for (const { m } of d.pisos) m.setStyle({ radius: 3.5, weight: 0.6, color: "#fff", fillOpacity: 0.9 });
      return;
    }
    d.anillo.setLatLng([hotelActivo.lat, hotelActivo.lon]);
    d.anillo.setRadius(Math.max(radio, 1));
    for (const { m, p } of d.pisos) {
      const cerca = distanciaM(hotelActivo.lat, hotelActivo.lon, p[0], p[1]) <= radio;
      m.setStyle(cerca
        ? { radius: 5, weight: 1.5, color: "#24231f", fillOpacity: 1 }
        : { radius: 3, weight: 0.4, color: "#fff", fillOpacity: 0.3 });
    }
  }, [hotelActivo, radio, datos]);

  useEffect(() => {
    const d = dentro.current;
    if (!d) return;
    for (const [nombre, capa] of Object.entries(d.barrios)) {
      const activo = nombre === seleccionado;
      capa.setStyle({ weight: activo ? 4 : 1.5, color: activo ? "#24231f" : "#6b6860" });
    }
  }, [seleccionado, vista, tipoBarrio]);

  return <div ref={contenedor} className="h-full w-full" />;
}
