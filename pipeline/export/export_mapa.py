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
- `desplazada` — Inside Airbnb mueve cada anuncio hasta 150 m a propósito

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


def exportar_hoteles() -> dict:
    """Hoteles y apartaments turistics, en ficheros separados.

    Van aparte porque son figuras legales distintas y confundirlas es el error mas facil de
    cometer con estos datos: la eliminacion de 2028 afecta a las VUT, no a los AT, que seguiran
    operando. Mezclarlos en una sola capa daria a entender que todo el alojamiento en apartamento
    desaparece.

    **Se lee de `gold/alojamientos_reglados.csv`, no del censo de bronze.** Antes se leia el censo
    y el precio crudo por separado, y llegaba al mapa un precio de una ventana de septiembre sin
    banda y sin decir si estaba medido o estimado. Cada punto lleva ahora `banda`, `estimado` y
    `apoyo`, que es lo que `docs/web-checklist.md` exige para no dar por sabido un precio imputado.
    """
    h = pd.read_csv(GOLD / "alojamientos_reglados.csv", dtype={"licencia_id": str},
                    low_memory=False)
    con_punto = h[h["lat"].notna()]

    puntos = [{
        "id": r["licencia_id"],
        "nom": sin_nan(r["nombre_comercial"]),
        "tipo": sin_nan(r["tipo"]),
        "cat": sin_nan(r["categoria"]),
        "plazas": int(r["plazas"]) if pd.notna(r["plazas"]) else None,
        "hab": int(r["habitaciones"]) if pd.notna(r["habitaciones"]) else None,
        "precio": round(float(r["precio_noche_final"])) if pd.notna(r["precio_noche_final"]) else None,
        "banda": sin_nan(r["banda_precio"]),
        # Sin estas dos, un precio estimado seria indistinguible de uno medido en el mapa.
        "estimado": bool(r["precio_es_estimado"]) if pd.notna(r["precio_es_estimado"]) else None,
        "apoyo": sin_nan(r["apoyo_estimacion"]),
        "mun": sin_nan(r["municipio"]),
        "barrio": sin_nan(r["barrio"]),
        "lat": round(float(r["lat"]), 6),
        "lon": round(float(r["lon"]), 6),
        "prec": sin_nan(r["precision"]),
    } for _, r in con_punto.iterrows()]

    # Las 5 estimaciones sin ejemplos comparables salen sin banda: un hueco es mas honesto que un
    # numero que nadie puede contradecir (ver `apoyo_estimacion` en docs/data-model.md).
    for p in puntos:
        if p["apoyo"] == "escaso":
            p["banda"] = None
            p["precio"] = None

    hoteles = [p for p in puntos if p["tipo"] == "hotel"]
    apartamentos = [p for p in puntos if p["tipo"] == "apartament_turistic"]
    volcar(DESTINO / "hoteles.json", hoteles)
    volcar(DESTINO / "apartaments_turistics.json", apartamentos)

    con_banda = [p for p in puntos if p["banda"]]
    return {
        "hoteles": {"total": int((h["tipo"] == "hotel").sum()), "con_punto": len(hoteles)},
        "apartaments_turistics": {
            "total": int((h["tipo"] == "apartament_turistic").sum()),
            "con_punto": len(apartamentos)},
        "con_banda": len(con_banda),
        "banda_observada": len([p for p in con_banda if p["estimado"] is False]),
        "banda_estimada": len([p for p in con_banda if p["estimado"] is True]),
        "sin_banda_por_apoyo": len([p for p in puntos if p["apoyo"] == "escaso"]),
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
    """Coordenadas desplazadas hasta 150 m por la fuente: solo agregados por barrio.

    Se lee de `gold/airbnb_para_web.csv`, que produce `notebooks/revisar_airbnb_v2.ipynb`: trae el
    precio por plaza corregido de temporada y el estado de licencia contrastado contra el registro
    oficial. Antes se leia `airbnb_bcn.csv`, salida de un segundo pipeline que aplicaba otra criba
    --el mapa publicaba desde la cadena que no mandaba-- y que se ha retirado.
    Es la unica escala en la que la oferta de Airbnb y la hotelera se comparan: 221 EUR de un piso
    para cuatro y 174 EUR de una habitacion de hotel no dicen nada enfrentados.
    """
    a = pd.read_csv(GOLD / "airbnb_para_web.csv", low_memory=False)
    # Los excluidos entran solo para poder decir cuantos hay y por que, no para contarlos como
    # oferta: son habitaciones, alojamiento reglado, anuncios apagados y repeticiones de una misma
    # vivienda. Publicar el total sin ese desglose diria que hay 15.406 pisos turisticos.
    fuera = pd.read_csv(GOLD / "airbnb_excluidos_web.csv", low_memory=False)
    # Capacidad latente: licencia vigente en el registro y sin actividad reciente en la plataforma.
    # No suma a `anuncios` --no es oferta anunciada-- pero la eliminacion de 2028 la alcanza igual,
    # asi que se publica al lado y no dentro. `recientes` separa lo que dejo de anunciarse hace
    # menos de dos anos de las licencias dormidas desde hace una decada: son dos cosas distintas
    # ante la pregunta de si esa vivienda puede volver al mercado.
    lat = pd.read_csv(GOLD / "airbnb_capacidad_latente.csv", low_memory=False)
    lat["anio_ultima_resena"] = pd.to_datetime(lat["last_review"], errors="coerce").dt.year

    def reparto(g: pd.DataFrame) -> dict:
        cuenta = g["banda_plaza"].value_counts()
        return {b: int(cuenta.get(b, 0)) for b in ("€", "€€", "€€€", "€€€€")}

    excluidos_barrio = fuera.groupby("neighbourhood").size()
    lat_barrio = {b: g for b, g in lat.groupby("neighbourhood")}

    filas = []
    for barrio, g in a.groupby("neighbourhood"):
        con_precio = g[g["precio_plaza_anual"].notna()]
        gl = lat_barrio.get(barrio)
        latente = {
            "viviendas": 0 if gl is None else len(gl),
            "plazas": 0 if gl is None else int(gl["accommodates"].sum()),
            "recientes": 0 if gl is None else int((gl["anio_ultima_resena"] >= 2024).sum()),
        }
        filas.append({
            "barrio": barrio,
            "distrito": g["neighbourhood_group"].iloc[0],
            "anuncios": len(g),
            "excluidos": int(excluidos_barrio.get(barrio, 0)),
            "con_licencia": int((g["estado_licencia"] == "con_licencia").sum()),
            "sin_licencia": int((g["estado_licencia"] == "sin_licencia").sum()),
            "sin_acreditar": int((g["estado_licencia"] == "licencia_sin_acreditar").sum()),
            "con_precio": len(con_precio),
            "precio_plaza_mediano": (round(float(con_precio["precio_plaza_anual"].median()), 1)
                                     if len(con_precio) else None),
            "bandas": reparto(g),
            "latente": latente,
        })

    volcar(DESTINO / "airbnb_por_barrio.json", filas)
    con = a["precio_plaza_anual"].notna()
    return {"sujetos_a_la_ley": len(a), "excluidos": len(fuera),
            "motivos": fuera["motivo_exclusion"].value_counts().to_dict(),
            "barrios": len(filas),
            "con_precio_plaza": int(con.sum()),
            "precio_plaza_mediano": round(float(a.loc[con, "precio_plaza_anual"].median()), 1),
            "capacidad_latente": {
                "viviendas": len(lat),
                "plazas": int(lat["accommodates"].sum()),
                "recientes": int((lat["anio_ultima_resena"] >= 2024).sum()),
                "barrios": lat["neighbourhood"].nunique()}}


def exportar_sustitucion() -> dict:
    """El escenario de 2028, por barrio y por escenario. Solo agregados.

    Lo produce `gold/modelar_sustitucion.py`. Se publican los cinco valores del peso porque el
    navegador no puede resolver los 5,2 millones de pares VUT-hotel: la barra de la web se mueve
    entre estos pasos, no de forma continua.

    **El peso no esta medido.** Se intento estimarlo con la demanda actual de Airbnb y no funciona
    --la distancia al centro no la predice y el coeficiente del precio sale con el signo cambiado--
    asi que la eleccion es de quien mira el mapa. Debe decirse al lado del control.
    """
    ruta = GOLD / "sustitucion_2028.csv"
    if not ruta.exists():
        return {"escenarios": 0}
    d = pd.read_csv(ruta)
    resumen_gold = pd.read_csv(GOLD / "calidad" / "sustitucion_resumen.csv")

    escenarios = {}
    for etiqueta, g in d.groupby("escenario"):
        escenarios[etiqueta] = [{
            "barrio": r["barrio"],
            "salen": int(r["plazas_que_salen"]),
            "llegan": int(r["plazas_que_llegan"]),
            "se_quedan": int(r["plazas_que_se_quedan"]),
            "sin_sitio": int(r["plazas_sin_sitio"]),
            "saldo": int(r["saldo"]),
            "km": None if pd.isna(r["km_mediano"]) else round(float(r["km_mediano"]), 2),
            "sobrecoste": None if pd.isna(r["sobrecoste_mediano"]) else round(
                float(r["sobrecoste_mediano"]), 1),
        } for _, r in g.iterrows()]

    volcar(DESTINO / "sustitucion_2028.json", {
        "escenarios": escenarios,
        "totales": resumen_gold.to_dict(orient="records"),
    })
    fila = resumen_gold.iloc[0]
    return {"escenarios": len(escenarios), "barrios": int(d["barrio"].nunique()),
            "ocupacion_partida": float(fila["ocupacion_partida"]),
            "plazas_vut": int(fila["plazas_vut"]),
            "plazas_regladas": int(fila["plazas_regladas"]),
            "sin_sitio": int(fila["plazas_sin_sitio"])}


def centroides_de_barrio() -> dict[str, list[float]]:
    """Punto donde anclar cada flecha, sacado de la geometria de barrios.

    Se usa `representative_point` y no el centroide: el centroide de un barrio en forma de ele o
    de media luna puede caer fuera del propio barrio, y una flecha que sale del mar no se entiende.
    """
    from shapely.geometry import shape

    ruta = RAIZ / "data" / "exports" / "geo" / "barrios.geojson"
    geo = json.loads(ruta.read_text(encoding="utf-8"))
    puntos = {}
    for feature in geo["features"]:
        punto = shape(feature["geometry"]).representative_point()
        puntos[feature["properties"]["barrio"]] = [round(punto.y, 6), round(punto.x, 6)]
    return puntos


def exportar_flujos() -> dict:
    """Movimientos entre barrios: de donde sale el turista y donde acaba durmiendo.

    Solo agregados barrio a barrio, nunca el recorrido de una vivienda concreta. Se excluye el
    flujo de un barrio a si mismo --no es un movimiento-- y los de menos de 20 turistas, que
    llenarian el mapa de rayas sin decir nada.
    """
    ruta = GOLD / "sustitucion_flujos_2028.csv"
    if not ruta.exists():
        return {"flujos": 0}
    d = pd.read_csv(ruta)
    centros = centroides_de_barrio()

    # Un flujo cuyo barrio no esta en la geometria no se puede dibujar: se descarta y se cuenta,
    # para que la diferencia no desaparezca en silencio.
    sin_geometria = sorted({b for b in set(d["origen"]) | set(d["destino"]) if b not in centros})

    escenarios = {}
    for etiqueta, g in d.groupby("escenario"):
        dibujables = g[g["origen"].isin(centros) & g["destino"].isin(centros)]
        escenarios[etiqueta] = [{
            "origen": r["origen"],
            "destino": r["destino"],
            "turistas": int(round(r["turistas"])),
            "km": round(float(r["km_mediano"]), 2),
        } for _, r in dibujables.iterrows()]

    volcar(DESTINO / "flujos_2028.json", {"centroides": centros, "escenarios": escenarios})
    return {"flujos": int(len(d)), "barrios_sin_geometria": sin_geometria,
            "maximo_turistas": int(d["turistas"].max())}


def main() -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)
    geo = cargar_geocodificado()
    print(f"Coordenadas geocodificadas utilizables: {len(geo):,}\n")

    resumen = {
        **exportar_hoteles(),
        "restauracion": exportar_restauracion(),
        "vut": exportar_vut(geo),
        "airbnb": exportar_airbnb(),
        "sustitucion_2028": exportar_sustitucion(),
        "flujos_2028": exportar_flujos(),
    }
    (DESTINO / "resumen.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")

    for nombre, datos in resumen.items():
        print(f"  {nombre:14s} {datos}")
    print(f"\nGuardado en {DESTINO.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
