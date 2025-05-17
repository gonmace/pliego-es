from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import GenericoForm
from .utils.langchain import generar_documento as generar_documento_antiguo
from .langgraph.graph import generar_documento as generar_documento_grafo
import markdown
from django.utils.safestring import mark_safe

def esp_generica_view(request):
    md_generado = None
    if request.method == 'POST':
        if 'descargar' in request.POST and 'md_generado' in request.session:
            response = HttpResponse(request.session['md_generado'], content_type='text/markdown')
            response['Content-Disposition'] = f'attachment; filename="{request.session.get("titulo", "documento")}.md"'
            return response

        form = GenericoForm(request.POST, request.FILES)
        if form.is_valid():
            archivos = request.FILES.getlist('archivos_md')
            aclaraciones = form.cleaned_data['aclaraciones']
            titulo = form.cleaned_data['titulo']
            
            # # Leer el contenido de los archivos
            especificaciones_tecnicas = []
            for archivo in archivos:
                try:
                    contenido = archivo.read().decode('utf-8')
                    especificaciones_tecnicas.append(contenido)
                    archivo.seek(0)  # Resetear el puntero del archivo
                except Exception as e:
                    print(f"Error al leer el archivo: {e}")
            
            # Usar el nuevo sistema de grafo
            try:
                md_generado = generar_documento_grafo(
                    titulo=titulo,
                    especificaciones_tecnicas=especificaciones_tecnicas,
                    aclaraciones=aclaraciones
                )
                
            except Exception as e:
                print(f"Error con el nuevo sistema de grafo: {e}")
                # Fallback al sistema antiguo si hay error
                # md_generado = generar_documento_antiguo(archivos, adicionales, titulo)
            
            # Procesar el markdown
            extensions = [
                'markdown.extensions.extra',
                'markdown.extensions.codehilite',
                'markdown.extensions.tables',
                'markdown.extensions.nl2br',
                # 'markdown.extensions.sane_lists'
            ]
            md_generado_html = markdown.markdown(
                md_generado, output_format='html', extensions=extensions)
            
            # Guardar en la sesión para la descarga
            request.session['md_generado'] = md_generado
            request.session['titulo'] = titulo
            
            return render(request, 'esp_generica.html', {'form': form, 'md_generado': md_generado_html})
    else:
        form = GenericoForm()
    
    return render(request, 'esp_generica.html', {'form': form})
