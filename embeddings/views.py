import os
import json
import re
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import EmbeddingsForm
from .utils.embeddings_processor import procesar_embeddings, listar_embeddings, borrar_embedding

def extraer_datos_desde_md(contenido):
    titulo_match = re.search(r"^##\s*(.+)", contenido, re.MULTILINE)
    descripcion_match = re.search(r"###\s*Descripción\.\s*\n+(.+?)(?=\n###|\Z)", contenido, re.DOTALL)

    titulo = titulo_match.group(1).strip() if titulo_match else ""
    descripcion = descripcion_match.group(1).strip().replace("\n", " ") if descripcion_match else ""
    texto_para_embedding = f"{titulo}. {descripcion}"
    return titulo, descripcion, texto_para_embedding

def embeddings_view(request):
    if request.method == 'POST':
        if 'borrar_seleccionados' in request.POST:
            # Manejar borrado múltiple de embeddings
            embedding_ids = request.POST.getlist('borrar_ids')
            if embedding_ids:
                borrados_exitosos = 0
                for embedding_id in embedding_ids:
                    if borrar_embedding(embedding_id):
                        borrados_exitosos += 1
                
                if borrados_exitosos > 0:
                    messages.success(request, f'Se borraron {borrados_exitosos} embeddings exitosamente.')
                else:
                    messages.error(request, 'No se pudo borrar ningún embedding.')
                
                return redirect('embeddings:embeddings_view')
            else:
                messages.warning(request, 'No se seleccionaron embeddings para borrar')
                return render(request, 'embeddings.html', {
                    'form': EmbeddingsForm(),
                    'embeddings': listar_embeddings()
                })
        
        form = EmbeddingsForm(request.POST, request.FILES)
        if form.is_valid():
            archivos = request.FILES.getlist('archivos_md')
            if not archivos:  # Si no hay archivos nuevos, solo mostrar la lista
                embeddings = listar_embeddings()
                return render(request, 'embeddings.html', {
                    'form': form,
                    'embeddings': embeddings
                })

            datos_estructurados = []
            carpeta_destino = os.path.join(settings.MEDIA_ROOT, 'Markdowns')
            os.makedirs(carpeta_destino, exist_ok=True)

            for archivo in archivos:
                nombre_archivo = archivo.name
                ruta_archivo = os.path.join(carpeta_destino, nombre_archivo)

                with open(ruta_archivo, 'wb+') as destino:
                    for chunk in archivo.chunks():
                        destino.write(chunk)

                with open(ruta_archivo, 'r', encoding='utf-8') as f:
                    contenido = f.read()
                    titulo, descripcion, texto_para_embedding = extraer_datos_desde_md(contenido)

                    datos_estructurados.append({
                        "titulo": titulo,
                        "descripcion": descripcion,
                        "texto_para_embedding": texto_para_embedding,
                        "nombre_archivo": nombre_archivo
                    })

            # Guardar resultado JSON
            json_output = os.path.join(settings.MEDIA_ROOT, 'datos_estructurados.json')
            
            with open(json_output, 'w', encoding='utf-8') as json_file:
                json.dump(datos_estructurados, json_file, ensure_ascii=False, indent=2)

            # Procesar embeddings
            try:
                db_path = procesar_embeddings(json_output)
                messages.success(request, f"Procesados {len(datos_estructurados)} archivos exitosamente.")
            except Exception as e:
                messages.error(request, f"Error al procesar embeddings: {str(e)}")
            
            return redirect('embeddings:embeddings_view')
    else:
        form = EmbeddingsForm()

    # Obtener lista de embeddings existentes
    embeddings = listar_embeddings()
    
    return render(request, 'embeddings.html', {
        'form': form,
        'embeddings': embeddings
    })

def delete_embeddings(request):
    if request.method == 'POST':
        embedding_ids = request.POST.getlist('selected_embeddings')
        if not embedding_ids:
            messages.warning(request, 'No se seleccionaron embeddings para eliminar')
            return redirect('embeddings:embeddings_view')
        
        borrados_exitosos = 0
        for embedding_id in embedding_ids:
            if borrar_embedding(embedding_id):
                borrados_exitosos += 1
        
        if borrados_exitosos > 0:
            messages.success(request, f'Se eliminaron {borrados_exitosos} embeddings exitosamente.')
        else:
            messages.error(request, 'No se pudo eliminar ningún embedding.')
        
        return redirect('embeddings:embeddings_view')
    
    return redirect('embeddings:embeddings_view')
