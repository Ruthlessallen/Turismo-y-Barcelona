# Checklist de la web interactiva

Lista de trabajo para la Fase 2 de `roadmap.md`: qué páginas tiene la web y qué dato lleva cada
una. **No es un acuerdo cerrado ni una ficha de feature** — es el guion que se va marcando, y cada
bloque pasará por `/feature` cuando toque construirlo.

Estado: **sin empezar.** Todo lo de aquí se apoya en datos que ya existen en `data/processed/`
salvo lo marcado con ⚠️.

---

## Estructura: cuatro páginas

Las licencias de apartamentos van en página propia porque el análisis ya no cabe al lado de nada
más — ver `pipeline/notebooks/03_auditoria_licencias.ipynb`.

| Página | Qué responde |
|---|---|
| 1 · Mapa principal | Dónde está la oferta turística, sobre el territorio |
| 2 · KPIs generales | Cuánta hay, de cada tipo |
| 3 · Licencias de apartamentos | Cuánta acredita licencia y cuánta no |
| 4 · Serie temporal | Cómo hemos llegado hasta aquí |

---

## 1 · Página principal — mapa geolocalizado

- [ ] Mapa con tres capas conmutables: **apartamentos turísticos**, **hoteles**, **bares y
      restaurantes**
- [ ] Filtro por municipio y por barrio (`FilterBar`)
- [ ] Clustering por densidad, no un punto por registro — en Ciutat Vella se solapan
- [ ] Capa opcional de zonas **PEUAT**, que explica visualmente dónde no pueden abrir hoteles nuevos

**Precisión geográfica — el punto que condiciona todo el diseño:**

- Barcelona ciudad tiene **coordenadas reales** (`nivel_geo = coordenada`)
- El resto de la provincia solo tiene **municipio** (`nivel_geo = municipio`) → ahí no hay puntos,
  hay coropletas
- Los anuncios de Airbnb vienen **desplazados ~200 m** por Inside Airbnb

Las tres precisiones no pueden pintarse igual sin mentir. El mapa debe distinguirlas visualmente y
decirlo en la leyenda, no solo en una nota al pie.

⚠️ **Bares y restaurantes está sin construir.** La fuente (Diputació de Barcelona, censo de
actividades) está verificada pero no integrada: falta clasificar la actividad, que viene como texto
libre (`BAR`, `RESTAURANT`...), no como código estable.

---

## 2 · Página de KPIs generales

- [ ] `StatTile` por categoría: **hoteles**, **apartamentos turísticos (AT)**, **VUT**, **bares y
      restaurantes**
- [ ] Plazas además de establecimientos — un hotel de 400 habitaciones y un VUT de 4 plazas no
      pesan igual
- [ ] Desglose provincia / ciudad de Barcelona
- [ ] Comparativa entre municipios (`ComparisonBarChart`)

**No mezclar VUT y AT en el mismo total.** Son figuras legales distintas y la eliminación de 2028
solo afecta a los VUT: los Apartaments Turístics siguen. Confundirlos es el error más fácil de
cometer en toda la web (ver `docs/prd.md`).

---

## 3 · Página de licencias de apartamentos

Traslada a la web el embudo del notebook 03. Cada cifra **por anuncios y por anfitriones**.

- [ ] Embudo completo, del total a los que no acreditan licencia, con lo descartado en cada paso visible
- [ ] Desglose por situación: verificada / no declara / número imposible / plausible inexistente /
      otro régimen / se asume por el anfitrión
- [ ] Top barrios, **por volumen y por tasa** — no solo volumen, o siempre gana el Eixample
- [ ] Concentración por anfitrión: cuántos tienen uno solo y cuántos anuncios acumulan los grandes
- [ ] Mapa de la oferta sin licencia, **agregado por barrio**, nunca por anuncio

**Reglas que no se negocian en esta página:**

- Se dice **"sin licencia acreditada"**, nunca "ilegal" ni "infractor". Describe lo observado —que el anuncio no acredita una licencia válida—, no una situación legal. El campo lo rellena el anfitrión sin
  validación técnica: una licencia real mal escrita cae en el mismo grupo
- **Nada resoluble a nivel de vivienda** — ni el mapa, ni una tabla, ni un tooltip
- Los criterios de exclusión se explican en la propia página, no en un anexo: sin ellos la cifra no
  significa nada
- El umbral de las 31 noches se explica bien: mide **cada cesión por separado**, no el acumulado
  del año

---

## 4 · Página de serie temporal

- [ ] Evolución del **parque legal de VUT** por trimestre, 2018-T2 → 2026-T1 (`TimeSeriesChart`)
- [ ] **Altas y bajas** por trimestre, no solo el stock: el saldo neto esconde el movimiento
- [ ] Serie por barrio y distrito
- [ ] Mapa temporal: cómo se ha ido moviendo la licencia por la ciudad
- [ ] Evolución de hoteles ⚠️

**Lo que ya está comprobado (2026-08-29):** cada fichero trimestral es una **foto del stock
activo**, no un acumulado, así que altas y bajas se pueden separar cruzando por `N_EXPEDIENT`.
Verificado sobre 2018-T2 → 2019-T2: 9.509 en ambos, 94 bajas, 67 altas, y la aritmética cuadra
exactamente con el total del trimestre siguiente.

**Dos obstáculos técnicos ya identificados:**

- **El esquema cambia entre trimestres** — 16 columnas en 2018, 21 en 2026.
  `NUMERO_REGISTRE_GENERALITAT` (el HUTB) no existe en los ficheros antiguos, así que hacia atrás
  solo se puede seguir por expediente
- **Hay ficheros mal formados** — el header de 2018 declara 16 columnas y las filas traen 17
  (`LONGITUD_X -LATITUD_Y` es un nombre para dos columnas); algunos traen BOM. Hay que parsear con
  detección, no con `read_csv` a secas

⚠️ **La serie de hoteles no existe todavía.** Open Data BCN sirve un snapshot único, no una serie.
Habría que buscar otra fuente o construirla guardando snapshots desde ahora.

⚠️ **No habrá serie de anuncios de Airbnb.** Inside Airbnb solo publica el snapshot actual
(probadas ocho fechas anteriores, todas 403) y el archivo de montera34 se corta en 2019-03. Sin
snapshots históricos no se puede calcular el % sin licencia de años pasados — y aunque se
consiguieran, habría que cruzar cada uno contra el registro **de su trimestre**, no contra el de
hoy, porque una licencia dada de baja hoy figura como inexistente.

---

## Un supuesto que la web debe dejar explícito

Eliminar ~10.000 licencias VUT **no elimina la oferta turística de la ciudad**. Los anuncios que
hoy no acreditan licencia no dependen de tenerla, así que no hay motivo para esperar que
desaparezcan con ella. Cualquier proyección de M-06 (absorción hotelera) que dé por hecho que la
oferta baja a cero se equivoca en el punto de partida.

Es un supuesto del análisis, no un dato medido, y debe aparecer como tal.

---

## Pendiente de decidir

- [ ] ¿Los bares y restaurantes son una capa del mapa o merecen su propia página?
- [ ] ¿La comparativa entre municipios va en KPIs o es la Fase 3 (M-07)?
- [ ] Los `HB-` de hotel **sí serían verificables** contra el registro que ya tenemos; los `AJ` de
      albergue no. Hoy se tratan igual en la web: ¿conviene separarlos?
