"""Unifica los registros de alojamiento turístico de las dos fuentes disponibles.

Cubre dos categorías, con el mismo método pero distinta configuración:
  - `hoteles`: hoteles y apartamentos turísticos (AT) de toda la provincia.
  - `vut`: viviendas de uso turístico (HUT), el objeto central del proyecto.

Fuentes (ver docs/architecture.md):
  - Registre de Turisme de Catalunya (Generalitat): toda la provincia, con CIF/razón social
    del titular. No trae coordenadas, ni plazas en el caso de los HUT.
  - Open Data BCN: solo ciudad de Barcelona, con coordenadas reales. Aporta además las plazas
    en el caso de los HUT. No trae titular.

No son duplicados a eliminar: cada fuente aporta campos que la otra no tiene (ver
docs/data-model.md → "Estrategia frente a Open Data BCN"). El objetivo es un registro unificado
que conserve lo mejor de ambas sin inventar ni perder filas.

Estrategia, en dos pasadas:
  1. Cruce exacto por número de registro oficial. Es una clave real, no una heurística:
     verificado el 2026-08-28, cruzan 443/446 en hoteles y 10.556 en VUT.
  2. Solo para lo que quede suelto: cruce por dirección normalizada, y únicamente cuando la
     correspondencia es 1:1. Cualquier ambigüedad se deja sin cruzar y se marca, antes que
     arriesgar una fusión incorrecta.

Uso:
    python unificar_registros.py            # ambas categorías
    python unificar_registros.py vut        # solo una
"""

from __future__ import annotations

import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
CRUDO = RAIZ / "data" / "raw"
PROCESADO = RAIZ / "data" / "processed"

# Patrón de los números de registro del Registre de Turisme de Catalunya.
# HB/HCC = hoteles, ATB/ATCC = apartamentos turísticos, HUTB = viviendas de uso turístico.
PATRON_CODIGO = re.compile(r"\b((?:HUTB|HCC|ATCC|HB|ATB)-?\d+)\b", re.IGNORECASE)

# Abreviaturas de tipo de vía → forma canónica. Cada fuente las escribe a su manera.
TIPOS_VIA = {
    "C": "CARRER", "CL": "CARRER", "CARRER": "CARRER", "CALLE": "CARRER",
    "AV": "AVINGUDA", "AVD": "AVINGUDA", "AVGDA": "AVINGUDA", "AVINGUDA": "AVINGUDA",
    "PS": "PASSEIG", "PG": "PASSEIG", "PASSEIG": "PASSEIG", "PASEO": "PASSEIG",
    "PL": "PLACA", "PZ": "PLACA", "PLACA": "PLACA", "PLAZA": "PLACA",
    "RB": "RAMBLA", "RAMBLA": "RAMBLA",
    "PJ": "PASSATGE", "PTGE": "PASSATGE", "PASSATGE": "PASSATGE",
    "RD": "RONDA", "RONDA": "RONDA",
    "TR": "TRAVESSERA", "TRAVESSERA": "TRAVESSERA",
    "CR": "CARRETERA", "CTRA": "CARRETERA", "CARRETERA": "CARRETERA",
    "GV": "GRAN VIA", "VIA": "VIA", "BXDA": "BAIXADA", "BAIXADA": "BAIXADA",
}

# Partículas que sobran al comparar nombres de calle: "Carrer de Llançà" == "Llançà".
PARTICULAS = {"DE", "DEL", "DELS", "DE LA", "DE LES", "D", "LA", "EL", "ELS", "LES", "L"}

# Por debajo de esta similitud de nombre, un cruce por dirección se marca para revisión manual.
UMBRAL_NOMBRE = 0.34


@dataclass(frozen=True)
class Perfil:
    """Configuración de una categoría. El método es idéntico; solo cambian fuentes y columnas."""

    nombre: str
    ruta_registre: Path
    ruta_opendata: Path
    salida: Path
    # Columnas del Registre → nombre canónico (ver docs/data-model.md).
    columnas_registre: dict[str, str]
    # Columnas de Open Data BCN → nombre canónico.
    columnas_opendata: dict[str, str]
    # Columna de Open Data BCN con el número de registro. Si es None, se extrae del nombre.
    columna_codigo: str | None
    # Campos que Open Data BCN aporta y el Registre no tiene.
    aporta: tuple[str, ...]
    # Si el cruce por dirección debe distinguir piso y puerta (imprescindible en VUT: varias
    # viviendas turísticas conviven en el mismo portal).
    usa_piso_puerta: bool = False
    encoding_opendata: str = "utf-8"
    mapa_tipos: dict[str, str] = field(default_factory=dict)


PERFILES = {
    "hoteles": Perfil(
        nombre="hoteles",
        ruta_registre=CRUDO / "registre_turisme" / "hoteles_y_apartaments_turistics_provincia_barcelona.csv",
        ruta_opendata=CRUDO / "hoteles" / "opendata_bcn_hotels_snapshot.csv",
        salida=PROCESADO / "hoteles_y_apartaments_unificados.csv",
        columnas_registre={
            "n_mero_inscripci": "licencia_id", "tipus_establiment": "tipo_raw",
            "r_tol": "nombre_comercial", "municipi": "municipio",
            "codi_municipi_idescat": "codi_ine", "comarca": "comarca",
            "tipus_de_via": "tipo_via", "nom_de_la_via": "nombre_via", "numero": "numero",
            "codi_postal": "codigo_postal", "categoria": "categoria",
            "total_places": "plazas", "total_estances": "habitaciones",
            "cif": "nif", "ra_social_del_titular": "razon_social",
        },
        columnas_opendata={
            "geo_epgs_4326_lat": "lat", "geo_epgs_4326_lon": "lon",
            "addresses_roadtype_name": "tipo_via_od", "addresses_road_name": "nombre_via_od",
            "addresses_start_street_number": "numero_od", "addresses_town": "municipio_od",
            "name": "nombre_od", "register_id": "id_od",
        },
        columna_codigo=None,  # va incrustado en `name`: "Hotel ... - HB-004452"
        aporta=("lat", "lon"),
        mapa_tipos={"Hotels": "hotel", "Apartaments Turístics": "apartament_turistic"},
    ),
    "vut": Perfil(
        nombre="vut",
        ruta_registre=CRUDO / "registre_turisme" / "hut_provincia_barcelona.csv",
        ruta_opendata=CRUDO / "vut" / "opendata_bcn_hut_2016-2026Q1.csv",
        salida=PROCESADO / "vut_unificados.csv",
        columnas_registre={
            "n_mero_inscripci": "licencia_id", "tipus_establiment": "tipo_raw",
            "r_tol": "nombre_comercial", "municipi": "municipio",
            "codi_municipi_idescat": "codi_ine", "comarca": "comarca",
            "tipus_de_via": "tipo_via", "nom_de_la_via": "nombre_via", "numero": "numero",
            "pis": "piso", "porta": "puerta",
            "codi_postal": "codigo_postal", "categoria": "categoria",
            "cif": "nif", "ra_social_del_titular": "razon_social",
        },
        columnas_opendata={
            "LATITUD_Y": "lat", "LONGITUD_X": "lon",
            "TIPUS_CARRER": "tipo_via_od", "CARRER": "nombre_via_od", "NUM1": "numero_od",
            "PIS": "piso_od", "PORTA": "puerta_od",
            "NUMERO_PLACES": "plazas", "N_EXPEDIENT": "id_od",
            "NOM_DISTRICTE": "distrito", "NOM_BARRI": "barrio",
        },
        columna_codigo="NUMERO_REGISTRE_GENERALITAT",
        # El Registre no publica plazas para HUT: aquí Open Data BCN aporta también capacidad.
        aporta=("lat", "lon", "plazas", "distrito", "barrio"),
        usa_piso_puerta=True,
        mapa_tipos={"Habitatges d'ús turístic": "vut"},
    ),
}


def texto_o_vacio(valor: object) -> str:
    """Convierte nulos a cadena vacía. No usar `valor or ''`: NaN es *truthy* en Python y
    acabaría colándose el literal 'nan' dentro de las claves de cruce."""
    if valor is None or pd.isna(valor):
        return ""
    return str(valor)


def quitar_acentos(texto: str) -> str:
    """Normaliza a mayúsculas sin acentos ni signos, para comparar cadenas de fuentes distintas."""
    if not isinstance(texto, str):
        return ""
    sin_acentos = "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"[^\w\s]", " ", sin_acentos.upper())


def normalizar_via(tipo: object, nombre: object) -> str:
    """Devuelve una forma canónica de la vía, comparable entre las dos fuentes.

    Une tipo y nombre porque cada fuente los reparte distinto: el Registre lleva el tipo en
    columna aparte, mientras que Open Data BCN (hoteles) deja `addresses_roadtype_name` vacío
    y mete el tipo dentro del propio nombre ("C Princesa", "Ronda de Sant Antoni").
    """
    texto = quitar_acentos(f"{texto_o_vacio(tipo)} {texto_o_vacio(nombre)}")
    palabras = [p for p in texto.split() if p]
    if not palabras:
        return ""

    canonico = TIPOS_VIA.get(palabras[0])
    if canonico:
        palabras = palabras[1:]
        if palabras and TIPOS_VIA.get(palabras[0]) == canonico:
            palabras = palabras[1:]  # tipo repetido en ambas columnas
    else:
        canonico = ""

    palabras = [p for p in palabras if p not in PARTICULAS]
    return f"{canonico} {' '.join(palabras)}".strip()


def primer_numero(valor: object) -> str:
    """Extrae el primer número de un portal. '2-4' → '2'; el Catastro tampoco acepta rangos."""
    encontrados = re.findall(r"\d+", texto_o_vacio(valor))
    return encontrados[0] if encontrados else ""


def normalizar_unidad(valor: object) -> str:
    """Normaliza piso o puerta. '01' y '1' son el mismo piso; 'Bx' y 'BJ' no se tocan."""
    texto = quitar_acentos(texto_o_vacio(valor)).strip()
    return texto.lstrip("0") or texto


def clave_direccion(fila: pd.Series, campos: dict[str, str], usa_piso_puerta: bool) -> str:
    """Clave de cruce por dirección. Vacía si falta cualquier parte obligatoria: sin dirección
    completa no se cruza — es preferible dejarlo sin pareja que arriesgar una fusión incorrecta.

    En VUT se añaden piso y puerta: en un mismo portal puede haber decenas de viviendas
    turísticas, así que calle+número no identifica nada por sí solo.
    """
    via = normalizar_via(fila.get(campos["tipo_via"]), fila.get(campos["nombre_via"]))
    num = primer_numero(fila.get(campos["numero"]))
    mun = quitar_acentos(texto_o_vacio(fila.get(campos["municipio"]))).strip()
    if not (via and num and mun):
        return ""
    clave = f"{mun}|{via}|{num}"
    if usa_piso_puerta:
        clave += f"|{normalizar_unidad(fila.get(campos['piso']))}|{normalizar_unidad(fila.get(campos['puerta']))}"
    return clave


def parecido_nombres(a: object, b: object) -> float:
    """Similitud 0-1 entre dos nombres comerciales, ignorando palabras genéricas.

    Solo se usa para *avisar* sobre cruces por dirección dudosos, nunca para decidir el cruce:
    un establecimiento puede cambiar de marca conservando edificio y licencia (caso verificado:
    '45 Times Barcelona Hotel' pasó a 'BLESS Barcelona' por diseño de su operador).
    """
    genericas = {"HOTEL", "HOSTAL", "APARTAMENTS", "APARTAMENTOS", "BARCELONA", "THE", "DE", "LA"}
    tokens_a = {p for p in quitar_acentos(texto_o_vacio(a)).split() if p not in genericas}
    tokens_b = {p for p in quitar_acentos(texto_o_vacio(b)).split() if p not in genericas}
    if not tokens_a or not tokens_b:
        return 0.0
    return len(tokens_a & tokens_b) / min(len(tokens_a), len(tokens_b))


def normalizar_codigo(valor: object) -> str | None:
    """Limpia un número de registro para poder cruzarlo.

    La fuente no es homogénea: se han encontrado códigos con un espacio tras el guion
    ('HUTB- 077183'), que sin normalizar quedaban fuera del cruce por pura tipografía.
    """
    texto = quitar_espacios(texto_o_vacio(valor)).upper()
    return texto or None


def quitar_espacios(texto: str) -> str:
    """Elimina todos los espacios internos, no solo los de los extremos."""
    return re.sub(r"\s+", "", texto)


def extraer_codigo(nombre: object) -> str | None:
    """Saca el número de registro incrustado en el nombre de Open Data BCN (solo hoteles).

    'Hotel chic&basic Born Boutique - HB-004452' → 'HB-004452'
    """
    encontrado = PATRON_CODIGO.search(texto_o_vacio(nombre))
    if not encontrado:
        return None
    codigo = quitar_espacios(encontrado.group(1)).upper()
    if "-" not in codigo:  # el Registre siempre lleva guion
        prefijo = re.match(r"^[A-Z]+", codigo).group(0)
        codigo = f"{prefijo}-{codigo[len(prefijo):]}"
    return codigo


def cargar_registre(perfil: Perfil) -> pd.DataFrame:
    """Carga el Registre de Turisme y deja los campos que interesan, ya renombrados."""
    df = pd.read_csv(perfil.ruta_registre, dtype=str).rename(columns=perfil.columnas_registre)
    df["tipo"] = df["tipo_raw"].map(perfil.mapa_tipos)
    # Se normaliza igual que el lado de Open Data BCN: ambas fuentes traen códigos con
    # espacios sueltos, y un cruce por clave no perdona una diferencia tipográfica.
    df["licencia_id"] = df["licencia_id"].apply(normalizar_codigo)

    # "No aplica" es el marcador de la fuente para titular persona física (protegido por RGPD).
    df["es_persona_fisica"] = df["nif"].eq("No aplica")
    df.loc[df["es_persona_fisica"], ["nif", "razon_social"]] = pd.NA

    columnas = [c for c in perfil.columnas_registre.values() if c != "tipo_raw"]
    return df[columnas + ["tipo", "es_persona_fisica"]]


def cargar_opendata(perfil: Perfil) -> pd.DataFrame:
    """Carga Open Data BCN quedándose con lo que aporta y con el código de registro."""
    df = pd.read_csv(perfil.ruta_opendata, dtype=str, encoding=perfil.encoding_opendata)
    # Algunos CSV del portal llegan con BOM, que se cuela en el primer campo y en su cabecera.
    df.columns = [c.lstrip("﻿") for c in df.columns]
    df = df.rename(columns=perfil.columnas_opendata)
    if "id_od" in df:
        df["id_od"] = df["id_od"].str.lstrip("﻿")

    if perfil.columna_codigo:
        df["codigo"] = df[perfil.columna_codigo].apply(normalizar_codigo)
    else:
        df["codigo"] = df["nombre_od"].apply(extraer_codigo)

    columnas = ["codigo"] + [c for c in perfil.columnas_opendata.values()]
    return df[[c for c in dict.fromkeys(columnas) if c in df]]


def unificar(perfil: Perfil) -> pd.DataFrame:
    """Ejecuta las dos pasadas y devuelve el registro unificado de una categoría."""
    registre = cargar_registre(perfil)
    opendata = cargar_opendata(perfil)

    print(f"\n{'=' * 60}\n{perfil.nombre.upper()}\n{'=' * 60}")
    print(f"Registre de Turisme : {len(registre):,} filas")
    print(f"Open Data BCN       : {len(opendata):,} filas")

    # Guarda previa: si una clave estuviera repetida, un merge la multiplicaría en silencio.
    dup_reg = registre["licencia_id"].duplicated().sum()
    dup_od = opendata["codigo"].dropna().duplicated().sum()
    if dup_reg or dup_od:
        raise ValueError(
            f"Claves duplicadas antes de cruzar (registre={dup_reg}, opendata={dup_od}). "
            "Revisar las fuentes: el cruce multiplicaría filas."
        )

    aporta = list(perfil.aporta)

    # --- Pasada 1: cruce exacto por número de registro ---
    con_codigo = opendata[opendata["codigo"].notna()].copy()
    unificado = registre.merge(
        con_codigo[["codigo"] + aporta], left_on="licencia_id", right_on="codigo", how="left"
    )
    unificado["metodo_match"] = unificado["codigo"].notna().map(
        {True: "codigo_registro", False: pd.NA}
    )
    unificado = unificado.drop(columns=["codigo"])
    n_codigo = int((unificado["metodo_match"] == "codigo_registro").sum())
    print(f"\nPasada 1 — cruce por número de registro : {n_codigo:,} filas cruzadas")

    # --- Pasada 2: cruce por dirección, solo para lo que quedó suelto ---
    codigos_usados = set(con_codigo["codigo"]) & set(registre["licencia_id"])
    sueltos = opendata[
        opendata["codigo"].isna() | ~opendata["codigo"].isin(codigos_usados)
    ].copy()
    print(f"Filas de Open Data BCN sin cruzar tras pasada 1 : {len(sueltos):,}")

    campos_od = {
        "tipo_via": "tipo_via_od", "nombre_via": "nombre_via_od", "numero": "numero_od",
        "municipio": "municipio_od", "piso": "piso_od", "puerta": "puerta_od",
    }
    campos_reg = {
        "tipo_via": "tipo_via", "nombre_via": "nombre_via", "numero": "numero",
        "municipio": "municipio", "piso": "piso", "puerta": "puerta",
    }

    n_direccion = 0
    univocas: set[str] = set()
    if not sueltos.empty:
        # Open Data BCN solo cubre la ciudad; si no trae columna de municipio, se asume.
        if "municipio_od" not in sueltos:
            sueltos["municipio_od"] = "Barcelona"

        sueltos["clave"] = sueltos.apply(
            lambda r: clave_direccion(r, campos_od, perfil.usa_piso_puerta), axis=1
        )
        pendientes = unificado["metodo_match"].isna()
        claves_registre = unificado.loc[pendientes].apply(
            lambda r: clave_direccion(r, campos_reg, perfil.usa_piso_puerta), axis=1
        )

        # Solo se aceptan claves que aparezcan UNA vez en cada lado: un match ambiguo
        # (dos establecimientos en el mismo portal, p. ej.) se descarta a propósito.
        val_reg = claves_registre[claves_registre != ""].value_counts()
        val_od = sueltos.loc[sueltos["clave"] != "", "clave"].value_counts()
        univocas = set(val_reg[val_reg == 1].index) & set(val_od[val_od == 1].index)
        ambiguas = (set(val_reg[val_reg > 1].index) | set(val_od[val_od > 1].index)) & (
            set(val_reg.index) & set(val_od.index)
        )
        if ambiguas:
            print(f"  {len(ambiguas):,} direcciones descartadas por ambiguas (más de un candidato)")

        if univocas:
            mapa = sueltos[sueltos["clave"].isin(univocas)].set_index("clave")
            for idx, clave in claves_registre.items():
                if clave not in univocas:
                    continue
                for campo in aporta:
                    if campo in mapa:
                        unificado.loc[idx, campo] = mapa.loc[clave, campo]
                unificado.loc[idx, "metodo_match"] = "direccion"
                n_direccion += 1

                # El cruce por dirección es el camino frágil. Si además los nombres no se
                # parecen, se avisa para revisarlo: el match se conserva, pero queda marcado.
                if "nombre_od" in mapa:
                    similitud = parecido_nombres(
                        unificado.loc[idx, "nombre_comercial"], mapa.loc[clave, "nombre_od"]
                    )
                    unificado.loc[idx, "similitud_nombre"] = round(similitud, 2)
                    if similitud < UMBRAL_NOMBRE:
                        print(
                            f"  AVISO nombres dispares ({similitud:.0%}) en {clave}: "
                            f"'{unificado.loc[idx, 'nombre_comercial']}' vs "
                            f"'{mapa.loc[clave, 'nombre_od']}' — revisar a mano"
                        )
    print(f"Pasada 2 — cruce por dirección          : {n_direccion:,} filas cruzadas")

    unificado["metodo_match"] = unificado["metodo_match"].fillna("solo_registre")

    # Lo de Open Data BCN que no cruzó por ninguna vía no se tira: se conserva marcado. Suelen
    # ser altas recientes que el Registre todavía no recoge (verificado con el ibis budget de
    # Poblenou, alta de julio 2026), o bajas que el Registre ya retiró.
    cruzadas = (
        set(sueltos.loc[sueltos["clave"].isin(univocas), "id_od"])
        if not sueltos.empty and "clave" in sueltos and "id_od" in sueltos
        else set()
    )
    huerfanos = sueltos[~sueltos.get("id_od", pd.Series(dtype=str)).isin(cruzadas)] if not sueltos.empty else pd.DataFrame()
    if not huerfanos.empty:
        extra = pd.DataFrame({
            # Sin número de registro no hay `licencia_id` real: se genera uno trazable a partir
            # del id de Open Data BCN, en vez de fingir una licencia que no consta.
            "licencia_id": huerfanos["codigo"].fillna("OPENDATA-" + huerfanos["id_od"].astype(str)),
            "nombre_comercial": huerfanos.get("nombre_od"),
            "municipio": huerfanos.get("municipio_od"),
            "tipo_via": huerfanos.get("tipo_via_od"),
            "nombre_via": huerfanos.get("nombre_via_od"),
            "numero": huerfanos.get("numero_od"),
            "piso": huerfanos.get("piso_od"),
            "puerta": huerfanos.get("puerta_od"),
            "metodo_match": "solo_opendata",
            **{c: huerfanos[c] for c in aporta if c in huerfanos},
        })
        unificado = pd.concat([unificado, extra], ignore_index=True)
        print(f"Filas solo en Open Data BCN (conservadas): {len(extra):,}")

    return marcar_nivel_geo(marcar_coordenadas_compartidas(unificado))


def marcar_coordenadas_compartidas(df: pd.DataFrame) -> pd.DataFrame:
    """Marca las filas que comparten coordenada exacta con otra.

    No es un error de la unificación: Open Data BCN geocodifica a nivel de portal, así que
    establecimientos contiguos o en la misma finca caen en el mismo punto (verificado: el
    Toledano ocupa plantas del edificio del Continental, en Rambla 138). Importa para [M-06]:
    al agrupar por proximidad estos puntos son indistinguibles, así que cualquier recuento de
    *establecimientos por punto* debe hacerse por licencia, nunca por coordenada.
    """
    df["coordenada_compartida"] = False
    con_coords = df["lat"].notna() & df["lon"].notna()
    if con_coords.any():
        duplicadas = df.loc[con_coords].duplicated(subset=["lat", "lon"], keep=False)
        df.loc[duplicadas[duplicadas].index, "coordenada_compartida"] = True
    return df


def marcar_nivel_geo(df: pd.DataFrame) -> pd.DataFrame:
    """Declara con qué precisión geográfica se puede usar cada fila.

    Decisión de alcance (2026-08-28): no se geocodifica la provincia fuera de la ciudad de
    Barcelona. No es una limitación que estorbe: la eliminación de licencias VUT ocurre en la
    ciudad, que es justo donde Open Data BCN ya aporta coordenadas reales. Fuera de ella basta
    con municipio y código postal, que están al 100% en ambas categorías.

      - `coordenada`: lat/lon reales. Vale para análisis de proximidad ([M-06], [M-08]).
      - `municipio` : solo agregados por municipio / código postal / comarca ([M-07]).

    Cualquier cálculo de proximidad debe filtrar por `nivel_geo == "coordenada"` en vez de
    asumir que todas las filas son comparables entre sí.
    """
    df["nivel_geo"] = df["lat"].notna().map({True: "coordenada", False: "municipio"})
    return df


def informe(df: pd.DataFrame, perfil: Perfil) -> None:
    """Resumen por pantalla y comprobaciones finales."""
    print("\n--- Resultado ---")
    print(df["metodo_match"].value_counts().to_string())

    con_coords = int(df["lat"].notna().sum())
    print(f"\nFilas totales          : {len(df):,}")
    print(f"Nivel coordenada       : {con_coords:,} ({con_coords / len(df):.1%})  proximidad OK")
    print(f"Nivel municipio        : {len(df) - con_coords:,}  agregados por municipio/CP")
    if "plazas" in df:
        print(f"Con plazas             : {int(df['plazas'].notna().sum()):,}")
    compartidas = int(df["coordenada_compartida"].sum())
    print(f"Coordenada compartida  : {compartidas:,}  (misma finca o portales contiguos)")

    duplicados = int(df["licencia_id"].duplicated().sum())
    if duplicados:
        raise ValueError(f"El resultado tiene {duplicados} licencia_id duplicados.")
    print("Sin duplicados         : OK")

    perfil.salida.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(perfil.salida, index=False, encoding="utf-8")
    print(f"\nGuardado en {perfil.salida.relative_to(RAIZ)}")


def main() -> None:
    pedidos = sys.argv[1:] or list(PERFILES)
    desconocidos = [p for p in pedidos if p not in PERFILES]
    if desconocidos:
        raise SystemExit(f"Perfil desconocido: {desconocidos}. Opciones: {list(PERFILES)}")

    for nombre in pedidos:
        perfil = PERFILES[nombre]
        informe(unificar(perfil), perfil)


if __name__ == "__main__":
    main()
