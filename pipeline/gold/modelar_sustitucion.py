"""Reparto de las plazas VUT entre el alojamiento reglado cuando la licencia desaparece en 2028.

El razonamiento y las comprobaciones estan en `pipeline/notebooks/modelar_sustitucion.ipynb`. Aqui
va solo lo que se ejecuta.

**El modelo.** Cada VUT que cierra busca alojamiento reglado. Cada hotel recibe una nota:

    utilidad = w x cercania + (1 - w) x parecido_de_precio

`w = 1` es un turista que solo quiere quedarse donde estaba; `w = 0`, uno que solo quiere pagar lo
mismo.

**`w` no se estima, y es deliberado.** Se probo estimarlo con la demanda actual de Airbnb y no
funciona: la distancia al centro no predice la demanda (p = 0,48) y el coeficiente del precio sale
positivo, que es causalidad inversa y no sensibilidad al precio. Ademas un turista aleman y uno
andaluz no tienen la misma sensibilidad, y ningun dato disponible los distingue. Se exportan varios
valores de `w` y la web deja elegir.

**Los hoteles no estan vacios.** Se descuenta la ocupacion real del INE, media de los ultimos doce
meses. Media anual y no mes a mes porque los precios del proyecto son equivalentes anuales: cruzar
precios anuales con ocupacion mensual mezclaria dos escalas de tiempo.

**El turno va de la VUT mas cara a la mas barata.** Hace falta un orden para que el reparto sea
determinista, y no es neutral: quien paga menos se queda sin sitio.

Entradas
    data/gold/airbnb_para_web.csv
    data/gold/alojamientos_reglados.csv
    data/bronze/serie_ine_barcelona.csv

Salidas
    data/gold/sustitucion_2028.csv          (barrio x escenario)
    data/gold/calidad/sustitucion_resumen.csv
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
GOLD = RAIZ / "data" / "gold"
BRONZE = RAIZ / "data" / "bronze"
SALIDA = GOLD / "sustitucion_2028.csv"
SALIDA_FLUJOS = GOLD / "sustitucion_flujos_2028.csv"
SALIDA_RESUMEN = GOLD / "calidad" / "sustitucion_resumen.csv"
SALIDA_RESTAURACION = GOLD / "restauracion_presion_2028.csv"

# A cuanta distancia de su hotel cena un turista. 200 m deja una mediana de 44 locales por hotel
# y solo 5 hoteles sin ninguno; a 150 m son 7 hoteles y a 400 m la "cercania" deja de serlo.
RADIO_COMIDA_M = 200

# Un flujo de dos o tres turistas entre dos barrios no dice nada y llena el mapa de rayas. El
# corte deja fuera el ruido sin perder ningun movimiento que se vea a simple vista.
MINIMO_FLUJO = 20

# Los valores que se precalculan. La web no puede resolver 5,2 millones de pares en el navegador,
# asi que la barra se mueve entre estos cinco pasos.
PESOS = {0.0: "solo_precio", 0.25: "sobre_todo_precio", 0.5: "equilibrio",
         0.75: "sobre_todo_barrio", 1.0: "solo_barrio"}

# Ocupacion media de los anuncios de Airbnb, ponderada por capacidad. **No es un dato oficial: no
# existe.** Se estima por dos vias independientes que convergen, y por eso se publica:
#
#   calendario  (365 - availability_365) / 365        -> 38,3%
#   resenas     resenas_12m / 0,50 x 3 noches / 365   -> 38,8%   (metodo de Inside Airbnb)
#
# Con estancias de 4 noches la segunda via sube al 48,6%, asi que la horquilla honesta es 38-48%.
# Se toma el extremo bajo porque es el que coincide con la via del calendario, que no depende de
# suponer ni tasa de resena ni duracion.
OCUPACION_AIRBNB = 0.383

# Los dos momentos que se publican. La ocupacion hotelera es la del INE **por habitaciones**, no
# por plazas: una habitacion doble vendida a una persona deja una plaza vacia que no se puede
# vender a nadie, asi que la habitacion es el limite real de un hotel.
#
# Julio no es un adorno: es el unico mes en el que la cuenta no sale, y publicarlo solo en media
# anual escondia justo el problema.
MOMENTOS = {
    "anio_medio": {"etiqueta": "Un ano medio", "ocupacion_hotel": 0.802, "factor_airbnb": 1.0},
    "julio": {"etiqueta": "Julio, la punta", "ocupacion_hotel": 0.865, "factor_airbnb": 1.165},
}

# Plazas por dormitorio donde Airbnb no lo declara (2,8% de los anuncios). Es la mediana observada
# en los que si lo declaran, y coincide con la ratio de nuestros hoteles (1,88 plazas/habitacion):
# por eso las dos unidades se pueden comparar sin corregir nada.
PLAZAS_POR_DORMITORIO = 2.0

LAT0 = 41.39


def proyectar(lat, lon) -> np.ndarray:
    """Grados a kilometros. A 41,39 N un grado de longitud mide 83 km y uno de latitud 111."""
    return np.c_[np.asarray(lon, float) * 111.320 * np.cos(np.radians(LAT0)),
                 np.asarray(lat, float) * 110.570]


def cargar() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Las dos tablas, ya con la habitacion como unidad.

    **Por que la habitacion y no la plaza.** Comparar plazas declaradas de VUT con plazas libres de
    hotel mezclaba dos cosas: una plaza libre de hotel suele ser la segunda cama de una habitacion
    ya vendida, que no se puede vender por separado. Un grupo de cuatro no cabe en una habitacion
    doble por mucho que el hotel tenga cuatro plazas sueltas repartidas.
    """
    vut = pd.read_csv(GOLD / "airbnb_para_web.csv", low_memory=False)
    hoteles = pd.read_csv(GOLD / "alojamientos_reglados.csv", low_memory=False)
    hoteles = hoteles[hoteles["banda_plaza"].notna() & hoteles["lat"].notna()
                      & hoteles["habitaciones"].notna()].reset_index(drop=True)

    dormitorios = pd.to_numeric(vut["bedrooms"], errors="coerce")
    plazas = pd.to_numeric(vut["accommodates"], errors="coerce")
    # Un estudio declara 0 dormitorios y sigue alojando gente: cuenta como uno.
    vut["dormitorios"] = dormitorios.where(dormitorios > 0).fillna(
        (plazas / PLAZAS_POR_DORMITORIO).round()).clip(lower=1)

    vut["precio"] = vut["precio_plaza_anual"]
    hoteles["precio"] = hoteles["precio_plaza"]
    return vut, hoteles


def matrices(vut: pd.DataFrame, hoteles: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    distancia = np.sqrt(((proyectar(vut["latitude"], vut["longitude"])[:, None, :]
                          - proyectar(hoteles["lat"], hoteles["lon"])[None, :, :]) ** 2).sum(axis=2))
    brecha = np.abs(vut["precio"].to_numpy()[:, None] - hoteles["precio"].to_numpy()[None, :])
    # Las dos magnitudes van a 0-1 para poder mezclarlas. 1 es el mejor hotel posible.
    return distancia, 1 - distancia / distancia.max(), 1 - brecha / brecha.max()


def repartir(vut, hoteles, distancia, cercania, parecido, w, capacidad) -> pd.DataFrame:
    """Las VUT eligen por turnos, de mas cara a mas barata, hasta agotar las habitaciones libres.

    Lo que se reparte son **habitaciones por noche**, descontada la ocupacion de los dos lados: una
    vivienda ocupada el 38% de las noches pide sus dormitorios el 38% de las noches, y un hotel al
    80% solo ofrece el 20% de las suyas. Antes se descontaba la ocupacion al hotel y no a la
    vivienda, que es lo que hacia salir una escasez que el dato no sostiene.
    """
    orden_hoteles = np.argsort(-(w * cercania + (1 - w) * parecido), axis=1)
    turno = np.argsort(-vut["precio"].to_numpy())
    libre = capacidad.astype(float).copy()
    precio_hotel = hoteles["precio"].to_numpy()

    filas = []
    for i in turno:
        pendientes = float(vut["demanda"].iloc[i])
        for j in orden_hoteles[i]:
            if pendientes <= 0:
                break
            if libre[j] <= 0:
                continue
            cabe = min(pendientes, libre[j])
            libre[j] -= cabe
            pendientes -= cabe
            filas.append({"vut_idx": i, "hotel_idx": j, "habitaciones": cabe,
                          "km": distancia[i, j],
                          "salto_precio": precio_hotel[j] - vut["precio"].iloc[i]})
        if pendientes > 0:
            filas.append({"vut_idx": i, "hotel_idx": -1, "habitaciones": pendientes,
                          "km": np.nan, "salto_precio": np.nan})
    return pd.DataFrame(filas)


def agregar_por_barrio(asignacion, vut, hoteles) -> pd.DataFrame:
    """Un barrio aparece como origen y como destino, y son dos cosas distintas.

    Se reparten habitaciones, pero se publican **turistas**: una habitacion no le dice nada a quien
    lee el mapa. Las dos cifras viajan juntas porque la que manda es la habitacion —es el limite
    que hace que alguien se quede sin sitio— y la que se entiende es la persona.
    """
    a = asignacion.copy()
    a["barrio_origen"] = vut["neighbourhood"].to_numpy()[a["vut_idx"].to_numpy()]
    a["turistas"] = a["habitaciones"] * vut["por_habitacion"].to_numpy()[a["vut_idx"].to_numpy()]
    colocadas = a[a["hotel_idx"] >= 0].copy()
    colocadas["barrio_destino"] = hoteles["barrio"].to_numpy()[colocadas["hotel_idx"].to_numpy()]

    salen = a.groupby("barrio_origen")["turistas"].sum().rename("turistas_que_salen")
    llegan = colocadas.groupby("barrio_destino")["turistas"].sum().rename("turistas_que_llegan")
    sin_sitio = (a[a["hotel_idx"] < 0].groupby("barrio_origen")["turistas"].sum()
                 .rename("turistas_sin_sitio"))
    se_quedan = (colocadas[colocadas["barrio_origen"] == colocadas["barrio_destino"]]
                 .groupby("barrio_origen")["turistas"].sum().rename("turistas_que_se_quedan"))
    habitaciones = colocadas.groupby("barrio_destino")["habitaciones"].sum().rename("habitaciones_ocupadas")
    recorrido = colocadas.groupby("barrio_origen")["km"].median().rename("km_mediano")
    sobrecoste = colocadas.groupby("barrio_origen")["salto_precio"].median().rename("sobrecoste_mediano")

    columnas = ["turistas_que_salen", "turistas_que_llegan", "turistas_sin_sitio",
                "turistas_que_se_quedan", "habitaciones_ocupadas"]
    barrios = pd.concat([salen, llegan, sin_sitio, se_quedan, habitaciones, recorrido, sobrecoste],
                        axis=1)
    barrios[columnas] = barrios[columnas].fillna(0)
    barrios["saldo"] = barrios["turistas_que_llegan"] - barrios["turistas_que_salen"]
    return barrios.round(2)


def agregar_flujos(asignacion, vut, hoteles) -> pd.DataFrame:
    """Movimientos barrio de origen -> barrio de destino, para dibujar las flechas.

    Se excluye el flujo de un barrio a si mismo: el mapa cuenta quien SE MUEVE, y una flecha que
    sale y entra en el mismo sitio no es un movimiento. Ese dato ya esta en
    `turistas_que_se_quedan`.
    """
    a = asignacion[asignacion["hotel_idx"] >= 0].copy()
    a["origen"] = vut["neighbourhood"].to_numpy()[a["vut_idx"].to_numpy()]
    a["destino"] = hoteles["barrio"].to_numpy()[a["hotel_idx"].to_numpy()]
    a["turistas"] = a["habitaciones"] * vut["por_habitacion"].to_numpy()[a["vut_idx"].to_numpy()]
    a = a[a["origen"] != a["destino"]]

    flujos = (a.groupby(["origen", "destino"])
              .agg(turistas=("turistas", "sum"), km_mediano=("km", "median"))
              .reset_index())
    return flujos[flujos["turistas"] >= MINIMO_FLUJO].round(2)


def cargar_restauracion() -> pd.DataFrame:
    r = pd.read_csv(GOLD / "restauracion_bcn.csv", low_memory=False)
    return r[r["latitud"].notna() & r["longitud"].notna()].reset_index(drop=True)


def vecindad(lat, lon, locales: pd.DataFrame) -> np.ndarray:
    """Matriz hotel x local: que parte de un turista de ese hotel le toca a cada local.

    **El turista cena cerca de donde duerme.** No es una afirmacion sobre el turismo en general
    —quien se aloja en Sants va a las Ramblas y eso pasa mucho— sino sobre las comidas ordinarias:
    el desayuno, la cena al volver. Nadie cruza la ciudad tres veces al dia para comer.

    **El reparto es a partes iguales entre los locales del radio.** Es lo unico que el dato
    sostiene: no sabemos que bar prefiere nadie, y ponderar por distancia dentro de 200 m seria
    inventar una preferencia con dos decimales de precision falsa. Cada turista reparte un punto
    entre los locales que tiene a mano.

    Los 5 hoteles sin ningun local a 200 m van al mas cercano, sea cual sea la distancia: dejarlos
    fuera diria que sus turistas no cenan.
    """
    H = proyectar(lat, lon)
    L = proyectar(locales["latitud"], locales["longitud"])
    metros = np.sqrt(((H[:, None, :] - L[None, :, :]) ** 2).sum(axis=2)) * 1000

    dentro = (metros <= RADIO_COMIDA_M).astype(float)
    huerfanos = dentro.sum(axis=1) == 0
    if huerfanos.any():
        dentro[huerfanos, metros[huerfanos].argmin(axis=1)] = 1.0
    return dentro / dentro.sum(axis=1, keepdims=True)


def agregar_restauracion(asignacion, vut, hoteles, locales, reparto_hotel, reparto_vut):
    """Donde cenan hoy estos turistas y donde cenarian en 2028, por barrio del local.

    El barrio que cuenta es el **del local**, no el del alojamiento: un hotel pegado al limite
    alimenta bares del barrio de al lado, y esa fuga es justo lo que un agregado por barrio del
    hotel no ensena.

    **No depende del escenario, y eso es un resultado, no un descuido.** La demanda (30.067 plazas)
    supera a la oferta libre (27.008), asi que los 757 hoteles se llenan en los cinco escenarios:
    da igual si el turista prefiere precio o barrio, el reparto sobre los hoteles es el mismo y el
    que cae sobre los bares tambien. La barra de la web mueve quien va a que hotel, no cuantos
    hoteles se llenan. Solo variaria con una ocupacion de partida mas baja —en noviembre, al 55,6%,
    sobrarian plazas— y ahi si decidiria la preferencia del turista.
    """
    por_hotel = np.zeros(len(hoteles))
    colocadas = asignacion[asignacion["hotel_idx"] >= 0]
    # Turistas, no habitaciones: quien cena es la persona.
    turistas = (colocadas["habitaciones"].to_numpy()
                * vut["por_habitacion"].to_numpy()[colocadas["vut_idx"].to_numpy()])
    np.add.at(por_hotel, colocadas["hotel_idx"].to_numpy(), turistas)

    # El "hoy" se mide con la misma ocupacion que el 2028: comparar una ocupacion real con una
    # capacidad declarada es justo el error que este cambio corrige.
    hoy = (vut["accommodates"] * vut["ocupacion"]).to_numpy()
    d = pd.DataFrame({
        "barrio": locales["barrio"],
        "en_2028": por_hotel @ reparto_hotel,
        "hoy": hoy @ reparto_vut,
    })
    a = d.groupby("barrio").agg(locales=("hoy", "size"), hoy=("hoy", "sum"),
                                en_2028=("en_2028", "sum")).reset_index()
    a["cambio"] = a["en_2028"] - a["hoy"]
    a["por_local_hoy"] = a["hoy"] / a["locales"]
    a["por_local_2028"] = a["en_2028"] / a["locales"]
    return a.round(2)


def main() -> None:
    vut, hoteles = cargar()
    distancia, cercania, parecido = matrices(vut, hoteles)
    locales = cargar_restauracion()
    reparto_hotel = vecindad(hoteles["lat"], hoteles["lon"], locales)
    reparto_vut = vecindad(vut["latitude"], vut["longitude"], locales)

    habitaciones_hotel = float(hoteles["habitaciones"].sum())
    vut["por_habitacion"] = vut["accommodates"] / vut["dormitorios"]

    bloques, bloques_flujo, bloques_rest, resumen = [], [], [], []
    for clave, momento in MOMENTOS.items():
        ocupacion = momento["ocupacion_hotel"]
        ocupacion_vut = min(OCUPACION_AIRBNB * momento["factor_airbnb"], 1.0)
        # Lo que de verdad hay que realojar esa noche, y lo que de verdad hay libre esa noche.
        vut["ocupacion"] = ocupacion_vut
        vut["demanda"] = vut["dormitorios"] * ocupacion_vut
        capacidad = (hoteles["habitaciones"] * (1 - ocupacion)).to_numpy()
        turistas = float((vut["demanda"] * vut["por_habitacion"]).sum())

        print(f"{momento['etiqueta']}  (hotel {ocupacion:.1%} por habitacion, "
              f"Airbnb {ocupacion_vut:.1%})")
        print(f"  habitaciones de hotel  {habitaciones_hotel:>9,.0f}")
        print(f"  libres una noche       {capacidad.sum():>9,.0f}")
        print(f"  habitaciones que piden {vut['demanda'].sum():>9,.0f}  ({turistas:,.0f} turistas)")

        for w, etiqueta in PESOS.items():
            asignacion = repartir(vut, hoteles, distancia, cercania, parecido, w, capacidad)

            barrios = agregar_por_barrio(asignacion, vut, hoteles)
            barrios.insert(0, "momento", clave)
            barrios.insert(1, "escenario", etiqueta)
            barrios.insert(2, "w", w)
            bloques.append(barrios.reset_index().rename(columns={"index": "barrio"}))

            flujos = agregar_flujos(asignacion, vut, hoteles)
            flujos.insert(0, "momento", clave)
            flujos.insert(1, "escenario", etiqueta)
            bloques_flujo.append(flujos)

            # La restauracion se calcula una vez por momento: dentro de un momento no depende del
            # escenario cuando los hoteles se saturan, y cuando no se saturan si — pero el reparto
            # sobre los bares lo hace el hotel, no la preferencia, asi que basta el equilibrio.
            if w == 0.5:
                rest = agregar_restauracion(asignacion, vut, hoteles, locales,
                                            reparto_hotel, reparto_vut)
                rest.insert(0, "momento", clave)
                bloques_rest.append(rest)

            colocadas = asignacion[asignacion["hotel_idx"] >= 0]
            fuera = asignacion[asignacion["hotel_idx"] < 0]
            por_hab = vut["por_habitacion"].to_numpy()
            sin_sitio = float((fuera["habitaciones"] * por_hab[fuera["vut_idx"].to_numpy()]).sum())
            resumen.append({
                "momento": clave, "etiqueta": momento["etiqueta"], "escenario": etiqueta, "w": w,
                "turistas_colocados": int((colocadas["habitaciones"]
                                           * por_hab[colocadas["vut_idx"].to_numpy()]).sum()),
                "turistas_sin_sitio": int(round(sin_sitio)),
                "habitaciones_sin_sitio": int(round(float(fuera["habitaciones"].sum()))),
                "km_mediano": round(float(colocadas["km"].median()), 2),
                "sobrecoste_mediano": round(float(colocadas["salto_precio"].median()), 1),
                "hoteles_usados": int(colocadas["hotel_idx"].nunique()),
                "ocupacion_hotel": ocupacion,
                "ocupacion_airbnb": round(ocupacion_vut, 4),
                "habitaciones_hotel": int(habitaciones_hotel),
                "habitaciones_libres": int(round(float(capacidad.sum()))),
                "turistas_a_realojar": int(round(turistas)),
            })
            print(f"    {etiqueta:<20} sin sitio {sin_sitio:>7,.0f} turistas   "
                  f"{resumen[-1]['km_mediano']:>5.2f} km")
        print()

    salida = pd.concat(bloques, ignore_index=True)
    salida.to_csv(SALIDA, index=False, encoding="utf-8")
    flujos = pd.concat(bloques_flujo, ignore_index=True)
    flujos.to_csv(SALIDA_FLUJOS, index=False, encoding="utf-8")
    restauracion = pd.concat(bloques_rest, ignore_index=True)
    restauracion.to_csv(SALIDA_RESTAURACION, index=False, encoding="utf-8")

    SALIDA_RESUMEN.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(resumen).to_csv(SALIDA_RESUMEN, index=False, encoding="utf-8")

    print(f"Guardado en {SALIDA.relative_to(RAIZ)}  ({len(salida):,} filas: "
          f"{salida['barrio'].nunique()} barrios x {len(PESOS)} escenarios x {len(MOMENTOS)} momentos)")
    print(f"Guardado en {SALIDA_FLUJOS.relative_to(RAIZ)}  ({len(flujos):,} flujos)")
    print(f"Guardado en {SALIDA_RESTAURACION.relative_to(RAIZ)}  ({len(restauracion):,} filas)")
    print(f"Guardado en {SALIDA_RESUMEN.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
