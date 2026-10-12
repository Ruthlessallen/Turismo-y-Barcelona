# Fuentes de los datos

De dónde sale cada dato, quién lo publica, con qué fecha y licencia, y qué se le hace. Las cifras
derivadas (cuántos pisos, cuánta ocupación, cuántos turistas) **no se repiten aquí**: viven en un
solo sitio, los JSON de `data/exports/mapa/`, y la web las lee de ahí.

| Documento | Para qué |
|---|---|
| `supuestos.md` | Las decisiones nuestras de las que depende el resultado |
| `criba.md` | Cuántos anuncios caen en cada filtro *(generado)* |
| `linaje.md` | Qué fichero alimenta a qué script *(generado)* |
| `diccionario.md` | Cada fichero de `data/`: filas, columnas y quién lo produce *(generado)* |
| `observaciones-datos.md` | Comprobaciones manuales contra la fuente original |

**Última revisión:** 2026-10-12.

---

## 1. Las fuentes originales

### 1.1 Registre de Turisme de Catalunya — Generalitat de Catalunya
- **Qué aporta:** el censo oficial de alojamiento de la provincia (viviendas de uso turístico,
  hoteles, apartaments turístics…). Es la única fuente con titular (razón social).
- **Cómo se obtiene:** API abierta de Transparència,
  `https://analisi.transparenciacatalunya.cat/resource/t2h3-cgys.json`. Descargado el 27-28 de agosto de 2026.
- **No trae:** coordenadas, ni plazas en las viviendas de uso turístico.
- **Datos personales.** Entre los titulares hay personas físicas. `data/raw/` no se versiona;
  `bronze/unificar_registros.py` anula los DNI por su forma y la web solo publica la sociedad titular.

### 1.2 Open Data BCN — Ajuntament de Barcelona (CC BY 4.0)
- Licencias de viviendas turísticas 2016–2026T1 (coordenadas reales y plazas de la ciudad), hoteles
  de la ciudad (barrio y distrito; snapshot congelado en 2023) y el mapa del PEUAT (12 zonas, 2022).
- Se cruza con el Registre primero por número de registro oficial y, lo que queda suelto, por
  dirección normalizada y solo si la correspondencia es 1:1.

### 1.3 Inside Airbnb — volcado del 24 de junio de 2026
- **Qué aporta:** los anuncios de la ciudad con precio, capacidad, licencia declarada y reseñas.
  `https://data.insideairbnb.com/spain/catalonia/barcelona/2026-06-24/`
- Es un anuncio, no una vivienda, y no es el registro oficial. **Las coordenadas están desplazadas
  hasta 150 m a propósito** por la fuente.
- De los anuncios a las viviendas del análisis hay seis filtros encadenados (`criba.md`).

### 1.4 INE — Encuesta de Ocupación Hotelera
- **Cómo se obtiene:** API pública `servicios.ine.es/wstempus` (viajeros y pernoctaciones,
  establecimientos, plazas y ocupación; punto turístico Barcelona, últimos 60 meses) y el Portal de
  Dades del Ajuntament (ADR por categoría, 2013–2026).
- **Tres usos:**
  1. **Ocupación por habitaciones**, media de 12 meses: es lo que descuenta las habitaciones ya
     vendidas. Por habitaciones y no por plazas porque la habitación es lo que limita a un hotel.
  2. **ADR por categoría** (ingreso medio por habitación ocupada): **el único precio de hotel del
     proyecto** (ver 2).
  3. **Estacionalidad** (trece años): lleva el precio de Airbnb a equivalente anual.
- **Su límite:** es un agregado de la ciudad por categoría. Nunca atribuye un precio a un hotel.

### 1.5 Censo comercial municipal — restauración
- Ajuntament de Barcelona, trabajo de campo de 2023 y 2024. Se usa el censo y no OpenStreetMap,
  que se deja fuera una cuarta parte de la restauración. No existe censo equivalente de 2026.
- Se retiran los locales con el mismo nombre a menos de 10 m (un edificio con dos accesos dado de
  alta dos veces); los locales sin nombre no se comparan.

### 1.6 Geometría — ICGC e Inside Airbnb
- Los barrios vienen del GeoJSON de Inside Airbnb; el ICGC aporta los municipios usados para
  verificar geocodificaciones. Antes de llegar al navegador se reparan las geometrías inválidas y
  se simplifican (si la superficie cambia más de un 1 %, el script falla).

### 1.7 PEUAT — Pla especial urbanístic d'allotjaments turístics
- Aprobado definitivamente el 23 de diciembre de 2021. Zonas del Open Data BCN; reglas según
  prensa y despachos jurídicos (PwC, Uría, Hosteltur): **zona 1** sin establecimientos nuevos,
  **zona 2** mantiene el censo (solo se abre sustituyendo uno cerrado), **zona 3** crecimiento
  contenido, **zona 4** regulación propia.
- En las zonas 3 y 4 la apertura depende de topes de plazas por subzona (3A–3E; 4A Prat Vermell, 4B
  la Sagrera, 4C 22@ Norte, de mantenimiento). Las cifras de plazas varían entre fuentes y no están
  contrastadas con el texto oficial.
- La propuesta de 2023 de admitir hoteles «singulares» en las zonas 1 y 2 avanzó en comisión, pero
  el gobierno municipal dijo que mantenía las restricciones y no consta aprobación definitiva (comprobado
  en octubre de 2026). Rige el plan de 2021. Solo informa sobre el mapa; no entra en ningún cálculo.

### 1.8 Hoteles anunciados — prensa
- `data/bronze/hoteles_nuevos_bcn.csv`, recopilado a mano el 5 de octubre de 2026 (Hosteltur, ON
  Economia, EjePrime). **No es un registro oficial.** Cada entrada lleva su enlace; casi todo es
  reforma o cambio de gestión de hoteles que ya existen.

### 1.9 Descartadas
- **Precios de hotel recogidos de portales de reserva** (Google Hotels, Booking): se usaron al
  principio, con un modelo para estimar los que faltaban, y se retiraron el 2026-10-12. Sus términos
  no permiten redistribuirlos, el 41 % de los precios eran estimados y el error del modelo superaba
  la variación natural de un hotel. Los scripts están archivados fuera del repo.
- AENA y Port de Barcelona: no respondieron al verificarlas. Observatori del Turisme: infografías,
  solo contexto.

---

## 2. De dónde sale un precio

- **Hotel:** no tiene precio propio. Recibe el ADR medio de los últimos 12 meses de su categoría
  oficial del INE (1–2 estrellas, 3, 4, 5; `bandas.categoria_ine`, `adr_ultimos_12_meses`). De ahí:
  banda por habitación (cortes 100/175/300 €) y banda por plaza (ADR ÷ plazas por habitación de la
  categoría; cortes 40/70/120 €). Todos los hoteles de una categoría comparten banda.
  - Hostales y pensiones (`sin_estrellas`) van con «1 y 2 estrellas», que es donde el INE los
    incluye: **es un supuesto**.
  - Apartaments turístics y «sense categoritzar» no tienen categoría oficial: sin banda, fuera del reparto.
- **Piso:** el precio anunciado en Inside Airbnb, sin corregir limpieza ni comisión, llevado a
  equivalente anual con la estacionalidad del INE.

Consecuencia que hay que decir: la banda es de la categoría, no del hotel, y con estos cortes
ningún hotel cae en la banda €.

---

## 3. Qué lee la web

La web es estática: descarga ficheros ya calculados. Cada uno lo produce un script del pipeline y
está descrito, con sus columnas, en `diccionario.md`. Las ocupaciones que usa el modelo viven en
`gold/modelo.py` y viajan a la web por `parametros.json`.

## 4. Lo que nunca sale del pipeline

- **Del piso, solo lo que pinta el mapa:** posición (ya desplazada por la fuente), plazas,
  dormitorios, precio y banda. Sin id, nombre del anuncio, anfitrión ni licencia. El anfitrión solo
  sale agregado (por barrio desde 5 pisos; en la portada los cinco con más de 20).
- **Del hotel, la sociedad titular** tal como figura en el registro público, sin CIF.
- **Los DNI y los datos de titulares particulares.**

## 5. Lo que este trabajo no puede decir

Está en `/fuentes` (sección «Lo que esto no puede decir») y en `supuestos.md`.

## 6. Cómo rehacerlo

El orden de ejecución está en `pipeline/README.md`. `data/raw/` no se versiona (redescargable con
`pipeline/sources/descargar_fuentes.py`). Tras cualquier cambio: `python pipeline/generar_linaje.py`,
`generar_criba.py` y `generar_diccionario.py`.
