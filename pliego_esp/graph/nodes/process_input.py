from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage
from langchain_community.callbacks.openai_info import OpenAICallbackHandler

from pliego_esp.graph.configuration import Configuration
from pliego_esp.graph.state import State

from rich.console import Console
console = Console()

async def process_input(state: State, *, config: RunnableConfig) -> State:
    """
    Procesa la consulta del usuario y genera una respuesta utilizando un modelo de lenguaje.
    
    Args:
        state: Estado actual de la conversación
        config: Configuración del proceso de ejecución
    """
    configuration = Configuration.from_runnable_config(config)
    
    console.print("---process_input---", style="bold cyan")
    
    # Get context from retriever if exists
    context = state.get("context", "")
        
    # Create prompt template
    system_message_content = (
    "You are an assistant with knowledge in law for question-answering tasks. "
    "Use the following retrieved context fragments to answer the question. "
    "If you don't know the answer, simply say that you don't know. "
    "If the question refers to a single article, mention the article number. "
    "Only respond in Spanish. \n"
    "Context: {context} \n"
    )
    
    # Format the prompt with context and question
    formatted_prompt = system_message_content.format(
        context=context
        )
    
    # Crear el mensaje del sistema
    system_message = SystemMessage(content=formatted_prompt)
    
    # Asegurarse de que el historial de mensajes se mantenga y agregar el nuevo mensaje
    messages =  [system_message] + state.get("messages", [])
    
    # Crear el modelo
    llm_chat = ChatOpenAI(
        model_name=configuration.llm_chat_model,
        temperature=0.1,
    )
    
    callback_handler = OpenAICallbackHandler()
    
    response = await llm_chat.ainvoke(
        messages,
        config={"callbacks":[callback_handler]}
        )

    print(f"Prompt Tokens: {callback_handler.prompt_tokens}")
    print(f"Completion Tokens: {callback_handler.completion_tokens}")
    print(f"Successful Requests: {callback_handler.successful_requests}")
    print(f"Total Cost (USD): ${callback_handler.total_cost}")
    state["token_cost"] += callback_handler.total_cost
    console.print(f"Total Cost Acumulated (USD): ${state['token_cost']}", style="bold cyan")
    console.print("-"*20, style="bold cyan")
    
    state["messages"] = response
    return state