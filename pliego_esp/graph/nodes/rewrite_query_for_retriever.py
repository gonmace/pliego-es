from langchain_core.prompts import PromptTemplate
from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.runnables import RunnableLambda
from langchain_community.callbacks.openai_info import OpenAICallbackHandler

from pliego_esp.graph.state import State

from rich.console import Console

console = Console()

# Prompt para dividir y ajustar consulta para retrieval
split_and_prepare_prompt = PromptTemplate.from_template("""
You are an assistant helping to process user queries for a legal document retriever.

Given a user's question, follow these steps:
1. If the question includes multiple parts or topics, split it into separate standalone questions.
2. If the question is already simple and focused, return it as-is.
3. For each resulting question, rewrite it to be as clear and precise as possible, using legal terms if relevant.

Query: "{query}"

Return the final list of queries (1 per line, no numbering):
""")

class QueryRewriter:
    def __init__(
        self, model: BaseLanguageModel,
        ):
        self.model = model

        """
        Args:
            model (BaseLanguageModel): Modelo de lenguaje a utilizar.
        """


    async def __call__(self, state: State) -> State:
        """
        Reformula la consulta proporcionada usando el contexto anterior.

        Args:
            state (State): Estado actual con las consultas y mensajes.
            config (RunnableConfig): Configuración para el modelo de lenguaje.

        Returns:
            State: Estado actualizado con la consulta reformulada.
        """
        # Determinar la consulta más reciente
        console.print("---rewrite_query_for_retriever---", style="bold magenta")
        console.print("Reformula la consulta para el retriever", style="magenta")

        query = state["query"][0]
        console.print(f"Query original: {query}", style="magenta")

        # Crear el reescritor de consultas
        chain = split_and_prepare_prompt | self.model | RunnableLambda(
            lambda msg: msg.content.strip().split("\n")
            )
        
        callback_handler = OpenAICallbackHandler()
        
        # Ejecutar la reformulación de la consulta
        subqueries  = await chain.ainvoke(
            {"query": query},
            config={"callbacks":[callback_handler]}
        )

        state["query"] = subqueries

        console.print(f"Subqueries: {subqueries}", style="bold magenta")
        print(f"Prompt Tokens: {callback_handler.prompt_tokens}")
        print(f"Completion Tokens: {callback_handler.completion_tokens}")
        print(f"Successful Requests: {callback_handler.successful_requests}")
        print(f"Total Cost (USD): ${callback_handler.total_cost}")
        state["token_cost"] = state["token_cost"] + callback_handler.total_cost
        console.print(f"Total Cost Acumulated (USD): ${state['token_cost']}", style="bold magenta")
        console.print("-" * 20, style="bold magenta")

        return state
