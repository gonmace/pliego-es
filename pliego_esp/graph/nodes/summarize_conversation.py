from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage
from langchain_community.callbacks.openai_info import OpenAICallbackHandler

from rag_legal.graph.configuration import Configuration
from rag_legal.graph.state import State

from rich.console import Console
console = Console()

async def summarize_conversation(state: State, *, config: RunnableConfig) -> State:
    """
    Genera un resumen de la conversación actual.
    
    Args:
        state: Estado actual de la conversación
        config: Configuración del proceso de ejecución
    """
    console.print("---summarize_conversation---", style="bold magenta")
    
    # Obtener el resumen existente si hay uno
    current_summary = state.get("summary", "")
    
    # Crear el prompt para el resumen
    if current_summary:
        summary_prompt = (
            f"""Este es el resumen actual de la conversación:
            {current_summary}
            
            Por favor, actualiza el resumen con la información más reciente de la conversación.
            Mantén el formato y estructura del resumen existente.
            """
        )
    else:
        summary_prompt = """Por favor, genera un resumen de la conversación actual.
        Incluye los puntos principales discutidos y cualquier información relevante.
        """
    
    # Crear el mensaje del sistema
    system_message = SystemMessage(content=summary_prompt)
    
    # Obtener los últimos mensajes de la conversación
    messages = [system_message] + state["messages"][-4:]  # Últimos 4 mensajes para contexto
    
    # Crear el modelo
    llm_chat = ChatOpenAI(
        model_name=Configuration.llm_chat_model,
        temperature=0.1
    )
    
    callback_handler = OpenAICallbackHandler()
    
    # Generar el resumen
    response = await llm_chat.ainvoke(
        messages,
        config={"callbacks":[callback_handler]}
        )
    
    # Actualizar el estado con el nuevo resumen
    state["summary"] = response.content
    
    console.print("Resumen generado:", style="bold magenta")
    print(f"Prompt Tokens: {callback_handler.prompt_tokens}")
    print(f"Completion Tokens: {callback_handler.completion_tokens}")
    print(f"Successful Requests: {callback_handler.successful_requests}")
    print(f"Total Cost (USD): ${callback_handler.total_cost}")
    state["token_cost"] = callback_handler.total_cost
    console.print(f"Total Cost Acumulated (USD): ${state['token_cost']}", style="bold magenta")
    console.print("-"*20, style="bold magenta")
    
    return state 