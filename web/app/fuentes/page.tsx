import type { Metadata } from "next";
import Link from "next/link";

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
  { id: "modelo", titulo: "El modelo de 2028" },
  { id: "privacidad", titulo: "Lo que nunca se publica" },
  { id: "limites", titulo: "Lo que esto no puede decir" },
];

export default function PaginaFuentes() {
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
              La web es estática: el navegador solo descarga tres ficheros. Todo lo demás ocurre
              antes, en el pipeline.
            </P>
            <Tabla
              cabeceras={["Fichero", "Qué contiene", "Lo produce"]}
              filas={[
                ["barrios.geojson", "Los 75 barrios de la ciudad", "ICGC, simplificado para el navegador"],
                [
                  "sustitucion_2028.json",
                  "64 barrios × 5 escenarios: quién sale, quién llega, quién no cabe",
                  "modelar_sustitucion.py",
                ],
                [
                  "flujos_2028.json",
                  "887 movimientos entre barrios, y el centro de cada uno",
                  "modelar_sustitucion.py",
                ],
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
                15.406 anuncios de la ciudad, con precio, capacidad declarada y reseñas. Es{" "}
                <em>un anuncio</em>, no una vivienda, y no es el registro oficial: cubre lo que se
                comercializa en una plataforma concreta un día concreto. La propia fuente desplaza
                cada anuncio hasta 150 metros a propósito, y por eso ninguno se publica como punto en
                el mapa: se agregan por barrio.
              </P>
              <P>
                De esos 15.406 se llega a <strong>6.834 viviendas</strong> descartando, por este
                orden: alojamiento ya reglado (901), habitaciones sueltas sin licencia (3.083),
                habitaciones de hotel (14), alquiler de temporada de más de 31 noches (1.848),
                anuncios sin reseñas desde septiembre de 2025 (876) y repeticiones del mismo anuncio
                (1.850).
              </P>
              <Aviso>
                El registro oficial tiene 24.075 licencias con 61.899 plazas. Este análisis mueve
                30.067 turistas, los de las 6.834 viviendas anunciadas hoy en Airbnb. Lo que no se
                anuncia allí no está en el mapa.
              </Aviso>
            </Fuente>

            <Fuente
              nombre="INE · Encuesta de Ocupación Hotelera"
              quien="Instituto Nacional de Estadística"
              fecha="Últimos 60 meses, punto turístico Barcelona"
            >
              <P>
                Dos usos distintos. Uno: la <strong>ocupación de partida</strong> —el 67,9% de media
                de los últimos doce meses— que descuenta las plazas de hotel que ya están ocupadas
                antes de repartir a nadie. Dos: la <strong>estacionalidad</strong>, trece años de
                serie, que permite llevar un precio de una fecha concreta a equivalente anual.
              </P>
              <P>
                Su límite: es un agregado de la ciudad. Sirve para el nivel y la tendencia, nunca
                para atribuir un precio a un hotel concreto.
              </P>
            </Fuente>

            <Fuente
              nombre="Censo comercial municipal"
              quien="Ajuntament de Barcelona"
              fecha="Trabajo de campo de 2023 y 2024"
            >
              <P>
                9.479 locales de restauración de la ciudad: 4.429 restaurantes, 4.272 bares y 778 de
                comida rápida. Se usa el censo y no OpenStreetMap porque OSM se deja fuera un 26% de
                la restauración de Barcelona. No existe un censo equivalente de 2026; se comprobó.
              </P>
            </Fuente>

            <Fuente
              nombre="Precios de hotel"
              quien="Portales de reserva"
              fecha="Consultados el 29 de septiembre de 2026"
            >
              <P>
                Precios recogidos de portales de reserva cuyos términos no permiten redistribuirlos.
                No se republican y no se citan como fuente: sirven para calibrar el análisis en
                local. Lo que se publica es la <strong>banda económica</strong>, nunca el euro
                exacto, y la referencia oficial citable es el ADR del INE.
              </P>
            </Fuente>

            <Fuente
              nombre="Geometría"
              quien="Institut Cartogràfic i Geològic de Catalunya"
              fecha="311 municipios de la provincia, 75 barrios de la ciudad"
            >
              <P>
                Antes de llegar al navegador se reparan dos barrios con la geometría mal cerrada y se
                simplifica el contorno, porque el fichero original pesa 13,7 MB y a la escala en que
                se mira una ciudad dos vértices separados por 20 metros caen en el mismo píxel. Si al
                simplificar la superficie total cambiara más de un 1%, el proceso se detiene.
              </P>
            </Fuente>
          </Seccion>

          <Seccion id="precio" numero={3} titulo="De dónde sale un precio">
            <P>
              Un hotel tiene precio por una de dos vías, y solo dos. <strong>Airbnb no aporta ni un
              solo precio de hotel</strong>: lo único que cruza de ese lado al hotelero es la
              geometría de los barrios.
            </P>
            <Tabla
              cabeceras={["Procedencia", "Cuántos", "Qué significa"]}
              filas={[
                ["Observado", "451", "Su ficha cruzó con un precio real recogido de un portal"],
                ["Estimado", "312", "No tiene precio recogido: lo calcula un modelo"],
                ["Sin precio", "800", "Ni lo uno ni lo otro — ver abajo"],
              ]}
            />
            <P>
              Los tres suman los 1.563 hoteles y apartaments turístics de la provincia. Los 800 sin
              precio son dos grupos que no tienen nada que ver entre sí:
            </P>
            <ul className="ml-4 list-disc space-y-2 text-[14px] leading-relaxed text-[#3a3935] marker:text-[#a3a09b]">
              <li>
                <strong>795 están fuera de la ciudad de Barcelona</strong> — Sitges, Castelldefels,
                l&apos;Hospitalet, Calella. Los precios recogidos cubren la ciudad y el modelo se
                entrenó solo con ella; estimar un hotel de Calella con lo aprendido en el Eixample
                sería inventar.
              </li>
              <li>
                <strong>5 están en la ciudad</strong>, y son apartaments turístics. El modelo les da
                un número, pero apoyándose en menos de diez casos comparables. Se les quita: un hueco
                es más honesto que una cifra que nadie puede contradecir.
              </li>
            </ul>
            <Aviso>
              <strong>El 41% de los precios de hotel que se publican están estimados por un
              modelo</strong>, frente al 3% en el lado de Airbnb. No es un detalle menor: significa
              que la banda de cuatro de cada diez hoteles es una deducción, no una medición.
            </Aviso>
            <P>
              El error del modelo se mide con validación cruzada repetida y no con una partición
              única. Una versión anterior anunciaba 40,6 € de error apartando 86 casos de prueba; la
              validación cruzada sobre los mismos datos daba 57 €. No era un modelo mejor, era una
              partición afortunada. Y el error se publica <em>por segmento</em>, porque los hoteles
              con precio recogido tienen 58 habitaciones de mediana y los que hay que estimar, 13.
            </P>
          </Seccion>

          <Seccion id="decisiones" numero={4} titulo="Las decisiones que mueven el resultado">
            <P>
              Cada una de estas es un sitio donde el resultado depende de un criterio nuestro y no del
              dato. No son defectos: son lo que hace falta para poder decir algo. El defecto sería
              tomarlas y no contarlas.
            </P>

            <Decision titulo="La plaza es la unidad comparable">
              Un piso entero para cuatro a 221 € y una habitación doble a 64 € no se pueden comparar;
              54 € y 43 € por plaza, sí. Se divide entre la capacidad <em>declarada</em>, no entre
              los ocupantes reales, y se aplica igual a los dos lados.
            </Decision>

            <Decision titulo="Se publica la banda, no el euro">
              El mismo hotel se mueve un ±22% sobre su propia mediana en quince días, según el tipo
              de habitación y la fecha. El modelo tiene un 27% de error: por debajo de la variación
              natural de aquello que mide. Una banda aguanta donde un euro exacto miente. Los cortes
              son 40, 70 y 120 € por plaza, elegidos para que hoteles y Airbnb ocupen varias bandas
              cada uno — no son los cuartiles de ninguno de los dos.
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

          <Seccion id="modelo" numero={5} titulo="El modelo de 2028">
            <P>
              Cada vivienda turística que cierra busca alojamiento reglado, y cada hotel recibe una
              nota que mezcla dos cosas: lo cerca que está y lo parecido que es su precio. La barra
              del mapa es el peso entre las dos.
            </P>

            <Decision titulo="Ese peso no se estima, y es deliberado">
              Se intentó deducirlo de la demanda actual de Airbnb y no funciona: la distancia al
              centro no predice la demanda, y el coeficiente del precio sale positivo, que es
              causalidad inversa y no sensibilidad al precio. Además, un turista alemán y uno andaluz
              no tienen la misma sensibilidad y ningún dato disponible los distingue. Por eso se
              publican cinco escenarios y decide quien mira.
            </Decision>

            <Decision titulo="Los hoteles no están vacíos">
              Se descuenta la ocupación real del INE: 67,9%. Quedan 27.010 plazas libres para 30.067
              turistas, así que <strong>3.057 no caben en ningún escenario</strong>. En noviembre,
              con la ocupación al 55,6%, cabrían todos; en julio, al 79,1%, no cabrían 12.490.
            </Decision>

            <Decision titulo="Se usa la ocupación media del año, no la de cada mes">
              Los precios del análisis son equivalentes anuales. Cruzar un precio anual con la
              ocupación de julio mezclaría dos escalas de tiempo distintas.
            </Decision>

            <Decision titulo="El reparto va de la vivienda más cara a la más barata">
              Hace falta un orden para que el resultado sea el mismo cada vez que se ejecuta, y ese
              orden <strong>no es neutral</strong>: quien paga menos es quien se queda sin sitio.
              Queda dicho porque cambia quién aparece en el mapa como «sin sitio».
            </Decision>

            <Decision titulo="La capacidad es un límite duro">
              Un hotel de 200 plazas no absorbe 500. La segmentación por precio, en cambio, no se
              impone: emerge sola. El 82% de las plazas de la banda más cara acaba en hoteles de 4 y
              5 estrellas, y ninguna plaza de las dos bandas baratas llega a un 5 estrellas.
            </Decision>
          </Seccion>

          <Seccion id="privacidad" numero={6} titulo="Lo que nunca se publica">
            <P>
              Un hotel o un restaurante es un establecimiento abierto al público y se publica como
              punto en el mapa. Una vivienda de uso turístico es una <em>vivienda</em>, y un anuncio
              de Airbnb también: esos se agregan siempre por barrio o municipio y nunca salen
              individualmente. No es una precaución de estilo, es la línea que separa analizar un
              mercado de señalar domicilios.
            </P>
            <P>
              Tampoco sale nada del titular. Entre los del Registre hay personas físicas con nombre y
              dirección; el pipeline detecta y anula sus documentos de identidad antes de que salgan
              de la primera capa, sin confiar en que la fuente los marque.
            </P>
            <P>
              Cada punto que sí se publica lleva dicho <strong>cómo de precisa</strong> es su
              posición: tomada del registro oficial, deducida de la dirección y verificada contra su
              municipio, o desplazada a propósito por la fuente. Pintarlas con el mismo símbolo daría
              a entender una precisión que no tenemos.
            </P>
          </Seccion>

          <Seccion id="limites" numero={7} titulo="Lo que esto no puede decir">
            <ol className="ml-4 list-decimal space-y-2 text-[14px] leading-relaxed text-[#3a3935] marker:text-[#a3a09b]">
              <li>
                <strong>No cubre las 24.075 licencias</strong>, cubre 6.834 viviendas anunciadas en
                Airbnb. Lo que no se anuncia allí no está.
              </li>
              <li>
                <strong>No sabe qué quiere un turista.</strong> Por eso la barra entre precio y
                ubicación la mueve quien mira, y no hay un escenario marcado como el correcto.
              </li>
              <li>
                <strong>No predice qué harán los hoteles.</strong> El reparto usa la capacidad y los
                precios de hoy. Si los precios suben al desaparecer la oferta alternativa —que es lo
                esperable— el reparto cambia.
              </li>
              <li>
                <strong>No mide meses.</strong> Todo es equivalente anual, salvo las cifras de julio
                y noviembre que se dan aparte como contexto.
              </li>
              <li>
                <strong>Un hotel no tiene un precio, tiene un rango.</strong> Se publica una banda
                precisamente por eso.
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
