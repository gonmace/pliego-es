# graph/nodes/inicio.py
from langchain_core.runnables import RunnableConfig

from pliego_esp.graph.state import State

from rich.console import Console
console = Console()

async def inicio(state: State, *, config: RunnableConfig) -> State:
    console.print("---inicio---", style="bold white")
    state["token_cost"] = 0
    
    return state