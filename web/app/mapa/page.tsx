"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import {
  COLOR, analisisHotel, dec, serieHotel, n,
  type BarrioHoy, type Capas, type ColorRestaurante, type DatosMapa, type Foco, type Hotel,
  type ModoAlojamiento, type TipoBarrio,
} from "@/app/lib/tiposMapa";

// Leaflet toca `window` al cargarse: sin esto el render del servidor revienta.
const MapaLimpio = dynamic(() => import("@/app/components/MapaLimpio"), {
  ssr: false,
  loading: () => <div className="h-full w-full bg-[#f5f4f1]" />,
});

const base = "/data/mapa";
const cargar = <T,>(ruta: string): Promise<T> => fetch(ruta).then((r) => r.json());

/** Verde gana clientes, morado los pierde: se distinguen en las tres formas de daltonismo. */
const LEYENDA_CAMBIO: [string, string][] = [
  ["#2f7a3e", "Gana 50 % o más"], ["#6fae6b", "Gana del 10 al 50 %"],
  ["#cfcac0", "Casi igual (±10 %)"], ["#a77bc0", "Pierde del 10 al 50 %"],
  ["#5b1f7a", "Pierde 50 % o más"], ["#e3e0da", "Sin turistas cerca hoy"],
];

export default function Pagina() {
  const [datos, setDatos] = useState<DatosMapa | null>(null);
  const [capas, setCapas] = useState<Capas>({ airbnb: true, hoteles: true, restauracion: false });
  const [vista, setVista] = useState<ModoAlojamiento>("puntos");
  const [tipo, setTipo] = useState<TipoBarrio>("pisos");
  const [colorRest, setColorRest] = useState<ColorRestaurante>("hoy");
  const [radio, setRadio] = useState(300);
  const [foco, setFoco] = useState<Foco>(null);

  useEffect(() => {
    Promise.all([
      cargar<GeoJSON.FeatureCollection>("/data/geo/barrios.geojson"),
      cargar<DatosMapa["barrios"]>(`${base}/barrios_hoy.json`),
      cargar<DatosMapa["pisos"]>(`${base}/puntos_pisos.json`),
      cargar<DatosMapa["hoteles"]>(`${base}/puntos_hoteles.json`),
      cargar<DatosMapa["restaurantes"]>(`${base}/puntos_restaurantes.json`),
      cargar<{ nuevos: DatosMapa["nuevos"] }>(`${base}/hoteles_pagina.json`),
      cargar<DatosMapa["param"]>(`${base}/parametros.json`),
    ]).then(([geo, barrios, pisos, hoteles, restaurantes, pagina, param]) =>
      setDatos({ geo, barrios, pisos, hoteles, restaurantes, nuevos: pagina.nuevos, param }));
  }, []);

  const alternar = (capa: keyof Capas) => {
    setCapas((c) => ({ ...c, [capa]: !c[capa] }));
    if (capa === "hoteles") setFoco((f) => (f?.tipo === "hotel" ? null : f));
  };

  const hotelActivo = foco?.tipo === "hotel" && capas.hoteles ? foco.hotel : null;
  const barrio = foco?.tipo === "barrio" ? foco.nombre : null;
  const ficha = useMemo(
    () => datos?.barrios.find((b) => b.barrio === barrio) ?? null, [datos, barrio]);

  if (!datos) return <main className="h-full bg-[#f5f4f1]" />;

  return (
    <main className="relative h-full text-[#24231f]">
      <MapaLimpio datos={datos} capas={capas} vista={vista} tipoBarrio={tipo}
        colorRestaurante={colorRest} radio={radio} hotelActivo={hotelActivo}
        onHotel={(hotel) => setFoco({ tipo: "hotel", hotel })}
        seleccionado={barrio}
        onBarrio={(nombre) => setFoco({ tipo: "barrio", nombre })} />

      <div className="absolute top-3 left-3 z-[1000] max-h-[calc(100%-1.5rem)] w-[248px] overflow-y-auto rounded border border-[#e3e0da] bg-white/95 p-3 text-[12px] shadow-sm">
        <ResumenPisos pisos={datos.pisos.length} barrios={datos.barrios} />
        <Titulo className="mt-3">Capas</Titulo>
        <div className="flex gap-1">
          <Capa activa={capas.airbnb} color={COLOR.piso} onClick={() => alternar("airbnb")}>Airbnb</Capa>
          <Capa activa={capas.hoteles} color={COLOR.hotel} onClick={() => alternar("hoteles")}>Hoteles</Capa>
          <Capa activa={capas.restauracion} color={COLOR.restaurante}
            onClick={() => alternar("restauracion")}>Restauración</Capa>
        </div>

        {(capas.airbnb || capas.hoteles) && (
          <>
            <Titulo className="mt-3">Alojamiento</Titulo>
            <Segmentos valor={vista} onCambio={setVista}
              opciones={[["puntos", "Puntos"], ["barrios", "Por barrios"]]} />
            {vista === "barrios" && (
              <div className="mt-1.5">
                <Segmentos valor={tipo} onCambio={setTipo}
                  opciones={[["pisos", "Pisos (naranja)"], ["hoteles", "Hoteles (azul)"]]} />
                <LeyendaBarrios tipo={tipo} barrios={datos.barrios} />
              </div>
            )}
          </>
        )}

        {capas.hoteles && vista === "puntos" && (
          <>
            <Titulo className="mt-3">Radio de cada hotel</Titulo>
            <label className="block">
              <span className="flex justify-between">
                <span>¿Cuántos pisos hay a…?</span><b className="tabular-nums">{radio} m</b>
              </span>
              <input type="range" min={0} max={500} step={50} value={radio}
                onChange={(e) => setRadio(Number(e.target.value))}
                className="mt-1 w-full accent-[#1f5fa8]" />
            </label>
            <p className="mt-1 text-[11px] text-[#52514e]">Pulsa un hotel.</p>
          </>
        )}

        {capas.restauracion && (
          <>
            <Titulo className="mt-3">Color de los bares</Titulo>
            <Segmentos valor={colorRest} onCambio={setColorRest}
              opciones={[["hoy", "Demanda hoy"], ["cambio", "Cambio en 2028"]]} />
            <ul className="mt-2 space-y-1">
              {colorRest === "hoy" ? (
                <>
                  <Leyenda color="#5b1f7a" texto="Demanda alta (20 % con más turistas cerca)" />
                  <Leyenda color="#a77bc0" texto="Demanda media" />
                  <Leyenda color="#d9c9e3" texto="Sin turistas a 200 m" />
                </>
              ) : LEYENDA_CAMBIO.map(([c, t]) => <Leyenda key={t} color={c} texto={t} />)}
            </ul>
          </>
        )}

        <p className="mt-3 text-[11px] text-[#52514e]">
          Cifras por barrio: <span style={{ color: "#c25a00" }}>pisos</span> ·{" "}
          <span style={{ color: COLOR.hotel }}>hoteles</span> ·{" "}
          <span style={{ color: COLOR.restaurante }}>locales</span>
        </p>
      </div>

      {hotelActivo ? (
        <PanelHotel hotel={hotelActivo} datos={datos} radio={radio} onCerrar={() => setFoco(null)} />
      ) : ficha ? (
        <PanelBarrio b={ficha} param={datos.param} hotelesBarrio={datos.hoteles.filter((h) => h.barrio === ficha.barrio)}
          onCerrar={() => setFoco(null)} />
      ) : null}
    </main>
  );
}

/** Lo primero que se ve: cuántos pisos turísticos hay y cuántos turistas alojan por noche. */
function ResumenPisos({ pisos, barrios }: { pisos: number; barrios: BarrioHoy[] }) {
  const bajo = barrios.reduce((s, b) => s + b.turistas_pisos[0], 0);
  const alto = barrios.reduce((s, b) => s + b.turistas_pisos[1], 0);
  return (
    <div className="mb-1 grid grid-cols-2 gap-2 text-center">
      <div className="rounded border-t-[3px] bg-[#fbe3cc] px-1 py-2" style={{ borderColor: COLOR.piso }}>
        <p className="text-[24px] leading-none font-semibold tabular-nums" style={{ color: "#a84a00" }}>{n(pisos)}</p>
        <p className="mt-1 text-[11px] leading-tight">pisos turísticos</p>
      </div>
      <div className="rounded border-t-[3px] bg-[#fbe3cc] px-1 py-2" style={{ borderColor: COLOR.piso }}>
        <p className="text-[24px] leading-none font-semibold tabular-nums" style={{ color: "#a84a00" }}>{rango(bajo, alto)}</p>
        <p className="mt-1 text-[11px] leading-tight">turistas por noche en Airbnb</p>
      </div>
    </div>
  );
}

function Titulo({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <p className={`mb-1.5 text-[10px] font-semibold tracking-wider text-[#52514e] uppercase ${className}`}>
      {children}
    </p>
  );
}

function Capa({ activa, color, onClick, children }: {
  activa: boolean; color: string; onClick: () => void; children: React.ReactNode;
}) {
  return (
    <button type="button" aria-pressed={activa} onClick={onClick}
      className="flex-1 rounded border px-1 py-1.5 font-medium"
      style={activa
        ? { background: color, borderColor: color, color: "#fff" }
        : { background: "#fff", borderColor: "#d8d5cd", color: "#52514e" }}>
      {children}
    </button>
  );
}

function Segmentos<T extends string>({ valor, onCambio, opciones }: {
  valor: T; onCambio: (v: T) => void; opciones: [T, string][];
}) {
  return (
    <div className="flex overflow-hidden rounded border border-[#d8d5cd]">
      {opciones.map(([id, texto]) => (
        <button key={id} type="button" aria-pressed={valor === id} onClick={() => onCambio(id)}
          className={`flex-1 px-2 py-1 ${valor === id ? "bg-[#24231f] text-white" : "bg-white"}`}>
          {texto}
        </button>
      ))}
    </div>
  );
}

const RAMPA = {
  pisos: ["#fdf0e1", "#f9d3a8", "#f3ad62", "#e8710a", "#a84a00"],
  hoteles: ["#e6eff8", "#b7d0ea", "#6f9fd0", "#1f5fa8", "#123a6b"],
};

/** Qué significa el color del barrio: el mismo corte que `clase()` del mapa (escala de raíz). */
function LeyendaBarrios({ tipo, barrios }: { tipo: TipoBarrio; barrios: BarrioHoy[] }) {
  const tope = Math.max(...barrios.map((b) => b[tipo]));
  const colores = RAMPA[tipo];
  const desde = (i: number) => (i === 0 ? 1 : Math.ceil(tope * (i / colores.length) ** 2));
  return (
    <div className="mt-2">
      <p className="mb-1 text-[11px]">
        Color = {tipo === "pisos" ? "pisos turísticos" : "hoteles"} en el barrio
      </p>
      <ul className="space-y-0.5 text-[11px]">
        {colores.map((c, i) => (
          <li key={c} className="flex items-center gap-2">
            <span className="inline-block h-2.5 w-4 shrink-0 rounded-sm border border-[#d8d5cd]" style={{ background: c }} />
            {i === colores.length - 1 ? `${n(desde(i))} o más` : `${n(desde(i))} – ${n(desde(i + 1) - 1)}`}
          </li>
        ))}
        <li className="flex items-center gap-2">
          <span className="inline-block h-2.5 w-4 shrink-0 rounded-sm border border-[#d8d5cd]" style={{ background: "#f3f1ec" }} />
          ninguno
        </li>
      </ul>
    </div>
  );
}

function Leyenda({ color, texto }: { color: string; texto: string }) {
  return (
    <li className="flex items-center gap-2">
      <span className="inline-block h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: color }} />
      {texto}
    </li>
  );
}

/** «1–2», o «2» cuando los dos extremos redondean igual: «2–2» no dice nada más que «2». */
const rango = (a: number, b: number) =>
  Math.round(a) === Math.round(b) ? n(Math.round(a)) : `${n(Math.round(a))}–${n(Math.round(b))}`;

/** 222 millones, o 433 mil: lo que se lee de un vistazo. */
function dinero(v: number): string {
  if (v >= 1e6) return `${(v / 1e6).toLocaleString("es", { maximumFractionDigits: 1 })} M€`;
  return `${n(Math.round(v / 1e3))} mil €`;
}

/** Qué hay alrededor de un hotel y qué le pasa en 2028. Un año medio. */
function PanelHotel({ hotel, datos, radio, onCerrar }: {
  hotel: Hotel; datos: DatosMapa; radio: number; onCerrar: () => void;
}) {
  const a = useMemo(() => analisisHotel(hotel, datos.pisos, radio, datos.param), [hotel, datos.pisos, radio, datos.param]);
  const serie = useMemo(() => serieHotel(hotel, datos.pisos, datos.param), [hotel, datos.pisos, datos.param]);
  const total = a.total;
  const libres = Math.max(total - a.ocupadas2028, 0);
  const pct = (v: number) => (total > 0 ? Math.round((v / total) * 100) : 0);
  const piden = a.habitaciones * datos.param.ocupacion_piso[0] / 100;
  const cubre = piden > 0 ? Math.min(a.absorbe / piden, 1) * 100 : 0;

  return (
    <aside className="absolute top-3 right-3 bottom-3 z-[1000] w-[300px] max-w-[85vw] overflow-y-auto rounded border border-[#e3e0da] bg-white p-4 text-[13px] shadow-sm">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h2 className="text-[16px] leading-tight font-semibold">{hotel.nom ?? "Hotel"}</h2>
          <p className="text-[11px] text-[#52514e]">{hotel.cat} · {hotel.barrio}</p>
        </div>
        <button type="button" onClick={onCerrar} aria-label="Cerrar" className="text-[18px] leading-none text-[#52514e]">×</button>
      </div>

      <Titulo className="mt-3">Las {n(total)} habitaciones del hotel</Titulo>
      <Apilada partes={[
        { valor: a.ocupadasHoy, color: "#9dbbdc", texto: "ocupadas hoy" },
        { valor: a.ocupadas2028 - a.ocupadasHoy, color: COLOR.hotel, texto: "absorbe de Airbnb" },
        { valor: libres, color: "#e3e0da", texto: "libres en 2028" },
      ]} total={total} formato={(v) => `${n(Math.round(v))} · ${pct(v)} %`} />

      <Titulo className="mt-4">Los pisos a {radio} m piden</Titulo>
      <Apilada partes={[
        { valor: Math.min(a.absorbe, piden), color: COLOR.hotel, texto: "las absorbe este hotel" },
        { valor: Math.max(piden - a.absorbe, 0), color: COLOR.piso, texto: "no las absorbe" },
      ]} total={Math.max(piden, 0.0001)} formato={(v) => `${n(Math.round(v))} hab.`} />
      <p className="mt-1 text-[11px] text-[#52514e]">
        {n(a.cerca)} pisos · {n(a.plazas)} plazas · {n(Math.round(piden))} habitaciones por noche
        {piden > 0 ? `, cubre el ${Math.round(cubre)} %` : ""}
      </p>
      {piden > a.absorbe && (
        <p className="mt-1 text-[11px] leading-snug text-[#52514e]">
          Absorbe menos de lo que piden por dos límites: solo recibe pisos de su banda ({hotel.banda ?? "—"}; los
          de otras bandas van a otros hoteles) y no puede pasar de sus habitaciones libres (
          {n(Math.round(Math.max(total - a.ocupadasHoy, 0)))}).
        </p>
      )}

      <Titulo className="mt-4">Habitaciones absorbibles, según el radio</Titulo>
      <Lineas serie={serie} radio={radio} libres={Math.max(total - a.ocupadasHoy, 0)} param={datos.param} />
    </aside>
  );
}

/** Una barra partida en tramos, con su leyenda debajo. */
function Apilada({ partes, total, formato }: {
  partes: { valor: number; color: string; texto: string }[]; total: number; formato: (v: number) => string;
}) {
  return (
    <>
      <div className="mt-1.5 flex h-4 overflow-hidden rounded bg-[#eeece7]">
        {partes.map((p) => (
          <div key={p.texto} style={{ width: `${(p.valor / total) * 100}%`, background: p.color }} />
        ))}
      </div>
      <ul className="mt-1 space-y-0.5 text-[11px]">
        {partes.map((p) => (
          <li key={p.texto} className="flex items-center gap-1.5">
            <i className="inline-block h-2 w-2 shrink-0 rounded-sm" style={{ background: p.color }} />
            <b className="tabular-nums">{formato(p.valor)}</b>
            <span className="text-[#52514e]">{p.texto}</span>
          </li>
        ))}
      </ul>
    </>
  );
}

/** Gráfico lineal pequeño: lo que piden los pisos crece con el radio; lo que el hotel puede dar, no. */
function Lineas({ serie, radio, libres, param }: {
  param: DatosMapa["param"];
  serie: { radio: number; pisos: number; piden: number; pidenAlto: number }[]; radio: number; libres: number;
}) {
  const W = 260, H = 110, X0 = 28, Y0 = 8, ancho = W - X0 - 6, alto = H - Y0 - 18;
  const max = Math.max(...serie.map((s) => s.pidenAlto), libres, 1) * 1.1;
  const x = (r: number) => X0 + (r / 500) * ancho;
  // El cero queda 4 unidades por encima del eje: el trazo no se sale por debajo de 0.
  // Lineal o logarítmica (log10 de 1 + v: así el 0 sigue siendo 0). La logarítmica abre la parte
  // de abajo, donde hay pocas habitaciones, y comprime la de arriba.
  const [log, setLog] = useState(false);
  const f = (v: number) => (log ? Math.log10(1 + v) / Math.log10(1 + max) : v / max);
  const y = (v: number) => Y0 + alto - 4 - f(v) * (alto - 4);
  const marcas = log ? [0, 1, 10, 100, 1000].filter((v) => v <= max) : [0, 0.5, 1].map((k) => Math.round((max * k) / 1.1));
  const linea = (f: (s: (typeof serie)[number]) => number) => serie.map((s) => `${x(s.radio)},${y(f(s))}`).join(" ");
  // Entre la curva y el hueco libre del hotel: azul donde el hotel tiene sitio de sobra, naranja donde
  // lo que piden los pisos no cabe y se va a otros hoteles. Se parte en el cruce de las dos.
  const bandas: { pts: string; color: string }[] = [];
  for (let i = 0; i < serie.length - 1; i++) {
    const [r0, r1] = [serie[i].radio, serie[i + 1].radio], [c0, c1] = [serie[i].piden, serie[i + 1].piden];
    const trozos: [number, number, number, number][] = [];
    if ((c0 - libres) * (c1 - libres) < 0) {
      const t = (libres - c0) / (c1 - c0), rc = r0 + (r1 - r0) * t;
      trozos.push([r0, c0, rc, libres], [rc, libres, r1, c1]);
    } else trozos.push([r0, c0, r1, c1]);
    for (const [a0, v0, a1, v1] of trozos) {
      const sobra = (v0 + v1) / 2 > libres;
      bandas.push({
        pts: `${x(a0)},${y(v0)} ${x(a1)},${y(v1)} ${x(a1)},${y(libres)} ${x(a0)},${y(libres)}`,
        color: sobra ? COLOR.piso : COLOR.hotel,
      });
    }
  }
  const actual = serie.find((s) => s.radio === Math.round(radio / 50) * 50) ?? serie[0];
  return (
    <>
      <div className="mt-1 flex items-center gap-1 text-[10px]">
        <span className="text-[#52514e]">Escala</span>
        {([false, true] as const).map((v) => (
          <button key={String(v)} type="button" aria-pressed={log === v} onClick={() => setLog(v)}
            className={`rounded border px-1.5 py-0.5 ${log === v ? "border-[#24231f] bg-[#24231f] text-white" : "border-[#d8d5cd] bg-white"}`}>
            {v ? "logarítmica" : "lineal"}
          </button>
        ))}
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="mt-1 w-full" role="img" aria-label="Habitaciones absorbibles según el radio">
        {marcas.map((v) => (
          <g key={v}>
            <line x1={X0} x2={W - 6} y1={y(v)} y2={y(v)} stroke="#eeece7" />
            <text x={X0 - 3} y={y(v) + 3} fontSize="8" textAnchor="end" fill="#52514e">{v}</text>
          </g>
        ))}
        {bandas.map((b, i) => <polygon key={i} points={b.pts} fill={b.color} fillOpacity="0.28" />)}
        <line x1={X0} x2={W - 6} y1={y(libres)} y2={y(libres)} stroke={COLOR.hotel} strokeWidth="1.2" strokeDasharray="4 3" />
        <polyline points={linea((s) => s.pidenAlto)} fill="none" stroke={COLOR.piso} strokeWidth="1" strokeDasharray="3 2" />
        <polyline points={linea((s) => s.piden)} fill="none" stroke={COLOR.piso} strokeWidth="2" />
        <line x1={X0} x2={W - 6} y1={Y0 + alto} y2={Y0 + alto} stroke="#d9d6cf" />
        <line x1={x(radio)} x2={x(radio)} y1={y(actual.piden)} y2={Y0 + alto} stroke="#24231f" strokeWidth="1" strokeDasharray="3 2" />
        <circle cx={x(radio)} cy={y(actual.piden)} r="3.5" fill={COLOR.piso} stroke="#fff" strokeWidth="1.5" />
        {[0, 250, 500].map((r) => (
          <text key={r} x={x(r)} y={H - 4} fontSize="8" textAnchor="middle" fill="#52514e">{r} m</text>
        ))}
      </svg>
      <ul className="space-y-0.5 text-[11px] text-[#52514e]">
        <li><i className="mr-1.5 inline-block h-0.5 w-3 align-middle" style={{ background: COLOR.piso }} />habitaciones absorbibles ({dec(param.ocupacion_piso[0])} %; discontinua, {dec(param.ocupacion_piso[1])} %)</li>
        <li><i className="mr-1.5 inline-block h-2 w-3 align-middle" style={{ background: COLOR.hotel, opacity: 0.45 }} />hueco libre en el hotel hoy ({n(Math.round(libres))} hab.): lo que aún le cabe</li>
        <li><i className="mr-1.5 inline-block h-2 w-3 align-middle" style={{ background: COLOR.piso, opacity: 0.45 }} />lo que no le cabe y se va a otros hoteles</li>
        <li>A {Math.round(radio / 50) * 50} m: <b className="text-[#24231f]">{n(Math.round(actual.piden))}</b> habitaciones absorbibles</li>
      </ul>
    </>
  );
}

function PanelBarrio({ b, hotelesBarrio, param, onCerrar }: {
  b: BarrioHoy; hotelesBarrio: Hotel[]; param: DatosMapa["param"]; onCerrar: () => void;
}) {
  const [bajo, alto] = b.turistas_pisos;
  // Ocupación por habitaciones: hoy la media del INE; en 2028, más lo que reciben de los pisos.
  const hoy = param.ocupacion_hotel_habitaciones;
  const habs = hotelesBarrio.reduce((s, h) => s + (h.hab ?? 0), 0);
  const absorbidas = hotelesBarrio.reduce((s, h) => s + (h.hab_abs ?? 0), 0);
  const sube = habs ? Math.min((absorbidas / habs) * 100, 100 - hoy) : null;
  const top = [...hotelesBarrio].filter((h) => (h.hab_abs ?? 0) > 0)
    .sort((a, c) => (c.hab_abs ?? 0) - (a.hab_abs ?? 0)).slice(0, 5);
  const tope = top[0]?.hab_abs ?? 1;
  // Quién gana, en la unidad que cada uno alquila: el hotel, habitaciones; Airbnb, el piso entero.
  const unidades = b.pisos + b.habitaciones_hoteles;
  const pisos = unidades ? (b.pisos / unidades) * 100 : 0;
  const hoteles = unidades ? 100 - pisos : 0;
  const mas = b.demanda_hoy > 0 ? (b.demanda_2028 / b.demanda_hoy - 1) * 100 : null;
  return (
    <aside className="absolute top-3 right-3 bottom-3 z-[1000] w-[290px] max-w-[85vw] overflow-y-auto rounded border border-[#e3e0da] bg-white p-4 text-[13px] shadow-sm">
      <div className="flex items-start justify-between gap-2">
        <h2 className="text-[16px] leading-tight font-semibold">{b.barrio}</h2>
        <button type="button" onClick={onCerrar} aria-label="Cerrar"
          className="text-[18px] leading-none text-[#52514e]">×</button>
      </div>

      <Titulo className="mt-3">Pisos frente a habitaciones de hotel</Titulo>
      <div className="flex h-5 overflow-hidden rounded bg-[#eeece7] text-[11px] font-semibold text-white"
        role="img" aria-label={`Pisos ${pisos.toFixed(0)} % y hoteles ${hoteles.toFixed(0)} %`}>
        <div className="flex items-center justify-center" style={{ width: `${pisos}%`, background: COLOR.piso }}>
          {pisos >= 12 && `${pisos.toFixed(0)} %`}
        </div>
        <div className="flex items-center justify-center" style={{ width: `${hoteles}%`, background: COLOR.hotel }}>
          {hoteles >= 12 && `${hoteles.toFixed(0)} %`}
        </div>
      </div>
      <p className="mt-1 text-[11px] text-[#52514e]">
        {unidades ? `${n(b.pisos)} pisos · ${n(b.habitaciones_hoteles)} habitaciones` : "Sin alojamiento"}
      </p>

      <Titulo className="mt-4">Noche mediana</Titulo>
      <Precio color={COLOR.piso} nombre="Piso entero" precio={b.precio_pisos} banda={b.banda_pisos} />
      <div className="mt-2 flex justify-between text-[12px]">
        <span>Precio medio por plaza (pisos)</span>
        <b className="tabular-nums">{b.precio_plaza_pisos == null ? "—" : `${dec(b.precio_plaza_pisos)} €`}</b>
      </div>
      <Precio color={COLOR.hotel} nombre="Habitación de hotel" precio={null} banda={b.banda_hoteles} />

      <Bloque color={COLOR.piso} titulo="Pisos" cifra={rango(bajo, alto)} unidad="turistas">
        {n(b.plazas_pisos)} plazas
      </Bloque>
      <section className="mt-2 rounded bg-[#fbe3cc] px-3 py-2 text-[11px] leading-snug text-[#52514e]">
        Se dejarían de facturar al año
        <b className="block text-[18px] leading-tight text-[#a84a00]">
          {dinero(b.facturacion_pisos[0])}–{dinero(b.facturacion_pisos[1])}
        </b>
        Aproximado: precio de la noche × noches ocupadas ({dec(param.ocupacion_piso[0])} %–{dec(param.ocupacion_piso[1])} %).
      </section>
      <Operador color={COLOR.piso} etiqueta="Anfitrión con más pisos" op={b.operador_pisos}
        unidad="pisos" vacio="Ningún anfitrión llega a 5 pisos" />

      <Bloque color={COLOR.hotel} titulo="Hoteles" cifra={n(b.turistas_hoteles)} unidad="turistas">
        {n(b.hoteles)} hoteles · {n(b.plazas_hoteles)} plazas · {n(habs)} habitaciones
      </Bloque>
      {sube != null && (
        <section className="mt-2 rounded bg-[#e6eff8] px-3 py-2 text-[11px] leading-snug text-[#52514e]">
          Ocupación de las habitaciones en 2028
          <b className="block text-[18px] leading-tight text-[#123a6b]">
            +{sube.toLocaleString("es", { maximumFractionDigits: 1 })} pts
          </b>
          Del {dec(hoy)} % al {dec(hoy + sube)} % de media en el barrio.
        </section>
      )}
      {top.length > 0 && (
        <div className="mt-2">
          <p className="mb-1 text-[11px] font-medium">Los 5 hoteles que más ganan (habitaciones ocupadas de más)</p>
          <ol className="space-y-1.5 text-[11px]">
            {top.map((h, i) => (
              <li key={`${h.nom}-${i}`}>
                <div className="flex justify-between gap-2">
                  <span className="truncate">{h.nom ?? "Hotel"}</span>
                  <b className="tabular-nums">+{n(Math.round(h.hab_abs ?? 0))}</b>
                </div>
                <span className="block h-1.5 rounded bg-[#eeece7]">
                  <span className="block h-full rounded" style={{ width: `${((h.hab_abs ?? 0) / tope) * 100}%`, background: COLOR.hotel }} />
                </span>
                <span className="text-[10px]">{n(h.hab)} hab. · +{n(Math.round(((h.hab_abs ?? 0) / (h.hab || 1)) * 100))} pts</span>
              </li>
            ))}
          </ol>
        </div>
      )}
      <Operador color={COLOR.hotel} etiqueta="Titular con más hoteles" op={b.operador_hoteles}
        unidad="hoteles" vacio="Ninguna sociedad reúne 2 hoteles" />

      <Bloque color={COLOR.restaurante} titulo="Restauración" cifra={n(b.restaurantes)} unidad="locales">
        {n(b.alta)} con demanda alta
        {mas == null ? "" : <> · clientes en 2028: <b className="text-[#24231f]">{mas > 0 ? "+" : ""}{n(Math.round(mas))} %</b></>}
      </Bloque>
      <section className="mt-2 pl-3 text-[11px] leading-snug text-[#52514e]">
        {b.marca
          ? <>Nombre más repetido: <b className="text-[#24231f]">{b.marca.nom}</b> ({n(b.marca.locales)})</>
          : "Ningún nombre se repite"}
      </section>

      <Link href="/fuentes" className="mt-4 block text-[11px] text-[#52514e] underline underline-offset-2">
        Supuestos y fuentes →
      </Link>
    </aside>
  );
}

function Operador({ color, etiqueta, op, unidad, vacio }: {
  color: string; etiqueta: string; op: { nom: string; n: number } | null; unidad: string;
  vacio: string;
}) {
  return (
    <section className="mt-2 border-l-[3px] pl-3 text-[11px] leading-snug text-[#52514e]"
      style={{ borderColor: color }}>
      {op ? (
        <>
          {etiqueta}: <b className="text-[#24231f]">{op.nom}</b> ({n(op.n)} {unidad})
        </>
      ) : vacio}
    </section>
  );
}

/** Escala común a todos los barrios, para que dos barras de dos barrios distintos se comparen. */
const PRECIO_TOPE = 400;

const BANDAS = ["€", "€€", "€€€", "€€€€"];

/** El piso con su euro y su banda; el hotel solo con la banda: un euro de hotel diría más de lo que sabemos. */
function Precio({ color, nombre, precio, banda }: {
  color: string; nombre: string; precio: number | null; banda: string | null;
}) {
  const ancho = precio != null
    ? Math.min((precio / PRECIO_TOPE) * 100, 100)
    : banda ? ((BANDAS.indexOf(banda) + 1) / BANDAS.length) * 100 : 0;
  return (
    <div className="mt-2">
      <div className="flex justify-between text-[12px]">
        <span>{nombre}</span>
        <span className="tabular-nums">
          {precio != null ? <><b>{n(Math.round(precio))} €</b> · {banda}</> : <b>{banda ?? "sin banda"}</b>}
        </span>
      </div>
      <div className="mt-0.5 h-2.5 rounded bg-[#eeece7]">
        <div className="h-full rounded" style={{ width: `${ancho}%`, background: color }} />
      </div>
    </div>
  );
}

function Bloque({ color, titulo, cifra, unidad, children }: {
  color: string; titulo: string; cifra: string; unidad: string; children: React.ReactNode;
}) {
  return (
    <section className="mt-3 border-l-[3px] pl-3" style={{ borderColor: color }}>
      <p className="text-[12px] font-medium">{titulo}</p>
      <p className="tabular-nums">
        <span className="text-[22px] leading-none font-semibold">{cifra}</span>{" "}
        <span className="text-[#52514e]">{unidad}</span>
      </p>
      <p className="mt-1 text-[11px] leading-snug text-[#52514e]">{children}</p>
    </section>
  );
}
