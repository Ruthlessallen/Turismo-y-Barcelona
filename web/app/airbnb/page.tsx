"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

type Paso = {
  clave: string;
  titulo: string;
  porque: string;
  descartados: number;
  plazas_descartadas: number;
  quedan: number;
  plazas_restantes: number;
};

type Criba = { inicio: { anuncios: number; plazas: number }; pasos: Paso[] };

// `toLocaleString("es")` deja 2390 sin punto: el español no agrupa los números de cuatro cifras.
// Aquí sí se agrupa siempre, porque estas cifras se leen unas junto a otras y «2390» al lado de
// «9.098» se lee como un número más pequeño de lo que es.
const n = (v: number) => v.toLocaleString("es", { useGrouping: "always" });

export default function PaginaAirbnb() {
  const [criba, setCriba] = useState<Criba | null>(null);
  const [paso, setPaso] = useState(0);

  useEffect(() => {
    fetch("/data/mapa/criba_airbnb.json").then((r) => r.json()).then(setCriba);
  }, []);

  const ultimo = criba?.pasos.length ?? 0;
  const mover = useCallback(
    (delta: number) => setPaso((p) => Math.min(Math.max(p + delta, 0), ultimo)),
    [ultimo],
  );

  // Las flechas del teclado mueven las tarjetas aunque el foco no esté en la barra: es el gesto
  // que espera quien está pasando tarjetas.
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
    if (paso === 0) {
      return { quedan: criba.inicio.anuncios, plazas: criba.inicio.plazas, actual: null };
    }
    const p = criba.pasos[paso - 1];
    return { quedan: p.quedan, plazas: p.plazas_restantes, actual: p };
  }, [criba, paso]);

  if (!criba || !estado) return <main className="min-h-full bg-[#faf9f7]" />;

  const total = criba.inicio.anuncios;
  const descartados = total - estado.quedan;
  const enElFinal = paso === ultimo;

  return (
    // Sin scroll de página a partir de tableta: la tarjeta se queda quieta y, si su texto no cabe,
    // scrollea ella sola. En móvil se deja fluir — forzar la altura ahí recorta el texto.
    <main className="flex min-h-full w-full flex-col bg-[#faf9f7] text-[#24231f] sm:h-full sm:overflow-hidden">
      <header className="shrink-0 px-5 pt-5 sm:px-8">
        <div className="mx-auto max-w-4xl">
          <h1 className="text-[17px] font-semibold tracking-tight">
            De 15.406 anuncios a 6.834 viviendas
          </h1>
        </div>
      </header>

      <div className="mx-auto flex w-full max-w-4xl min-h-0 flex-1 flex-col gap-4 px-5 py-5 sm:px-8">
        {/* Las cifras, arriba y siempre visibles: son lo que cambia al pasar cada tarjeta. */}
        <section className="shrink-0">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-wider text-[#52514e]">
                Quedan
              </p>
              <p className="text-[44px] leading-none font-semibold tabular-nums">
                {n(estado.quedan)}
              </p>
              <p className="mt-1 text-[13px] text-[#52514e]">
                anuncios · {n(estado.plazas)} plazas
              </p>
            </div>
            <div className="text-right">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-[#52514e]">
                Descartados
              </p>
              <p className="text-[26px] leading-none font-semibold tabular-nums text-[#cf4a30]">
                {n(descartados)}
              </p>
              <p className="mt-1 text-[13px] text-[#52514e]">
                {((descartados / total) * 100).toFixed(0)}% del volcado
              </p>
            </div>
          </div>

          <div className="mt-3 flex h-3 overflow-hidden rounded-sm bg-[#f0d9d2]">
            <div
              className="bg-[#2f6fb5] transition-all duration-300"
              style={{ width: `${(estado.quedan / total) * 100}%` }}
            />
          </div>
        </section>

        {/* Una tarjeta cada vez. El texto de por qué no compite con los otros cinco. */}
        <section className="flex min-h-0 flex-1 flex-col rounded border border-[#e3e0da] bg-white">
          <div className="flex min-h-0 flex-1 flex-col justify-center overflow-y-auto px-6 py-6 sm:px-10">
            {estado.actual ? (
              <>
                <p className="text-[11px] font-semibold uppercase tracking-wider text-[#52514e]">
                  Descarte {paso} de {ultimo}
                </p>
                <h2 className="mt-2 text-[22px] leading-tight font-semibold tracking-tight">
                  {estado.actual.titulo}
                </h2>
                <p className="mt-1 text-[15px] font-semibold tabular-nums text-[#cf4a30]">
                  −{n(estado.actual.descartados)} anuncios ·{" "}
                  {n(estado.actual.plazas_descartadas)} plazas
                </p>
                <p className="mt-3 max-w-xl text-[15px] leading-relaxed text-[#3a3935]">
                  {estado.actual.porque}
                </p>
                {enElFinal && (
                  <p className="mt-4 max-w-xl rounded border-l-2 border-[#d8d5cf] bg-[#faf9f7] px-4 py-3 text-[13px] leading-relaxed text-[#52514e]">
                    Lo que queda son las <strong>6.834 viviendas</strong> a las que la ley quita la
                    licencia, y sus <strong>30.067 plazas</strong> son los turistas que hay que
                    realojar. <strong>No son todas las de Barcelona:</strong> el registro oficial
                    tiene 24.075 licencias con 61.899 plazas, y aquí solo está lo anunciado en
                    Airbnb.
                  </p>
                )}
              </>
            ) : (
              <>
                <p className="text-[11px] font-semibold uppercase tracking-wider text-[#52514e]">
                  El punto de partida
                </p>
                <h2 className="mt-2 text-[22px] leading-tight font-semibold tracking-tight">
                  Todo lo que Airbnb anunciaba el 24 de junio de 2026
                </h2>
                <p className="mt-3 max-w-xl text-[15px] leading-relaxed text-[#3a3935]">
                  No todo esto es lo que la ley elimina en 2028. Pasa las tarjetas para ir
                  descartando lo que no cuenta, y por qué.
                </p>
                <p className="mt-3 max-w-xl text-[13px] leading-relaxed text-[#52514e]">
                  Un anuncio puede fallar varias condiciones a la vez y{" "}
                  <strong>solo se cuenta en la primera</strong>. Por eso el orden importa: va de lo
                  estructural —si la ley le alcanza— a lo circunstancial —si sigue vendiendo, si
                  está repetido—.
                </p>
              </>
            )}
          </div>

          <div className="flex shrink-0 items-center justify-between gap-4 border-t border-[#e3e0da] px-4 py-3">
            <Flecha alPulsar={() => mover(-1)} desactivada={paso === 0} etiqueta="Anterior">
              ‹
            </Flecha>

            {/* Los puntos hacen de índice: cuántas tarjetas hay y en cuál estás. */}
            <div className="flex items-center gap-1.5">
              {Array.from({ length: ultimo + 1 }, (_, i) => (
                <button
                  key={i}
                  onClick={() => setPaso(i)}
                  aria-label={i === 0 ? "El punto de partida" : `Descarte ${i}`}
                  aria-current={paso === i}
                  className={`h-2.5 rounded-full transition-all ${
                    paso === i
                      ? "w-6 bg-[#24231f]"
                      : i < paso
                        ? "w-2.5 bg-[#cf4a30]"
                        : "w-2.5 bg-[#ddd9d2] hover:bg-[#b9b5ae]"
                  }`}
                />
              ))}
            </div>

            <Flecha alPulsar={() => mover(1)} desactivada={enElFinal} etiqueta="Siguiente">
              ›
            </Flecha>
          </div>
        </section>

        <div className="flex shrink-0 items-center justify-between gap-4 text-[11px] text-[#52514e]">
          <span>Usa las flechas del teclado, o pincha los puntos.</span>
          <Link href="/fuentes" className="underline underline-offset-2">
            de dónde sale cada cifra →
          </Link>
        </div>
      </div>
    </main>
  );
}

function Flecha({
  alPulsar,
  desactivada,
  etiqueta,
  children,
}: {
  alPulsar: () => void;
  desactivada: boolean;
  etiqueta: string;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={alPulsar}
      disabled={desactivada}
      aria-label={etiqueta}
      className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full border text-[20px] leading-none transition ${
        desactivada
          ? "cursor-not-allowed border-[#eeece7] text-[#d3cfc8]"
          : "border-[#e3e0da] text-[#24231f] hover:bg-[#f5f4f1]"
      }`}
    >
      {children}
    </button>
  );
}
