"""Segundo pase del cruce de precios: recupera los hoteles que el primero dejó sin emparejar.

    python pipeline/transform/rescatar_precios_hoteles.py

Entradas
    data/processed/hoteles_bcn.csv                          — censo de la ciudad con lo ya cruzado
    data/processed/hoteles_cruce_base.csv                   — qué fichas usó el primer pase
    data/raw/precios_hoteles/google_hotels_2026-09-29_eur.csv

Salidas
    data/processed/hoteles_bcn_precios_rescatados.csv  — pares aceptados automaticamente
    data/processed/hoteles_bcn_precios_a_revisar.csv   — pares dudosos, para mirar a mano

**Por qué hace falta un segundo pase.** `cruzar_precios_hoteles.py` se ejecutó cuando solo 446 de
los 768 establecimientos tenían coordenada. La geocodificación del ICGC llegó después y subió esa
cifra a 763, pero el cruce nunca se relanzó: 101 hoteles que hoy tienen coordenada no fueron
candidatos al emparejamiento por distancia porque, cuando aquello corrió, no tenían ninguna. El
resultado es que quedan 601 fichas de Google con precio sin asignar y 338 hoteles sin precio.

**Por qué no vale el vecino más cercano.** En el Eixample hay decenas de hoteles en 150 metros. Al
probarlo, `Hostal Oliva` y `Eurostars Cristal Palace` reclamaban los dos la misma ficha —un
Safestay que no es ninguno de ellos— porque cada uno la tenía como vecina más próxima. Un precio
pegado al hotel equivocado es peor que no tener precio: no hay nada después que lo delate.

**Cómo se resuelve.** Como una asignación global: se construye la matriz de coste entre hoteles y
fichas, se prohíben los pares que no superan los filtros, y `linear_sum_assignment` reparte de
forma que **cada ficha se use como mucho una vez** y el coste total sea mínimo. Eso convierte el
problema de "a quién se parece más esta ficha" en "qué reparto completo es el más coherente", que
es lo que impide que dos hoteles se queden con la misma.

**Tres filtros que un par debe pasar.** Distancia y parecido de nombre combinados —cuanto más lejos,
más nombre hace falta—, y concordancia de categoría: si el registro dice tres estrellas y Google
dice cinco, no es el mismo establecimiento por muy cerca que estén.
"""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from scipy.spatial import cKDTree

RAIZ = Path(__file__).resolve().parents[2]
PROC = RAIZ / "data" / "processed"
RUTA_GOOGLE = RAIZ / "data" / "raw" / "precios_hoteles" / "google_hotels_2026-09-29_eur.csv"
SALIDA = PROC / "hoteles_bcn_precios_rescatados.csv"
SALIDA_REVISION = PROC / "hoteles_bcn_precios_a_revisar.csv"

# Metros por grado, a la latitud de Barcelona. Basta para distancias de pocos cientos de metros.
METROS_GRADO = 111320.0
LATITUD = 41.4

# Radio máximo que se considera. Más allá, ni el nombre exacto convence: dos hoteles de la misma
# cadena a 400 m tienen nombres casi idénticos y son establecimientos distintos.
RADIO_MAXIMO = 250.0

# Combinaciones admitidas de (distancia máxima, parecido mínimo del nombre). Cuanto más lejos está
# la ficha, más tiene que decir el nombre para compensar.
#
# Los umbrales son severos por un caso concreto: el mismo grupo hotelero con dos establecimientos
# en la misma manzana. `Chic Basic Tallers` y `chic&basic Lemon Boutique` se parecen un 0,61 y
# están a 83 m, y son hoteles distintos. Con una versión anterior más laxa —0,30 de parecido
# bastaba a 60 m— entraban también `Continental` con `Hotel Monegal` a 78 m y `Goya Principal` con
# `Hostal Amra` a 49 m, que no tienen nada que ver. Sale menos rescate y del bueno: la coordenada
# de la mayoría es del portal de la calle, no del establecimiento, así que 60 m no significa
# "mismo edificio" como significaría con coordenada propia.
UMBRALES = [(40.0, 0.60), (100.0, 0.80), (250.0, 0.90)]

# Diferencia de estrellas que se tolera. Uno, porque el Registre distingue "4 superior" y Google no,
# y porque alguna ficha arrastra la categoría desactualizada.
ESTRELLAS_TOLERANCIA = 1.0

# Columnas del fichero de rescate. Fijas y explícitas porque el fichero **acumula**: una ejecución
# que no encuentre nada nuevo no puede quedarse sin columnas y borrar lo que ya había.
NL = chr(10)

COLUMNAS_RESCATE = ["licencia_id", "nombre_registro", "nombre_google", "precio_rescatado",
                    "metros", "similitud", "estrellas_censo", "estrellas_google", "confianza"]

# Palabras que comparten tantos establecimientos que no distinguen a ninguno. `guest` y `house`
# entraron tarde: sin ellas, `Casa Maca Guest House` y `CasaNova Guest House` puntuaban 0,83 y se
# emparejaban a 9,8 m, siendo negocios distintos —el registro tiene tres licencias Casa Maca en
# Bruc 146 y ningún CasaNova, y el H10 Casanova está a kilómetro y medio con su precio ya asignado.
RUIDO = re.compile(r"\b(hotel|hostal|hostel|pensio|pension|apartaments?|apartments?|aparthotel|"
                   r"guest|house|rooms?|suites?|residencia|barcelona|bcn|the|by|and|de|del|la|el|"
                   r"les|los|las)\b")


def normalizar(texto: object) -> str:
    """Minúsculas, sin diacríticos y sin las palabras que casi todos comparten.

    `Hotel Barcelona Center` y `Hotel Barcelona Princess` comparten dos de tres palabras y saldrían
    parecidísimos sin quitar el ruido. Lo que distingue a un hotel de otro es lo que queda después.
    """
    if pd.isna(texto):
        return ""
    plano = unicodedata.normalize("NFKD", str(texto))
    plano = "".join(c for c in plano if not unicodedata.combining(c)).lower()
    plano = re.sub(r"[^a-z0-9\s]", " ", plano)
    return re.sub(r"\s+", " ", RUIDO.sub(" ", plano)).strip()


def parecido(a: str, b: str) -> float:
    """Parecido entre dos nombres ya normalizados, por la mejor de dos medidas.

    `SequenceMatcher` compara carácter a carácter y castiga el orden distinto; la proporción de
    palabras compartidas no. `Praktik Rambla` y `Rambla Praktik` son el mismo hotel y solo la
    segunda medida lo ve.

    La proporción se calcula sobre el nombre **más largo**, no sobre el más corto. Dividiendo entre
    el más corto, cualquier nombre de una sola palabra contenido en el otro puntúa 1,00: así
    `Central Apartment` salía idéntico a `Hostal Razio Central Station B`, que está a 206 m y es
    otro establecimiento. Sobre el más largo esa pareja cae a 0,25 y no pasa ningún filtro.
    """
    if not a or not b:
        return 0.0
    literal = SequenceMatcher(None, a, b).ratio()
    pa, pb = set(a.split()), set(b.split())
    palabras = len(pa & pb) / max(len(pa), len(pb)) if pa and pb else 0.0
    return max(literal, palabras)


def admisible(metros: float, similitud: float, est_censo: float, est_google: float) -> bool:
    """Si el par puede ser el mismo establecimiento."""
    if metros > RADIO_MAXIMO:
        return False
    if pd.notna(est_censo) and pd.notna(est_google):
        if abs(float(est_censo) - float(est_google)) > ESTRELLAS_TOLERANCIA:
            return False
    return any(metros <= d and similitud >= s for d, s in UMBRALES)


def fichas_libres(censo: pd.DataFrame) -> pd.DataFrame:
    """Fichas de Google con precio que el primer pase no llegó a usar."""
    google = pd.read_csv(RUTA_GOOGLE)
    base = pd.read_csv(PROC / "hoteles_cruce_base.csv", low_memory=False)
    usadas = set(base.loc[base["nombre_raspado"].notna(), "nombre_raspado"]
                 .astype(str).str.lower())
    libres = google[google["nightly"].notna()
                    & ~google["name"].astype(str).str.lower().isin(usadas)]
    return libres.reset_index(drop=True)


def emparejar(faltan: pd.DataFrame, libres: pd.DataFrame) -> pd.DataFrame:
    """Asignación global entre hoteles sin precio y fichas sin dueño."""
    escala = METROS_GRADO * np.cos(np.radians(LATITUD))
    arbol = cKDTree(np.c_[libres["lat"] * METROS_GRADO, libres["lng"] * escala])
    puntos = np.c_[faltan["lat"] * METROS_GRADO, faltan["lon"] * escala]

    nombres_censo = faltan["nombre_comercial"].map(normalizar).tolist()
    nombres_google = libres["name"].map(normalizar).tolist()

    # Coste alto = par prohibido. Solo se rellenan los pares que superan los filtros.
    PROHIBIDO = 1e6
    coste = np.full((len(faltan), len(libres)), PROHIBIDO)
    candidatos = arbol.query_ball_point(puntos, r=RADIO_MAXIMO)

    for i, vecinas in enumerate(candidatos):
        for j in vecinas:
            metros = float(np.hypot(*(puntos[i] - np.array(
                [libres.at[j, "lat"] * METROS_GRADO, libres.at[j, "lng"] * escala]))))
            sim = parecido(nombres_censo[i], nombres_google[j])
            if admisible(metros, sim, faltan.iloc[i]["estrellas"], libres.at[j, "stars"]):
                # El nombre pesa más que la distancia: a igualdad de metros manda el parecido, y
                # 200 m con el nombre exacto es mejor apuesta que 20 m con un nombre distinto.
                coste[i, j] = metros / RADIO_MAXIMO + 2.0 * (1.0 - sim)

    filas, columnas = linear_sum_assignment(coste)
    resultado = []
    for i, j in zip(filas, columnas):
        if coste[i, j] >= PROHIBIDO:
            continue
        metros = float(np.hypot(*(puntos[i] - np.array(
            [libres.at[j, "lat"] * METROS_GRADO, libres.at[j, "lng"] * escala]))))
        sim = parecido(nombres_censo[i], nombres_google[j])
        resultado.append({
            "licencia_id": faltan.iloc[i]["licencia_id"],
            "nombre_registro": faltan.iloc[i]["nombre_comercial"],
            "nombre_google": libres.at[j, "name"],
            "precio_rescatado": float(libres.at[j, "nightly"]),
            "metros": round(metros, 1),
            "similitud": round(sim, 3),
            "estrellas_censo": faltan.iloc[i]["estrellas"],
            "estrellas_google": libres.at[j, "stars"],
            "confianza": ("alta" if metros <= 60 and sim >= 0.55 else
                          "media" if sim >= 0.55 or metros <= 60 else "baja"),
        })
    return pd.DataFrame(resultado, columns=COLUMNAS_RESCATE)


def veredictos_previos() -> pd.DataFrame:
    """Lo que una persona ya dictaminó en pasadas anteriores.

    Se lee antes de regenerar el fichero de revisión, porque `revisar()` lo reescribe: sin esto,
    cada ejecución borraría el trabajo manual y habría que repetirlo.
    """
    if not SALIDA_REVISION.exists():
        return pd.DataFrame(columns=["licencia_id", "nombre_google", "veredicto"])
    r = pd.read_csv(SALIDA_REVISION, dtype={"licencia_id": str})
    if "veredicto" not in r.columns:
        return pd.DataFrame(columns=["licencia_id", "nombre_google", "veredicto"])
    return r[r["veredicto"].notna()]


def aprobados(previos: pd.DataFrame) -> pd.DataFrame:
    """Los pares que una persona confirmó como el mismo establecimiento."""
    if previos.empty:
        return pd.DataFrame(columns=COLUMNAS_RESCATE)
    marca = previos["veredicto"].astype(str).str.strip().str.lower()
    ok = previos[marca.isin(["si", "sí", "s", "x", "1", "true"])].copy()
    ok["confianza"] = "manual"
    return ok


def main() -> None:
    censo = pd.read_csv(PROC / "hoteles_bcn.csv", low_memory=False)
    libres = fichas_libres(censo)

    # Se reconsidera lo que el **primer** cruce no resolvió, no lo que ahora mismo carece de precio.
    # Es la diferencia entre un paso reejecutable y uno que se desmonta solo: una vez incorporado un
    # rescate al censo, ese hotel deja de figurar como faltante, la siguiente pasada no lo propone y
    # la salida pierde lo que la anterior había encontrado.
    pendiente = censo["origen_precio"].ne("cruce_inicial") | censo["origen_precio"].isna()
    faltan = censo[pendiente & censo["lat"].notna()].reset_index(drop=True)
    print(f"Sin resolver por el primer cruce   : {len(faltan)}")
    print(f"Fichas de Google con precio libres : {len(libres)}")

    previos = veredictos_previos()
    automaticos = emparejar(faltan, libres)
    manuales = aprobados(previos).reindex(columns=COLUMNAS_RESCATE)
    rescatados = (pd.concat([automaticos, manuales], ignore_index=True)
                  .drop_duplicates("licencia_id", keep="first"))
    print(f"  emparejados automáticamente : {len(automaticos)}")
    print(f"  aprobados a mano            : {len(manuales)}")

    if rescatados.empty:
        print(NL + "Ningún par supera los filtros.")
    else:
        print(NL + f"Rescatados en total: {len(rescatados)}")
        print(rescatados["confianza"].value_counts().to_string())
        for _, f in rescatados.sort_values("metros").iterrows():
            print(f"  [{f['confianza'][:6]:6s}] {str(f['nombre_registro'])[:28]:30s} -> "
                  f"{str(f['nombre_google'])[:30]:32s} {f['metros']:5.0f} m  "
                  f"{f['precio_rescatado']:6.0f} EUR")
        rescatados.to_csv(SALIDA, index=False, encoding="utf-8")
        base = int((censo["origen_precio"] == "cruce_inicial").sum())
        print(NL + f"Cobertura de precio: {base} -> {base + len(rescatados)} de {len(censo)} "
              f"({(base + len(rescatados)) / len(censo):.1%})")
        print(f"Guardado en {SALIDA.relative_to(RAIZ)}")

    revisar(faltan, libres, previos, set(rescatados["licencia_id"]))


def revisar(faltan: pd.DataFrame, libres: pd.DataFrame, previos: pd.DataFrame,
            aceptados: set) -> None:
    """Deja para una persona los pares que se quedan a las puertas de los umbrales estrictos.

    Con los umbrales laxos entraban 66 pares y con los estrictos 14. Entre unos y otros hay casos
    buenos —`Hosteria Grau` con `Eco Boutique Hostal Grau` es el mismo a cinco metros tras cambiar
    de marca— mezclados con otros que no lo son. Automatizar esa distinción exigiría más señal de
    la que hay; mirarlos a ojo son diez minutos.

    **El fichero conserva todas las filas, también las ya aprobadas.** Es el registro del juicio
    humano y no puede perder ninguna: una versión anterior excluía las aceptadas por considerarlas
    resueltas, y al regenerarse se llevó por delante los veredictos que las sostenían, dejando
    huérfanos los precios que habían entrado gracias a ellos.
    """
    global UMBRALES
    estrictos, UMBRALES = UMBRALES, [(60.0, 0.30), (120.0, 0.55), (250.0, 0.80)]
    try:
        laxos = emparejar(faltan, libres)
    finally:
        UMBRALES = estrictos
    if laxos.empty and previos.empty:
        return

    juicios = previos[["licencia_id", "nombre_google", "veredicto"]]
    dudosos = laxos.merge(juicios, on=["licencia_id", "nombre_google"], how="left")

    # Un par juzgado que el emparejador ya no propone —porque su hotel dejó de faltar— se conserva
    # igualmente: si desapareciera, la próxima pasada no sabría de dónde salió su precio.
    huerfanos = previos[~previos.set_index(["licencia_id", "nombre_google"]).index.isin(
        dudosos.set_index(["licencia_id", "nombre_google"]).index)]
    dudosos = pd.concat([dudosos, huerfanos], ignore_index=True)

    # Los que el emparejador ya aceptó por su cuenta se marcan solos: pedir un juicio humano sobre
    # algo que no está en duda gasta la atención que hace falta para los que sí lo están.
    auto = dudosos["veredicto"].isna() & dudosos["licencia_id"].isin(aceptados)
    dudosos.loc[auto, "veredicto"] = "auto"
    dudosos.to_csv(SALIDA_REVISION, index=False, encoding="utf-8")
    pendientes = int(dudosos["veredicto"].isna().sum())
    print(NL + f"{len(dudosos)} pares en {SALIDA_REVISION.relative_to(RAIZ)}, "
          f"{pendientes} sin veredicto")
    if pendientes:
        print("   (pon 'si' en `veredicto` a los que sean el mismo establecimiento)")


if __name__ == "__main__":
    main()
