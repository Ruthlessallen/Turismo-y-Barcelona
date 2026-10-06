"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { BarrasH } from "@/app/components/Graficos";

type Parte = { etiqueta: string; anuncios: number };

type Paso = {
  clave: string;
  titulo: string;
  porque: string;
  descartados: number;
  plazas_descartadas: number;
  quedan: number;
  plazas_restantes: number;
  desglose: Parte[];
};

type Criba = { inicio: { anuncios: number; plazas: number }; partida: Parte[]; pasos: Paso[] };

type Licencias = {
  registro: { licencias: number; plazas: number };
  con_anuncio: { licencias: number; plazas: number };
  solo_descartados: { licencias: number; plazas: number };
  sin_anuncio: { licencias: number; plazas: number };
  casadas: { anuncios: number; plazas_airbnb: number; plazas_registro: number };
  pisos_estado: { con_registro: { pisos: number; plazas: number } };
  registro_detalle: {
    mediana_plazas: number; hutb_maximo: number; expediente_desde: number; licencias_2012_2014: number;
    por_distrito: { distrito: string; licencias: number }[];
    vigor: { trimestre_inicial: string; inicial: number; trimestre_minimo: string; minimo: number;
      trimestre_ultimo: string; ultimo: number };
  };
};

// `toLocaleString("es")` deja 2390 sin punto: el español no agrupa los números de cuatro cifras.
const n = (v: number) => v.toLocaleString("es", { useGrouping: "always" });
const trimestre = (t: string) => `${t.slice(5, 7)} de ${t.slice(0, 4)}`;

/** Naranjas: es la página de Airbnb. */
const NARANJA = "#e8710a";
const OSCURO = "#a84a00";
const CLARO = "#fbe3cc";

export default function PaginaAirbnb() {
  const [criba, setCriba] = useState<Criba | null>(null);
  const [lic, setLic] = useState<Licencias | null>(null);
  const [paso, setPaso] = useState(0);

  useEffect(() => {
    fetch("/data/mapa/criba_airbnb.json").then((r) => r.json()).then(setCriba);
    fetch("/data/mapa/licencias.json").then((r) => r.json()).then(setLic);
  }, []);

  // Tarjetas: la de partida, un descarte cada una, «lo que no vemos» y el registro por distrito.
  const ultimo = criba?.pasos.length ?? 0;
  const sinAnuncio = ultimo + 1;
  const fin = ultimo + 2;
  const mover = useCallback(
    (delta: number) => setPaso((p) => Math.min(Math.max(p + delta, 0), fin)),
    [fin],
  );

  useEffect(() => {
    const alPulsar = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight") mover(1);
      if (e.key === "ArrowLeft") mover(-1);
    };
    window.addEventListener("keydown", alPulsar);
    return () => window.removeEventListener("keydown", alPulsar);
  }, [mover]);

  const estado = useMemo(() => {
    if (!criba) return null;
    const k = Math.min(paso, criba.pasos.length);
    if (k === 0) return { quedan: criba.inicio.anuncios, plazas: criba.inicio.plazas, actual: null };
    const p = criba.pasos[k - 1];
    return { quedan: p.quedan, plazas: p.plazas_restantes, actual: p };
  }, [criba, paso]);

  if (!criba || !estado || !lic) return <main className="min-h-full bg-[#faf9f7]" />;

  const total = criba.inicio.anuncios;
  const descartados = total - estado.quedan;
  const viviendas = criba.pasos[ultimo - 1].quedan;
  const r = lic.registro_detalle;

  return (
    <main className="flex min-h-full w-full flex-col bg-[#faf9f7] text-[#24231f] sm:h-full sm:overflow-hidden">
      <header className="shrink-0 px-5 pt-5 sm:px-8">
        <div className="mx-auto max-w-4xl">
          <h1 className="text-[17px] font-semibold tracking-tight">
            De {n(total)} anuncios de Airbnb a {n(viviendas)} viviendas con registro
          </h1>
          <p className="mt-0.5 text-[12px] text-[#52514e]">
            Los {n(total)} anuncios son todos los que Airbnb publicaba en Barcelona el 24 de junio de
            2026 (volcado de Inside Airbnb).
          </p>
        </div>
      </header>

      <div className="mx-auto flex w-full max-w-4xl min-h-0 flex-1 flex-col gap-4 px-5 py-5 sm:px-8">
        <section className="shrink-0">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-wider text-[#52514e]">Siguen en el análisis</p>
              <p className="text-[44px] leading-none font-semibold tabular-nums" style={{ color: OSCURO }}>{n(estado.quedan)}</p>
              <p className="mt-1 text-[13px] text-[#52514e]">anuncios, con {n(estado.plazas)} plazas</p>
            </div>
            <div className="text-right">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-[#52514e]">Descartados hasta aquí</p>
              <p className="text-[26px] leading-none font-semibold tabular-nums text-[#52514e]">{n(descartados)}</p>
              <p className="mt-1 text-[13px] text-[#52514e]">
                anuncios: el {((descartados / total) * 100).toFixed(0)} % de los {n(total)}
              </p>
            </div>
          </div>
          <div className="mt-3 flex h-3 overflow-hidden rounded-sm" style={{ background: CLARO }}>
            <div className="transition-all duration-300" style={{ width: `${(estado.quedan / total) * 100}%`, background: NARANJA }} />
          </div>
          <p className="mt-1.5 flex flex-wrap gap-x-4 text-[11px] text-[#52514e]">
            <span><i className="mr-1 inline-block h-2 w-2 rounded-sm" style={{ background: NARANJA }} />siguen en el análisis</span>
            <span><i className="mr-1 inline-block h-2 w-2 rounded-sm" style={{ background: CLARO }} />descartados</span>
          </p>
        </section>

        {/* Una tarjeta cada vez, de tamaño fijo: si el contenido no cabe, scrollea ella sola. */}
        <section className="flex shrink-0 flex-col rounded border border-[#e3e0da] bg-white sm:h-[min(520px,62dvh)]">
          <div className="flex min-h-0 flex-1 flex-col overflow-y-auto px-6 py-5 sm:px-10">
            <div className="my-auto">
              {paso === fin ? (
                <>
                  <Etiqueta>El registro oficial · Open Data BCN</Etiqueta>
                  <Titulo>Licencias por distrito</Titulo>
                  <Cifra>{n(lic.registro.licencias)} licencias · {n(lic.registro.plazas)} plazas · mediana de {n(r.mediana_plazas)} por licencia</Cifra>
                  <div className="mt-3 max-w-xl">
                    <BarrasH color={NARANJA} filas={r.por_distrito.map((d) => ({ etiqueta: d.distrito, valor: d.licencias }))} />
                  </div>
                  <ul className="mt-3 max-w-xl space-y-0.5 text-[12px] leading-snug text-[#3a3935]">
                    <li><b>En vigor:</b> {n(r.vigor.inicial)} ({trimestre(r.vigor.trimestre_inicial)}) → {n(r.vigor.minimo)} ({trimestre(r.vigor.trimestre_minimo)}, el mínimo) → <b>{n(r.vigor.ultimo)}</b> ({trimestre(r.vigor.trimestre_ultimo)}).</li>
                    <li><b>Desde cuándo:</b> el expediente más antiguo es de {r.expediente_desde}; {n(r.licencias_2012_2014)} son de 2012–2014 (año de solicitud, no de alta). Número más alto emitido: HUTB-{String(r.hutb_maximo)}.</li>
                  </ul>
                </>
              ) : paso === sinAnuncio ? (
                <>
                  <Etiqueta>Lo que no vemos · faltan datos</Etiqueta>
                  <Titulo>{n(lic.sin_anuncio.licencias)} licencias sin ningún anuncio</Titulo>
                  <Cifra>{n(lic.sin_anuncio.plazas)} plazas · la mitad de las del registro</Cifra>
                  <div className="mt-4 max-w-xl">
                    <BarrasH color={NARANJA} ancho="14rem" max={lic.registro.plazas} filas={[
                      { etiqueta: `En los ${n(lic.pisos_estado.con_registro.pisos)} pisos`, valor: lic.con_anuncio.plazas, color: NARANJA },
                      { etiqueta: "Solo con anuncios descartados", valor: lic.solo_descartados.plazas, color: "#f3ad62" },
                      { etiqueta: "Sin ningún anuncio", valor: lic.sin_anuncio.plazas, color: "#b9b5ae" },
                    ]} />
                    <p className="mt-1 text-[11px] text-[#52514e]">Plazas del registro oficial ({n(lic.registro.plazas)} en total).</p>
                  </div>
                  <p className="mt-3 max-w-xl text-[13px] leading-relaxed text-[#3a3935]">
                    De ellas no sabemos nada: pueden estar en otra plataforma, dormidas o sin uso. Aquí no cuentan; si
                    todas estuvieran activas serían hasta <b>{n(lic.sin_anuncio.plazas)} plazas más</b>. En los pisos que
                    casan con una licencia, Airbnb declara {n(lic.casadas.plazas_airbnb)} plazas y el registro {n(lic.casadas.plazas_registro)}.
                  </p>
                </>
              ) : (
                <>
                  <Etiqueta>{estado.actual ? `Descarte ${paso} de ${ultimo}` : "El punto de partida"}</Etiqueta>
                  <Titulo>{estado.actual ? estado.actual.titulo : "Todo lo que Airbnb anunciaba el 24 de junio de 2026"}</Titulo>
                  {estado.actual ? (
                    <Cifra>−{n(estado.actual.descartados)} anuncios · {n(estado.actual.plazas_descartadas)} plazas</Cifra>
                  ) : (
                    <Cifra>{n(total)} anuncios · {n(criba.inicio.plazas)} plazas</Cifra>
                  )}
                  <p className="mt-2 max-w-xl text-[14px] leading-relaxed text-[#3a3935]">
                    {estado.actual ? estado.actual.porque
                      : "No todo esto es lo que la ley elimina en 2028. Un anuncio puede fallar varias condiciones y solo se cuenta en la primera: el orden va de lo estructural a lo circunstancial."}
                  </p>
                  <p className="mt-3 mb-1.5 text-[12px] font-medium">
                    {estado.actual ? "Cómo se reparten los descartados" : "Qué tipo de anuncio es"}
                  </p>
                  <div className="max-w-xl">
                    <BarrasH color={NARANJA} ancho="14rem" filas={(estado.actual ? estado.actual.desglose : criba.partida)
                      .map((d) => ({ etiqueta: d.etiqueta, valor: d.anuncios }))} />
                  </div>
                  {paso === ultimo && (
                    <p className="mt-3 max-w-xl rounded border-l-2 bg-[#faf9f7] px-4 py-2 text-[12px] leading-relaxed text-[#52514e]" style={{ borderColor: NARANJA }}>
                      Quedan <b>{n(estado.quedan)} viviendas</b> y sus <b>{n(estado.plazas)} plazas</b>. No son todas las
                      licencias de Barcelona: mira las dos últimas tarjetas.
                    </p>
                  )}
                </>
              )}
            </div>
          </div>

          <div className="flex shrink-0 items-center justify-between gap-4 border-t border-[#e3e0da] px-4 py-3">
            <Flecha alPulsar={() => mover(-1)} desactivada={paso === 0} etiqueta="Anterior">‹</Flecha>
            <div className="flex items-center gap-1.5">
              {Array.from({ length: fin + 1 }, (_, i) => (
                <button key={i} onClick={() => setPaso(i)} aria-current={paso === i}
                  aria-label={i === 0 ? "El punto de partida" : i === sinAnuncio ? "Lo que no vemos" : i === fin ? "Licencias por distrito" : `Descarte ${i}`}
                  className={`h-2.5 rounded-full transition-all ${paso === i ? "w-6 bg-[#24231f]" : "w-2.5 hover:opacity-80"}`}
                  style={paso === i ? undefined : { background: i < paso ? NARANJA : "#ddd9d2" }} />
              ))}
            </div>
            <Flecha alPulsar={() => mover(1)} desactivada={paso === fin} etiqueta="Siguiente">›</Flecha>
          </div>
        </section>

        <div className="flex shrink-0 items-center justify-between gap-4 text-[11px] text-[#52514e]">
          <span>Usa las flechas del teclado, o pincha los puntos.</span>
          <Link href="/fuentes" className="underline underline-offset-2">de dónde sale cada cifra →</Link>
        </div>
      </div>
    </main>
  );
}

const Etiqueta = ({ children }: { children: React.ReactNode }) => (
  <p className="text-[11px] font-semibold uppercase tracking-wider" style={{ color: OSCURO }}>{children}</p>
);
const Titulo = ({ children }: { children: React.ReactNode }) => (
  <h2 className="mt-1.5 text-[22px] leading-tight font-semibold tracking-tight">{children}</h2>
);
const Cifra = ({ children }: { children: React.ReactNode }) => (
  <p className="mt-1 text-[15px] font-semibold tabular-nums" style={{ color: OSCURO }}>{children}</p>
);

function Flecha({ alPulsar, desactivada, etiqueta, children }: {
  alPulsar: () => void; desactivada: boolean; etiqueta: string; children: React.ReactNode;
}) {
  return (
    <button onClick={alPulsar} disabled={desactivada} aria-label={etiqueta}
      className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full border text-[20px] leading-none transition ${
        desactivada ? "cursor-not-allowed border-[#eeece7] text-[#d3cfc8]" : "border-[#e3e0da] text-[#24231f] hover:bg-[#f5f4f1]"}`}>
      {children}
    </button>
  );
}
