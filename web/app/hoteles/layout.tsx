import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Hoteles",
  description:
    "Los hoteles de Barcelona: habitaciones, ocupación, estacionalidad y qué supone para ellos que desaparezcan los pisos turísticos.",
};

export default function LayoutHoteles({ children }: { children: React.ReactNode }) {
  return children;
}
