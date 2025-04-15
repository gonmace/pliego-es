from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder
    )
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_community.callbacks.openai_info import OpenAICallbackHandler

from pliego_esp.utils.utils import get_message_text
from pliego_esp.graph.configuration import Configuration
from pliego_esp.graph.state import State

from rich.console import Console
console = Console()

async def rewrite_query_by_context(state: State, *, config: RunnableConfig) -> State:
    """
    Genera una consulta de búsqueda basada en el estado y la configuración actuales.
    
    Args:
        state: Estado actual de la conversación
        config: Configuración del proceso de ejecución
        
    Returns:
        Estado actualizado con la consulta procesada
    """    
    console.print("---rewrite_query_by_context---", style="bold yellow")

    # Obtener los últimos 4 mensajes del historial para mantener el contexto relevante
    messages = state['messages'][-4:]
    
    human_input = get_message_text(messages[-1])
    
    if len(messages) == 1:
        # Caso especial: primera pregunta del usuario
        # En este caso, usamos la entrada directamente sin modificación
        state["query"] = [human_input]
        
        console.print(f"Query sin modificar generada (primer mensaje): {state["query"]}", style="bold red")
        console.print("-" * 20, style="bold yellow")
        return state

    else:
        # Configuración del modelo de chat con temperatura baja para respuestas más deterministas
        configuration = Configuration.from_runnable_config(config)

        chat_model = ChatOpenAI(
            model_name=configuration.llm_chat_model,
            temperature=0,
        )
        
        human_message = HumanMessage(content=human_input)
        
        messages = state.get("messages", [])

        # Definición del mensaje del sistema que establece las reglas para el procesamiento de consultas
        system_message = SystemMessage(
            content=(
                "You are an assistant that evaluates whether a user query is self-contained or needs prior context.\n\n"
                "Rules:\n"
                "1. If the query is clear and understandable on its own, return it EXACTLY as it was written. Do not rephrase, reword, improve, or add anything.\n"
                "2. If the query depends on previous messages to make sense (e.g. it's vague, uses pronouns like 'that', or lacks context), rewrite it using ONLY the relevant chat history to make it a standalone question.\n"
                "3. Do NOT assume anything not explicitly written in the previous messages.\n"
                "4. NEVER add explanations, comments, or extra questions. Just return the final query — unchanged or rewritten.\n\n"
                "Examples:\n"
                "User: What is possession effective?\n→ What is possession effective?\n"
                "History: My tenant hasn't paid rent in 3 months.\nUser: Can I evict him?\n→ Can I evict a tenant who hasn't paid rent in 3 months?\n"
                "User: Can I evict a tenant?\n→ Can I evict a tenant?\n"
            )
        )        

        # Creación del prompt de chat que combina el mensaje del sistema, el historial y la consulta actual
        chat_prompt = ChatPromptTemplate.from_messages(
            [system_message,
             MessagesPlaceholder(variable_name="messages"),
             human_message]
        )

        # Construcción de la cadena de procesamiento que transformará la consulta
        query_transformation_chain = chat_prompt | chat_model | StrOutputParser()
        
        callback_handler = OpenAICallbackHandler()
        
        # Procesamiento asíncrono de la consulta usando el historial de mensajes
        consulta = await query_transformation_chain.ainvoke(
            {"messages": messages},
            config={"callbacks":[callback_handler]}
            )

        # Actualización del estado con la consulta procesada y la información de tokens
        state["query"] = [consulta]
        
        # Visualización de la consulta original y la reescrita para debugging
        console.print(f"Query original: {get_message_text(messages[-1])}", style="yellow")
        console.print(f"Query reescrita: {consulta}", style="bold yellow")
        print(f"Prompt Tokens: {callback_handler.prompt_tokens}")
        print(f"Completion Tokens: {callback_handler.completion_tokens}")
        print(f"Successful Requests: {callback_handler.successful_requests}")
        print(f"Total Cost (USD): ${callback_handler.total_cost}")
        state["token_cost"] = state["token_cost"] + callback_handler.total_cost
        console.print("-" * 20, style="bold yellow")
        return state