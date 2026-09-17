"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

/** Lo que publica `export_mapa.py` en `resumen.json`. Solo los campos que esta página usa. */
type Resumen = {
  hoteles: { total: number };
  restauracion: { total: number; por_tipo: Record<string, number> };
  restauracion_2028: { ganan: number; pierden: number };
  vut: { total: number };
  airbnb: { sujetos_a_la_ley: number; precio_plaza_mediano: number };
  criba_airbnb: { inicio: number; final: number };
  sustitucion_2028: {
    ocupacion_partida: number;
    plazas_vut: number;
    plazas_regladas: number;
    sin_sitio: number;
  };
};

const n = (v: number) => v.toLocaleString("es", { useGrouping: "always" });

export default function Portada() {
  const [r, setResumen] = useState<Resumen | null>(null);

  useEffect(() => {
    fetch("/data/mapa/resumen.json").then((x) => x.json()).then(setResumen);
  }, []);

  if (!r) return <main className="min-h-full bg-[#faf9f7]" />;

  const libres = Math.round(r.sustitucion_2028.plazas_regladas * (1 - r.sustitucion_2028.ocupacion_partida));

  return (
    <main className="min-h-full bg-[#faf9f7] text-[#24231f]">
      <div className="mx-auto max-w-6xl px-5 py-8 sm:px-8">
        <h1 className="max-w-2xl text-2xl leading-tight font-semibold tracking-tight">
          Barcelona elimina las licencias de piso turístico en noviembre de 2028
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-[#52514e]">
          Qué hay hoy, qué desaparece y dónde acabarían durmiendo esos turistas. Todas las cifras
          salen de fuentes públicas y cada una dice de dónde viene.
        </p>

        <h2 className="mt-8 mb-3 text-[11px] font-semibold uppercase tracking-wider text-[#52514e]">
          Lo que hay hoy
        </h2>
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <Cifra
            valor={n(r.vut.total)}
            titulo="Licencias de piso turístico"
            pie="En la provincia, del registro oficial"
          />
          <Cifra
            valor={n(r.criba_airbnb.inicio)}
            titulo="Anuncios en Airbnb"
            pie="Volcado del 24 de junio de 2026"
          />
          <Cifra valor={n(r.hoteles.total)} titulo="Hoteles en la ciudad" pie="Del Registre de Turisme" />
          <Cifra
            valor={n(r.restauracion.total)}
            titulo="Bares y restaurantes"
            pie="Censo comercial municipal"
          />
        </div>

        <h2 className="mt-8 mb-3 text-[11px] font-semibold uppercase tracking-wider text-[#52514e]">
          Lo que desaparece
        </h2>
        <div className="grid gap-3 lg:grid-cols-3">
          <Bloque
            titulo="6.834 viviendas, no 15.406 anuncios"
            enlace={{ href: "/airbnb", texto: "pasar las tarjetas del embudo →" }}
          >
            De los {n(r.criba_airbnb.inicio)} anuncios publicados, la mayoría no es lo que la ley
            elimina: hay hoteles, habitaciones sueltas, alquiler de temporada, anuncios apagados y
            repeticiones de una misma vivienda. Quedan{" "}
            <strong>{n(r.criba_airbnb.final)}</strong>, con {n(r.sustitucion_2028.plazas_vut)}{" "}
            plazas.
          </Bloque>
          <Bloque
            titulo={`${n(r.sustitucion_2028.sin_sitio)} turistas no caben`}
            enlace={{ href: "/mapa", texto: "ver el mapa barrio a barrio →" }}
          >
            Los hoteles no están vacíos: descontada la ocupación real del{" "}
            {(r.sustitucion_2028.ocupacion_partida * 100).toFixed(0)}%, quedan {n(libres)} plazas
            libres para {n(r.sustitucion_2028.plazas_vut)} turistas. En un año medio{" "}
            <strong>{n(r.sustitucion_2028.sin_sitio)} se quedan fuera de la ciudad</strong>, y en
            julio serían 12.490.
          </Bloque>
          <Bloque
            titulo="40 barrios pierden clientela"
            enlace={{ href: "/mapa", texto: "ver la capa de restauración →" }}
          >
            Al mudarse el turista, se muda con quién cena. De los 73 barrios con locales,{" "}
            <strong>{r.restauracion_2028.pierden} pierden</strong> comensales y{" "}
            {r.restauracion_2028.ganan} ganan. La Sagrada Família pierde 2.137; el Raval gana 1.255.
          </Bloque>
        </div>

        <section className="mt-8 rounded border border-[#e3e0da] bg-white p-5">
          <h2 className="text-[15px] font-semibold tracking-tight">Antes de leer ninguna cifra</h2>
          <p className="mt-2 max-w-3xl text-[14px] leading-relaxed text-[#3a3935]">
            Esto <strong>no cubre las {n(r.vut.total)} licencias</strong> del registro oficial:
            cubre las {n(r.criba_airbnb.final)} viviendas que hoy se anuncian en Airbnb. Lo que se
            alquila por otras plataformas, o por ninguna, no aparece. Y el reparto de 2028 es un
            modelo con supuestos, no una predicción: el peso entre precio y ubicación lo elige quien
            mira el mapa, porque ningún dato disponible lo decide.
          </p>
          <Link
            href="/fuentes"
            className="mt-3 inline-block text-[12px] text-[#52514e] underline underline-offset-2"
          >
            fuentes, decisiones y límites →
          </Link>
        </section>
      </div>
    </main>
  );
}

function Cifra({ valor, titulo, pie }: { valor: string; titulo: string; pie: string }) {
  return (
    <div className="rounded border border-[#e3e0da] bg-white p-4">
      <p className="text-[28px] leading-none font-semibold tabular-nums">{valor}</p>
      <p className="mt-1.5 text-[13px] font-medium">{titulo}</p>
      <p className="mt-0.5 text-[11px] leading-snug text-[#52514e]">{pie}</p>
    </div>
  );
}

function Bloque({
  titulo,
  enlace,
  children,
}: {
  titulo: string;
  enlace: { href: string; texto: string };
  children: React.ReactNode;
}) {
  return (
    <article className="flex flex-col rounded border border-[#e3e0da] bg-white p-5">
      <h3 className="text-[15px] font-semibold tracking-tight">{titulo}</h3>
      <p className="mt-2 flex-1 text-[14px] leading-relaxed text-[#3a3935]">{children}</p>
      <Link
        href={enlace.href}
        className="mt-3 text-[12px] text-[#52514e] underline underline-offset-2"
      >
        {enlace.texto}
      </Link>
    </article>
  );
}
