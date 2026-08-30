"""Cruza precios de hotel raspados con el registro oficial, y mide si el cruce es fiable.

Entrada
    data/raw/precios_hoteles/*.json   (o .csv) — salida del scraper de Apify
Salida
    data/processed/hoteles_cruce_base.csv

El objetivo de este script **no es sumar precios**: es responder si el emparejamiento funciona.
Un precio pegado al hotel equivocado es peor que no tener precio, porque no se nota. Por eso el
informe final es de calidad de cruce, no de estadística de precios.

Estrategia, de más fiable a menos:

1. **Coordenada** — a menos de 60 m y con nombres parecidos. El criterio fuerte, pero solo sirve
   para los 445 hoteles con `lat`/`lon` (ver `nivel_geo` en `docs/data-model.md`).
2. **Nombre idéntico** — una vez normalizado, "Acta Splendid" coincide letra por letra. Salva las
   fuentes que no traen coordenadas, y una igualdad exacta no ocurre por casualidad.
3. **Nombre contenido y cerca** — el registro guarda "Goya" y el portal "Hotel Goya Barcelona".
4. **Nombre contenido y único en la ciudad** — si "ABREVADERO" aparece en una sola ficha de las
   1.500, no hay ambigüedad. Única vía para los hoteles sin coordenada en el registro.
5. **Parecido literal alto** — último recurso, y el único que se marca dudoso por defecto.

Por qué el orden importa: la contención sola es peligrosa cuando el nombre del registro es un
topónimo. Buscando "Lima" o "Lourdes" en una fuente global aparecen hoteles de Perú y de Francia
con el nombre contenido y precio perfectamente válido, y el resultado es un precio de otro país
pegado a un hostal del Raval. Por eso la coordenada y la igualdad exacta van primero.

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
# Coordenadas obtenidas del ICGC para los hoteles que el registro no trae geolocalizados
# (`geocodificar_hoteles.py`). Es opcional: si no existe, el cruce sigue funcionando con menos
# alcance, porque sin coordenada solo quedan los métodos por nombre.
RUTA_GEOCODIFICADOS = RAIZ / "data" / "processed" / "hoteles_geocodificados.csv"
# Fichero propio a propósito: `enriquecer_hoteles_con_booking.py` produce
# `hoteles_con_precio.csv` a partir de este, y si ambos escribieran el mismo nombre el que
# corriera último borraría el trabajo del otro sin avisar.
RUTA_SALIDA = RAIZ / "data" / "processed" / "hoteles_cruce_base.csv"

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

# Caja que contiene la ciudad de Barcelona. Sirve de guardarraíl para el emparejamiento por
# contención de nombre, que sin verificación geográfica es peligroso: muchos hoteles del registro
# se llaman como una ciudad ("Lima", "Lourdes", "Albi", "Girona", "Santo Domingo"), y en una
# fuente global el nombre aparece contenido en un hotel de Perú o de Francia, con su precio
# perfectamente válido. El resultado sería una tarifa de otro país pegada a un hostal del Raval.
BBOX_BARCELONA = (41.32, 41.47, 2.05, 2.24)  # lat_min, lat_max, lon_min, lon_max


def en_barcelona(lat: object, lon: object) -> bool:
    """¿La ficha está geográficamente en Barcelona? Sin coordenadas no se puede afirmar."""
    if pd.isna(lat) or pd.isna(lon):
        return False
    lat_min, lat_max, lon_min, lon_max = BBOX_BARCELONA
    return lat_min <= float(lat) <= lat_max and lon_min <= float(lon) <= lon_max


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
        "nombre": ["name", "hotelName", "title", "displayName", "nombre_alojamiento"],
        "lat": ["latitude", "lat", "location.lat", "coordinates.lat", "gpsCoordinates.latitude"],
        "lon": ["longitude", "lng", "lon", "location.lng", "coordinates.lng",
                "gpsCoordinates.longitude"],
        "precio": ["nightly", "price", "pricePerNight", "rate", "price.value", "nightlyPrice",
                   "precio_noche_eur"],
        "moneda": ["currency", "currencyCode", "price.currency"],
        "estrellas": ["stars", "starRating", "hotelClass", "rating.stars"],
        "puntuacion": ["rating", "reviewScore", "score", "guestRating", "puntuacion"],
        "direccion": ["address", "formattedAddress", "location.address", "direccion_original"],
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
    # Solo las fichas con coordenada dentro de Barcelona pueden usarse para emparejar por
    # contención de nombre (ver BBOX_BARCELONA).
    salida["en_bcn"] = salida.apply(lambda r: en_barcelona(r["lat"], r["lon"]), axis=1)
    return salida[salida["nombre"].notna()]


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
            bruto = pd.json_normalize(datos if isinstance(datos, list) else [datos])
        else:
            bruto = pd.read_csv(f)

        # Cada fichero se normaliza **por separado y antes de unirlos**. Concatenar primero y
        # buscar las columnas después parece equivalente y no lo es: la búsqueda encuentra el
        # nombre que use el primer fichero (`name`) y lo aplica a todos, de modo que las filas
        # de una fuente que la llame distinto (`nombre_alojamiento`) quedan vacías en silencio.
        normalizado = preparar_raspados(bruto)
        # Guardar de dónde viene cada ficha: las fuentes no son igual de fiables y conviene
        # poder rastrear un precio raro hasta el fichero que lo trajo.
        normalizado["fichero_origen"] = f.name
        trozos.append(normalizado)
        print(f"  leído {f.name}: {len(bruto):,} filas → "
              f"{normalizado['precio'].notna().sum():,} con precio")
    return pd.concat(trozos, ignore_index=True)


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

        # 2. Nombre normalizado idéntico. Es el criterio que salva las fuentes sin coordenadas:
        # "Acta Splendid" o "Barceló Raval" coinciden letra por letra una vez quitados acentos y
        # palabras de relleno, y una igualdad exacta no se produce por casualidad.
        if mejor is None and clave_h:
            iguales = raspados[raspados["clave"] == clave_h]
            if len(iguales) >= 1:
                # Si hay varias fichas con el mismo nombre, se prefiere la que traiga precio.
                con_precio = iguales[iguales["precio"].notna()]
                i = (con_precio if len(con_precio) else iguales).index[0]
                mejor, metodo, sim = raspados.loc[i], "nombre_exacto", 1.0

        # 3. Nombre contenido + cerca. Salva los casos en que el registro guarda "Goya" y el
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

        # 4. Nombre único **entre las fichas situadas en Barcelona**. Es la vía para los hoteles
        # sin coordenada en nuestro registro (309 de 754): si "ABREVADERO" aparece en una sola
        # ficha, no hay ambigüedad. Restringirlo a fichas con coordenada verificada es lo que
        # evita que "Lima" empareje con un hotel de Perú (ver BBOX_BARCELONA).
        if mejor is None and clave_h:
            verificadas = raspados[raspados["en_bcn"]]
            contenidos = verificadas[verificadas["clave"].apply(lambda c: contenido_en(clave_h, c))]
            if len(contenidos) == 1:
                i = contenidos.index[0]
                mejor, metodo = raspados.loc[i], "nombre_unico"
                sim = parecido(clave_h, raspados.loc[i, "clave"])

        # 5. Parecido literal alto, como último recurso.
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
            "origen_coordenada": h.get("origen_coordenada"),
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
                "fichero_origen": mejor["fichero_origen"],
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
    # La mediana por categoría viaja siempre con su cobertura en plazas. Sin ese porcentaje al
    # lado, una mediana calculada sobre el 40% de una categoría se lee igual que una calculada
    # sobre el 85%, y no valen lo mismo: los hoteles que faltan son sistemáticamente los pequeños,
    # así que la mediana de una categoría poco cubierta tira hacia arriba.
    plazas = pd.to_numeric(d["plazas"], errors="coerce")
    cubiertas = plazas.where(d.index.isin(fiables.index), 0)
    cobertura = (cubiertas.groupby(d["categoria"]).sum()
                 / plazas.groupby(d["categoria"]).sum() * 100)

    por_cat = fiables.groupby("categoria")["precio"].agg(["size", "median"]).round(0)
    por_cat.columns = ["hoteles", "precio_mediano"]
    por_cat["% plazas cubiertas"] = cobertura.round(1)
    por_cat["fiabilidad"] = pd.cut(
        por_cat["% plazas cubiertas"], [0, 50, 70, 101],
        labels=["baja: sobreestima", "media", "alta"])
    print(f"\n{por_cat.sort_values('precio_mediano').to_string()}")

    cobertura = len(fiables) / len(d)
    if cobertura < 0.5:
        print(f"\nCobertura del {cobertura:.1%}: insuficiente para hablar del parque hotelero.")
        print("Sirve para explorar, no para una media de ciudad.")


def main() -> None:
    print(f"Leyendo {DIR_PRECIOS.relative_to(RAIZ)}")
    raspados = cargar_raspados()
    print(f"  {len(raspados):,} fichas con nombre | {raspados['precio'].notna().sum():,} con precio")

    hoteles = pd.read_csv(RUTA_HOTELES, dtype=str)
    hoteles = hoteles[(hoteles["tipo"] == "hotel") & (hoteles["municipio"] == "Barcelona")].copy()
    for c in ("lat", "lon"):
        hoteles[c] = pd.to_numeric(hoteles[c], errors="coerce")
    del_registro = int(hoteles["lat"].notna().sum())

    # Rellenar los huecos con lo geocodificado, sin pisar nunca la coordenada del registro: la
    # oficial es más fiable que una dirección resuelta por aproximación.
    if RUTA_GEOCODIFICADOS.exists():
        geo = pd.read_csv(RUTA_GEOCODIFICADOS)
        geo = geo.loc[geo["geocodificado"] == True, ["licencia_id", "lat", "lon"]]  # noqa: E712
        hoteles = hoteles.merge(geo, on="licencia_id", how="left", suffixes=("", "_geo"))
        hoteles["origen_coordenada"] = hoteles["lat"].notna().map(
            {True: "registro", False: "geocodificada"})
        hoteles["lat"] = hoteles["lat"].fillna(hoteles["lat_geo"])
        hoteles["lon"] = hoteles["lon"].fillna(hoteles["lon_geo"])
        hoteles.loc[hoteles["lat"].isna(), "origen_coordenada"] = None
    else:
        hoteles["origen_coordenada"] = hoteles["lat"].notna().map({True: "registro", False: None})

    print(f"  {len(hoteles):,} hoteles oficiales en la ciudad "
          f"({hoteles['lat'].notna().sum()} con coordenada: "
          f"{del_registro} del registro + {int(hoteles['lat'].notna().sum()) - del_registro} geocodificadas)")

    d = cruzar(hoteles, raspados)
    informe(d)

    RUTA_SALIDA.parent.mkdir(parents=True, exist_ok=True)
    d.to_csv(RUTA_SALIDA, index=False, encoding="utf-8")
    print(f"\nGuardado en {RUTA_SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
