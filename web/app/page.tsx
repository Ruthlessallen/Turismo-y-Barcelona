"use client";

import { useEffect, useLayoutEffect, useRef, useState } from "react";

import { BarrasDivergentes, Cifra, Seccion, Tarjeta } from "@/app/components/Graficos";
import { COLOR, OSCURO, n } from "@/app/lib/tiposMapa";

/** Lo que publica `export_mapa_limpio.py` en `dashboard.json`. */
type Dashboard = {
  hoteles: {
    total: number; habitaciones: number; plazas: number;
    bandas: Record<string, number>;
    titulares: { nom: string; n: number; plazas: number }[];
    turistas_nuevos: number; turistas_nuevos_pct: number;
  };
  pisos: {
    anuncios_barridos: number; total: number; habitaciones: number; plazas: number;
    bandas: Record<string, number>;
    anfitriones: { nom: string; n: number; plazas: number }[];
    facturacion: [number, number];
  };
};

/** Los barrios de `flujo.json`: los mismos que enseña `/turistas`. */
type BarrioFlujo = {
  barrio: string; hoy: number; en_2028: number; saldo: number; cambio_pct: number | null;
};

/** 222 millones: lo que se lee de un vistazo. */
const millones = (v: number) => (v / 1e6).toLocaleString("es", { maximumFractionDigits: 0 });

const pct = (b: BarrioFlujo) =>
  b.cambio_pct == null ? "" : `${b.cambio_pct > 0 ? "+" : ""}${n(Math.round(b.cambio_pct))} %`;

/** Lo que sale al pasar el ratón por una barra: los turistas que hay hoy y los de 2028. */
const hoy = (b: BarrioFlujo) => `Hoy: ${n(b.hoy)} turistas · 2028: ${n(b.en_2028)}`;

/**
 * Escala el contenido para que llene la pantalla: mide cuánto ocupa a tamaño natural y lo agranda
 * (con `zoom`) hasta donde cabe en alto y en ancho, sin pasar de 1,8 ni bajar de 1.
 */
function useEncaje(listo: boolean) {
  const caja = useRef<HTMLDivElement>(null);
  useLayoutEffect(() => {
    const el = caja.current;
    const padre = el?.parentElement;
    if (!el || !padre) return;
    const ajustar = () => {
      el.style.zoom = "1";
      const z = Math.min(padre.clientHeight / el.offsetHeight, padre.clientWidth / (el.offsetWidth || 1152), 1.8);
      el.style.zoom = String(Math.max(1, Math.floor(z * 100) / 100));
    };
    ajustar();
    window.addEventListener("resize", ajustar);
    return () => window.removeEventListener("resize", ajustar);
  }, [listo]);
  return caja;
}

export default function Portada() {
  const [d, setD] = useState<Dashboard | null>(null);
  const [barrios, setBarrios] = useState<BarrioFlujo[] | null>(null);
  const caja = useEncaje(Boolean(d && barrios));

  useEffect(() => {
    fetch("/data/mapa/dashboard.json").then((r) => r.json()).then(setD);
    fetch("/data/mapa/flujo.json").then((r) => r.json()).then((f) => setBarrios(f.barrios));
  }, []);

  if (!d || !barrios) return <main className="min-h-full bg-[#faf9f7]" />;
  const { hoteles: h, pisos: p } = d;
  const totalBandas = Object.values(h.bandas).reduce((a, b) => a + b, 0);
  const totalBandasPisos = Object.values(p.bandas).reduce((a, b) => a + b, 0);

  const sube = barrios.filter((b) => b.saldo > 0).sort((a, b) => b.saldo - a.saldo).slice(0, 5);
  const baja = barrios.filter((b) => b.saldo < 0).sort((a, b) => a.saldo - b.saldo).slice(0, 5);
  const tope = Math.max(...sube.map((b) => b.saldo), ...baja.map((b) => -b.saldo));

  return (
    // Una pantalla: dos columnas arriba (hoteles y Airbnb) y los barrios debajo. Todo en versión
    // compacta para que quepa sin scroll; en pantallas pequeñas se apila y se desplaza.
    <main className="min-h-full bg-[#faf9f7] text-[#24231f] lg:h-full">
      <div ref={caja} className="mx-auto max-w-6xl px-5 py-3 sm:px-8">
        <div className="grid gap-x-4 gap-y-2 lg:grid-cols-2">
          <Seccion color={COLOR.hotel} titulo="Hoteles" compacta>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              <Cifra compacta valor={n(h.total)} etiqueta="hoteles" color={OSCURO.hotel} />
              <Cifra compacta valor={n(h.habitaciones)} etiqueta="habitaciones" color={OSCURO.hotel} />
              <Cifra compacta valor={n(h.plazas)} etiqueta="plazas" color={OSCURO.hotel} />
              <Cifra compacta valor={`+${h.turistas_nuevos_pct.toLocaleString("es")} %`}
                etiqueta="turistas más en 2028" color={OSCURO.hotel}
                pie={`${n(h.turistas_nuevos)} por noche`} />
            </div>
            <div className="mt-2 grid gap-2">
              <Tarjeta compacta titulo="Bandas económicas · por habitación">
                <Bandas bandas={h.bandas} total={totalBandas}
                  colores={["#9dbbdc", "#6f9fd0", "#1f5fa8", "#123a6b"]} />
              </Tarjeta>
              <Tarjeta compacta titulo="Titulares con más hoteles">
                <Ranking filas={h.titulares} unidad="hoteles" />
              </Tarjeta>
            </div>
          </Seccion>

          <Seccion color={COLOR.piso} titulo="Airbnb" compacta>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              <Cifra compacta valor={n(p.total)} etiqueta="pisos" pie={`de ${n(p.anuncios_barridos)} anuncios`}
                color={OSCURO.piso} />
              <Cifra compacta valor={n(p.habitaciones)} etiqueta="habitaciones" color={OSCURO.piso} />
              <Cifra compacta valor={n(p.plazas)} etiqueta="plazas" color={OSCURO.piso} />
              <Cifra compacta valor={`${millones(p.facturacion[0])}–${millones(p.facturacion[1])}`}
                etiqueta="millones de € al año" pie="aproximado" color={OSCURO.piso} />
            </div>
            <div className="mt-2 grid gap-2">
              <Tarjeta compacta titulo="Bandas económicas · por plaza">
                <Bandas bandas={p.bandas} total={totalBandasPisos}
                  colores={["#f3ad62", "#e8710a", "#a84a00", "#6b2f00"]} />
              </Tarjeta>
              <Tarjeta compacta titulo="Anfitriones con más pisos">
                <Ranking filas={p.anfitriones} unidad="pisos" />
              </Tarjeta>
            </div>
          </Seccion>
        </div>

        <div className="mt-2">
          <Seccion color="#24231f" titulo="Turistas en 2028, por noche" compacta>
            <div className="grid gap-2 lg:grid-cols-2">
              <Tarjeta compacta titulo="Los 5 barrios que ganan turistas">
                <BarrasDivergentes compacta tope={tope}
                  filas={sube.map((b) => ({ etiqueta: b.barrio, valor: b.saldo, pie: pct(b), detalle: hoy(b) }))} />
              </Tarjeta>
              <Tarjeta compacta titulo="Los 5 barrios que pierden turistas">
                <BarrasDivergentes compacta tope={tope}
                  filas={baja.map((b) => ({ etiqueta: b.barrio, valor: b.saldo, pie: pct(b), detalle: hoy(b) }))} />
              </Tarjeta>
            </div>
          </Seccion>
        </div>
      </div>
    </main>
  );
}

/** Una lista con el nombre a la izquierda y, a la derecha del todo, cuántos y cuántas plazas. */
function Ranking({ filas, unidad }: {
  filas: { nom: string; n: number; plazas: number }[]; unidad: string;
}) {
  return (
    <div className="text-[13px]">
      <div className="mb-1 grid grid-cols-[1fr_4rem_5.5rem] gap-2 text-[11px] text-[#52514e]">
        <span />
        <span className="text-right">{unidad}</span>
        <span className="text-right">plazas</span>
      </div>
      <ol className="space-y-0.5">
        {filas.map((f) => (
          <li key={f.nom} className="grid grid-cols-[1fr_4rem_5.5rem] items-baseline gap-2">
            <span className="truncate">{f.nom}</span>
            <b className="text-right tabular-nums">{n(f.n)}</b>
            <span className="text-right tabular-nums text-[#52514e]">{n(f.plazas)}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}

/** Una barra partida en las cuatro bandas, con el recuento debajo. */
function Bandas({ bandas, total, colores }: {
  bandas: Record<string, number>; total: number; colores: string[];
}) {
  return (
    <>
      <div className="flex h-5 overflow-hidden rounded text-[11px] font-semibold text-white">
        {Object.entries(bandas).map(([banda, cuantos], i) => (
          <div key={banda} className="flex items-center justify-center"
            style={{ width: `${(cuantos / total) * 100}%`, background: colores[i] }}>
            {cuantos / total > 0.08 && banda}
          </div>
        ))}
      </div>
      <ul className="mt-1 flex justify-between text-[12px] tabular-nums">
        {Object.entries(bandas).map(([banda, cuantos]) => (
          <li key={banda}><b>{n(cuantos)}</b> <span className="text-[#52514e]">{banda}</span></li>
        ))}
      </ul>
    </>
  );
}
