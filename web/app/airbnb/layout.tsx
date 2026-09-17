import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Airbnb",
  description:
    "De los 15.406 anuncios de Airbnb en Barcelona a las 6.834 viviendas que pierden la licencia " +
    "en 2028, descarte a descarte.",
};

export default function LayoutAirbnb({ children }: { children: React.ReactNode }) {
  return children;
}
