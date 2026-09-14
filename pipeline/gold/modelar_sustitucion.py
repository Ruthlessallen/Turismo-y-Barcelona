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
SALIDA_RESUMEN = GOLD / "calidad" / "sustitucion_resumen.csv"

# Los valores que se precalculan. La web no puede resolver 5,2 millones de pares en el navegador,
# asi que la barra se mueve entre estos cinco pasos.
PESOS = {0.0: "solo_precio", 0.25: "sobre_todo_precio", 0.5: "equilibrio",
         0.75: "sobre_todo_barrio", 1.0: "solo_barrio"}

LAT0 = 41.39


def proyectar(lat, lon) -> np.ndarray:
    """Grados a kilometros. A 41,39 N un grado de longitud mide 83 km y uno de latitud 111."""
    return np.c_[np.asarray(lon, float) * 111.320 * np.cos(np.radians(LAT0)),
                 np.asarray(lat, float) * 110.570]


def cargar() -> tuple[pd.DataFrame, pd.DataFrame, float]:
    vut = pd.read_csv(GOLD / "airbnb_para_web.csv", low_memory=False)
    hoteles = pd.read_csv(GOLD / "alojamientos_reglados.csv", low_memory=False)
    hoteles = hoteles[hoteles["banda_plaza"].notna() & hoteles["lat"].notna()].reset_index(drop=True)

    serie = pd.read_csv(BRONZE / "serie_ine_barcelona.csv", low_memory=False)
    ocupacion = serie[serie["serie"].str.contains("Grado de ocupaci", na=False)
                      & serie["serie"].str.contains("por plazas. B", na=False)]
    media = float(ocupacion.sort_values("mes").tail(12)["valor"].mean()) / 100

    vut["precio"] = vut["precio_plaza_anual"]
    hoteles["precio"] = hoteles["precio_plaza"]
    return vut, hoteles, media


def matrices(vut: pd.DataFrame, hoteles: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    distancia = np.sqrt(((proyectar(vut["latitude"], vut["longitude"])[:, None, :]
                          - proyectar(hoteles["lat"], hoteles["lon"])[None, :, :]) ** 2).sum(axis=2))
    brecha = np.abs(vut["precio"].to_numpy()[:, None] - hoteles["precio"].to_numpy()[None, :])
    # Las dos magnitudes van a 0-1 para poder mezclarlas. 1 es el mejor hotel posible.
    return distancia, 1 - distancia / distancia.max(), 1 - brecha / brecha.max()


def repartir(vut, hoteles, distancia, cercania, parecido, w, capacidad) -> pd.DataFrame:
    """Las VUT eligen por turnos, de mas cara a mas barata, hasta agotar el aforo."""
    orden_hoteles = np.argsort(-(w * cercania + (1 - w) * parecido), axis=1)
    turno = np.argsort(-vut["precio"].to_numpy())
    libre = capacidad.astype(float).copy()
    precio_hotel = hoteles["precio"].to_numpy()

    filas = []
    for i in turno:
        pendientes = float(vut["accommodates"].iloc[i])
        for j in orden_hoteles[i]:
            if pendientes <= 0:
                break
            if libre[j] <= 0:
                continue
            cabe = min(pendientes, libre[j])
            libre[j] -= cabe
            pendientes -= cabe
            filas.append({"vut_idx": i, "hotel_idx": j, "plazas": cabe,
                          "km": distancia[i, j],
                          "salto_precio": precio_hotel[j] - vut["precio"].iloc[i]})
        if pendientes > 0:
            filas.append({"vut_idx": i, "hotel_idx": -1, "plazas": pendientes,
                          "km": np.nan, "salto_precio": np.nan})
    return pd.DataFrame(filas)


def agregar_por_barrio(asignacion, vut, hoteles) -> pd.DataFrame:
    """Un barrio aparece como origen y como destino, y son dos cosas distintas."""
    a = asignacion.copy()
    a["barrio_origen"] = vut["neighbourhood"].to_numpy()[a["vut_idx"].to_numpy()]
    colocadas = a[a["hotel_idx"] >= 0].copy()
    colocadas["barrio_destino"] = hoteles["barrio"].to_numpy()[colocadas["hotel_idx"].to_numpy()]

    salen = a.groupby("barrio_origen")["plazas"].sum().rename("plazas_que_salen")
    llegan = colocadas.groupby("barrio_destino")["plazas"].sum().rename("plazas_que_llegan")
    sin_sitio = (a[a["hotel_idx"] < 0].groupby("barrio_origen")["plazas"].sum()
                 .rename("plazas_sin_sitio"))
    se_quedan = (colocadas[colocadas["barrio_origen"] == colocadas["barrio_destino"]]
                 .groupby("barrio_origen")["plazas"].sum().rename("plazas_que_se_quedan"))
    recorrido = colocadas.groupby("barrio_origen")["km"].median().rename("km_mediano")
    sobrecoste = colocadas.groupby("barrio_origen")["salto_precio"].median().rename("sobrecoste_mediano")

    barrios = pd.concat([salen, llegan, sin_sitio, se_quedan, recorrido, sobrecoste], axis=1)
    barrios[["plazas_que_salen", "plazas_que_llegan", "plazas_sin_sitio",
             "plazas_que_se_quedan"]] = barrios[["plazas_que_salen", "plazas_que_llegan",
                                                 "plazas_sin_sitio", "plazas_que_se_quedan"]].fillna(0)
    barrios["saldo"] = barrios["plazas_que_llegan"] - barrios["plazas_que_salen"]
    return barrios.round(2)


def main() -> None:
    vut, hoteles, ocupacion = cargar()
    distancia, cercania, parecido = matrices(vut, hoteles)

    plazas_totales = float(hoteles["plazas"].sum())
    necesarias = float(vut["accommodates"].sum())
    capacidad = (hoteles["plazas"] * (1 - ocupacion)).to_numpy()

    print(f"Ocupacion hotelera (INE, media 12 meses): {ocupacion:.1%}")
    print(f"  plazas regladas {plazas_totales:>9,.0f}")
    print(f"  libres          {capacidad.sum():>9,.0f}")
    print(f"  plazas VUT      {necesarias:>9,.0f}")
    print()

    bloques, resumen = [], []
    for w, etiqueta in PESOS.items():
        asignacion = repartir(vut, hoteles, distancia, cercania, parecido, w, capacidad)
        barrios = agregar_por_barrio(asignacion, vut, hoteles)
        barrios.insert(0, "escenario", etiqueta)
        barrios.insert(1, "w", w)
        bloques.append(barrios.reset_index().rename(columns={"index": "barrio"}))

        colocadas = asignacion[asignacion["hotel_idx"] >= 0]
        sin_sitio = float(asignacion.loc[asignacion["hotel_idx"] < 0, "plazas"].sum())
        resumen.append({
            "escenario": etiqueta, "w": w,
            "plazas_colocadas": int(colocadas["plazas"].sum()),
            "plazas_sin_sitio": int(round(sin_sitio)),
            "km_mediano": round(float(colocadas["km"].median()), 2),
            "sobrecoste_mediano": round(float(colocadas["salto_precio"].median()), 1),
            "hoteles_usados": int(colocadas["hotel_idx"].nunique()),
        })
        print(f"  {etiqueta:<20} sin sitio {sin_sitio:>7,.0f}   "
              f"{resumen[-1]['km_mediano']:>5.2f} km   "
              f"{resumen[-1]['sobrecoste_mediano']:>6.1f} EUR/plaza")

    salida = pd.concat(bloques, ignore_index=True)
    salida.to_csv(SALIDA, index=False, encoding="utf-8")

    tabla_resumen = pd.DataFrame(resumen)
    tabla_resumen["ocupacion_partida"] = round(ocupacion, 4)
    tabla_resumen["plazas_regladas"] = int(plazas_totales)
    tabla_resumen["plazas_vut"] = int(necesarias)
    SALIDA_RESUMEN.parent.mkdir(parents=True, exist_ok=True)
    tabla_resumen.to_csv(SALIDA_RESUMEN, index=False, encoding="utf-8")

    print()
    print(f"Guardado en {SALIDA.relative_to(RAIZ)}  "
          f"({len(salida):,} filas: {salida['barrio'].nunique()} barrios x {len(PESOS)} escenarios)")
    print(f"Guardado en {SALIDA_RESUMEN.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
