# Página de Airbnb: de 15.406 anuncios a 6.834 viviendas

**Fecha:** 2026-09-16 12:40
**Tipo:** Feature
**Requisitos:** paso 3 de `web-checklist.md` (el eje del proyecto)

## Qué se hizo

Ruta `/airbnb` con el embudo completo y una barra de 0 a 6 filtros. Al arrastrarla bajan los
números y aparece qué se acaba de descartar y por qué.

En cada paso se ven **anuncios y plazas**. Solo con anuncios, descartar 3.083 habitaciones sueltas
y 901 hoteles parece comparable, y en plazas no lo es: una habitación aloja a dos personas y un
hotel a doscientas.

| Paso | Descarta | Quedan |
|---|---|---|
| — | — | 15.406 · 56.420 plazas |
| 1 · Declara hotel, albergue o apartament turístic | −901 | 14.505 |
| 2 · Habitación suelta sin licencia | −3.083 | 11.422 |
| 3 · Habitación de hotel | −14 | 11.408 |
| 4 · Estancia mínima de más de 31 noches | −1.848 | 9.560 |
| 5 · Sin reseñas desde septiembre de 2025 | −876 | 8.684 |
| 6 · Repite nombre y anfitrión | −1.850 | **6.834 · 30.067 plazas** |

La página cierra diciendo lo que la cifra **no** es: el registro oficial tiene 24.075 licencias con
61.899 plazas, y esto es solo lo anunciado en Airbnb.

## El dato

`export_mapa.py` gana `exportar_criba_airbnb()` → `criba_airbnb.json`. Los pasos se declaran en
`PASOS_CRIBA` con la misma clave que el `motivo_exclusion` del CSV, y **el export falla si aparece
un motivo sin paso declarado**: si la criba cambia y este listado no, los números saldrían mal en
silencio, que es peor que un error.

El orden es el mismo que el de `criba.md`, y no es decorativo: un anuncio puede fallar varias
condiciones a la vez y solo se cuenta en la primera, así que moverlo cambia los números de cada
paso sin cambiar el total.

## Un fallo de formato, de paso

`toLocaleString("es")` deja 2390 sin punto: el español no agrupa los números de cuatro cifras. En
una columna donde al lado hay «9.098», eso se lee como un número más pequeño de lo que es. Se
fuerza `useGrouping: "always"` aquí y en el KPI «Sin sitio» del mapa, que tenía el mismo defecto.

## Rediseño a tarjetas (misma fecha, 13:20)

La primera versión listaba los seis descartes uno debajo de otro y la página scrolleaba. Ahora:

- **Una tarjeta cada vez.** El texto de por qué no compite con los otros cinco.
- **Sin scroll de página a partir de tableta** (`sm:h-dvh sm:overflow-hidden`). En móvil se deja
  fluir: forzar la altura ahí recortaría el texto, que es lo único que la página tiene que contar.
  Si alguna tarjeta creciera, scrollea ella sola dentro de su marco, no la página.
- **Flechas ‹ ›, puntos de índice y flechas del teclado.** Los puntos dicen cuántas tarjetas hay,
  en cuál estás y cuáles ya has pasado (en rojo).
- Las cifras y la barra se quedan arriba, fijas: son lo que cambia al pasar cada tarjeta.
- El aviso de «no son todas las de Barcelona» aparece **en la última tarjeta**, que es donde la
  cifra final ya está a la vista y puede malinterpretarse.

## Verificación

```
export_mapa.py  →  criba_airbnb {'pasos': 6, 'inicio': 15406, 'final': 6834}
tsc --noEmit    →  sin errores
```

En local, sin errores de consola. A 1280x860, `scrollHeight === innerHeight`: no hay scroll de
página, ni en la primera tarjeta ni en la última, que es la que más texto lleva. La tarjeta tampoco
scrollea por dentro a esa altura. El botón «Siguiente» avanza (15.406 → 14.505) y se desactiva en
la última, donde quedan 6.834 · 30.067 y 8.572 descartados (56%).

**No se ha ejecutado el build de producción.**
