"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useState } from "react";

import { ESCENARIOS, type BarrioSustitucion, type IdEscenario, type Sustitucion } from "@/app/lib/tipos";
import type { Medida } from "@/app/components/MapaBarrios";

// Leaflet toca `window` al cargarse: sin esto el render del servidor revienta.
const MapaBarrios = dynamic(() => import("@/app/components/MapaBarrios"), {
  ssr: false,
  loading: () => <div className="h-full w-full bg-[#f5f4f1]" />,
});

const MEDIDAS: { id: Medida; etiqueta: string; ayuda: string }[] = [
  { id: "saldo", etiqueta: "Saldo del barrio", ayuda: "Plazas que llegan menos las que se van" },
  { id: "sin_sitio", etiqueta: "Sin sitio", ayuda: "Plazas que no encuentran hotel en la ciudad" },
  { id: "se_quedan", etiqueta: "Se quedan", ayuda: "Plazas que encuentran hotel en su propio barrio" },
];

export default function Pagina() {
  const [geojson, setGeojson] = useState<GeoJSON.FeatureCollection | null>(null);
  const [sustitucion, setSustitucion] = useState<Sustitucion | null>(null);
  const [escenario, setEscenario] = useState<IdEscenario>("equilibrio");
  const [medida, setMedida] = useState<Medida>("saldo");
  const [barrio, setBarrio] = useState<string | null>(null);

  useEffect(() => {
    fetch("/data/geo/barrios.geojson").then((r) => r.json()).then(setGeojson);
    fetch("/data/mapa/sustitucion_2028.json").then((r) => r.json()).then(setSustitucion);
  }, []);

  const porBarrio = useMemo(() => {
    const filas = sustitucion?.escenarios[escenario] ?? [];
    return Object.fromEntries(filas.map((f) => [f.barrio, f])) as Record<string, BarrioSustitucion>;
  }, [sustitucion, escenario]);

  const totales = sustitucion?.totales.find((t) => t.escenario === escenario);
  const activo = barrio ? porBarrio[barrio] : null;
  const indice = ESCENARIOS.findIndex((e) => e.id === escenario);

  return (
    <main className="flex h-dvh w-full flex-col bg-[#faf9f7] text-[#24231f] lg:flex-row">
      <aside className="w-full shrink-0 overflow-y-auto border-b border-[#e3e0da] bg-white p-5 lg:w-[340px] lg:border-r lg:border-b-0">
        <h1 className="text-[15px] font-semibold tracking-tight">Barcelona sin pisos turísticos</h1>
        <p className="mt-1 text-xs text-[#52514e]">
          Dónde se alojarían los turistas de las 6.834 viviendas de uso turístico anunciadas en
          Airbnb cuando la licencia desaparezca en 2028.
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
          aria-label="Peso entre precio y barrio"
        />
        <div className="flex justify-between text-[11px] text-[#52514e]">
          <span>Su precio</span>
          <span>Su barrio</span>
        </div>
        <p className="mt-2 text-sm font-medium">{ESCENARIOS[indice].etiqueta}</p>

        {totales && (
          <dl className="mt-4 grid grid-cols-2 gap-x-3 gap-y-2 text-sm">
            <Dato titulo="Se mueven" valor={`${totales.km_mediano} km`} />
            <Dato titulo="Pagan de más" valor={`${totales.sobrecoste_mediano} €`} />
            <Dato titulo="Sin sitio" valor={totales.plazas_sin_sitio.toLocaleString("es")} />
            <Dato titulo="Hoteles usados" valor={totales.hoteles_usados.toLocaleString("es")} />
          </dl>
        )}

        <p className="mt-3 border-l-2 border-[#e3e0da] pl-3 text-[11px] leading-relaxed text-[#52514e]">
          Este peso <strong>no está medido</strong>: lo eliges tú. Un turista alemán y uno andaluz no
          tienen la misma sensibilidad al precio, y ningún dato disponible los distingue.
        </p>

        <h2 className="mt-6 mb-2 text-[11px] font-semibold uppercase tracking-wider text-[#52514e]">
          Qué pinta el mapa
        </h2>
        <div className="flex flex-col gap-1">
          {MEDIDAS.map((m) => (
            <label key={m.id} className="flex cursor-pointer items-baseline gap-2 py-1 text-sm">
              <input
                type="radio"
                name="medida"
                checked={medida === m.id}
                onChange={() => setMedida(m.id)}
                className="accent-[#2f6fb5]"
              />
              <span>
                {m.etiqueta}
                <span className="block text-[11px] text-[#52514e]">{m.ayuda}</span>
              </span>
            </label>
          ))}
        </div>

        {activo && (
          <div className="mt-6 rounded border border-[#e3e0da] bg-[#faf9f7] p-3">
            <h3 className="text-sm font-semibold">{activo.barrio}</h3>
            <dl className="mt-2 space-y-1 text-[13px]">
              <Linea titulo="Plazas que se van" valor={activo.salen} />
              <Linea titulo="Se quedan en el barrio" valor={activo.se_quedan} />
              <Linea titulo="Llegan de otros barrios" valor={activo.llegan} />
              <Linea titulo="Sin sitio en la ciudad" valor={activo.sin_sitio} />
            </dl>
            <button
              onClick={() => setBarrio(null)}
              className="mt-3 text-[11px] text-[#52514e] underline underline-offset-2"
            >
              quitar selección
            </button>
          </div>
        )}

        {totales && (
          <p className="mt-6 border-t border-[#e3e0da] pt-4 text-[11px] leading-relaxed text-[#52514e]">
            Los hoteles no están vacíos: se descuenta una ocupación del{" "}
            <strong>{(totales.ocupacion_partida * 100).toFixed(0)}%</strong>, media de los últimos
            doce meses del INE. Quedan {(totales.plazas_regladas * (1 - totales.ocupacion_partida)).toLocaleString("es", { maximumFractionDigits: 0 })}{" "}
            plazas libres para {totales.plazas_vut.toLocaleString("es")}, así que{" "}
            <strong>{totales.plazas_sin_sitio.toLocaleString("es")} no caben</strong> en ningún
            escenario.
          </p>
        )}
      </aside>

      <div className="min-h-[50vh] flex-1">
        <MapaBarrios
          geojson={geojson}
          datos={porBarrio}
          medida={medida}
          barrioActivo={barrio}
          onBarrio={setBarrio}
        />
      </div>
    </main>
  );
}

function Dato({ titulo, valor }: { titulo: string; valor: string }) {
  return (
    <div>
      <dt className="text-[11px] text-[#52514e]">{titulo}</dt>
      <dd className="text-base font-semibold tabular-nums">{valor}</dd>
    </div>
  );
}

function Linea({ titulo, valor }: { titulo: string; valor: number }) {
  return (
    <div className="flex justify-between gap-3">
      <dt className="text-[#52514e]">{titulo}</dt>
      <dd className="tabular-nums font-medium">{valor.toLocaleString("es")}</dd>
    </div>
  );
}
