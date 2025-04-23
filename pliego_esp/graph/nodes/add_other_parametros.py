from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.callbacks.openai_info import OpenAICallbackHandler

from pliego_esp.graph.state import State
from pliego_esp.graph.configuration import Configuration
from langchain_core.runnables import RunnableConfig
from pliego_esp.graph.callbacks import shared_callback_handler

from rich.console import Console

console = Console()

def add_other_parametros(state: State, *, config: RunnableConfig) -> State:
    console.print("------ add_other_parametros ------", style="bold magenta")

    # Guardar el costo inicial
    costo_inicial = shared_callback_handler.total_cost
    console.print(f"Costo inicial: ${costo_inicial:.6f}", style="magenta")

    configuration = Configuration.from_runnable_config(config)
    llm = ChatOpenAI(
        model=configuration.chat_model,
        temperature=0.0,
        callbacks=[shared_callback_handler]
    )

    nombre_prompt = ChatPromptTemplate.from_template("""
Dado un parámetro clave del proyecto expresado de forma libre:

"{parametro_clave}"

Dado un parámetro clave expresado de forma libre por un usuario de obra:

"{parametro_clave}"

Tu tarea es sugerir un nombre técnico **de una sola palabra**, clara y neutra, que pueda usarse como título de parámetro en una tabla de especificaciones técnicas de construcción.

### Reglas:
- Usa solo **una palabra genérica**, como por ejemplo:
  - Color
  - Resistencia
  - Secado
  - Adherencia
  - Aplicación
  - Tipo
  - Dureza
  - Preparación
  - Recubrimiento
- No incluyas valores concretos, medidas, materiales ni colores (como "amarillo", "5 mm", "uretano").
- Si no puedes generar una palabra adecuada, responde con: "Otros"
- Responde solo con una palabra, sin explicaciones ni puntuación.
""")
    cost = 0
    nuevos = []
    console.print(f"Nuevos parametros: {len(state['parametros_no_asignados'])}", style="bold magenta")
    for clave in state["parametros_no_asignados"]:
        prompt = nombre_prompt.format_prompt(parametro_clave=clave).to_messages()
        sugerido = llm.invoke(prompt).content.strip()

        if sugerido.lower() == "otros" or sugerido == "":
            nombre_param = "Otros"
        else:
            nombre_param = sugerido.strip().rstrip(".") + "*"  # Marcar con * para revisión

        nueva_fila = {
            "Parámetro Técnico": nombre_param,
            "Opciones válidas": "-",
            "Valor por defecto": "-",
            "Valor Asignado": clave
        }
        nuevos.append(nueva_fila)
        
        cost += shared_callback_handler.total_cost
        
        console.print(f"Costo parcial después de procesar '{clave}': ${shared_callback_handler.total_cost:.6f}", style="magenta")
    
    # Calcular el costo total de este nodo
    costo_nodo = shared_callback_handler.total_cost - costo_inicial
    console.print(f"Costo total del nodo add_other_parametros: ${costo_nodo:.6f}", style="bold magenta")
    console.print(f"Costo acumulado hasta ahora: ${shared_callback_handler.total_cost:.6f}", style="magenta")
    
    console.print(f"Nuevos parametros: {len(nuevos)}", style="magenta")
    for fila in nuevos:
        console.print(fila, style="magenta")

    console.print(20*"-", style="bold magenta")
    return {
        "other_parametros": nuevos,
        }
