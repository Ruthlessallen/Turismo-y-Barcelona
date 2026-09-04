"""Definicion unica de las bandas economicas. La importan hoteles y Airbnb.

Hay **dos bandas distintas** y confundirlas invalida cualquier comparacion:

`banda_precio` — por habitacion y noche, cortes en 100 / 175 / 300 EUR
    Lo que paga quien reserva una habitacion de hotel. Es la magnitud que publica la estadistica
    oficial (el ADR del INE es ingreso por habitacion ocupada) y contra la que se valido el
    raspado. Solo tiene sentido para alojamiento reglado.

`banda_plaza` — por plaza y noche, cortes en 40 / 70 / 120 EUR
    Lo que cuesta alojar a **una persona**. Es la unica escala en la que un piso entero para cuatro
    y una habitacion doble de hotel son comparables: 221 EUR y 64 EUR no dicen nada enfrentados,
    54 EUR y 43 EUR por plaza si.

**Por que 40/70/120 y no cuartiles.** Los cuartiles de cada mercado caen en sitios distintos —el
hotel mediano esta en 81 EUR/plaza y el anuncio mediano de Airbnb en 43— asi que unos cuartiles
comunes partirian el mercado barato por la mitad y dejarian el hotelero entero en la banda alta.
Con estos cortes, los hoteles se reparten 2/29/52/17 por ciento y los anuncios 45/36/15/3: cada
mercado ocupa varias bandas y la comparacion enseña algo.

**Que es "por plaza" exactamente.** Precio dividido entre la capacidad declarada, no entre los
ocupantes reales. Una pareja en un piso para cuatro paga el piso entero, igual que en un hotel
paga la habitacion. Es precio por plaza **disponible**, y se aplica igual a los dos lados, que es
lo que hace la comparacion valida.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

CORTES_HABITACION = [100, 175, 300]
CORTES_PLAZA = [40, 70, 120]
ETIQUETAS = ["€", "€€", "€€€", "€€€€"]


def asignar(precio: pd.Series, cortes: list[int]) -> pd.Series:
    """Etiqueta de banda, nula donde no hay precio.

    `np.digitize` no distingue el nulo, lo mete en la primera banda: un alojamiento sin precio
    saldria como el mas barato de la ciudad. Por eso la mascara va aparte.
    """
    numerico = pd.to_numeric(precio, errors="coerce")
    indices = np.digitize(numerico.fillna(-1), cortes)
    etiquetas = pd.Series(np.take(ETIQUETAS, indices), index=precio.index, dtype=object)
    return etiquetas.where(numerico.notna())


def por_habitacion(precio_noche: pd.Series) -> pd.Series:
    return asignar(precio_noche, CORTES_HABITACION)


def por_plaza(precio_plaza: pd.Series) -> pd.Series:
    return asignar(precio_plaza, CORTES_PLAZA)


def precio_por_plaza_hotel(precio_noche: pd.Series, plazas: pd.Series,
                           habitaciones: pd.Series) -> pd.Series:
    """Lleva el precio de hotel de habitacion a plaza.

    El divisor es plazas por habitacion, no plazas: el precio raspado es de **una** habitacion, no
    del hotel entero. La mediana del parque son 1,9 plazas por habitacion, coherente con que casi
    todo el inventario sean dobles.
    """
    por_habitacion_ = pd.to_numeric(plazas, errors="coerce") / pd.to_numeric(
        habitaciones, errors="coerce")
    por_habitacion_ = por_habitacion_.where(por_habitacion_ > 0)
    return (pd.to_numeric(precio_noche, errors="coerce") / por_habitacion_).round(2)
