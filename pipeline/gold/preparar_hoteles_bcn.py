"""Deja en un solo fichero todas las variables de los alojamientos de Barcelona ciudad.

    python pipeline/transform/preparar_hoteles_bcn.py

Entradas
    data/bronze/hoteles_y_apartaments_unificados.csv   — censo del Registre de Turisme
    data/bronze/precios_hoteles_cruzados.csv                 — precios raspados ya cruzados
    data/bronze/geocodificacion_verificada.csv         — ICGC verificado contra polígono
    data/bronze/hoteles_geocodificados.csv             — geocodificación previa
    data/raw/hoteles/opendata_bcn_hotels_snapshot.csv     — barrio y distrito del Ajuntament
    data/raw/geometria/insideairbnb_barrios_barcelona.geojson

Salida
    data/gold/hoteles_bcn.csv

Sustituye a `preparar_hoteles_bcn_analisis.py` y `preparar_hoteles_bcn_imputacion.py`, que
construían este mismo dataset por dos caminos que no coincidían: 306 de 768 filas discrepaban en
la categoría y una rama perdía 322 coordenadas que la otra sí tenía.

**El precio no se divide.** Las dos fuentes ya cotizan por noche: Google devuelve `nightly` y
Booking trae `precio_noche_eur` calculado sobre su estancia de dos noches. `cruzar_precios_hoteles`
mapea `precio` desde esas dos columnas, así que volver a dividir entre dos dejaba la mediana
hotelera de Barcelona en 86 € cuando la real es 173 €.

**La categoría no es una escala.** Un hostal y un apartament turístic no tienen cero estrellas: no
se miden en estrellas. Ponerlos en 0,0 y 0,5 de una variable continua afirma que un AT vale menos
que un hostal y este menos que una estrella, que es una ordenación inventada. Aquí van `estrellas`
—solo donde existen, nula en el resto— y `tipo_alojamiento` como categórica.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
BRONZE = RAIZ / "data" / "bronze"
GOLD = RAIZ / "data" / "gold"
CALIDAD = GOLD / "calidad"
RAW = RAIZ / "data" / "raw"
SALIDA = GOLD / "hoteles_bcn.csv"

# Plaça de Catalunya, origen convencional de distancias en la ciudad.
CENTRO = (41.3870, 2.1700)

# Meses que cubre el raspado (estancias del 29-09 al 07-10 de 2026) y a qué banda oficial del INE
# corresponde cada categoría del Registre, para la corrección de temporada.
MESES_RASPADO = [9, 10]
BANDA_OFICIAL = {
    "1 and 2 gold stars and silver stars": [1.0, 2.0],
    "3 gold stars": [3.0],
    "4 gold stars": [4.0, 4.5],
    "5 gold stars": [5.0],
}
RADIO_TIERRA_KM = 6371.0

ESTRELLAS = {
    "gran luxe": 5.0, "5 estrelles": 5.0,
    "4 estrelles superior": 4.5, "4 estrelles": 4.0,
    "3 estrelles": 3.0, "2 estrelles": 2.0, "1 estrella": 1.0,
}

# El nombre comercial distingue lo que la categoría oficial agrupa entero bajo "No aplica".
SUBTIPOS = [
    ("hostal", r"hostal|hostel|alberg"),
    ("pension", r"pensio|pension"),
    ("residencia", r"residencia|residence"),
    ("apartamentos", r"apartament|apartment|aparthotel|apartahotel|suites"),
]

CADENAS = {
    "Catalonia": r"\bcatalonia\b|\btexfil\b",
    "H10": r"\bh10\b",
    "NH": r"\bnh\b",
    "Melia": r"\bmelia\b|\btryp\b",
    "HCC": r"\bhcc\b",
    "Eurostars": r"\beurostars\b|\bexe\b|\bhotusa\b",
    "Vincci": r"\bvincci\b",
    "Acta": r"\bacta\b",
    "Sercotel": r"\bsercotel\b",
    "Barcelo": r"\bbarcelo\b",
    "Abba": r"\babba\b",
    "Praktik": r"\bpraktik\b",
    "Chic & Basic": r"\bchic\s*(&|and)\s*basic\b",
    "Atiram": r"\batiram\b",
    "Derby": r"\bderby\b",
    "SB": r"\bsb\b",
    "Ibis / Accor": r"\bibis\b|\baccor\b|\bnovotel\b|\bmercure\b|\bsofitel\b",
    "Hilton": r"\bhilton\b|\bdoubletree\b",
    "Marriott": r"\bmarriott\b|\bac hotels\b|\bmoxy\b",
    "Ilunion": r"\bilunion\b|\bconfortel\b",
    "Hesperia": r"\bhesperia\b",
    "Silken": r"\bsilken\b",
    "Room Mate": r"\broom\s*mate\b",
    "Generator / Safestay": r"\bgenerator\b|\bsafestay\b",
    "Occidental / Ayre": r"\boccidental\b|\bayre\b",
}


def sin_acentos(texto: object) -> str:
    """Minúsculas y sin diacríticos.

    Comparar `Barceló` contra un literal acentuado depende de que el fichero y el script compartan
    codificación, y aquí no la compartían: el valor acabó guardado como `Barcel�` y su grupo
    no agrupaba con nada. Quitando los diacríticos de ambos lados la comparación deja de depender
    de eso.
    """
    if pd.isna(texto):
        return ""
    plano = unicodedata.normalize("NFKD", str(texto))
    return "".join(c for c in plano if not unicodedata.combining(c)).lower().strip()


def clave(texto: object) -> str:
    """Nombre reducido a letras y números, para detectar el mismo establecimiento dos veces."""
    return re.sub(r"[^a-z0-9]+", " ", sin_acentos(texto)).strip()


def distancia_km(lat: pd.Series, lon: pd.Series) -> pd.Series:
    """Haversine hasta Plaça Catalunya.

    La versión anterior hacía `sqrt(dlat^2 + dlon^2) * 111`, que da por hecho que un grado de
    longitud mide lo mismo que uno de latitud. A 41,4° un grado de longitud son 83 km, no 111: el
    eje este-oeste salía inflado un tercio, justo el eje en el que se estira la ciudad.
    """
    lat1, lon1 = np.radians(CENTRO[0]), np.radians(CENTRO[1])
    lat2, lon2 = np.radians(lat.astype(float)), np.radians(lon.astype(float))
    a = (np.sin((lat2 - lat1) / 2) ** 2
         + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2)
    return 2 * RADIO_TIERRA_KM * np.arcsin(np.sqrt(a))


def codigo_postal(valor: object) -> object:
    if pd.isna(valor):
        return np.nan
    digitos = re.sub(r"\D", "", str(valor).split(".")[0])
    return digitos.zfill(5) if digitos else np.nan


def cadena_hotelera(nombre: object, razon: object) -> str:
    texto = f"{sin_acentos(nombre)} {sin_acentos(razon)}"
    for nombre_cadena, patron in CADENAS.items():
        if re.search(patron, texto):
            return nombre_cadena
    return "Independiente"


def subtipo(nombre: object, razon: object) -> str:
    texto = f"{sin_acentos(nombre)} {sin_acentos(razon)}"
    for etiqueta, patron in SUBTIPOS:
        if re.search(patron, texto):
            return etiqueta
    return "sin_indicio"


def anadir_coordenadas(d: pd.DataFrame) -> pd.DataFrame:
    """Tres fuentes por orden de fiabilidad, sin pisar nunca una mejor con una peor."""
    d = d.copy()
    for c in ("lat", "lon"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d["origen_coord"] = np.where(d["lat"].notna(), "censo", None)

    verificada = pd.read_csv(BRONZE / "geocodificacion_verificada.csv",
                             dtype={"licencia_id": str}, low_memory=False)
    verificada = verificada[verificada["municipio_coincide"] == True]  # noqa: E712
    previa = pd.read_csv(BRONZE / "hoteles_geocodificados.csv", dtype={"licencia_id": str})

    for fuente, etiqueta in ((verificada, "icgc_verificada"), (previa, "icgc")):
        fuente = fuente[["licencia_id", "lat", "lon"]].drop_duplicates("licencia_id")
        d = d.merge(fuente, on="licencia_id", how="left", suffixes=("", "_n"))
        falta = d["lat"].isna() & d["lat_n"].notna()
        d.loc[falta, "lat"] = d.loc[falta, "lat_n"]
        d.loc[falta, "lon"] = d.loc[falta, "lon_n"]
        d.loc[falta, "origen_coord"] = etiqueta
        d = d.drop(columns=["lat_n", "lon_n"])
    return d


def anadir_barrio(d: pd.DataFrame) -> pd.DataFrame:
    """Barrio por punto dentro de polígono; solo sin coordenada se recurre al nombre.

    La versión anterior asignaba la moda del código postal, que reparte mal: un CP del Eixample
    cubre varios barrios y todos acababan etiquetados como el más frecuente de ellos.
    """
    import geopandas as gpd

    d = d.copy()
    # `object`, no float: inicializarlas con NaN las tipa como float64 y luego no admiten texto.
    d["barrio"] = pd.Series(pd.NA, index=d.index, dtype="object")
    d["distrito"] = pd.Series(pd.NA, index=d.index, dtype="object")

    barrios = gpd.read_file(RAW / "geometria" / "insideairbnb_barrios_barcelona.geojson")
    con_punto = d["lat"].notna() & d["lon"].notna()
    puntos = gpd.GeoDataFrame(
        d[con_punto], crs="EPSG:4326",
        geometry=gpd.points_from_xy(d.loc[con_punto, "lon"], d.loc[con_punto, "lat"]))
    unido = gpd.sjoin(puntos, barrios[["neighbourhood", "neighbourhood_group", "geometry"]],
                      how="left", predicate="within")
    unido = unido[~unido.index.duplicated(keep="first")]
    d.loc[unido.index, "barrio"] = unido["neighbourhood"]
    d.loc[unido.index, "distrito"] = unido["neighbourhood_group"]

    # Open Data BCN para los que se quedaron sin punto.
    od = pd.read_csv(RAW / "hoteles" / "opendata_bcn_hotels_snapshot.csv", low_memory=False)
    od["licencia_id"] = od["name"].str.extract(r"(HB-\d{6})")
    od = (od.dropna(subset=["licencia_id"]).drop_duplicates("licencia_id")
            [["licencia_id", "addresses_neighborhood_name", "addresses_district_name"]])
    d = d.merge(od, on="licencia_id", how="left")
    d["barrio"] = d["barrio"].fillna(d["addresses_neighborhood_name"])
    d["distrito"] = d["distrito"].fillna(d["addresses_district_name"])
    return d.drop(columns=["addresses_neighborhood_name", "addresses_district_name"])


def incorporar_rescatados(d: pd.DataFrame) -> pd.DataFrame:
    """Suma los precios del segundo pase del cruce, si ya se ha ejecutado.

    Se leen del libro de emparejamientos los pares dados por buenos, ya sea por el emparejador
    (`auto`) o por una persona (`si`).

    `rescatar_precios_hoteles.py` lee este mismo fichero para saber a quién le falta precio, así
    que hay un orden entre los dos: preparar, rescatar, preparar. No es circular —el rescate solo
    devuelve pares licencia/precio— y es idempotente.
    """
    ruta = BRONZE / "precios_emparejamientos.csv"
    if not ruta.exists():
        return d
    r = pd.read_csv(ruta, dtype={"licencia_id": str})
    # `auto` lo acepto el emparejador por su cuenta; `si` lo confirmo una persona. Cualquier otro
    # valor —`no`, o vacio— es un par que no se ha dado por bueno y no debe aportar precio.
    r = r[r["veredicto"].astype(str).str.strip().str.lower().isin(["auto", "si", "sí"])]
    r = r[["licencia_id", "precio_rescatado"]].drop_duplicates("licencia_id")
    d = d.merge(r, on="licencia_id", how="left")
    nuevos = d["precio_noche"].isna() & d["precio_rescatado"].notna()
    d.loc[nuevos, "precio_noche"] = d.loc[nuevos, "precio_rescatado"]
    d.loc[nuevos, "origen_precio"] = "rescate"
    print(f"  precios incorporados del segundo pase: {int(nuevos.sum())}")
    return d.drop(columns="precio_rescatado")


def a_equivalente_anual(d: pd.DataFrame) -> pd.DataFrame:
    """Quita a los precios el efecto de haberse consultado en temporada alta.

    El raspado corresponde a estancias del 29 de septiembre al 7 de octubre de 2026, y esas dos
    semanas están un 16% y un 13% por encima de la media anual según trece años de serie oficial.
    Un hotel a 175 € en esa ventana ronda los 151 € de media en el año.

    Importa para las bandas: con cortes en 100/175/300, un hotel a 178 € en septiembre cae en
    `€€€`, pero su media anual son 153 € y le corresponde `€€`. Sin corregir, la ciudad entera
    aparece una banda más cara de lo que es.

    El factor se toma por categoría, no global, porque la estacionalidad no es igual en todas: los
    cinco estrellas oscilan menos entre temporadas que los de una y dos.
    """
    ruta = BRONZE / "adr_estacionalidad.csv"
    if not ruta.exists():
        print("  (sin adr_estacionalidad.csv: no se aplica corrección de temporada)")
        d["precio_noche_anual"] = np.nan
        return d

    est = pd.read_csv(ruta)
    # La ventana cae a caballo de los dos meses, así que se promedian.
    ventana = est[est["mes"].isin(MESES_RASPADO)].groupby("categoria_oficial")["factor"].mean()

    banda = pd.Series(index=d.index, dtype=object)
    for nombre, estrellas in BANDA_OFICIAL.items():
        banda[d["estrellas"].isin(estrellas)] = nombre
    # Hostales y pensiones van con la banda de "estrellas de plata", que es donde los mete el INE.
    banda[d["estrellas"].isna()] = "1 and 2 gold stars and silver stars"

    factor = banda.map(ventana)
    d["factor_temporada"] = factor.round(3)
    d["precio_noche_anual"] = (d["precio_noche"] / factor).round(2)
    print(f"  factor de temporada por categoría: "
          f"{ {k[:18]: round(v, 3) for k, v in ventana.items()} }")
    return d


def marcar_duplicados(d: pd.DataFrame) -> pd.DataFrame:
    """Señala, sin borrar, el mismo establecimiento inscrito con dos licencias.

    No se elimina ninguno: dos licencias en el mismo portal pueden ser dos negocios distintos
    —un hostal y un hotel comparten edificio con frecuencia en Ciutat Vella— y resolver eso
    automáticamente perdería registros buenos. La columna deja el caso a la vista.
    """
    d = d.copy()
    d["_k"] = (d["nombre_comercial"].map(clave) + "|" + d["nombre_via"].map(clave)
               + "|" + d["numero"].astype(str))
    d["duplicado_probable"] = d.duplicated("_k", keep=False)
    return d.drop(columns="_k")


def main() -> None:
    censo = pd.read_csv(BRONZE / "hoteles_y_apartaments_unificados.csv", dtype=str, low_memory=False)
    d = censo[censo["municipio"] == "Barcelona"].copy()
    print(f"Barcelona ciudad: {len(d)} alojamientos en el censo")

    # Un registro sin `tipo` viene del fichero de hoteles del Ajuntament: es un hotel.
    d["tipo"] = d["tipo"].fillna("hotel")

    for c in ("plazas", "habitaciones"):
        d[c] = pd.to_numeric(d[c], errors="coerce")

    precios = pd.read_csv(BRONZE / "precios_hoteles_cruzados.csv", low_memory=False)
    fiables = precios[precios["precio"].notna() & ~precios["dudoso"].fillna(False)]
    d = d.merge(fiables[["licencia_id", "precio", "metodo_cruce", "puntuacion"]],
                on="licencia_id", how="left")
    # El precio ya viene por noche en ambas fuentes. No se divide.
    d = d.rename(columns={"precio": "precio_noche"})
    d["origen_precio"] = np.where(d["precio_noche"].notna(), "cruce_inicial", None)
    d = incorporar_rescatados(d)

    d = anadir_coordenadas(d)
    d = anadir_barrio(d)

    d["codigo_postal"] = d["codigo_postal"].map(codigo_postal)
    cat = d["categoria"].map(sin_acentos)
    d["estrellas"] = cat.map(ESTRELLAS)
    d["tipo_alojamiento"] = np.select(
        [d["estrellas"].notna(),
         d["tipo"].eq("apartament_turistic") | cat.eq("sense categoritzar")],
        ["hotel_estrellas", "apartament_turistic"], default="sin_estrellas")
    d["subtipo"] = [subtipo(n, r) for n, r in zip(d["nombre_comercial"], d["razon_social"])]
    d["cadena"] = [cadena_hotelera(n, r) for n, r in zip(d["nombre_comercial"], d["razon_social"])]
    d["es_cadena"] = d["cadena"].ne("Independiente")
    d["distancia_centro_km"] = distancia_km(d["lat"], d["lon"]).round(3)
    d = a_equivalente_anual(d)
    d = marcar_duplicados(d)

    columnas = ["licencia_id", "nombre_comercial", "razon_social", "tipo", "tipo_alojamiento",
                "subtipo", "categoria", "estrellas", "cadena", "es_cadena", "plazas",
                "habitaciones", "codigo_postal", "barrio", "distrito", "nombre_via", "numero",
                "lat", "lon", "origen_coord", "distancia_centro_km", "precio_noche",
                "precio_noche_anual", "factor_temporada", "origen_precio", "metodo_cruce",
                "puntuacion", "duplicado_probable"]
    d[columnas].to_csv(SALIDA, index=False, encoding="utf-8")

    print(f"\nCobertura sobre {len(d)}:")
    for c in ("estrellas", "plazas", "habitaciones", "codigo_postal", "barrio", "lat",
              "precio_noche"):
        print(f"  {c:20s} {d[c].notna().sum():4d}  ({d[c].notna().mean():6.1%})")
    print(f"\n  coordenadas por origen : {d['origen_coord'].value_counts(dropna=False).to_dict()}")
    print(f"  tipo_alojamiento       : {d['tipo_alojamiento'].value_counts().to_dict()}")
    print(f"  subtipo de sin_estrellas: "
          f"{d[d['tipo_alojamiento'] == 'sin_estrellas']['subtipo'].value_counts().to_dict()}")
    print(f"  en cadena              : {int(d['es_cadena'].sum())} "
          f"en {d['cadena'].nunique() - 1} grupos")
    print(f"  duplicado_probable     : {int(d['duplicado_probable'].sum())}")
    p = d["precio_noche"].dropna()
    print(f"\n  precio/noche: n={len(p)}  mediana={p.median():.0f} EUR  "
          f"p1={p.quantile(.01):.0f}  p99={p.quantile(.99):.0f}")
    print(f"\nGuardado en {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
