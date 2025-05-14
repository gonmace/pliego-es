#views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse, FileResponse, HttpResponseRedirect
from bs4 import BeautifulSoup
import re
import sys
import os
import zipfile
import shutil

from prep_doc_gen.procesadores.del_p_into_li import eliminar_p_dentro_li
from prep_doc_gen.procesadores.format_p_h1_h2_h3_h4_h5_li import procesar_archivo_con_prefijo
from prep_doc_gen.procesadores.split_html_to_md import extraer_y_convertir
from .forms import DocumentoForm, HTMLTagForm, TagsForm, HTMLForm
from .procesadores.eliminar_headers_footers import delete_headers_footers
from .procesadores.del_tags import eliminar_tags_html
import os
from django.urls import reverse
from django.conf import settings
import subprocess

base_dir = settings.BASE_DIR
temp_dir = os.path.join(settings.BASE_DIR, 'temp')

os.makedirs(temp_dir, exist_ok=True)

def download_file(request, filename):
    # Buscar el archivo en la carpeta output dentro de temp
    file_path = os.path.join(settings.BASE_DIR, 'temp', 'output', filename)
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True)
    return JsonResponse({'success': False, 'error': 'Archivo no encontrado'})

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
                                
                # Guardar el archivo subido
                temp_path = os.path.join(temp_dir, archivo.name)
                with open(temp_path, 'wb+') as destination:
                    for chunk in archivo.chunks():
                        destination.write(chunk)
                
                output_filename = '11_' + os.path.splitext(archivo.name)[0] + '.html'
                output_path = os.path.join(temp_dir, output_filename)
                
                subprocess.run(['pandoc', temp_path, '-o', output_path])
                
                return redirect('download_file', filename=output_filename)
    
        if 'etiquetas' in request.POST:
            form = TagsForm(request.POST, request.FILES)
            if form.is_valid():
                archivo = form.cleaned_data['archivo']
                etiquetas = form.cleaned_data['etiquetas']
                
                # Guardar el archivo subido
                temp_path = os.path.join(temp_dir, archivo.name)
                with open(temp_path, 'wb+') as destination:
                    for chunk in archivo.chunks():
                        destination.write(chunk)
                
                # Si etiquetas es una lista, usarla directamente
                tags_list = etiquetas if isinstance(etiquetas, list) else etiquetas.split()
                output_filename = eliminar_tags_html(temp_path, tags_list)
                
                # Eliminar el archivo temporal
                os.remove(temp_path)
                
                return redirect('download_file', filename=output_filename)

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
                                
                # Guardar el archivo subido
                temp_path = os.path.join(temp_dir, archivo.name)
                with open(temp_path, 'wb+') as destination:
                    for chunk in archivo.chunks():
                        destination.write(chunk)
                
                # Procesar el archivo
                procesar_archivo_con_prefijo(temp_path)
                
                # Obtener el nombre del archivo de salida
                output_filename = '14_' + os.path.basename(temp_path)
                
                # Mover el archivo procesado a la carpeta output
                source_path = os.path.join(os.path.dirname(temp_path), output_filename)
                target_path = os.path.join(output_dir, output_filename)
                if os.path.exists(source_path):
                    os.rename(source_path, target_path)
                
                # Eliminar el archivo temporal
                os.remove(temp_path)
                
                # Redirigir a la página de descarga
                return redirect('download_file', filename=output_filename)

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
        'form_etiquetas': TagsForm(),
        'form_lip': HTMLForm(),
        'form_format': HTMLForm(),
        'form_split': HTMLTagForm()
    }
    return render(request, 'prepare_doc_gen.html', context)
    
