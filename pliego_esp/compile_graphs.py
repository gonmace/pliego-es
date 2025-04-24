# compile_graphs.py
from asgiref.sync import async_to_sync

# from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph

from pliego_esp.graph.graph import create_workflow

from rich.console import Console
console = Console()

# Variables globales para almacenar los grafos compilados
workflow: StateGraph | None = None
# memory_saver: MemorySaver | None = None

def initialize_graphs():
    """
    Inicializa los grafos una sola vez al inicio de la aplicación.
    Esta función debe ser llamada desde el método ready() de la AppConfig.
    """
    # global workflow, memory_saver
    global workflow
    
    try:
        console.print("[compile_graphs.py] Iniciando compilación de grafos...", style="bold blue")
        
        # Crear el memory_saver una sola vez
        # memory_saver = MemorySaver()
        
        # Compilar el workflow
        workflow = async_to_sync(create_workflow)()
        
        return True
        
    except Exception as e:
        console.print(f"[compile_graphs.py] Error al compilar los grafos: {str(e)}", style="bold red")
        return False

def get_workflow():
    """
    Retorna el workflow compilado.
    Si no está inicializado, retorna None.
    """
    return workflow

# def get_memory_saver():
#     """
#     Retorna el memory_saver.
#     Si no está inicializado, retorna None.
#     """
#     return memory_saver

