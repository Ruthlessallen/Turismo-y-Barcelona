import type { Metadata } from "next";

// El mapa es un componente de cliente y no puede exportar `metadata`: va en el layout del segmento.
export const metadata: Metadata = {
  title: "El mapa",
  description:
    "Dónde dormirían en 2028 los turistas de las 6.834 viviendas de uso turístico anunciadas hoy " +
    "en Airbnb, barrio a barrio.",
};

export default function LayoutMapa({ children }: { children: React.ReactNode }) {
  return children;
}
