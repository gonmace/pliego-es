from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pliego_esp.graph.configuration import Configuration
from pliego_esp.graph.state import State
from langchain_core.runnables import RunnableConfig
from langchain_community.callbacks.openai_info import OpenAICallbackHandler
from pliego_esp.graph.callbacks import shared_callback_handler

from rich.console import Console
import json

console = Console()

prompt_template = ChatPromptTemplate.from_template(
    """Eres un asistente técnico en construcción.

A continuación tienes una lista de actividades que son compatibles con la especificacion, cada una con un nombre y su descripción.

También recibirás una propuesta de nueva actividad.

Tu tarea es:

1. Revisar si la actividad propuesta **coincide conceptualmente** con alguna actividad de la lista, aunque no tenga el mismo nombre exacto.
2. Si coincide, responde solo con el **nombre exacto** de la actividad compatible.
3. Si no hay coincidencia, responde con la actividad propuesta seguida de un asterisco (`*`).

### Actividades compatibles:
{actividades_compatibles}

### Actividad propuesta:
{actividad_propuesta}

Respuesta:
"""
)

async def match_adicionales(state: State, *, config: RunnableConfig) -> State:
    console.print("----- match_adicionales -----", style="bold green")
    
    # Guardar el costo inicial
    costo_inicial = shared_callback_handler.total_cost
    console.print(f"Costo inicial: ${costo_inicial:.6f}", style="bold green")
    
    configuration = Configuration.from_runnable_config(config)
    
    llm = ChatOpenAI(
        model=configuration.chat_model,
        temperature=0.0,
        callbacks=[shared_callback_handler]
    )

    actividades_compatibles_json = json.dumps(state["parsed_adicionales"], ensure_ascii=False, indent=2)

    adicionales_finales = []
    other_adicionales = []
    cost = 0

    for actividad in state["adicionales"]:
        prompt = prompt_template.format_prompt(
            actividades_compatibles=actividades_compatibles_json,
            actividad_propuesta=actividad
        ).to_messages()

        salida = llm.invoke(prompt).content.strip()
        
        if not salida.endswith("*"):
            # Buscar el objeto original completo por nombre
            match = next(
                (item for item in state["parsed_adicionales"] if item["actividad"] == salida),
                None
            )
            if match:
                adicionales_finales.append(match)
            else:
                # En caso muy raro donde haya coincidencia pero no match exacto (fallback)
                other_adicionales.append({
                    "actividad": salida,
                    "descripcion": "-"
                })
        else:
            other_adicionales.append({
                "actividad": salida,
                "descripcion": "-"
            })
        cost += shared_callback_handler.total_cost
        console.print(f"Costo parcial después de procesar '{actividad}': ${shared_callback_handler.total_cost:.6f}", style="green")
        
    # Calcular el costo total de este nodo
    costo_nodo = shared_callback_handler.total_cost - costo_inicial
    console.print(f"Costo total del nodo match_adicionales: ${costo_nodo:.6f}", style="bold green")
    console.print(f"Costo acumulado hasta ahora: ${shared_callback_handler.total_cost:.6f}", style="bold green")

    console.print(f"Adicionales finales: {adicionales_finales}", style="bold green")
    console.print(f"Otros adicionales: {other_adicionales}", style="bold turquoise")
    return {
        "adicionales_finales": adicionales_finales,
        "other_adicionales": other_adicionales
        }
