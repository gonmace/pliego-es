from langchain_core.runnables import RunnableConfig
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_community.callbacks.openai_info import OpenAICallbackHandler

from pliego_esp.graph.state import State
from pliego_esp.graph.configuration import Configuration
from pliego_esp.graph.callbacks import shared_callback_handler

from rich.console import Console

console = Console()

async def match_parametros_clave(state: State, *, config: RunnableConfig) -> State:
    console.print("------ match_parametros_clave ------", style="bold blue")
    
    # Guardar el costo inicial
    costo_inicial = shared_callback_handler.total_cost
    console.print(f"Costo inicial: ${costo_inicial:.6f}", style="bold blue")
    
    configuration = Configuration.from_runnable_config(config)
    
    # Cambiar a gpt-3.5-turbo que tiene mejor soporte para seguimiento de tokens
    llm = ChatOpenAI(
        model=configuration.chat_model,
        temperature=0.0,
        callbacks=[shared_callback_handler]
    )

    fila_prompt = ChatPromptTemplate.from_template("""
Estás procesando una tabla de parámetros técnicos para una especificación de construcción.

Analiza el siguiente parámetro técnico de la tabla:

- Nombre del parámetro: {parametro}
- Opciones válidas: {opciones_validas}

Y evalúa si **alguno de los siguientes valores clave del proyecto representa un valor apropiado para este parámetro técnico**:

{parametros_clave}

### Reglas:

- La relación debe ser clara: si el valor clave puede ser asignado directamente a este parámetro técnico, entonces es una coincidencia.
- Si hay una coincidencia clara, responde con el valor exacto del parámetro clave.
- Si no hay coincidencia válida, responde únicamente con un guion (`-`), sin comillas ni explicaciones.

No expliques nada más.
""")

    tabla_actualizada = []
    parametros_usados = set()
    
    for fila in state["parsed_parametros"]:
        prompt = fila_prompt.format_prompt(
            parametro=fila["Parámetro Técnico"],
            opciones_validas=fila["Opciones válidas"],
            parametros_clave=state["parametros_clave"]
        ).to_messages()
        
        # Pasar los callbacks en el método invoke
        salida = llm.invoke(
            prompt
        ).content.strip()
        
        console.print(f"Costo parcial después de procesar '{fila['Parámetro Técnico']}': ${shared_callback_handler.total_cost:.6f}", style="blue")
        if salida != "-" and salida in state["parametros_clave"]:
            parametros_usados.add(salida)
        
        fila["Valor Asignado"] = salida
        tabla_actualizada.append(fila)

    # Calcular el costo total de este nodo
    costo_nodo = shared_callback_handler.total_cost - costo_inicial
    console.print(f"Costo total del nodo match_parametros_clave: ${costo_nodo:.6f}", style="bold blue")
    console.print(f"Costo acumulado hasta ahora: ${shared_callback_handler.total_cost:.6f}", style="bold blue")

    console.print(tabla_actualizada, style="blue")
    
    # Determinar cuáles parámetros clave NO se usaron
    parametros_no_asignados = [
        clave for clave in state["parametros_clave"] if clave not in parametros_usados
    ]
    
    console.print(f"Nuevos parametros: {len(parametros_no_asignados)}", style="cyan")
    for fila in parametros_no_asignados:
        console.print(fila, style="bold cyan")

    console.print(20*"-", style="bold cyan")
    return {
        "parsed_parametros": tabla_actualizada,
        "parametros_no_asignados": parametros_no_asignados,
        }
    
