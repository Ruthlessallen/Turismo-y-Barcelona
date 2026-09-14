"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { ESCENARIOS, type IdEscenario } from "@/app/lib/tipos";
import type { Centroides, Flujo } from "@/app/components/MapaFlujos";

const MapaFlujos = dynamic(() => import("@/app/components/MapaFlujos"), {
  ssr: false,
  loading: () => <div className="h-full w-full bg-[#f5f4f1]" />,
});

type Datos = { centroides: Centroides; escenarios: Record<string, Flujo[]> };

export default function PaginaFlujos() {
  const [geojson, setGeojson] = useState<GeoJSON.FeatureCollection | null>(null);
  const [datos, setDatos] = useState<Datos | null>(null);
  const [escenario, setEscenario] = useState<IdEscenario>("equilibrio");
  const [barrio, setBarrio] = useState<string | null>(null);
  const [minimo, setMinimo] = useState(100);

  useEffect(() => {
    fetch("/data/geo/barrios.geojson").then((r) => r.json()).then(setGeojson);
    fetch("/data/mapa/flujos_2028.json").then((r) => r.json()).then(setDatos);
  }, []);

  const flujos = useMemo(() => datos?.escenarios[escenario] ?? [], [datos, escenario]);
  const indice = ESCENARIOS.findIndex((e) => e.id === escenario);

  const delBarrio = useMemo(() => {
    if (!barrio) return null;
    const salen = flujos.filter((f) => f.origen === barrio);
    const llegan = flujos.filter((f) => f.destino === barrio);
    return {
      salen: salen.reduce((s, f) => s + f.turistas, 0),
      llegan: llegan.reduce((s, f) => s + f.turistas, 0),
      destinos: [...salen].sort((a, b) => b.turistas - a.turistas).slice(0, 5),
    };
  }, [flujos, barrio]);

  const visibles = flujos.filter(
    (f) => f.turistas >= minimo && (!barrio || f.origen === barrio || f.destino === barrio),
  );

  return (
    <main className="flex h-dvh w-full flex-col bg-[#faf9f7] text-[#24231f] lg:flex-row">
      <aside className="w-full shrink-0 overflow-y-auto border-b border-[#e3e0da] bg-white p-5 lg:w-[330px] lg:border-r lg:border-b-0">
        <Link href="/" className="text-[11px] text-[#52514e] underline underline-offset-2">
          ← mapa de barrios
        </Link>
        <h1 className="mt-3 text-[15px] font-semibold tracking-tight">Adónde se van</h1>
        <p className="mt-1 text-xs leading-relaxed text-[#52514e]">
          Cada flecha es un movimiento de turistas entre dos barrios: salen del barrio donde estaba
          su piso y acaban durmiendo donde queda sitio.
        </p>
        <p className="mt-2 rounded border-l-2 border-[#d8d5cf] bg-[#faf9f7] px-3 py-2 text-[11px] leading-relaxed text-[#52514e]">
          Solo se mueven los <strong>30.067 turistas de las 6.834 viviendas anunciadas hoy en
          Airbnb</strong>. El registro oficial tiene 24.075 licencias con 61.899 plazas: las que no
          se anuncian en Airbnb no están en este mapa.
        </p>

        <h2 className="mt-6 mb-2 text-[11px] font-semibold uppercase tracking-wider text-[#52514e]">
          ¿Qué busca el turista?
        </h2>
        <input
          type="range"
          min={0}
          max={ESCENARIOS.length - 1}
          step={1}
          value={indice}
          onChange={(e) => setEscenario(ESCENARIOS[Number(e.target.value)].id)}
          className="w-full accent-[#2f6fb5]"
          aria-label="Peso entre precio y ubicación"
        />
        <div className="flex justify-between text-[11px] text-[#52514e]">
          <span>Precio</span>
          <span>Ubicación</span>
        </div>

        <h2 className="mt-6 mb-1 text-[11px] font-semibold uppercase tracking-wider text-[#52514e]">
          Flechas de más de {minimo} turistas
        </h2>
        <input
          type="range"
          min={20}
          max={500}
          step={20}
          value={minimo}
          onChange={(e) => setMinimo(Number(e.target.value))}
          className="w-full accent-[#2f6fb5]"
          aria-label="Tamaño mínimo del flujo"
        />
        <p className="text-[11px] text-[#52514e]">
          {visibles.length} de {flujos.length} movimientos a la vista
        </p>

        {delBarrio ? (
          <div className="mt-6 rounded border border-[#e3e0da] bg-[#faf9f7] p-3">
            <h3 className="text-sm font-semibold">{barrio}</h3>
            <div className="mt-2 flex gap-4 text-[13px]">
              <div>
                <span className="block text-[10px] text-[#52514e]">se van</span>
                <span className="font-semibold tabular-nums text-[#cf4a30]">
                  {delBarrio.salen.toLocaleString("es")}
                </span>
              </div>
              <div>
                <span className="block text-[10px] text-[#52514e]">llegan</span>
                <span className="font-semibold tabular-nums text-[#2f6fb5]">
                  {delBarrio.llegan.toLocaleString("es")}
                </span>
              </div>
            </div>
            {delBarrio.destinos.length > 0 && (
              <>
                <h4 className="mt-3 text-[10px] uppercase tracking-wider text-[#52514e]">
                  Se van sobre todo a
                </h4>
                <ul className="mt-1 space-y-0.5 text-[12px]">
                  {delBarrio.destinos.map((d) => (
                    <li key={d.destino} className="flex justify-between gap-2">
                      <span>{d.destino}</span>
                      <span className="tabular-nums font-medium">
                        {d.turistas.toLocaleString("es")}
                      </span>
                    </li>
                  ))}
                </ul>
              </>
            )}
            <button
              onClick={() => setBarrio(null)}
              className="mt-3 text-[11px] text-[#52514e] underline underline-offset-2"
            >
              ver todos los movimientos
            </button>
          </div>
        ) : (
          <p className="mt-6 text-[12px] text-[#52514e]">
            Pincha un barrio para aislar sus movimientos.
          </p>
        )}

        <div className="mt-6 space-y-1.5 border-t border-[#e3e0da] pt-4 text-[11px] text-[#52514e]">
          {barrio ? (
            <>
              <p className="flex items-center gap-2">
                <span className="inline-block h-1.5 w-7 shrink-0 rounded-full bg-[#cf4a30]" />
                se van de {barrio}
              </p>
              <p className="flex items-center gap-2">
                <span className="inline-block h-1.5 w-7 shrink-0 rounded-full bg-[#2f6fb5]" />
                llegan a {barrio}
              </p>
            </>
          ) : (
            <p className="flex items-center gap-2">
              <span className="inline-block h-1.5 w-7 shrink-0 rounded-full bg-[#8a8783]" />
              todos los movimientos. <strong>Pincha un barrio</strong> y se separan en rojo los que
              se van y azul los que llegan.
            </p>
          )}
          <p className="pt-1 leading-relaxed">
            El grosor es el número de turistas. Los movimientos dentro del mismo barrio no se
            dibujan: no hay desplazamiento que enseñar.
          </p>
        </div>
      </aside>

      <div className="min-h-[55vh] flex-1">
        <MapaFlujos
          geojson={geojson}
          flujos={flujos}
          centroides={datos?.centroides ?? {}}
          barrioActivo={barrio}
          onBarrio={setBarrio}
          minimo={minimo}
        />
      </div>
    </main>
  );
}
