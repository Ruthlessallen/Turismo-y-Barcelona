"""Adonde van los turistas cuando desaparecen los pisos: cada uno elige hotel por su banda.

Es el reparto que usa la web desde el 2026-10-05 (`export/export_mapa_limpio.py` llama a `asignar`).
Sustituye al reparto por cercania y parecido de precio de `modelar_sustitucion.py`, que sigue
alimentando solo a `/mapa-anterior`. Ejecutado a mano, imprime la comparacion de variantes.

La regla, tal como se plantea:
  1. El turista va a un hotel de **su banda**, el mas cercano con habitaciones libres.
  2. Si en su banda no queda sitio, va a la **siguiente banda mas cara**, el mas cercano. Y asi hasta
     la mas cara. Solo despues, y como ultimo recurso, baja a una mas barata.
  3. La distancia no limita: si el unico hotel libre de su banda esta al otro lado de la ciudad,
     va. La variante B, para comparar, prefiere dentro de 1 km antes de cambiar de banda.

La banda es la **por plaza** (40/70/120 EUR) en los dos lados: es la unica escala en la que un piso
entero y una habitacion de hotel se pueden comparar.

Un ano medio: ocupacion del hotel 80,2 % por habitaciones, de los pisos 38,3 %. Lo que se reparte
son habitaciones; se cuentan turistas al final. Los pisos eligen en orden aleatorio (semilla fija):
el orden decide quien se queda con las habitaciones escasas de una banda, no cuantos caben.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

import modelar_sustitucion as m

SALIDA = m.GOLD / "calidad" / "flujos_banda_resumen.csv"
BANDAS = ["€", "€€", "€€€", "€€€€"]
TOPE_KM = 1.0
SEMILLAS = [0, 1, 2]


def claves(dist: np.ndarray, delta: np.ndarray, tope: float | None) -> np.ndarray:
    """Orden de preferencia de cada piso sobre cada hotel: menor clave, antes se elige."""
    paso = np.where(delta >= 0, delta, 3 + (-delta))  # misma, +1, +2, +3, y luego -1, -2, -3
    clave = paso * 1000.0 + dist
    if tope is not None:
        clave = clave + (dist > tope) * 10000.0
    return clave


def repartir(vut, hot, dist, delta, tope, semilla) -> pd.DataFrame:
    orden_hoteles = np.argsort(claves(dist, delta, tope), axis=1)
    libre = np.array(hot["habitaciones"] * (1 - m.MOMENTOS["anio_medio"]["ocupacion_hotel"]), dtype=float)
    demanda = (vut["dormitorios"] * m.OCUPACION_AIRBNB).to_numpy()
    filas = []
    for i in np.random.default_rng(semilla).permutation(len(vut)):
        pendiente = demanda[i]
        for j in orden_hoteles[i]:
            if pendiente <= 0:
                break
            if libre[j] <= 0:
                continue
            cabe = min(pendiente, libre[j])
            libre[j] -= cabe
            pendiente -= cabe
            filas.append((i, j, cabe))
        if pendiente > 0:
            filas.append((i, -1, pendiente))
    return pd.DataFrame(filas, columns=["vut_idx", "hotel_idx", "habitaciones"])


def asignar(semilla: int = 0, tope: float | None = None):
    """El reparto de un ano medio. Devuelve (asignacion, vut, hotel, km, banda_vut, banda_hotel).

    `asignacion` tiene una fila por pareja piso-hotel: `vut_idx`, `hotel_idx` (-1 si no cabe) y las
    `habitaciones` por noche que ese piso coloca en ese hotel.
    """
    vut, hot = m.cargar()
    vut = vut[vut["banda_plaza"].notna()].reset_index(drop=True)
    dist, _, _ = m.matrices(vut, hot)
    idx = {b: i for i, b in enumerate(BANDAS)}
    bv = vut["banda_plaza"].map(idx).to_numpy()
    bh = hot["banda_plaza"].map(idx).to_numpy()
    delta = bh[None, :] - bv[:, None]
    return repartir(vut, hot, dist, delta, tope, semilla), vut, hot, dist, bv, bh


def resumen(nombre, a, vut, hot, dist, bv, bh) -> dict:
    por_hab = (vut["accommodates"] / vut["dormitorios"]).to_numpy()
    col = a[a["hotel_idx"] >= 0].copy()
    col["tur"] = col["habitaciones"] * por_hab[col["vut_idx"]]
    col["km"] = dist[col["vut_idx"], col["hotel_idx"]]
    col["salto"] = bh[col["hotel_idx"]] - bv[col["vut_idx"]]
    col["b_orig"] = bv[col["vut_idx"]]
    col["b_dest"] = bh[col["hotel_idx"]]
    w = col["tur"].to_numpy()

    def pct(mask):
        return float(w[mask].sum() / w.sum() * 100)

    def cuantil(q):  # ponderado por turistas
        o = np.argsort(col["km"].to_numpy())
        c = np.cumsum(w[o]) / w.sum()
        return float(col["km"].to_numpy()[o][np.searchsorted(c, q)])

    fuera = a[a["hotel_idx"] < 0]
    sin_sitio = float((fuera["habitaciones"] * por_hab[fuera["vut_idx"]]).sum())
    salto = col["salto"].to_numpy()
    print(f"\n{nombre}")
    print(f"  turistas colocados {w.sum():>8,.0f}   sin sitio {sin_sitio:,.0f}")
    print(f"  su banda {pct(salto == 0):5.1f} %   una mas cara {pct(salto == 1):5.1f} %   "
          f"dos o tres mas {pct(salto >= 2):5.1f} %   mas barata {pct(salto < 0):5.1f} %")
    print(f"  km: mediana {cuantil(.5):.2f}   p90 {cuantil(.9):.2f}   max {col['km'].max():.1f}   "
          f"mas de 2 km: {pct(col['km'].to_numpy() > 2):.1f} %   hoteles usados {col['hotel_idx'].nunique()}")
    mat = (col.groupby(["b_orig", "b_dest"])["tur"].sum().unstack(fill_value=0)
           .reindex(index=range(4), columns=range(4), fill_value=0))
    mat.index = [f"sale de {b}" for b in BANDAS]
    mat.columns = [f"va a {b}" for b in BANDAS]
    print(mat.round(0).astype(int).to_string())
    largo = mat.stack().rename("turistas").reset_index()
    largo.columns = ["origen", "destino", "turistas"]
    largo.insert(0, "variante", nombre)
    return {"mediana": cuantil(.5), "p90": cuantil(.9), "su_banda": pct(salto == 0), "tabla": largo}


def main() -> None:
    vut, hot = m.cargar()
    vut = vut[vut["banda_plaza"].notna()].reset_index(drop=True)
    dist, _, _ = m.matrices(vut, hot)
    bv = vut["banda_plaza"].map({b: i for i, b in enumerate(BANDAS)}).to_numpy()
    bh = hot["banda_plaza"].map({b: i for i, b in enumerate(BANDAS)}).to_numpy()
    delta = bh[None, :] - bv[:, None]

    print("OFERTA Y DEMANDA POR BANDA (habitaciones por noche, un ano medio)")
    libre = (hot["habitaciones"] * (1 - m.MOMENTOS["anio_medio"]["ocupacion_hotel"])).to_numpy()
    demanda = (vut["dormitorios"] * m.OCUPACION_AIRBNB).to_numpy()
    for i, b in enumerate(BANDAS):
        print(f"  {b:<5} hoteles libres {libre[bh == i].sum():>7,.0f}   pisos piden {demanda[bv == i].sum():>7,.0f}")

    tablas = []
    for nombre, tope in (("A. banda primero, sin limite de distancia", None),
                         (f"B. banda primero, antes dentro de {TOPE_KM:.0f} km", TOPE_KM)):
        res = []
        for s in SEMILLAS:
            a = repartir(vut, hot, dist, delta, tope, s)
            res.append(resumen(f"{nombre} (semilla {s})" if s else nombre, a, vut, hot, dist, bv, bh))
        tablas.append(res[0]["tabla"])
        print(f"  -> con 3 ordenes distintos: mediana {min(r['mediana'] for r in res):.2f}-"
              f"{max(r['mediana'] for r in res):.2f} km, su banda "
              f"{min(r['su_banda'] for r in res):.0f}-{max(r['su_banda'] for r in res):.0f} %")

    # Referencia: el modelo actual (precio y cercania al 50 %), mismos datos.
    _, cercania, parecido = m.matrices(vut, hot)
    vut["precio"] = vut["precio_plaza_anual"]
    vut["por_habitacion"] = vut["accommodates"] / vut["dormitorios"]
    vut["demanda"] = vut["dormitorios"] * m.OCUPACION_AIRBNB
    asign = m.repartir(vut, hot, dist, cercania, parecido, 0.5, libre)
    tablas.append(resumen("Referencia: modelo actual (precio y cercania al 50 %)",
                          asign[["vut_idx", "hotel_idx", "habitaciones"]], vut, hot, dist, bv, bh)["tabla"])

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    pd.concat(tablas).to_csv(SALIDA, index=False, encoding="utf-8")
    print(f"\nGuardado en {SALIDA.relative_to(m.RAIZ)}")


if __name__ == "__main__":
    main()
