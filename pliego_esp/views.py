# views.py
from django.shortcuts import render, redirect
from asgiref.sync import async_to_sync, sync_to_async
from langchain_core.runnables import RunnableConfig
import uuid
import os
import json
from pathlib import Path
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
# import markdown

from pliego_esp.forms import PliegoForm
# from pliego_esp.graph import ttest_node
from pliego_esp.services.graph_service import PliegoEspService

from rich.console import Console
console = Console()

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
    "parametros_clave": ["Acabado texturizado", "Pintura de 3 colores", "Empleo de compresor", "Realizar revoque"],
    "adicionales": ["Retiro de recubrimientos antiguos"]
    # "parametros_clave": [],
    # "adicionales": []
}

# @login_required
@csrf_exempt
def pliego_especificaciones_view(request):
    if request.method == "POST":
        request_type = request.POST.get('request_type')

        if request_type == "inicio":
            
            form = PliegoForm(request.POST)
            if form.is_valid():
                
                especificacion = {
                    "pliego_base": form.cleaned_data["pliego_base"],
                    "titulo": form.cleaned_data["titulo"],
                    "parametros_clave": [param.strip() for param in form.cleaned_data["parametros_clave"].split(",")],
                    "adicionales": [adicional.strip() for adicional in form.cleaned_data["adicionales"].split(",")]
                }
                
                # Configurar el RunnableConfig
                conversation_id = str(uuid.uuid4())
                config = RunnableConfig(
                    recursion_limit=10,
                    configurable={
                        "thread_id": conversation_id,
                        "user": request.user.username
                        }
                    )
                # Procesamos el mensaje usando el servicio de forma asíncrona
                response_data = async_to_sync(PliegoEspService.process_pliego)(
                    input=especificacion,
                    config=config
                    )
                
                if response_data["type"] == "__interrupt__":
                    return JsonResponse({
                        'type': response_data["type"],
                        'action': response_data["action"],
                        'items': response_data['items'],
                        'config': response_data['config'],
                    })
            
        else:
            resume = json.loads(request.POST.get('items'))
            config = json.loads(request.POST.get('config'))
            
            response_data = async_to_sync(PliegoEspService.process_pliego)(
                input=resume,
                config=config,
                resume_data=True
            )

            return JsonResponse({
                'content': response_data.get('content', ''),
                'token_cost': response_data.get('token_cost', 0),
                'conversation_id': response_data.get('conversation_id', '')
            })
            
    else:
        form = PliegoForm()
    
    return render(request, "pliego_especificaciones.html", {"form": form})