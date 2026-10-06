"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useEffect, useState } from "react";

import { BarrasH, Cifra, Columnas, Seccion, Tarjeta } from "@/app/components/Graficos";
import { LEYENDA, type HotelesBarrio } from "@/app/lib/hotelesMapa";
import { GRUPOS_PEUAT } from "@/app/lib/peuat";
import { COLOR, OSCURO, n, type HotelNuevo } from "@/app/lib/tiposMapa";

// Leaflet toca `window` al cargarse: sin esto el render del servidor revienta.
const MapaHoteles = dynamic(() => import("@/app/components/MapaHoteles"), {
  ssr: false,
  loading: () => <div className="h-full w-full bg-[#f5f4f1]" />,
});

type Pagina = {
  barrios: HotelesBarrio[];
  categorias: { cat: string; hoteles: number; habitaciones: number }[];
  ocupacion_mensual: { mes: string; ocupacion: number }[];
  ocupacion_bandas: { banda: string; habitaciones: number; hoy: number; en_2028: number }[];
  ocupacion: { hoy: number; en_2028: number; habitaciones: number; habitaciones_absorbidas: number };
  nuevos: HotelNuevo[];
};

type Ine = {
  periodo: string; viajeros: number; pernoctaciones: number; estancia_media: number; extranjeros_pct: number;
};

const MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
const mes = (aaaamm: string) => MESES[Number(aaaamm.slice(5, 7)) - 1];
/** «2025-08 a 2026-07» → «ago 2025 – jul 2026». */
const periodo = (p: string) =>
  p.split(" a ").map((m) => `${MESES[Number(m.slice(5, 7)) - 1]} ${m.slice(0, 4)}`).join(" – ");
const dec = (v: number) => v.toLocaleString("es", { maximumFractionDigits: 1 });
const millones = (v: number) => (v / 1e6).toLocaleString("es", { maximumFractionDigits: 1 });

/** Los nombres de categoría del registro vienen en catalán; «No aplica» son hostales y pensiones. */
const CATEGORIA = (c: string) => (c === "No aplica" ? "Hostales y pensiones" : c.replace("estrelles", "estrellas"));

export default function PaginaHoteles() {
  const [p, setP] = useState<Pagina | null>(null);
  const [ine, setIne] = useState<Ine | null>(null);
  const [barrios, setBarrios] = useState<GeoJSON.FeatureCollection | null>(null);
  const [peuat, setPeuat] = useState<GeoJSON.FeatureCollection | null>(null);
  const [verPeuat, setVerPeuat] = useState(true);

  useEffect(() => {
    fetch("/data/mapa/hoteles_pagina.json").then((r) => r.json()).then(setP);
    fetch("/data/mapa/turistas.json").then((r) => r.json()).then((t) => setIne(t.ine));
    fetch("/data/geo/barrios.geojson").then((r) => r.json()).then(setBarrios);
    fetch("/data/geo/peuat.geojson").then((r) => r.json()).then(setPeuat);
  }, []);

  if (!p || !ine || !barrios || !peuat) return <main className="min-h-full bg-[#faf9f7]" />;
  const nuevaObra = p.nuevos.filter((h) => h.tipo === "Obra nueva").reduce((s, h) => s + (h.habitaciones ?? 0), 0);

  return (
    <main className="min-h-full bg-[#faf9f7] text-[#24231f]">
      <div className="mx-auto grid max-w-6xl gap-8 px-5 py-8 sm:px-8 lg:grid-cols-[minmax(0,1fr)_420px]">
        <div className="min-w-0">
          <Seccion color={COLOR.hotel} titulo={`Lo que dice el INE · hoteles de Barcelona · ${periodo(ine.periodo)}`}>
            <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
              <Cifra valor={`${millones(ine.viajeros)} M`} etiqueta="viajeros" color={OSCURO.hotel} />
              <Cifra valor={`${millones(ine.pernoctaciones)} M`} etiqueta="pernoctaciones" color={OSCURO.hotel} />
              <Cifra valor={ine.estancia_media.toLocaleString("es", { minimumFractionDigits: 2 })} etiqueta="noches de estancia media" color={OSCURO.hotel} />
              <Cifra valor={`${n(Math.round(ine.extranjeros_pct))} %`} etiqueta="vienen del extranjero" color={OSCURO.hotel} />
            </div>
          </Seccion>

          <Seccion color={COLOR.hotel} titulo="Qué supone para un hotel que desaparezcan los pisos">
            <div className="grid gap-3">
              <Tarjeta titulo="Habitaciones ocupadas por banda, hoy y en 2028 (%)">
                <BarrasH max={100} formato={(v) => `${dec(v)} %`}
                  filas={p.ocupacion_bandas.flatMap((b) => [
                    { etiqueta: `${b.banda} · hoy`, valor: (b.hoy / b.habitaciones) * 100, color: "#9dbbdc" },
                    { etiqueta: `${b.banda} · 2028`, valor: (b.en_2028 / b.habitaciones) * 100, color: COLOR.hotel },
                  ])} />
                <p className="mt-2 text-[11px] text-[#52514e]">Banda por plaza. Los hoteles baratos se llenan: casi no tienen hueco.</p>
              </Tarjeta>

              <Tarjeta titulo="Ocupación por habitaciones, mes a mes (INE, %)">
                <Columnas datos={p.ocupacion_mensual.map((o) => ({ etiqueta: mes(o.mes), valor: o.ocupacion }))}
                  referencia={p.ocupacion.hoy} formato={(v) => `${Math.round(v)}`} alto={150} />
                <p className="mt-2 text-[11px] text-[#52514e]">Línea: media anual, {dec(p.ocupacion.hoy)} %.</p>
              </Tarjeta>
            </div>
          </Seccion>

          <Seccion color={COLOR.hotel} titulo="Detalle hotelero">
            <Tarjeta titulo="Habitaciones por categoría">
              <BarrasH color={COLOR.hotel}
                filas={p.categorias.slice(0, 8).map((c) => ({
                  etiqueta: CATEGORIA(c.cat), valor: c.habitaciones, pie: `· ${n(c.hoteles)} hoteles` }))} />
            </Tarjeta>
          </Seccion>
        </div>

        {/* Columna derecha: el mapa, y debajo los hoteles anunciados. Sin scroll propio: la página es la que se mueve. */}
        <aside className="min-w-0">
          <div className="rounded border border-[#e3e0da] bg-white p-3">
            <div className="mb-2 flex items-start justify-between gap-2">
              <p className="text-[12px] leading-snug font-medium">
                Hoteles por barrio y turistas de más en 2028
              </p>
              <button type="button" aria-pressed={verPeuat} onClick={() => setVerPeuat(!verPeuat)}
                className={`shrink-0 rounded border px-2 py-0.5 text-[11px] ${verPeuat
                  ? "border-[#24231f] bg-[#24231f] text-white" : "border-[#d8d5cd] bg-white"}`}>
                PEUAT
              </button>
            </div>
            <div className="h-[340px] overflow-hidden rounded border border-[#e3e0da]">
              <MapaHoteles barrios={barrios} peuat={peuat} datos={p.barrios} verPeuat={verPeuat} />
            </div>
            <ul className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-[11px]">
              {LEYENDA.map((l) => (
                <li key={l.texto} className="flex items-center gap-1">
                  <span className="inline-block h-2.5 w-2.5 rounded-sm border border-[#d8d5cd]" style={{ background: l.color }} />
                  {l.texto}
                </li>
              ))}
            </ul>
            {verPeuat && (
              <>
                <ul className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-[11px]">
                  {GRUPOS_PEUAT.map((g) => (
                    <li key={g.id} className="flex items-center gap-1">
                      <span className="inline-block w-4 border-t-[3px]" style={{ borderColor: g.color, borderStyle: g.dash ? "dashed" : "solid" }} />
                      {g.etiqueta}
                    </li>
                  ))}
                </ul>
                <p className="mt-1 text-[10px] leading-snug text-[#52514e]">
                  Zonas del PEUAT con los códigos del Ajuntament. Cuáles admiten hoteles nuevos no está verificado.
                </p>
              </>
            )}
            <p className="mt-1 text-[10px] leading-snug text-[#52514e]">
              Color: turistas de más en los hoteles del barrio en 2028. Acércate para ver hoteles · %.
            </p>
          </div>

          <div className="mt-3 rounded border border-[#e3e0da] bg-white p-3">
            <p className="text-[12px] font-medium">Hoteles anunciados</p>
            <p className="mt-0.5 text-[11px] text-[#52514e]">
              {n(nuevaObra)} habitaciones de obra nueva, el {dec((nuevaObra / p.ocupacion.habitaciones_absorbidas) * 100)} % de las
              que piden los pisos.
            </p>
            <ul className="mt-2 divide-y divide-[#eeece7] text-[12px]">
              {p.nuevos.map((h) => (
                <li key={h.nombre} className="py-2">
                  <p className="font-medium">{h.nombre}</p>
                  <p className="text-[11px] text-[#52514e]">{h.direccion}</p>
                  <p className="mt-0.5 flex flex-wrap gap-x-2 text-[11px]">
                    <span className="tabular-nums">{h.habitaciones == null ? "— hab." : `${n(h.habitaciones)} hab.`}</span>
                    <span>{h.apertura}</span>
                    <span className="text-[#52514e]">{h.tipo}</span>
                    <a href={h.url} target="_blank" rel="noopener" className="underline underline-offset-2">{h.fuente}</a>
                  </p>
                </li>
              ))}
            </ul>
            <p className="mt-1 text-[10px] text-[#52514e]">
              De prensa, 5 de octubre de 2026: no es un registro oficial.{" "}
              <Link href="/fuentes" className="underline underline-offset-2">Fuentes →</Link>
            </p>
          </div>
        </aside>
      </div>
    </main>
  );
}
