# Ajustes: bandas en vertical, facturación con el calendario, descarte duplicado, portada a pantalla

**Fecha:** 2026-10-07 10:00
**Tipo:** Ajuste

- **`/hoteles`:** la ocupación por banda pasa a columnas verticales: base del 80,2 % de hoy, igual
  en todas, y encima lo que sube en 2028 (+19,8 pts en las bandas € y €€, +11,5 en las €€€ y +0,7
  en las €€€€), con la diferencia entre bandas a la vista.
- **Facturación de un piso:** el dataset sí trae las noches (`availability_365`), y de ahí salía ya
  el 38,3 %. El suelo usa ahora el calendario de cada anuncio y no un 38,3 % plano: **178–232 M€**
  (antes 185–232). El popup del piso también.
- **Embudo de `/airbnb`:** el descarte 1 (alojamiento reglado) y el 3 (habitación de hotel) eran el
  mismo caso: se unen en 915. Quedan seis descartes.
- **`/airbnb`:** la tarjeta tiene tamaño fijo en todos los pasos.
- **Portada:** se agranda sola para llenar la pantalla (hasta 1,8×) en vez de quedarse pequeña.
