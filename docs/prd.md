# Product Requirements Document (PRD)

Fuente de verdad sobre qué construimos y por qué. Actualizar este archivo cuando cambie el
alcance, las funcionalidades o el usuario objetivo. Si algo se mueve a "fuera de alcance", no
borrar: mover a la sección correspondiente.

---

## Resumen ejecutivo

Hay dos capas normativas en juego, no una sola "ley": el **Decret Llei 3/2023** de la Generalitat
regula las VUT en 262 municipios de toda Catalunya con un tope del 10% en 2028, y **por encima de
eso**, la ciudad de Barcelona ha decidido ir más lejos y bajar a **cero licencias VUT — del orden
de 10.000 pisos — para noviembre de 2028**, decisión a la que ya se han sumado varios municipios
colindantes del área metropolitana. Detalle en `architecture.md` → Integraciones externas. Este
proyecto construye un dashboard interactivo que cruza oferta turística (apartamentos, hoteles,
bares/restaurantes) con demanda (entradas por todas las vías de acceso, estadísticas turísticas
oficiales) en toda la **provincia de Barcelona**, con una ventana de **2021 a 2031**: cinco años
de histórico antes de hoy y una proyección a cinco años vista.

El objetivo es entender qué puede ocurrir cuando esa oferta desaparece de la ciudad: si la absorbe
el sector hotelero, si se desplaza a otros municipios de la provincia, y cómo se mueve el gasto y
los flujos turísticos alrededor de ese cambio.

Se publica como **web pública interactiva, sin usuarios gestionados**: código y datos en un
repositorio de GitHub, con despliegue en Vercel (Next.js, ver `architecture.md`). Cualquier
visitante puede explorar los datos, las fuentes y los cruces sin necesidad de cuenta.

---

## Problema que resuelve

Hoy no existe una fuente unificada que cruce quién opera los pisos turísticos de Barcelona, cuántas
licencias hoteleras y de restauración hay alrededor, y cómo entran los turistas a la provincia por
todas sus vías de acceso a lo largo del tiempo. Sin esa base cruzada, cualquier intuición sobre "qué
pasará cuando desaparezcan los pisos turísticos" es especulación: no hay forma de ver si la demanda
turística se redirige a hoteles, si se desplaza a otros municipios de la provincia, o si
simplemente baja.

---

## Usuario objetivo

Público general con interés en el tema. Es una web abierta, sin cuentas ni perfiles gestionados;
sirve por igual a varios perfiles:

- **Ciudadanía y prensa:** quiere entender qué está pasando con la vivienda turística en su
  ciudad/barrio, con datos y fuentes verificables en vez de titulares sueltos.
  - Frustración principal: los datos existen pero están dispersos entre fuentes oficiales
    distintas (ayuntamientos, aeropuerto, puerto, estadísticas turísticas) y nadie los ha cruzado.
- **Investigadores y analistas de políticas públicas:** quieren los datos y la metodología
  citables, con fuente y fecha de extracción visibles para cada dato.
- **Sector hotelero/inmobiliario:** quiere entender cómo se mueven oferta y demanda ante el cambio
  regulatorio, para su propia toma de decisiones (el proyecto no da recomendaciones, ver "Fuera de
  alcance").

---

## Funcionalidades core (MoSCoW)

### MUST
- **[M-01] Base de datos de licencias de apartamentos turísticos (VUT) con empresa/titular** —
  Dado el dashboard abierto, cuando el usuario filtra por municipio de la provincia y rango de
  fechas, entonces ve el número de licencias VUT activas y su evolución en ese periodo.
  *Negativo:* dado un municipio sin datos disponibles en la fuente oficial, cuando se selecciona,
  entonces el dashboard indica explícitamente "sin datos", nunca un cero que se pueda confundir con
  "cero licencias".
- **[M-02] Base de datos de licencias y empresas hoteleras** — Dado un municipio seleccionado,
  cuando el usuario consulta el panel de hoteles, entonces ve el número de hoteles, plazas totales
  y categoría, con su evolución en la ventana temporal del proyecto.
- **[M-03] Base de datos de licencias de bares/restaurantes** — Dado un municipio seleccionado,
  cuando el usuario consulta el panel de restauración, entonces ve el número de licencias activas
  y su evolución en el tiempo.
- **[M-04] Serie histórica de entradas de turistas por vía de acceso** — Dado un rango temporal
  seleccionado, cuando el usuario consulta el panel de llegadas, entonces ve el número de entradas
  por vía (aérea, marítima/crucero y terrestre) y su tendencia.
- **[M-05] Estadísticas turísticas generales integradas** (pernoctaciones, ocupación, gasto
  turístico) — Dado un municipio y un rango temporal, cuando el usuario consulta el panel de
  estadísticas, entonces ve estas métricas cruzadas con oferta (M-01/M-02/M-03) y llegadas (M-04).
- **[M-06] Estimación de absorción por proximidad (hoteles + Apartaments Turístics)** — Dado un
  cluster de HUT (viviendas de uso turístico, agrupadas por proximidad geográfica) que pierden su
  licencia, cuando el usuario consulta la vista de proyección, entonces ve qué porcentaje de
  capacidad adicional necesitarían asumir **los hoteles y los Apartaments Turístics (AT)** cercanos
  a ese cluster para absorber a los turistas que antes se alojaban ahí, con la metodología (radio
  de proximidad, criterio de agrupación, fórmula del porcentaje) visible en el propio dashboard, no
  como caja negra.
  *Por qué se incluye AT junto a hoteles:* ni el Decret Llei 3/2023 ni la política de Barcelona
  afectan a los Apartaments Turístics — ambos hablan explícitamente de "habitatges d'ús turístic"
  (vivienda), y el PEUAT prevé eliminar la categoría de uso turístic *d'habitatge*, no la de AT. Es
  oferta que no desaparece, igual que los hoteles — aunque es una categoría pequeña (337 en toda
  Catalunya), se incluye por precisión del modelo, no porque cambie mucho el resultado.
  *Negativo:* si un cluster no tiene ningún hotel dentro del radio de proximidad definido, el
  dashboard lo señala explícitamente como "sin oferta hotelera cercana" en vez de mostrar un
  porcentaje sin sentido.
  *Matiz importante:* la capacidad hotelera cercana no se trata como libremente ampliable — el
  PEUAT (plan urbanístico de Barcelona) bloquea licencias hoteleras nuevas en 3 de sus 4 zonas (ver
  `architecture.md`). El dashboard distingue "% que absorbería la capacidad hotelera actual" de
  "margen legal para crecer más allá de eso", que en la mayoría de la ciudad es cero.
- **[M-07] Vista comparativa por municipio de la provincia** — Dado el conjunto de municipios de la
  provincia, cuando el usuario compara "ciudad de Barcelona" contra el resto, entonces puede
  detectar si la oferta turística se desplaza hacia fuera de la ciudad a lo largo del tiempo.
- **[M-08] Mapa de oferta anunciada en Airbnb frente a licencias VUT oficiales** — Dado un periodo
  seleccionado, cuando el usuario consulta el mapa de oferta anunciada, entonces ve la ubicación de
  los anuncios activos de Airbnb **agrupados en clusters** (nunca puntos individuales sueltos), en
  tres categorías: con licencia HUTB verificada, exento (alquiler de temporada, hostel... — no es
  "sin licencia", es una categoría legal distinta), y sin licencia acreditada. El método
  principal de cruce es **directo por número de licencia** (Airbnb obliga a declararlo en Barcelona
  y ~la mitad de los anuncios lo trae parseable); solo cuando no hay número declarado ni exención,
  cae a un fallback por dirección aproximada.
  *Negativo:* el fallback por dirección parte de coordenadas ofuscadas ~200m por Inside Airbnb, así
  que es una estimación con margen de error, nunca una certeza — el dashboard etiqueta ese caso como
  "sin licencia acreditada", nunca como "ilegal confirmado" (ver WON'T). El match directo
  por número de licencia no tiene ese margen de error: es una comparación exacta contra el registro.
  *Límite de cobertura:* Inside Airbnb solo publica datos para la ciudad de Barcelona, no para el
  resto de la provincia — este mapa queda acotado a la ciudad salvo que aparezca otra fuente para
  el resto de municipios.
  *Salvaguarda de diseño:* el mapa nunca permite hacer zoom hasta resolver un cluster en un único
  punto identificable — es una restricción técnica del componente, no solo una norma de estilo (ver
  `design-system.md` → `ListingClusterMap`).

### SHOULD
- **[S-01] Filtro por empresa/operador y marca** — Dado el panel de licencias VUT u hoteleras,
  cuando el usuario filtra por empresa, entonces ve cuántas licencias controla ese operador y su
  concentración relativa de mercado.
  *Aviso verificado con datos reales:* agrupar solo por `cif`/titular legal **infravalora la
  concentración real** — es habitual que una misma cadena registre cada hotel bajo una sociedad
  distinta (comprobado: la cadena "Catalonia" tiene 32 hoteles en el Registre de Turisme bajo 19
  titulares legales distintos, p. ej. "Duques de Bergara S.L.U" es titular de 6 de ellos). La
  concentración real hay que medirla también por **marca** (extraída del nombre comercial), no
  solo por CIF.
- **[S-02] Exportación de datos filtrados** — Dado cualquier panel con filtros aplicados, cuando el
  usuario pide exportar, entonces recibe un CSV con exactamente los datos visibles en pantalla.

### COULD
- **[C-01] Señales de "zonas de mayor impacto"** — Dado el cruce de datos por municipio/barrio,
  cuando la caída de oferta VUT sea especialmente pronunciada frente a la oferta hotelera
  circundante, entonces el dashboard lo destaca visualmente.
- **[C-02] Referencias comparativas con otras ciudades** que ya hayan limitado los pisos turísticos,
  como contexto para la proyección (M-06).

### WON'T (esta versión)
- **Publicar en la web pública** predicciones o señalamientos a nivel de vivienda o dirección
  individual — la web pública siempre agrega por municipio/barrio. Esto es un límite de
  *publicación*, no de *análisis*: el pipeline interno puede trabajar a más detalle si hace falta
  (ver `data-model.md` → Granularidad), pero eso no sale publicado tal cual sin verificación legal
  previa — nombrar una dirección concreta como "sin licencia" sin esa verificación es una
  acusación, no un dato.
- Datos en tiempo real o feeds en vivo — el proyecto trabaja con datos históricos y estadísticos
  publicados por fuentes oficiales, con su fecha de extracción documentada.
- Gestión de cuentas de usuario, login o roles — la web es de acceso público y abierto, sin
  autenticación.

Las WON'T no llevan ID ni criterio: no se van a construir. Si alguna entra más adelante, se le
asigna ID nuevo al moverla de sección.

---

## Flujos de usuario principales

**Flujo de exploración principal:** el usuario abre el dashboard y ve la provincia de Barcelona
con el número de licencias VUT activas por municipio. Ajusta el rango temporal (2021–2031, con el
punto "hoy" marcado en la línea de tiempo) y compara la evolución de plazas turísticas por tipo
(VUT, hotel) frente a las llegadas de turistas por aeropuerto y puerto. Al seleccionar un
municipio, ve el desglose de empresas/operadores con más licencias, la evolución de licencias de
restauración, y la proyección estimada para los próximos años tras la eliminación de las VUT en la
ciudad de Barcelona.

**Flujo de comparación territorial:** el usuario fija "ciudad de Barcelona" como referencia y
selecciona uno o varios municipios de la provincia para comparar la evolución de oferta turística,
buscando señales de desplazamiento.

(Diagramas de estos flujos, si hacen falta, van en `architecture.md` o `user-flows.md`, no aquí.)

---

## Requisitos no funcionales

- **Trazabilidad de fuentes:** todo dato mostrado debe poder rastrearse a su fuente oficial y
  fecha de extracción — esto es un análisis para tomar decisiones, no una demo.
- **Rendimiento:** los filtros por municipio/periodo deben responder con fluidez sobre ~10 años de
  datos agregados de toda la provincia.
- **Acceso público sin autenticación:** cualquier visitante entra sin cuenta ni login (ver WON'T).
- **Responsive:** usable en móvil y escritorio — es una web pública, no una herramienta interna.
- **Accesible:** contraste suficiente y navegación por teclado como mínimo, al ser un sitio de
  acceso público (detalle en `design-system.md`).

---

## Fuera de alcance (explícito)

- Municipios fuera de la provincia de Barcelona.
- Publicar direcciones o viviendas concretas señaladas como "sin licencia" en la web pública sin
  verificación legal previa (ver WON'T) — el análisis interno sí puede llegar a ese nivel.
- Recomendaciones de inversión o asesoramiento financiero personalizado.
