# graph/nodes/inicio.py
import re

from pliego_esp.graph.state import State

from rich.console import Console
console = Console()

async def clean_and_capture_sections(state: State) -> State:
    console.print("-----clean_and_capture_sections-----", style="italic white")
    
    seccion_PTE = re.search(
        r"### Parámetros Técnicos\s+((?:\|.*\n?)+)",
        state["pliego_base"]
    )
    
    if seccion_PTE:
        tabla_md = seccion_PTE.group(1).strip()
        console.print("Parametros técnicos recomendados", style="white")
        console.print(tabla_md, style="white")
        console.print(20*"-", style="white")
        
        # Guardar la tabla en formato Markdown
        state["parametros_pliego"] = tabla_md
    else:
        print("No se encontró la sección 'Parámetros Técnicos Recomendados'")
    
    seccion_adicionales = re.search(r"### Adicionales\s+((?:- .+\n?)+)", state["pliego_base"])
    
    if seccion_adicionales:
        adicionales_md = seccion_adicionales.group(1).strip()
        console.print("Adicionales", style="white")
        console.print(adicionales_md, style="white")
        
        # Guardar la tabla en formato Markdown
        state["adicionales_pliego"] = adicionales_md

    else:
        print("No se encontró la sección 'Adicionales'")
    
    # Eliminar desde la sección "### Parámetros Técnicos Recomendados" en adelante
    texto_recortado = re.split(r"### Parámetros Técnicos Recomendados", state["pliego_base"])[0].strip()
    state["pliego_base"] = texto_recortado
    
    console.print(20*"-", style="white")
    
    return {
        "pliego_base": state["pliego_base"],
        "titulo": state["titulo"],
        "parametros_clave": state["parametros_clave"],
        "adicionales": state["adicionales"],
        "parametros_pliego": state["parametros_pliego"],
        "adicionales_pliego": state["adicionales_pliego"]
    }