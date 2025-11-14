from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Value, CharField, Count
from django.db.models.functions import Coalesce, Concat, NullIf, Trim, Lower
from django.db.models import Q
from esp_web.models import Proyecto


@login_required
def proyecto_main_view(request):
    """
    Vista principal que muestra opciones para crear nuevo proyecto o usar uno existente
    """
    # Obtener parámetros de ordenamiento
    sort_by = request.GET.get('sort_by', 'fecha_creacion')
    order = request.GET.get('order', 'desc')
    
    # Validar el campo de ordenamiento
    valid_sort_fields = ['nombre', 'solicitante', 'fecha_creacion', 'publico', 'usuario', 'especificaciones']
    if sort_by not in valid_sort_fields:
        sort_by = 'fecha_creacion'
    
    # Validar el orden
    if order not in ['asc', 'desc']:
        order = 'desc'

    per_page_options = [10, 20, 50, 100]
    per_page_raw = request.GET.get('per_page', str(per_page_options[0]))
    try:
        per_page = int(per_page_raw)
        if per_page not in per_page_options:
            per_page = per_page_options[0]
    except (TypeError, ValueError):
        per_page = per_page_options[0]
    
    # Aplicar ordenamiento
    proyectos_qs = (
        Proyecto.objects.filter(
            activo=True
        )
        .filter(
            Q(publico=True) | Q(creado_por=request.user)
        )
        .select_related('creado_por')
        .annotate(
            usuario_full_name=Trim(
                Concat(
                    Coalesce('creado_por__first_name', Value('', output_field=CharField())),
                    Value(' ', output_field=CharField()),
                    Coalesce('creado_por__last_name', Value('', output_field=CharField()))
                )
            )
        )
        .annotate(
            usuario_sort=Coalesce(
                NullIf('usuario_full_name', Value('', output_field=CharField())),
                'creado_por__username',
                Value('', output_field=CharField())
            )
        )
        .annotate(usuario_sort_lower=Lower('usuario_sort'))
        .annotate(num_especificaciones=Count('especificaciones', distinct=True))
    )

    sort_field_map = {
        'usuario': 'usuario_sort_lower',
        'especificaciones': 'num_especificaciones',
    }
    order_field = sort_field_map.get(sort_by, sort_by)

    order_by = f'-{order_field}' if order == 'desc' else order_field

    proyectos_qs = proyectos_qs.order_by(order_by)

    paginator = Paginator(proyectos_qs, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')
    base_query = query_params.urlencode()
    
    proyecto_seleccionado = None
    
    # Obtener el proyecto seleccionado si existe
    if request.session.get('proyecto_actual_id'):
        try:
            proyecto_seleccionado = Proyecto.objects.get(
                id=request.session['proyecto_actual_id'],
                activo=True
            )
        except Proyecto.DoesNotExist:
            # Si el proyecto no existe, limpiar la sesión
            request.session.pop('proyecto_actual_id', None)
            request.session.pop('proyecto_actual_nombre', None)
    
    return render(request, 'main/index.html', {
        'proyectos': page_obj.object_list,
        'page_obj': page_obj,
        'base_query': base_query,
        'proyecto_seleccionado': proyecto_seleccionado,
        'sort_by': sort_by,
        'order': order,
        'per_page': per_page,
        'per_page_options': per_page_options,
    })
