"""Parametros y tablas de base del modelo de 2028. Lo importan `modelar_flujos_banda.py` y el export.

Aqui estan los porcentajes que el proyecto da por buenos (una sola fuente: de aqui salen a la web
por `parametros.json`) y la carga de las dos tablas que se reparten: los pisos y los hoteles.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
GOLD = RAIZ / "data" / "gold"

# A cuanta distancia de su hotel cena un turista. 200 m deja una mediana de 44 locales por hotel
# y solo 5 hoteles sin ninguno; a 150 m son 7 hoteles y a 400 m la "cercania" deja de serlo.
RADIO_COMIDA_M = 200

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

# Ocupacion hotelera del INE **por habitaciones**, media de un ano. No por plazas: una habitacion
# doble vendida a una persona deja una plaza vacia que no se puede vender a nadie, asi que la
# habitacion es el limite real de un hotel.
OCUPACION_HOTEL_HAB = 0.802

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
    return vut, hoteles


def distancias(vut: pd.DataFrame, hoteles: pd.DataFrame) -> np.ndarray:
    """Kilometros entre cada piso y cada hotel."""
    return np.sqrt(((proyectar(vut["latitude"], vut["longitude"])[:, None, :]
                     - proyectar(hoteles["lat"], hoteles["lon"])[None, :, :]) ** 2).sum(axis=2))
