"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { BarrasDivergentes, BarrasH, Cifra, Seccion, Tarjeta } from "@/app/components/Graficos";
import { COLOR, OSCURO, n } from "@/app/lib/tiposMapa";

type Barrio = {
  barrio: string; hoy: number; en_2028: number; cambio: number; locales: number; cambio_pct: number | null;
};

type Pagina = {
  locales: number; con_turistas: number; hoy: number; en_2028: number; ganan: number; pierden: number;
  marcas: { nom: string; locales: number; cambio_pct: number | null }[];
  locales_top: { nom: string | null; tipo: string | null; barrio: string | null; hoy: number; en_2028: number }[];
  barrios_mas: Barrio[];
  barrios_menos: Barrio[];
};

const signo = (v: number) => `${v > 0 ? "+" : v < 0 ? "−" : ""}${n(Math.abs(Math.round(v)))}`;
const pct = (v: number | null) => (v == null ? "" : `${signo(v)} %`);

/** Lo que sale al pasar el ratón por la barra de un barrio. */
const detalle = (b: Barrio) => `Hoy: ${n(b.hoy)} clientes · 2028: ${n(b.en_2028)}`;

export default function PaginaRestauracion() {
  const [p, setP] = useState<Pagina | null>(null);

  useEffect(() => {
    fetch("/data/mapa/restauracion_pagina.json").then((r) => r.json()).then(setP);
  }, []);

  if (!p) return <main className="min-h-full bg-[#faf9f7]" />;
  const mas = p.barrios_mas.map((b) => ({ etiqueta: b.barrio, valor: b.cambio, pie: pct(b.cambio_pct), detalle: detalle(b) }));
  const menos = p.barrios_menos.map((b) => ({ etiqueta: b.barrio, valor: b.cambio, pie: pct(b.cambio_pct), detalle: detalle(b) }));
  const maxLocal = Math.max(...p.locales_top.map((l) => l.en_2028 - l.hoy));

  return (
    <main className="min-h-full bg-[#faf9f7] text-[#24231f]">
      <div className="mx-auto max-w-6xl px-5 py-8 sm:px-8">
        <Seccion color={COLOR.restaurante} titulo="Restauración de Barcelona">
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <Cifra valor={n(p.locales)} etiqueta="locales" color={OSCURO.restaurante} />
            <Cifra valor={`+${((p.en_2028 / p.hoy - 1) * 100).toLocaleString("es", { maximumFractionDigits: 1 })} %`} etiqueta="clientes de turistas en 2028" grande
              pie={`${n(p.hoy)} → ${n(p.en_2028)} por noche`} color={OSCURO.restaurante} />
            <Cifra valor={n(p.ganan)} etiqueta="locales que ganan" color={OSCURO.restaurante} />
            <Cifra valor={n(p.pierden)} etiqueta="locales que pierden" color={OSCURO.restaurante} />
          </div>
        </Seccion>

        <Seccion color={COLOR.restaurante} titulo="Las 10 marcas con más locales">
          <Tarjeta titulo="Locales con el mismo nombre comercial">
            <BarrasH color={COLOR.restaurante} ancho="11rem"
              filas={p.marcas.map((m) => ({
                etiqueta: m.nom, valor: m.locales,
                pie: m.cambio_pct == null ? "" : `· clientes en 2028 ${pct(m.cambio_pct)}`,
              }))} />
            <p className="mt-2 text-[11px] text-[#52514e]">
              Es el rótulo, no la empresa: el censo de la ciudad no trae CIF ni razón social.
            </p>
          </Tarjeta>
        </Seccion>

        <Seccion color={COLOR.restaurante} titulo="Los 5 locales que más ganan en 2028">
          <Tarjeta titulo="Clientes potenciales por noche: turistas alojados a menos de 200 m">
            <ol className="space-y-2 text-[13px]">
              {p.locales_top.map((l, i) => (
                <li key={`${l.nom}-${i}`} className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3">
                  <div className="min-w-0">
                    <p className="truncate font-medium">{l.nom ?? "Sin nombre"}</p>
                    <p className="truncate text-[11px] text-[#52514e]">{l.tipo} · {l.barrio}</p>
                    <span className="mt-1 block h-2 rounded bg-[#eeece7]">
                      <span className="block h-full rounded" style={{ width: `${((l.en_2028 - l.hoy) / maxLocal) * 100}%`, background: "#7aa885" }} />
                    </span>
                  </div>
                  <p className="text-right tabular-nums">
                    <b style={{ color: "#3f7a4b" }}>+{n(Math.round(l.en_2028 - l.hoy))}</b>
                    <span className="block text-[11px] text-[#52514e]">{n(Math.round(l.hoy))} → {n(Math.round(l.en_2028))}</span>
                  </p>
                </li>
              ))}
            </ol>
          </Tarjeta>
        </Seccion>

        <Seccion color={COLOR.restaurante} titulo="Barrios, por clientes de turistas en 2028 (por noche)">
          <div className="grid gap-3 lg:grid-cols-2">
            <Tarjeta titulo="Los 5 que más ganan">
              <BarrasDivergentes filas={mas} />
            </Tarjeta>
            <Tarjeta titulo="Los 5 que menos ganan">
              <BarrasDivergentes filas={menos} />
            </Tarjeta>
          </div>
          <p className="mt-2 text-[11px] text-[#52514e]">
            Clientes que hoy duermen a menos de 200 m. El turista de piso cuenta la mitad hoy y entero en 2028.{" "}
            <Link href="/fuentes" className="underline underline-offset-2">Supuestos →</Link>
          </p>
        </Seccion>
      </div>
    </main>
  );
}
