import requests
import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .forms import EspecificacionTecnicaForm

N8N_WEBHOOK_URL = 'https://jaimemc.app.n8n.cloud/webhook-test/parametros'
N8N_WEBHOOK_TITULO_URL = 'https://jaimemc.app.n8n.cloud/webhook-test/titulo'


@login_required
def n8n_pasos_view(request):
    """
    Vista principal con sistema de pasos
    """
    pasos = [
        {"numero": 1, "nombre": "Parámetros"},
        {"numero": 2, "nombre": "Título"},
        {"numero": 3, "nombre": "Adicionales"},
    ]
    paso_actual = int(request.GET.get('paso', 1))
    
    # Limpiar toda la sesión relacionada con n8n al inicio
    request.session.pop('n8n_paso1_data', None)
    request.session.pop('n8n_respuesta_api', None)
    request.session.pop('n8n_respuesta_completa', None)
    request.session.pop('n8n_actividades_adicionales', None)
    
    # Inicializar variables vacías (no usar sesión)
    datos_paso1 = {}
    respuesta_api = {}
    respuesta_completa = {}
    actividades_adicionales = {}
    
    return render(request, 'n8n/pasos.html', {
        'pasos': pasos,
        'paso_actual': paso_actual,
        'datos_paso1': datos_paso1,
        'respuesta_api': respuesta_api,
        'respuesta_completa': respuesta_completa,
        'actividades_adicionales': actividades_adicionales,
    })


@login_required
@require_http_methods(["POST"])
def guardar_paso1_view(request):
    """
    Vista AJAX para guardar datos del paso 1
    """
    try:
        data = json.loads(request.body)
        titulo = data.get('titulo', '').strip()
        descripcion = data.get('descripcion', '').strip()
        tipo_servicio = data.get('tipo_servicio', '').strip()
        
        if not titulo or not descripcion or not tipo_servicio:
            return JsonResponse({
                'success': False,
                'error': 'Título, descripción y tipo de servicio son requeridos'
            }, status=400)
        
        # No guardar en sesión
        
        return JsonResponse({
            'success': True,
            'message': 'Datos guardados exitosamente'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON inválidos'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error inesperado: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def enviar_actividades_view(request):
    """
    Vista AJAX para enviar actividades adicionales seleccionadas
    """
    try:
        data = json.loads(request.body)
        actividades_seleccionadas = data.get('actividades', [])
        
        if not actividades_seleccionadas:
            return JsonResponse({
                'success': False,
                'error': 'Debe seleccionar al menos una actividad'
            }, status=400)
        
        # Preparar payload con las actividades seleccionadas
        payload = {
            'actividades': actividades_seleccionadas
        }
        
        # Enviar POST request a la API
        # Nota: Puedes cambiar esta URL según necesites o obtenerla de la sesión
        response = requests.post(
            N8N_WEBHOOK_TITULO_URL,  # Cambiar por la URL correcta
            json=payload,
            headers={
                'Content-Type': 'application/json'
            },
            timeout=180
        )
        
        response.raise_for_status()
        
        response_data = None
        try:
            response_data = response.json()
            response_data_str = json.dumps(response_data, indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            response_data_str = f"Status Code: {response.status_code}\n\nRespuesta:\n{response.text}"
        
        return JsonResponse({
            'success': True,
            'message': 'Actividades enviadas exitosamente',
            'response_data': response_data_str,
        })
        
    except requests.exceptions.Timeout:
        return JsonResponse({
            'success': False,
            'error': 'La solicitud tardó demasiado tiempo. Por favor, intente nuevamente.'
        }, status=408)
    except requests.exceptions.RequestException as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al comunicarse con la API: {str(e)}'
        }, status=500)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON inválidos'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error inesperado: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def enviar_especificacion_view(request):
    """
    Vista AJAX para enviar título y descripción a la API de n8n
    """
    try:
        data = json.loads(request.body)
        titulo = data.get('titulo', '').strip()
        descripcion = data.get('descripcion', '').strip()
        tipo_servicio = data.get('tipo_servicio', '').strip()
        
        if not titulo or not descripcion or not tipo_servicio:
            return JsonResponse({
                'success': False,
                'error': 'Título, descripción y tipo de servicio son requeridos'
            }, status=400)
        
        # Obtener sessionID del usuario activo
        session_id = request.session.session_key or ''
        
        # Preparar los datos para enviar a la API
        payload = {
            'titulo': titulo,
            'descripcion': descripcion,
            'tipo_servicio': tipo_servicio,
            'sessionID': session_id
        }
        
        # Enviar POST request a la API webhook y esperar respuesta
        response = requests.post(
            N8N_WEBHOOK_URL,
            json=payload,
            headers={
                'Content-Type': 'application/json'
            },
            timeout=180  # Timeout de 180 segundos (3 minutos) para esperar la respuesta
        )
        
        # Verificar si la respuesta fue exitosa
        response.raise_for_status()
        
        # Intentar parsear la respuesta JSON
        response_data = None
        try:
            response_data = response.json()
            # Convertir a string formateado para mostrar en el template
            response_data_str = json.dumps(response_data, indent=2, ensure_ascii=False)
            
            # No guardar en sesión
        except json.JSONDecodeError:
            # Si no es JSON, usar el texto de la respuesta
            response_data_str = f"Status Code: {response.status_code}\n\nRespuesta:\n{response.text}"
        
        return JsonResponse({
            'success': True,
            'message': 'Datos enviados exitosamente a la API y respuesta recibida.',
            'response_data': response_data_str,
            'requiere_respuesta': response_data.get('requiere_respuesta', False) if isinstance(response_data, dict) else False,
            'pregunta': response_data.get('pregunta', '') if isinstance(response_data, dict) else '',
            'observacion': response_data.get('observacion', '') if isinstance(response_data, dict) else '',
            'titulo_actual': response_data.get('titulo_actual', '') if isinstance(response_data, dict) else '',
            'descripcion_actual': response_data.get('descripcion_actual', '') if isinstance(response_data, dict) else '',
            'titulo': response_data.get('titulo', '') if isinstance(response_data, dict) else '',
            'descripcion': response_data.get('descripcion', '') if isinstance(response_data, dict) else '',
            'has_output': bool(response_data.get('output')) if isinstance(response_data, dict) else False,
        })
        
    except requests.exceptions.Timeout:
        return JsonResponse({
            'success': False,
            'error': 'La solicitud tardó demasiado tiempo. Por favor, intente nuevamente.'
        }, status=408)
    except requests.exceptions.RequestException as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al comunicarse con la API: {str(e)}'
        }, status=500)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON inválidos'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error inesperado: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def enviar_actividades_view(request):
    """
    Vista AJAX para enviar actividades adicionales seleccionadas
    """
    try:
        data = json.loads(request.body)
        actividades_seleccionadas = data.get('actividades', [])
        
        if not actividades_seleccionadas:
            return JsonResponse({
                'success': False,
                'error': 'Debe seleccionar al menos una actividad'
            }, status=400)
        
        # Preparar payload con las actividades seleccionadas
        payload = {
            'actividades': actividades_seleccionadas
        }
        
        # Enviar POST request a la API
        # Nota: Puedes cambiar esta URL según necesites o obtenerla de la sesión
        response = requests.post(
            N8N_WEBHOOK_TITULO_URL,  # Cambiar por la URL correcta
            json=payload,
            headers={
                'Content-Type': 'application/json'
            },
            timeout=180
        )
        
        response.raise_for_status()
        
        response_data = None
        try:
            response_data = response.json()
            response_data_str = json.dumps(response_data, indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            response_data_str = f"Status Code: {response.status_code}\n\nRespuesta:\n{response.text}"
        
        return JsonResponse({
            'success': True,
            'message': 'Actividades enviadas exitosamente',
            'response_data': response_data_str,
        })
        
    except requests.exceptions.Timeout:
        return JsonResponse({
            'success': False,
            'error': 'La solicitud tardó demasiado tiempo. Por favor, intente nuevamente.'
        }, status=408)
    except requests.exceptions.RequestException as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al comunicarse con la API: {str(e)}'
        }, status=500)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON inválidos'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error inesperado: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def enviar_parametros_seleccionados_view(request):
    """
    Vista AJAX para enviar parámetros seleccionados a la API
    """
    try:
        data = json.loads(request.body)
        parametros_seleccionados = data.get('parametros', [])
        
        if not parametros_seleccionados:
            return JsonResponse({
                'success': False,
                'error': 'Debe seleccionar al menos un parámetro'
            }, status=400)
        
        # Obtener título, descripción y tipo de servicio del request (no de sesión)
        titulo = data.get('titulo', '').strip()
        descripcion = data.get('descripcion', '').strip()
        tipo_servicio = data.get('tipo_servicio', '').strip()
        
        if not titulo or not descripcion or not tipo_servicio:
            return JsonResponse({
                'success': False,
                'error': 'Título, descripción y tipo de servicio son requeridos'
            }, status=400)
        
        # Formatear parámetros para que solo contengan parametro y valor_recomendado
        parametros_formateados = []
        for param in parametros_seleccionados:
            parametros_formateados.append({
                'parametro': param.get('parametro', ''),
                'valor_recomendado': param.get('valor_recomendado', '')
            })
        
        # Preparar payload con título, descripción, tipo de servicio y parámetros
        payload = {
            'titulo': titulo,
            'descripcion': descripcion,
            'tipo_servicio': tipo_servicio,
            'parametros': parametros_formateados
        }
        
        # Enviar POST request a la API
        response = requests.post(
            N8N_WEBHOOK_TITULO_URL,
            json=payload,
            headers={
                'Content-Type': 'application/json'
            },
            timeout=180  # Timeout de 180 segundos (3 minutos) para esperar la respuesta
        )
        
        response.raise_for_status()
        
        response_data = None
        try:
            response_data = response.json()
            response_data_str = json.dumps(response_data, indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            response_data_str = f"Status Code: {response.status_code}\n\nRespuesta:\n{response.text}"
        
        # Extraer datos de la respuesta para el modal
        titulo_inicial = ''
        titulo_propuesto = ''
        resume_url = ''
        if isinstance(response_data, dict):
            titulo_inicial = response_data.get('titulo_inicial', '')
            titulo_propuesto = response_data.get('titulo_propuesto', '')
            resume_url = response_data.get('resume_url', '')
        
        return JsonResponse({
            'success': True,
            'message': 'Parámetros enviados exitosamente',
            'response_data': response_data_str,
            'titulo_inicial': titulo_inicial,
            'titulo_propuesto': titulo_propuesto,
            'resume_url': resume_url,
            'response_json': response_data if isinstance(response_data, dict) else None,
        })
        
    except requests.exceptions.Timeout:
        return JsonResponse({
            'success': False,
            'error': 'La solicitud tardó demasiado tiempo. Por favor, intente nuevamente.'
        }, status=408)
    except requests.exceptions.RequestException as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al comunicarse con la API: {str(e)}'
        }, status=500)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON inválidos'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error inesperado: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def enviar_actividades_view(request):
    """
    Vista AJAX para enviar actividades adicionales seleccionadas
    """
    try:
        data = json.loads(request.body)
        actividades_seleccionadas = data.get('actividades', [])
        
        if not actividades_seleccionadas:
            return JsonResponse({
                'success': False,
                'error': 'Debe seleccionar al menos una actividad'
            }, status=400)
        
        # Preparar payload con las actividades seleccionadas
        payload = {
            'actividades': actividades_seleccionadas
        }
        
        # Enviar POST request a la API
        # Nota: Puedes cambiar esta URL según necesites o obtenerla de la sesión
        response = requests.post(
            N8N_WEBHOOK_TITULO_URL,  # Cambiar por la URL correcta
            json=payload,
            headers={
                'Content-Type': 'application/json'
            },
            timeout=180
        )
        
        response.raise_for_status()
        
        response_data = None
        try:
            response_data = response.json()
            response_data_str = json.dumps(response_data, indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            response_data_str = f"Status Code: {response.status_code}\n\nRespuesta:\n{response.text}"
        
        return JsonResponse({
            'success': True,
            'message': 'Actividades enviadas exitosamente',
            'response_data': response_data_str,
        })
        
    except requests.exceptions.Timeout:
        return JsonResponse({
            'success': False,
            'error': 'La solicitud tardó demasiado tiempo. Por favor, intente nuevamente.'
        }, status=408)
    except requests.exceptions.RequestException as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al comunicarse con la API: {str(e)}'
        }, status=500)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON inválidos'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error inesperado: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def enviar_titulo_ajustado_view(request):
    """
    Vista AJAX para enviar el título ajustado (aceptado o rechazado)
    """
    try:
        data = json.loads(request.body)
        titulo_final = data.get('titulo_final', '').strip()
        aceptar = data.get('aceptar', False)
        resume_url = data.get('resume_url', '').strip()
        
        if not titulo_final:
            return JsonResponse({
                'success': False,
                'error': 'El título final es requerido'
            }, status=400)
        
        if not resume_url:
            return JsonResponse({
                'success': False,
                'error': 'La URL de resume es requerida'
            }, status=400)
        
        # Preparar payload con el título final
        payload = {
            'titulo_final': titulo_final,
            'aceptar': aceptar
        }
        
        # Enviar POST request a la resume_url proporcionada
        response = requests.post(
            resume_url,
            json=payload,
            headers={
                'Content-Type': 'application/json'
            },
            timeout=180
        )
        
        response.raise_for_status()
        
        response_data = None
        try:
            response_data = response.json()
            response_data_str = json.dumps(response_data, indent=2, ensure_ascii=False)
            
            # No guardar en sesión
        except json.JSONDecodeError:
            response_data_str = f"Status Code: {response.status_code}\n\nRespuesta:\n{response.text}"
        
        return JsonResponse({
            'success': True,
            'message': 'Título enviado exitosamente',
            'response_data': response_data_str,
            'has_actividades': bool(response_data.get('actividades_adicionales')) if isinstance(response_data, dict) else False,
        })
        
    except requests.exceptions.Timeout:
        return JsonResponse({
            'success': False,
            'error': 'La solicitud tardó demasiado tiempo. Por favor, intente nuevamente.'
        }, status=408)
    except requests.exceptions.RequestException as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al comunicarse con la API: {str(e)}'
        }, status=500)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON inválidos'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error inesperado: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def enviar_actividades_view(request):
    """
    Vista AJAX para enviar actividades adicionales seleccionadas
    """
    try:
        data = json.loads(request.body)
        actividades_seleccionadas = data.get('actividades', [])
        
        if not actividades_seleccionadas:
            return JsonResponse({
                'success': False,
                'error': 'Debe seleccionar al menos una actividad'
            }, status=400)
        
        # Preparar payload con las actividades seleccionadas
        payload = {
            'actividades': actividades_seleccionadas
        }
        
        # Enviar POST request a la API
        # Nota: Puedes cambiar esta URL según necesites o obtenerla de la sesión
        response = requests.post(
            N8N_WEBHOOK_TITULO_URL,  # Cambiar por la URL correcta
            json=payload,
            headers={
                'Content-Type': 'application/json'
            },
            timeout=180
        )
        
        response.raise_for_status()
        
        response_data = None
        try:
            response_data = response.json()
            response_data_str = json.dumps(response_data, indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            response_data_str = f"Status Code: {response.status_code}\n\nRespuesta:\n{response.text}"
        
        return JsonResponse({
            'success': True,
            'message': 'Actividades enviadas exitosamente',
            'response_data': response_data_str,
        })
        
    except requests.exceptions.Timeout:
        return JsonResponse({
            'success': False,
            'error': 'La solicitud tardó demasiado tiempo. Por favor, intente nuevamente.'
        }, status=408)
    except requests.exceptions.RequestException as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al comunicarse con la API: {str(e)}'
        }, status=500)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON inválidos'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error inesperado: {str(e)}'
        }, status=500)
