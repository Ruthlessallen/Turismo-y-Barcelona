"use client";

import { useEffect, useState } from "react";

import { COLOR, n } from "@/app/lib/tiposMapa";

/** Lo que publica `export_mapa_limpio.py` en `dashboard.json`. */
type Dashboard = {
  hoteles: {
    total: number; habitaciones: number; plazas: number;
    bandas: Record<string, number>;
    titulares: { nom: string; n: number }[];
    turistas_nuevos: number; turistas_nuevos_pct: number;
  };
  pisos: {
    anuncios_barridos: number; total: number; habitaciones: number; plazas: number;
    facturacion: [number, number];
  };
};

/** 222 millones: lo que se lee de un vistazo. */
const millones = (v: number) => (v / 1e6).toLocaleString("es", { maximumFractionDigits: 0 });

export default function Portada() {
  const [d, setD] = useState<Dashboard | null>(null);

  useEffect(() => {
    fetch("/data/mapa/dashboard.json").then((r) => r.json()).then(setD);
  }, []);

  if (!d) return <main className="min-h-full bg-[#faf9f7]" />;
  const { hoteles: h, pisos: p } = d;
  const totalBandas = Object.values(h.bandas).reduce((a, b) => a + b, 0);

  return (
    <main className="min-h-full bg-[#faf9f7] text-[#24231f]">
      <div className="mx-auto max-w-6xl px-5 py-8 sm:px-8">
        <Seccion color={COLOR.hotel} titulo="Hoteles">
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <Cifra valor={n(h.total)} etiqueta="hoteles" />
            <Cifra valor={n(h.habitaciones)} etiqueta="habitaciones" />
            <Cifra valor={n(h.plazas)} etiqueta="plazas" />
            <Cifra valor={`+${h.turistas_nuevos_pct.toLocaleString("es")} %`}
              etiqueta="turistas nuevos tras 2028" destacada color={COLOR.hotel}
              pie={`${n(h.turistas_nuevos)} por noche`} />
          </div>

          <div className="mt-3 grid gap-3 lg:grid-cols-2">
            <Tarjeta titulo="Bandas económicas">
              <div className="flex h-7 overflow-hidden rounded text-[12px] font-semibold text-white">
                {Object.entries(h.bandas).map(([banda, cuantos], i) => (
                  <div key={banda} className="flex items-center justify-center"
                    style={{ width: `${(cuantos / totalBandas) * 100}%`,
                      background: ["#9dbbdc", "#6f9fd0", "#1f5fa8", "#123a6b"][i] }}>
                    {cuantos / totalBandas > 0.08 && banda}
                  </div>
                ))}
              </div>
              <ul className="mt-2 flex justify-between text-[13px] tabular-nums">
                {Object.entries(h.bandas).map(([banda, cuantos]) => (
                  <li key={banda}><b>{n(cuantos)}</b> <span className="text-[#52514e]">{banda}</span></li>
                ))}
              </ul>
            </Tarjeta>

            <Tarjeta titulo="Titulares con más hoteles">
              <ol className="space-y-1 text-[13px]">
                {h.titulares.map((t) => (
                  <li key={t.nom} className="flex justify-between gap-3">
                    <span className="truncate">{t.nom}</span>
                    <b className="tabular-nums">{t.n}</b>
                  </li>
                ))}
              </ol>
            </Tarjeta>
          </div>
        </Seccion>

        <Seccion color={COLOR.piso} titulo="Airbnb">
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <Cifra valor={n(p.total)} etiqueta="pisos" pie={`de ${n(p.anuncios_barridos)} anuncios`} />
            <Cifra valor={n(p.habitaciones)} etiqueta="habitaciones" />
            <Cifra valor={n(p.plazas)} etiqueta="plazas" />
            <Cifra valor={`${millones(p.facturacion[0])}–${millones(p.facturacion[1])} M€`}
              etiqueta="al año" pie="aproximado" destacada color={COLOR.piso} />
          </div>
        </Seccion>
      </div>
    </main>
  );
}

function Seccion({ color, titulo, children }: {
  color: string; titulo: string; children: React.ReactNode;
}) {
  return (
    <section className="mb-8">
      <h2 className="mb-3 flex items-center gap-2 text-[11px] font-semibold tracking-wider text-[#52514e] uppercase">
        <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: color }} />
        {titulo}
      </h2>
      {children}
    </section>
  );
}

function Cifra({ valor, etiqueta, pie, destacada, color }: {
  valor: string; etiqueta: string; pie?: string; destacada?: boolean; color?: string;
}) {
  return (
    <div className="rounded border border-[#e3e0da] bg-white p-4"
      style={destacada ? { borderColor: color, borderWidth: 2 } : undefined}>
      <p className="text-[30px] leading-none font-semibold tabular-nums">{valor}</p>
      <p className="mt-1.5 text-[13px] font-medium">{etiqueta}</p>
      {pie && <p className="mt-0.5 text-[11px] text-[#52514e]">{pie}</p>}
    </div>
  );
}

function Tarjeta({ titulo, children }: { titulo: string; children: React.ReactNode }) {
  return (
    <div className="rounded border border-[#e3e0da] bg-white p-4">
      <p className="mb-2 text-[12px] font-medium">{titulo}</p>
      {children}
    </div>
  );
}
