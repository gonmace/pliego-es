from django.shortcuts import render
from asgiref.sync import async_to_sync
from langchain_core.runnables import RunnableConfig
import uuid
import os
from pathlib import Path

from pliego_esp.services.graph_service import PliegoEspService

# Definir la ruta al archivo Markdown del pliego base
PLIEGO_BASE_PATH = Path(__file__).resolve().parent / "templates" / "pliego_base.md"

# Función para cargar el contenido del pliego base desde el archivo Markdown
def load_pliego_base():
    if os.path.exists(PLIEGO_BASE_PATH):
        with open(PLIEGO_BASE_PATH, 'r', encoding='utf-8') as file:
            return file.read()
    else:
        return "Pliego de especificaciones base."

especificaciones = {
    "pliego_base": load_pliego_base(),
    "parametros": "Parametros de la especificación",
    "adicionales": "Actividades adicionales de la especificación"
}

async def pliego_especificaciones_async(request):
    # Generar un ID de conversación único
    conversation_id = str(uuid.uuid4())
    
    # Configurar el RunnableConfig
    config = RunnableConfig(
        recursion_limit=10,
        configurable={
            "thread_id": conversation_id
        }
    )
    
    # Mensaje inicial para el procesamiento
    initial_message = "Que puedes hacer."
    
    # Procesamos el mensaje usando el servicio
    response_data = await PliegoEspService.process_message(
        input=initial_message,
        config=config,
        user=request.user
    )
    
    # Renderizar la plantilla con los datos de respuesta
    return render(request, 'pliego_especificaciones.html', {
        'response': response_data['response'],
        'token_cost': response_data['token_cost'],
        'conversation_id': conversation_id
    })

def pliego_especificaciones(request):
    return async_to_sync(pliego_especificaciones_async)(request)
