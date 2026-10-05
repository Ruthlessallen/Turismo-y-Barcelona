import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Turistas",
  description:
    "Cuántos turistas entran en este análisis, qué dice el INE y adónde van los de los pisos en 2028.",
};

export default function LayoutTuristas({ children }: { children: React.ReactNode }) {
  return children;
}
