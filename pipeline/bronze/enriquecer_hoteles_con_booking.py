"""Rellena con precios de Booking los hoteles que el cruce principal dejó sin precio.

Último eslabón de la cadena de precios hoteleros:

    cruzar_precios_hoteles.py  →  hoteles_cruce_base.csv
                                        ↓  (este script)
                                  hoteles_con_precio.csv

Entradas
    data/bronze/precios_hoteles_cruzados.csv                 — el cruce ya hecho
    data/raw/hoteles/hoteles_booking_unificados_2026.csv     — precios de Booking
Salidas
    data/bronze/precios_hoteles_cruzados.csv   (el mismo fichero, completado)

**Se ejecuta despues de `cruzar_precios_hoteles.py` y sobre su misma salida.** Antes escribia un
segundo fichero, y los dos resultaban tener las mismas 754 filas y las mismas 17 columnas: solo
cambiaban nueve celdas, los precios que Booking rellena. Mantener dos copias de una tabla que
difiere en nueve celdas invita a que alguien lea la equivocada.

Solo toca los hoteles **sin precio**: los que el cruce principal ya resolvió por coordenada no se
tocan, porque ese método es más fiable que emparejar por nombre.

La validación es estricta a propósito. Emparejar hoteles por nombre falla de dos maneras conocidas
y silenciosas: las palabras genéricas ("Hotel Central Barcelona" contra "Hostal Central") hacen
parecidos altos entre establecimientos distintos, de ahí `PALABRAS_GENERICAS`; y un nombre del
registro que sea un topónimo empareja con hoteles de otra ciudad. Un precio pegado al hotel
equivocado es peor que no tener precio, porque nada lo delata después.
"""

from __future__ import annotations

import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
# Entrada: la salida de `cruzar_precios_hoteles.py`, no una copia congelada en `data/raw/`.
# Leer de una copia rompía la cadena en silencio: el cruce mejoraba —489 emparejamientos por
# coordenada en vez de 319 tras geocodificar— y este script seguía partiendo de la versión vieja,
# así que el fichero final quedaba peor que su propia base sin que nada lo indicara.
CENSO_CSV = RAIZ / "data" / "bronze" / "precios_hoteles_cruzados.csv"
# Los datos raspados son entrada, no resultado: viven en `data/raw/`, que no se versiona por
# NOTA HISTORICA: este script escribia ademas una copia en `data/raw/hoteles/`. Se retiro al
# adoptar la arquitectura medallon: `raw` guarda descargas, no derivados. Esa copia ya habia
# causado un fallo silencioso —otro script la leia congelada y no veia las mejoras de geocodificado.
# Antes decia: contener nombres y direcciones. Tenerlos tambien en `data/processed/` era una copia del
# mismo fichero, con el riesgo de que las tres se desincronizaran.
BOOKING_CSV = RAIZ / "data" / "raw" / "hoteles" / "hoteles_booking_unificados_2026.csv"

SALIDA = CENSO_CSV   # completa el mismo fichero: es la misma tabla en otra fase

# Palabras genéricas que no deben usarse solas para validar una coincidencia
PALABRAS_GENERICAS = {
    "hotel", "hostal", "albergue", "barcelona", "bcn", "pension", "pensiun",
    "residencia", "guesthouse", "s.l.", "sl", "de", "del", "la", "el", "los",
    "las", "y", "e", "en", "da", "di", "by", "boutique", "inn", "b&b", "bb",
    "casa", "palace", "center", "central", "plaza", "grand", "royal", "beach",
    "park", "suites", "hostel", "apartments", "rooms"
}


def normalizar_cadena(texto: str) -> str:
    """Normaliza un texto eliminando tildes, mayúsculas y caracteres especiales.

    Args:
        texto: Cadena de texto a normalizar.

    Returns:
        Cadena de texto normalizada.
    """
    if not texto or pd.isna(texto):
        return ""
    txt = str(texto).lower()
    txt = "".join(c for c in unicodedata.normalize("NFD", txt) if unicodedata.category(c) != "Mn")
    for s in [",", ".", "-", "_", "/", "(", ")", "&", "+", "*"]:
        txt = txt.replace(s, " ")
    return " ".join(txt.split())


def es_match_valido(nombre_censo: str, nombre_booking: str) -> tuple[bool, float]:
    """Evalúa de forma estricta si dos nombres pertenecen exactamente al mismo hotel.

    Args:
        nombre_censo: Nombre registrado en el censo oficial.
        nombre_booking: Nombre extraído de Booking.com.

    Returns:
        Tupla con (es_valido, porcentaje_similitud).
    """
    na = normalizar_cadena(nombre_censo)
    nb = normalizar_cadena(nombre_booking)

    if not na or not nb:
        return False, 0.0

    # 1. Coincidencia exacta de la cadena completa normalizada
    if na == nb:
        return True, 1.0

    # 2. Ratio de similitud sobre la cadena completa (mínimo 85%)
    ratio_full = SequenceMatcher(None, na, nb).ratio()
    if ratio_full >= 0.85:
        return True, round(ratio_full, 2)

    # 3. Comparación de palabras clave distintivas (excluyendo stopwords turísticas y genéricas)
    palabras_a = [w for w in na.split() if w not in PALABRAS_GENERICAS and len(w) > 2]
    palabras_b = [w for w in nb.split() if w not in PALABRAS_GENERICAS and len(w) > 2]

    if palabras_a and palabras_b:
        str_a = " ".join(palabras_a)
        str_b = " ".join(palabras_b)
        ratio_distintivo = SequenceMatcher(None, str_a, str_b).ratio()
        if ratio_distintivo >= 0.85 and ratio_full >= 0.60:
            return True, round(ratio_distintivo, 2)

    return False, 0.0


def cruzar_y_enriquecer_censo() -> pd.DataFrame:
    """Combina el censo oficial de hoteles con los precios validados de Booking.com.

    Returns:
        DataFrame del censo enriquecido con los precios verificados.
    """
    if not CENSO_CSV.exists():
        raise FileNotFoundError(f"No se encontró el censo oficial: {CENSO_CSV}")
    if not BOOKING_CSV.exists():
        raise FileNotFoundError(f"No se encontró el dataset de Booking: {BOOKING_CSV}")

    df_censo = pd.read_csv(CENSO_CSV)
    df_booking = pd.read_csv(BOOKING_CSV)

    # Limpiar cualquier asignación incorrecta previa
    for idx, row in df_censo.iterrows():
        metodo = str(row.get("metodo_cruce", "")).lower()
        if metodo in ["booking_playwright", "sin_cruce"] and pd.isna(row.get("precio")):
            df_censo.at[idx, "precio"] = None
            df_censo.at[idx, "nombre_raspado"] = None
            df_censo.at[idx, "puntuacion"] = None
            df_censo.at[idx, "similitud"] = None
            df_censo.at[idx, "metodo_cruce"] = "sin_cruce"

    precios_iniciales = df_censo["precio"].notna().sum()
    registros_rellenados = 0

    for idx, row in df_censo.iterrows():
        metodo = str(row.get("metodo_cruce", "")).lower()
        if pd.isna(row.get("precio")) or metodo == "sin_cruce":
            nombre_censo = str(row.get("nombre_registro", ""))

            mejor_match = None
            mejor_score = 0.0

            for _, b_row in df_booking.iterrows():
                nombre_b = str(b_row.get("nombre_alojamiento", ""))
                valido, score = es_match_valido(nombre_censo, nombre_b)

                if valido and score > mejor_score:
                    mejor_score = score
                    mejor_match = b_row

            if mejor_match is not None:
                registros_rellenados += 1
                precio_noche = mejor_match.get("precio_noche_eur")
                if pd.isna(precio_noche):
                    precio_noche = mejor_match.get("precio_total_eur")

                df_censo.at[idx, "nombre_raspado"] = mejor_match.get("nombre_alojamiento")
                df_censo.at[idx, "precio"] = precio_noche
                df_censo.at[idx, "moneda"] = "EUR"
                df_censo.at[idx, "puntuacion"] = mejor_match.get("puntuacion")
                df_censo.at[idx, "metodo_cruce"] = "booking_playwright"
                df_censo.at[idx, "similitud"] = mejor_score
                df_censo.at[idx, "dudoso"] = False

    SALIDA.parent.mkdir(parents=True, exist_ok=True)

    df_censo.to_csv(SALIDA, index=False, encoding="utf-8")

    precios_finales = df_censo["precio"].notna().sum()

    print("=" * 60)
    print("INFORME DE ENRIQUECIMIENTO STRICTO DE HOTELES DE BARCELONA")
    print("=" * 60)
    print(f"Total de hoteles registrados en el censo oficial: {len(df_censo)}")
    print(f"Hoteles con precio verificado antes del cruce: {precios_iniciales} ({precios_iniciales / len(df_censo):.1%})")
    print(f"Hoteles verdaderos asignados desde Booking.com: {registros_rellenados}")
    print(f"Hoteles con precio tras el cruce estricto: {precios_finales} ({precios_finales / len(df_censo):.1%})")
    print("-" * 60)
    print(f" - CSV procesado guardado en: {SALIDA}")
    print("=" * 60)

    return df_censo


def main():
    """Punto de entrada principal para ejecutar el enriquecimiento."""
    cruzar_y_enriquecer_censo()


if __name__ == "__main__":
    main()
