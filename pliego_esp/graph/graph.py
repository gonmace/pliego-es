import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from langchain_core.runnables import RunnableConfig
from graph_retriever.strategies import Eager
from langgraph.checkpoint.memory import MemorySaver

from pliego_esp.graph.configuration import Configuration
from pliego_esp.graph.state import State

from pliego_esp.graph.nodes.relevance_check import RelevanceCheckNode
from pliego_esp.graph.nodes.process_input import process_input
from pliego_esp.graph.nodes.rewrite_query_by_context import rewrite_query_by_context
from pliego_esp.graph.nodes.rewrite_query_for_retriever import QueryRewriter
from pliego_esp.graph.nodes.retrieve_documents import RetrieveDocuments
from pliego_esp.graph.nodes.off_topic_query import off_topic_response
from pliego_esp.graph.nodes.inicio import inicio

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


# Crear un único MemorySaver para toda la aplicación
# Este objeto se encarga de mantener el estado entre ejecuciones

async def create_workflow(memory_saver: MemorySaver) -> tuple[StateGraph, MemorySaver]:
    """
    Crea y configura el workflow principal del sistema.
    
    Args:
        config (RunnableConfig): Configuración que contiene los parámetros necesarios
                               para inicializar los componentes del workflow.
    
    Returns:
        CompiledStateGraph: El workflow compilado y listo para ser ejecutado.
    """
    # Extraer la configuración del RunnableConfig
    configuration = Configuration.from_runnable_config()

    # Configurar el modelo de chat con parámetros específicos
    model_chat = ChatOpenAI(
        model=configuration.llm_chat_model,
        temperature=0.1,  # Baja temperatura para respuestas más deterministas
        )
    
    # Inicializar los nodos del workflow
    
    # Nodo para verificar la relevancia de las consultas
    # Utiliza un vectorstore para comparar la similitud de la consulta con el contexto
    relevance_check = RelevanceCheckNode(
        vectorstore=configuration.vectorstore,
        threshold=0.35 # Umbral de similitud para considerar una consulta relevante
        )
    
    # Nodo para reescribir las consultas
    # Mejora las consultas basándose en el contexto histórico
    query_rewriter = QueryRewriter(
        model=model_chat,
        )
    
    # Nodo para recuperar documentos relevantes
    # Configurado para buscar en documentos específicos del código civil y procesal
    retrieve_documents = RetrieveDocuments(
        vectorstore=configuration.vectorstore,
        edges=[("id", "ID_Original")],  # Configuración de las relaciones entre documentos
        strategy=Eager(k=5, start_k=4, max_depth=1),  # Estrategia de búsqueda con parámetros optimizados
        documento_filter=["CODIGO CIVIL (SUBFRAGMENTOS)", "CODIGO PROCESAL CIVIL (SUBFRAGMENTOS)"],  # Tipos de documentos a buscar
        umbral_contexto=0.6  # Umbral de similitud para el contexto
    )

    # Función auxiliar para verificar si hay contexto disponible
    # Retorna True si hay contexto, False si está vacío
    async def check_context(state: State) -> bool:
        if state["context"] != "":
            return True
        else:
            return False



    # Crear el grafo de estado que maneja el flujo de trabajo
    workflow = StateGraph(State)

    # Agregar los nodos al workflow
    workflow.add_node("inicio", inicio)
    # workflow.add_node("rewrite_query_by_context", rewrite_query_by_context)
    # workflow.add_node("relevance_check", relevance_check)
    # workflow.add_node("off_topic_query", off_topic_response)
    # workflow.add_node("rewrite_query_for_retriever", query_rewriter)
    # workflow.add_node("retrieve_documents", retrieve_documents)
    # workflow.add_node("process_input", process_input)
    # workflow.add_node("evaluate_summarizing", evaluate_summarizing)
    
    # Configurar el flujo de trabajo:
    # 1. Comienza con la reescritura de la consulta basada en el contexto
    # workflow.set_entry_point("rewrite_query_by_context")
    # workflow.add_edge("inicio", "rewrite_query_by_context")
    # workflow.add_edge("rewrite_query_by_context", "relevance_check")
    # 2. Verifica la relevancia de la consulta
    # Si es relevante, continúa con la reescritura para el retriever
    # Si no es relevante, termina con una respuesta de fuera de tema
    # workflow.add_conditional_edges("relevance_check", 
    #                                RelevanceCheckNode.check_relevance,
    #                                {
    #                                    True: "rewrite_query_for_retriever",
    #                                    False: END
    #                                    }
    #                                )

    # # 4. Continúa con la reescritura de la consulta y recuperación de documentos
    workflow.set_entry_point("inicio")
    workflow.add_edge("inicio", END)
    
    # # 5. Verifica si se encontró contexto relevante
    # # Si hay contexto, procesa la entrada para generar la respuesta
    # # Si no hay contexto, termina con una respuesta de fuera de tema
    # workflow.add_conditional_edges("retrieve_documents", check_context,
    #                                {True: "process_input",
    #                                 False: "off_topic_query"}
    #                                )
    # workflow.add_edge("off_topic_query", END)
    # # 6. Procesa la entrada y termina el workflow
    # workflow.add_edge("process_input", END)

    # Compilar el workflow con el memory_saver para mantener el estado entre ejecuciones
    return workflow.compile(checkpointer=memory_saver)


