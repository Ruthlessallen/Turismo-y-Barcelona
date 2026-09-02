"""Genera los datos del mapa: puntos donde se puede, agregados donde no.

    python pipeline/export_mapa.py

Salidas
    data/exports/mapa/hoteles.json          — puntos individuales
    data/exports/mapa/apartaments_turistics.json — puntos individuales, capa aparte
    data/exports/mapa/restauracion.json     — puntos individuales
    data/exports/mapa/vut_por_barrio.json   — agregado
    data/exports/mapa/vut_por_municipio.json — agregado
    data/exports/mapa/airbnb_por_barrio.json — agregado
    data/exports/mapa/resumen.json          — totales y metadatos

**Qué se publica como punto y qué no.** Un hotel o un restaurante son establecimientos abiertos al
público: su ubicación ya es pública y se exporta como punto. Una VUT es una **vivienda**, y un
anuncio de Airbnb también: esos se agregan por barrio o municipio y nunca salen individualmente
(ver `docs/prd.md` → Fuera de alcance). No es una precaución de estilo; es la línea que separa
analizar un mercado de señalar domicilios.

**Tres precisiones geográficas que el mapa debe distinguir.** Cada punto lleva `precision`:

- `exacta` — coordenada del registro oficial u Open Data BCN
- `geocodificada` — deducida de la dirección con el ICGC, verificada contra el municipio
- `desplazada` — Inside Airbnb mueve cada anuncio hasta ~200 m a propósito

Pintarlas con el mismo símbolo daría a entender una precisión que no tenemos.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
BRONZE = RAIZ / "data" / "bronze"
GOLD = RAIZ / "data" / "gold"
CALIDAD = GOLD / "calidad"
DESTINO = RAIZ / "data" / "exports" / "mapa"


def sin_nan(valor):
    """`None` en lugar de NaN. `json.dumps` escribe `NaN`, que no es JSON válido y rompe el
    `fetch` del navegador con un error de sintaxis lejos de donde está la causa."""
    return None if pd.isna(valor) else valor


def volcar(ruta: Path, datos) -> None:
    """Escribe JSON válido: sin NaN ni Infinity, que `json` acepta y el navegador no."""
    ruta.write_text(json.dumps(datos, ensure_ascii=False, allow_nan=False), encoding="utf-8")


def cargar_geocodificado() -> pd.DataFrame:
    """Coordenadas del ICGC que superaron la verificación por municipio."""
    ruta = BRONZE / "geocodificacion_verificada.csv"
    if not ruta.exists():
        ruta = BRONZE / "geocodificacion_icgc.csv"
    if not ruta.exists():
        return pd.DataFrame(columns=["licencia_id", "lat", "lon"])

    d = pd.read_csv(ruta, dtype={"licencia_id": str})
    d = d[d["geocodificado"] == True]  # noqa: E712
    # Si la verificación está disponible, solo entran las que cuadran con su municipio: una
    # dirección resuelta en otro pueblo es peor que no tener coordenada.
    if "municipio_coincide" in d.columns:
        d = d[d["municipio_coincide"] == True]  # noqa: E712
    return d[["licencia_id", "lat", "lon"]]


def completar_coordenadas(d: pd.DataFrame, geo: pd.DataFrame) -> pd.DataFrame:
    """Rellena huecos con lo geocodificado, sin pisar la coordenada oficial."""
    d = d.copy()
    for c in ("lat", "lon"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d["precision"] = d["lat"].notna().map({True: "exacta", False: None})

    d = d.merge(geo, on="licencia_id", how="left", suffixes=("", "_geo"))
    rellena = d["lat"].isna() & d["lat_geo"].notna()
    d.loc[rellena, ["lat", "lon", "precision"]] = (
        d.loc[rellena, ["lat_geo", "lon_geo"]].assign(precision="geocodificada").values)
    return d.drop(columns=["lat_geo", "lon_geo"], errors="ignore")


def exportar_hoteles(geo: pd.DataFrame) -> dict:
    """Hoteles y apartaments turístics, en ficheros separados.

    Van aparte porque son figuras legales distintas y confundirlas es el error más fácil de
    cometer con estos datos: la eliminación de 2028 afecta a las VUT, no a los AT, que seguirán
    operando. Mezclarlos en una sola capa daría a entender que todo el alojamiento en apartamento
    desaparece.
    """
    h = pd.read_csv(BRONZE / "hoteles_y_apartaments_unificados.csv", dtype=str)
    h = completar_coordenadas(h, geo)

    # Un registro de Open Data BCN sin correspondencia en el Registre se queda sin `tipo`. Viene
    # del fichero de hoteles del Ajuntament, así que hotel es: dejarlo nulo lo excluiría del mapa.
    h["tipo"] = h["tipo"].fillna("hotel")

    precios = pd.read_csv(BRONZE / "precios_hoteles_cruzados.csv")
    fiables = precios[precios["precio"].notna() & ~precios["dudoso"].fillna(False)]
    h = h.merge(fiables[["licencia_id", "precio"]], on="licencia_id", how="left")

    con_punto = h[h["lat"].notna()]
    puntos = [{
        "id": r["licencia_id"],
        "nom": sin_nan(r["nombre_comercial"]),
        "tipo": sin_nan(r["tipo"]),
        "cat": sin_nan(r["categoria"]),
        "plazas": int(float(r["plazas"])) if pd.notna(r["plazas"]) else None,
        "hab": int(float(r["habitaciones"])) if pd.notna(r["habitaciones"]) else None,
        "precio": round(float(r["precio"])) if pd.notna(r["precio"]) else None,
        "mun": sin_nan(r["municipio"]),
        "lat": round(float(r["lat"]), 6),
        "lon": round(float(r["lon"]), 6),
        "prec": r["precision"],
    } for _, r in con_punto.iterrows()]

    hoteles = [p for p in puntos if p["tipo"] == "hotel"]
    apartamentos = [p for p in puntos if p["tipo"] == "apartament_turistic"]
    volcar(DESTINO / "hoteles.json", hoteles)
    volcar(DESTINO / "apartaments_turistics.json", apartamentos)

    return {
        "hoteles": {"total": int((h["tipo"] == "hotel").sum()), "con_punto": len(hoteles)},
        "apartaments_turistics": {
            "total": int((h["tipo"] == "apartament_turistic").sum()),
            "con_punto": len(apartamentos)},
        "con_precio": int(con_punto["precio"].notna().sum()),
    }


def exportar_restauracion() -> dict:
    ruta = BRONZE / "restauracion_con_municipio.csv"
    if not ruta.exists():
        return {"total": 0, "con_punto": 0}
    d = pd.read_csv(ruta)
    d = d[pd.to_numeric(d["latitud"], errors="coerce").notna()]
    # Solo la provincia: OSM devolvió locales de fuera al consultar por caja envolvente.
    d = d[d["municipio_poligono"].notna()]

    puntos = [{
        "nom": sin_nan(r["nombre_comercial"]),
        "tipo": sin_nan(r["tipo_local"]),
        "cocina": sin_nan(r["tipo_cocina"]),
        "mun": sin_nan(r["municipio_poligono"]),
        "barrio": sin_nan(r.get("barrio")),
        "lat": round(float(r["latitud"]), 6),
        "lon": round(float(r["longitud"]), 6),
    } for _, r in d.iterrows()]

    volcar(DESTINO / "restauracion.json", puntos)
    return {"total": len(puntos), "por_tipo": d["tipo_local"].value_counts().to_dict()}


def exportar_vut(geo: pd.DataFrame) -> dict:
    """Las VUT son viviendas: solo agregados, nunca puntos."""
    v = pd.read_csv(BRONZE / "vut_unificados.csv", dtype=str)
    v = completar_coordenadas(v, geo)
    v["plazas_n"] = pd.to_numeric(v["plazas"], errors="coerce")

    por_barrio = (v[v["barrio"].notna()].groupby("barrio")
                  .agg(licencias=("licencia_id", "size"), plazas=("plazas_n", "sum"))
                  .reset_index())
    por_barrio["plazas"] = por_barrio["plazas"].fillna(0).astype(int)

    por_municipio = (v.groupby("municipio")
                     .agg(licencias=("licencia_id", "size"), plazas=("plazas_n", "sum"),
                          con_coordenada=("lat", "count"))
                     .reset_index())
    por_municipio["plazas"] = por_municipio["plazas"].fillna(0).astype(int)

    (DESTINO / "vut_por_barrio.json").write_text(
        por_barrio.to_json(orient="records", force_ascii=False), encoding="utf-8")
    (DESTINO / "vut_por_municipio.json").write_text(
        por_municipio.to_json(orient="records", force_ascii=False), encoding="utf-8")
    return {"total": len(v), "barrios": len(por_barrio), "municipios": len(por_municipio)}


def exportar_airbnb() -> dict:
    """Coordenadas desplazadas ~200 m por la fuente: solo agregados."""
    a = pd.read_csv(GOLD / "airbnb_situacion_licencia.csv")
    por_barrio = (a.groupby("neighbourhood")
                  .agg(anuncios=("id", "size"),
                       sujetos_vut=("sujeto_a_vut", "sum"),
                       sin_licencia=("sin_licencia", "sum"),
                       distrito=("neighbourhood_group", "first"))
                  .reset_index().rename(columns={"neighbourhood": "barrio"}))
    for c in ("sujetos_vut", "sin_licencia"):
        por_barrio[c] = por_barrio[c].astype(int)

    (DESTINO / "airbnb_por_barrio.json").write_text(
        por_barrio.to_json(orient="records", force_ascii=False), encoding="utf-8")
    return {"total": len(a), "barrios": len(por_barrio)}


def main() -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)
    geo = cargar_geocodificado()
    print(f"Coordenadas geocodificadas utilizables: {len(geo):,}\n")

    resumen = {
        **exportar_hoteles(geo),
        "restauracion": exportar_restauracion(),
        "vut": exportar_vut(geo),
        "airbnb": exportar_airbnb(),
    }
    (DESTINO / "resumen.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")

    for nombre, datos in resumen.items():
        print(f"  {nombre:14s} {datos}")
    print(f"\nGuardado en {DESTINO.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
