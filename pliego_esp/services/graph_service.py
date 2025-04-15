import asyncio
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage
from langchain_core.load import load, dumpd

from pliego_esp.graph.state import State
from pliego_esp.models import TokenCost
from pliego_esp.compile_graphs import get_workflow

from rich.console import Console
from asgiref.sync import sync_to_async

console = Console()

class PliegoEspService:
    @staticmethod
    async def process_message(input: str, config: RunnableConfig, user=None) -> dict:
        """
        Procesa un mensaje y retorna la respuesta del chatbot.
        
        Args:
            message: El mensaje del usuario
            conversation_id: ID de la conversación
            user: Usuario autenticado (opcional)
            
        Returns:
            dict: Respuesta del chatbot con información de tokens
        """
        # Obtener el workflow y memory_saver
        workflow = get_workflow()
        if workflow is None:
            return {
                "response": "Error: El sistema no está inicializado correctamente. Por favor, contacte al administrador.",
                "token_cost": 0
            }
        
        # Obtener los valores de credits y total_cost del usuario actual
        try:
            token_cost = await sync_to_async(TokenCost.objects.get)(user=user)
            credits = token_cost.credits
            total_cost = token_cost.total_cost
            ratio = total_cost/credits*100
            if ratio > 100:
                return {
                    "response": "No tienes suficientes créditos para continuar. Por favor, actualiza tu plan.",
                    "token_cost": 0
                }
        except TokenCost.DoesNotExist:
            credits = 0.5  # Valor por defecto
            total_cost = 0
        
        # Inicializar el estado con el mensaje del usuario
        initial_state = State(
            messages=[HumanMessage(content=input)]
        )
        
        # Procesar el mensaje y obtener el estado
        result = await workflow.ainvoke(initial_state, config)

        state = workflow.get_state(config)
        
        response = result["messages"][-1]
    
        return {
            "response": response.content,
            "token_cost": state.values.get("token_cost", 0)
        }
    
