import asyncio
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage
from langchain_core.load import load, dumpd

from pliego_esp.graph.state import State
from pliego_esp.models import TokenCost
from pliego_esp.compile_graphs import get_workflow
from pliego_esp.graph.callbacks import shared_callback_handler

from rich.console import Console
from asgiref.sync import sync_to_async

console = Console()

class PliegoEspService:
    @staticmethod
    async def process_message(input: dict, config: RunnableConfig, user=None) -> dict:

        # Obtener el workflow y memory_saver
        workflow = get_workflow()
        if workflow is None:
            return {
                "response": "Error: El sistema no está inicializado correctamente. Por favor, contacte al administrador.",
                "token_cost": 0
            }
        
        # Obtener los valores de credits y total_cost del usuario actual
        credits = 0.5  # Valor por defecto
        total_cost = 0
        
        # Solo intentar obtener TokenCost si el usuario está autenticado
        if user and user.is_authenticated:
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
                # Si no existe un registro para este usuario, usamos los valores por defecto
                pass
        
        # Reiniciar el callback_handler antes de cada ejecución
        shared_callback_handler.total_tokens = 0
        shared_callback_handler.prompt_tokens = 0
        shared_callback_handler.completion_tokens = 0
        shared_callback_handler.successful_requests = 0
        shared_callback_handler.total_cost = 0.0
        
        # Inicializar el estado con el mensaje del usuario
        initial_state = State(
            pliego_base=input["pliego_base"],
            titulo=input["titulo"],
            parametros_clave=input["parametros_clave"],
            adicionales=input["adicionales"],
            token_cost=0.0
        )
        
        # Procesar el mensaje y obtener el estado
        result = await workflow.ainvoke(initial_state, config)

        state = workflow.get_state(config)
        
        response = result["messages"][-1]
        
        # Obtener el costo total acumulado del callback_handler compartido
        token_cost = shared_callback_handler.total_cost
    
        return {
            "response": response.content,
            "token_cost": token_cost
        }
    
