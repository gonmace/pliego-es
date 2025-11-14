from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.http import require_http_methods
from django.conf import settings
import json
import os
from PIL import Image
from esp_web.models import Proyecto
from .models import Ubicacion, UbicacionImagen
from .forms import UbicacionForm, UbicacionContenidoForm
from .utils.generar_ubicacion_pdf import generar_ubicacion_pdf


@login_required
def crear_ubicacion_view(request, proyecto_id):
    """
    Vista para crear una nueva ubicación
    """
    proyecto = get_object_or_404(Proyecto, id=proyecto_id, activo=True)
    
    if proyecto.creado_por != request.user:
        messages.error(request, 'Solo puedes crear ubicaciones en tus propios proyectos.')
        return redirect('esp_web:proyecto_detalle', proyecto_id=proyecto.id)
    
    if request.method == 'POST':
        form = UbicacionForm(request.POST)
        if form.is_valid():
            ubicacion = form.save(commit=False)
            ubicacion.proyecto = proyecto
            
            # Si tiene coordenadas y ciudad, generar PDF automáticamente
            if ubicacion.latitud and ubicacion.longitud and ubicacion.ciudad:
                try:
                    ubicacion.save()  # Guardar primero para tener el ID
                    # Intentar obtener la API key desde settings
                    api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', None)
                    generar_ubicacion_pdf(ubicacion, google_maps_api_key=api_key)
                    ubicacion.save()  # Guardar nuevamente con los archivos adjuntos
                    messages.success(request, f'Ubicación "{ubicacion.nombre}" creada exitosamente. PDF generado automáticamente.')
                except ValueError as e:
                    # Error específico de API key no configurada
                    ubicacion.save()  # Guardar sin PDF si hay error
                    messages.warning(request, f'Ubicación "{ubicacion.nombre}" creada exitosamente. Para generar el PDF automáticamente, configure GOOGLE_MAPS_API_KEY en su archivo .env')
                except Exception as e:
                    ubicacion.save()  # Guardar sin PDF si hay error
                    messages.warning(request, f'Ubicación "{ubicacion.nombre}" creada, pero hubo un error al generar el PDF: {str(e)}')
            else:
                ubicacion.save()
                messages.success(request, f'Ubicación "{ubicacion.nombre}" creada exitosamente.')
            
            return redirect('esp_web:proyecto_detalle', proyecto_id=proyecto.id)
    else:
        form = UbicacionForm()
    
    return render(request, 'ubi_web/crear_ubicacion.html', {
        'form': form,
        'proyecto': proyecto,
    })


@login_required
def editar_ubicacion_view(request, ubicacion_id):
    """
    Vista para editar una ubicación existente
    """
    ubicacion = get_object_or_404(Ubicacion, id=ubicacion_id, proyecto__activo=True)
    proyecto = ubicacion.proyecto
    
    if proyecto.creado_por != request.user:
        messages.error(request, 'Solo puedes editar ubicaciones de tus proyectos.')
        return redirect('esp_web:proyecto_detalle', proyecto_id=proyecto.id)
    
    if request.method == 'POST':
        form = UbicacionForm(request.POST, instance=ubicacion)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ubicación actualizada correctamente.')
            return redirect('esp_web:proyecto_detalle', proyecto_id=proyecto.id)
    else:
        form = UbicacionForm(instance=ubicacion)
    
    return render(request, 'ubi_web/editar_ubicacion.html', {
        'form': form,
        'ubicacion': ubicacion,
        'proyecto': proyecto,
    })


@login_required
def editar_contenido_ubicacion_view(request, ubicacion_id):
    """
    Vista para editar el contenido markdown de una ubicación
    """
    ubicacion = get_object_or_404(Ubicacion, id=ubicacion_id, proyecto__activo=True)
    proyecto = ubicacion.proyecto

    if proyecto.creado_por != request.user:
        messages.error(request, 'Solo puedes editar el contenido de ubicaciones de tus proyectos.')
        return redirect('esp_web:proyecto_detalle', proyecto_id=proyecto.id)

    if request.method == 'POST':
        form = UbicacionContenidoForm(request.POST, instance=ubicacion)
        if form.is_valid():
            form.save()
            messages.success(request, 'Contenido de ubicación actualizado correctamente.')
            return redirect('esp_web:proyecto_detalle', proyecto_id=proyecto.id)
    else:
        form = UbicacionContenidoForm(instance=ubicacion)

    return render(request, 'ubi_web/editar_contenido_ubicacion.html', {
        'form': form,
        'ubicacion': ubicacion,
        'proyecto': proyecto,
    })


@login_required
def eliminar_ubicacion_view(request, ubicacion_id):
    """
    Vista para eliminar una ubicación
    """
    ubicacion = get_object_or_404(Ubicacion, id=ubicacion_id, proyecto__activo=True)
    proyecto = ubicacion.proyecto
    
    if proyecto.creado_por != request.user:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'error': 'Solo puedes eliminar ubicaciones de tus proyectos.'}, status=403)
        messages.error(request, 'Solo puedes eliminar ubicaciones de tus proyectos.')
        return redirect('esp_web:proyecto_detalle', proyecto_id=proyecto.id)
    
    if request.method == 'POST':
        # Eliminar todas las imágenes asociadas
        for imagen in ubicacion.imagenes.all():
            if imagen.imagen:
                imagen.imagen.delete(save=False)
        ubicacion.delete()
        
        # Si es una petición AJAX, devolver JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({
                'success': True,
                'message': 'Ubicación eliminada correctamente.'
            })
        
        messages.success(request, 'Ubicación eliminada correctamente.')
        return redirect('esp_web:proyecto_detalle', proyecto_id=proyecto.id)
    
    # Si es GET, mostrar la página de confirmación (para compatibilidad)
    return render(request, 'ubi_web/eliminar_ubicacion.html', {
        'ubicacion': ubicacion,
        'proyecto': proyecto,
    })


@login_required
def obtener_imagenes_ubicacion_view(request, ubicacion_id):
    """
    Vista AJAX para obtener las imágenes de una ubicación
    """
    ubicacion = get_object_or_404(Ubicacion, id=ubicacion_id, proyecto__activo=True)
    
    # Verificar permisos
    if not (ubicacion.proyecto.publico or ubicacion.proyecto.creado_por == request.user):
        return JsonResponse({'error': 'No tienes permisos para ver las imágenes de esta ubicación.'}, status=403)
    
    imagenes = ubicacion.imagenes.all()
    imagenes_data = [{
        'id': img.id,
        'url': img.imagen.url if img.imagen else '',
        'descripcion': img.descripcion or '',
        'fecha_subida': img.fecha_subida.strftime('%d/%m/%Y %H:%M')
    } for img in imagenes]
    
    return JsonResponse({
        'success': True,
        'imagenes': imagenes_data
    })


@login_required
@require_http_methods(["POST"])
def subir_imagenes_ubicacion_view(request, ubicacion_id):
    """
    Vista AJAX para subir imágenes a una ubicación
    """
    ubicacion = get_object_or_404(Ubicacion, id=ubicacion_id, proyecto__activo=True)
    
    # Verificar que el usuario es propietario del proyecto
    if ubicacion.proyecto.creado_por != request.user:
        return JsonResponse({'error': 'Solo puedes agregar imágenes a ubicaciones de tus proyectos.'}, status=403)
    
    imagenes_subidas = request.FILES.getlist('imagenes')
    
    if not imagenes_subidas:
        return JsonResponse({'error': 'No se proporcionaron imágenes.'}, status=400)
    
    imagenes_creadas = []
    for imagen_file in imagenes_subidas:
        # Validar que sea una imagen
        try:
            img = Image.open(imagen_file)
            img.verify()
            imagen_file.seek(0)  # Resetear el archivo después de verificar
        except Exception:
            continue
        
        ubicacion_imagen = UbicacionImagen(
            ubicacion=ubicacion,
            imagen=imagen_file
        )
        ubicacion_imagen.save()
        imagenes_creadas.append({
            'id': ubicacion_imagen.id,
            'url': ubicacion_imagen.imagen.url
        })
    
    if not imagenes_creadas:
        return JsonResponse({'error': 'No se pudieron procesar las imágenes. Asegúrate de que sean archivos de imagen válidos.'}, status=400)
    
    return JsonResponse({
        'success': True,
        'message': f'{len(imagenes_creadas)} imagen(es) subida(s) correctamente.',
        'imagenes': imagenes_creadas
    })


@login_required
@require_http_methods(["POST"])
def eliminar_imagen_ubicacion_view(request, imagen_id):
    """
    Vista AJAX para eliminar una imagen de una ubicación
    """
    imagen = get_object_or_404(UbicacionImagen, id=imagen_id)
    ubicacion = imagen.ubicacion
    
    # Verificar que el usuario es propietario del proyecto
    if ubicacion.proyecto.creado_por != request.user:
        return JsonResponse({'error': 'Solo puedes eliminar imágenes de ubicaciones de tus proyectos.'}, status=403)
    
    # Eliminar el archivo físico
    if imagen.imagen:
        imagen.imagen.delete(save=False)
    
    imagen.delete()
    
    return JsonResponse({
        'success': True,
        'message': 'Imagen eliminada correctamente.'
    })


@login_required
@require_http_methods(["POST"])
def actualizar_descripcion_imagen_ubicacion_view(request, imagen_id):
    """
    Vista AJAX para actualizar la descripción de una imagen de ubicación
    """
    imagen = get_object_or_404(UbicacionImagen, id=imagen_id)
    ubicacion = imagen.ubicacion
    
    # Verificar que el usuario es propietario del proyecto
    if ubicacion.proyecto.creado_por != request.user:
        return JsonResponse({'error': 'Solo puedes editar descripciones de imágenes de tus proyectos.'}, status=403)
    
    try:
        data = json.loads(request.body)
        descripcion = data.get('descripcion', '').strip()
        
        imagen.descripcion = descripcion
        imagen.save(update_fields=['descripcion'])
        
        return JsonResponse({
            'success': True,
            'message': 'Descripción actualizada correctamente.'
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Datos JSON inválidos.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def descargar_pdf_ubicacion_view(request, ubicacion_id):
    """
    Vista para descargar el PDF de una ubicación
    """
    ubicacion = get_object_or_404(Ubicacion, id=ubicacion_id, proyecto__activo=True)
    
    # Verificar permisos
    if not (ubicacion.proyecto.publico or ubicacion.proyecto.creado_por == request.user):
        messages.error(request, 'No tienes permisos para descargar el PDF de esta ubicación.')
        return redirect('esp_web:proyecto_detalle', proyecto_id=ubicacion.proyecto.id)
    
    if not ubicacion.documento_pdf:
        messages.error(request, 'No hay PDF disponible para esta ubicación.')
        return redirect('esp_web:proyecto_detalle', proyecto_id=ubicacion.proyecto.id)
    
    # Verificar que el archivo existe físicamente
    if not os.path.exists(ubicacion.documento_pdf.path):
        messages.error(request, 'El archivo PDF no se encuentra en el servidor.')
        return redirect('esp_web:proyecto_detalle', proyecto_id=ubicacion.proyecto.id)
    
    try:
        response = FileResponse(
            open(ubicacion.documento_pdf.path, 'rb'),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'attachment; filename="ubicacion_{ubicacion.nombre}_{ubicacion.id}.pdf"'
        return response
    except Exception as e:
        messages.error(request, f'Error al descargar el PDF: {str(e)}')
        return redirect('esp_web:proyecto_detalle', proyecto_id=ubicacion.proyecto.id)
