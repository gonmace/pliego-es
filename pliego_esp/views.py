from django.shortcuts import render
from asgiref.sync import async_to_sync
from langchain_core.runnables import RunnableConfig
import uuid
import os
from pathlib import Path
from django.contrib.auth.decorators import login_required

from pliego_esp.services.graph_service import PliegoEspService

# Definir la ruta al archivo Markdown del pliego base
PLIEGO_BASE_PATH = Path(__file__).resolve().parent / "pliegos_base" / "pintado_de_piso_industrial[].md"

# Función para cargar el contenido del pliego base desde el archivo Markdown
def load_pliego_base():
    if os.path.exists(PLIEGO_BASE_PATH):
        with open(PLIEGO_BASE_PATH, 'r', encoding='utf-8') as file:
            return file.read()
    else:
        return "Pliego de especificaciones base."

especificacion = {
    "pliego_base": load_pliego_base(),
    "titulo": "Pintado de piso industrial",
    "parametros_clave": ["Acabado texturizado", "Pintura de 3 colores", "Empleo de compresor"],
    "adicionales": ["Retiro de recubrimientos antiguos"]
    # "parametros_clave": [],
    # "adicionales": []
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
    
    # Procesamos el mensaje usando el servicio
    response_data = await PliegoEspService.process_message(
        input=especificacion,
        config=config,
        user=request.user
    )
    
    # Renderizar la plantilla con los datos de respuesta
    return render(request, 'pliego_especificaciones.html', {
        'response': response_data['response'],
        'token_cost': response_data['token_cost'],
        'conversation_id': conversation_id,
        'user': request.user
    })

# Opcional: Si quieres que solo los usuarios autenticados puedan acceder a esta vista
# @login_required
def pliego_especificaciones(request):
    return async_to_sync(pliego_especificaciones_async)(request)
