# graph/nodes/inicio.py
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage
from pliego_esp.graph.state import State

from rich.console import Console
console = Console()

async def inicio(state: State, *, config: RunnableConfig) -> State:
    console.print("---inicio---", style="bold green")
    state["token_cost"] = 0
    
    
    
    state["messages"] = [
        HumanMessage(content=f"Pliego base: {state['pliego_base']}\nTitulo: {state['titulo']}\nParametros clave: {state['parametros_clave']}\nAdicionales: {state['adicionales']}")
    ]
    
    return state