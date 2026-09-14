"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { ESCENARIOS, type BarrioSustitucion, type IdEscenario, type Sustitucion } from "@/app/lib/tipos";
import type { Centroides, Flujo } from "@/app/lib/flechas";
import type { Medida } from "@/app/components/MapaBarrios";

type DatosFlujos = { centroides: Centroides; escenarios: Record<string, Flujo[]> };

// Leaflet toca `window` al cargarse: sin esto el render del servidor revienta.
const MapaBarrios = dynamic(() => import("@/app/components/MapaBarrios"), {
  ssr: false,
  loading: () => <div className="h-full w-full bg-[#f5f4f1]" />,
});

const VISTAS: { id: Medida; etiqueta: string }[] = [
  { id: "saldo", etiqueta: "Gana o pierde" },
  { id: "sin_sitio", etiqueta: "Sin sitio" },
];

export default function Pagina() {
  const [geojson, setGeojson] = useState<GeoJSON.FeatureCollection | null>(null);
  const [sustitucion, setSustitucion] = useState<Sustitucion | null>(null);
  const [escenario, setEscenario] = useState<IdEscenario>("equilibrio");
  const [medida, setMedida] = useState<Medida>("saldo");
  const [barrio, setBarrio] = useState<string | null>(null);
  const [flechas, setFlechas] = useState(false);
  const [minimoFlujo, setMinimoFlujo] = useState(200);
  const [datosFlujos, setDatosFlujos] = useState<DatosFlujos | null>(null);

  useEffect(() => {
    fetch("/data/geo/barrios.geojson").then((r) => r.json()).then(setGeojson);
    fetch("/data/mapa/sustitucion_2028.json").then((r) => r.json()).then(setSustitucion);
  }, []);

  // Los flujos pesan 92 KB y la capa arranca apagada: se piden la primera vez que se encienden.
  useEffect(() => {
    if (!flechas || datosFlujos) return;
    fetch("/data/mapa/flujos_2028.json").then((r) => r.json()).then(setDatosFlujos);
  }, [flechas, datosFlujos]);

  const porBarrio = useMemo(() => {
    const filas = sustitucion?.escenarios[escenario] ?? [];
    return Object.fromEntries(filas.map((f) => [f.barrio, f])) as Record<string, BarrioSustitucion>;
  }, [sustitucion, escenario]);

  const flujosVisibles = useMemo(() => {
    if (!flechas) return [];
    const todos = datosFlujos?.escenarios[escenario] ?? [];
    return todos.filter(
      (f) =>
        f.turistas >= minimoFlujo && (!barrio || f.origen === barrio || f.destino === barrio),
    );
  }, [flechas, datosFlujos, escenario, minimoFlujo, barrio]);

  const totales = sustitucion?.totales.find((t) => t.escenario === escenario);
  const activo = barrio ? porBarrio[barrio] : null;
  const indice = ESCENARIOS.findIndex((e) => e.id === escenario);

  return (
    <main className="flex h-dvh w-full flex-col bg-[#faf9f7] text-[#24231f] lg:flex-row">
      <aside className="w-full shrink-0 overflow-y-auto border-b border-[#e3e0da] bg-white p-5 lg:w-[330px] lg:border-r lg:border-b-0">
        <h1 className="text-[15px] font-semibold tracking-tight">Barcelona sin pisos turísticos</h1>
        <p className="mt-1 text-xs leading-relaxed text-[#52514e]">
          Dónde dormirían en 2028 los turistas de las 6.834 viviendas de uso turístico anunciadas
          hoy en Airbnb.
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

        {totales && (
          <dl className="mt-4 grid grid-cols-3 gap-2">
            <Dato titulo="Se mueven" valor={`${totales.km_mediano} km`} />
            <Dato titulo="Pagan de más" valor={`${totales.sobrecoste_mediano} €`} />
            <Dato titulo="Sin sitio" valor={totales.plazas_sin_sitio.toLocaleString("es")} fijo />
          </dl>
        )}

        <h2 className="mt-6 mb-2 text-[11px] font-semibold uppercase tracking-wider text-[#52514e]">
          El mapa
        </h2>
        <div className="flex gap-1 rounded border border-[#e3e0da] p-0.5">
          {VISTAS.map((v) => (
            <button
              key={v.id}
              onClick={() => setMedida(v.id)}
              className={`flex-1 rounded px-2 py-1.5 text-[12px] transition ${
                medida === v.id ? "bg-[#24231f] text-white" : "text-[#52514e] hover:bg-[#f5f4f1]"
              }`}
            >
              {v.etiqueta}
            </button>
          ))}
        </div>

        <Leyenda medida={medida} />

        {activo ? (
          <div className="mt-5 rounded border border-[#e3e0da] bg-[#faf9f7] p-3">
            <h3 className="text-sm font-semibold">{activo.barrio}</h3>
            <dl className="mt-2 space-y-1 text-[13px]">
              <Linea titulo="Turistas que se quedan sin piso" valor={activo.salen} />
              <Linea titulo="Encuentran hotel aquí mismo" valor={activo.se_quedan} />
              <Linea titulo="Llegan desde otros barrios" valor={activo.llegan} />
              <Linea titulo="No encuentran sitio en la ciudad" valor={activo.sin_sitio} />
            </dl>
            <button
              onClick={() => setBarrio(null)}
              className="mt-3 text-[11px] text-[#52514e] underline underline-offset-2"
            >
              quitar selección
            </button>
          </div>
        ) : (
          <p className="mt-5 text-[12px] text-[#52514e]">Pincha un barrio para ver su detalle.</p>
        )}

        <div className="mt-6 border-t border-[#e3e0da] pt-4">
          <label className="flex cursor-pointer items-center gap-2">
            <input
              type="checkbox"
              checked={flechas}
              onChange={(e) => setFlechas(e.target.checked)}
              className="accent-[#2f6fb5]"
            />
            <span className="text-[11px] font-semibold uppercase tracking-wider text-[#52514e]">
              Adónde se van
            </span>
          </label>

          {flechas && (
            <>
              <p className="mt-2 text-[11px] leading-relaxed text-[#52514e]">
                Cada flecha es un movimiento entre dos barrios. El grosor es el número de turistas.
              </p>
              <div className="mt-2">
                <input
                  type="range"
                  min={20}
                  max={500}
                  step={20}
                  value={minimoFlujo}
                  onChange={(e) => setMinimoFlujo(Number(e.target.value))}
                  className="w-full accent-[#2f6fb5]"
                  aria-label="Tamaño mínimo del flujo"
                />
                <p className="text-[11px] text-[#52514e]">
                  {flujosVisibles.length} movimientos de más de {minimoFlujo} turistas
                </p>
              </div>
              <div className="mt-2 space-y-1 text-[11px] text-[#52514e]">
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
                    pincha un barrio para separar ida y vuelta
                  </p>
                )}
              </div>
              <Link
                href="/flujos"
                className="mt-2 inline-block text-[11px] text-[#52514e] underline underline-offset-2"
              >
                verlas en su propio mapa →
              </Link>
            </>
          )}
        </div>

        {totales && (
          <p className="mt-6 border-t border-[#e3e0da] pt-4 text-[11px] leading-relaxed text-[#52514e]">
            Los hoteles no están vacíos: se descuenta una ocupación del{" "}
            <strong>{(totales.ocupacion_partida * 100).toFixed(0)}%</strong>, media de los últimos
            doce meses del INE. Quedan 27.092 plazas libres para 30.067, así que{" "}
            <strong>2.975 no caben en ningún escenario</strong>.
            <br />
            <br />
            Esa cifra es la de un año medio. En noviembre, con la ocupación al 55,6%, cabrían todos.
            En julio, al 79,1%, <strong>no cabrían 12.437</strong>.
          </p>
        )}
      </aside>

      <div className="min-h-[55vh] flex-1">
        <MapaBarrios
          geojson={geojson}
          datos={porBarrio}
          medida={medida}
          barrioActivo={barrio}
          onBarrio={setBarrio}
          flujos={flujosVisibles}
          centroides={datosFlujos?.centroides ?? {}}
        />
      </div>
    </main>
  );
}

/** El color no se explica solo: sin esto, el rojo y el azul son decoración. */
function Leyenda({ medida }: { medida: Medida }) {
  const escalas: Record<Medida, { colores: string[]; izquierda: string; derecha: string }> = {
    saldo: {
      colores: ["#cf4a30", "#ea7a63", "#f7b7a8", "#eeece7", "#a8c8e8", "#6fa2d4", "#2f6fb5"],
      izquierda: "pierde turistas",
      derecha: "gana turistas",
    },
    sin_sitio: {
      colores: ["#eeece7", "#f4efe6", "#e5d5b8", "#d4b184", "#bd8850", "#9c5f27"],
      izquierda: "ninguno",
      derecha: "muchos sin sitio",
    },
    se_quedan: {
      colores: ["#eeece7", "#f4efe6", "#e5d5b8", "#d4b184", "#bd8850", "#9c5f27"],
      izquierda: "ninguno",
      derecha: "casi todos",
    },
  };
  const escala = escalas[medida];
  return (
    <div className="mt-3">
      <div className="flex h-3 overflow-hidden rounded-sm">
        {escala.colores.map((c) => (
          <div key={c} className="flex-1" style={{ backgroundColor: c }} />
        ))}
      </div>
      <div className="mt-1 flex justify-between text-[10px] text-[#52514e]">
        <span>{escala.izquierda}</span>
        <span>{escala.derecha}</span>
      </div>
    </div>
  );
}

function Dato({ titulo, valor, fijo }: { titulo: string; valor: string; fijo?: boolean }) {
  return (
    <div className={fijo ? "rounded bg-[#f5f4f1] px-2 py-1" : ""}>
      <dt className="text-[10px] leading-tight text-[#52514e]">{titulo}</dt>
      <dd className="text-[15px] font-semibold tabular-nums">{valor}</dd>
    </div>
  );
}

function Linea({ titulo, valor }: { titulo: string; valor: number }) {
  return (
    <div className="flex justify-between gap-3">
      <dt className="text-[#52514e]">{titulo}</dt>
      <dd className="font-medium tabular-nums">{valor.toLocaleString("es")}</dd>
    </div>
  );
}
