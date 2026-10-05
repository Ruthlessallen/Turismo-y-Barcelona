"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { BarrasH, Cifra, Columnas, Seccion, Tarjeta } from "@/app/components/Graficos";
import { COLOR, n, type HotelNuevo } from "@/app/lib/tiposMapa";

type Pagina = {
  categorias: { cat: string; hoteles: number; habitaciones: number }[];
  ocupacion_mensual: { mes: string; ocupacion: number }[];
  ocupacion_bandas: { banda: string; habitaciones: number; hoy: number; en_2028: number }[];
  ocupacion: { hoy: number; en_2028: number; habitaciones: number; habitaciones_absorbidas: number };
  nuevos: HotelNuevo[];
};

type Dashboard = { hoteles: { total: number; habitaciones: number; plazas: number } };

const MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
const mes = (aaaamm: string) => MESES[Number(aaaamm.slice(5, 7)) - 1];
const dec = (v: number) => v.toLocaleString("es", { maximumFractionDigits: 1 });

/** Los nombres de categoría del registro vienen en catalán; «No aplica» son hostales y pensiones. */
const CATEGORIA = (c: string) => (c === "No aplica" ? "Hostales y pensiones" : c.replace("estrelles", "estrellas"));

export default function PaginaHoteles() {
  const [p, setP] = useState<Pagina | null>(null);
  const [d, setD] = useState<Dashboard | null>(null);

  useEffect(() => {
    fetch("/data/mapa/hoteles_pagina.json").then((r) => r.json()).then(setP);
    fetch("/data/mapa/dashboard.json").then((r) => r.json()).then(setD);
  }, []);

  if (!p || !d) return <main className="min-h-full bg-[#faf9f7]" />;
  const nuevaObra = p.nuevos.filter((h) => h.tipo === "Obra nueva").reduce((s, h) => s + (h.habitaciones ?? 0), 0);
  const anunciadas = p.nuevos.reduce((s, h) => s + (h.habitaciones ?? 0), 0);

  return (
    <main className="min-h-full bg-[#faf9f7] text-[#24231f]">
      <div className="mx-auto max-w-6xl px-5 py-8 sm:px-8">
        <Seccion color={COLOR.hotel} titulo="Hoteles de Barcelona">
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <Cifra valor={n(d.hoteles.total)} etiqueta="hoteles" />
            <Cifra valor={n(d.hoteles.habitaciones)} etiqueta="habitaciones" />
            <Cifra valor={n(d.hoteles.plazas)} etiqueta="plazas" />
            <Cifra valor={`${dec(p.ocupacion.hoy)} → ${dec(p.ocupacion.en_2028)} %`}
              etiqueta="habitaciones ocupadas, hoy y en 2028" color={COLOR.hotel}
              pie={`${n(p.ocupacion.habitaciones_absorbidas)} habitaciones más`} />
          </div>
        </Seccion>

        <Seccion color={COLOR.hotel} titulo="Qué supone para un hotel que desaparezcan los pisos">
          <div className="grid gap-3 lg:grid-cols-2">
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

        <Seccion color={COLOR.hotel} titulo="Hoteles anunciados">
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <Cifra valor={n(nuevaObra)} etiqueta="habitaciones de obra nueva"
              pie={`${dec((nuevaObra / p.ocupacion.habitaciones_absorbidas) * 100)} % de las que piden los pisos`} />
            <Cifra valor={n(anunciadas)} etiqueta="habitaciones anunciadas, con reformas"
              pie="cambios de gestión incluidos" />
          </div>

          <div className="mt-3 overflow-x-auto rounded border border-[#e3e0da] bg-white">
            <table className="w-full text-left text-[12px]">
              <thead className="border-b border-[#e3e0da] text-[#52514e]">
                <tr>
                  <th className="px-3 py-2 font-medium">Hotel</th>
                  <th className="px-3 py-2 font-medium">Habitaciones</th>
                  <th className="px-3 py-2 font-medium">Apertura</th>
                  <th className="px-3 py-2 font-medium">Qué es</th>
                  <th className="px-3 py-2 font-medium">Fuente</th>
                </tr>
              </thead>
              <tbody>
                {p.nuevos.map((h) => (
                  <tr key={h.nombre} className="border-b border-[#eeece7] last:border-0">
                    <td className="px-3 py-2"><b>{h.nombre}</b><span className="block text-[#52514e]">{h.direccion}</span></td>
                    <td className="px-3 py-2 tabular-nums">{n(h.habitaciones)}</td>
                    <td className="px-3 py-2">{h.apertura}</td>
                    <td className="px-3 py-2">{h.tipo}</td>
                    <td className="px-3 py-2">
                      <a href={h.url} target="_blank" rel="noopener" className="underline underline-offset-2">{h.fuente}</a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-2 text-[11px] text-[#52514e]">
            Recopilado de prensa el 5 de octubre de 2026: no es un registro oficial. En el mapa salen con una
            exclamación los que tienen dirección. <Link href="/fuentes" className="underline underline-offset-2">Fuentes →</Link>
          </p>
        </Seccion>
      </div>
    </main>
  );
}
