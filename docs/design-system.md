# Design System

Fuente de verdad visual del proyecto. Consultar antes de crear cualquier componente nuevo.
Actualizar cuando se añadan nuevos patrones, componentes o se modifique la identidad visual.

Es un dashboard de datos públicos: la paleta y las convenciones de gráficos siguen el método de
la skill `dataviz` (color por función, no por gusto — categórico/secuencial/divergente/estado, con
validación de accesibilidad para daltonismo). Este proyecto no parte de una marca propia, así que
usa directamente la **paleta de referencia validada** de esa skill. Si más adelante se define una
identidad de marca propia, se sustituyen estos valores y se revalida con
`scripts/validate_palette.js` — el resto del sistema no cambia.

Light y dark mode son ambos de primera clase desde el arranque: cada rol de color lleva su valor
en ambos modos, no es un dark mode "automático" por inversión.

---

## Paleta de colores

**Roles base de UI:**

| Rol | Light | Dark |
|-----|-------|------|
| Primary (acento) | `#2a78d6` | `#3987e5` |
| Background (page plane) | `#f9f9f7` | `#0d0d0d` |
| Surface (cards, paneles) | `#fcfcfb` | `#1a1a19` |
| Text primary | `#0b0b0b` | `#ffffff` |
| Text secondary | `#52514e` | `#c3c2b7` |
| Muted (ejes, etiquetas) | `#898781` | `#898781` |
| Gridline / borde | `#e1e0d9` | `#2c2c2a` |
| Success (delta positivo) | `#006300` | `#0ca30c` |
| Error / critical | `#d03b3b` | `#e66767` |
| Warning | `#fab219` | `#fab219` |

**Paleta categórica** (series de un mismo gráfico — municipios, tipos de alojamiento). Orden fijo,
nunca se reordena ni se cicla:

| Slot | Uso sugerido | Light | Dark |
|------|--------------|-------|------|
| 1 | Serie principal / VUT | `#2a78d6` | `#3987e5` |
| 2 | Hoteles | `#eb6834` | `#d95926` |
| 3 | Bares/restaurantes | `#1baf7a` | `#199e70` |
| 4 | Cuarta serie (evitar junto a 2) | `#eda100` | `#c98500` |
| 5 | — | `#e87ba4` | `#d55181` |
| 6 | — | `#008300` | `#008300` |
| 7 | — | `#4a3aa7` | `#9085e9` |
| 8 | — | `#e34948` | `#e66767` |

En mapas coropléticos, gráficos de dispersión o small multiples (donde se comparan todos los pares
a la vez, no solo adyacentes), **tope de 3 series** — los slots 1-3 son los únicos validados para
esa comparación completa. Más de 3 categorías → agrupar en "Otros" o usar paneles separados por
municipio.

**Secuencial** (magnitud continua — nº de licencias en el mapa coroplético de la provincia): un
solo hue, azul, de claro a oscuro. Rampa completa en `references/palette.md` de la skill `dataviz`
si hace falta más de 8 pasos.

**Divergente** (comparativas antes/después, ganancia/pérdida de oferta): azul ↔ rojo, con gris
neutro (`#f0efec` light / `#383835` dark) en el punto medio ("sin cambio").

**Estado** (fijo, nunca se reutiliza para series): good `#0ca30c`, warning `#fab219`, serious
`#ec835a`, critical `#d03b3b`. Siempre con icono + etiqueta, nunca solo color — varios de estos
tonos bajan de 3:1 de contraste en modo claro por diseño.

**Regla de integridad específica de este proyecto:** el tramo proyectado de cualquier serie
temporal (después de "hoy", ver M-06 en `prd.md`) nunca lleva el mismo tratamiento visual que el
dato observado. Ver "Estilo de componentes".

---

## Tipografía

- **Toda la interfaz, incluida la cifra hero:** `system-ui, -apple-system, "Segoe UI", sans-serif`.
  Sin display ni serif — la prioridad es legibilidad y carga rápida en una web pública.
- Cifras grandes sueltas (stat tiles, hero number): figuras proporcionales por defecto.
- Columnas que deben alinear verticalmente (tablas, ejes de gráfico): `font-variant-numeric:
  tabular-nums`.
- Escala tipográfica a definir en la maquetación de la primera pantalla — no bloquea el resto de
  la documentación.

---

## Espaciado y grid

- Escala base 4px: 4, 8, 12, 16, 24, 32, 48, 64, 96.
- Grid: 12 columnas, gutter 24px, max-width 1200px para el contenido; los paneles de mapa/gráfico
  a ancho completo dentro de esa franja.
- Densidad compacta en tablas (operadores, licencias), estándar en el resto — hay bastante dato
  que mostrar por pantalla.

---

## Estilo de componentes

- Border radius: 8px en cards/paneles, 4px en inputs y filtros, full en badges de estado.
- Sombras: solo en tooltips y elementos flotantes (nunca decorativas en cards).
- Iconos: set lineal simple tipo Lucide (SVG puro), 20px base — sin comprometerse a un binding de
  framework concreto hasta decidir el stack en `architecture.md`.
- **Datos observados vs. proyectados** (regla de integridad, ver arriba): observado = línea/relleno
  sólido. Proyectado = línea discontinua + etiqueta "proyección" visible junto al tramo, nunca el
  mismo trazo que un dato real. Esto aplica a todo gráfico temporal que cruce el punto "hoy".
- Gráficos: trazos finos, extremos de dato redondeados 4px, líneas 2px, marcadores ≥8px, hueco de
  2px entre segmentos apilados o barras adyacentes. Leyenda siempre presente con ≥2 series (ninguna
  con 1 sola). Toda serie codificada por color lleva además etiqueta directa o tabla equivalente —
  el color nunca es la única forma de distinguir una serie.
- Toda cifra o panel que muestre datos lleva nota de fuente + fecha de extracción visible (ver
  componente `SourceFootnote` abajo) — no es opcional, es un requisito de `prd.md`.

---

## Tono visual

Serio y creíble, no corporativo ni frío: es una web pública sobre un cambio regulatorio con
impacto real en vivienda y turismo, y el público incluye prensa e investigadores que necesitan
poder citarla. El dato es el protagonista — la interfaz no compite visualmente con el gráfico.

Qué NO debe parecer: ni un dashboard de BI interno (denso, sin contexto), ni una pieza de opinión
o activismo visual (nada de iconografía cargada o titulares editorializados) — cada afirmación
visual tiene que sostenerse en el dato y su fuente.

---

## Componentes definidos

A medida que se construyan, documentar aquí props reales y variantes. Lista inicial derivada
directamente de las features MUST/SHOULD de `prd.md`:

### FilterBar
Selector de municipio (uno o varios, para comparar) + rango temporal 2021–2031 con "hoy" marcado
en la línea de tiempo. Una sola fila, encima de los gráficos — nunca lateral en desktop.

### ChoroplethMap
Mapa de la provincia de Barcelona coloreado por la métrica activa (paleta secuencial azul).
Soporta M-01/M-02/M-03 (licencias por municipio) y M-07 (comparativa territorial).

### ListingClusterMap
Mapa de puntos agrupados en clusters para la oferta anunciada en Airbnb (M-08), coloreados por
estado del cruce con el registro oficial (paleta categórica: con licencia encontrada / candidato
sin licencia detectada — nunca la palabra "ilegal" en la interfaz, ver `prd.md` → WON'T).

**Restricción técnica, no solo de estilo:** el componente tiene un zoom máximo por debajo del cual
ya no se pueden resolver clusters individuales — nunca se renderiza un cluster de tamaño 1 como un
punto identificable. Esto hace cumplir el límite de "nunca dirección individual en la web pública"
(`prd.md` → WON'T) a nivel de componente, no solo como convención que alguien podría olvidar.

### StatTile
Cifra clave + delta frente al periodo anterior (p.ej. "Licencias VUT activas: 8.420 · -12% vs hace
5 años"). Sin gráfico dentro — para eso está `TimeSeriesChart`.

### TimeSeriesChart
Evolución temporal de una métrica (licencias, llegadas, pernoctaciones). Aplica la regla
observado/proyectado de "Estilo de componentes" en todo tramo posterior a "hoy" (M-06).

### ComparisonBarChart
Comparativa entre municipios o entre tipos de oferta (VUT / hotel / restauración) en un punto
temporal dado (M-07).

### OperatorTable
Tabla ordenable de empresas/operadores por nº de licencias (S-01). Densidad compacta.

### SourceFootnote
Nota fija en cada panel: fuente oficial + fecha de extracción. Obligatoria, no decorativa — es la
base de la credibilidad de todo el proyecto.

### ExportButton
Exporta a CSV exactamente los datos visibles tras los filtros aplicados (S-02).

---

## Referencias visuales

Sin referencias fijadas todavía. Dirección sugerida por el tono (serio, dato-primero, citable):
paneles de datos al estilo Our World in Data o el desk de gráficos de un medio (ES: Datadista,
Civio) — más que un dashboard de producto SaaS. Ajusta o sustituye si tienes otras referencias en
mente.
