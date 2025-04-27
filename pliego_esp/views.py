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
# import markdown

from pliego_esp.forms import PliegoForm
# from pliego_esp.graph import ttest_node
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
    "parametros_clave": ["Acabado texturizado", "Pintura de 3 colores", "Empleo de compresor", "Realizar revoque"],
    "adicionales": ["Retiro de recubrimientos antiguos"]
    # "parametros_clave": [],
    # "adicionales": []
}

@sync_to_async
def render_template(template_name, context):
    template = loader.get_template(template_name)
    return template.render(context)

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
    
    # # Procesamos el mensaje usando el servicio
    # response_data = await PliegoEspService.process_message(
    #     input=especificacion,
    #     config=config,
    #     user=None  # No usar autenticación por ahora
    # )
    # TODO cambiar por lo de arriba en produccion
    response_data = await ttest_node.run_node_only()
    
    # Renderizar la plantilla de forma asíncrona
    html = await render_template('pliego_especificaciones.html', {
        # 'response': response_data['response'],
        # 'token_cost': response_data['token_cost'],
        # 'conversation_id': conversation_id,
        # 'user': None  # No usar autenticación por ahora
    })
    
    return HttpResponse(html)

# Opcional: Si quieres que solo los usuarios autenticados puedan acceder a esta vista
# @login_required
def pliego_especificaciones_view(request):
    if request.method == "POST":
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
                    "thread_id": request.user.id if request.user.is_authenticated else conversation_id,
                    "user": request.user
                    }
                )
            # Procesamos el mensaje usando el servicio de forma asíncrona
            response_data = async_to_sync(PliegoEspService.process_message)(
                input=especificacion,
                config=config,
                user=request.user
            )
            
            # Verificar si es una solicitud AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'response': response_data.get('response', ''),
                    'token_cost': response_data.get('token_cost', 0),
                    'conversation_id': conversation_id
                })
            
            # Si no es AJAX, redirigir después de éxito
            return redirect("gracias")  # redirigir después de éxito
    else:
        form = PliegoForm()
    
    return render(request, "pliego_especificaciones.html", {"form": form})

# def pliego_especificaciones(request):
#     return async_to_sync(pliego_especificaciones_async)(request)

def gracias_view(request):
    return render(request, "gracias.html")