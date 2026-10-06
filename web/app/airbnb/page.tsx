"use client";

import Link from "next/link";

import { BarrasH } from "@/app/components/Graficos";
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

type Grupo = { licencias: number; plazas: number };
type Licencias = {
  registro: Grupo; con_anuncio: Grupo; solo_descartados: Grupo; sin_anuncio: Grupo;
  casadas: { anuncios: number; plazas_airbnb: number; plazas_registro: number };
  pisos_estado: {
    total: Pisos; con_registro: Pisos;
    no_acreditado: Pisos & { detalle: Record<"numero_imposible" | "numero_no_consta" | "numero_de_otra_cosa", Pisos> };
    sin_registro: Pisos & {
      detalle: Record<"no_declara_nada" | "declara_exencion" | "habitacion_con_numero_falso" | "anfitrion_con_hutb_sin_vinculo", Pisos>;
    };
  };
  registro_detalle: {
    mediana_plazas: number; hutb_maximo: number; expediente_desde: number; licencias_2012_2014: number;
    por_distrito: { distrito: string; licencias: number }[];
    vigor: { trimestre_inicial: string; inicial: number; trimestre_minimo: string; minimo: number;
      trimestre_ultimo: string; ultimo: number };
  };
};
type Pisos = { pisos: number; plazas: number };

// `toLocaleString("es")` deja 2390 sin punto: el español no agrupa los números de cuatro cifras.
// Aquí sí se agrupa siempre, porque estas cifras se leen unas junto a otras y «2390» al lado de
// «9.098» se lee como un número más pequeño de lo que es.
const n = (v: number) => v.toLocaleString("es", { useGrouping: "always" });

export default function PaginaAirbnb() {
  const [criba, setCriba] = useState<Criba | null>(null);
  const [lic, setLic] = useState<Licencias | null>(null);
  const [paso, setPaso] = useState(0);

  useEffect(() => {
    fetch("/data/mapa/criba_airbnb.json").then((r) => r.json()).then(setCriba);
    fetch("/data/mapa/licencias.json").then((r) => r.json()).then(setLic);
  }, []);

  // Después del último descarte hay una tarjeta más: lo que el embudo no ve.
  const ultimo = criba?.pasos.length ?? 0;
  const fin = ultimo + 1;
  const mover = useCallback(
    (delta: number) => setPaso((p) => Math.min(Math.max(p + delta, 0), fin)),
    [fin],
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
    const k = Math.min(paso, criba.pasos.length);
    if (k === 0) {
      return { quedan: criba.inicio.anuncios, plazas: criba.inicio.plazas, actual: null };
    }
    const p = criba.pasos[k - 1];
    return { quedan: p.quedan, plazas: p.plazas_restantes, actual: p };
  }, [criba, paso]);

  if (!criba || !estado || !lic) return <main className="min-h-full bg-[#faf9f7]" />;

  const total = criba.inicio.anuncios;
  const descartados = total - estado.quedan;
  const enElFinal = paso === ultimo;
  const enLicencias = paso === fin;
  const viviendas = criba.pasos[criba.pasos.length - 1].quedan;

  return (
    // Sin scroll de página a partir de tableta: la tarjeta se queda quieta y, si su texto no cabe,
    // scrollea ella sola. En móvil se deja fluir — forzar la altura ahí recorta el texto.
    <>
    <main className="flex min-h-full w-full flex-col bg-[#faf9f7] text-[#24231f] sm:h-full sm:overflow-hidden">
      <header className="shrink-0 px-5 pt-5 sm:px-8">
        <div className="mx-auto max-w-4xl">
          <h1 className="text-[17px] font-semibold tracking-tight">
            De {n(total)} anuncios a {n(viviendas)} viviendas
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
          <div className="flex min-h-0 flex-1 flex-col overflow-y-auto px-6 py-6 sm:px-10">
            <div className="my-auto">
            {enLicencias ? (
              <TarjetaLicencias lic={lic} />
            ) : estado.actual ? (
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
                    Quedan <strong>{n(estado.quedan)} viviendas</strong> y sus{" "}
                    <strong>{n(estado.plazas)} plazas</strong>.{" "}
                    <strong>No son todas las licencias de Barcelona:</strong> mira la última tarjeta.
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
          </div>

          <div className="flex shrink-0 items-center justify-between gap-4 border-t border-[#e3e0da] px-4 py-3">
            <Flecha alPulsar={() => mover(-1)} desactivada={paso === 0} etiqueta="Anterior">
              ‹
            </Flecha>

            {/* Los puntos hacen de índice: cuántas tarjetas hay y en cuál estás. */}
            <div className="flex items-center gap-1.5">
              {Array.from({ length: fin + 1 }, (_, i) => (
                <button
                  key={i}
                  onClick={() => setPaso(i)}
                  aria-label={i === 0 ? "El punto de partida" : i === fin ? "Lo que no vemos" : `Descarte ${i}`}
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

            <Flecha alPulsar={() => mover(1)} desactivada={paso === fin} etiqueta="Siguiente">
              ›
            </Flecha>
          </div>
        </section>

        <div className="flex shrink-0 items-center justify-between gap-4 text-[11px] text-[#52514e]">
          {enLicencias ? (
            <a href="#registro" className="font-medium underline underline-offset-2">
              Más datos del registro, abajo ↓
            </a>
          ) : (
            <span>Usa las flechas del teclado, o pincha los puntos.</span>
          )}
          <Link href="/fuentes" className="underline underline-offset-2">
            de dónde sale cada cifra →
          </Link>
        </div>
      </div>
    </main>

    {/* Lo que el embudo no ve, fuera de la tarjeta: debajo, con la página ya con scroll. */}
    {enLicencias && <DatosDebajo lic={lic} />}
    </>
  );
}

/** Lo que el embudo no ve: licencias del registro sin ningún anuncio en Airbnb. Solo la barra. */
function TarjetaLicencias({ lic }: { lic: Licencias }) {
  const total = lic.registro.plazas;
  const trozos = [
    { clave: `en los ${n(lic.pisos_estado.con_registro.pisos)} pisos`, plazas: lic.con_anuncio.plazas,
      estilo: { background: "#2f6fb5" } },
    { clave: "solo con anuncios descartados", plazas: lic.solo_descartados.plazas, estilo: { background: "#9dbbdc" } },
    {
      clave: "sin ningún anuncio",
      plazas: lic.sin_anuncio.plazas,
      estilo: { background: "repeating-linear-gradient(45deg,#b9b5ae 0 6px,#e3e0da 6px 12px)" },
    },
  ];
  return (
    <>
      <p className="text-[11px] font-semibold tracking-wider text-[#a0521a] uppercase">
        Lo que no vemos · faltan datos
      </p>
      <h2 className="mt-2 text-[22px] leading-tight font-semibold tracking-tight">
        {n(lic.sin_anuncio.licencias)} licencias sin ningún anuncio
      </h2>
      <p className="mt-1 text-[15px] font-semibold tabular-nums text-[#a0521a]">
        {n(lic.sin_anuncio.plazas)} plazas · la mitad de las del registro
      </p>

      <div className="mt-4 flex h-5 max-w-xl overflow-hidden rounded-sm">
        {trozos.map((t) => (
          <div key={t.clave} style={{ width: `${(t.plazas / total) * 100}%`, ...t.estilo }} />
        ))}
      </div>
      <ul className="mt-2 max-w-xl space-y-1 text-[13px]">
        {trozos.map((t) => (
          <li key={t.clave} className="flex items-center gap-2">
            <span className="inline-block h-3 w-3 shrink-0 rounded-sm" style={t.estilo} />
            <b className="tabular-nums">{n(t.plazas)}</b>
            <span className="text-[#52514e]">plazas {t.clave}</span>
          </li>
        ))}
      </ul>
    </>
  );
}

/** Todo lo demás, debajo de la tarjeta: el registro oficial y los pisos sin registro. */
function DatosDebajo({ lic }: { lic: Licencias }) {
  return (
    <div id="registro" className="mx-auto w-full max-w-4xl px-5 pb-10 sm:px-8">
      <div className="rounded border border-[#e3e0da] bg-white px-6 py-6 sm:px-10">
        <p className="max-w-xl text-[14px] leading-relaxed text-[#3a3935]">
          El registro oficial de la ciudad tiene <strong>{n(lic.registro.licencias)} licencias</strong> y{" "}
          <strong>{n(lic.registro.plazas)} plazas</strong>. Los pisos que analizamos declaran{" "}
          {n(lic.pisos_estado.con_registro.plazas)}. De las licencias sin anuncio no sabemos nada: pueden
          estar en otra plataforma, dormidas o sin uso. Aquí no cuentan, pero si todas estuvieran activas
          serían hasta <strong>{n(lic.sin_anuncio.plazas)} plazas más</strong>.
        </p>
        <p className="mt-2 max-w-xl text-[13px] leading-relaxed text-[#52514e]">
          En los pisos que sí casan con una licencia, Airbnb declara {n(lic.casadas.plazas_airbnb)} plazas y el
          registro {n(lic.casadas.plazas_registro)}.
        </p>

        <Registro lic={lic} />
        <SinRegistro lic={lic} />
      </div>
    </div>
  );
}

const trimestre = (t: string) => `${t.slice(5, 7)} de ${t.slice(0, 4)}`;

/** Los datos oficiales: Open Data BCN, una fila por licencia. */
function Registro({ lic }: { lic: Licencias }) {
  const r = lic.registro_detalle;
  return (
    <section className="mt-8 max-w-xl border-t border-[#e3e0da] pt-5">
      <p className="text-[11px] font-semibold tracking-wider text-[#52514e] uppercase">
        El registro oficial · Open Data BCN
      </p>
      <div className="mt-3 grid grid-cols-3 gap-3">
        <Dato valor={n(lic.registro.licencias)} etiqueta="licencias" />
        <Dato valor={n(lic.registro.plazas)} etiqueta="plazas" />
        <Dato valor={n(r.mediana_plazas)} etiqueta="plazas por licencia (mediana)" />
      </div>

      <p className="mt-4 mb-2 text-[12px] font-medium">Licencias por distrito</p>
      <BarrasH color="#52514e" filas={r.por_distrito.map((d) => ({ etiqueta: d.distrito, valor: d.licencias }))} />

      <ul className="mt-4 space-y-1 text-[13px] leading-snug text-[#3a3935]">
        <li>
          <b>Licencias en vigor:</b> {n(r.vigor.inicial)} ({trimestre(r.vigor.trimestre_inicial)}) →{" "}
          {n(r.vigor.minimo)} ({trimestre(r.vigor.trimestre_minimo)}, el mínimo) →{" "}
          <b>{n(r.vigor.ultimo)}</b> ({trimestre(r.vigor.trimestre_ultimo)}).
        </li>
        <li>
          <b>Desde cuándo:</b> el expediente más antiguo es de {r.expediente_desde}; {n(r.licencias_2012_2014)} son de
          2012–2014. Es el año de la solicitud, no el del alta.
        </li>
        <li>
          <b>Número más alto emitido:</b> HUTB-{n(r.hutb_maximo).replace(".", "")}. El registro no trae habitaciones.
        </li>
      </ul>
    </section>
  );
}

/** Pisos anunciados cuya licencia no se puede acreditar: el último descarte del embudo. */
function SinRegistro({ lic }: { lic: Licencias }) {
  const e = lic.pisos_estado;
  const sin = e.no_acreditado.pisos + e.sin_registro.pisos;
  const plazasSin = e.no_acreditado.plazas + e.sin_registro.plazas;
  const pct = (v: number) => `${Math.round((v / e.total.plazas) * 100)} %`;
  const trozos = [
    { clave: "con registro, analizados", g: e.con_registro, color: "#2f6fb5" },
    { clave: "registro que no consta", g: e.no_acreditado, color: "#a0521a" },
    { clave: "sin registro", g: e.sin_registro, color: "#cf4a30" },
  ];
  return (
    <section className="mt-8 max-w-xl border-t border-[#e3e0da] pt-5">
      <p className="text-[11px] font-semibold tracking-wider text-[#cf4a30] uppercase">
        Sin registro acreditado · fuera del análisis (último descarte)
      </p>
      <h3 className="mt-1 text-[18px] leading-tight font-semibold">
        {n(sin)} pisos, {n(plazasSin)} plazas ({pct(plazasSin)})
      </h3>

      <div className="mt-3 flex h-5 overflow-hidden rounded-sm">
        {trozos.map((t) => (
          <div key={t.clave} style={{ width: `${(t.g.plazas / e.total.plazas) * 100}%`, background: t.color }} />
        ))}
      </div>
      <ul className="mt-2 space-y-1 text-[13px]">
        {trozos.map((t) => (
          <li key={t.clave} className="flex items-center gap-2">
            <span className="inline-block h-3 w-3 shrink-0 rounded-sm" style={{ background: t.color }} />
            <b className="tabular-nums">{n(t.g.pisos)}</b>
            <span className="text-[#52514e]">pisos {t.clave} · {n(t.g.plazas)} plazas</span>
          </li>
        ))}
      </ul>

      <p className="mt-5 mb-2 text-[12px] font-medium">
        Dicen tener registro, y no consta · {n(e.no_acreditado.pisos)}
      </p>
      <BarrasH color="#a0521a" ancho="12rem" filas={[
        { etiqueta: "Número imposible", valor: e.no_acreditado.detalle.numero_imposible.pisos },
        { etiqueta: "Número que no consta", valor: e.no_acreditado.detalle.numero_no_consta.pisos },
        { etiqueta: "Número de otra cosa", valor: e.no_acreditado.detalle.numero_de_otra_cosa.pisos },
      ]} />
      <p className="mt-1 text-[11px] leading-snug text-[#52514e]">
        Imposible: por encima del HUTB-{n(lic.registro_detalle.hutb_maximo).replace(".", "")} o de relleno
        (123456, 000000). De otra cosa: valía para una habitación o para un hotel.
      </p>

      <p className="mt-5 mb-2 text-[12px] font-medium">
        Deberían tenerlo y no lo declaran · {n(e.sin_registro.pisos)}
      </p>
      <BarrasH color="#cf4a30" ancho="12rem" filas={[
        { etiqueta: "No declara nada", valor: e.sin_registro.detalle.no_declara_nada.pisos },
        { etiqueta: "Declara exención", valor: e.sin_registro.detalle.declara_exencion.pisos },
        { etiqueta: "Habitación, con número falso", valor: e.sin_registro.detalle.habitacion_con_numero_falso.pisos },
        { etiqueta: "Anfitrión con otras licencias", valor: e.sin_registro.detalle.anfitrion_con_hutb_sin_vinculo.pisos },
      ]} />
      <p className="mt-1 text-[11px] leading-snug text-[#52514e]">
        Habitación: anuncia una habitación con un número que no consta. Otras licencias: el anfitrión tiene
        licencias, pero ninguna es de esta vivienda.
      </p>

      <p className="mt-5 rounded border-l-2 border-[#cf4a30] bg-[#faf9f7] px-4 py-3 text-[13px] leading-relaxed text-[#3a3935]">
        La ley de 2028 quita licencias, y estos pisos no tienen ninguna acreditada que quitar. Si siguen
        operando, será fuera del mercado legal, y no hay dato que diga que se vayan. <b>No cuentan</b> como
        turistas que haya que realojar.
      </p>
    </section>
  );
}

function Dato({ valor, etiqueta }: { valor: string; etiqueta: string }) {
  return (
    <div>
      <p className="text-[22px] leading-none font-semibold tabular-nums">{valor}</p>
      <p className="mt-1 text-[11px] leading-snug text-[#52514e]">{etiqueta}</p>
    </div>
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
