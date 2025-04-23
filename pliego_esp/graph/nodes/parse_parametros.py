
from pliego_esp.graph.state import State
import re
from rich.console import Console
console = Console()

def parse_parametros(state: State) -> State:
    console.print("------ parse_parametros ------", style="bold yellow")
    tabla_md = state["parametros_pliego"]
    # Filas de la tabla (omitimos la línea de separadores)
    lineas = [l.strip() for l in tabla_md.strip().split('\n') if l.strip() and not re.match(r'^\|[-\s|]+$', l)]

    # Separar encabezados
    encabezados = [c.strip() for c in lineas[0].split('|') if c.strip()]

    # Filas como lista de dicts
    filas = []
    for linea in lineas[1:]:
        columnas = [c.strip() for c in linea.split('|') if c.strip()]
        fila_dict = dict(zip(encabezados, columnas))
        filas.append(fila_dict)

    console.print(filas, style="yellow")
    console.print(20*"-", style="bold yellow")
    return { "parsed_parametros": filas}