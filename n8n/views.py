import requests
import json
import markdown
import logging
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .forms import EspecificacionTecnicaForm
from .models import EspecificacionTecnica, Parametros, ActividadesAdicionales

logger = logging.getLogger(__name__)

N8N_WEBHOOK_URL = 'https://jaimemc.app.n8n.cloud/webhook/parametros'
N8N_WEBHOOK_TITULO_URL = 'https://jaimemc.app.n8n.cloud/webhook/titulo'
N8N_WEBHOOK_ADICIONALES_URL = 'https://jaimemc.app.n8n.cloud/webhook/adicionales'
N8N_WEBHOOK_FINAL_URL = 'https://jaimemc.app.n8n.cloud/webhook/final'


@login_required
def n8n_pasos_view(request):
    """
    Vista principal con sistema de pasos
    """
    try:
        pasos = [
            {"numero": 1, "nombre": "Parámetros"},
            {"numero": 2, "nombre": "Título"},
            {"numero": 3, "nombre": "Adicionales"},
            {"numero": 4, "nombre": "Actividades"},
            {"numero": 5, "nombre": "Resultado"},
        ]
        paso_actual = int(request.GET.get('paso', 1))
        
        # Guardar proyecto_id en la sesión si viene como parámetro GET
        proyecto_id = request.GET.get('proyecto_id')
        if proyecto_id:
            try:
                proyecto_id = int(proyecto_id)
                # Verificar que el proyecto existe y el usuario tiene acceso
                from esp_web.models import Proyecto
                proyecto = Proyecto.objects.get(id=proyecto_id, activo=True)
                # Verificar que el usuario es el propietario o el proyecto es público
                if proyecto.creado_por == request.user or proyecto.publico:
                    request.session['n8n_proyecto_id'] = proyecto_id
            except (ValueError, Proyecto.DoesNotExist) as e:
                # Si el proyecto no existe o no es válido, ignorar silenciosamente
                logger.warning(f"Proyecto no válido o no encontrado: {str(e)}")
            except Exception as e:
                logger.error(f"Error al procesar proyecto_id en n8n_pasos_view: {str(e)}", exc_info=True)
    
        # Limpiar toda la sesión relacionada con n8n al inicio (solo si no es paso 5)
        if paso_actual != 5:
            request.session.pop('n8n_paso1_data', None)
            request.session.pop('n8n_respuesta_api', None)
            request.session.pop('n8n_respuesta_completa', None)
            request.session.pop('n8n_actividades_adicionales', None)
        
        # Inicializar variables vacías (no usar sesión)
        datos_paso1 = {}
        respuesta_api = {}
        respuesta_completa = {}
        actividades_adicionales = {}
        
        # Determinar qué template usar según el paso
        if paso_actual == 1:
            template_name = 'n8n/paso1_datos_iniciales.html'
        elif paso_actual == 5:
            template_name = 'n8n/paso5_resultado.html'
        else:
            template_name = 'n8n/pasos.html'
        
        return render(request, template_name, {
            'pasos': pasos,
            'paso_actual': paso_actual,
            'datos_paso1': datos_paso1,
            'respuesta_api': respuesta_api,
            'respuesta_completa': respuesta_completa,
            'actividades_adicionales': actividades_adicionales,
            'form': EspecificacionTecnicaForm(),
        })
    except Exception as e:
        logger.error(f"Error inesperado en n8n_pasos_view: {str(e)}", exc_info=True)
        from django.http import HttpResponseServerError
        return HttpResponseServerError('Error interno del servidor. Por favor, contacte al administrador.')


# Vista eliminada: parametros_paso2_view ya no se necesita porque el paso 2 es un modal


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
        
    except json.JSONDecodeError as e:
        logger.error(f"JSONDecodeError en guardar_paso1_view: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON inválidos'
        }, status=400)
    except Exception as e:
        logger.error(f"Error inesperado en guardar_paso1_view: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor. Por favor, contacte al administrador o intente nuevamente más tarde.'
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
        
        # Guardar en el modelo EspecificacionTecnica antes de enviar a la API
        try:
            especificacion = EspecificacionTecnica.objects.create(
                titulo=titulo,
                descripcion=descripcion,
                tipo_servicio=tipo_servicio,
                creado_por=request.user
            )
            logger.info(f"EspecificacionTecnica guardada con ID: {especificacion.id}")
        except Exception as e:
            logger.error(f"Error al guardar EspecificacionTecnica: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': 'Error al guardar la especificación técnica. Por favor, intente nuevamente.'
            }, status=500)
        
        # Preparar los datos para enviar a la API
        payload = {
            'titulo': titulo,
            'descripcion': descripcion,
            'tipo_servicio': tipo_servicio
        }
        
        # Enviar POST request a la API webhook y esperar respuesta
        # Usar timeout de 60 segundos para evitar que Gunicorn mate al worker
        try:
            response = requests.post(
                N8N_WEBHOOK_URL,
                json=payload,
                headers={
                    'Content-Type': 'application/json'
                },
                timeout=60  # Timeout de 60 segundos para evitar timeout de Gunicorn
            )
            
            # Verificar si la respuesta fue exitosa
            response.raise_for_status()
            
            # Intentar parsear la respuesta JSON
            response_data = None
            try:
                response_data = response.json()
            except json.JSONDecodeError as e:
                logger.warning(f"Respuesta no es JSON válido: {str(e)}")
                # Si no es JSON, usar el texto de la respuesta
                response_data = {'text': response.text, 'status_code': response.status_code}
        except requests.exceptions.Timeout:
            logger.error(f"Timeout al enviar a {N8N_WEBHOOK_URL}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al comunicarse con la API {N8N_WEBHOOK_URL}: {str(e)}", exc_info=True)
            raise
        
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
        logger.error("Timeout en enviar_especificacion_view")
        return JsonResponse({
            'success': False,
            'error': 'La solicitud tardó demasiado tiempo. Por favor, intente nuevamente.'
        }, status=408)
    except requests.exceptions.RequestException as e:
        logger.error(f"RequestException en enviar_especificacion_view: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Error al comunicarse con la API. Por favor, intente nuevamente más tarde.'
        }, status=500)
    except json.JSONDecodeError as e:
        logger.error(f"JSONDecodeError en enviar_especificacion_view: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON inválidos'
        }, status=400)
    except Exception as e:
        logger.error(f"Error inesperado en enviar_especificacion_view: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor. Por favor, contacte al administrador o intente nuevamente más tarde.'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def enviar_actividades_view(request):
    """
    Vista AJAX para guardar actividades adicionales seleccionadas en el modelo y luego enviar a la API
    """
    try:
        data = json.loads(request.body)
        actividades_seleccionadas = data.get('actividades', [])
        
        if not actividades_seleccionadas:
            return JsonResponse({
                'success': False,
                'error': 'Debe seleccionar al menos una actividad'
            }, status=400)
        
        # Obtener el ID de la especificación técnica
        especificacion_id = data.get('especificacion_id')
        
        if not especificacion_id:
            return JsonResponse({
                'success': False,
                'error': 'El ID de la especificación técnica es requerido'
            }, status=400)
        
        # Buscar la EspecificacionTecnica por ID
        try:
            especificacion_tecnica = EspecificacionTecnica.objects.get(id=especificacion_id)
        except EspecificacionTecnica.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'No se encontró la especificación técnica base para vincular las actividades. Asegúrese de haber completado los pasos anteriores.'
            }, status=404)
        
        actividades_guardadas = []
        # Guardar las actividades seleccionadas en el modelo ActividadesAdicionales
        for actividad in actividades_seleccionadas:
            try:
                actividad_obj = ActividadesAdicionales.objects.create(
                    especificacion_tecnica=especificacion_tecnica,
                    nombre=actividad.get('nombre', ''),
                    unidad_medida=actividad.get('unidad_medida', ''),
                    descripcion=actividad.get('descripcion', '')
                )
                actividades_guardadas.append(actividad_obj)
            except Exception as e:
                logger.error(f"Error al guardar actividad: {str(e)}", exc_info=True)
                # Continuar con las siguientes actividades aunque una falle
                continue
        
        logger.info(f"Actividades guardadas exitosamente: {len(actividades_guardadas)} actividades")
        
        # Refrescar la especificación técnica desde la BD para asegurar datos actualizados
        especificacion_tecnica.refresh_from_db()
        
        # Obtener TODOS los parámetros técnicos guardados relacionados con esta especificación técnica desde la BD
        parametros_tecnicos = especificacion_tecnica.parametros.all()
        parametros_formateados = []
        for param in parametros_tecnicos:
            parametros_formateados.append({
                'parametro': param.parametro,
                'valor_recomendado': param.valor or '',
                'unidad_medida': param.unidad or '',
                'detalle': param.detalle or ''
            })
        
        logger.info(f"Parámetros técnicos obtenidos de BD: {len(parametros_formateados)} parámetros")
        
        # Obtener TODAS las actividades adicionales guardadas relacionadas con esta especificación técnica desde la BD
        actividades_adicionales_bd = especificacion_tecnica.actividades_adicionales.all()
        actividades_formateadas = []
        for actividad_obj in actividades_adicionales_bd:
            actividades_formateadas.append({
                'nombre': actividad_obj.nombre,
                'unidad_medida': actividad_obj.unidad_medida or '',
                'descripcion': actividad_obj.descripcion or ''
            })
        
        logger.info(f"Actividades adicionales obtenidas de BD: {len(actividades_formateadas)} actividades")
        
        # Preparar payload final con todos los datos extraídos de la BD usando el ID de la especificación técnica
        payload_final = {
            'titulo': especificacion_tecnica.titulo,
            'descripcion': especificacion_tecnica.descripcion,
            'servicio': especificacion_tecnica.tipo_servicio,
            'parametros_tecnicos': parametros_formateados,
            'actividades_adicionales': actividades_formateadas
        }
        
        logger.info(f"Enviando POST a URL final: {N8N_WEBHOOK_FINAL_URL}")
        logger.debug(f"Payload final: {json.dumps(payload_final, indent=2, ensure_ascii=False)}")
        
        # Enviar POST request a la API final DESPUÉS de guardar todo en la BD
        final_response = None
        final_response_data = None
        final_response_str = None
        markdown_html_para_respuesta = None
        raw_markdown_para_respuesta = None
        
        try:
            final_response = requests.post(
                N8N_WEBHOOK_FINAL_URL,
                json=payload_final,
                headers={
                    'Content-Type': 'application/json'
                },
                timeout=60
            )
            
            logger.info(f"Respuesta de URL final - Status Code: {final_response.status_code}")
            
            final_response.raise_for_status()
            
            try:
                final_response_data = final_response.json()
                final_response_str = json.dumps(final_response_data, indent=2, ensure_ascii=False)
                logger.debug(f"Respuesta JSON de URL final: {final_response_str}")
                
                # Extraer el markdown del output o actividades_adicionales si existe
                markdown_resultado = None
                if isinstance(final_response_data, list) and len(final_response_data) > 0:
                    first_item = final_response_data[0]
                    if isinstance(first_item, dict):
                        # Buscar en 'output' primero
                        if 'output' in first_item:
                            markdown_resultado = first_item['output']
                            logger.info(f"Markdown encontrado en formato array[0].output: {len(markdown_resultado) if markdown_resultado else 0} caracteres")
                        # Si no hay output, buscar en 'actividades_adicionales'
                        elif 'actividades_adicionales' in first_item:
                            markdown_resultado = first_item['actividades_adicionales']
                            logger.info(f"Markdown encontrado en formato array[0].actividades_adicionales: {len(markdown_resultado) if markdown_resultado else 0} caracteres")
                elif isinstance(final_response_data, dict):
                    # Buscar en 'output' primero
                    if 'output' in final_response_data:
                        markdown_resultado = final_response_data['output']
                        logger.info(f"Markdown encontrado en formato dict.output: {len(markdown_resultado) if markdown_resultado else 0} caracteres")
                    # Si no hay output, buscar en 'actividades_adicionales'
                    elif 'actividades_adicionales' in final_response_data:
                        markdown_resultado = final_response_data['actividades_adicionales']
                        logger.info(f"Markdown encontrado en formato dict.actividades_adicionales: {len(markdown_resultado) if markdown_resultado else 0} caracteres")
                
                # Guardar el markdown en el modelo si existe
                if markdown_resultado:
                    especificacion_tecnica.resultado_markdown = markdown_resultado
                    especificacion_tecnica.save(update_fields=['resultado_markdown'])
                    logger.info(f"Markdown guardado en el modelo: {len(markdown_resultado)} caracteres")
                    
                    # Convertir markdown a HTML para la respuesta
                    extensions = [
                        'markdown.extensions.extra',
                        'markdown.extensions.codehilite',
                        'markdown.extensions.tables',
                        'markdown.extensions.nl2br',
                        'markdown.extensions.sane_lists'
                    ]
                    markdown_html = markdown.markdown(
                        markdown_resultado, output_format='html', extensions=extensions
                    )
                    
                    # Guardar markdown_html y raw_markdown en variables para agregarlos a response_dict
                    # También agregarlos a final_response_data para referencia
                    if isinstance(final_response_data, list) and len(final_response_data) > 0:
                        if isinstance(final_response_data[0], dict):
                            final_response_data[0]['markdown_html'] = markdown_html
                            final_response_data[0]['raw_markdown'] = markdown_resultado
                    elif isinstance(final_response_data, dict):
                        final_response_data['markdown_html'] = markdown_html
                        final_response_data['raw_markdown'] = markdown_resultado
                    
                    logger.info(f"Markdown HTML generado: {len(markdown_html)} caracteres")
                    # Guardar en variables para usar después
                    markdown_html_para_respuesta = markdown_html
                    raw_markdown_para_respuesta = markdown_resultado
                else:
                    logger.warning("No se encontró markdown en la respuesta")
            except json.JSONDecodeError as e:
                final_response_str = f"Status Code: {final_response.status_code}\n\nRespuesta:\n{final_response.text}"
                logger.warning(f"Respuesta no JSON de URL final: {str(e)}")
        except requests.exceptions.Timeout as e:
            # Si hay timeout, registrar el error
            error_msg = f"Timeout al enviar a la URL final: {str(e)}"
            logger.error(error_msg, exc_info=True)
            final_response_str = error_msg
            final_response_data = {'error': error_msg, 'type': 'timeout'}
        except requests.exceptions.RequestException as e:
            # Si falla el POST a la URL final, registrar el error pero no fallar completamente
            error_msg = f"Error al enviar a la URL final ({N8N_WEBHOOK_FINAL_URL}): {str(e)}"
            logger.error(error_msg, exc_info=True)
            final_response_str = error_msg
            final_response_data = {'error': str(e), 'type': 'request_exception', 'url': N8N_WEBHOOK_FINAL_URL}
        except Exception as e:
            # Capturar cualquier otro error inesperado
            error_msg = f"Error inesperado al enviar a la URL final: {str(e)}"
            logger.error(error_msg, exc_info=True)
            final_response_str = error_msg
            final_response_data = {'error': str(e), 'type': 'unexpected'}
        
        # Preparar respuesta con el markdown si existe
        response_dict = {
            'success': True,
            'message': 'Actividades guardadas y enviadas exitosamente',
            'response_data': final_response_str,
            'actividades_guardadas': len(actividades_guardadas),
            'parametros_enviados': len(parametros_formateados),
            'final_response': final_response_data if final_response_data else None,
        }
        
        # Agregar markdown HTML y raw directamente en la respuesta si existe
        # Usar las variables guardadas anteriormente si existen
        if markdown_html_para_respuesta:
            response_dict['markdown_html'] = markdown_html_para_respuesta
            response_dict['raw_markdown'] = raw_markdown_para_respuesta
            logger.debug(f"Agregando markdown a response_dict (desde variables): HTML={len(markdown_html_para_respuesta)} chars, Raw={len(raw_markdown_para_respuesta) if raw_markdown_para_respuesta else 0} chars")
        else:
            # Buscar markdown_html y raw_markdown en final_response_data como fallback
            markdown_html_to_add = None
            raw_markdown_to_add = None
            
            if final_response_data:
                if isinstance(final_response_data, list) and len(final_response_data) > 0:
                    first_item = final_response_data[0]
                    if isinstance(first_item, dict):
                        markdown_html_to_add = first_item.get('markdown_html')
                        raw_markdown_to_add = first_item.get('raw_markdown')
                        # También verificar si hay output directamente (el markdown raw)
                        if not raw_markdown_to_add and first_item.get('output'):
                            raw_markdown_to_add = first_item.get('output')
                        # También verificar si hay actividades_adicionales directamente (el markdown raw)
                        if not raw_markdown_to_add and first_item.get('actividades_adicionales'):
                            raw_markdown_to_add = first_item.get('actividades_adicionales')
                elif isinstance(final_response_data, dict):
                    markdown_html_to_add = final_response_data.get('markdown_html')
                    raw_markdown_to_add = final_response_data.get('raw_markdown')
                    # También verificar si hay output directamente
                    if not raw_markdown_to_add and final_response_data.get('output'):
                        raw_markdown_to_add = final_response_data.get('output')
                    # También verificar si hay actividades_adicionales directamente (el markdown raw)
                    if not raw_markdown_to_add and final_response_data.get('actividades_adicionales'):
                        raw_markdown_to_add = final_response_data.get('actividades_adicionales')
            
            # Agregar markdown a la respuesta principal si existe
            if markdown_html_to_add or raw_markdown_to_add:
                if markdown_html_to_add:
                    response_dict['markdown_html'] = markdown_html_to_add
                if raw_markdown_to_add:
                    response_dict['raw_markdown'] = raw_markdown_to_add
                logger.debug(f"Agregando markdown a response_dict (fallback): HTML={len(markdown_html_to_add) if markdown_html_to_add else 0} chars, Raw={len(raw_markdown_to_add) if raw_markdown_to_add else 0} chars")
        
        return JsonResponse(response_dict)
        
    except requests.exceptions.Timeout:
        return JsonResponse({
            'success': False,
            'error': 'La solicitud tardó demasiado tiempo. Por favor, intente nuevamente.'
        }, status=408)
    except requests.exceptions.RequestException as e:
        logger.error(f"RequestException en enviar_actividades_view: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Error al comunicarse con la API. Por favor, intente nuevamente más tarde.'
        }, status=500)
    except json.JSONDecodeError as e:
        logger.error(f"JSONDecodeError en enviar_actividades_view: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON inválidos'
        }, status=400)
    except Exception as e:
        logger.error(f"Error inesperado en enviar_actividades_view: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor. Por favor, contacte al administrador o intente nuevamente más tarde.'
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
        
        # Los parámetros son opcionales, se puede continuar sin seleccionar ninguno
        
        # Obtener el ID de la especificación técnica
        especificacion_id = data.get('especificacion_id')
        
        if not especificacion_id:
            return JsonResponse({
                'success': False,
                'error': 'El ID de la especificación técnica es requerido'
            }, status=400)
        
        # Buscar la EspecificacionTecnica por ID
        try:
            especificacion_tecnica = EspecificacionTecnica.objects.get(id=especificacion_id)
        except EspecificacionTecnica.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'No se encontró la especificación técnica relacionada'
            }, status=404)
        
        # Guardar los parámetros seleccionados en el modelo Parametros
        # Solo los que tienen check=true (todos los que vienen en parametros_seleccionados)
        parametros_guardados = []
        for param in parametros_seleccionados:
            try:
                parametro_obj = Parametros.objects.create(
                    especificacion_tecnica=especificacion_tecnica,
                    parametro=param.get('parametro', ''),
                    valor=param.get('valor_recomendado', ''),
                    unidad=param.get('unidad_medida', ''),
                    detalle=param.get('detalle', '')
                )
                parametros_guardados.append(parametro_obj.id)
            except Exception as e:
                logger.error(f"Error al guardar parámetro: {str(e)}", exc_info=True)
                # Continuar con los siguientes parámetros aunque uno falle
                continue
        
        # Formatear parámetros para incluir parametro, valor y unidad
        parametros_formateados = []
        for param in parametros_seleccionados:
            parametros_formateados.append({
                'parametro': param.get('parametro', ''),
                'valor': param.get('valor_recomendado', ''),
                'unidad': param.get('unidad_medida', '')
            })
        
        # Preparar payload con título, descripción, tipo de servicio y parámetros
        payload = {
            'titulo': especificacion_tecnica.titulo,
            'descripcion': especificacion_tecnica.descripcion,
            'tipo_servicio': especificacion_tecnica.tipo_servicio,
            'parametros': parametros_formateados
        }
        
        # Enviar POST request a la API
        try:
            response = requests.post(
                N8N_WEBHOOK_TITULO_URL,
                json=payload,
                headers={
                    'Content-Type': 'application/json'
                },
                timeout=60  # Timeout de 60 segundos para evitar timeout de Gunicorn
            )
            
            response.raise_for_status()
            
            response_data = None
            try:
                response_data = response.json()
                response_data_str = json.dumps(response_data, indent=2, ensure_ascii=False)
            except json.JSONDecodeError as e:
                logger.warning(f"Respuesta no es JSON válido en enviar_parametros_seleccionados_view: {str(e)}")
                response_data_str = f"Status Code: {response.status_code}\n\nRespuesta:\n{response.text}"
        except requests.exceptions.Timeout:
            logger.error(f"Timeout al enviar a {N8N_WEBHOOK_TITULO_URL}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al comunicarse con la API {N8N_WEBHOOK_TITULO_URL}: {str(e)}", exc_info=True)
            raise
        
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
        logger.error("Timeout en enviar_parametros_seleccionados_view")
        return JsonResponse({
            'success': False,
            'error': 'La solicitud tardó demasiado tiempo. Por favor, intente nuevamente.'
        }, status=408)
    except requests.exceptions.RequestException as e:
        logger.error(f"RequestException en enviar_parametros_seleccionados_view: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Error al comunicarse con la API. Por favor, intente nuevamente más tarde.'
        }, status=500)
    except json.JSONDecodeError as e:
        logger.error(f"JSONDecodeError en enviar_parametros_seleccionados_view: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON inválidos'
        }, status=400)
    except Exception as e:
        logger.error(f"Error inesperado en enviar_parametros_seleccionados_view: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor. Por favor, contacte al administrador o intente nuevamente más tarde.'
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
        
        # Obtener el ID de la especificación técnica
        especificacion_id = data.get('especificacion_id')
        
        if not especificacion_id:
            return JsonResponse({
                'success': False,
                'error': 'El ID de la especificación técnica es requerido'
            }, status=400)
        
        # Buscar la EspecificacionTecnica por ID
        try:
            especificacion_tecnica = EspecificacionTecnica.objects.get(id=especificacion_id)
        except EspecificacionTecnica.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'No se encontró la especificación técnica relacionada.'
            }, status=404)
        
        # Si se acepta la sugerencia, actualizar el título en EspecificacionTecnica
        if aceptar:
            # Actualizar el título usando PATCH (actualización parcial)
            especificacion_tecnica.titulo = titulo_final
            especificacion_tecnica.save(update_fields=['titulo'])
            # Refrescar desde la BD para obtener el título actualizado
            especificacion_tecnica.refresh_from_db()
        
        # Obtener los parámetros técnicos guardados relacionados con esta especificación técnica desde la BD
        parametros_tecnicos = especificacion_tecnica.parametros.all()
        parametros_formateados = []
        for param in parametros_tecnicos:
            parametros_formateados.append({
                'parametro': param.parametro,
                'valor_recomendado': param.valor or '',
                'unidad_medida': param.unidad or '',
                'detalle': param.detalle or ''
            })
        
        # Preparar payload para adicionales con información de la BD
        adicionales_payload = {
            'titulo_final': titulo_final,
            'aceptar': aceptar,
            'titulo': especificacion_tecnica.titulo,
            'descripcion': especificacion_tecnica.descripcion,
            'servicio': especificacion_tecnica.tipo_servicio,
            'parametros_tecnicos': parametros_formateados
        }
        
        # Enviar POST directamente a la URL de adicionales
        try:
            adicionales_response = requests.post(
                N8N_WEBHOOK_ADICIONALES_URL,
                json=adicionales_payload,
                headers={
                    'Content-Type': 'application/json'
                },
                timeout=60
            )
            
            adicionales_response.raise_for_status()
            
            # Procesar respuesta de adicionales
            adicionales_response_data = None
            try:
                adicionales_response_data = adicionales_response.json()
                adicionales_response_str = json.dumps(adicionales_response_data, indent=2, ensure_ascii=False)
            except json.JSONDecodeError as e:
                logger.warning(f"Respuesta no es JSON válido en enviar_titulo_ajustado_view: {str(e)}")
                adicionales_response_str = f"Status Code: {adicionales_response.status_code}\n\nRespuesta:\n{adicionales_response.text}"
                adicionales_response_data = {'text': adicionales_response.text, 'status_code': adicionales_response.status_code}
        except requests.exceptions.Timeout:
            logger.error(f"Timeout al enviar a {N8N_WEBHOOK_ADICIONALES_URL}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al comunicarse con la API {N8N_WEBHOOK_ADICIONALES_URL}: {str(e)}", exc_info=True)
            raise
        
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
                    timeout=60
                )
                
                resume_response.raise_for_status()
                
                try:
                    resume_response_data = resume_response.json()
                except json.JSONDecodeError as e:
                    logger.warning(f"Respuesta de resume_url no es JSON válido: {str(e)}")
                    resume_response_data = {'text': resume_response.text, 'status_code': resume_response.status_code}
                    
            except requests.exceptions.RequestException as e:
                # Si falla el POST a resume_url, solo registrar el error pero no fallar
                logger.warning(f"Error al enviar a resume_url: {str(e)}", exc_info=True)
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
        logger.error("Timeout en enviar_titulo_ajustado_view")
        return JsonResponse({
            'success': False,
            'error': 'La solicitud tardó demasiado tiempo. Por favor, intente nuevamente.'
        }, status=408)
    except requests.exceptions.RequestException as e:
        logger.error(f"RequestException en enviar_titulo_ajustado_view: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Error al comunicarse con la API. Por favor, intente nuevamente más tarde.'
        }, status=500)
    except json.JSONDecodeError as e:
        logger.error(f"JSONDecodeError en enviar_titulo_ajustado_view: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON inválidos'
        }, status=400)
    except Exception as e:
        logger.error(f"Error inesperado en enviar_titulo_ajustado_view: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor. Por favor, contacte al administrador o intente nuevamente más tarde.'
        }, status=500)


# Función duplicada eliminada - usar la función en línea 267 que guarda en el modelo


@login_required
def paso5_resultado_view(request):
    """
    Vista AJAX para obtener el resultado del paso 5 (markdown renderizado)
    """
    try:
        # Obtener el ID de la especificación técnica desde los parámetros GET o POST
        especificacion_id = request.GET.get('especificacion_id') or request.POST.get('especificacion_id')
        
        # Si no viene en GET/POST, intentar obtenerlo del body JSON (para requests AJAX)
        if not especificacion_id and request.body:
            try:
                data = json.loads(request.body)
                especificacion_id = data.get('especificacion_id')
            except (json.JSONDecodeError, AttributeError):
                pass
        
        if not especificacion_id:
            return JsonResponse({
                'success': False,
                'error': 'El ID de la especificación técnica es requerido'
            }, status=400)
        
        # Buscar la EspecificacionTecnica por ID que tenga resultado_markdown
        try:
            especificacion_tecnica = EspecificacionTecnica.objects.get(
                id=especificacion_id,
                resultado_markdown__isnull=False
            )
            if not especificacion_tecnica.resultado_markdown:
                raise EspecificacionTecnica.DoesNotExist
        except EspecificacionTecnica.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'No se encontró el resultado de la especificación técnica. Asegúrese de haber completado todos los pasos anteriores.'
            }, status=404)
        
        # Convertir markdown a HTML
        extensions = [
            'markdown.extensions.extra',
            'markdown.extensions.codehilite',
            'markdown.extensions.tables',
            'markdown.extensions.nl2br',
            'markdown.extensions.sane_lists'
        ]
        markdown_html = markdown.markdown(
            especificacion_tecnica.resultado_markdown,
            output_format='html',
            extensions=extensions
        )
        
        return JsonResponse({
            'success': True,
            'markdown_html': markdown_html,
            'raw_markdown': especificacion_tecnica.resultado_markdown,
            'titulo': especificacion_tecnica.titulo,
        })
        
    except Exception as e:
        logger.error(f"Error inesperado en paso5_resultado_view: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor. Por favor, contacte al administrador o intente nuevamente más tarde.'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def guardar_resultado_view(request):
    """
    Vista AJAX para guardar el resultado final de la especificación técnica
    Si hay un proyecto_id en la sesión, convierte EspecificacionTecnica en Especificacion
    """
    try:
        data = json.loads(request.body)
        contenido = data.get('contenido', '').strip()
        
        if not contenido:
            return JsonResponse({
                'success': False,
                'error': 'El contenido es requerido'
            }, status=400)
        
        # Obtener el ID de la especificación técnica
        especificacion_id = data.get('especificacion_id')
        
        if not especificacion_id:
            return JsonResponse({
                'success': False,
                'error': 'El ID de la especificación técnica es requerido'
            }, status=400)
        
        # Buscar la EspecificacionTecnica por ID
        try:
            especificacion_tecnica = EspecificacionTecnica.objects.get(id=especificacion_id)
        except EspecificacionTecnica.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'No se encontró la especificación técnica relacionada.'
            }, status=404)
        
        # Actualizar el resultado_markdown si es diferente
        if especificacion_tecnica.resultado_markdown != contenido:
            especificacion_tecnica.resultado_markdown = contenido
            especificacion_tecnica.save(update_fields=['resultado_markdown'])
        
        # Si hay un proyecto_id en la sesión, convertir a Especificacion
        proyecto_id = request.session.get('n8n_proyecto_id')
        redirect_url = None
        
        if proyecto_id:
            try:
                from esp_web.models import Proyecto, Especificacion
                from django.core.files.base import ContentFile
                from django.utils.text import slugify
                from django.utils import timezone
                from django.urls import reverse
                
                proyecto = Proyecto.objects.get(id=proyecto_id, activo=True)
                
                # Verificar que el usuario tiene acceso al proyecto
                if proyecto.creado_por != request.user and not proyecto.publico:
                    return JsonResponse({
                        'success': False,
                        'error': 'No tiene permisos para guardar en este proyecto'
                    }, status=403)
                
                # Crear la especificación en el proyecto
                slug = slugify(especificacion_tecnica.titulo) or 'especificacion'
                timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
                filename = f"{slug}-{timestamp}.md"
                
                especificacion = Especificacion(
                    proyecto=proyecto,
                    titulo=especificacion_tecnica.titulo,
                    contenido=contenido,
                    especificacion_tecnica=especificacion_tecnica,  # Vincular automáticamente
                )
                especificacion.archivo.save(filename, ContentFile(contenido), save=True)
                
                # Limpiar el proyecto_id de la sesión después de guardar
                request.session.pop('n8n_proyecto_id', None)
                
                # Preparar URL de redirección al proyecto
                redirect_url = reverse('esp_web:proyecto_detalle', args=[proyecto.id]) + '?guardado=1'
                
            except Proyecto.DoesNotExist:
                # Si el proyecto no existe, solo guardar en EspecificacionTecnica
                request.session.pop('n8n_proyecto_id', None)
            except Exception as e:
                # Si hay algún error al convertir, solo guardar en EspecificacionTecnica
                logger.error(f"Error al convertir EspecificacionTecnica a Especificacion: {str(e)}", exc_info=True)
        
        return JsonResponse({
            'success': True,
            'message': 'Especificación guardada exitosamente',
            'especificacion_id': especificacion_tecnica.id,
            'redirect_url': redirect_url,
        })
        
    except json.JSONDecodeError as e:
        logger.error(f"JSONDecodeError en guardar_resultado_view: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON inválidos'
        }, status=400)
    except Exception as e:
        logger.error(f"Error inesperado en guardar_resultado_view: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor. Por favor, contacte al administrador o intente nuevamente más tarde.'
        }, status=500)
