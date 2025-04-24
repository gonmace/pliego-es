import os
from pathlib import Path
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

from langchain_core.runnables import RunnableConfig
from graph_retriever.strategies import Eager
from langgraph.checkpoint.memory import MemorySaver

from pliego_esp.graph.nodes.process_pliego import process_pliego
from pliego_esp.graph.state import State

from pliego_esp.graph.nodes.clean_and_capture_sections import clean_and_capture_sections
from pliego_esp.graph.nodes.parse_adicionales import parse_adicionales
from pliego_esp.graph.nodes.match_adicionales import match_adicionales
from pliego_esp.graph.nodes.parse_parametros import parse_parametros
from pliego_esp.graph.nodes.match_parametros_clave import match_parametros_clave
from pliego_esp.graph.nodes.add_other_parametros import add_other_parametros

from rich.console import Console
console = Console()

# Cargar variables de entorno
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
console.print(f"[graph.py] Intentando cargar .env desde: {env_path}", style="bold red")
load_dotenv(env_path, override=True)

# Verificar la API key al importar el módulo
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OPENAI_API_KEY no está configurada en las variables de entorno")
console.print(f"[graph.py] OPENAI_API_KEY: {api_key[:10] + '...' if api_key else 'No encontrada'}", style="bold red")

async def create_workflow() -> StateGraph:
    """
    Crea y configura el workflow principal del sistema.
    
    Args:
        config (RunnableConfig): Configuración que contiene los parámetros necesarios
                               para inicializar los componentes del workflow.
    
    Returns:
        CompiledStateGraph: El workflow compilado y listo para ser ejecutado.
    """

    # Crear el grafo de estado que maneja el flujo de trabajo
    workflow = StateGraph(State)

    # Agregar los nodos al workflow con el callback_handler compartido
    workflow.add_node("clean_and_capture_sections", clean_and_capture_sections)
    
    # Primer flujo paralelo
    workflow.add_node("parse_adicionales", parse_adicionales)
    workflow.add_node("match_adicionales", match_adicionales)
    
    # Segundo flujo paralelo
    workflow.add_node("parse_parametros", parse_parametros)
    workflow.add_node("match_parametros_clave", match_parametros_clave)
    workflow.add_node("add_other_parametros", add_other_parametros)

    workflow.add_node("process_pliego", process_pliego)

    # Flujo de trabajo
    workflow.set_entry_point("clean_and_capture_sections")
    
    # Primer flujo paralelo
    workflow.add_edge("clean_and_capture_sections", "parse_adicionales")
    workflow.add_edge("parse_adicionales", "match_adicionales")
    
    # Segundo flujo paralelo
    workflow.add_edge("clean_and_capture_sections", "parse_parametros")  
    workflow.add_edge("parse_parametros", "match_parametros_clave")
    workflow.add_edge("match_parametros_clave", "add_other_parametros")
    
    # Convergencia de flujos
    workflow.add_edge(
        ["add_other_parametros", "match_adicionales"], 
        "process_pliego")
    
    # Flujo final
    workflow.add_edge("process_pliego", END)
    
    # Compilar el workflow con el memory_saver para mantener el estado entre ejecuciones
    return workflow.compile(debug=False)


