/**
 * Gráficos sencillos en HTML: barras, sin librería. Una cifra por barra, a la vista, y el color
 * dice qué es (nunca decora). Para el signo se usa verde y morado, que se distinguen en las tres
 * formas de daltonismo comunes; verde y rojo no.
 */

import { n } from "@/app/lib/tiposMapa";

export const VERDE = "#2f7a3e";
export const MORADO = "#7b3fa0";

export type FilaBarra = { etiqueta: string; valor: number; color?: string; pie?: string };

/** Barras horizontales, de cero al máximo. */
export function BarrasH({ filas, max, color = "#24231f", formato = (v: number) => n(Math.round(v)) }: {
  filas: FilaBarra[]; max?: number; color?: string; formato?: (v: number) => string;
}) {
  const tope = max ?? Math.max(...filas.map((f) => f.valor), 1);
  return (
    <ul className="space-y-1.5">
      {filas.map((f) => (
        <li key={f.etiqueta} className="grid grid-cols-[minmax(0,9rem)_1fr_auto] items-center gap-2 text-[12px]">
          <span className="truncate">{f.etiqueta}</span>
          <span className="h-3 rounded bg-[#eeece7]">
            <span className="block h-full rounded" style={{ width: `${(f.valor / tope) * 100}%`, background: f.color ?? color }} />
          </span>
          <b className="tabular-nums">{formato(f.valor)}{f.pie ? <span className="font-normal text-[#52514e]"> {f.pie}</span> : null}</b>
        </li>
      ))}
    </ul>
  );
}

/** Barras que salen del centro: a la derecha lo que sube (verde), a la izquierda lo que baja (morado). */
export function BarrasDivergentes({ filas, tope: topeFijo, formato = (v: number) => `${v > 0 ? "+" : ""}${n(v)}` }: {
  filas: FilaBarra[]; tope?: number; formato?: (v: number) => string;
}) {
  const tope = topeFijo ?? Math.max(...filas.map((f) => Math.abs(f.valor)), 1);
  return (
    <ul className="space-y-1.5">
      {filas.map((f) => {
        const ancho = (Math.abs(f.valor) / tope) * 50;
        const sube = f.valor >= 0;
        return (
          <li key={f.etiqueta} className="grid grid-cols-[minmax(0,10rem)_1fr_auto] items-center gap-2 text-[12px]">
            <span className="truncate">{f.etiqueta}</span>
            <span className="relative h-3 rounded bg-[#eeece7]">
              <span className="absolute top-0 left-1/2 h-full w-px bg-[#a3a09b]" />
              <span className="absolute top-0 h-full rounded"
                style={{ width: `${ancho}%`, background: sube ? VERDE : MORADO,
                  [sube ? "left" : "right"]: "50%" }} />
            </span>
            <b className="tabular-nums" style={{ color: sube ? VERDE : MORADO }}>
              {formato(f.valor)}{f.pie ? <span className="font-normal text-[#52514e]"> {f.pie}</span> : null}
            </b>
          </li>
        );
      })}
    </ul>
  );
}

/** Columnas verticales, con una línea de referencia opcional (la media). */
export function Columnas({ datos, color = "#1f5fa8", referencia, max = 100, formato = (v: number) => `${v}`, alto = 120 }: {
  datos: { etiqueta: string; valor: number }[]; color?: string; referencia?: number; max?: number;
  formato?: (v: number) => string; alto?: number;
}) {
  return (
    <div>
      <div className="relative flex items-end gap-1.5" style={{ height: alto }}>
        {datos.map((d) => (
          <div key={d.etiqueta} className="flex h-full flex-1 flex-col items-center justify-end">
            <span className="mb-0.5 text-[10px] tabular-nums text-[#52514e]">{formato(d.valor)}</span>
            <span className="w-full rounded-t" style={{ height: `${(d.valor / max) * 100 * 0.82}%`, background: color }} />
          </div>
        ))}
        {referencia != null && (
          <span className="pointer-events-none absolute right-0 left-0 border-t border-dashed border-[#24231f]"
            style={{ bottom: `${(referencia / max) * 100 * 0.82}%` }} />
        )}
      </div>
      <div className="mt-1 flex gap-1.5">
        {datos.map((d) => (
          <span key={d.etiqueta} className="flex-1 text-center text-[10px] text-[#52514e]">{d.etiqueta}</span>
        ))}
      </div>
    </div>
  );
}

/** Una matriz de origen y destino: cuanto más oscuro, más turistas. */
export function Matriz({ etiquetas, valores, color = "31,95,168", titulo }: {
  etiquetas: string[]; valores: number[][]; color?: string; titulo: { filas: string; columnas: string };
}) {
  const tope = Math.max(...valores.flat(), 1);
  return (
    <div className="text-[12px]">
      <div className="grid grid-cols-[4.5rem_repeat(4,1fr)] gap-1">
        <span className="text-[10px] text-[#52514e]">{titulo.filas} ↓ · {titulo.columnas} →</span>
        {etiquetas.map((e) => <span key={e} className="text-center font-medium">{e}</span>)}
        {valores.map((fila, i) => (
          <div key={etiquetas[i]} className="contents">
            <span className="font-medium">{etiquetas[i]}</span>
            {fila.map((v, j) => (
              <span key={j} className="rounded py-1.5 text-center tabular-nums"
                style={{ background: v ? `rgba(${color},${0.12 + 0.88 * (v / tope)})` : "#f3f1ec",
                  color: v / tope > 0.5 ? "#fff" : "#24231f" }}>
                {v ? n(v) : "·"}
              </span>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

export function Cifra({ valor, etiqueta, pie, color }: {
  valor: string; etiqueta: string; pie?: string; color?: string;
}) {
  return (
    <div className="rounded border border-[#e3e0da] bg-white p-4" style={color ? { borderColor: color, borderWidth: 2 } : undefined}>
      <p className="text-[28px] leading-none font-semibold tabular-nums">{valor}</p>
      <p className="mt-1.5 text-[13px] font-medium">{etiqueta}</p>
      {pie && <p className="mt-0.5 text-[11px] text-[#52514e]">{pie}</p>}
    </div>
  );
}

export function Tarjeta({ titulo, children, className = "" }: {
  titulo: string; children: React.ReactNode; className?: string;
}) {
  return (
    <div className={`rounded border border-[#e3e0da] bg-white p-4 ${className}`}>
      <p className="mb-2.5 text-[12px] font-medium">{titulo}</p>
      {children}
    </div>
  );
}

export function Seccion({ color, titulo, children }: {
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
