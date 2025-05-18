import os
import json
import re
from django.conf import settings
from django.shortcuts import render
from .forms import EmbeddingsForm

def extraer_datos_desde_md(contenido):
    titulo_match = re.search(r"^##\s*(.+)", contenido, re.MULTILINE)
    descripcion_match = re.search(r"###\s*Descripción\.\s*\n+(.+?)(?=\n###|\Z)", contenido, re.DOTALL)

    titulo = titulo_match.group(1).strip() if titulo_match else ""
    descripcion = descripcion_match.group(1).strip().replace("\n", " ") if descripcion_match else ""
    texto_para_embedding = f"{titulo}. {descripcion}"
    return titulo, descripcion, texto_para_embedding

def embeddings_view(request):
    if request.method == 'POST':
        form = EmbeddingsForm(request.POST, request.FILES)
        if form.is_valid():
            archivos = request.FILES.getlist('archivos_md')
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

            return render(request, 'embeddings.html', {
                'form': form,
                'resultados': f"Procesados {len(datos_estructurados)} archivos.",
                'json_path': json_output
            })
    else:
        form = EmbeddingsForm()

    return render(request, 'embeddings.html', {'form': form})
