"""Dibuja el recorrido de los registros: donde se decide, cuantos caen y por que.

    python pipeline/generar_criba.py

Salida
    docs/criba.md   — un diagrama de decision por conjunto, con los recuentos reales

**Distinto de `docs/linaje.md`.** Aquel dice que fichero alimenta a que script; este dice que le
pasa a cada registro. Son las dos preguntas de la trazabilidad y no se responden con el mismo
dibujo: una es de tuberias, la otra de caudal.

**Los recuentos salen del dato, no del texto.** Cada rombo y cada cifra se leen de los CSV que el
pipeline acaba de producir, asi que el diagrama no puede afirmar una criba que ya no ocurre. Si
alguien cambia un umbral y vuelve a ejecutar, las cifras se mueven solas.

**Por que importa el orden de los rombos.** Un anuncio puede fallar varias condiciones a la vez —un
hotel que ademas lleva dos anos sin resenas— y solo se cuenta en la primera que incumple. El orden
elegido va de lo estructural a lo circunstancial: primero si la ley le alcanza siquiera, despues si
sigue vivo, y al final si tenemos precio. Leido al reves, el mismo dato contaria otra historia.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
GOLD = RAIZ / "data" / "gold"
SALIDA = RAIZ / "docs" / "criba.md"

# Cada paso: clave del motivo, pregunta del rombo, por que rama se cae, y a donde.
# La rama se declara en vez de deducirse: unas preguntas descartan al responder "si" y otras al
# responder "no", y dejar eso implicito es la forma mas rapida de invertir un diagrama sin notarlo.
PASOS_AIRBNB = [
    ("alojamiento_reglado", "¿Declara licencia de hotel,<br>albergue o apartament turistic?", "si",
     "Alojamiento reglado<br>cuenta en el lado hotelero"),
    ("habitacion_sin_hutb", "¿Cede la vivienda entera,<br>o declara un HUTB?", "no",
     "Habitaciones sueltas sin licencia<br>no es lo que la ley elimina"),
    ("habitacion_de_hotel", "¿Es habitacion de hotel?", "si",
     "Habitacion de establecimiento<br>se analiza en el otro lado"),
    ("estancia_de_32_noches", "¿Estancia minima<br>de 31 noches o menos?", "no",
     "Alquiler de temporada<br>fuera del alcance de la ley"),
    ("sin_actividad_desde_09_2025", "¿Tiene resenas<br>desde septiembre de 2025?", "no",
     "Sin huespedes recientes<br>no vende"),
    ("duplicado de nombre y anfitrion", "¿Es la primera vez que<br>aparece este anuncio?", "no",
     "Mismo nombre y anfitrion<br>ya contado"),
]


def nodo(texto: str) -> str:
    return texto.replace('"', "'")


def diagrama(inicio: int, pasos: list, conteos: dict[str, int], final: str) -> str:
    """Una cadena de rombos, cada uno con su salida lateral hacia el descarte."""
    lineas = ["flowchart TD",
              f'  entrada["<b>{inicio:,} anuncios</b><br>Inside Airbnb 2026-06-24"]']
    anterior, quedan = "entrada", inicio

    for i, (clave, pregunta, rama_descarte, destino) in enumerate(pasos):
        caen = conteos.get(clave, 0)
        quedan -= caen
        sigue_label = "no" if rama_descarte == "si" else "si"
        d, fuera, sigue = f"d{i}", f"x{i}", f"s{i}"
        lineas += [
            f'  {d}{{"{nodo(pregunta)}"}}',
            f'  {fuera}["{nodo(destino)}<br><b>{caen:,}</b>"]',
            f'  {sigue}["{quedan:,} siguen"]',
            f"  {anterior} --> {d}",
            f'  {d} -->|"{rama_descarte}"| {fuera}',
            f'  {d} -->|"{sigue_label}"| {sigue}',
        ]
        anterior = sigue

    lineas += [f'  final(["<b>{final}</b><br>{quedan:,}"])', f"  {anterior} --> final",
               "  classDef descarte fill:#f6e6e6,stroke:#b06060;",
               "  classDef meta fill:#e2f0e2,stroke:#4a8a4a;",
               f"  class {','.join(f'x{i}' for i in range(len(pasos)))} descarte;",
               "  class final meta;"]
    return "\n".join(lineas)


def main() -> None:
    # Se leen las salidas del notebook `pipeline/notebooks/revisar_airbnb_v2.ipynb`, que es donde
    # vive el criterio vigente. El pipeline mantiene su propia criba en `preparar_airbnb_bcn.py`,
    # con umbrales distintos; mientras no converjan, este diagrama describe la del notebook, que es
    # la que alimenta la web.
    dentro = pd.read_csv(GOLD / "airbnb_para_web.csv", low_memory=False)
    fuera = pd.read_csv(GOLD / "airbnb_excluidos_web.csv", low_memory=False)
    conteos = fuera["motivo_exclusion"].value_counts().to_dict()
    inicio = len(dentro) + len(fuera)

    filas = ["| Paso | Descartados | Quedan |", "|---|---:|---:|"]
    quedan = inicio
    filas.append(f"| Anuncios de partida | — | {inicio:,} |")
    for clave, *_ in PASOS_AIRBNB:
        caen = conteos.get(clave, 0)
        quedan -= caen
        filas.append(f"| {clave.replace('_', ' ')} | −{caen:,} | {quedan:,} |")
    filas.append(f"| **Sujetos a la ley de 2028** | | **{quedan:,}** |")

    SALIDA.write_text(f"""# Criba de los datos

**Generado por `pipeline/generar_criba.py` — no editar a mano.** Los recuentos se leen de los CSV
que el pipeline acaba de producir, asi que no pueden afirmar una criba que ya no ocurre.

Complementa a `docs/linaje.md`: aquel dibuja que fichero alimenta a que script, este dibuja que le
pasa a cada registro.

## Airbnb: que anuncios quedan sujetos a la eliminacion de 2028

Un anuncio puede incumplir varias condiciones a la vez y **solo se cuenta en la primera**. El orden
va de lo estructural a lo circunstancial: primero si la ley le alcanza, despues si sigue vivo, y al
final si hay precio.

```mermaid
{diagrama(inicio, PASOS_AIRBNB, conteos, "df_v2<br>viviendas de uso turistico")}
```

{chr(10).join(filas)}

Los descartados no se borran: quedan en `data/gold/airbnb_excluidos_web.csv` con su `motivo_exclusion`,
de modo que cualquiera puede rehacer el recuento con otro criterio sin volver al dato crudo.
""", encoding="utf-8")

    print(f"partida {inicio:,} -> sujetos {quedan:,}")
    for clave, *_ in PASOS_AIRBNB:
        print(f"  -{clave:26s} {conteos.get(clave, 0):6,}")
    print(f"Guardado en {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
