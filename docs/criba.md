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
  x0["Alojamiento reglado<br>cuenta en el lado hotelero<br><b>901</b>"]
  s0["14,505 siguen"]
  entrada --> d0
  d0 -->|"si"| x0
  d0 -->|"no"| s0
  d1{"¿Cede la vivienda entera,<br>o declara un HUTB?"}
  x1["Habitaciones sueltas sin licencia<br>no es lo que la ley elimina<br><b>3,083</b>"]
  s1["11,422 siguen"]
  s0 --> d1
  d1 -->|"no"| x1
  d1 -->|"si"| s1
  d2{"¿Es habitacion de hotel?"}
  x2["Habitacion de establecimiento<br>se analiza en el otro lado<br><b>14</b>"]
  s2["11,408 siguen"]
  s1 --> d2
  d2 -->|"si"| x2
  d2 -->|"no"| s2
  d3{"¿Estancia minima<br>de 31 noches o menos?"}
  x3["Alquiler de temporada<br>fuera del alcance de la ley<br><b>1,848</b>"]
  s3["9,560 siguen"]
  s2 --> d3
  d3 -->|"no"| x3
  d3 -->|"si"| s3
  d4{"¿Tiene resenas<br>desde septiembre de 2025?"}
  x4["Sin huespedes recientes<br>no vende<br><b>876</b>"]
  s4["8,684 siguen"]
  s3 --> d4
  d4 -->|"no"| x4
  d4 -->|"si"| s4
  d5{"¿Es la primera vez que<br>aparece este anuncio?"}
  x5["Mismo nombre y anfitrion<br>ya contado<br><b>1,850</b>"]
  s5["6,834 siguen"]
  s4 --> d5
  d5 -->|"no"| x5
  d5 -->|"si"| s5
  final(["<b>df_v2<br>viviendas de uso turistico</b><br>6,834"])
  s5 --> final
  classDef descarte fill:#f6e6e6,stroke:#b06060;
  classDef meta fill:#e2f0e2,stroke:#4a8a4a;
  class x0,x1,x2,x3,x4,x5 descarte;
  class final meta;
```

| Paso | Descartados | Quedan |
|---|---:|---:|
| Anuncios de partida | — | 15,406 |
| alojamiento reglado | −901 | 14,505 |
| habitacion sin hutb | −3,083 | 11,422 |
| habitacion de hotel | −14 | 11,408 |
| estancia de 32 noches | −1,848 | 9,560 |
| sin actividad desde 09 2025 | −876 | 8,684 |
| duplicado de nombre y anfitrion | −1,850 | 6,834 |
| **Sujetos a la ley de 2028** | | **6,834** |

Los descartados no se borran: quedan en `data/gold/airbnb_excluidos_web.csv` con su `motivo_exclusion`,
de modo que cualquiera puede rehacer el recuento con otro criterio sin volver al dato crudo.
