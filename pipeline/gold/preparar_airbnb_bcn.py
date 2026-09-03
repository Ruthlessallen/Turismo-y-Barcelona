"""Tabla publicable de la oferta anunciada en Airbnb, con precio por plaza y banda economica.

    python pipeline/gold/preparar_airbnb_bcn.py

Entradas
    data/bronze/airbnb_anuncios.csv            — anuncios con capacidad y precio por plaza
    data/gold/airbnb_situacion_licencia.csv    — que declara cada anuncio sobre su licencia
    data/bronze/adr_estacionalidad.csv         — factor de temporada, para el equivalente anual

Salida
    data/gold/airbnb_bcn.csv

Pone la oferta de Airbnb en la **misma escala** que el alojamiento reglado, que es lo que permite
preguntar adonde puede ir quien se quede sin su piso turistico en 2028. Sin esa escala comun la
comparacion no existe: 221 EUR de un piso para cuatro y 174 EUR de una habitacion de hotel no
dicen nada enfrentados.

**El volcado es del 24 de junio y se corrige de temporada.** Junio esta un 19,8% por encima de la
media anual segun la serie del INE. Comparar un Airbnb de junio con un hotel ya llevado a
equivalente anual atribuiria a Airbnb una carestia que es del calendario.

**Y ahi va una suposicion que conviene tener presente:** se aplica a Airbnb la estacionalidad
**hotelera**, porque no existe una serie de estacionalidad para el alquiler turistico. Es
razonable —los dos venden noches a los mismos visitantes en la misma ciudad— pero no esta medido.
Si la estacionalidad de Airbnb fuese mas plana, esta correccion lo abarataria de mas.

**Que no se publica.** Ni el anuncio ni su ubicacion salen a `data/exports`: una VUT es una
vivienda, y las coordenadas de Inside Airbnb ya vienen desplazadas hasta 200 m a proposito. Esta
tabla existe para agregarse por barrio, no para senalar pisos.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from bandas import ETIQUETAS, por_plaza

RAIZ = Path(__file__).resolve().parents[2]
BRONZE = RAIZ / "data" / "bronze"
GOLD = RAIZ / "data" / "gold"
SALIDA = GOLD / "airbnb_bcn.csv"
SALIDA_EXCLUIDOS = GOLD / "airbnb_excluidos.csv"

# Mes del volcado de Inside Airbnb.
MES_VOLCADO = 6

# El decreto define el uso turistico como cesion por un periodo "igual o inferior a 31 dies".
# Igual O INFERIOR: un anuncio cuyo minimo son 31 noches puede alojar una estancia de 31 noches,
# que es uso turistico y necesita licencia. Solo a partir de 32 queda fuera del alcance de la ley.
NOCHES_USO_TURISTICO = 31

# Que figura legal declara cada prefijo del Registre. Solo la primera esta sujeta a la eliminacion
# de 2028; las demas son alojamiento reglado que sigue operando y cuenta en el lado hotelero.
REGIMEN = {"HUTB": "vivienda_uso_turistico", "HUT": "vivienda_uso_turistico",
           "HB": "hotel", "HCC": "hotel", "AJ": "albergue",
           "ATB": "apartament_turistic", "ATCC": "apartament_turistic"}

# Un anuncio inactivo es el que tuvo huespedes y dejo de tenerlos. No basta con no tener resenas:
# los 3.088 que no tienen ninguna ofrecen 282 noches de mediana, mas calendario abierto que los
# que si las tienen, asi que son nuevos o simplemente no resenados, no muertos.
DIAS_DISPONIBLES_MINIMOS = 30

PATRON_REGIONAL = re.compile(
    r"Barcelona\s*-\s*Regional registration number\s*(?:<br\s*/?>)*\s*([^<]*)", re.I)

MOTIVOS = ["regimen_no_vut", "no_es_cesion_entera", "estancia_de_32_noches", "sin_actividad",
           "repeticion_de_vivienda", "sin_precio_aprovechable"]

# Ultimo ano con volcado. Un anuncio sin precio cuya ultima resena es anterior no aporta ni oferta
# ni tarifa.
ANYO_VOLCADO = 2026

COLUMNAS = ["id", "host_id", "host_perfil", "regimen", "cesion_entera", "estado_actividad",
            "sujeto_a_ley_vut", "motivo_exclusion", "anuncios_del_anfitrion", "last_review", "neighbourhood_group", "neighbourhood", "room_type",
            "property_type", "accommodates", "bedrooms", "minimum_nights", "uso_turistico",
            "borde_31_noches", "licencia_regional", "vivienda_id", "anuncios_de_la_vivienda",
            "es_repeticion", "precio_anuncio", "precio_por_plaza", "precio_plaza_anual",
            "banda_plaza", "factor_temporada", "number_of_reviews_ltm", "availability_365",
            "license", "situacion", "sujeto_a_vut", "sin_licencia", "actividad_reciente"]


def factor_de_junio() -> float:
    """Cuanto pesa el mes del volcado sobre la media del año.

    Se promedian las cuatro categorias oficiales en vez de elegir una: la de "1 y 2 estrellas y
    estrellas de plata" seria la mas parecida al mercado de Airbnb por precio, pero esa semejanza
    es una suposicion sobre la que no hay dato, y el promedio no privilegia ninguna lectura. Las
    cuatro rondan 1,16-1,20 en junio, asi que la eleccion cambia poco.
    """
    est = pd.read_csv(BRONZE / "adr_estacionalidad.csv")
    return float(est.loc[est["mes"] == MES_VOLCADO, "factor"].mean())


def clasificar(d: pd.DataFrame) -> pd.DataFrame:
    """Decide que anuncios cuentan como vivienda de uso turistico sujeta a la ley.

    Tres criterios, y ninguno es opcional:

    **El regimen declarado.** 897 anuncios declaran licencia de hotel, albergue o apartament
    turistic. Son alojamiento reglado que la eliminacion de 2028 no toca: cuentan en el lado
    hotelero, no en el de los pisos que desaparecen.

    **La cesion ha de ser de la vivienda entera.** La figura del habitatge d'us turistic se define
    por ceder el alojamiento completo; alquilar habitaciones sueltas no es un HUT. Son 4.494
    anuncios de habitacion, y quedan fuera del recuento — lo que no significa que sean legales,
    solo que no son lo que la ley de 2028 elimina. Entre ellos hay 631 que declaran un HUTB
    anunciando una habitacion, que es usar una licencia de vivienda entera para otra cosa.

    **La estancia minima.** Ver `NOCHES_USO_TURISTICO`.
    """
    d = d.copy()
    prefijo = d["licencia_regional"].str.extract(r"^([A-Z]{2,4})", expand=False)
    d["regimen"] = prefijo.map(REGIMEN).fillna("sin_declarar")
    d["cesion_entera"] = d["room_type"].eq("Entire home/apt")
    return d


def estado_de_actividad(d: pd.DataFrame) -> pd.Series:
    """Si el anuncio vende, no vende, o no se puede saber.

    Un anuncio sin resenas en un ano no ha tenido huespedes que lo dejaran, y mantener una licencia
    para algo que no se vende no tiene sentido economico. Pero "sin resenas" no basta como criterio:
    hay que separar al que dejo de vender del que aun no ha empezado.

    - `activo`        alguna resena en los ultimos doce meses.
    - `sin_confirmar` ninguna resena nunca, pero mas de 30 noches disponibles. No se puede afirmar
      que venda ni que no; su calendario esta abierto, asi que darlo por inexistente restaria
      oferta real.
    - `inactivo`      tuvo resenas y ninguna en doce meses, o no tuvo ninguna y ademas tiene el
      calendario cerrado. La mediana de estos lleva ano y medio sin una resena y el percentil 90,
      casi ocho anos.

    El reparto valida el criterio por otro lado: el 51% de los `inactivo` no tienen ni precio,
    frente al 5% de los `activo`. Los nulos de precio estan donde estan los anuncios apagados.
    """
    ltm = pd.to_numeric(d["number_of_reviews_ltm"], errors="coerce").fillna(0) > 0
    nunca = pd.to_numeric(d["number_of_reviews"], errors="coerce").fillna(0) == 0
    disponible = pd.to_numeric(d["availability_365"], errors="coerce").fillna(0) >         DIAS_DISPONIBLES_MINIMOS
    return pd.Series(np.select([ltm, nunca & disponible], ["activo", "sin_confirmar"],
                               default="inactivo"), index=d.index)


def sin_precio_aprovechable(d: pd.DataFrame) -> pd.Series:
    """Anuncios sin precio de los que ademas no se puede deducir ninguno.

    Antes de descartar nada se agota la via de recuperarlo: la deduplicacion conserva la copia que
    si cotiza (ver `marcar_repeticiones`), lo que devuelve el precio de 21 viviendas que antes
    quedaban representadas por su copia muda.

    De lo que queda se descarta:

    - Lo que lleva sin resenas desde 2025 o antes. Sin tarifa y sin huespedes recientes, no es
      oferta que nadie pueda contratar.
    - Lo de 2026 cuyo anfitrion no tiene ningun otro anuncio. Sin tarifa propia ni un anuncio
      hermano del que deducirla, no hay de donde sacar el precio.

    Se conserva, en cambio, lo de 2026 cuyo anfitrion si cotiza en otros anuncios: son 148 casos
    con el calendario abierto --hasta 124 dias-- que lo mas probable es que estuvieran ocupados el
    dia del volcado. Eso es oferta real aunque ese dia no tuviera hueco, y contarla como
    inexistente restaria viviendas del alcance de la ley.

    Los que nunca han tenido una resena tampoco se descartan: ofrecen 313 dias de mediana y son
    anuncios recien publicados, no apagados.
    """
    sin_precio = d["precio_anuncio"].isna()
    resena = pd.to_datetime(d["last_review"], errors="coerce")
    anterior = resena.dt.year < ANYO_VOLCADO
    huerfano = resena.dt.year.eq(ANYO_VOLCADO) & (d["anuncios_del_anfitrion"] <= 1)
    return sin_precio & (anterior | huerfano)


def motivo_de_exclusion(d: pd.DataFrame) -> pd.Series:
    """Por que un anuncio no cuenta. Se queda el primer motivo que aplica, en este orden.

    El orden importa para leer el embudo: un hotel que ademas lleva dos anos sin resenas sale como
    `regimen_no_vut`, porque lo primero que hay que decir de el es que nunca estuvo sujeto a la ley.
    """
    return pd.Series(np.select(
        [d["regimen"].isin(["hotel", "albergue", "apartament_turistic"]),
         ~d["cesion_entera"],
         ~d["uso_turistico"],
         d["estado_actividad"].eq("inactivo"),
         d["es_repeticion"],
         sin_precio_aprovechable(d)],
        MOTIVOS, default=None), index=d.index)


def marcar_repeticiones(d: pd.DataFrame) -> pd.DataFrame:
    """Senala los anuncios que son la misma vivienda, sin borrarlos.

    El discriminante es la licencia declarada, no que las filas se parezcan: hay 903 filas
    identicas en host, barrio, tipo, capacidad y precio, y una parte son habitaciones distintas
    del mismo hostel, que son oferta real y no duplicados.

    **Solo se aplica a las HUTB.** Una vivienda de uso turistico es, por definicion, una vivienda:
    dos anuncios con el mismo HUTB son el mismo piso —530 licencias aparecen repetidas, con 1.028
    filas de mas—. En cambio un hotel (`HB`) promedia 3,66 anuncios por licencia y un albergue
    (`AJ`) 4,72, porque publican sus habitaciones por separado y cada una es oferta distinta.

    No se eliminan filas: `es_repeticion` marca las que no son la primera de su vivienda, y quien
    cuente oferta filtra por esa columna. Borrarlas perderia el numero de veces que un mismo piso
    esta anunciado, que es informacion sobre como opera ese titular.
    """
    d = d.copy()
    d["licencia_regional"] = d["license"].map(
        lambda t: (lambda m: m.group(1).strip() if m else None)(PATRON_REGIONAL.search(str(t))))

    es_hutb = d["licencia_regional"].str.match(r"^HUTB", na=False)
    d["vivienda_id"] = np.where(es_hutb, d["licencia_regional"], "anuncio:" + d["id"].astype(str))
    d["anuncios_de_la_vivienda"] = d.groupby("vivienda_id")["id"].transform("size")

    # De cada vivienda se conserva la copia mas util, no la primera que salga. El orden es: que
    # tenga precio, que su ultima resena sea mas reciente, y el id como desempate reproducible.
    #
    # No es un detalle de estilo. Quedarse con la primera por id dejaba 21 viviendas representadas
    # por una copia sin precio mientras se descartaba la copia que si cotizaba: el mismo piso, el
    # dato disponible, y tirado por el criterio de desempate.
    orden = d.assign(
        _con_precio=d["precio_anuncio"].notna().astype(int),
        _resena=pd.to_datetime(d.get("last_review"), errors="coerce"),
    ).sort_values(["_con_precio", "_resena", "id"], ascending=[False, False, True])
    d["es_repeticion"] = orden.duplicated("vivienda_id").reindex(d.index) & es_hutb
    d["es_repeticion"] = d["es_repeticion"].fillna(False)
    return d


def perfil_del_anfitrion(d: pd.DataFrame) -> pd.Series:
    """Si un anfitrion acredita licencia en unos anuncios y en otros no.

    Importa porque cambia como se lee un anuncio sin licencia. Quien no acredita ninguna puede ser
    un particular que desconoce el tramite; quien acredita en trescientos anuncios y no en ciento
    diecisiete sabe perfectamente cual es el tramite. Son 163 anfitriones que concentran el 25% de
    la oferta turistica, con una mediana de siete anuncios cada uno.
    """
    turistico = d[d["uso_turistico"]]
    con = turistico["situacion"].eq("licencia_verificada").groupby(turistico["host_id"]).sum()
    sin = (turistico["situacion"]
           .isin(["sin_declarar", "licencia_no_encontrada", "hutb_no_verificable"])
           .groupby(turistico["host_id"]).sum())
    perfil = pd.Series("sin_anuncios_turisticos", index=con.index, dtype=object)
    perfil[(con > 0) & (sin == 0)] = "solo_con_licencia"
    perfil[(con == 0) & (sin > 0)] = "solo_sin_licencia"
    perfil[(con > 0) & (sin > 0)] = "mixto"
    return d["host_id"].map(perfil)


def main() -> None:
    a = pd.read_csv(BRONZE / "airbnb_anuncios.csv", low_memory=False)
    print(f"Anuncios: {len(a):,}")

    if "last_review" not in a.columns:
        raise KeyError("falta last_review en bronze/airbnb_anuncios.csv")

    licencias = pd.read_csv(GOLD / "airbnb_situacion_licencia.csv", low_memory=False)
    a = a.merge(
        licencias[["id", "situacion", "sujeto_a_vut", "sin_licencia", "actividad_reciente"]],
        on="id", how="left")

    a["uso_turistico"] = a["minimum_nights"] <= NOCHES_USO_TURISTICO
    a["borde_31_noches"] = a["minimum_nights"] == NOCHES_USO_TURISTICO
    a = marcar_repeticiones(a)
    a = clasificar(a)
    a["estado_actividad"] = estado_de_actividad(a)
    a["anuncios_del_anfitrion"] = a.groupby("host_id")["id"].transform("size")
    a["host_perfil"] = perfil_del_anfitrion(a)
    a["motivo_exclusion"] = motivo_de_exclusion(a)
    a["sujeto_a_ley_vut"] = a["motivo_exclusion"].isna()

    factor = factor_de_junio()
    a["factor_temporada"] = round(factor, 3)
    a["precio_plaza_anual"] = (a["precio_por_plaza"] / factor).round(2)
    a["banda_plaza"] = por_plaza(a["precio_plaza_anual"])

    sujetos = a[a["sujeto_a_ley_vut"]]
    excluidos = a[~a["sujeto_a_ley_vut"]]
    sujetos[COLUMNAS].to_csv(SALIDA, index=False, encoding="utf-8")
    excluidos[COLUMNAS].to_csv(SALIDA_EXCLUIDOS, index=False, encoding="utf-8")

    print(); print("  EMBUDO")
    print(f"    de partida                    {len(a):6,}")
    for motivo in MOTIVOS:
        print(f"    -{motivo:28s} {int((a['motivo_exclusion'] == motivo).sum()):6,}")
    print(f"    = sujetos a la ley de 2028    {len(sujetos):6,}")

    con = sujetos["banda_plaza"].notna()
    print(); print(f"  factor de temporada (junio): {factor:.3f}")
    print(f"  con precio y banda         : {int(con.sum()):,} de {len(sujetos):,} "
          f"({con.mean():.1%}) | sin precio {int((~con).sum()):,}")
    print(f"  en el borde de 31 noches   : {int(sujetos['borde_31_noches'].sum()):,}")
    print(f"  perfil del anfitrion       : {sujetos['host_perfil'].value_counts().to_dict()}")
    print(f"  estado                     : {sujetos['estado_actividad'].value_counts().to_dict()}")
    print(f"  con precio por plaza       : {int(con.sum()):,} ({con.mean():.1%})")
    print(); print("  reparto por banda: "
          f"{sujetos['banda_plaza'].value_counts().reindex(ETIQUETAS).to_dict()}")

    vivos = sujetos[con]
    print(); print("  precio por plaza y noche, por perfil del anfitrion:")
    print(vivos.groupby("host_perfil")["precio_plaza_anual"]
          .agg(["size", "median"]).round(1).to_string())

    print(); print("  por situacion de licencia:")
    print(vivos.groupby("situacion")["precio_plaza_anual"]
          .agg(["size", "median"]).round(1).sort_values("size", ascending=False).to_string())

    print(); print(f"Guardado en {SALIDA.relative_to(RAIZ)}")
    print(f"           {SALIDA_EXCLUIDOS.relative_to(RAIZ)}  ({len(excluidos):,} anuncios)")


if __name__ == "__main__":
    main()
