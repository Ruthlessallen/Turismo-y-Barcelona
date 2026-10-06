/**
 * Las zonas del PEUAT (Pla Especial Urbanístic d'Allotjaments Turístics), de `peuat.geojson`.
 *
 * El Ajuntament publica 12 polígonos con códigos `ZE1`, `ZE2`, `ZE3A`…`ZE4C` y `EXCLO`. Se agrupan
 * por su número porque es lo que la prensa llama zona 1, 2, 3 y 4. **Qué códigos admiten hoteles
 * nuevos no está verificado** contra el texto del plan: según la prensa, las zonas 1 y 2 no.
 */
export type GrupoPeuat = "ze1" | "ze2" | "ze3" | "ze4" | "exclo";

export const GRUPOS_PEUAT: { id: GrupoPeuat; etiqueta: string; color: string; dash?: string }[] = [
  { id: "ze1", etiqueta: "Zona 1", color: "#b3261e" },
  { id: "ze2", etiqueta: "Zona 2", color: "#d98200" },
  { id: "ze3", etiqueta: "Zona 3 (A–E)", color: "#2f7a3e" },
  { id: "ze4", etiqueta: "Zona 4 (A–C)", color: "#6a4c93" },
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
