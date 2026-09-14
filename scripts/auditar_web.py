"""Auditoria de punta a punta: web <- exports <- gold <- fuentes, y el modelo por dentro."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
GOLD = RAIZ / "data" / "gold"
EXPORTS = RAIZ / "data" / "exports" / "mapa"
WEB = RAIZ / "web" / "public" / "data" / "mapa"

fallos, avisos = [], []


def comprobar(condicion, mensaje, detalle=""):
    estado = "OK  " if condicion else "FALLA"
    print(f"  [{estado}] {mensaje}{('  -> ' + detalle) if detalle and not condicion else ''}")
    if not condicion:
        fallos.append(f"{mensaje} {detalle}")


def avisar(mensaje):
    print(f"  [AVISO] {mensaje}")
    avisos.append(mensaje)


print("=" * 78)
print("1. LA WEB LEE LO MISMO QUE HAY EN EXPORTS")
print("=" * 78)
for nombre in ["sustitucion_2028.json", "flujos_2028.json", "airbnb_por_barrio.json",
               "resumen.json"]:
    a, b = (EXPORTS / nombre), (WEB / nombre)
    comprobar(b.exists(), f"{nombre} existe en web/public")
    if b.exists():
        comprobar(a.read_bytes() == b.read_bytes(), f"{nombre} identico a data/exports",
                  f"{a.stat().st_size} vs {b.stat().st_size} bytes")

print()
print("=" * 78)
print("2. EXPORTS CUADRA CON GOLD")
print("=" * 78)
gold_sust = pd.read_csv(GOLD / "sustitucion_2028.csv")
gold_fluj = pd.read_csv(GOLD / "sustitucion_flujos_2028.csv")
exp_sust = json.loads((EXPORTS / "sustitucion_2028.json").read_text(encoding="utf-8"))
exp_fluj = json.loads((EXPORTS / "flujos_2028.json").read_text(encoding="utf-8"))

comprobar(set(exp_sust["escenarios"]) == set(gold_sust["escenario"]),
          "mismos escenarios en gold y export")
for esc, filas in exp_sust["escenarios"].items():
    g = gold_sust[gold_sust["escenario"] == esc]
    comprobar(len(filas) == len(g), f"{esc}: mismo numero de barrios", f"{len(filas)} vs {len(g)}")
    suma_json = sum(f["salen"] for f in filas)
    suma_gold = g["plazas_que_salen"].sum()
    comprobar(abs(suma_json - suma_gold) <= len(filas),
              f"{esc}: 'salen' cuadra (redondeo)", f"{suma_json} vs {suma_gold:.0f}")

for esc, filas in exp_fluj["escenarios"].items():
    g = gold_fluj[gold_fluj["escenario"] == esc]
    comprobar(len(filas) == len(g), f"{esc}: mismos flujos", f"{len(filas)} vs {len(g)}")

print()
print("=" * 78)
print("3. CONSERVACION: NO SE PIERDE NI SE INVENTA NINGUN TURISTA")
print("=" * 78)
vut = pd.read_csv(GOLD / "airbnb_para_web.csv", low_memory=False)
hoteles = pd.read_csv(GOLD / "alojamientos_reglados.csv", low_memory=False)
hoteles = hoteles[hoteles["banda_plaza"].notna() & hoteles["lat"].notna()].reset_index(drop=True)
TOTAL_VUT = vut["accommodates"].sum()
resumen = pd.read_csv(GOLD / "calidad" / "sustitucion_resumen.csv")

comprobar(abs(TOTAL_VUT - resumen["plazas_vut"].iloc[0]) < 1,
          "el total de plazas VUT del resumen sale del dato", f"{TOTAL_VUT} vs {resumen['plazas_vut'].iloc[0]}")
comprobar(abs(hoteles["plazas"].sum() - resumen["plazas_regladas"].iloc[0]) < 1,
          "el total de plazas regladas del resumen sale del dato")

for esc, g in gold_sust.groupby("escenario"):
    salen = g["plazas_que_salen"].sum()
    llegan = g["plazas_que_llegan"].sum()
    sin_sitio = g["plazas_sin_sitio"].sum()
    comprobar(abs(salen - TOTAL_VUT) < 1, f"{esc}: suma de 'salen' = total VUT",
              f"{salen:.0f} vs {TOTAL_VUT:.0f}")
    comprobar(abs(llegan + sin_sitio - TOTAL_VUT) < 1,
              f"{esc}: colocados + sin sitio = total VUT", f"{llegan:.0f}+{sin_sitio:.0f}")

print()
print("=" * 78)
print("4. EL REPARTO RESPETA EL AFORO")
print("=" * 78)
OCUPACION = float(resumen["ocupacion_partida"].iloc[0])
capacidad_barrio = (hoteles.groupby("barrio")["plazas"].sum() * (1 - OCUPACION))
for esc, g in gold_sust.groupby("escenario"):
    recibidas = g.set_index("barrio")["plazas_que_llegan"]
    excedidos = []
    for barrio, cuantas in recibidas.items():
        tope = capacidad_barrio.get(barrio, 0)
        if cuantas > tope + 0.5:
            excedidos.append(f"{barrio}: {cuantas:.0f} > {tope:.0f}")
    comprobar(not excedidos, f"{esc}: ningun barrio recibe mas de su aforo libre",
              "; ".join(excedidos[:3]))

print()
print("=" * 78)
print("5. LOS FLUJOS CUADRAN CON LOS TOTALES POR BARRIO")
print("=" * 78)
for esc in gold_sust["escenario"].unique():
    f = gold_fluj[gold_fluj["escenario"] == esc]
    b = gold_sust[gold_sust["escenario"] == esc].set_index("barrio")
    # salen_fuera = salen - se_quedan - sin_sitio ; los flujos < 20 turistas estan recortados
    for barrio in ["la Sagrada Família", "la Dreta de l'Eixample", "el Raval"]:
        if barrio not in b.index:
            continue
        esperado = (b.loc[barrio, "plazas_que_salen"] - b.loc[barrio, "plazas_que_se_quedan"]
                    - b.loc[barrio, "plazas_sin_sitio"])
        real = f[f["origen"] == barrio]["turistas"].sum()
        perdido = esperado - real
        ok = -1 <= perdido <= 20 * 40   # lo recortado por el minimo de 20
        if esc == "equilibrio":
            print(f"    {barrio[:34]:<36} salen fuera {esperado:>7.0f} | en flechas {real:>7.0f}"
                  f" | recortado {perdido:>6.0f}")
        if not ok:
            fallos.append(f"{esc}/{barrio}: flujos no cuadran ({esperado:.0f} vs {real:.0f})")
comprobar(not [x for x in fallos if "flujos no cuadran" in x],
          "los flujos por barrio cuadran con los totales (salvo el corte de 20)")

print()
print("=" * 78)
print("6. LAS DOS ESCALAS DE PRECIO SON LA MISMA")
print("=" * 78)
comprobar("precio_plaza_anual" in vut.columns, "la VUT usa precio equivalente anual")
comprobar(vut["precio_plaza_anual"].notna().all(), "ninguna VUT sin precio")
comprobar(hoteles["precio_plaza"].notna().all(), "ningun hotel sin precio por plaza")
factor = vut["factor_temporada"].iloc[0]
comprobar(abs(vut["precio_por_plaza"].median() / factor - vut["precio_plaza_anual"].median()) < 1,
          f"el precio anual de la VUT es el de junio dividido por {factor}")
print(f"    VUT    mediana {vut['precio_plaza_anual'].median():6.1f} EUR/plaza (anual)")
print(f"    hotel  mediana {hoteles['precio_plaza'].median():6.1f} EUR/plaza (anual)")
estimados = vut["precio_plaza_es_estimado"].mean()
print(f"    {estimados:.1%} de los precios VUT son estimados por modelo")
h_est = pd.read_csv(GOLD / "hoteles_bcn_precio_estimado.csv", low_memory=False)
print(f"    {h_est['precio_es_estimado'].mean():.1%} de los precios hoteleros son estimados")

print()
print("=" * 78)
print("7. LA OCUPACION SALE DEL INE Y ES LA QUE DICE LA WEB")
print("=" * 78)
serie = pd.read_csv(RAIZ / "data" / "bronze" / "serie_ine_barcelona.csv", low_memory=False)
oc = serie[serie["serie"].str.contains("Grado de ocupaci", na=False)
           & serie["serie"].str.contains("por plazas. B", na=False)].sort_values("mes")
media = oc.tail(12)["valor"].mean() / 100
comprobar(abs(media - OCUPACION) < 0.0001, "la ocupacion del modelo es la media de 12 meses del INE",
          f"{media:.4f} vs {OCUPACION:.4f}")
print(f"    ventana usada: {oc.tail(12)['mes'].iloc[0]} a {oc.tail(12)['mes'].iloc[-1]}")

print()
print("=" * 78)
print("8. EL MODELO POR DENTRO: LA UTILIDAD ELIGE LO QUE DICE ELEGIR")
print("=" * 78)
LAT0 = 41.39


def proyectar(lat, lon):
    return np.c_[np.asarray(lon, float) * 111.320 * np.cos(np.radians(LAT0)),
                 np.asarray(lat, float) * 110.570]


vut["precio"] = vut["precio_plaza_anual"]
hoteles["precio"] = hoteles["precio_plaza"]
D = np.sqrt(((proyectar(vut["latitude"], vut["longitude"])[:, None, :]
              - proyectar(hoteles["lat"], hoteles["lon"])[None, :, :]) ** 2).sum(axis=2))
B = np.abs(vut["precio"].to_numpy()[:, None] - hoteles["precio"].to_numpy()[None, :])
cerc, par = 1 - D / D.max(), 1 - B / B.max()

# Con w=1 sin limite de aforo, el elegido TIENE que ser el mas cercano. Si no, hay un bug.
elegido_w1 = (1.0 * cerc).argmax(axis=1)
comprobar((elegido_w1 == D.argmin(axis=1)).all(), "con w=1 el destino es siempre el mas cercano")
elegido_w0 = (1.0 * par).argmax(axis=1)
# No se compara el indice sino el precio: cuando dos hoteles cuestan exactamente lo mismo, el
# desempate cae de un lado u otro segun el orden de operaciones, y eso no es un error del modelo.
brecha_elegida = B[np.arange(len(B)), elegido_w0]
comprobar(np.allclose(brecha_elegida, B.min(axis=1), atol=1e-9),
          "con w=0 el destino es siempre el mas parecido en precio (empates aparte)",
          f"peor desvio {np.abs(brecha_elegida - B.min(axis=1)).max():.2e} EUR")
empates = int((elegido_w0 != B.argmin(axis=1)).sum())
if empates:
    print(f"    {empates} empates exactos de precio, resueltos por orden de operaciones "
          f"(desvio maximo {np.abs(brecha_elegida - B.min(axis=1)).max():.1e} EUR)")
comprobar(D.min() >= 0 and np.isfinite(D).all(), "matriz de distancias sana")
print(f"    distancia VUT-hotel: min {D.min():.3f} km, mediana del minimo {np.median(D.min(1)):.2f} km,"
      f" max {D.max():.1f} km")

print()
print("=" * 78)
print("9. LO QUE LA WEB DICE, COMPROBADO CONTRA EL DATO")
print("=" * 78)
eq = gold_sust[gold_sust["escenario"] == "equilibrio"]
r_eq = resumen[resumen["escenario"] == "equilibrio"].iloc[0]
libres = resumen["plazas_regladas"].iloc[0] * (1 - OCUPACION)
print(f"    'Quedan 27.092 plazas libres'      -> {libres:,.0f}")
print(f"    '2.975 no caben'                   -> {r_eq['plazas_sin_sitio']:,}")
print(f"    'ocupacion del 68%'                -> {OCUPACION:.1%}")
print(f"    'se mueven 0,48 km'                -> {r_eq['km_mediano']} km")
print(f"    'pagan de mas 24 EUR'              -> {r_eq['sobrecoste_mediano']} EUR")
print(f"    '6.834 viviendas / 30.067 plazas'  -> {len(vut):,} / {TOTAL_VUT:,.0f}")
comprobar(abs(libres - 27092) < 5, "las 27.092 plazas libres de la web salen del dato")
comprobar(r_eq["plazas_sin_sitio"] == 2975, "las 2.975 sin sitio salen del dato")
comprobar(len(vut) == 6834 and abs(TOTAL_VUT - 30067) < 1, "6.834 viviendas y 30.067 plazas")

print()
print("=" * 78)
print("10. ETIQUETAS DE LA WEB QUE PUEDEN ENGANAR")
print("=" * 78)
for barrio in ["la Dreta de l'Eixample", "el Raval"]:
    fila = eq[eq["barrio"] == barrio].iloc[0]
    de_fuera = fila["plazas_que_llegan"] - fila["plazas_que_se_quedan"]
    print(f"    {barrio[:30]:<32} llegan={fila['plazas_que_llegan']:>7.0f}"
          f"  se_quedan={fila['plazas_que_se_quedan']:>7.0f}  de fuera={de_fuera:>7.0f}")
print("    `plazas_que_llegan` INCLUYE a los del propio barrio. La web resta `se_quedan` para")
print("    rotular 'Llegan desde otros barrios' y ensena el total en una linea aparte.")

print()
print("=" * 78)
print(f"RESULTADO: {len(fallos)} fallos, {len(avisos)} avisos")
print("=" * 78)
for f in fallos:
    print(f"  FALLA: {f}")
for a in avisos:
    print(f"  AVISO: {a}")
