import type { Metadata } from "next";

// El mapa es un componente de cliente y no puede exportar `metadata`: va en el layout del segmento.
export const metadata: Metadata = {
  title: "Mapa anterior",
  description:
    "Dónde dormirían en 2028 los turistas de las 4.985 viviendas con registro acreditado anunciadas hoy " +
    "en Airbnb, barrio a barrio.",
};

export default function LayoutMapa({ children }: { children: React.ReactNode }) {
  return children;
}
