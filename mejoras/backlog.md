# Backlog de mejoras

<!-- Ideas de mejora que no entran en el sprint actual pero que no queremos perder.
     No es un compromiso, es un repositorio de ideas.
     Añadir una entrada cada vez que surja una idea durante el desarrollo. -->

---

## Formato de entrada

```
### [MEJORA-XX] Título de la idea
**Área:** Frontend / Backend / UX / Infraestructura / Negocio
**Prioridad estimada:** Alta / Media / Baja
**Origen:** De dónde salió la idea (conversación, feedback de usuario, etc.)

Descripción breve de la mejora y por qué aportaría valor.
```

---

### [MEJORA-01] Banderas booleanas para los toggles de la web
**Area:** Frontend / Backend
**Prioridad estimada:** Media
**Origen:** conversacion del 2026-09-04, al publicar la capacidad latente

`airbnb_para_web.csv` ya trae tres columnas booleanas utiles para filtrar en la web:
`precio_plaza_es_estimado` (observado frente a estimado), `precio_recortado` y
`consta_en_registro`. `airbnb_capacidad_latente.csv` tambien tiene `consta_en_registro`, pero ahi
vale `True` en las 293 --es el filtro que las define-- asi que no discrimina nada.

Falta decidir que se quiere poder encender y apagar en el dashboard y crear las banderas que no
existan, en el cuaderno y no en el frontend: si el criterio vive en el JavaScript, deja de estar
documentado y deja de poder auditarse.

Candidatas evidentes segun lo que ya se calcula: `es_operador` (anfitrion con N o mas anuncios),
`estancia_corta` (tramo de 1-6 noches), `licencia_por_encima_del_maximo` (los 889 que declaran un
numero mayor que HUTB-80024) y `latente_reciente` (dejo de anunciarse en 2024 o despues).

Hacerlo mientras el cuaderno esta cargado es barato; reconstruir el estado mas adelante, no.
