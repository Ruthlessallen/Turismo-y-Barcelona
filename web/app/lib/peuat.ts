/**
 * Las zonas del PEUAT (Pla Especial Urbanístic d'Allotjaments Turístics), de `peuat.geojson`.
 *
 * El Ajuntament publica 12 polígonos con códigos `ZE1`, `ZE2`, `ZE3A`…`ZE4C` y `EXCLO`. Se agrupan
 * por su número. Reglas del PEUAT de 2021, según prensa y despachos jurídicos: zona 1 no admite
 * establecimientos nuevos; zona 2 mantiene el censo (solo sustitución); zona 3 crecimiento contenido;
 * zona 4 regulación propia. Las zonas 3 y 4 dependen de topes de plazas por subzona, no contrastados con el texto oficial.
 */
export type GrupoPeuat = "ze1" | "ze2" | "ze3" | "ze4" | "exclo";

export const GRUPOS_PEUAT: { id: GrupoPeuat; etiqueta: string; color: string; dash?: string }[] = [
  { id: "ze1", etiqueta: "Zona 1 · sin hoteles nuevos", color: "#b3261e" },
  { id: "ze2", etiqueta: "Zona 2 · solo sustitución", color: "#d98200" },
  { id: "ze3", etiqueta: "Zona 3 · crecimiento contenido", color: "#2f7a3e" },
  { id: "ze4", etiqueta: "Zona 4 · regulación propia", color: "#6a4c93" },
  { id: "exclo", etiqueta: "Excluida", color: "#7a7a7a", dash: "4 4" },
];

export function grupoPeuat(zona: string): GrupoPeuat {
  const z = zona.toUpperCase();
  if (z.startsWith("ZE1")) return "ze1";
  if (z.startsWith("ZE2")) return "ze2";
  if (z.startsWith("ZE3")) return "ze3";
  if (z.startsWith("ZE4")) return "ze4";
  return "exclo";
}
