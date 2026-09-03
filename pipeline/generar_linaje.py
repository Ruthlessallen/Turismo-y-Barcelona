"""Dibuja el linaje del pipeline leyendo el codigo, no la documentacion.

    python pipeline/generar_linaje.py

Salida
    docs/linaje.md   — diagrama Mermaid y tabla de dependencias

**Por que se genera y no se dibuja.** Un diagrama hecho a mano describe el pipeline del dia en que
alguien lo dibujo. Este se construye recorriendo el AST de cada script y anotando que ficheros
lee y cuales escribe, asi que no puede discrepar del codigo: si discrepa, es que el codigo cambio
y basta con volver a ejecutarlo.

Se descarto leer los docstrings, que ya declaran "Entradas" y "Salidas": diez de los dieciocho
scripts no los tienen completos, y aunque se completaran, un docstring puede quedarse viejo
mientras el codigo sigue. Las llamadas a `read_csv` y `to_csv` no.

**Como distingue lectura de escritura.** `pd.read_csv(X)` y `gpd.read_file(X)` marcan X como
entrada; `X.to_csv(...)`, `X.to_file(...)` y `X.write_text(...)` marcan X como salida. Las rutas se
resuelven siguiendo las constantes del modulo —`BRONZE / "fichero.csv"`— hasta el literal.

**Lo que no ve.** Un fichero cuyo nombre se componga en tiempo de ejecucion, o una lectura dentro
de una funcion que reciba la ruta como argumento desde fuera del modulo. Al final del informe se
listan las llamadas que no se pudieron resolver, para que el hueco se vea en vez de silenciarse.
"""

from __future__ import annotations

import ast
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PIPELINE = RAIZ / "pipeline"
SALIDA = RAIZ / "docs" / "linaje.md"

LECTURAS = {"read_csv", "read_file", "read_parquet", "read_json", "read_text"}
ESCRITURAS = {"to_csv", "to_file", "to_parquet", "write_text", "to_json"}

CAPAS = {"raw": "raw", "bronze": "bronze", "gold": "gold", "exports": "exports"}


class Rastreador(ast.NodeVisitor):
    """Sigue las constantes de ruta del modulo y anota que se lee y que se escribe."""

    def __init__(self) -> None:
        self.constantes: dict[str, str] = {}
        self.entradas: set[str] = set()
        self.salidas: set[str] = set()
        self.sin_resolver: list[str] = []

    def ruta(self, nodo: ast.AST) -> str | None:
        """Resuelve `BRONZE / "x.csv"` o `RAIZ / "data" / "gold" / "y.csv"` hasta su literal."""
        if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str):
            return nodo.value
        if isinstance(nodo, ast.Name):
            # Si no se conoce la constante, vale su propio nombre como raiz simbolica: `RAIZ` sale
            # de `Path(__file__).resolve().parents[2]`, que no es un literal, y sin este recurso
            # ninguna ruta construida sobre ella llegaria a resolverse.
            return self.constantes.get(nodo.id, nodo.id)
        if isinstance(nodo, ast.BinOp) and isinstance(nodo.op, ast.Div):
            izq, der = self.ruta(nodo.left), self.ruta(nodo.right)
            if izq is None or der is None:
                return None
            return f"{izq}/{der}"
        return None

    def visit_Assign(self, nodo: ast.Assign) -> None:
        """Registra constantes de ruta asignadas a variables en el módulo."""
        destino = nodo.targets[0]
        if isinstance(destino, ast.Name):
            resuelta = self.ruta(nodo.value)
            if resuelta:
                self.constantes[destino.id] = resuelta
        self.generic_visit(nodo)

    def visit_Call(self, nodo: ast.Call) -> None:
        """Intercepta llamadas de lectura y escritura para anotar las rutas involucradas."""
        nombre = nodo.func.attr if isinstance(nodo.func, ast.Attribute) else None
        if nombre in LECTURAS and nodo.args:
            self._anotar(self.ruta(nodo.args[0]), self.entradas, nombre)
        elif nombre in ESCRITURAS:
            # Dos formas distintas: `df.to_csv(ruta)` pasa el destino como argumento, mientras que
            # `ruta.write_text(contenido)` lo tiene en el objeto y el argumento es el texto. Tomar
            # siempre el primer argumento capturaria el contenido del fichero como si fuera su
            # nombre.
            if nombre == "write_text" and isinstance(nodo.func, ast.Attribute):
                candidato = self.ruta(nodo.func.value)
            else:
                candidato = self.ruta(nodo.args[0]) if nodo.args else None
                if candidato is None and isinstance(nodo.func, ast.Attribute):
                    candidato = self.ruta(nodo.func.value)
            self._anotar(candidato, self.salidas, nombre)
        self.generic_visit(nodo)

    def _anotar(self, ruta: str | None, destino: set[str], llamada: str) -> None:
        """Solo entra lo que parece un fichero. Una ruta que acaba en un identificador sin punto
        --una variable local que llega de fuera-- no es un nombre de fichero y se anota como no
        resuelta, que es distinto de descartarla en silencio."""
        if ruta is None or "." not in Path(ruta).name:
            self.sin_resolver.append(llamada)
        else:
            destino.add(ruta)


def capa_de(ruta: str) -> str:
    """Determina la capa de datos (raw, bronze, gold, etc.) según la ruta del fichero."""
    for parte in Path(ruta).parts:
        if parte in CAPAS:
            return CAPAS[parte]
    return "otros"


def analizar() -> tuple[dict, list]:
    """Recorre todos los scripts del pipeline analizando su AST para extraer dependencias."""
    grafo, avisos = {}, []
    for script in sorted(PIPELINE.rglob("*.py")):
        if script.name in ("generar_linaje.py", "bandas.py"):
            continue
        r = Rastreador()
        r.visit(ast.parse(script.read_text(encoding="utf-8")))
        clave = str(script.relative_to(PIPELINE)).replace("\\", "/")
        grafo[clave] = {"entradas": sorted(r.entradas), "salidas": sorted(r.salidas)}
        if r.sin_resolver:
            avisos.append((clave, len(r.sin_resolver)))
    return grafo, avisos


def identificador(texto: str) -> str:
    """Genera un identificador válido para un nodo del diagrama Mermaid."""
    return "n_" + "".join(c if c.isalnum() else "_" for c in texto)


def mermaid(grafo: dict) -> str:
    """Construye el código del diagrama Mermaid a partir del grafo de dependencias."""
    ficheros: dict[str, str] = {}
    for datos in grafo.values():
        for f in datos["entradas"] + datos["salidas"]:
            ficheros[f] = capa_de(f)

    lineas = ["flowchart TD"]
    for capa, titulo in (("raw", "raw · descargas"), ("bronze", "bronze · limpio"),
                         ("gold", "gold · transformado"), ("exports", "exports · web"),
                         ("otros", "sin capa")):
        de_la_capa = [f for f, c in ficheros.items() if c == capa]
        if not de_la_capa:
            continue
        lineas.append(f'  subgraph {capa} ["{titulo}"]')
        for f in sorted(de_la_capa):
            lineas.append(f'    {identificador(f)}[("{Path(f).name}")]')
        lineas.append("  end")

    lineas.append('  subgraph scripts ["scripts"]')
    for script in grafo:
        lineas.append(f'    {identificador(script)}["{script}"]')
    lineas.append("  end")

    for script, datos in grafo.items():
        for f in datos["entradas"]:
            lineas.append(f"  {identificador(f)} --> {identificador(script)}")
        for f in datos["salidas"]:
            lineas.append(f"  {identificador(script)} --> {identificador(f)}")
    return "\n".join(lineas)


def main() -> None:
    """Función principal que ejecuta el análisis y genera el documento markdown con el linaje."""
    grafo, avisos = analizar()
    total_ficheros = len({f for d in grafo.values() for f in d["entradas"] + d["salidas"]})

    filas = ["| Script | Capa | Lee | Escribe |", "|---|---|---|---|"]
    for script, datos in grafo.items():
        capa = script.split("/")[0]
        lee = "<br>".join(Path(f).name for f in datos["entradas"]) or "—"
        escribe = "<br>".join(Path(f).name for f in datos["salidas"]) or "—"
        filas.append(f"| `{script}` | {capa} | {lee} | {escribe} |")

    aviso = ""
    if avisos:
        detalle = ", ".join(f"`{s}` ({n})" for s, n in avisos)
        aviso = (f"\n**Llamadas no resueltas:** {detalle}. Son rutas que se componen en tiempo de "
                 f"ejecucion o que llegan como argumento; el grafo no las incluye y por eso se "
                 f"listan aqui en vez de pasar desapercibidas.\n")

    SALIDA.write_text(f"""# Linaje de los datos

**Generado por `pipeline/generar_linaje.py` — no editar a mano.** Se reconstruye leyendo el AST de
cada script y anotando que ficheros lee y cuales escribe, asi que describe el pipeline tal como
esta, no como se documento. Volver a ejecutarlo despues de cualquier cambio.

{len(grafo)} scripts, {total_ficheros} ficheros.
{aviso}
```mermaid
{mermaid(grafo)}
```

## Dependencias por script

{chr(10).join(filas)}
""", encoding="utf-8")

    print(f"{len(grafo)} scripts | {total_ficheros} ficheros")
    for script, n in avisos:
        print(f"  sin resolver en {script}: {n} llamadas")
    print(f"Guardado en {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
