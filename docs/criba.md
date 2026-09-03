# Criba de los datos

**Generado por `pipeline/generar_criba.py` — no editar a mano.** Los recuentos se leen de los CSV
que el pipeline acaba de producir, asi que no pueden afirmar una criba que ya no ocurre.

Complementa a `docs/linaje.md`: aquel dibuja que fichero alimenta a que script, este dibuja que le
pasa a cada registro.

## Airbnb: que anuncios quedan sujetos a la eliminacion de 2028

Un anuncio puede incumplir varias condiciones a la vez y **solo se cuenta en la primera**. El orden
va de lo estructural a lo circunstancial: primero si la ley le alcanza, despues si sigue vivo, y al
final si hay precio.

```mermaid
flowchart TD
  entrada["<b>15,406 anuncios</b><br>Inside Airbnb 2026-06-24"]
  d0{"¿Declara licencia de hotel,<br>albergue o apartament turistic?"}
  x0["Alojamiento reglado<br>cuenta en el lado hotelero<br><b>897</b>"]
  s0["14,509 siguen"]
  entrada --> d0
  d0 -->|"si"| x0
  d0 -->|"no"| s0
  d1{"¿Cede la vivienda entera?"}
  x1["Habitaciones sueltas<br>un HUT se cede completo<br><b>3,739</b>"]
  s1["10,770 siguen"]
  s0 --> d1
  d1 -->|"no"| x1
  d1 -->|"si"| s1
  d2{"¿Estancia minima<br>de 31 noches o menos?"}
  x2["Alquiler de temporada<br>fuera del alcance de la ley<br><b>1,848</b>"]
  s2["8,922 siguen"]
  s1 --> d2
  d2 -->|"no"| x2
  d2 -->|"si"| s2
  d3{"¿Ha tenido huespedes<br>en los ultimos 12 meses?"}
  x3["Apagados<br>sin resenas y sin calendario<br><b>802</b>"]
  s3["8,120 siguen"]
  s2 --> d3
  d3 -->|"no"| x3
  d3 -->|"si"| s3
  d4{"¿Es la primera vez que<br>aparece esta HUTB?"}
  x4["El mismo piso ya contado<br>se conserva la copia con precio<br><b>769</b>"]
  s4["7,351 siguen"]
  s3 --> d4
  d4 -->|"no"| x4
  d4 -->|"si"| s4
  d5{"¿Tiene precio, o un anuncio<br>hermano del que deducirlo?"}
  x5["Sin tarifa recuperable<br><b>67</b>"]
  s5["7,284 siguen"]
  s4 --> d5
  d5 -->|"no"| x5
  d5 -->|"si"| s5
  final(["<b>Viviendas de uso turistico<br>sujetas a la ley</b><br>7,284"])
  s5 --> final
  classDef descarte fill:#f6e6e6,stroke:#b06060;
  classDef meta fill:#e2f0e2,stroke:#4a8a4a;
  class x0,x1,x2,x3,x4,x5 descarte;
  class final meta;
```

| Paso | Descartados | Quedan |
|---|---:|---:|
| Anuncios de partida | — | 15,406 |
| regimen no vut | −897 | 14,509 |
| no es cesion entera | −3,739 | 10,770 |
| estancia de 32 noches | −1,848 | 8,922 |
| sin actividad | −802 | 8,120 |
| repeticion de vivienda | −769 | 7,351 |
| sin precio aprovechable | −67 | 7,284 |
| **Sujetos a la ley de 2028** | | **7,284** |

Los descartados no se borran: quedan en `data/gold/airbnb_excluidos.csv` con su `motivo_exclusion`,
de modo que cualquiera puede rehacer el recuento con otro criterio sin volver al dato crudo.
