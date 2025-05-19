# views.py
import sys
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
import openai
from django.conf import settings
import markdown

from pliego_esp.forms import PliegoForm
# from pliego_esp.graph import ttest_node
from pliego_esp.services.graph_service import PliegoEspService
from pliego_esp.utils.mejorar_titulo import mejorar_titulo_especificacion
from pliego_esp.utils.similitud_titulos import calcular_similitud_titulos

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
                    recursion_limit=100,
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
                    return JsonResponse({
                        'content': response_data.get('content', ''),
                        'token_cost': response_data.get('token_cost', 0),
                        'conversation_id': response_data.get('conversation_id', '')
                    })
            
        else:
            resume = json.loads(request.POST.get('items'))
            config = json.loads(request.POST.get('config'))
            
            response_data = async_to_sync(PliegoEspService.process_pliego)(
                input=resume,
                config=config,
                resume_data=True
            )
            
            if response_data["type"] == "__interrupt__":
                return JsonResponse({
                    'type': response_data["type"],
                    'action': response_data["action"],
                    'items': response_data['items'],
                    'config': response_data['config'],
                })

            return JsonResponse({
                'content': response_data.get('content', ''),
                'token_cost': response_data.get('token_cost', 0),
                'conversation_id': response_data.get('conversation_id', '')
            })
            
    else:
        form = PliegoForm()
    
    return render(request, "pliego_especificaciones.html", {"form": form})


@csrf_exempt
def mejorar_titulo(request):
    if request.method == 'POST':
        try:
            # Decodificar el body como UTF-8
            body = request.body.decode('utf-8')
            print(f"Body recibido: {body}")
            
            data = json.loads(body)
            titulo_especificacion = data.get('titulo_especificacion', '')
            
            if not titulo_especificacion:
                return JsonResponse({'error': 'La especificación está vacía'}, status=400)
            
            resultado = mejorar_titulo_especificacion(titulo_especificacion)
            
            if resultado['success']:
                return JsonResponse({
                    'success': True,
                    'titulo_especificacion_mejorado': resultado['titulo_especificacion_mejorado']
                })
            else:
                return JsonResponse({'error': resultado['error']}, status=500)
            
        except Exception as e:
            print(f"Error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

def extraer_parametros_tecnicos(contenido):
    """Extrae los parámetros técnicos de un documento Markdown."""
    import re
    
    # Buscar la sección de parámetros técnicos
    patron = r"### Parámetros Técnicos\n\n(.*?)(?=\n\n###|\Z)"
    match = re.search(patron, contenido, re.DOTALL)
    
    if not match:
        return []
    
    # Extraer la tabla
    tabla = match.group(1)
    lineas = tabla.strip().split('\n')
    
    # Procesar la tabla
    parametros = []
    for linea in lineas[2:]:  # Saltar las líneas de encabezado y separador
        if linea.strip():
            # Dividir por el carácter | y limpiar espacios
            columnas = [col.strip() for col in linea.split('|') if col.strip()]
            if len(columnas) >= 2:
                parametro = {
                    'nombre': columnas[0],
                    'opciones': columnas[1].split(', ') if len(columnas) > 1 else [],
                    'valor_defecto': columnas[2] if len(columnas) > 2 else None
                }
                parametros.append(parametro)
    
    return parametros

def extraer_adicionales(contenido):
    """Extrae los adicionales de un documento Markdown."""
    import re
    
    # Buscar la sección de adicionales
    patron = r"### Adicionales\n\n(.*?)(?=\n\n###|\Z)"
    match = re.search(patron, contenido, re.DOTALL)
    
    if not match:
        return []
    
    # Extraer la lista de adicionales
    adicionales_texto = match.group(1)
    lineas = adicionales_texto.strip().split('\n')
    
    # Procesar los adicionales
    adicionales = []
    for linea in lineas:
        if linea.strip():
            # Extraer el texto entre ** si existe
            match = re.search(r'\*\*(.*?)\*\*:\s*(.*)', linea)
            if match:
                nombre = match.group(1).strip()
                descripcion = match.group(2).strip()
                adicionales.append({
                    'nombre': nombre,
                    'descripcion': descripcion
                })
    
    return adicionales

@csrf_exempt
def nuevo_pliego_view(request):
    pasos = [
        {"numero": 1, "nombre": "Nombre Actividad"},
        {"numero": 2, "nombre": "Especificación Técnica Base"},
        {"numero": 3, "nombre": "Parámetros Técnicos"},
        {"numero": 4, "nombre": "Actividades Adicionales"},
        {"numero": 5, "nombre": "Generar Pliego"},
    ]
    paso_actual = int(request.GET.get('paso', 1))

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            paso = data.get('paso', 1)

            if paso == 1:
                print("Procesando paso 1", file=sys.stderr)
                # Obtener datos del paso 1
                titulo_original = data.get('titulo_original', '')
                titulo_sugerido = data.get('titulo_sugerido', '')
                titulo_final = data.get('titulo_final', '')
                
                # Guardar en la sesión
                request.session['paso1_data'] = {
                    'titulo_original': titulo_original,
                    'titulo_sugerido': titulo_sugerido,
                    'titulo_final': titulo_final,
                    'sugerencia_aceptada': titulo_final == titulo_sugerido
                }
                
                return JsonResponse({
                    'success': True,
                    'message': 'Datos del paso 1 guardados correctamente',
                    'paso': paso + 1
                })
            elif paso == 2:
                print("Procesando paso 2", file=sys.stderr)
                # Calcular similitud entre títulos
                paso1_data = request.session.get('paso1_data', {})
                titulo_original = paso1_data.get('titulo_original', '')
                titulo_sugerido = paso1_data.get('titulo_sugerido', '')
                
                resultado_similitud = calcular_similitud_titulos(titulo_original, titulo_sugerido)
                
                if resultado_similitud['success']:
                    # Encontrar el documento con mejor score
                    mejor_score = max(resultado_similitud['estadisticas']['mejor_score_original'], 
                                    resultado_similitud['estadisticas']['mejor_score_sugerido'])
                    
                    mejor_documento = resultado_similitud['ranking'][0]['document']
                    nombre_archivo = resultado_similitud['ranking'][0]['nombre_archivo']
                    
                    if mejor_documento:
                        request.session['paso2_data'] = {
                            'mejor_documento': mejor_documento,
                            'nombre_archivo': nombre_archivo,
                            'mejor_score': mejor_score
                        }
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Análisis de similitud completado',
                        'ranking': resultado_similitud['ranking'],
                        'estadisticas': resultado_similitud['estadisticas']
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': resultado_similitud.get('error', 'Error desconocido')
                    }, status=500)
            
            elif paso == 3:
                print("Procesando paso 3", file=sys.stderr)
                
                # Si es una solicitud GET o si no hay parámetros en el request, cargar la tabla
                if request.method == 'GET' or not data.get('parametros'):
                    # Obtener el nombre del archivo base
                    archivo_base = request.session.get('paso2_data', {}).get('nombre_archivo', '')
                    ruta_archivo = os.path.join(settings.MEDIA_ROOT, 'Markdowns', archivo_base)
                    
                    # Leer el contenido del archivo
                    try:
                        with open(ruta_archivo, 'r', encoding='utf-8') as file:
                            contenido = file.read()
                            
                            # Extraer parámetros técnico
                            parametros = extraer_parametros_tecnicos(contenido)
                            
                            return JsonResponse({
                                'success': True,
                                'message': 'Parámetros extraídos correctamente',
                                'parametros_tecnicos': parametros,
                            })
                    except Exception as e:
                        console.print(f"Error al leer el archivo: {str(e)}", style="bold red")
                        return JsonResponse({
                            'success': False,
                            'error': f'Error al leer el archivo: {str(e)}'
                        }, status=500)
                
                # Si hay parámetros en el request, guardarlos en la sesión
                else:
                    parametros = data.get('parametros', [])
                    
                    parametros_con_valor = [param for param in parametros if param.get('valor')]
                    
                    request.session['paso3_data'] = {
                        'parametros': parametros_con_valor,
                        'recomendaciones': [param.get('recomendacion', '') for param in parametros_con_valor]
                    }
                    
                    console.print("Parámetros guardados correctamente", style="bold green")
                    console.print(parametros_con_valor)
                
                    return JsonResponse({
                        'success': True,
                        'message': 'Parámetros guardados correctamente',
                        'paso': paso + 1,
                        'parametros': parametros_con_valor
                    })
            elif paso == 4:
                print("Procesando paso 4", file=sys.stderr)
                
                # Si es una solicitud GET o si no hay adicionales en el request, cargar la tabla
                if request.method == 'GET' or not data.get('adicionales'):
                    # Obtener el nombre del archivo base
                    archivo_base = request.session.get('paso2_data', {}).get('nombre_archivo', '')
                    ruta_archivo = os.path.join(settings.MEDIA_ROOT, 'Markdowns', archivo_base)
                    
                    # Leer el contenido del archivo
                    try:
                        with open(ruta_archivo, 'r', encoding='utf-8') as file:
                            contenido = file.read()
                            
                            # Extraer adicionales
                            adicionales = extraer_adicionales(contenido)
                            
                            return JsonResponse({
                                'success': True,
                                'message': 'Adicionales extraídos correctamente',
                                'adicionales': adicionales,
                            })
                    except Exception as e:
                        console.print(f"Error al leer el archivo: {str(e)}", style="bold red")
                        return JsonResponse({
                            'success': False,
                            'error': f'Error al leer el archivo: {str(e)}'
                        }, status=500)
                
                # Si hay adicionales en el request, guardarlos en la sesión
                else:
                    adicionales = data.get('adicionales', [])
                    request.session['paso4_data'] = {
                        'adicionales': adicionales
                    }
                    
                    console.print("Adicionales guardados correctamente", style="bold green")
                    console.print(adicionales)
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Adicionales guardados correctamente',
                        'paso': paso + 1,
                        'adicionales': adicionales
                    })
            elif paso == 5:
                print("Procesando paso 5", file=sys.stderr)
                return JsonResponse({
                    'success': True,
                    'message': 'Paso 5 procesado correctamente',
                    'paso': paso
                })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    # Para GET requests, incluir los datos del paso 1 y similitud si existen
    paso1_data = request.session.get('paso1_data', {})
    paso2_data = request.session.get('paso2_data', {})
    paso3_data = request.session.get('paso3_data', {})
    paso4_data = request.session.get('paso4_data', {})
    
    return render(request, 'pasos.html', {
        'pasos': pasos,
        'paso_actual': paso_actual,
        'paso1_data': paso1_data,
        'paso2_data': paso2_data,
        'paso3_data': paso3_data,
        'paso4_data': paso4_data
    })

@csrf_exempt
def generar_pliego(request):
    if request.method == "POST":
        request_type = request.POST.get('request_type')
        if request_type == "inicio":
            console.print("Generando pliego", style="bold green")
            archivo_base = request.session.get('paso2_data', {}).get('nombre_archivo', '')
            ruta_archivo = os.path.join(settings.MEDIA_ROOT, 'Markdowns', archivo_base)
            
            contenido_pliego = ""
            try:
                with open(ruta_archivo, 'r', encoding='utf-8') as file:
                    contenido_pliego = file.read()
                    
            except Exception as e:
                console.print(f"Error al leer el archivo: {str(e)}", style="bold red")
                return JsonResponse({
                    'success': False,
                    'error': f'Error al leer el archivo: {str(e)}'
                }, status=500)
            
            titulo_pliego = request.session.get('paso1_data', {}).get('titulo_final', '')
            parametros_tecnicos = request.session.get('paso3_data', {}).get('parametros', [])
            adicionales = request.session.get('paso4_data', {}).get('adicionales', [])
            
            # console.print(titulo_pliego, style="bold green")
            # console.print(parametros_tecnicos, style="bold green")
            # console.print(adicionales, style="bold green")
            # console.print(contenido_pliego, style="bold red")
            
            especificacion = {
                "pliego_base": contenido_pliego,
                "titulo": titulo_pliego,
                "parametros_clave": parametros_tecnicos,
                "adicionales": adicionales
            }
            
            # Configurar el RunnableConfig
            conversation_id = str(uuid.uuid4())
            config = RunnableConfig(
                recursion_limit=100,
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
                return JsonResponse({
                    'content': response_data.get('content', ''),
                    'token_cost': response_data.get('token_cost', 0),
                    'conversation_id': response_data.get('conversation_id', '')
                })
        else:
            resume = json.loads(request.POST.get('items'))
            config = json.loads(request.POST.get('config'))
            
            response_data = async_to_sync(PliegoEspService.process_pliego)(
                input=resume,
                config=config,
                resume_data=True
            )
            
            if response_data["type"] == "__interrupt__":
                return JsonResponse({
                    'type': response_data["type"],
                    'action': response_data["action"],
                    'items': response_data['items'],
                    'config': response_data['config'],
                })

                        # Procesar el markdown
            extensions = [
                'markdown.extensions.extra',
                'markdown.extensions.codehilite',
                # 'markdown.extensions.tables',
                # 'markdown.extensions.nl2br',
                # 'markdown.extensions.sane_lists'
            ]
            md_generado_html = markdown.markdown(
                response_data.get('content', ''), output_format='html', extensions=extensions)
                        
            return JsonResponse({
                'content': md_generado_html,
                'token_cost': response_data.get('token_cost', 0),
                'conversation_id': response_data.get('conversation_id', '')
            })