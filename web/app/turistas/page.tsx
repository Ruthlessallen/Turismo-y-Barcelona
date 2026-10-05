"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  BarrasDivergentes, BarrasH, Cifra, Matriz, Seccion, Tarjeta, MORADO, VERDE,
} from "@/app/components/Graficos";
import { COLOR, n } from "@/app/lib/tiposMapa";

type Turistas = {
  ine: {
    periodo: string; viajeros: number; pernoctaciones: number; estancia_media: number;
    extranjeros_pct: number; pernoctaciones_por_noche: number;
  };
  dataset: {
    hoteles_noche: number; hoteles_pernoctaciones_ano: number; pisos_noche: [number, number];
    pisos_pernoctaciones_ano: [number, number]; estancia_pisos: number;
    pisos_turistas_ano: [number, number]; nuevos_noche: number; hoteles_frente_a_ine_pct: number;
  };
};

type Flujo = {
  turistas: number;
  km: { mediana: number; media: number; p90: number; maximo: number; mas_de_2km_pct: number };
  distancia: { desde: number; hasta: number | null; pct: number }[];
  bandas: { etiquetas: string[]; matriz: number[][]; su_banda_pct: number; una_mas_pct: number; dos_o_mas_pct: number };
  barrios: { barrio: string; hoy: number; en_2028: number; salen: number; llegan: number; saldo: number; cambio_pct: number | null }[];
};

const millones = (v: number, d = 1) => (v / 1e6).toLocaleString("es", { maximumFractionDigits: d });
const dec = (v: number, d = 2) => v.toLocaleString("es", { maximumFractionDigits: d });

const MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
/** «2025-08 a 2026-07» → «ago 2025 – jul 2026». */
const periodo = (p: string) =>
  p.split(" a ").map((m) => `${MESES[Number(m.slice(5, 7)) - 1]} ${m.slice(0, 4)}`).join(" – ");

const TRAMO = (desde: number, hasta: number | null) =>
  hasta == null ? `más de ${desde} km`
    : desde === 0 ? `menos de ${hasta * 1000} m`
      : hasta <= 1 ? `${desde * 1000}–${hasta * 1000} m` : `${dec(desde, 1)}–${dec(hasta, 1)} km`;

export default function PaginaTuristas() {
  const [t, setT] = useState<Turistas | null>(null);
  const [f, setF] = useState<Flujo | null>(null);

  useEffect(() => {
    fetch("/data/mapa/turistas.json").then((r) => r.json()).then(setT);
    fetch("/data/mapa/flujo.json").then((r) => r.json()).then(setF);
  }, []);

  if (!t || !f) return <main className="min-h-full bg-[#faf9f7]" />;
  const { ine, dataset: d } = t;
  const sube = [...f.barrios].filter((b) => b.saldo > 0).sort((a, b) => b.saldo - a.saldo).slice(0, 8);
  const baja = [...f.barrios].filter((b) => b.saldo < 0).sort((a, b) => a.saldo - b.saldo).slice(0, 8);
  const tope = Math.max(...sube.map((b) => b.saldo), ...baja.map((b) => -b.saldo));
  const pct = (b: { cambio_pct: number | null }) => (b.cambio_pct == null ? "" : `${b.cambio_pct > 0 ? "+" : ""}${n(Math.round(b.cambio_pct))} %`);

  return (
    <main className="min-h-full bg-[#faf9f7] text-[#24231f]">
      <div className="mx-auto max-w-6xl px-5 py-8 sm:px-8">
        <Seccion color="#24231f" titulo="Turistas en este conjunto de datos">
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <Cifra valor={n(d.hoteles_noche)} etiqueta="en hoteles" pie="por noche" />
            <Cifra valor={`${n(d.pisos_noche[0])}–${n(d.pisos_noche[1])}`} etiqueta="en pisos" pie="por noche" />
            <Cifra valor={n(d.nuevos_noche)} etiqueta="pasan a hoteles en 2028" pie="por noche" color={COLOR.hotel} />
            <Cifra valor={`${millones(d.pisos_turistas_ano[0])}–${millones(d.pisos_turistas_ano[1])} M`}
              etiqueta="turistas al año en pisos" pie={`a ${d.estancia_pisos} noches de estancia`} />
          </div>
        </Seccion>

        <Seccion color={COLOR.hotel} titulo="Lo que dice el INE · hoteles de Barcelona">
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <Cifra valor={`${millones(ine.viajeros)} M`} etiqueta="viajeros" pie={periodo(ine.periodo)} />
            <Cifra valor={`${millones(ine.pernoctaciones)} M`} etiqueta="pernoctaciones" />
            <Cifra valor={dec(ine.estancia_media)} etiqueta="noches de estancia media" />
            <Cifra valor={`${n(Math.round(ine.extranjeros_pct))} %`} etiqueta="vienen del extranjero" />
          </div>
          <div className="mt-3 grid gap-3 lg:grid-cols-2">
            <Tarjeta titulo="Pernoctaciones en hoteles, por noche">
              <BarrasH max={ine.pernoctaciones_por_noche} color={COLOR.hotel} filas={[
                { etiqueta: "INE", valor: ine.pernoctaciones_por_noche },
                { etiqueta: "Nuestros 750 hoteles", valor: d.hoteles_noche,
                  pie: `(${d.hoteles_frente_a_ine_pct > 0 ? "+" : ""}${n(Math.round(d.hoteles_frente_a_ine_pct))} %)` },
              ]} />
            </Tarjeta>
            <Tarjeta titulo="Pernoctaciones al año">
              <BarrasH max={ine.pernoctaciones} filas={[
                { etiqueta: "Hoteles · INE", valor: ine.pernoctaciones, color: COLOR.hotel },
                { etiqueta: "Hoteles · nuestros", valor: d.hoteles_pernoctaciones_ano, color: COLOR.hotel },
                { etiqueta: "Pisos · nuestros (media)", valor: (d.pisos_pernoctaciones_ano[0] + d.pisos_pernoctaciones_ano[1]) / 2, color: COLOR.piso,
                  pie: `(${millones(d.pisos_pernoctaciones_ano[0])}–${millones(d.pisos_pernoctaciones_ano[1])} M)` },
              ]} formato={(v) => `${millones(v)} M`} />
            </Tarjeta>
          </div>
          <p className="mt-2 text-[11px] text-[#52514e]">
            INE, Encuesta de Ocupación Hotelera (hoteles, hostales y pensiones), {periodo(ine.periodo)}. El INE
            no mide pisos turísticos. <Link href="/fuentes" className="underline underline-offset-2">Fuentes →</Link>
          </p>
        </Seccion>

        <Seccion color={COLOR.piso} titulo="Adónde van los turistas de los pisos">
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <Cifra valor={`${dec(f.km.mediana)} km`} etiqueta="distancia mediana" />
            <Cifra valor={`${dec(f.km.media)} km`} etiqueta="distancia media" />
            <Cifra valor={`${dec(f.km.p90, 1)} km`} etiqueta="el 90 % llega a menos de" />
            <Cifra valor={`${dec(f.km.mas_de_2km_pct, 1)} %`} etiqueta="recorre más de 2 km" pie={`máximo ${dec(f.km.maximo, 1)} km`} />
          </div>

          <div className="mt-3 grid gap-3 lg:grid-cols-2">
            <Tarjeta titulo="Cuántos se alejan, por tramo (% de turistas)">
              <BarrasH max={50} color={COLOR.piso} formato={(v) => `${dec(v, 1)} %`}
                filas={f.distancia.map((c) => ({ etiqueta: TRAMO(c.desde, c.hasta), valor: c.pct }))} />
            </Tarjeta>
            <Tarjeta titulo="De qué banda sale y a cuál llega (turistas por noche)">
              <Matriz etiquetas={f.bandas.etiquetas} valores={f.bandas.matriz}
                titulo={{ filas: "sale de", columnas: "va a" }} />
              <p className="mt-2 text-[12px] tabular-nums">
                <b>{n(Math.round(f.bandas.su_banda_pct))} %</b> su banda ·{" "}
                <b>{n(Math.round(f.bandas.una_mas_pct))} %</b> una más cara ·{" "}
                <b>{n(Math.round(f.bandas.dos_o_mas_pct))} %</b> dos o más
              </p>
            </Tarjeta>
          </div>

          <div className="mt-3 grid gap-3 lg:grid-cols-2">
            <Tarjeta titulo="Barrios que ganan turistas en 2028 (por noche)">
              <BarrasDivergentes tope={tope}
                filas={sube.map((b) => ({ etiqueta: b.barrio, valor: b.saldo, pie: pct(b) }))} />
            </Tarjeta>
            <Tarjeta titulo="Barrios que pierden turistas en 2028 (por noche)">
              <BarrasDivergentes tope={tope}
                filas={baja.map((b) => ({ etiqueta: b.barrio, valor: b.saldo, pie: pct(b) }))} />
            </Tarjeta>
          </div>
          <p className="mt-2 text-[11px] text-[#52514e]">
            <span style={{ color: VERDE }}>■</span> llegan más de los que salen ·{" "}
            <span style={{ color: MORADO }}>■</span> salen más de los que llegan. Turistas por noche, año medio.
          </p>
        </Seccion>
      </div>
    </main>
  );
}
