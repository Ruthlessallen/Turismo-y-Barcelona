"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import {
  COLOR, analisisHotel, n,
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
    ]).then(([geo, barrios, pisos, hoteles, restaurantes, pagina]) =>
      setDatos({ geo, barrios, pisos, hoteles, restaurantes, nuevos: pagina.nuevos }));
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
        <Titulo>Capas</Titulo>
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
        <PanelBarrio b={ficha} onCerrar={() => setFoco(null)} />
      ) : null}
    </main>
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
  const a = useMemo(() => analisisHotel(hotel, datos.pisos, radio), [hotel, datos.pisos, radio]);
  const pct = (v: number) => (a.total > 0 ? Math.round((v / a.total) * 100) : 0);

  return (
    <aside className="absolute top-3 right-3 bottom-3 z-[1000] w-[290px] max-w-[85vw] overflow-y-auto rounded border border-[#e3e0da] bg-white p-4 text-[13px] shadow-sm">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h2 className="text-[16px] leading-tight font-semibold">{hotel.nom ?? "Hotel"}</h2>
          <p className="text-[11px] text-[#52514e]">{hotel.cat} · {hotel.barrio}</p>
        </div>
        <button type="button" onClick={onCerrar} aria-label="Cerrar"
          className="text-[18px] leading-none text-[#52514e]">×</button>
      </div>

      <Bloque color={COLOR.piso} titulo={`Pisos a ${radio} m`} cifra={n(a.cerca)} unidad="pisos">
        {n(a.plazas)} plazas · {n(a.habitaciones)} habitaciones
      </Bloque>
      <Bloque color={COLOR.hotel} titulo="El hotel" cifra={n(a.total)} unidad="habitaciones">
        {n(hotel.plazas)} plazas
      </Bloque>
      <Bloque color={COLOR.hotel} titulo="Ocupadas hoy" cifra={n(Math.round(a.ocupadasHoy))}
        unidad="habitaciones">
        {pct(a.ocupadasHoy)} % del hotel
      </Bloque>
      <Bloque color="#24231f" titulo="Ocupadas en 2028" cifra={n(Math.round(a.ocupadas2028))}
        unidad="habitaciones">
        {pct(a.ocupadas2028)} % del hotel
      </Bloque>
      <Bloque color={COLOR.piso} titulo="Absorbe de Airbnb" cifra={n(a.pisosAbsorbidos)} unidad="pisos">
        {n(Math.round(a.absorbe))} habitaciones
      </Bloque>
    </aside>
  );
}

function PanelBarrio({ b, onCerrar }: { b: BarrioHoy; onCerrar: () => void }) {
  const [bajo, alto] = b.turistas_pisos;
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
      <Precio color={COLOR.hotel} nombre="Habitación de hotel" precio={null} banda={b.banda_hoteles} />

      <Bloque color={COLOR.piso} titulo="Pisos" cifra={rango(bajo, alto)} unidad="turistas">
        {n(b.plazas_pisos)} plazas · {dinero(b.facturacion_pisos[0])}–{dinero(b.facturacion_pisos[1])} al año
      </Bloque>
      <Operador color={COLOR.piso} etiqueta="Anfitrión con más pisos" op={b.operador_pisos}
        unidad="pisos" vacio="Ningún anfitrión llega a 5 pisos" />

      <Bloque color={COLOR.hotel} titulo="Hoteles" cifra={n(b.turistas_hoteles)} unidad="turistas">
        {n(b.hoteles)} hoteles · {n(b.plazas_hoteles)} plazas
      </Bloque>
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
