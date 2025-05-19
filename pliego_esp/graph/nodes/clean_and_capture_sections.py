# graph/nodes/inicio.py
import re

from pliego_esp.graph.state import State

from rich.console import Console
console = Console()

async def clean_and_capture_sections(state: State) -> State:
    console.print("-----clean_and_capture_sections-----", style="italic white")
    
    # Eliminar desde la sección "### Parámetros Técnicos Recomendados" en adelante
    texto_recortado = re.split(r"### Parámetros Técnicos", state["pliego_base"])[0].strip()
    state["pliego_base"] = texto_recortado
    
    # console.print(state["pliego_base"], style="white")
    console.print(20*"-", style="white")
    return {
        "pliego_base": state["pliego_base"],
        "titulo": state["titulo"],
        "parametros_clave": state["parametros_clave"],
        "adicionales": state["adicionales"],
    }