import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Restauración",
  description:
    "Las marcas con más locales de Barcelona y qué locales y barrios ganan o pierden clientes cuando " +
    "los turistas de los pisos pasan a los hoteles.",
};

export default function LayoutRestauracion({ children }: { children: React.ReactNode }) {
  return children;
}
