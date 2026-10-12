"""Exporta el embudo de Airbnb para `/airbnb`: de los anuncios del volcado a las viviendas del analisis.

    python pipeline/export/export_criba.py

Salida
    data/exports/mapa/criba_airbnb.json   — anuncios y plazas que caen en cada paso, con su desglose

Lee `airbnb_excluidos_web.csv` y `airbnb_para_web.csv`, que escribe el notebook de limpieza y retoca
`gold/separar_sin_registro.py`. No lleva ningun dato por anuncio: solo recuentos.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
GOLD = RAIZ / "data" / "gold"
DESTINO = RAIZ / "data" / "exports" / "mapa"


def volcar(ruta: Path, datos) -> None:
    """Escribe JSON valido: sin NaN ni Infinity, que `json` acepta y el navegador no."""
    ruta.write_text(json.dumps(datos, ensure_ascii=False, allow_nan=False), encoding="utf-8")


# La criba, en el orden en que se aplica. La clave es el `motivo_exclusion` del CSV; el resto es
# como se cuenta en la web. El orden va de lo estructural a lo circunstancial: primero si la ley le
# alcanza, despues si sigue vivo, y al final si es una repeticion.
#
# **Un anuncio puede fallar varias condiciones a la vez y solo se cuenta en la primera.** Por eso el
# orden no es decorativo: moverlo cambia los numeros de cada paso sin cambiar el total.
PASOS_CRIBA = [
    ("alojamiento_reglado", "Es un hotel, albergue o apartament turístic, o una habitación de uno",
     "Se rige por otro régimen y la ley de 2028 no lo toca; el establecimiento ya cuenta en el lado "
     "hotelero. Incluye los 14 anuncios de habitaciones de hotel, que es el mismo caso."),
    ("habitacion_sin_hutb", "Alquila una habitación suelta, sin declarar licencia",
     "Lo que desaparece en 2028 son las licencias de vivienda de uso turístico, no las "
     "habitaciones dentro de una casa."),
    ("estancia_de_32_noches", "Exige quedarse más de 31 noches",
     "La normativa catalana define estancia turística como 31 días o menos. Por encima es "
     "alquiler de temporada, que la ley de 2028 no toca."),
    ("sin_actividad_desde_09_2025", "No tiene ninguna reseña desde septiembre de 2025",
     "Sigue publicado pero no vende. Contarlo diría que hay oferta donde no la hay."),
    ("duplicado de nombre y anfitrion", "Repite nombre y anfitrión de otro anuncio ya contado",
     "Una misma vivienda puede anunciarse varias veces. Contarla dos veces infla el parque."),
    ("sin_registro_acreditado", "No tiene un registro acreditado en el registro oficial",
     "La ley de 2028 quita licencias, y este piso no tiene ninguna acreditada que perder. Si sigue "
     "operando será fuera del mercado legal, y no hay dato que diga que se vaya: no cuenta como "
     "turista que haya que realojar."),
]


ROOM = {"Entire home/apt": "Vivienda entera", "Private room": "Habitación privada",
        "Shared room": "Habitación compartida", "Hotel room": "Habitación de hotel"}
MOTIVO_REGISTRO = {
    "número por encima del máximo emitido": "Número imposible", "número de relleno (123456, 000000 y similares)": "Número imposible",
    "número que no consta en el registro": "Número que no consta",
    "HUTB válido usado para anunciar una habitación, no la vivienda entera": "Número de otra cosa",
    "el anfitrión acredita hotel o albergue en otros anuncios": "Número de otra cosa",
    "no declara nada": "No declara nada", "declara exención": "Declara exención",
    "HUTB que no consta, y además anuncia una habitación": "Habitación con número falso",
    "anfitrión con HUTB, pero nada liga esta vivienda a ninguna": "Anfitrión con otras licencias",
}


def desglose(clave: str, g: pd.DataFrame) -> list[dict]:
    """Los anuncios de un descarte, partidos por lo que mejor explica ese descarte."""
    if clave == "alojamiento_reglado":
        s = g["categoria_licencia"].fillna("Habitación de hotel")
        s = s.str.replace(r" \(.*\)", "", regex=True).replace({"Apartament turístic": "Apartamento turístico"})
    elif clave == "habitacion_sin_hutb":
        s = g["neighbourhood_group"]
    elif clave == "estancia_de_32_noches":
        s = pd.cut(pd.to_numeric(g["minimum_nights"], errors="coerce"), [0, 32, 89, 364, 10_000],
                   labels=["32 noches", "33 a 89", "90 a 364", "un año o más"]).astype(str)
    elif clave == "sin_actividad_desde_09_2025":
        a = pd.to_datetime(g["last_review_dt"], errors="coerce").dt.year
        s = pd.cut(a, [0, 2022, 2023, 2024, 2025], labels=["2022 o antes", "2023", "2024", "2025"]).astype(str)
    elif clave == "duplicado de nombre y anfitrion":
        s = pd.cut(pd.to_numeric(g["calculated_host_listings_count"], errors="coerce"), [0, 9, 99, 299, 10_000],
                   labels=["Anfitrión de 1 a 9 anuncios", "de 10 a 99", "de 100 a 299", "de 300 o más"]).astype(str)
    elif clave == "sin_registro_acreditado":
        s = g["motivo_estado"].map(MOTIVO_REGISTRO).fillna("Otro")
    else:
        return []
    c = s.value_counts()
    return [{"etiqueta": k, "anuncios": int(v)} for k, v in c.items()]


def exportar_criba_airbnb() -> dict:
    """El embudo de 15.406 anuncios a 4.985 viviendas, paso a paso.

    Se publican **anuncios y plazas** en cada paso. Solo con anuncios, descartar 3.083 habitaciones
    sueltas y 901 hoteles parece comparable, y en plazas no lo es: una habitacion suelta aloja a dos
    personas y un hotel a doscientas.
    """
    ruta = GOLD / "airbnb_excluidos_web.csv"
    if not ruta.exists():
        return {"pasos": 0}
    fuera = pd.read_csv(ruta, low_memory=False)
    dentro = pd.read_csv(GOLD / "airbnb_para_web.csv", low_memory=False)

    # Si la criba cambia y este listado no, los numeros saldrian mal en silencio.
    # Una habitación de hotel y un hotel son el mismo descarte: se cuentan juntos.
    fuera = fuera.assign(motivo_exclusion=fuera["motivo_exclusion"].replace(
        {"habitacion_de_hotel": "alojamiento_reglado"}))
    claves = {c for c, *_ in PASOS_CRIBA}
    sobran = set(fuera["motivo_exclusion"].unique()) - claves
    if sobran:
        raise ValueError(f"motivos sin paso declarado en PASOS_CRIBA: {sobran}")

    quedan = len(fuera) + len(dentro)
    plazas = float(fuera["accommodates"].fillna(0).sum() + dentro["accommodates"].fillna(0).sum())
    pasos = []
    for clave, titulo, porque in PASOS_CRIBA:
        caen = fuera[fuera["motivo_exclusion"] == clave]
        quedan -= len(caen)
        plazas -= float(caen["accommodates"].fillna(0).sum())
        pasos.append({
            "clave": clave, "titulo": titulo, "porque": porque,
            "descartados": len(caen),
            "plazas_descartadas": int(round(caen["accommodates"].fillna(0).sum())),
            "quedan": quedan,
            "plazas_restantes": int(round(plazas)),
            "desglose": desglose(clave, caen),
        })

    volcar(DESTINO / "criba_airbnb.json", {
        "inicio": {"anuncios": len(fuera) + len(dentro),
                   "plazas": int(round(float(fuera["accommodates"].fillna(0).sum()
                                             + dentro["accommodates"].fillna(0).sum())))},
        "pasos": pasos,
        "partida": [{"etiqueta": ROOM.get(k, k), "anuncios": int(v)} for k, v in
                    pd.concat([fuera["room_type"], dentro["room_type"]]).value_counts().items()],
    })
    return {"pasos": len(pasos), "inicio": len(fuera) + len(dentro), "final": quedan}


def main() -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)
    print(exportar_criba_airbnb())


if __name__ == "__main__":
    main()
