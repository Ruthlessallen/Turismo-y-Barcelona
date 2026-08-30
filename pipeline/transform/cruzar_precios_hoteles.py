"""Cruza precios de hotel raspados con el registro oficial, y mide si el cruce es fiable.

Entrada
    data/raw/precios_hoteles/*.json   (o .csv) — salida del scraper de Apify
Salida
    data/processed/hoteles_con_precio.csv

El objetivo de este script **no es sumar precios**: es responder si el emparejamiento funciona.
Un precio pegado al hotel equivocado es peor que no tener precio, porque no se nota. Por eso el
informe final es de calidad de cruce, no de estadística de precios.

Estrategia, de más fiable a menos:

1. **Coordenada** — dos establecimientos a menos de 60 m con nombres parecidos son el mismo. Es
   el criterio fuerte, pero solo sirve para los 445 hoteles con `lat`/`lon` (ver `nivel_geo` en
   `docs/data-model.md`: fuera de Barcelona ciudad no hay coordenada).
2. **Nombre** — respaldo cuando no hay coordenada. Frágil: "Catalonia Ramblas" y "Catalonia Plaza"
   se parecen mucho y son hoteles distintos, así que exige un parecido alto.

Todo cruce por debajo del umbral se marca `dudoso` y **no se descarta en silencio**: queda en la
salida con su motivo, para poder revisarlo.

Aviso sobre la fuente: estos precios se obtienen raspando un portal de reservas, cuyos términos
lo prohíben. Sirven para explorar y modelar en local; para publicar cifras en el dashboard hace
falta una fuente citable (ver `docs/architecture.md` → Integraciones externas).
"""

from __future__ import annotations

import json
import math
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
DIR_PRECIOS = RAIZ / "data" / "raw" / "precios_hoteles"
RUTA_HOTELES = RAIZ / "data" / "processed" / "hoteles_y_apartaments_unificados.csv"
RUTA_SALIDA = RAIZ / "data" / "processed" / "hoteles_con_precio.csv"

# Un hotel y su ficha raspada rara vez caen en el mismo punto exacto: el portal geolocaliza por
# portal o por centroide del edificio. 60 m absorbe esa holgura sin llegar al edificio de al lado.
METROS_MAXIMOS = 60
# Cuando el nombre del registro aparece entero dentro del raspado, la propia contención ya acota
# bastante, así que se puede admitir más distancia sin perder fiabilidad.
METROS_CON_NOMBRE = 150
# Con coordenada coincidente basta un parecido moderado; sin ella hay que ser mucho más estricto.
PARECIDO_CON_COORDENADA = 0.55
PARECIDO_SOLO_NOMBRE = 0.85

# Palabras que aparecen en casi todas las fichas y solo añaden ruido al comparar nombres.
RUIDO = {"HOTEL", "HOTELES", "APARTHOTEL", "BARCELONA", "BCN", "THE", "EL", "LA", "LOS", "LAS",
         "DE", "DEL", "Y", "AND", "BY", "A", "&"}


def quitar_acentos(texto: object) -> str:
    """Mayúsculas sin acentos ni signos, para comparar cadenas de fuentes distintas."""
    if not isinstance(texto, str):
        return ""
    sin = "".join(c for c in unicodedata.normalize("NFD", texto)
                  if unicodedata.category(c) != "Mn")
    return re.sub(r"[^\w\s]", " ", sin.upper())


def clave_nombre(texto: object) -> str:
    """Reduce un nombre comercial a sus palabras distintivas."""
    palabras = [p for p in quitar_acentos(texto).split() if p and p not in RUIDO]
    return " ".join(palabras)


def parecido(a: str, b: str) -> float:
    """Similitud 0-1 entre dos nombres ya normalizados."""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def contenido_en(registro: str, raspado: str) -> bool:
    """¿Están todas las palabras distintivas del registro dentro del nombre raspado?

    Hace falta porque las dos fuentes nombran distinto: el registro guarda el nombre
    administrativo, casi siempre una palabra ("Goya", "Lirio"), mientras que el portal muestra la
    marca comercial completa ("Hotel Goya Barcelona"). `SequenceMatcher` penaliza esa diferencia
    de longitud y da parecidos de 0,3 en pares que son el mismo hotel; la contención no.

    Se exige que la palabra más larga tenga al menos 4 letras: con "SOL" o "MAR" cualquier nombre
    contendría a cualquiera.
    """
    palabras_r = [p for p in registro.split() if p]
    if not palabras_r or max(len(p) for p in palabras_r) < 4:
        return False
    palabras_x = set(raspado.split())
    return all(p in palabras_x for p in palabras_r)


def metros(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia aproximada en metros. A escala de ciudad, la aproximación plana sobra."""
    dlat = (lat2 - lat1) * 111_320
    dlon = (lon2 - lon1) * 111_320 * math.cos(math.radians((lat1 + lat2) / 2))
    return math.hypot(dlat, dlon)


def cargar_raspados() -> pd.DataFrame:
    """Lee lo que haya dejado el scraper: JSON o CSV, con nombres de campo variables."""
    if not DIR_PRECIOS.exists():
        raise SystemExit(
            f"No existe {DIR_PRECIOS.relative_to(RAIZ)}.\n"
            "Guarda ahí la exportación del scraper (JSON o CSV) y vuelve a ejecutar."
        )
    ficheros = sorted(list(DIR_PRECIOS.glob("*.json")) + list(DIR_PRECIOS.glob("*.csv")))
    if not ficheros:
        raise SystemExit(f"No hay ficheros en {DIR_PRECIOS.relative_to(RAIZ)}")

    trozos = []
    for f in ficheros:
        if f.suffix == ".json":
            datos = json.loads(f.read_text(encoding="utf-8"))
            trozos.append(pd.json_normalize(datos if isinstance(datos, list) else [datos]))
        else:
            trozos.append(pd.read_csv(f))
        print(f"  leído {f.name}: {len(trozos[-1]):,} filas")
    return pd.concat(trozos, ignore_index=True)


def localizar_columna(df: pd.DataFrame, candidatas: list[str]) -> str | None:
    """Encuentra una columna por varios nombres posibles: cada scraper la llama distinto."""
    normalizadas = {c.lower().replace("_", "").replace(".", ""): c for c in df.columns}
    for cand in candidatas:
        clave = cand.lower().replace("_", "").replace(".", "")
        if clave in normalizadas:
            return normalizadas[clave]
    return None


def preparar_raspados(bruto: pd.DataFrame) -> pd.DataFrame:
    """Renombra a un esquema estable, sea cual sea el scraper de origen."""
    mapa = {
        "nombre": ["name", "hotelName", "title", "displayName"],
        "lat": ["latitude", "lat", "location.lat", "coordinates.lat", "gpsCoordinates.latitude"],
        "lon": ["longitude", "lng", "lon", "location.lng", "coordinates.lng",
                "gpsCoordinates.longitude"],
        "precio": ["nightly", "price", "pricePerNight", "rate", "price.value", "nightlyPrice"],
        "moneda": ["currency", "currencyCode", "price.currency"],
        "estrellas": ["stars", "starRating", "hotelClass", "rating.stars"],
        "puntuacion": ["rating", "reviewScore", "score", "guestRating"],
        "direccion": ["address", "formattedAddress", "location.address"],
        # Rango entre portales para el mismo hotel: dice cuánto varía el precio según dónde se
        # reserve, que es más informativo que un único importe.
        "oferta_min": ["oferta_min", "lowest", "minPrice"],
        "oferta_max": ["oferta_max", "maxPrice"],
        "n_ofertas": ["n_ofertas", "offers", "totalOffers"],
    }
    salida = pd.DataFrame(index=bruto.index)
    for destino, candidatas in mapa.items():
        col = localizar_columna(bruto, candidatas)
        salida[destino] = bruto[col] if col else pd.NA
        if col is None and destino in ("nombre", "precio"):
            print(f"  AVISO: no se encontró columna para '{destino}'")

    for c in ("lat", "lon", "precio", "puntuacion", "oferta_min", "oferta_max"):
        salida[c] = pd.to_numeric(salida[c], errors="coerce")
    salida["clave"] = salida["nombre"].apply(clave_nombre)
    return salida[salida["nombre"].notna()]


def cruzar(hoteles: pd.DataFrame, raspados: pd.DataFrame) -> pd.DataFrame:
    """Empareja cada hotel oficial con su ficha raspada. Devuelve una fila por hotel oficial."""
    filas = []
    con_coord = raspados[raspados["lat"].notna() & raspados["lon"].notna()]

    for _, h in hoteles.iterrows():
        mejor, metodo, distancia, sim = None, "sin_cruce", None, 0.0
        clave_h = clave_nombre(h["nombre_comercial"])

        # 1. Por coordenada, cuando el hotel oficial la tiene.
        if pd.notna(h["lat"]) and pd.notna(h["lon"]) and len(con_coord):
            d = con_coord.apply(
                lambda r: metros(float(h["lat"]), float(h["lon"]), r["lat"], r["lon"]), axis=1)
            cerca = con_coord[d <= METROS_MAXIMOS]
            if len(cerca):
                sims = cerca["clave"].apply(lambda c: parecido(clave_h, c))
                if sims.max() >= PARECIDO_CON_COORDENADA:
                    i = sims.idxmax()
                    mejor, metodo, distancia, sim = raspados.loc[i], "coordenada", d[i], sims.max()

        # 2. Nombre contenido + cerca. Salva los casos en que el registro guarda "Goya" y el
        # portal "Hotel Goya Barcelona": misma casa, parecido literal bajísimo. Se admite un radio
        # mayor que en el paso 1 porque la contención del nombre ya es una condición fuerte.
        if mejor is None and clave_h and pd.notna(h["lat"]) and len(con_coord):
            d = con_coord.apply(
                lambda r: metros(float(h["lat"]), float(h["lon"]), r["lat"], r["lon"]), axis=1)
            cerca = con_coord[(d <= METROS_CON_NOMBRE)]
            contenidos = cerca[cerca["clave"].apply(lambda c: contenido_en(clave_h, c))]
            if len(contenidos) == 1:  # dos candidatos igual de válidos no resuelven nada
                i = contenidos.index[0]
                mejor, metodo, distancia = raspados.loc[i], "nombre_cerca", d[i]
                sim = parecido(clave_h, raspados.loc[i, "clave"])

        # 3. Nombre único en toda la ciudad. Es la única vía para los hoteles sin coordenada en
        # nuestro registro (309 de 754): si "ABREVADERO" aparece en una sola ficha de las 1.500,
        # no hay ambigüedad que resolver. Si aparece en varias, no se elige ninguna.
        if mejor is None and clave_h:
            contenidos = raspados[raspados["clave"].apply(lambda c: contenido_en(clave_h, c))]
            if len(contenidos) == 1:
                i = contenidos.index[0]
                mejor, metodo = raspados.loc[i], "nombre_unico"
                sim = parecido(clave_h, raspados.loc[i, "clave"])

        # 4. Parecido literal alto, como último recurso.
        if mejor is None and clave_h:
            sims = raspados["clave"].apply(lambda c: parecido(clave_h, c))
            if len(sims) and sims.max() >= PARECIDO_SOLO_NOMBRE:
                i = sims.idxmax()
                mejor, metodo, sim = raspados.loc[i], "nombre", sims.max()

        fila = {
            "licencia_id": h["licencia_id"],
            "nombre_registro": h["nombre_comercial"],
            "categoria": h["categoria"],
            "habitaciones": h["habitaciones"],
            "plazas": h["plazas"],
            "metodo_cruce": metodo,
            "similitud": round(sim, 2),
            "distancia_m": round(distancia) if distancia is not None else None,
        }
        if mejor is not None:
            fila |= {
                "nombre_raspado": mejor["nombre"],
                "precio": mejor["precio"],
                "moneda": mejor["moneda"],
                "estrellas_raspadas": mejor["estrellas"],
                "puntuacion": mejor["puntuacion"],
                "oferta_min": mejor["oferta_min"],
                "oferta_max": mejor["oferta_max"],
            }
        filas.append(fila)

    d = pd.DataFrame(filas)

    # Una misma ficha raspada asignada a varios hoteles del registro señala un problema: o el
    # registro tiene tres licencias para un mismo establecimiento (LIMONAIA 1, 2 y 3), o el
    # emparejamiento por nombre ha juntado hoteles distintos. En ambos casos el precio no puede
    # atribuirse a uno solo, así que se marca.
    if "nombre_raspado" in d:
        usos = d["nombre_raspado"].value_counts()
        d["ficha_compartida"] = d["nombre_raspado"].map(usos).fillna(0).astype(int) > 1
    else:
        d["ficha_compartida"] = False

    # Un cruce solo por nombre, sin coordenada que lo respalde, es el más expuesto a error.
    d["dudoso"] = ((d["metodo_cruce"] == "nombre") & (d["similitud"] < 0.95)) | d["ficha_compartida"]
    return d


def informe(d: pd.DataFrame) -> None:
    """Calidad del cruce primero; los precios solo después, y sobre lo que cruzó bien."""
    print(f"\n{'—' * 60}\nCalidad del cruce sobre {len(d):,} hoteles del registro:")
    for metodo, n in d["metodo_cruce"].value_counts().items():
        print(f"  {metodo:12s}: {n:5,}  ({n / len(d):5.1%})")
    print(f"  {'dudosos':12s}: {int(d['dudoso'].sum()):5,}  ← revisar antes de usar")
    print(f"      de ellos, misma ficha en varios hoteles: {int(d['ficha_compartida'].sum()):,}")

    fiables = d[(d["metodo_cruce"] != "sin_cruce") & ~d["dudoso"] & d.get("precio").notna()]
    if fiables.empty:
        print("\nNingún cruce fiable con precio. Revisa que el scraper traiga nombre y coordenadas.")
        return

    print(f"\nPrecios sobre {len(fiables):,} cruces fiables:")
    print(f"  mediana: {fiables['precio'].median():.0f}  |  media: {fiables['precio'].mean():.0f}")
    por_cat = fiables.groupby("categoria")["precio"].agg(["size", "median"]).round(0)
    por_cat.columns = ["hoteles", "precio_mediano"]
    print(f"\n{por_cat.sort_values('precio_mediano').to_string()}")

    cobertura = len(fiables) / len(d)
    if cobertura < 0.5:
        print(f"\nCobertura del {cobertura:.1%}: insuficiente para hablar del parque hotelero.")
        print("Sirve para explorar, no para una media de ciudad.")


def main() -> None:
    print(f"Leyendo {DIR_PRECIOS.relative_to(RAIZ)}")
    raspados = preparar_raspados(cargar_raspados())
    print(f"  {len(raspados):,} fichas con nombre | {raspados['precio'].notna().sum():,} con precio")

    hoteles = pd.read_csv(RUTA_HOTELES, dtype=str)
    hoteles = hoteles[(hoteles["tipo"] == "hotel") & (hoteles["municipio"] == "Barcelona")].copy()
    for c in ("lat", "lon"):
        hoteles[c] = pd.to_numeric(hoteles[c], errors="coerce")
    print(f"  {len(hoteles):,} hoteles oficiales en la ciudad "
          f"({hoteles['lat'].notna().sum()} con coordenada)")

    d = cruzar(hoteles, raspados)
    informe(d)

    RUTA_SALIDA.parent.mkdir(parents=True, exist_ok=True)
    d.to_csv(RUTA_SALIDA, index=False, encoding="utf-8")
    print(f"\nGuardado en {RUTA_SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
