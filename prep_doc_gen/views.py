#views.py
import os
import zipfile
import shutil
from django.shortcuts import render, redirect
from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt
import json
from bs4 import BeautifulSoup
from django.urls import reverse

from prep_doc_gen.procesadores.del_p_into_li import eliminar_p_dentro_li
from prep_doc_gen.procesadores.format_p_h1_h2_h3_h4_h5_li import procesar_archivo_con_prefijo
from prep_doc_gen.procesadores.split_html_to_md import extraer_y_convertir
from prep_doc_gen.procesadores.get_titles import extraer_titulos

from .forms import DocumentoForm, HTMLTagForm, TagsForm, HTMLForm
from .procesadores.eliminar_headers_footers import delete_headers_footers
from .procesadores.del_tags import eliminar_tags_html

from django.conf import settings
import subprocess

base_dir = settings.BASE_DIR
temp_dir = os.path.join(settings.BASE_DIR, 'temp')

os.makedirs(temp_dir, exist_ok=True)

def is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'

def download_file(request, filename):
    """
    Vista para descargar archivos procesados
    """
    file_path = os.path.join(temp_dir, 'output', filename)
    print(f"Intentando descargar archivo: {file_path}")
    print(f"¿El archivo existe? {os.path.exists(file_path)}")
    print(f"Contenido del directorio output: {os.listdir(os.path.join(temp_dir, 'output'))}")
    
    if os.path.exists(file_path):
        print(f"Archivo encontrado, preparando descarga: {file_path}")
        response = FileResponse(open(file_path, 'rb'))
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    raise Http404(f"El archivo {filename} no existe")

def replace_titles_in_html(file_path, new_titles, tag):
    with open(file_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file.read(), 'html.parser')
    
    # Encontrar todos los elementos del tag especificado
    elements = soup.find_all(tag)
    
    # Reemplazar cada título con su nuevo valor
    for element, new_title in zip(elements, new_titles):
        element.string = new_title
    
    # Guardar el archivo modificado
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(str(soup))

def prepare_doc_view(request):
    if request.method == 'POST':
        
        if 'submit_eliminar' in request.POST:
            form = DocumentoForm(request.POST, request.FILES)
            if form.is_valid():
                archivo = form.cleaned_data['archivo']
                                
                # Guardar el archivo subido
                temp_path = os.path.join(temp_dir, archivo.name)
                with open(temp_path, 'wb+') as destination:
                    for chunk in archivo.chunks():
                        destination.write(chunk)
                
                # Procesar el archivo
                output_filename = delete_headers_footers(temp_path, base_dir)
                
                # Eliminar el archivo temporal
                os.remove(temp_path)
                
                # Redirigir a la página de descarga
                return redirect('download_file', filename=output_filename)
    
        if 'submit_convertir' in request.POST:
            form = DocumentoForm(request.POST, request.FILES)
            if form.is_valid():
                archivo = form.cleaned_data['archivo']
                
                # Crear directorio output si no existe
                output_dir = os.path.join(temp_dir, 'output')
                os.makedirs(output_dir, exist_ok=True)
                                
                # Guardar el archivo subido
                temp_path = os.path.join(temp_dir, archivo.name)
                with open(temp_path, 'wb+') as destination:
                    for chunk in archivo.chunks():
                        destination.write(chunk)
                
                output_filename = '11_' + os.path.splitext(archivo.name)[0] + '.html'
                output_path = os.path.join(output_dir, output_filename)
                
                subprocess.run(['pandoc', temp_path, '-o', output_path])
                
                # Eliminar el archivo temporal
                os.remove(temp_path)
                
                return redirect('download_file', filename=output_filename)
    
        if 'submit_titulos' in request.POST:
            form = HTMLTagForm(request.POST, request.FILES)
            if form.is_valid():
                archivo = form.cleaned_data['archivo']
                etiqueta = form.cleaned_data['etiqueta']
                
                # Guardar el archivo subido
                temp_path = os.path.join(temp_dir, archivo.name)
                with open(temp_path, 'wb+') as destination:
                    for chunk in archivo.chunks():
                        destination.write(chunk)

                json_result = extraer_titulos(temp_path, etiqueta)

                # Siempre retornar JSON response para este endpoint
                return JsonResponse({
                    'success': True,
                    'resultados': json_result,
                    'tag': etiqueta,
                    'original_filename': archivo.name,
                    'original_filepath': temp_path
                })
        
        # Nuevo endpoint para procesar la lista final de títulos
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.method == 'POST':
            try:
                data = json.loads(request.body)
                print("Datos recibidos:", data)
                
                if data.get('action') == 'final_titles' and data.get('file_type') == 'titulos':
                    titles = data.get('titles', [])
                    original_filename = data.get('original_filename')
                    original_filepath = data.get('original_filepath')
                    tag = data.get('tag')
                    
                    if not all([titles, original_filename, original_filepath, tag]):
                        return JsonResponse({
                            'success': False,
                            'error': 'Faltan datos requeridos'
                        })
                    
                    # Crear nombre del archivo de salida
                    output_filename = '12_' + original_filename
                    output_path = os.path.join(temp_dir, 'output', output_filename)
                    
                    print("Rutas de archivos:")
                    print("Input:", original_filepath)
                    print("Output:", output_path)
                    
                    # Verificar si el archivo original existe
                    if not os.path.exists(original_filepath):
                        return JsonResponse({
                            'success': False,
                            'error': f'Archivo original no encontrado en: {original_filepath}'
                        })
                    
                    # Asegurar que el directorio de salida existe
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    
                    try:
                        # Copiar archivo original al nuevo archivo
                        shutil.copy2(original_filepath, output_path)
                        
                        # Reemplazar los títulos en el archivo
                        replace_titles_in_html(output_path, titles, tag)
                        
                        print("\n=== LISTA FINAL DE TÍTULOS ===")
                        print(f"Tipo de archivo: {data.get('file_type')}")
                        print(f"Archivo procesado: {output_filename}")
                        print("----------------------------")
                        for i, title in enumerate(titles, 1):
                            print(f"{i}. {title}")
                        print("============================\n")
                        
                        # Generar URL de descarga usando reverse
                        download_url = reverse('download_file', kwargs={'filename': output_filename})
                        
                        return JsonResponse({
                            'success': True,
                            'message': f'Lista de {len(titles)} títulos procesada',
                            'download_url': download_url
                        })
                    except Exception as e:
                        print("Error al procesar el archivo:", str(e))  # Debug print
                        return JsonResponse({
                            'success': False,
                            'error': f'Error al procesar el archivo: {str(e)}'
                        })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'Tipo de acción o archivo no válido'
                    })
            except json.JSONDecodeError as e:
                print("Error al decodificar JSON:", str(e))  # Debug print
                return JsonResponse({
                    'success': False,
                    'error': f'Error al decodificar JSON: {str(e)}'
                })
            except Exception as e:
                print("Error general:", str(e))  # Debug print
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                })
    
        if 'etiquetas' in request.POST:
            form = TagsForm(request.POST, request.FILES)
            if form.is_valid():
                archivo = form.cleaned_data['archivo']
                etiquetas = form.cleaned_data['etiquetas']
                
                # Crear directorio output si no existe
                output_dir = os.path.join(temp_dir, 'output')
                os.makedirs(output_dir, exist_ok=True)
                print(f"Directorio output creado/verificado: {output_dir}")
                
                # Guardar el archivo subido
                temp_path = os.path.join(temp_dir, archivo.name)
                print(f"Guardando archivo temporal en: {temp_path}")
                with open(temp_path, 'wb+') as destination:
                    for chunk in archivo.chunks():
                        destination.write(chunk)
                
                try:
                    # Si etiquetas es una lista, usarla directamente
                    tags_list = etiquetas if isinstance(etiquetas, list) else etiquetas.split()
                    print(f"Tags a eliminar: {tags_list}")
                    
                    # Procesar el archivo
                    output_filename = eliminar_tags_html(temp_path, tags_list)
                    print(f"Nombre del archivo de salida: {output_filename}")
                    
                    # Verificar que el archivo existe en el directorio output
                    output_path = os.path.join(output_dir, output_filename)
                    print(f"Ruta completa del archivo de salida: {output_path}")
                    
                    # Si el archivo no está en output, pero existe en temp/output, moverlo
                    source_path = os.path.join(os.path.dirname(temp_path), 'output', output_filename)
                    if os.path.exists(source_path) and not os.path.exists(output_path):
                        print(f"Moviendo archivo de {source_path} a {output_path}")
                        os.rename(source_path, output_path)
                    
                    # Verificar que el archivo existe
                    if not os.path.exists(output_path):
                        raise FileNotFoundError(f"El archivo procesado no se encuentra en: {output_path}")
                    
                    print(f"¿El archivo existe en la ubicación final? {os.path.exists(output_path)}")
                    
                    # Eliminar el archivo temporal
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                        print("Archivo temporal eliminado")
                    
                    return redirect('download_file', filename=output_filename)
                except Exception as e:
                    print(f"Error durante el procesamiento: {str(e)}")
                    # Si hay un error, asegurarse de limpiar el archivo temporal
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    raise e

        if 'submit_lip' in request.POST:
            form = HTMLForm(request.POST, request.FILES)
            if form.is_valid():
                archivo = form.cleaned_data['archivo']
                
                # Crear directorio output si no existe
                output_dir = os.path.join(temp_dir, 'output')
                os.makedirs(output_dir, exist_ok=True)
                                
                # Guardar el archivo subido
                temp_path = os.path.join(temp_dir, archivo.name)
                with open(temp_path, 'wb+') as destination:
                    for chunk in archivo.chunks():
                        destination.write(chunk)
                
                # Procesar el archivo
                output_filename = eliminar_p_dentro_li(temp_path, base_dir)
                
                # Extraer solo el nombre del archivo de la ruta completa
                output_filename = os.path.basename(output_filename)
                
                # Mover el archivo procesado a la carpeta output
                source_path = os.path.join(os.path.dirname(temp_path), output_filename)
                target_path = os.path.join(output_dir, output_filename)
                if os.path.exists(source_path):
                    os.rename(source_path, target_path)
                
                # Eliminar el archivo temporal
                os.remove(temp_path)
                
                # Redirigir a la página de descarga
                return redirect('download_file', filename=output_filename)

        if 'submit_format' in request.POST:
            form = HTMLForm(request.POST, request.FILES)
            if form.is_valid():
                archivo = form.cleaned_data['archivo']
                
                # Crear directorio output si no existe
                output_dir = os.path.join(temp_dir, 'output')
                os.makedirs(output_dir, exist_ok=True)
                print(f"Directorio output creado/verificado: {output_dir}")
                                
                # Guardar el archivo subido
                temp_path = os.path.join(temp_dir, archivo.name)
                print(f"Guardando archivo temporal en: {temp_path}")
                with open(temp_path, 'wb+') as destination:
                    for chunk in archivo.chunks():
                        destination.write(chunk)
                
                try:
                    # Procesar el archivo
                    procesar_archivo_con_prefijo(temp_path)
                    
                    # Obtener el nombre del archivo de salida
                    output_filename = '15_' + os.path.basename(temp_path)
                    print(f"Nombre del archivo de salida: {output_filename}")
                    
                    # Verificar que el archivo existe en el directorio output
                    output_path = os.path.join(output_dir, output_filename)
                    print(f"Ruta completa del archivo de salida: {output_path}")
                    
                    # Si el archivo no está en output, pero existe en temp/output, moverlo
                    source_path = os.path.join(os.path.dirname(temp_path), 'output', output_filename)
                    if os.path.exists(source_path) and not os.path.exists(output_path):
                        print(f"Moviendo archivo de {source_path} a {output_path}")
                        os.rename(source_path, output_path)
                    
                    # Verificar que el archivo existe
                    if not os.path.exists(output_path):
                        raise FileNotFoundError(f"El archivo procesado no se encuentra en: {output_path}")
                    
                    print(f"¿El archivo existe en la ubicación final? {os.path.exists(output_path)}")
                    
                    # Eliminar el archivo temporal
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                        print("Archivo temporal eliminado")
                    
                    return redirect('download_file', filename=output_filename)
                except Exception as e:
                    print(f"Error durante el procesamiento: {str(e)}")
                    # Si hay un error, asegurarse de limpiar el archivo temporal
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    raise e

        if 'submit_split' in request.POST:
            form = HTMLTagForm(request.POST, request.FILES)
            if form.is_valid():
                archivo = form.cleaned_data['archivo']
                etiqueta = form.cleaned_data['etiqueta']
                
                # Crear directorio output si no existe
                output_dir = os.path.join(temp_dir, 'output')
                os.makedirs(output_dir, exist_ok=True)
                
                # Crear directorio temporal para los archivos MD
                md_dir = os.path.join(temp_dir, 'md_files')
                os.makedirs(md_dir, exist_ok=True)
                                
                # Guardar el archivo subido
                temp_path = os.path.join(temp_dir, archivo.name)
                with open(temp_path, 'wb+') as destination:
                    for chunk in archivo.chunks():
                        destination.write(chunk)
                
                # Procesar el archivo y dividirlo en MD usando la etiqueta seleccionada
                extraer_y_convertir(temp_path, etiqueta=etiqueta, output_dir=md_dir, formato='md')
                
                # Crear archivo ZIP con los archivos MD
                zip_filename = '15_' + os.path.splitext(archivo.name)[0] + '.zip'
                zip_path = os.path.join(output_dir, zip_filename)
                
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(md_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, md_dir)
                            zipf.write(file_path, arcname)
                
                # Limpiar archivos temporales
                os.remove(temp_path)
                shutil.rmtree(md_dir)
                
                # Redirigir a la página de descarga
                return redirect('download_file', filename=zip_filename)

    context = {
        'form_eliminar': DocumentoForm(),
        'form_convertir': DocumentoForm(),
        'form_titulos': HTMLTagForm(),
        'form_etiquetas': TagsForm(),
        'form_lip': HTMLForm(),
        'form_format': HTMLForm(),
        'form_split': HTMLTagForm()
    }
    return render(request, 'prepare_doc_gen.html', context)
    
