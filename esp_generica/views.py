from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import GenericoForm
from .utils.langchain import generar_documento
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
            adicionales = form.cleaned_data['adicionales']
            titulo = form.cleaned_data['titulo']
            md_generado = generar_documento(archivos, adicionales, titulo)
            
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
            
            print(md_generado)
            return render(request, 'esp_generica.html', {'form': form, 'md_generado': md_generado_html})
    else:
        form = GenericoForm()
    
    return render(request, 'esp_generica.html', {'form': form})
