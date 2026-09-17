"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

/**
 * Las secciones del sitio, en el orden en que se leen: primero el resumen, después el mapa, y al
 * final el detalle de cada lado. `/flujos` no está aquí a propósito: es una vista del mapa, no una
 * sección, y se llega desde él.
 */
const SECCIONES = [
  { href: "/", etiqueta: "Resumen" },
  { href: "/mapa", etiqueta: "El mapa" },
  { href: "/airbnb", etiqueta: "Airbnb" },
  { href: "/fuentes", etiqueta: "Fuentes" },
];

export default function Nav() {
  const ruta = usePathname();

  return (
    <nav className="shrink-0 border-b border-[#e3e0da] bg-white">
      <div className="mx-auto flex max-w-6xl items-center gap-4 px-5 py-2.5 sm:px-8">
        <Link href="/" className="shrink-0 text-[13px] font-semibold tracking-tight">
          Barcelona sin pisos turísticos
        </Link>
        <ul className="flex min-w-0 flex-1 items-center justify-end gap-1 overflow-x-auto">
          {SECCIONES.map((s) => {
            // `/mapa` y `/mapa/algo` son la misma sección; `/` solo se marca en la raíz exacta.
            const activa = s.href === "/" ? ruta === "/" : ruta.startsWith(s.href);
            return (
              <li key={s.href}>
                <Link
                  href={s.href}
                  aria-current={activa ? "page" : undefined}
                  className={`block rounded px-2.5 py-1 text-[12px] whitespace-nowrap transition ${
                    activa
                      ? "bg-[#24231f] text-white"
                      : "text-[#52514e] hover:bg-[#f5f4f1] hover:text-[#24231f]"
                  }`}
                >
                  {s.etiqueta}
                </Link>
              </li>
            );
          })}
        </ul>
      </div>
    </nav>
  );
}
