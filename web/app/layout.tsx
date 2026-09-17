import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

import Nav from "@/app/components/Nav";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  // Plantilla: cada página pone su nombre delante y el sitio queda detrás.
  title: {
    default: "Barcelona sin pisos turísticos",
    template: "%s · Barcelona sin pisos turísticos",
  },
  description:
    "Dónde se alojarían los turistas de las viviendas de uso turístico de Barcelona cuando " +
    "desaparezca su licencia en 2028.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      {/*
        El nav es fijo y el contenido ocupa lo que queda. Pasar el alto por aquí y no por cada
        página es lo que permite que el mapa se quede quieto —nunca scrollea— mientras una página
        de texto sí puede: cada una elige qué hacer con `h-full`, pero ninguna vuelve a medir la
        ventana por su cuenta.
      */}
      <body
        className={`${geistSans.variable} ${geistMono.variable} flex h-dvh flex-col overflow-hidden antialiased`}
      >
        <Nav />
        <div className="min-h-0 flex-1 overflow-y-auto">{children}</div>
      </body>
    </html>
  );
}
