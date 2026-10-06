"use client";

import { useEffect, useState } from "react";

import { BarrasH, Cifra, Matriz, Seccion, Tarjeta } from "@/app/components/Graficos";
import { COLOR, OSCURO, n } from "@/app/lib/tiposMapa";

type Turistas = {
  ine: {
    periodo: string; viajeros: number; pernoctaciones: number; estancia_media: number;
    extranjeros_pct: number; pernoctaciones_por_noche: number;
  };
  dataset: {
    hoteles_noche: number; hoteles_pernoctaciones_ano: number; pisos_noche: [number, number];
    pisos_pernoctaciones_ano: [number, number]; estancia_pisos: number;
    pisos_turistas_ano: [number, number]; nuevos_noche: number; hoteles_frente_a_ine_pct: number;
    hoteles_viajeros_equivalentes: number;
  };
};

type Flujo = {
  turistas: number;
  km: { mediana: number; media: number; p90: number; maximo: number; mas_de_2km_pct: number };
  distancia: { desde: number; hasta: number | null; pct: number }[];
  bandas: { etiquetas: string[]; matriz: number[][]; su_banda_pct: number; una_mas_pct: number; dos_o_mas_pct: number };
};

const millones = (v: number, d = 1) => (v / 1e6).toLocaleString("es", { maximumFractionDigits: d });
const dec = (v: number, d = 2) => v.toLocaleString("es", { maximumFractionDigits: d });

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
  // Por noche y con nuestros propios datos: ni la estancia ni el INE intervienen.
  const pctPisos = d.pisos_noche.map((p) => (p / (p + d.hoteles_noche)) * 100);

  return (
    <main className="min-h-full bg-[#faf9f7] text-[#24231f]">
      <div className="mx-auto max-w-6xl px-5 py-8 sm:px-8">
        <Seccion color={COLOR.piso} titulo="Adónde van los turistas de los pisos">
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <Cifra valor={`${dec(f.km.mediana)} km`} etiqueta="distancia mediana" color={OSCURO.piso} />
            <Cifra valor={`${dec(f.km.media)} km`} etiqueta="distancia media" color={OSCURO.piso} />
            <Cifra valor={`${dec(f.km.p90, 1)} km`} etiqueta="el 90 % llega a menos de" color={OSCURO.piso} />
            <Cifra valor={`${dec(f.km.mas_de_2km_pct, 1)} %`} etiqueta="recorre más de 2 km"
              pie={`máximo ${dec(f.km.maximo, 1)} km`} color={OSCURO.piso} />
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
        </Seccion>

        <Seccion color="#24231f" titulo="Viajeros: el INE frente a nuestros datos">
          <div className="grid gap-3 lg:grid-cols-[2fr_1fr]">
            <Tarjeta titulo="Viajeros al año">
              <BarrasH max={ine.viajeros} formato={(v) => `${millones(v)} M`} filas={[
                { etiqueta: "Hoteles · INE", valor: ine.viajeros, color: COLOR.hotel },
                { etiqueta: "Hoteles · nuestros", valor: d.hoteles_viajeros_equivalentes, color: COLOR.hotel,
                  pie: `a ${dec(ine.estancia_media)} noches` },
                { etiqueta: "Pisos · nuestros", valor: (d.pisos_turistas_ano[0] + d.pisos_turistas_ano[1]) / 2, color: COLOR.piso,
                  pie: `(${millones(d.pisos_turistas_ano[0])}–${millones(d.pisos_turistas_ano[1])} M a ${d.estancia_pisos} noches)` },
              ]} />
            </Tarjeta>
            <Cifra
              valor={`${n(Math.round(pctPisos[0]))}–${n(Math.round(pctPisos[1]))} %`}
              etiqueta="de los turistas se alojan en pisos, según nuestro dataset"
              pie="por noche, en hoteles y pisos de este análisis"
              color={OSCURO.piso} />
          </div>
        </Seccion>
      </div>
    </main>
  );
}
