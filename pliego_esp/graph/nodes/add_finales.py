from pliego_esp.graph.state import State
from rich.console import Console
from langchain_core.runnables import RunnableConfig
import re
console = Console()

PARRAFO_FINAL_PROCEDIMIENTO = """
Los trabajos deben ser realizados por personal calificado y capacitado, siguiendo estrictamente las normas de seguridad y contando con los equipos de protección personal necesarios para cada etapa del proceso.

> **Nota:** EMBOL S.A. se deslinda de cualquier responsabilidad asociada a la actividad de transporte y disposición de los residuos generados. La empresa contratista es responsable de llevar a cabo la actividad de manera segura y conforme a todas las normativas y regulaciones aplicables.
"""

def agregar_parrafo_a_procedimiento(texto, parrafo):
    # Buscar todas las secciones que comienzan con ### y sus posiciones
    secciones = list(re.finditer(r"^### (.+?)\.\s*$", texto, flags=re.MULTILINE))
    
    for i, match in enumerate(secciones):
        if match.group(1).strip().lower() == "procedimiento":
            inicio = match.end()  # después de '### Procedimiento.'
            fin = secciones[i + 1].start() if i + 1 < len(secciones) else len(texto)
            contenido_original = texto[inicio:fin].rstrip()
            nuevo_contenido = f"{contenido_original}\n{parrafo}\n"
            return texto[:inicio] + nuevo_contenido + texto[fin:]

    # Si no se encuentra la sección, devolver texto original
    return texto

async def add_finales(state: State, *, config: RunnableConfig) -> State:
    console.print("------ add_finales ------", style="bold cyan")

    especificacion = state.get("especificacion_generada", "")
    
    especificacion_con_finales = agregar_parrafo_a_procedimiento(especificacion, PARRAFO_FINAL_PROCEDIMIENTO)
    
    return {
        "especificacion_generada": especificacion_con_finales
    }
    
