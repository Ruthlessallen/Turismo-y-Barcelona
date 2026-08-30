"""Prueba de 10 hoteles contra Places API (New): ¿qué campos de precio llegan de verdad?

No es un módulo del pipeline: es la comprobación previa que decide si Google sirve como fuente
de precio hotelero. Gasta 10 llamadas de las 1.000 gratuitas al mes.

    python pipeline/sources/probar_google_places.py

Necesita `GOOGLE_MAPS_API_KEY` en `.env.local` (fuera de git). La clave viaja por cabecera,
nunca por la línea de comandos ni por la URL: un token en un argumento acaba en el historial del
shell y en los logs.

Lo que se quiere averiguar, y por qué:

- **`priceLevel`** es un enum de cinco valores (FREE … VERY_EXPENSIVE) sin umbrales publicados.
  Sirve para ordenar, no para comparar en euros, y es muy grueso: cinco cajones para 754 hoteles.
- **`priceRange`** sí trae `startPrice`/`endPrice` en moneda real. Es el campo que interesa, pero
  Google solo lo rellena donde tiene datos y no documenta la cobertura. De ahí esta prueba.
- **`servesDinner` y compañía** aproximan "tiene restaurante", sin ser lo mismo: un hotel puede
  servir cenas sin restaurante abierto al público.

Si `priceRange` viene vacío en la mayoría, Google no resuelve el precio y hay que volver a la vía
de estrellas + tamaño calibrados con los hoteles que ya tienen precio real vía Airbnb.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
RUTA_HOTELES = RAIZ / "data" / "processed" / "hoteles_y_apartaments_unificados.csv"
RUTA_SALIDA = RAIZ / "data" / "processed" / "prueba_google_places.csv"

BUSCAR = "https://places.googleapis.com/v1/places:searchText"

# El tramo de facturación lo fija el campo más caro del fieldMask, así que se pide lo justo.
CAMPOS = ",".join([
    "places.id", "places.displayName", "places.formattedAddress", "places.location",
    "places.priceLevel", "places.priceRange", "places.rating", "places.userRatingCount",
    "places.servesBreakfast", "places.servesLunch", "places.servesDinner", "places.types",
])

MUESTRA = 10


def leer_clave() -> str:
    """Lee la clave de `.env.local` o del entorno. Nunca se imprime ni se pasa por argumento."""
    clave = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not clave:
        env = RAIZ / ".env.local"
        if env.exists():
            for linea in env.read_text(encoding="utf-8").splitlines():
                if linea.startswith("GOOGLE_MAPS_API_KEY="):
                    clave = linea.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not clave:
        raise SystemExit(
            "Falta GOOGLE_MAPS_API_KEY. Añádela a .env.local:\n"
            "  echo 'GOOGLE_MAPS_API_KEY=tu_clave' > .env.local"
        )
    return clave


def consultar(texto: str, clave: str) -> dict:
    """Una búsqueda de texto. La clave va por cabecera, no por la URL."""
    cuerpo = json.dumps({"textQuery": texto, "languageCode": "es", "maxResultCount": 1}).encode()
    peticion = urllib.request.Request(
        BUSCAR,
        data=cuerpo,
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": clave,
            "X-Goog-FieldMask": CAMPOS,
        },
    )
    try:
        with urllib.request.urlopen(peticion, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        detalle = e.read().decode("utf-8", "replace")[:300]
        return {"error": f"HTTP {e.code}", "detalle": detalle}


def main() -> None:
    clave = leer_clave()
    hoteles = pd.read_csv(RUTA_HOTELES, dtype=str)
    # Con nombre y en la ciudad: sin nombre comercial la búsqueda por texto no tiene a qué agarrarse.
    candidatos = hoteles[
        (hoteles["tipo"] == "hotel")
        & (hoteles["municipio"] == "Barcelona")
        & hoteles["nombre_comercial"].notna()
        & (hoteles["nombre_comercial"] != "Sense especificar")
    ]
    # Los más grandes primero: si Google no tiene datos ni de estos, no los tendrá de ninguno.
    muestra = candidatos.assign(
        hab=pd.to_numeric(candidatos["habitaciones"], errors="coerce")
    ).nlargest(MUESTRA, "hab")

    print(f"Consultando {len(muestra)} hoteles (de {len(candidatos):,} posibles)\n")
    filas = []
    for _, h in muestra.iterrows():
        consulta = f"{h['nombre_comercial']} hotel Barcelona"
        r = consultar(consulta, clave)
        if "error" in r:
            print(f"  ERROR {h['nombre_comercial'][:34]:36s} {r['error']} {r['detalle'][:120]}")
            continue
        lugares = r.get("places", [])
        if not lugares:
            print(f"  sin resultado   {h['nombre_comercial'][:34]}")
            continue
        p = lugares[0]
        rango = p.get("priceRange", {})
        fila = {
            "licencia_id": h["licencia_id"],
            "nombre_registro": h["nombre_comercial"],
            "nombre_google": p.get("displayName", {}).get("text"),
            "habitaciones": h["habitaciones"],
            "categoria": h["categoria"],
            "price_level": p.get("priceLevel"),
            "precio_desde": (rango.get("startPrice") or {}).get("units"),
            "precio_hasta": (rango.get("endPrice") or {}).get("units"),
            "moneda": (rango.get("startPrice") or {}).get("currencyCode"),
            "rating": p.get("rating"),
            "n_valoraciones": p.get("userRatingCount"),
            "sirve_desayuno": p.get("servesBreakfast"),
            "sirve_comida": p.get("servesLunch"),
            "sirve_cena": p.get("servesDinner"),
        }
        filas.append(fila)
        precio = (f"{fila['precio_desde']}-{fila['precio_hasta']} {fila['moneda']}"
                  if fila["precio_desde"] else "—")
        print(f"  {str(fila['nombre_google'])[:30]:32s} nivel={str(fila['price_level']):24s} "
              f"rango={precio:16s} cena={fila['sirve_cena']}")

    if not filas:
        raise SystemExit("\nNinguna consulta devolvió datos. Revisa que Places API (New) esté habilitada.")

    d = pd.DataFrame(filas)
    d.to_csv(RUTA_SALIDA, index=False, encoding="utf-8")

    print(f"\n{'—' * 62}\nCobertura sobre {len(d)} hoteles consultados:")
    print(f"  con priceLevel (banda)     : {d['price_level'].notna().sum()}")
    print(f"  con priceRange (euros)     : {d['precio_desde'].notna().sum()}  ← lo que decide")
    print(f"  con datos de restauración  : {d[['sirve_desayuno','sirve_comida','sirve_cena']].notna().any(axis=1).sum()}")
    print(f"  con rating                 : {d['rating'].notna().sum()}")
    print(f"\nGuardado en {RUTA_SALIDA.relative_to(RAIZ)}")

    if d["precio_desde"].notna().sum() == 0:
        print("\npriceRange vino vacío en los 10. Con solo la banda de priceLevel, Google no")
        print("resuelve el precio en euros: tocaría calibrar con estrellas + tamaño.")


if __name__ == "__main__":
    main()
