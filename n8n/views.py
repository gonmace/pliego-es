import requests
import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .forms import EspecificacionTecnicaForm
from .models import EspecificacionTecnica, Parametros

N8N_WEBHOOK_URL = 'https://jaimemc.app.n8n.cloud/webhook/parametros'
N8N_WEBHOOK_TITULO_URL = 'https://jaimemc.app.n8n.cloud/webhook/titulo'
N8N_WEBHOOK_ADICIONALES_URL = 'https://jaimemc.app.n8n.cloud/webhook-test/adicionales'


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
    Guarda primero en el modelo EspecificacionTecnica antes de enviar a la API
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
        
        # Guardar en el modelo EspecificacionTecnica antes de enviar a la API
        especificacion = EspecificacionTecnica.objects.create(
            titulo=titulo,
            descripcion=descripcion,
            tipo_servicio=tipo_servicio,
            sessionID=session_id,
            creado_por=request.user
        )
        
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
        except json.JSONDecodeError:
            # Si no es JSON, usar el texto de la respuesta
            response_data = {'text': response.text, 'status_code': response.status_code}
        
        # Devolver la respuesta de la API directamente (como objeto JSON)
        # para que el JavaScript pueda procesarla fácilmente
        return JsonResponse({
            'success': True,
            'message': 'Datos guardados en modelo y enviados exitosamente a la API.',
            'response_data': response_data,  # Devolver como objeto, no como string
            'especificacion_id': especificacion.id,  # ID del registro guardado
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
        
        # Obtener sessionID del usuario activo
        session_id = request.session.session_key or ''
        
        # Buscar la EspecificacionTecnica más reciente con el mismo sessionID y título
        especificacion_tecnica = EspecificacionTecnica.objects.filter(
            sessionID=session_id,
            titulo=titulo,
            descripcion=descripcion,
            tipo_servicio=tipo_servicio
        ).order_by('-fecha_creacion').first()
        
        if not especificacion_tecnica:
            return JsonResponse({
                'success': False,
                'error': 'No se encontró la especificación técnica relacionada'
            }, status=400)
        
        # Guardar los parámetros seleccionados en el modelo Parametros
        # Solo los que tienen check=true (todos los que vienen en parametros_seleccionados)
        parametros_guardados = []
        for param in parametros_seleccionados:
            parametro_obj = Parametros.objects.create(
                especificacion_tecnica=especificacion_tecnica,
                parametro=param.get('parametro', ''),
                valor=param.get('valor_recomendado', ''),
                unidad=param.get('unidad_medida', ''),
                detalle=param.get('detalle', ''),
                sessionID=session_id
            )
            parametros_guardados.append(parametro_obj.id)
        
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
            'message': 'Parámetros guardados y enviados exitosamente',
            'response_data': response_data_str,
            'titulo_inicial': titulo_inicial,
            'titulo_propuesto': titulo_propuesto,
            'resume_url': resume_url,
            'response_json': response_data if isinstance(response_data, dict) else None,
            'parametros_guardados': len(parametros_guardados),
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
    Si se acepta la sugerencia, actualiza el título en EspecificacionTecnica
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
        
        # Obtener sessionID del usuario activo
        session_id = request.session.session_key or ''
        
        # Si se acepta la sugerencia, actualizar el título en EspecificacionTecnica
        if aceptar and session_id:
            # Buscar la EspecificacionTecnica más reciente con el mismo sessionID
            especificacion_tecnica = EspecificacionTecnica.objects.filter(
                sessionID=session_id
            ).order_by('-fecha_creacion').first()
            
            if especificacion_tecnica:
                # Actualizar el título usando PATCH (actualización parcial)
                especificacion_tecnica.titulo = titulo_final
                especificacion_tecnica.save(update_fields=['titulo'])
        
        # Preparar payload para adicionales
        adicionales_payload = {
            'titulo_final': titulo_final,
            'aceptar': aceptar,
            'sessionID': session_id
        }
        
        # Enviar POST directamente a la URL de adicionales
        adicionales_response = requests.post(
            N8N_WEBHOOK_ADICIONALES_URL,
            json=adicionales_payload,
            headers={
                'Content-Type': 'application/json'
            },
            timeout=180
        )
        
        adicionales_response.raise_for_status()
        
        # Procesar respuesta de adicionales
        adicionales_response_data = None
        try:
            adicionales_response_data = adicionales_response.json()
            adicionales_response_str = json.dumps(adicionales_response_data, indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            adicionales_response_str = f"Status Code: {adicionales_response.status_code}\n\nRespuesta:\n{adicionales_response.text}"
            adicionales_response_data = {'text': adicionales_response.text, 'status_code': adicionales_response.status_code}
        
        # Opcionalmente, enviar a resume_url si existe y es válida (pero no es crítico)
        resume_response_data = None
        if resume_url and resume_url.strip():
            try:
                resume_payload = {
                    'titulo_final': titulo_final,
                    'aceptar': aceptar
                }
                
                resume_response = requests.post(
                    resume_url,
                    json=resume_payload,
                    headers={
                        'Content-Type': 'application/json'
                    },
                    timeout=180
                )
                
                resume_response.raise_for_status()
                
                try:
                    resume_response_data = resume_response.json()
                except json.JSONDecodeError:
                    resume_response_data = {'text': resume_response.text, 'status_code': resume_response.status_code}
                    
            except requests.exceptions.RequestException as e:
                # Si falla el POST a resume_url, solo registrar el error pero no fallar
                print(f"Error al enviar a resume_url: {str(e)}")
                resume_response_data = {'error': str(e)}
        
        return JsonResponse({
            'success': True,
            'message': 'Título enviado exitosamente',
            'response_data': adicionales_response_str,
            'has_actividades': bool(adicionales_response_data.get('actividades_adicionales')) if isinstance(adicionales_response_data, dict) else False,
            'adicionales_response': adicionales_response_data,
            'resume_response': resume_response_data,
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
