from pliego_esp.graph.state import State
from rich.console import Console
import json
from pliego_esp.graph.callbacks import shared_callback_handler

console = Console()

async def prov_pliego(state: State) -> State:
    console.print("------ prov_pliego ------", style="bold red")

    # Usar el costo del callback handler
    total_cost = shared_callback_handler.total_cost
    
    console.print(f"Costo total acumulado: ${total_cost:.6f}", style="bold red")

    console.print(20*"-", style="bold red")
    return {
        "token_cost": total_cost
    }