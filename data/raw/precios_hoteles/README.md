# precios_hoteles — precios raspados de portales de reserva

Deja aquí la exportación del scraper (JSON o CSV). `pipeline/transform/cruzar_precios_hoteles.py`
lee todo lo que encuentre en esta carpeta y lo cruza con el registro oficial.

El script busca por sí solo los campos habituales bajo distintos nombres (`name`/`hotelName`,
`latitude`/`lat`, `price`/`pricePerNight`...), así que no hace falta renombrar nada.

**Cuantos más campos traiga la exportación, mejor cruza.** Lo que de verdad importa:

- `name` — imprescindible
- `latitude` / `longitude` — sin coordenadas el cruce cae al método por nombre, que es frágil:
  "Catalonia Ramblas" y "Catalonia Plaza" se parecen mucho y son hoteles distintos
- `price` + `currency`

## Sobre la procedencia

Estos precios salen de raspar un portal de reservas, cuyos términos lo prohíben. Sirven para
explorar y modelar en local. **Para publicar cifras en el dashboard hace falta una fuente
citable** — el ADR del INE es la referencia oficial (ver `docs/architecture.md`).

Como todo `data/raw/`, esta carpeta no se versiona.
