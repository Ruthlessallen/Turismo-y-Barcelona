import { readFileSync } from "node:fs";
import { join } from "node:path";

import type { Metadata } from "next";
import { dec } from "@/app/lib/tiposMapa";

export const metadata: Metadata = {
  title: "Fuentes y método",
  description:
    "De dónde sale cada número del mapa: fuentes originales, qué se transforma, por qué, y qué " +
    "no puede decir este análisis.",
};

/** El índice y los títulos salen de aquí, para que no puedan desincronizarse. */
const SECCIONES = [
  { id: "que-lee", titulo: "Qué lee la web" },
  { id: "fuentes", titulo: "Las fuentes originales" },
  { id: "precio", titulo: "De dónde sale un precio" },
  { id: "decisiones", titulo: "Las decisiones que mueven el resultado" },
  { id: "modelo", titulo: "Lo que calcula la web" },
  { id: "privacidad", titulo: "Lo que nunca se publica" },
  { id: "limites", titulo: "Lo que esto no puede decir" },
];

/**
 * Las cifras de esta página salen de los mismos JSON que pintan el resto de la web, leídos al
 * construir. Así no hay un segundo sitio donde escribirlas a mano ni que se pueda desfasar.
 */
const leer = (f: string) => JSON.parse(readFileSync(join(process.cwd(), "public/data/mapa", f), "utf-8"));
const n = (v: number) => v.toLocaleString("es", { useGrouping: "always" });

export default function PaginaFuentes() {
  const dash = leer("dashboard.json");
  const par = leer("parametros.json");
  const lic = leer("licencias.json");
  const criba = leer("criba_airbnb.json");
  const hp = leer("hoteles_pagina.json");
  const rp = leer("restauracion_pagina.json");
  const fl = leer("flujo.json");
  const hoteles: { cat_ine: string | null; adr: number | null; banda: string | null; hab: number | null }[] =
    leer("puntos_hoteles.json");
  const paso = (clave: string): number => criba.pasos.find((x: { clave: string }) => x.clave === clave).descartados;
  const nPisos: number = dash.pisos.total;
  const [ocPisoBaja, ocPisoAlta] = par.ocupacion_piso as [number, number];
  const obraNueva = hp.nuevos
    .filter((h: { tipo: string }) => h.tipo === "Obra nueva")
    .reduce((t: number, h: { habitaciones: number | null }) => t + (h.habitaciones ?? 0), 0);
  const categorias = Object.values(
    hoteles.reduce((acc: Record<string, { cat: string; adr: number | null; banda: string | null; hoteles: number; hab: number }>, h) => {
      const k = h.cat_ine ?? "Sin categoría";
      acc[k] ??= { cat: k, adr: h.adr, banda: h.banda, hoteles: 0, hab: 0 };
      acc[k].hoteles++; acc[k].hab += h.hab ?? 0;
      return acc;
    }, {}));
  const libres = Math.round(hp.ocupacion.habitaciones * (1 - par.ocupacion_hotel_habitaciones / 100));
  return (
    <main className="min-h-full bg-[#faf9f7] text-[#24231f]">
      <header className="border-b border-[#e3e0da] bg-white">
        <div className="mx-auto max-w-5xl px-5 py-6 sm:px-8">
          <h1 className="mt-3 text-2xl font-semibold tracking-tight">Fuentes y método</h1>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-[#52514e]">
            De dónde sale cada número que se publica, quién lo publica, qué le hacemos por el camino
            y por qué. Escrito para que se pueda rehacer el recorrido sin preguntarnos nada.
          </p>
        </div>
      </header>

      <div className="mx-auto max-w-5xl gap-10 px-5 py-8 sm:px-8 lg:flex">
        <nav className="mb-8 shrink-0 lg:sticky lg:top-8 lg:mb-0 lg:h-fit lg:w-56">
          <h2 className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-[#52514e]">
            En esta página
          </h2>
          <ol className="space-y-1.5 text-[13px]">
            {SECCIONES.map((s, i) => (
              <li key={s.id} className="flex gap-2">
                <span className="tabular-nums text-[#a3a09b]">{i + 1}</span>
                <a href={`#${s.id}`} className="text-[#52514e] hover:text-[#24231f] hover:underline">
                  {s.titulo}
                </a>
              </li>
            ))}
          </ol>
        </nav>

        <div className="min-w-0 flex-1 space-y-10">
          <Seccion id="que-lee" numero={1} titulo="Qué lee la web">
            <P>
              La web es estática: el navegador solo descarga ficheros ya calculados. Todo lo demás
              ocurre antes, en el pipeline.
            </P>
            <Tabla
              cabeceras={["Fichero", "Qué contiene", "Lo produce"]}
              filas={[
                ["barrios.geojson, peuat.geojson", "Los 73 barrios de la ciudad y las 12 zonas del PEUAT", "preparar_geometria_web.py"],
                ["puntos_pisos.json", `${n(nPisos)} pisos: posición, plazas, dormitorios, precio de la noche y banda`, "export_mapa_limpio.py"],
                ["puntos_hoteles.json", `${n(dash.hoteles.total)} hoteles: habitaciones, plazas, categoría INE, banda y sociedad titular`, "export_mapa_limpio.py"],
                ["puntos_restaurantes.json", `${n(rp.locales)} locales: clientes potenciales hoy y en 2028`, "export_mapa_limpio.py"],
                ["barrios_hoy.json, dashboard.json", "Las cifras de cada barrio y las de la portada", "export_mapa_limpio.py"],
                ["turistas.json, flujo.json", "Turistas frente al INE; distancia, bandas y barrios que suben y bajan", "export_mapa_limpio.py"],
                ["hoteles_pagina.json, restauracion_pagina.json, licencias.json", "Lo que pintan esas tres páginas", "export_mapa_limpio.py"],
                ["criba_airbnb.json", "Cuántos anuncios caen en cada paso del embudo de Airbnb", "export_criba.py"],
                ["parametros.json", "Las ocupaciones que usa el modelo: una sola fuente para toda la web", "export_mapa_limpio.py"],
              ]}
            />
          </Seccion>

          <Seccion id="fuentes" numero={2} titulo="Las fuentes originales">
            <Fuente
              nombre="Registre de Turisme de Catalunya"
              quien="Generalitat de Catalunya"
              fecha="Descargado en agosto de 2026"
            >
              <P>
                El censo oficial de alojamiento de toda la provincia: 27.180 registros, de los
                cuales 23.975 viviendas de uso turístico, 1.442 hoteles y 120 apartaments
                turístics. Es la única fuente que identifica al titular. No trae coordenadas, y en
                las viviendas de uso turístico tampoco plazas.
              </P>
            </Fuente>

            <Fuente
              nombre="Open Data BCN"
              quien="Ajuntament de Barcelona · licencia CC BY 4.0"
              fecha="Serie de licencias hasta 2026 · censo de hoteles congelado en 2023"
            >
              <P>
                Aporta las coordenadas reales y las plazas de las viviendas turísticas de la ciudad,
                y el barrio de cada hotel. No se solapa con el Registre: cada fuente tiene campos que
                la otra no. Se cruzan por número de registro oficial —que es una clave real, no una
                coincidencia de nombres— y lo que queda suelto, por dirección normalizada y solo
                cuando la correspondencia es exacta. Cualquier ambigüedad se deja sin cruzar.
              </P>
            </Fuente>

            <Fuente
              nombre="Inside Airbnb"
              quien="Proyecto independiente que publica volcados de la plataforma"
              fecha="Volcado del 24 de junio de 2026"
            >
              <P>
                {n(criba.inicio.anuncios)} anuncios de la ciudad, con precio, capacidad declarada y reseñas. Es{" "}
                <em>un anuncio</em>, no una vivienda, y no es el registro oficial: cubre lo que se
                comercializa en una plataforma concreta un día concreto. La propia fuente desplaza
                cada anuncio hasta 150 metros a propósito: el punto del mapa es esa posición
                desplazada, no la dirección de la vivienda.
              </P>
              <P>
                De esos {n(criba.inicio.anuncios)} se llega a <strong>{n(nPisos)} viviendas</strong> descartando, por este
                orden: alojamiento ya reglado, con sus habitaciones de hotel ({n(paso("alojamiento_reglado"))}), habitaciones
                sueltas sin licencia ({n(paso("habitacion_sin_hutb"))}), alquiler de temporada de más de 31 noches ({n(paso("estancia_de_32_noches"))}),
                anuncios sin reseñas desde septiembre de 2025 ({n(paso("sin_actividad_desde_09_2025"))}), repeticiones del mismo anuncio
                ({n(paso("duplicado de nombre y anfitrion"))}) y, al final, los que no tienen registro acreditado ({n(paso("sin_registro_acreditado"))}).
              </P>
              <Aviso>
                El registro oficial de la ciudad tiene {n(lic.registro.licencias)} licencias con {n(lic.registro.plazas)} plazas.
                Este análisis mueve {n(lic.pisos_estado.con_registro.plazas)} plazas, las de las {n(nPisos)} viviendas con
                registro acreditado anunciadas hoy en Airbnb. Otras {n(lic.sin_anuncio.licencias)} licencias, con{" "}
                {n(lic.sin_anuncio.plazas)} plazas, no tienen ningún anuncio, y {n(paso("sin_registro_acreditado"))} pisos
                anunciados no tienen registro acreditado: no sabemos nada de ellos. Están contados en la página de Airbnb.
              </Aviso>
            </Fuente>

            <Fuente
              nombre="INE · Encuesta de Ocupación Hotelera"
              quien="Instituto Nacional de Estadística"
              fecha="Últimos 60 meses, punto turístico Barcelona"
            >
              <P>
                Tres usos. Uno: la <strong>ocupación de partida</strong> —el {dec(par.ocupacion_hotel_habitaciones)}% de media
                anual, por habitaciones— que descuenta las habitaciones ya vendidas antes de repartir
                a nadie. Dos: el <strong>ADR por categoría</strong> (ingreso medio por habitación
                ocupada, del Portal de Dades del Ajuntament sobre la misma encuesta), que es el único
                precio de hotel del proyecto. Tres: la <strong>estacionalidad</strong>, trece años de
                serie, que lleva el precio de Airbnb a equivalente anual.
              </P>
              <P>
                La ocupación es <em>por habitaciones</em> y no por plazas ({dec(par.ocupacion_hotel_plazas)}%), porque la
                habitación es lo que limita a un hotel. Las dos salen de la misma encuesta y miden
                cosas distintas.
              </P>
              <P>
                Su límite: es un agregado por categoría de la ciudad. Sirve para el nivel y la
                tendencia, nunca para atribuir un precio a un hotel concreto.
              </P>
            </Fuente>

            <Fuente
              nombre="Censo comercial municipal"
              quien="Ajuntament de Barcelona"
              fecha="Trabajo de campo de 2023 y 2024"
            >
              <P>
                {n(rp.locales)} locales de restauración de la ciudad. Se retiran 14 locales repetidos: el mismo nombre a menos de 10 metros,
                que es un edificio con dos accesos dado de alta dos veces. Se usa el censo y no OpenStreetMap porque OSM se deja fuera un 26% de
                la restauración de Barcelona. No existe un censo equivalente de 2026; se comprobó.
              </P>
            </Fuente>

            <Fuente
              nombre="Precios de hotel"
              quien="INE · Portal de Dades del Ajuntament de Barcelona"
              fecha="ADR mensual por categoría, 2013 – julio de 2026"
            >
              <P>
                No se usa ningún precio recogido de portales de reserva: se probaron y se
                descartaron. Cada hotel recibe el ADR medio de los últimos 12 meses de su categoría
                oficial. Detalle en «De dónde sale un precio».
              </P>
            </Fuente>

            <Fuente
              nombre="Hoteles anunciados"
              quien="Prensa del sector: Hosteltur, ON Economia, EjePrime"
              fecha="Recopilado a mano el 5 de octubre de 2026"
            >
              <P>
                No es un registro oficial: no existe un dataset de hoteles previstos. Son {hp.nuevos.length}{" "}
                entradas, cada una con su enlace en la página de hoteles. <strong>Casi todo es
                reforma o cambio de gestión de hoteles que ya existen</strong>: de obra nueva hay {n(obraNueva)}{" "}
                habitaciones, el {dec((obraNueva / hp.ocupacion.habitaciones_absorbidas) * 100)}% de las {n(hp.ocupacion.habitaciones_absorbidas)} que piden los pisos.
              </P>
            </Fuente>

            <Fuente
              nombre="PEUAT · Pla especial urbanístic d'allotjaments turístics"
              quien="Ajuntament de Barcelona · aprobado definitivamente el 23 de diciembre de 2021"
              fecha="Zonas del Open Data BCN; reglas según prensa y despachos jurídicos"
            >
              <P>
                El mapa de <em>Hoteles</em> pinta las 12 zonas por su código y las agrupa por número.
                Según el plan: la <strong>zona 1</strong> no admite establecimientos nuevos; la{" "}
                <strong>zona 2</strong> mantiene el censo (solo se abre sustituyendo uno que cerró);
                la <strong>zona 3</strong> permite crecimiento contenido; la <strong>zona 4</strong> tiene
                regulación propia (Prat Vermell, la Sagrera, el norte del 22@). No está verificado el
                detalle por subzona (3A–3E, 4A–4C) contra el texto del plan, y una propuesta de
                2023 para admitir hoteles «singulares» en las zonas 1 y 2 no consta como aprobada.
                No entra en ningún cálculo: es información sobre el mapa.
              </P>
            </Fuente>

            <Fuente
              nombre="Geometría"
              quien="Institut Cartogràfic i Geològic de Catalunya"
              fecha="75 barrios de la ciudad y 12 zonas del PEUAT"
            >
              <P>
                Antes de llegar al navegador se reparan dos barrios con la geometría mal cerrada y se
                simplifica el contorno, porque a la escala de una ciudad dos vértices
                separados por 5 metros caen en el mismo píxel. Si al simplificar la superficie total cambiara más de un 1%, el proceso se detiene.
              </P>
            </Fuente>
          </Seccion>

          <Seccion id="precio" numero={3} titulo="De dónde sale un precio">
            <P>
              <strong>Un hotel no tiene precio propio.</strong> Recibe el ADR oficial de su
              categoría (INE, media de los últimos 12 meses) y de ahí salen sus dos bandas. Todos los
              hoteles de una categoría comparten banda.
            </P>
            <Tabla
              cabeceras={["Categoría oficial", "Hoteles", "Habitaciones", "ADR por habitación", "Banda por plaza"]}
              filas={categorias.map((c) => [
                c.cat === "Sin categoría" ? "Sin categoría (sin banda)" : c.cat,
                n(c.hoteles), n(c.hab), c.adr == null ? "—" : `${n(c.adr)} €`, c.banda ?? "—",
              ])}
            />
            <P>
              La banda por plaza divide ese ADR entre las plazas por habitación de la categoría
              (mediana), con cortes en 40, 70 y 120 € por plaza: es la única escala en la que un piso
              entero y una habitación de hotel se comparan. Los hostales y pensiones van con «1 y 2
              estrellas», que es donde el INE los incluye: <strong>es un supuesto</strong>. Los
              apartaments turístics y lo «sense categoritzar» no tienen categoría oficial y quedan
              fuera del reparto.
            </P>
            <Aviso>
              Consecuencia: la banda es una propiedad de la categoría, no del hotel. Un 3 estrellas
              de lujo y uno modesto salen igual. Y con estos cortes no hay hoteles en la banda €.
            </Aviso>
            <P>
              <strong>Un piso lleva el precio que anuncia en Airbnb</strong>, tal como lo publica la
              fuente, sin corregir limpieza ni comisión, y llevado a equivalente anual con la
              estacionalidad hotelera del INE.
            </P>
          </Seccion>

          <Seccion id="decisiones" numero={4} titulo="Las decisiones que mueven el resultado">
            <P>
              Cada una de estas es un sitio donde el resultado depende de un criterio nuestro y no del
              dato. No son defectos: son lo que hace falta para poder decir algo. El defecto sería
              tomarlas y no contarlas.
            </P>

            <Decision titulo="Dos unidades, y cada una para una pregunta">
              Para <strong>cuánto cuesta</strong>, la plaza: un piso para cuatro a 221 € y una
              habitación doble a 64 € no se comparan, pero 54 € y 43 € por plaza, sí. Para{" "}
              <strong>si cabe la gente</strong>, la habitación: una plaza libre de hotel suele ser
              la segunda cama de una habitación ya vendida, no se vende aparte, y un grupo de cuatro
              no cabe en ella.
            </Decision>

            <Decision titulo="La ocupación de los pisos turísticos se estima">
              No existe ninguna estadística pública que diga cuántas noches se alquila un piso
              turístico. Se calcula por dos vías que no comparten supuestos —el calendario del
              anuncio y el recuento de reseñas— y dan <strong>{dec(ocPisoBaja)}% y 38,8%</strong>. Que coincidan
              es lo que la hace publicable. Consecuencia: los {n(nPisos)} pisos no alojan a {n(lic.pisos_estado.con_registro.plazas)}{" "}
              personas cada noche, sino a <strong>{n(fl.turistas)}</strong>.
            </Decision>

            <Decision titulo="De los hoteles se publica la categoría y su banda">
              El ADR de una categoría es un dato oficial y se enseña. Pero no es el precio de ningún
              hotel concreto, así que no se enseña como si lo fuera: se enseña la categoría y la
              banda. Los pisos sí llevan el precio que anuncian.
            </Decision>

            <Decision titulo="El precio de Airbnb se publica tal y como se anuncia">
              La fuente no captura la limpieza, la comisión ni los impuestos. No se corrige, porque el
              dato no permite saber quién cobra la limpieza aparte y quién la lleva incluida, y
              aplicar un importe común a todos sería falso para los segundos. Consecuencia asumida:
              en estancias cortas, la banda de Airbnb puede quedar por debajo de lo que se acaba
              pagando.
            </Decision>

            <Decision titulo="La estacionalidad hotelera se aplica a Airbnb">
              El volcado es de junio y se lleva a equivalente anual con el factor de la serie del
              INE, porque no existe una serie estacional del alquiler turístico. Es{" "}
              <strong>el supuesto más frágil de todos</strong>: si el alquiler turístico fuera más
              plano que el hotelero, estaríamos abaratando Airbnb de más.
            </Decision>
          </Seccion>

          <Seccion id="modelo" numero={5} titulo="Lo que calcula la web">
            <P>
              Todo es <strong>un año medio</strong>. Se descartó enseñar también julio: dos fechas a
              la vez confundían más que aclaraban.
            </P>

            <Decision titulo="Un hotel alquila habitaciones; un piso se alquila entero">
              Por eso no se comparan plazas con plazas: se comparan habitaciones de hotel con pisos
              enteros, y la noche de una con la noche del otro. La plaza solo se usa para la banda de
              precio, que es la única escala común.
            </Decision>

            <Decision titulo="Qué hay cerca de un hotel y qué recibe en 2028">
              El radio de 0 a 500 metros cuenta los pisos que tiene cerca, con sus plazas y sus
              habitaciones (un piso, tantas como dormitorios; una si es un estudio). Aparte, para
              cada hotel: sus habitaciones, las ocupadas hoy ({dec(par.ocupacion_hotel_habitaciones)}% por habitaciones, INE) y las
              ocupadas en 2028, que son esas más las que recibe de los pisos según el reparto.
            </Decision>
            <Tabla
              cabeceras={["Toda la ciudad, un año medio", "Habitaciones"]}
              filas={[
                ["Libres en los hoteles", n(libres)],
                ["Que piden los pisos", n(hp.ocupacion.habitaciones_absorbidas)],
                ["Ocupación hotelera", `del ${dec(hp.ocupacion.hoy)}% al ${dec(hp.ocupacion.en_2028)}%`],
              ]}
            />

            <Decision titulo="Cada turista elige hotel por su banda">
              No se mira si prefiere precio o ubicación: se mira la banda. Cada turista va a un
              hotel de su banda, el más cercano con habitaciones libres; si no queda sitio, va a la
              siguiente más cara. La distancia no limita. Resultado: el {dec(fl.bandas.su_banda_pct)}% encuentra
              hotel de su banda, el {dec(fl.bandas.una_mas_pct)}% sube una banda y el {dec(fl.bandas.dos_o_mas_pct)}% sube dos o más. La mediana de
              distancia es de {dec(fl.km.mediana)} km y el 90% llega a menos de {dec(fl.km.p90)} km. Supone la misma ocupación
              en todas las bandas, y los hostales probablemente estén más llenos.
            </Decision>

            <Decision titulo="En restauración solo se mira a quien hoy cocina">
              Los locales ya tienen clientes y eso no se estima. Se mira un solo grupo: el turista que
              hoy elige un piso para ahorrar cocinando y que, en un hotel sin cocina, tiene que salir
              a comer. Cada turista reparte su demanda entre los locales a menos de {par.radio_comida_m} metros de
              donde duerme. Hoy el de piso cuenta la mitad —tiene cocina— y en 2028, ya en un hotel,
              cuenta entero. <strong>La mitad es un supuesto, no un dato</strong>, y de él sale por sí
              solo el aumento total (+{dec((rp.en_2028 / rp.hoy - 1) * 100)}%). Lo que sí aporta el modelo es dónde: {n(rp.ganan)} locales ganan
              y {n(rp.pierden)} pierden. El % es sobre estos clientes, no sobre todos los del local.
            </Decision>

            <Decision titulo="Los turistas se comparan con el INE">
              La página de Turistas pone los viajeros y pernoctaciones del INE frente a los que alojan
              los hoteles de este conjunto. El INE no mide pisos: los pisos se estiman con la
              ocupación de arriba y, a 3 noches de estancia —un supuesto—, se pasa de turistas por
              noche a turistas al año.
            </Decision>
          </Seccion>

          <Seccion id="privacidad" numero={6} titulo="Lo que nunca se publica">
            <P>
              Un hotel o un restaurante es un establecimiento abierto al público y se publica como
              punto. Un piso también sale como punto, pero solo con lo que pinta el mapa: la
              posición que da la fuente (ya desplazada hasta 150 metros), las plazas, los
              dormitorios, el precio y la banda. <strong>Nunca</strong> su identificador, el nombre
              del anuncio, el anfitrión ni el número de licencia. El anfitrión solo aparece agregado:
              por barrio si tiene cinco pisos o más en él, y en la portada los cinco con más pisos de
              la ciudad, siempre que tengan al menos veinte. Es el nombre público en Airbnb: con tantos
              pisos es un operador, aunque el nombre pueda ser el de una persona. Quien tiene uno o
              dos pisos no sale en ningún ranking.
            </P>
            <P>
              Del hotel se publica la sociedad titular, nunca una persona física. Entre los titulares
              del Registre hay personas físicas con nombre y dirección; el pipeline respeta el
              marcador de la fuente, detecta y anula además sus documentos de identidad, y no publica
              el CIF.
            </P>
            <P>
              Los puntos de los pisos están desplazados a propósito por la fuente. Pintarlos como si
              fueran la dirección daría a entender una precisión que no tenemos.
            </P>
          </Seccion>

          <Seccion id="limites" numero={7} titulo="Lo que esto no puede decir">
            <ol className="ml-4 list-decimal space-y-2 text-[14px] leading-relaxed text-[#3a3935] marker:text-[#a3a09b]">
              <li>
                <strong>No cubre las {n(lic.registro.licencias)} licencias de la ciudad</strong>, cubre {n(nPisos)} viviendas
                con registro acreditado anunciadas en Airbnb. {n(lic.sin_anuncio.licencias)} licencias no tienen ningún
                anuncio y {n(paso("sin_registro_acreditado"))} pisos anunciados no tienen registro acreditado: no están.
              </li>
              <li>
                <strong>No sabe qué quiere un turista.</strong> Qué hotel elige, o si prefiere precio
                o ubicación, no está en ningún dato: el reparto es una simulación, no una
                predicción.
              </li>
              <li>
                <strong>No predice qué harán los hoteles ni cuánto subirá el precio.</strong> Depende
                de la estacionalidad, que existiría aunque Airbnb no se fuera; de los turistas que se
                irán a otros municipios; de los pisos que la ley no toca; y de la oferta nueva que
                permita el PEUAT. Los hoteles baratos y los hostales serían los que más presión
                reciben.
              </li>
              <li>
                <strong>Mide un año medio, no doce.</strong> En los picos del verano habrá menos
                hueco en los hoteles.
              </li>
              <li>
                <strong>Da por hecho que el turista sigue viniendo.</strong> Realoja a todos los que
                hoy duermen en esos pisos: nadie se queda en su casa ni se va a otra ciudad.
              </li>
              <li>
                <strong>Un hotel no tiene un precio.</strong> Tiene la banda de su categoría: dos
                hoteles de la misma categoría salen iguales aunque uno cueste el doble.
              </li>
              <li>
                <strong>Lo que factura un piso es un orden de magnitud:</strong> ocupación del
                las noches ocupadas × el precio de la noche. El suelo usa el calendario de cada anuncio (365 − `availability_365`, que es de donde sale el {dec(ocPisoBaja)}%); el techo, el {dec(ocPisoAlta)}% de las 365 noches. No hay dato de facturación.
              </li>
              <li>
                <strong>No hay plazas de los restaurantes</strong>: el censo no las trae. El nombre
                comercial más repetido de un barrio no es la empresa: el censo de la ciudad no trae
                CIF.
              </li>
            </ol>
          </Seccion>
        </div>
      </div>

      <footer className="border-t border-[#e3e0da] bg-white">
        <div className="mx-auto max-w-5xl px-5 py-6 text-[12px] leading-relaxed text-[#52514e] sm:px-8">
          El detalle técnico —el grafo de qué fichero alimenta a qué script, el recuento de cada
          filtro y el diccionario de cada tabla— vive en el repositorio, en{" "}
          <code className="rounded bg-[#f5f4f1] px-1 py-0.5 text-[11px]">docs/</code>.
        </div>
      </footer>
    </main>
  );
}

function Seccion({
  id,
  numero,
  titulo,
  children,
}: {
  id: string;
  numero: number;
  titulo: string;
  children: React.ReactNode;
}) {
  return (
    <section id={id} className="scroll-mt-8">
      <h2 className="flex items-baseline gap-2 text-lg font-semibold tracking-tight">
        <span className="text-[13px] tabular-nums text-[#a3a09b]">{numero}</span>
        {titulo}
      </h2>
      <div className="mt-3 space-y-4">{children}</div>
    </section>
  );
}

function P({ children }: { children: React.ReactNode }) {
  return <p className="text-[14px] leading-relaxed text-[#3a3935]">{children}</p>;
}

/** Una fuente con su procedencia siempre visible: sin eso, el texto es una afirmación sin dueño. */
function Fuente({
  nombre,
  quien,
  fecha,
  children,
}: {
  nombre: string;
  quien: string;
  fecha: string;
  children: React.ReactNode;
}) {
  return (
    <article className="rounded border border-[#e3e0da] bg-white p-4">
      <h3 className="text-[15px] font-semibold tracking-tight">{nombre}</h3>
      <p className="mt-0.5 text-[11px] text-[#52514e]">
        {quien} · {fecha}
      </p>
      <div className="mt-2.5 space-y-2.5">{children}</div>
    </article>
  );
}

function Decision({ titulo, children }: { titulo: string; children: React.ReactNode }) {
  return (
    <div className="border-l-2 border-[#d8d5cf] pl-4">
      <h3 className="text-[14px] font-semibold">{titulo}</h3>
      <p className="mt-1 text-[14px] leading-relaxed text-[#3a3935]">{children}</p>
    </div>
  );
}

function Aviso({ children }: { children: React.ReactNode }) {
  return (
    <p className="rounded border-l-2 border-[#cf4a30] bg-[#fdf3f0] px-3 py-2.5 text-[13px] leading-relaxed text-[#3a3935]">
      {children}
    </p>
  );
}

/** Las tablas se desbordan en móvil antes que estrujar una columna hasta romper la palabra. */
function Tabla({ cabeceras, filas }: { cabeceras: string[]; filas: string[][] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[30rem] border-collapse text-[13px]">
        <thead>
          <tr className="border-b border-[#e3e0da] text-left">
            {cabeceras.map((c) => (
              <th key={c} className="py-2 pr-4 font-semibold text-[#52514e]">
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {filas.map((f) => (
            <tr key={f[0]} className="border-b border-[#efede9] align-top">
              {f.map((celda, i) => (
                <td
                  key={i}
                  className={`py-2 pr-4 ${i === 0 ? "font-medium" : "text-[#52514e]"} ${
                    i === 1 && /^\d/.test(celda) ? "tabular-nums" : ""
                  }`}
                >
                  {celda}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
