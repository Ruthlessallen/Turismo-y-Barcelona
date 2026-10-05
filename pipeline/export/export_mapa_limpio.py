"""Datos del mapa limpio: tres capas de puntos y las cifras de hoy por barrio.

Sustituye al mapa de sustitucion 2028 como pagina principal, pero no lo borra: `/mapa-anterior`
sigue leyendo sus propios ficheros, que este script no toca.

**Pisos turisticos como punto.** Es una decision del proyecto (2026-10-04) que contradice la
politica anterior de publicar las viviendas solo agregadas. Para acotar el efecto, cada punto
lleva solo lo que el mapa pinta: coordenada, plazas, dormitorios, precio por plaza y banda. Ni id,
ni nombre del anuncio, ni anfitrion, ni numero de licencia. La coordenada ya viene desplazada
hasta 150 m por Inside Airbnb, y aqui se redondea a 5 decimales (~1 m), no se afina.

**Demanda de los restaurantes hoy.** Cada turista alojado reparte un punto, a partes iguales,
entre los locales que tiene a menos de 200 m (el mismo criterio que `modelar_sustitucion.py`).
Turistas por noche = plazas x ocupacion: 38,3% en pisos (estimada, no hay dato oficial) y 67,9%
en hoteles (INE, por plazas: aqui se cuentan personas, no habitaciones). **Los de piso cuentan la
mitad** (`PESO_PISO_EN_RESTAURACION`): con cocina propia cenan menos fuera. El peso es un supuesto.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
GOLD = RAIZ / "data" / "gold"
DESTINO = RAIZ / "data" / "exports" / "mapa"
sys.path.insert(0, str(RAIZ / "pipeline" / "gold"))
from bandas import por_habitacion, por_plaza  # noqa: E402
from modelar_sustitucion import OCUPACION_AIRBNB, RADIO_COMIDA_M, proyectar  # noqa: E402

OCUPACION_HOTEL_PLAZAS = 0.679
OCUPACION_AIRBNB_ALTA = 0.48  # extremo alto del rango 38-48% que se maneja para los pisos
# Un turista de piso tiene cocina; uno de hotel, no. Es un supuesto del proyecto (2026-10-04), no un
# dato: no sabemos cuanto cocina nadie. Con 0 solo contarian los hoteles; con 1, los dos igual.
PESO_PISO_EN_RESTAURACION = 0.5
BLOQUE = 400  # filas de alojamiento por bloque: la matriz entera, 7.584 x 9.479, no cabe holgada


# Variantes del mismo nombre comercial que el censo escribe distinto. Solo las evidentes: agrupar
# por parecido de texto uniria negocios distintos.
ALIAS_MARCA = {"STARBUCKS COFFEE": "STARBUCKS"}


def marca(nombre) -> str | None:
    """Nombre comercial normalizado, para contar cuantos locales comparten nombre.

    **No es la empresa.** El censo municipal de la ciudad trae el nombre del rotulo, no el CIF ni
    la razon social (esos solo los trae el censo de la Diputacio, que no cubre Barcelona). Dos
    locales con el mismo rotulo suelen ser una cadena, pero no esta garantizado, y una empresa con
    rotulos distintos cuenta como varias.
    """
    if pd.isna(nombre):
        return None
    t = unicodedata.normalize("NFKD", str(nombre)).encode("ascii", "ignore").decode().upper()
    t = re.sub(r"[^A-Z0-9& ]", "", t).strip()
    t = ALIAS_MARCA.get(t, t)
    return t.replace("MC DONALDS", "MCDONALDS") or None


def volcar(nombre: str, datos) -> None:
    (DESTINO / nombre).write_text(
        json.dumps(datos, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def num(v, cifras=None):
    if pd.isna(v):
        return None
    return round(float(v), cifras) if cifras is not None else int(round(float(v)))


def texto(v):
    return None if pd.isna(v) else str(v)


def pisos() -> pd.DataFrame:
    a = pd.read_csv(GOLD / "airbnb_para_web.csv", low_memory=False)
    estimado = a["precio_plaza_anual"].isna()
    precio = a["precio_plaza_anual"].fillna(a["precio_plaza_final"])
    return pd.DataFrame({
        "anfitrion": a["host_name"],
        "lat": a["latitude"], "lon": a["longitude"], "barrio": a["neighbourhood"],
        "plazas": a["accommodates"], "dorm": a["bedrooms"],
        # Un estudio declara 0 dormitorios y sigue alojando gente: cuenta como uno.
        "hab_piso": pd.to_numeric(a["bedrooms"], errors="coerce").where(a["bedrooms"] > 0)
        .fillna((a["accommodates"] / 2).round()).clip(lower=1),
        "precio": precio, "banda": a["banda_plaza"],
        # Lo que cuesta la noche del piso entero, que es lo que se alquila. Anualizado, no el
        # precio de portada: sale del precio por plaza corregido de temporada.
        "precio_piso": precio * a["accommodates"],
        "origen": np.where(precio.isna(), None, np.where(estimado, "estimado", "observado")),
    })


def razon_social(texto) -> str | None:
    """Razon social tal como la publica el registro, sin el rotulo entre parentesis.

    `No aplica` es el marcador de la fuente para titular persona fisica: no se publica. Tampoco el
    CIF. Solo el nombre de la sociedad, que es un dato del registro publico de empresas.
    """
    if pd.isna(texto) or str(texto).strip().lower() == "no aplica":
        return None
    t = re.sub(r"\(.*?\)", "", str(texto)).strip(" .,").upper()
    return re.sub(r"\s+", " ", t) or None


def hoteles() -> pd.DataFrame:
    h = pd.read_csv(GOLD / "alojamientos_reglados.csv", dtype={"licencia_id": str},
                    low_memory=False)
    h = h[(h["municipio"] == "Barcelona") & (h["tipo"] == "hotel") & h["lat"].notna()]
    reg = pd.read_csv(RAIZ / "data" / "raw" / "registre_turisme"
                      / "hoteles_y_apartaments_turistics_provincia_barcelona.csv",
                      dtype=str, usecols=["n_mero_inscripci", "ra_social_del_titular"])
    reg["k"] = reg["n_mero_inscripci"].str.strip().str.upper()
    h = h.assign(k=h["licencia_id"].str.upper()).merge(
        reg[["k", "ra_social_del_titular"]].drop_duplicates("k"), on="k", how="left")
    return pd.DataFrame({
        "titular": h["ra_social_del_titular"].map(razon_social),
        "nom": h["nombre_comercial"], "cat": h["categoria"], "barrio": h["barrio"],
        "lat": h["lat"], "lon": h["lon"], "plazas": h["plazas"], "hab": h["habitaciones"],
        "precio_hab": h["precio_noche_final"], "banda_hab": h["banda_precio"],
        "precio": h["precio_plaza"], "banda": h["banda_plaza"], "origen": h["origen_precio"],
    }).reset_index(drop=True)


def a_locales(lat, lon, valor, r: pd.DataFrame) -> np.ndarray:
    """Reparte `valor` (turistas por noche) de cada alojamiento entre los locales a <200 m."""
    A = proyectar(lat, lon)
    L = proyectar(r["latitud"], r["longitud"])
    valor = np.asarray(valor, float)
    tur = np.zeros(len(r))
    for i in range(0, len(A), BLOQUE):
        a = A[i:i + BLOQUE]
        metros = np.sqrt(((a[:, None, :] - L[None, :, :]) ** 2).sum(axis=2)) * 1000
        dentro = (metros <= RADIO_COMIDA_M).astype(float)
        huerfanos = dentro.sum(axis=1) == 0
        if huerfanos.any():
            dentro[huerfanos, metros[huerfanos].argmin(axis=1)] = 1.0
        reparto = dentro / dentro.sum(axis=1, keepdims=True)
        tur += valor[i:i + BLOQUE] @ reparto
    return tur


def absorbido_2028() -> pd.DataFrame:
    """Turistas por noche que cada hotel recibe de los pisos que desaparecen (un año medio).

    Es el reparto del modelo de sustitucion con el peso 0,5 entre precio y barrio, sin tocar nada
    de el: se llama, no se reimplementa. En un año medio caben todos, asi que el total es el de los
    turistas de los pisos (la misma cifra que en la portada).
    """
    import modelar_sustitucion as m

    vut, hot = m.cargar()
    distancia, cercania, parecido = m.matrices(vut, hot)
    vut["por_habitacion"] = vut["accommodates"] / vut["dormitorios"]
    momento = m.MOMENTOS["anio_medio"]
    vut["ocupacion"] = m.OCUPACION_AIRBNB
    vut["demanda"] = vut["dormitorios"] * m.OCUPACION_AIRBNB
    capacidad = (hot["habitaciones"] * (1 - momento["ocupacion_hotel"])).to_numpy()
    asignacion = m.repartir(vut, hot, distancia, cercania, parecido, 0.5, capacidad)
    col = asignacion[asignacion["hotel_idx"] >= 0]
    tur = col["habitaciones"].to_numpy() * vut["por_habitacion"].to_numpy()[col["vut_idx"].to_numpy()]
    por_hotel = np.zeros(len(hot))
    np.add.at(por_hotel, col["hotel_idx"].to_numpy(), tur)
    return pd.DataFrame({"lat": hot["lat"], "lon": hot["lon"], "tur": por_hotel})


def operador(serie: pd.Series, minimo: int):
    """El nombre que mas alojamientos reune en el barrio, si llega al minimo."""
    c = serie.dropna().value_counts()
    if c.empty or c.iloc[0] < minimo:
        return None
    return {"nom": str(c.index[0]), "n": int(c.iloc[0])}


def mediana(serie: pd.Series):
    v = pd.to_numeric(serie, errors="coerce").dropna()
    return round(float(v.median()), 1) if len(v) else None


def banda(serie: pd.Series):
    m = mediana(serie)
    return None if m is None else por_plaza(pd.Series([m])).iloc[0]


def banda_habitacion(serie: pd.Series):
    m = mediana(serie)
    return None if m is None else por_habitacion(pd.Series([m])).iloc[0]


def marca_principal(g: pd.DataFrame):
    """El nombre comercial que mas locales repite en el barrio, si alguno se repite."""
    c = g["nombre"].map(marca).value_counts()
    if c.empty or c.iloc[0] < 2:
        return None
    return {"nom": str(c.index[0]), "locales": int(c.iloc[0])}


def dashboard(p: pd.DataFrame, h: pd.DataFrame, ab: pd.DataFrame) -> dict:
    """Las cifras de la portada: solo numeros, un ano medio, sin escenarios.

    Los turistas nuevos son los que los pisos aportan a los hoteles al desaparecer (reparto del
    modelo de sustitucion, un ano medio), frente a los que alojan hoy los hoteles por plazas.
    """
    todos = pd.read_csv(GOLD / "airbnb_excluidos_web.csv", low_memory=False, usecols=["id"])
    turistas_hotel_hoy = float((h["plazas"].fillna(0) * OCUPACION_HOTEL_PLAZAS).sum())
    nuevos = float(ab["tur"].sum())
    titulares = h["titular"].dropna().value_counts().head(5)
    bandas = h["banda_hab"].value_counts()
    return {
        "hoteles": {
            "total": len(h), "habitaciones": int(h["hab"].fillna(0).sum()),
            "plazas": int(h["plazas"].fillna(0).sum()),
            "bandas": {b: int(bandas.get(b, 0)) for b in ("€", "€€", "€€€", "€€€€")},
            "sin_banda": int(h["banda_hab"].isna().sum()),
            "titulares": [{"nom": k, "n": int(v)} for k, v in titulares.items()],
            "turistas_hoy": round(turistas_hotel_hoy),
            "turistas_nuevos": round(nuevos),
            "turistas_nuevos_pct": round(nuevos / turistas_hotel_hoy * 100, 1),
        },
        "pisos": {
            "anuncios_barridos": len(p) + len(todos),
            "total": len(p), "habitaciones": int(p["hab_piso"].sum()),
            "plazas": int(p["plazas"].sum()),
            # Orden de magnitud: ocupacion 38,3-48 % x 365 noches x precio de la noche del piso.
            "facturacion": [round(float(p["precio_piso"].fillna(0).sum() * 365 * OCUPACION_AIRBNB)),
                            round(float(p["precio_piso"].fillna(0).sum() * 365
                                        * OCUPACION_AIRBNB_ALTA))],
        },
    }


def main() -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)
    p, h = pisos(), hoteles()
    r = pd.read_csv(GOLD / "restauracion_bcn.csv", low_memory=False)
    r = r[r["latitud"].notna() & r["longitud"].notna()].reset_index(drop=True)
    hotel_hoy = a_locales(h["lat"], h["lon"], h["plazas"].fillna(0) * OCUPACION_HOTEL_PLAZAS, r)
    piso_hoy = a_locales(p["lat"], p["lon"], p["plazas"] * OCUPACION_AIRBNB, r)
    # Hoy: el de piso cuenta la mitad (cocina). En 2028 esos turistas duermen en hoteles, que no
    # tienen cocina, y cuentan enteros. De ahi sale cuantos clientes mas (o menos) puede haber.
    r["turistas"] = hotel_hoy + PESO_PISO_EN_RESTAURACION * piso_hoy
    ab = absorbido_2028()
    r["turistas_2028"] = hotel_hoy + a_locales(ab["lat"], ab["lon"], ab["tur"], r)
    r["mas_pct"] = np.where(r["turistas"] > 0,
                            (r["turistas_2028"] / r["turistas"].where(r["turistas"] > 0) - 1) * 100,
                            np.nan)

    volcar("puntos_pisos.json", [
        [round(x.lat, 5), round(x.lon, 5), num(x.plazas), num(x.dorm), num(x.precio_piso),
         num(x.precio, 1), texto(x.banda), texto(x.origen), x.barrio, num(x.hab_piso)] for x in p.itertuples()])
    volcar("puntos_hoteles.json", [{
        "nom": texto(x.nom), "titular": texto(x.titular), "cat": texto(x.cat),
        "barrio": texto(x.barrio), "lat": round(x.lat, 5), "lon": round(x.lon, 5), "plazas": num(x.plazas),
        "hab": num(x.hab), "banda_hab": texto(x.banda_hab),
        # Solo la banda: el mismo hotel se mueve un 22 % en quince dias y el modelo yerra un 27 %,
        # asi que un euro exacto de hotel diria mas de lo que sabemos.
        "banda": texto(x.banda), "origen": texto(x.origen),
    } for x in h.itertuples()])
    volcar("puntos_restaurantes.json", [{
        "nom": texto(x.nombre), "tipo": texto(x.tipo_local), "barrio": texto(x.barrio),
        "dir": texto(x.direccion), "lat": round(x.latitud, 5), "lon": round(x.longitud, 5),
        "tur": num(x.turistas, 1), "tur28": num(x.turistas_2028, 1),
        "mas": num(x.mas_pct, 0),
    } for x in r.itertuples()])

    # Umbral de «demanda alta»: el quintil superior de los locales que tienen algun turista cerca.
    con = r.loc[r["turistas"] > 0, "turistas"]
    umbral = float(con.quantile(0.8))
    r["alta"] = r["turistas"] >= umbral

    g_p, g_h, g_r = p.groupby("barrio"), h.groupby("barrio"), r.groupby("barrio")
    barrios = sorted(set(p["barrio"]) | set(h["barrio"].dropna()) | set(r["barrio"].dropna()))
    filas = []
    for b in barrios:
        gp = g_p.get_group(b) if b in g_p.groups else p.iloc[0:0]
        gh = g_h.get_group(b) if b in g_h.groups else h.iloc[0:0]
        gr = g_r.get_group(b) if b in g_r.groups else r.iloc[0:0]
        filas.append({
            "barrio": b,
            "pisos": len(gp), "plazas_pisos": int(gp["plazas"].sum()),
            "hoteles": len(gh), "plazas_hoteles": int(gh["plazas"].fillna(0).sum()),
            "restaurantes": len(gr), "alta": int(gr["alta"].sum()),
            # Rango y no una cifra: la ocupacion de los pisos no es un dato oficial.
            "turistas_pisos": [round(float(gp["plazas"].sum() * OCUPACION_AIRBNB)),
                               round(float(gp["plazas"].sum() * OCUPACION_AIRBNB_ALTA))],
            "turistas_hoteles": round(float(gh["plazas"].fillna(0).sum()
                                            * OCUPACION_HOTEL_PLAZAS)),
            # La unidad de alquiler no es la misma: el hotel alquila habitaciones, Airbnb alquila
            # el piso entero. Por eso se comparan habitaciones con pisos y la noche de una con la
            # noche del otro, no plazas con plazas.
            "habitaciones_hoteles": int(gh["hab"].fillna(0).sum()),
            "precio_pisos": mediana(gp["precio_piso"]),
            "banda_pisos": banda(gp["precio"]),  # por plaza: es la unica banda que tienen los pisos
            "banda_hoteles": banda_habitacion(gh["precio_hab"]),
            "marca": marca_principal(gr),
            "demanda_hoy": round(float(gr["turistas"].sum())),
            "demanda_2028": round(float(gr["turistas_2028"].sum())),
            # Orden de magnitud, no facturacion real: ocupacion x 365 noches x precio de la noche.
            "facturacion_pisos": [round(float(gp["precio_piso"].fillna(0).sum()
                                              * 365 * OCUPACION_AIRBNB)),
                                  round(float(gp["precio_piso"].fillna(0).sum()
                                              * 365 * OCUPACION_AIRBNB_ALTA))],
            # Hoteles: la sociedad titular. Pisos: el anfitrion segun Airbnb, solo a partir de 5
            # anuncios en el barrio, que separa al operador profesional del particular.
            "operador_hoteles": operador(gh["titular"], 2),
            "operador_pisos": operador(gp["anfitrion"], 5),
        })
    volcar("barrios_hoy.json", filas)
    volcar("dashboard.json", dashboard(p, h, ab))

    resumen = {
        "pisos": len(p), "hoteles": len(h), "restaurantes": len(r),
        "pisos_sin_banda": int(p["banda"].isna().sum()),
        "hoteles_sin_banda": int(h["banda"].isna().sum()),
        "restaurantes_con_turistas": int((r["turistas"] > 0).sum()),
        "umbral_demanda_alta_turistas_noche": round(umbral, 2),
        "restaurantes_demanda_alta": int(r["alta"].sum()),
        "turistas_noche_total": round(float(r["turistas"].sum())),
        "barrios": len(filas),
    }
    print(json.dumps(resumen, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
