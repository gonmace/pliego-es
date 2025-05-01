from pliego_esp.graph.state import State
from rich.console import Console
from langchain_core.runnables import RunnableConfig

console = Console()

PARRAFO_FINAL = """
Los trabajos deben ser realizados por personal calificado y capacitado, siguiendo estrictamente las normas de seguridad y contando con los equipos de protección personal necesarios para cada etapa del proceso.

> **Nota:** EMBOL S.A. se deslinda de cualquier responsabilidad asociada a la actividad de transporte y disposición de los residuos generados. La empresa contratista es responsable de llevar a cabo la actividad de manera segura y conforme a todas las normativas y regulaciones aplicables.
"""

async def add_finales(state: State, *, config: RunnableConfig) -> State:
    console.print("------ add_finales ------", style="bold cyan")

    especificacion = state.get("especificacion_generada", "")
    
    # Buscar la sección de Procedimiento
    if "## Procedimiento" in especificacion:
        # Dividir el documento en secciones
        secciones = especificacion.split("## Procedimiento")
        if len(secciones) > 1:
            # Agregar el párrafo final al final de la sección de Procedimiento
            procedimiento = secciones[1].split("\n\n##")[0]  # Tomar solo la sección de Procedimiento
            procedimiento_con_final = procedimiento.rstrip() + "\n\n" + PARRAFO_FINAL
            
            # Reconstruir el documento
            especificacion_con_finales = (
                secciones[0] + 
                "## Procedimiento" + 
                procedimiento_con_final + 
                "\n\n##" + 
                "\n\n##".join(secciones[1].split("\n\n##")[1:])
            )
            
            return {
                "especificacion_generada": especificacion_con_finales,
                "token_cost": state.get("token_cost", 0)
            }
    
    # Si no se encuentra la sección de Procedimiento, devolver el estado sin cambios
    console.print("No se encontró la sección de Procedimiento", style="red")
    return state
