# Diccionario de datos

Cada fichero de `data/` (salvo `raw/`, que no se versiona): filas, columnas y qué script lo
produce. Generado por `pipeline/generar_diccionario.py`; no se edita a mano.

## bronze

| Fichero | Filas | Lo produce | Columnas / claves |
|---|---:|---|---|
| `adr_estacionalidad.csv` | 48 | `bronze/preparar_adr_por_categoria.py` | categoria_oficial, mes, factor, anyos |
| `adr_por_categoria.csv` | 636 | `bronze/preparar_adr_por_categoria.py` | categoria_oficial, fecha, anyo, mes, adr |
| `airbnb_anuncios.csv` | 15.406 | `bronze/unificar_airbnb.py` | id, name, host_id, host_name, calculated_host_listings_count, neighbourhood_group, neighbourhood, latitude, longitude, room_type, property_type, accommodates, bedrooms, beds, minimum_nights, precio_anuncio, precio_por_plaza, availability_365, number_of_reviews, number_of_reviews_ltm, last_review, review_scores_rating, license |
| `geocodificacion_icgc.csv` | 14.474 | `sources/geocodificar_registros.py` | licencia_id, origen, municipio, direccion_consultada, lat, lon, etiqueta_icgc, geocodificado, en_ciudad |
| `geocodificacion_verificada.csv` | 12.982 | `bronze/asignar_municipio.py` | licencia_id, origen, municipio, direccion_consultada, lat, lon, etiqueta_icgc, geocodificado, en_ciudad, municipio_poligono, municipio_coincide |
| `hoteles_geocodificados.csv` | 309 | `sources/geocodificar_hoteles.py` | licencia_id, nombre_comercial, direccion_consultada, lat, lon, etiqueta_icgc, geocodificado |
| `hoteles_nuevos_bcn.csv` | 4 | `—` | nombre, marca, direccion, habitaciones, categoria, apertura, tipo, lat, lon, precision, fuente, url, consultado |
| `hoteles_y_apartaments_unificados.csv` | 1.563 | `—` | licencia_id, nombre_comercial, municipio, codi_ine, comarca, tipo_via, nombre_via, numero, codigo_postal, categoria, plazas, habitaciones, nif, razon_social, tipo, es_persona_fisica, titular_id, lat, lon, metodo_match, similitud_nombre, piso, puerta, coordenada_compartida, nivel_geo |
| `municipios_provincia_barcelona.geojson` | 311 | `bronze/reparar_geometria_municipios.py` | GmlID, OBJECTID, CODIMUNI, NOMMUNI, NOMMUNIIND, CAPMUNI, CAPMUNIIND, AREAM5000, CODICOMAR, NOMCOMAR, CAPCOMAR, CAPCOMIND, CODIVEGUE, NOMVEGUE, CAPVEGUE, CODIPROV, NOMPROV, CAPPROV, SHAPE_Length, SHAPE_Area |
| `serie_ine_barcelona.csv` | 926 | `sources/descargar_ine_barcelona.py` | fuente, serie, unidad, anyo, periodo, provisional, fecha, valor, mes |
| `serie_vut_trimestral.csv` | 30 | `sources/descargar_serie_vut.py` | trimestre, anyo, stock, altas, bajas, variacion_neta |
| `titulares.csv` | 3.107 | `bronze/unificar_registros.py` | nif, titular_id |
| `vut_unificados.csv` | 24.075 | `—` | licencia_id, nombre_comercial, municipio, codi_ine, comarca, tipo_via, nombre_via, numero, piso, puerta, codigo_postal, categoria, nif, razon_social, tipo, es_persona_fisica, titular_id, lat, lon, plazas, distrito, barrio, metodo_match, coordenada_compartida, nivel_geo |

## gold

| Fichero | Filas | Lo produce | Columnas / claves |
|---|---:|---|---|
| `airbnb_capacidad_latente.csv` | 293 | `—` | id, name, host_id, host_name, calculated_host_listings_count, neighbourhood_group, neighbourhood, latitude, longitude, room_type, property_type, accommodates, bedrooms, beds, minimum_nights, precio_anuncio, precio_por_plaza, availability_365, number_of_reviews, number_of_reviews_ltm, last_review, review_scores_rating, license, price, licencia_regional, categoria_licencia, licencia_norm, prefijo, consta_en_registro, estado_licencia, motivo_estado, last_review_dt, motivo_exclusion |
| `airbnb_excluidos_web.csv` | 10.421 | `gold/separar_sin_registro.py` | id, name, host_id, host_name, calculated_host_listings_count, neighbourhood_group, neighbourhood, latitude, longitude, room_type, property_type, accommodates, bedrooms, beds, minimum_nights, precio_anuncio, precio_por_plaza, availability_365, number_of_reviews, number_of_reviews_ltm, last_review, review_scores_rating, license, price, licencia_regional, categoria_licencia, licencia_norm, prefijo, consta_en_registro, estado_licencia, motivo_estado, last_review_dt, motivo_exclusion |
| `airbnb_para_web.csv` | 4.985 | `gold/separar_sin_registro.py` | id, name, host_id, host_name, calculated_host_listings_count, neighbourhood_group, neighbourhood, latitude, longitude, room_type, property_type, accommodates, bedrooms, beds, minimum_nights, precio_anuncio, precio_por_plaza, availability_365, number_of_reviews, number_of_reviews_ltm, last_review, review_scores_rating, license, price, licencia_regional, categoria_licencia, licencia_norm, prefijo, consta_en_registro, estado_licencia, motivo_estado, last_review_dt, tipo_cesion, factor_temporada, precio_plaza_anual, banda_plaza, tramo_estancia, precio_plaza_recortado, precio_recortado, precio_plaza_estimado |
| `alojamientos_reglados.csv` | 1.563 | `gold/preparar_alojamientos_provincia.py` | licencia_id, nombre_comercial, tipo, municipio, codi_ine, barrio, categoria, estrellas, tipo_alojamiento, plazas, habitaciones, titular_id, lat, lon, precision, precio_noche_final, banda_precio, precio_plaza, banda_plaza, origen_precio, categoria_ine |
| `calidad/flujos_banda_resumen.csv` | 48 | `—` | variante, origen, destino, turistas |
| `hoteles_bcn.csv` | 768 | `gold/preparar_hoteles_bcn.py` | licencia_id, nombre_comercial, razon_social, tipo, tipo_alojamiento, subtipo, categoria, estrellas, cadena, es_cadena, plazas, habitaciones, codigo_postal, barrio, distrito, nombre_via, numero, lat, lon, origen_coord, distancia_centro_km, categoria_ine, precio_noche, origen_precio, duplicado_probable |
| `restauracion_bcn.csv` | 9.465 | `gold/preparar_restauracion_bcn.py` | local_id, nombre, tipo_local, distrito, barrio, codigo_barrio, calle, numero, direccion, latitud, longitud, fecha_revision, local_identificado |

## exports

| Fichero | Filas | Lo produce | Columnas / claves |
|---|---:|---|---|
| `geo/barrios.geojson` | 75 | `—` | barrio, distrito |
| `geo/peuat.geojson` | 12 | `—` | zona |
| `mapa/barrios_hoy.json` | 73 | `—` | lista de dict |
| `mapa/criba_airbnb.json` | — | `—` | inicio, pasos, partida |
| `mapa/dashboard.json` | — | `—` | hoteles, pisos |
| `mapa/flujo.json` | — | `—` | turistas, km, distancia, bandas, barrios |
| `mapa/hoteles_pagina.json` | — | `—` | barrios, categorias, ocupacion_mensual, ocupacion_bandas, ocupacion, nuevos |
| `mapa/licencias.json` | — | `—` | pisos_estado, registro_detalle, registro, con_anuncio, solo_descartados, sin_anuncio, casadas |
| `mapa/parametros.json` | — | `—` | ocupacion_hotel_habitaciones, ocupacion_hotel_plazas, ocupacion_piso, radio_comida_m |
| `mapa/puntos_hoteles.json` | 750 | `—` | lista de dict |
| `mapa/puntos_pisos.json` | 4.985 | `—` | lista de list |
| `mapa/puntos_restaurantes.json` | 9.465 | `—` | lista de dict |
| `mapa/restauracion_pagina.json` | — | `—` | locales, con_turistas, hoy, en_2028, ganan, pierden, marcas, locales_top, barrios_mas, barrios_menos |
| `mapa/turistas.json` | — | `—` | ine, dataset |
