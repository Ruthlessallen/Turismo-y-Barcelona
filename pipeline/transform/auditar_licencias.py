"""Clasifica la oferta anunciada en Airbnb según su situación de licencia.

Implementa el cruce de [M-08] en `docs/prd.md`: contrastar lo anunciado contra el registro
oficial de licencias VUT. El análisis exploratorio que justifica cada decisión de este script
está en `pipeline/notebooks/03_auditoria_licencias.ipynb`.

Entradas
    data/raw/airbnb/insideairbnb_barcelona_<fecha>_listings.csv
    data/processed/vut_unificados.csv   (generado por unificar_registros.py)

Salida
    data/processed/airbnb_situacion_licencia.csv

Tres cautelas que condicionan todo el diseño:

1. **El campo `license` contiene dos números distintos.** El nacional incrusta el HUTB y le
   añade dígitos de control: `ESFCTU...HUTB-002062349` frente al real `HUTB-002062`. Buscar
   `HUTB-\\d+` en todo el campo captura el equivocado y multiplica por dos las licencias dadas
   por inválidas (36,2% en vez de 14,8%). Solo se lee la sección regional de Barcelona.

2. **No toda la oferta necesita licencia VUT.** Una habitación en vivienda habitual o un
   alquiler de 32+ noches se rigen por otro régimen. Contar sus anuncios como irregulares sería
   sencillamente incorrecto, así que `sujeto_a_vut` acota el universo antes de contar nada.

3. **Declarar no es tener, y no declarar no es carecer.** El campo lo rellena el anfitrión. El
   resultado se etiqueta como *candidato*, nunca como infracción (ver WON'T en `docs/prd.md`).
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
DIR_AIRBNB = RAIZ / "data" / "raw" / "airbnb"
RUTA_VUT = RAIZ / "data" / "processed" / "vut_unificados.csv"
RUTA_SALIDA = RAIZ / "data" / "processed" / "airbnb_situacion_licencia.csv"

# Solo la sección regional lleva el número bueno (ver cautela 1 en el docstring).
PATRON_REGIONAL = re.compile(
    r"Barcelona\s*-\s*Regional registration number\s*(?:<br\s*/?>)*\s*([^<]*)", re.I
)
PATRON_LICENCIA = re.compile(r"^(HUTB|HB|ATB|AJ|HCC|ATCC)[-\s]*(\d+)", re.I)
PATRON_EXENCION = re.compile(r"^Exempt\s*-?\s*", re.I)

# Algunos anuncios dejan vacía la sección regional pero incrustan un HUTB en el número nacional
# (`ESFCTU...HUTB-0002190`). Sirve para saber que **declaran algo**, pero NO para verificar cuál:
# comprobado sobre los 6.468 anuncios que traen ambos números, el nacional coincide con el
# regional solo el 95,2% de las veces, y los desajustes no son truncamientos sino números
# distintos (regional HUTB-007986 frente a nacional HUTB-0041843). Dar por buena esa extracción
# produciría coincidencias falsas, porque el espacio de numeración está lo bastante poblado como
# para que un número equivocado exista igualmente en el registro.
PATRON_HUTB_EN_NACIONAL = re.compile(r"HUTB-?\d+", re.I)

# Umbral legal del régimen VUT. La normativa catalana define estancia turística como
# "període de temps continu igual o inferior a 31 dies": hasta 31 noches es uso turístico
# (exige HUT), a partir de 32 es alquiler de temporada y queda fuera del régimen.
MAX_NOCHES_VUT = 31

# Un anuncio sin reseñas desde 2025 o antes no describe oferta en circulación: sin clientes, la
# licencia que le falte no dice nada sobre el mercado. Se exige actividad dentro del año del
# snapshot (2026-06-24), de modo que 2025 y anteriores quedan fuera aunque sigan publicados.
INICIO_ACTIVIDAD = pd.Timestamp("2026-01-01")

# La sección regional no solo declara HUTB: también aparecen licencias de otros regímenes
# (hoteles, albergues, apartamentos turísticos). Un anuncio con una de estas SÍ está
# acreditado — simplemente no bajo el régimen VUT — y no puede contarse como candidato.
PREFIJOS_NO_VUT = {"HB": "hotel", "HCC": "hotel", "ATB": "apartament_turistic",
                   "ATCC": "apartament_turistic", "AJ": "alberg"}


def leer_licencia(texto: object) -> tuple[str | None, int | None, str | None]:
    """Lee la sección regional del campo `license` de Inside Airbnb.

    Devuelve `(prefijo, numero, motivo_exencion)`. El prefijo distingue el régimen:
    `HUTB` es vivienda de uso turístico; `HB`/`ATB`/`AJ` son otros tipos de establecimiento.
    Todo a `None` cuando el anuncio no declara nada.
    """
    if not isinstance(texto, str):
        return None, None, None

    encontrado = PATRON_REGIONAL.search(texto)
    if encontrado:
        valor = encontrado.group(1).strip()
        if PATRON_EXENCION.match(valor):
            return None, None, PATRON_EXENCION.sub("", valor).strip().lower() or "sin especificar"
        licencia = PATRON_LICENCIA.match(valor)
        if licencia:
            return licencia.group(1).upper(), int(licencia.group(2)), None

    # Sin sección regional utilizable: si el número nacional incrusta un HUTB, el anuncio está
    # declarando una licencia aunque no podamos leer cuál (ver PATRON_HUTB_EN_NACIONAL). Se marca
    # con prefijo propio para no confundirlo ni con una licencia verificada ni con "no declara".
    if PATRON_HUTB_EN_NACIONAL.search(texto):
        return "HUTB_SOLO_NACIONAL", None, None

    return None, None, None


def cargar_licencias_oficiales() -> tuple[set[str], int]:
    """Devuelve el conjunto de licencias VUT vigentes y el número más alto emitido.

    El máximo sirve para separar un posible error de tecleo de un número que la Generalitat
    todavía no ha llegado a emitir: por encima de él, la licencia no puede existir.
    """
    vut = pd.read_csv(RUTA_VUT, dtype=str)
    validas = vut.loc[vut["licencia_id"].str.match(r"^HUTB-\d+$", na=False), "licencia_id"]
    if validas.empty:
        raise ValueError(f"No se encontraron licencias HUTB en {RUTA_VUT}")
    numeros = validas.str.split("-").str[1].astype(int)
    return set(validas), int(numeros.max())


def localizar_airbnb() -> Path:
    """Toma el snapshot de Inside Airbnb más reciente disponible en `data/raw/airbnb/`."""
    candidatos = sorted(DIR_AIRBNB.glob("insideairbnb_barcelona_*_listings.csv"))
    if not candidatos:
        raise FileNotFoundError(
            f"No hay snapshot de Inside Airbnb en {DIR_AIRBNB}. "
            "Ejecuta primero: python pipeline/sources/descargar_fuentes.py airbnb"
        )
    return candidatos[-1]


def clasificar(anuncios: pd.DataFrame, oficiales: set[str], num_maximo: int) -> pd.DataFrame:
    """Añade las columnas de situación de licencia al conjunto de anuncios."""
    leido = anuncios["license"].apply(leer_licencia)
    anuncios["prefijo_licencia"] = [r[0] for r in leido]
    anuncios["numero_licencia"] = [r[1] for r in leido]
    anuncios["exencion"] = [r[2] for r in leido]

    es_vut = anuncios["prefijo_licencia"] == "HUTB"
    anuncios["hutb"] = None
    anuncios.loc[es_vut, "hutb"] = anuncios.loc[es_vut, "numero_licencia"].apply(
        lambda n: f"HUTB-{int(n):06d}"
    )
    anuncios["licencia_existe"] = anuncios["hutb"].isin(oficiales)
    anuncios["regimen_declarado"] = anuncios["prefijo_licencia"].map(PREFIJOS_NO_VUT)

    # Un número por encima del último emitido no puede corresponder a ninguna licencia real,
    # así que no se explica como error de transcripción.
    anuncios["fuera_de_rango"] = (
        es_vut & ~anuncios["licencia_existe"] & (anuncios["numero_licencia"] > num_maximo)
    )

    def situacion(fila: pd.Series) -> str:
        if pd.notna(fila["hutb"]):
            return "licencia_verificada" if fila["licencia_existe"] else "licencia_no_encontrada"
        if fila["prefijo_licencia"] == "HUTB_SOLO_NACIONAL":
            return "hutb_no_verificable"  # declara HUTB solo en el número nacional
        if pd.notna(fila["regimen_declarado"]):
            return "licencia_otro_regimen"  # hotel, albergue o apartamento turístico
        if pd.notna(fila["exencion"]):
            return "exencion_declarada"
        return "sin_declarar"

    anuncios["situacion"] = anuncios.apply(situacion, axis=1)

    # Acota el universo: solo la vivienda completa de estancia corta necesita licencia VUT.
    anuncios["sujeto_a_vut"] = (anuncios["room_type"] == "Entire home/apt") & (
        anuncios["minimum_nights"] <= MAX_NOCHES_VUT
    )

    # Solo cuenta la oferta con clientes: sin reservas recientes, la falta de licencia no describe
    # actividad real. Se exige reseña dentro del año del snapshot, así que 2025 y anterior quedan
    # fuera aunque el anuncio siga publicado.
    ultima = pd.to_datetime(anuncios.get("last_review"), errors="coerce")
    anuncios["actividad_reciente"] = ultima >= INICIO_ACTIVIDAD

    # Un anfitrión puede acreditar licencia en unos anuncios y no en otros. Saberlo cambia la
    # lectura del caso: quien ya ha declarado una licencia válida en otro anuncio no es alguien
    # que ignore el trámite.
    con_licencia = anuncios.loc[anuncios["situacion"] == "licencia_verificada", "host_id"]
    anuncios["host_acredita_en_otro"] = anuncios["host_id"].isin(set(con_licencia)) & (
        anuncios["situacion"] != "licencia_verificada"
    )

    sin_acreditar = (
        anuncios["sujeto_a_vut"]
        & anuncios["actividad_reciente"]
        & anuncios["situacion"].isin(["sin_declarar", "licencia_no_encontrada"])
    )

    # La conclusión operativa. "Candidato", nunca "infractor": el campo lo rellena el anfitrión
    # y una licencia real mal escrita cae exactamente aquí. Quien acredita licencia en otro anuncio
    # suyo se aparta a su propia categoría: conoce el trámite, así que la falta apunta más a un
    # descuido al rellenar el campo que a operar al margen del registro.
    anuncios["candidato_sin_licencia"] = sin_acreditar & ~anuncios["host_acredita_en_otro"]
    anuncios["candidato_host_con_licencia"] = sin_acreditar & anuncios["host_acredita_en_otro"]
    return anuncios


def informe(anuncios: pd.DataFrame, num_maximo: int) -> None:
    """Resumen por pantalla, con las cifras que van al changelog."""
    sujetos = anuncios[anuncios["sujeto_a_vut"]]
    candidatos = anuncios[anuncios["candidato_sin_licencia"]]

    print(f"\nAnuncios analizados        : {len(anuncios):,}")
    print(f"Sujetos al régimen VUT     : {len(sujetos):,}")
    print("\nSituación de los sujetos a VUT:")
    for etiqueta, n in sujetos["situacion"].value_counts().items():
        print(f"  {etiqueta:24s}: {n:6,}  ({n / len(sujetos):5.1%})")

    print(f"\nCandidatos sin licencia    : {len(candidatos):,} ({len(candidatos) / len(sujetos):.1%} de los sujetos)")
    print(f"  con número imposible     : {int(candidatos['fuera_de_rango'].sum()):,}  (por encima de HUTB-{num_maximo})")
    print(
        f"\nNúmeros imposibles en todo el conjunto: {int(anuncios['fuera_de_rango'].sum()):,} "
        "(incluye anuncios no sujetos al régimen VUT)"
    )

    sin_actividad = sujetos[~sujetos["actividad_reciente"] & sujetos["situacion"].isin(
        ["sin_declarar", "licencia_no_encontrada"])]
    print(f"\nExcluidos por última reseña anterior a {INICIO_ACTIVIDAD:%Y} (o sin reseñas): "
          f"{len(sin_actividad):,}")

    en_frontera = candidatos["minimum_nights"] == MAX_NOCHES_VUT
    print(f"\nCandidatos con estancia mínima de exactamente {MAX_NOCHES_VUT} noches: {int(en_frontera.sum()):,}")
    print("  justo en el límite del régimen VUT: una noche más quedarían exentos")
    print(f"Candidatos fuera de la frontera: {len(candidatos) - int(en_frontera.sum()):,}")

    aparte = anuncios[anuncios["candidato_host_con_licencia"]]
    print(f"\nCaso aparte — anfitrión acredita licencia en otro anuncio suyo: {len(aparte):,}")
    print(f"  anfitriones distintos: {aparte['host_id'].nunique():,}")

    por_host = candidatos.groupby("host_id").size()
    if not por_host.empty:
        grandes = por_host[por_host >= 5]
        print(f"\nAnfitriones con candidatos : {len(por_host):,}")
        print(f"  con 5 o más anuncios     : {len(grandes):,}  → {grandes.sum():,} anuncios")


def main() -> None:
    ruta_airbnb = localizar_airbnb()
    print(f"Snapshot   : {ruta_airbnb.name}")
    anuncios = pd.read_csv(ruta_airbnb)

    oficiales, num_maximo = cargar_licencias_oficiales()
    print(f"Licencias oficiales VUT: {len(oficiales):,} (máximo emitido: HUTB-{num_maximo})")

    anuncios = clasificar(anuncios, oficiales, num_maximo)
    informe(anuncios, num_maximo)

    columnas = [
        "id", "name", "host_id", "host_name", "calculated_host_listings_count",
        "neighbourhood_group", "neighbourhood", "latitude", "longitude",
        "room_type", "minimum_nights", "price", "availability_365", "number_of_reviews",
        "last_review", "number_of_reviews_ltm",
        "license", "prefijo_licencia", "hutb", "regimen_declarado", "exencion",
        "licencia_existe", "fuera_de_rango",
        "situacion", "sujeto_a_vut", "actividad_reciente", "host_acredita_en_otro",
        "candidato_sin_licencia", "candidato_host_con_licencia",
    ]
    salida = anuncios[[c for c in columnas if c in anuncios]]

    # Las coordenadas vienen ya ofuscadas ~200 m por Inside Airbnb, y aquí se conservan tal
    # cual: el detalle se queda en `data/processed/`. La agregación por barrio o distrito para
    # lo que se publica es responsabilidad de `pipeline/export.py` (ver docs/data-model.md).
    RUTA_SALIDA.parent.mkdir(parents=True, exist_ok=True)
    salida.to_csv(RUTA_SALIDA, index=False, encoding="utf-8")
    print(f"\nGuardado en {RUTA_SALIDA.relative_to(RAIZ)}  ({len(salida):,} filas)")


if __name__ == "__main__":
    main()
