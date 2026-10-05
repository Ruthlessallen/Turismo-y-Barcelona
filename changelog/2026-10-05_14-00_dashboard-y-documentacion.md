# Dashboard de cifras, un solo momento y documentación al día

**Fecha:** 2026-10-05 14:00
**Tipo:** Funcionalidad y documentación

## Por qué

El mapa limpio de la mañana (ver la entrada anterior) dejó tres decisiones por documentar y una
portada que seguía contando el modelo antiguo, con texto y con dos fechas.

## Qué cambia

- **`/` es ahora un dashboard de cifras, sin texto.** Hoteles (hoteles, habitaciones, plazas,
  bandas, titulares con más hoteles, +20,3 % de turistas nuevos en hoteles tras 2028) y Airbnb
  (pisos, habitaciones, plazas, 222–278 M€ al año). Sale de `dashboard.json`.
- **Un solo momento: el año medio.** Julio queda fuera de la web nueva (sigue en `/mapa-anterior`
  y en el modelo).
- **Hoteles solo con banda, nunca el euro**, como ya decía `/fuentes`. `puntos_hoteles.json` ya no
  lleva precios. Los pisos conservan el precio anunciado.
- **Texto del mapa recortado.** Los paneles dicen cifras; lo que explica está en `/fuentes`.
- **Prototipo de flujos por banda** (`pipeline/gold/prototipo_flujos_banda.py`), sin publicar: el
  turista va a un hotel de su banda y, si no hay hueco, a la siguiente más cara.

## Documentación

- `docs/fuentes.md` y la página `/fuentes`: qué lee la web, lo que calcula (radio de un hotel,
  restauración, flujos por banda), lo que se publica de un piso, nuevos límites.
- `docs/supuestos.md`: B5 revisado con datos; C5 (licencias sin anuncio: 5.394, 30.980 plazas); F1
  reescrito (cada uno alquila una cosa distinta); F5 (un año medio); F7–F11 nuevos. La sección de
  geolocalización pasa a ser la G (había dos F).
- `CLAUDE.md`, `data/README.md`, `docs/prd.md` y `docs/data-model.md`: la regla de granularidad
  pasa de «nunca a nivel de vivienda» a «del piso, solo lo que pinta el mapa».
- `docs/web-checklist.md`, `docs/roadmap.md`, `README.md`: estado real y pendientes.
- `docs/linaje.md` y `docs/criba.md` regenerados.

## Hallazgo del prototipo

En un año medio los hoteles de banda € tienen 57 habitaciones libres y los pisos baratos piden
1.629: solo el 34 % de los turistas encuentra hotel de su banda. El volumen acaba en los €€€ (72 %)
y la presión de precio es de los €.

## Pendiente de decidir

Ver `docs/web-checklist.md` → «Pendiente de decidir».
