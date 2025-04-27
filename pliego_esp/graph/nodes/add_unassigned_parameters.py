from pliego_esp.graph.state import State
from rich.console import Console
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pliego_esp.graph.configuration import Configuration
from langchain_core.runnables import RunnableConfig
from pliego_esp.graph.callbacks import shared_callback_handler
from langgraph.types import interrupt
from typing import Optional, Literal
from langchain_core.messages import HumanMessage

from pydantic import BaseModel, Field

console = Console()

async def add_unassigned_parameters(state: State, *, config: RunnableConfig):
    console.print("------ add_unassigned_parameters ------", style="bold blue")

    costo_inicial = shared_callback_handler.total_cost
    console.print(f"Costo inicial: ${costo_inicial:.6f}", style="blue")
    
    respuesta_humana = interrupt({
        "mensaje": "nuevos parametros",
        "items": state.get("evaluaciones_otros_parametros", [])
    })
    state["messages"] = [
        HumanMessage(content=f"Pliego base: {state['pliego_base']}\nTitulo: {state['titulo']}\nParametros clave: {state['parametros_clave']}\nAdicionales: {state['adicionales']}")
    ]
    # Retorna el estado actualizado con 'items' para que esté disponible en result
    return {
        "messages": state["messages"],
        "respuesta_usuario": respuesta_humana
    }