import os
from pathlib import Path
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph

from langchain_core.runnables import RunnableConfig
from graph_retriever.strategies import Eager
from langgraph.checkpoint.memory import MemorySaver

from pliego_esp.graph.nodes.add_finales import add_finales
from pliego_esp.graph.nodes.add_other_adicionales import add_other_adicionales
from pliego_esp.graph.nodes.review_other_adicionales import review_other_adicionales
from pliego_esp.graph.nodes.add_unassigned_parameters import add_unassigned_parameters
from pliego_esp.graph.nodes.review_unassigned_parameters import review_unassigned_parameters
from pliego_esp.graph.nodes.process_pliego import process_pliego
from pliego_esp.graph.state import State

from pliego_esp.graph.nodes.clean_and_capture_sections import clean_and_capture_sections
from pliego_esp.graph.nodes.parse_adicionales import parse_adicionales
from pliego_esp.graph.nodes.match_adicionales import match_adicionales
from pliego_esp.graph.nodes.parse_parametros import parse_parametros
from pliego_esp.graph.nodes.match_parametros_clave import match_parametros_clave
from pliego_esp.graph.nodes.unassigned_parameters import unassigned_parameters

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

async def create_workflow(memory_saver: MemorySaver) -> CompiledStateGraph:
    # Crear el grafo de estado que maneja el flujo de trabajo
    workflow = StateGraph(State)

    # # Agregar los nodos al workflow con el callback_handler compartido
    workflow.add_node("clean_and_capture_sections", clean_and_capture_sections)
    
    # # Primer flujo paralelo
    workflow.add_node("parse_adicionales", parse_adicionales)
    workflow.add_node("match_adicionales", match_adicionales)
    
    # # Segundo flujo paralelo
    workflow.add_node("parse_parametros", parse_parametros)
    workflow.add_node("match_parametros_clave", match_parametros_clave)
    workflow.add_node("unassigned_parameters", unassigned_parameters)

    # # Tercer flujo convergente
    workflow.add_node("process_pliego", process_pliego)
    workflow.add_node("review_unassigned_parameters", review_unassigned_parameters)
    workflow.add_node("add_unassigned_parameters", add_unassigned_parameters)
    workflow.add_node("review_other_adicionales", review_other_adicionales)
    workflow.add_node("add_other_adicionales", add_other_adicionales)
    workflow.add_node("add_finales", add_finales)
    
    
    # FLUJO DE TRABAJO
    workflow.set_entry_point("clean_and_capture_sections")
    
    # # Primer flujo paralelo
    workflow.add_edge("clean_and_capture_sections", "parse_adicionales")
    workflow.add_edge("parse_adicionales", "match_adicionales")
    
    # Segundo flujo paralelo
    workflow.add_edge("clean_and_capture_sections", "parse_parametros")  
    workflow.add_edge("parse_parametros", "match_parametros_clave")
    workflow.add_edge("match_parametros_clave", "unassigned_parameters")
    
    # Convergencia de flujos
    workflow.add_edge(
        ["unassigned_parameters", "match_adicionales"], 
        "process_pliego")
    
    # Flujo final
    workflow.add_edge("process_pliego", "review_unassigned_parameters")
    
    # workflow.set_entry_point("review_unassigned_parameters")
    workflow.add_edge("review_unassigned_parameters", "add_unassigned_parameters")
    workflow.add_edge("add_unassigned_parameters", "review_other_adicionales")
    workflow.add_edge("review_other_adicionales", "add_other_adicionales")
    workflow.add_edge("add_other_adicionales", "add_finales")
    workflow.add_edge("add_finales", END)
    
        
    # Compilar el workflow con el memory_saver para mantener el estado entre ejecuciones
    return workflow.compile(checkpointer=memory_saver, debug=False)