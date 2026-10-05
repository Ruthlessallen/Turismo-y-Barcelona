# Mapa limpio: tres capas, cada una con su pregunta

**Fecha:** 2026-10-05 10:00
**Tipo:** Funcionalidad

## Por qué

El mapa de sustitución 2028 se había ido de madre: demasiadas medidas en una sola pantalla. Se
conserva en `/mapa-anterior` para revisar cosas y `/mapa` pasa a ser simple.

## Qué hay

**Tres capas, cada una con su pregunta.**

- **Airbnb:** un punto por piso (plazas, dormitorios, precio de la noche del piso entero, banda
  por plaza) y, al pulsarlo, lo facturado al año: ocupación del 38,3 al 48 % × 365 noches × precio.
  Es un orden de magnitud, no facturación real.
- **Hoteles:** un punto por hotel y un radio de 0 a 500 m. Al pulsar un hotel, cuántos pisos hay
  en el radio, cuántas habitaciones pedirían y cuántas puede absorber ese hotel solo, en un año
  medio y en julio.
- **Restauración:** un punto por local, coloreado por la demanda de hoy o por el cambio en 2028.

**Panel de barrio:** reparto de unidades de alquiler (habitaciones de hotel frente a pisos
enteros), precio mediano de la noche de cada uno, turistas, facturación de los pisos, titular con
más hoteles, anfitrión con más pisos (desde 5), nombre comercial que más locales repite.

## Decisiones y supuestos

- **Unidad de alquiler:** el hotel alquila habitaciones; Airbnb, el piso entero. No se comparan
  plazas con plazas. La banda del piso sigue siendo por plaza porque no hay una banda de piso entero.
- **Restauración, demanda de hoy:** el turista de piso cuenta la mitad (cocina propia). **El 0,5 es
  un supuesto, no un dato** (`PESO_PISO_EN_RESTAURACION`).
- **Restauración, 2028:** los turistas de piso duermen en hoteles —reparto del modelo de
  sustitución, año medio, peso 0,5 entre precio y barrio— y cuentan enteros. El aumento total
  (+9,2 %: 62.462 → 68.240 clientes potenciales por noche) sale del 0,5 y no del modelo; lo que
  informa el modelo es **dónde** sube (4.147 locales ganan) y dónde baja (4.444 pierden).
- **Absorción de un hotel:** cada hotel por separado. Otros hoteles del mismo radio compiten por los
  mismos pisos, así que no se pueden sumar.
- **Sin dato:** plazas de los restaurantes (el censo no las trae). El nombre comercial no es la
  empresa: el censo de la ciudad no trae CIF.

## Pendiente de decidir

Los pisos salen como punto individual, lo que contradice `CLAUDE.md`, `data/README.md`,
`docs/prd.md` y la página `/fuentes`. No se ha publicado nada: hay que decidir cómo se reescriben
esas reglas antes de subirlo.
