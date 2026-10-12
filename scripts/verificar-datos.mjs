#!/usr/bin/env node
/**
 * Comprueba que los datos que lee la web son coherentes entre sí. Sin dependencias.
 *
 *   node scripts/verificar-datos.mjs
 *
 * No prueba que la web "se vea bien" (eso es `next build` y mirarla): prueba que ninguna cifra
 * contradice a otra y que no se cuela nada que no debe publicarse. Sale con código 1 si algo falla.
 */
import { readFileSync, readdirSync } from "node:fs";
import { join, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const RAIZ = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const EXPORTS = join(RAIZ, "data", "exports", "mapa");
const WEB = join(RAIZ, "web", "public", "data", "mapa");
const leer = (dir, f) => JSON.parse(readFileSync(join(dir, f), "utf-8"));

const fallos = [];
const comprobar = (ok, mensaje) => { if (!ok) fallos.push(mensaje); };

// 1. La copia de la web es idéntica a lo exportado.
for (const f of readdirSync(WEB)) {
  comprobar(readFileSync(join(WEB, f), "utf-8") === readFileSync(join(EXPORTS, f), "utf-8"),
    `web/public/data/mapa/${f} no coincide con data/exports/mapa/${f} (falta copiarlo)`);
}
for (const f of readdirSync(EXPORTS)) {
  comprobar(readdirSync(WEB).includes(f), `data/exports/mapa/${f} no está en la web`);
}

const pisos = leer(WEB, "puntos_pisos.json");
const hoteles = leer(WEB, "puntos_hoteles.json");
const rest = leer(WEB, "puntos_restaurantes.json");
const dash = leer(WEB, "dashboard.json");
const par = leer(WEB, "parametros.json");
const hp = leer(WEB, "hoteles_pagina.json");
const criba = leer(WEB, "criba_airbnb.json");
const lic = leer(WEB, "licencias.json");

// 2. Los recuentos de la portada son los de los puntos.
comprobar(pisos.length === dash.pisos.total, `pisos: ${pisos.length} puntos y ${dash.pisos.total} en dashboard`);
comprobar(hoteles.length === dash.hoteles.total, `hoteles: ${hoteles.length} puntos y ${dash.hoteles.total} en dashboard`);
comprobar(lic.pisos_estado.con_registro.pisos === pisos.length, "licencias.json no cuadra con los pisos publicados");

// 3. Privacidad: el piso es una tupla de 11 valores simples, sin id, nombre ni anfitrión.
comprobar(pisos.every((p) => Array.isArray(p) && p.length === 11), "algún piso no es una tupla de 11 valores");
comprobar(pisos.every((p) => p.every((v) => v === null || typeof v === "number" || typeof v === "string")), "algún piso lleva un valor no simple");
const textoPisos = readFileSync(join(WEB, "puntos_pisos.json"), "utf-8");
comprobar(!/host_|licencia|HUTB|listing_id/i.test(textoPisos), "puntos_pisos.json contiene texto de anfitrión o licencia");
comprobar(dash.pisos.anfitriones.every((a) => a.n >= 20), "un anfitrión de la portada tiene menos de 20 pisos");

// 4. Hoteles: sin precio propio, banda de su categoría, una sola por categoría.
const porCategoria = {};
for (const h of hoteles) {
  comprobar(h.banda !== null && h.cat_ine !== null, `hotel sin categoría o banda: ${h.nom}`);
  const k = h.cat_ine; porCategoria[k] ??= new Set(); porCategoria[k].add(`${h.banda}|${h.adr}`);
  comprobar(!("origen" in h) && !("precio" in h) && !("banda_hab" in h), "un hotel lleva un campo de precio propio");
}
for (const [k, v] of Object.entries(porCategoria)) comprobar(v.size === 1, `la categoría ${k} tiene más de una banda/ADR: ${[...v]}`);

// 5. Ocupación: hoy es el parámetro, 2028 no pasa de 100 y el reparto cuadra con los hoteles.
comprobar(dash.hoteles.ocupacion_hoy === par.ocupacion_hotel_habitaciones, "ocupación de hoy distinta de parametros.json");
comprobar(dash.hoteles.ocupacion_2028 > dash.hoteles.ocupacion_hoy && dash.hoteles.ocupacion_2028 <= 100, `ocupación 2028 fuera de rango: ${dash.hoteles.ocupacion_2028}`);
const absorbidas = hoteles.reduce((s, h) => s + (h.hab_abs ?? 0), 0);
comprobar(Math.abs(absorbidas - hp.ocupacion.habitaciones_absorbidas) <= 50, `habitaciones absorbidas: ${absorbidas} frente a ${hp.ocupacion.habitaciones_absorbidas}`);
const libres = hp.ocupacion.habitaciones * (1 - par.ocupacion_hotel_habitaciones / 100);
comprobar(absorbidas <= libres * 1.01, "los hoteles absorben más habitaciones de las que tienen libres");

// 6. El embudo de Airbnb suma.
const descartados = criba.pasos.reduce((s, p) => s + p.descartados, 0);
comprobar(criba.inicio.anuncios - descartados === pisos.length, `criba: ${criba.inicio.anuncios} - ${descartados} != ${pisos.length}`);

// 7. Restauración: ningún local sin coordenadas.
comprobar(rest.every((r) => Number.isFinite(r.lat) && Number.isFinite(r.lon)), "un local sin coordenadas");

if (fallos.length) {
  console.error(`✗ ${fallos.length} fallo(s):\n` + fallos.map((f) => `  - ${f}`).join("\n"));
  process.exit(1);
}
console.log(`✓ datos coherentes: ${pisos.length} pisos, ${hoteles.length} hoteles, ${rest.length} locales`);
