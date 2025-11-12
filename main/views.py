from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Value, CharField, Count
from django.db.models.functions import Coalesce, Concat, NullIf, Trim, Lower
from django.db.models import Q
from django.utils.http import url_has_allowed_host_and_scheme
from django.urls import reverse
from django.core.files.base import ContentFile
from django.utils.text import slugify
from django.utils import timezone
from django.utils.safestring import mark_safe
from markdown import markdown
from .models import Proyecto, Especificacion
from .forms import ProyectoForm, EspecificacionForm


def _get_especificaciones_accesibles(request):
    qs = (
        Especificacion.objects.filter(
            proyecto__activo=True
        )
        .filter(
            Q(proyecto__publico=True) | Q(proyecto__creado_por=request.user)
        )
        .select_related('proyecto')
        .order_by('proyecto__nombre', '-fecha_creacion')
    )
    especificaciones = []
    for especificacion in qs:
        preview_html = markdown(especificacion.contenido or '', extensions=['extra'])
        especificacion.preview_html = mark_safe(preview_html)
        especificaciones.append(especificacion)
    return especificaciones


def _copiar_especificaciones(user, especificaciones_ids, proyecto_destino):
    copiados = 0
    for spec_id in especificaciones_ids:
        try:
            especificacion = Especificacion.objects.select_related('proyecto').get(
                id=spec_id,
                proyecto__activo=True
            )
        except Especificacion.DoesNotExist:
            continue

        if not (especificacion.proyecto.publico or especificacion.proyecto.creado_por == user):
            continue

        base_titulo = especificacion.titulo
        nuevo_titulo = base_titulo
        contador = 1
        while Especificacion.objects.filter(proyecto=proyecto_destino, titulo=nuevo_titulo).exists():
            if contador == 1:
                nuevo_titulo = f"{base_titulo} (Copia)"
            else:
                nuevo_titulo = f"{base_titulo} (Copia {contador})"
            contador += 1

        nueva_especificacion = Especificacion(
            proyecto=proyecto_destino,
            titulo=nuevo_titulo,
            contenido=especificacion.contenido,
            token_cost=especificacion.token_cost,
        )

        slug = slugify(nueva_especificacion.titulo) or 'especificacion'
        filename = f"{slug}-{timezone.now():%Y%m%d%H%M%S}.md"
        nueva_especificacion.archivo.save(filename, ContentFile(especificacion.contenido), save=False)
        nueva_especificacion.save()
        copiados += 1
    return copiados


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


@login_required
def crear_proyecto_view(request):
    """
    Vista para crear un nuevo proyecto
    """
    if request.method == 'POST':
        form = ProyectoForm(request.POST)
        if form.is_valid():
            proyecto = form.save(commit=False)
            if request.user.is_authenticated:
                proyecto.creado_por = request.user
            proyecto.save()
            messages.success(request, f'Proyecto "{proyecto.nombre}" creado exitosamente.')
            # Redirigir a la página principal o a la lista de proyectos
            return redirect('main:proyecto_main')
    else:
        form = ProyectoForm()
    
    return render(request, 'main/crear_proyecto.html', {
        'form': form
    })


@login_required
def lista_proyectos_view(request):
    """
    Vista para listar todos los proyectos existentes
    """
    proyectos = Proyecto.objects.filter(activo=True).order_by('-fecha_creacion')
    
    return render(request, 'main/lista_proyectos.html', {
        'proyectos': proyectos
    })


@login_required
def proyecto_detalle_view(request, proyecto_id):
    """
    Vista de detalle del proyecto seleccionado
    """
    proyecto = get_object_or_404(Proyecto, id=proyecto_id, activo=True)
    es_propietario = proyecto.creado_por == request.user

    # Persistir el proyecto activo en la sesión
    request.session['proyecto_actual_id'] = proyecto.id
    request.session['proyecto_actual_nombre'] = proyecto.nombre

    especificaciones = proyecto.especificaciones.all()

    spec_sort_by = request.GET.get('spec_sort_by', 'titulo')
    spec_order = request.GET.get('spec_order', 'asc')

    valid_spec_sort_fields = ['titulo', 'proyecto', 'usuario']
    if spec_sort_by not in valid_spec_sort_fields:
        spec_sort_by = 'titulo'

    if spec_order not in ['asc', 'desc']:
        spec_order = 'asc'

    especificaciones_accesibles = _get_especificaciones_accesibles(request)
    spec_modal_open = request.GET.get('spec_modal_open') == '1'

    key_map = {
        'titulo': lambda e: (e.titulo or '').lower(),
        'proyecto': lambda e: (e.proyecto.nombre or '').lower(),
        'usuario': lambda e: (
            (
                e.proyecto.creado_por.get_full_name()
                or e.proyecto.creado_por.username
            ).lower()
            if e.proyecto.creado_por
            else ''
        ),
    }

    especificaciones_accesibles.sort(
        key=key_map[spec_sort_by],
        reverse=(spec_order == 'desc')
    )

    return render(request, 'main/proyecto_detalle.html', {
        'proyecto': proyecto,
        'especificaciones': especificaciones,
        'es_propietario': es_propietario,
        'especificaciones_accesibles': especificaciones_accesibles,
        'spec_sort_by': spec_sort_by,
        'spec_order': spec_order,
        'spec_modal_open': spec_modal_open,
    })


@login_required
def ingresar_proyecto_view(request, proyecto_id):
    """
    Vincula el proyecto activo y redirige al flujo de nuevo pliego
    """
    proyecto = get_object_or_404(Proyecto, id=proyecto_id, activo=True)

    if proyecto.creado_por != request.user:
        messages.error(request, 'Solo puedes crear especificaciones en tus propios proyectos.')
        return redirect('main:proyecto_main')

    request.session['proyecto_actual_id'] = proyecto.id
    request.session['proyecto_actual_nombre'] = proyecto.nombre

    intended = request.GET.get('next')
    if intended == 'detalle':
        return redirect('main:proyecto_detalle', proyecto_id=proyecto.id)

    return redirect(reverse('nuevo_pliego_view'))


@login_required
def seleccionar_proyecto_view(request, proyecto_id):
    """
    Vista para seleccionar un proyecto existente
    """
    proyecto = get_object_or_404(Proyecto, id=proyecto_id, activo=True)
    
    # Guardar el proyecto seleccionado en la sesión
    request.session['proyecto_actual_id'] = proyecto.id
    request.session['proyecto_actual_nombre'] = proyecto.nombre
    
    next_url = request.GET.get('next')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)

    referer = request.META.get('HTTP_REFERER')
    if referer and url_has_allowed_host_and_scheme(referer, allowed_hosts={request.get_host()}):
        return redirect(referer)

    return redirect('main:proyecto_main')


@login_required
def editar_especificacion_view(request, especificacion_id):
    especificacion = get_object_or_404(Especificacion, id=especificacion_id, proyecto__activo=True)
    proyecto = especificacion.proyecto

    if proyecto.creado_por != request.user:
        messages.error(request, 'Solo puedes editar especificaciones de tus proyectos.')
        return redirect('main:proyecto_detalle', proyecto_id=proyecto.id)

    if request.method == 'POST':
        form = EspecificacionForm(request.POST, instance=especificacion)
        if form.is_valid():
            especificacion = form.save(commit=False)
            if especificacion.archivo:
                especificacion.archivo.delete(save=False)
            slug = slugify(especificacion.titulo) or 'especificacion'
            filename = f"{slug}-{timezone.now().strftime('%Y%m%d%H%M%S')}.md"
            especificacion.archivo.save(filename, ContentFile(especificacion.contenido), save=False)
            especificacion.save()
            messages.success(request, 'Especificación actualizada correctamente.')
            return redirect('main:proyecto_detalle', proyecto_id=proyecto.id)
    else:
        form = EspecificacionForm(instance=especificacion)

    return render(request, 'main/editar_especificacion.html', {
        'form': form,
        'especificacion': especificacion,
        'proyecto': proyecto,
    })


@login_required
def eliminar_especificacion_view(request, especificacion_id):
    especificacion = get_object_or_404(Especificacion, id=especificacion_id, proyecto__activo=True)
    proyecto = especificacion.proyecto

    if proyecto.creado_por != request.user:
        messages.error(request, 'Solo puedes eliminar especificaciones de tus proyectos.')
        return redirect('main:proyecto_detalle', proyecto_id=proyecto.id)

    if request.method == 'POST':
        if especificacion.archivo:
            especificacion.archivo.delete(save=False)
        especificacion.delete()
        messages.success(request, 'Especificación eliminada correctamente.')
        return redirect('main:proyecto_detalle', proyecto_id=proyecto.id)

    return render(request, 'main/eliminar_especificacion.html', {
        'especificacion': especificacion,
        'proyecto': proyecto,
    })


@login_required
def eliminar_proyecto_view(request, proyecto_id):
    """
    Vista para eliminar (desactivar) un proyecto
    """
    proyecto = get_object_or_404(Proyecto, id=proyecto_id, activo=True)

    if proyecto.creado_por != request.user:
        messages.error(request, 'Solo puedes eliminar proyectos que pertenecen a tu cuenta.')
        return redirect('main:proyecto_main')
    
    if request.method == 'POST':
        proyecto.activo = False
        proyecto.save()
        messages.success(request, f'Proyecto "{proyecto.nombre}" eliminado exitosamente.')
        return redirect('main:proyecto_main')
    
    return render(request, 'main/eliminar_proyecto.html', {
        'proyecto': proyecto
    })


@login_required
def especificaciones_disponibles_view(request):
    sort_by = request.GET.get('sort_by', 'nombre')
    order = request.GET.get('order', 'asc')
    dest_id = request.GET.get('dest')
    dest_project = None

    valid_sort_fields = ['nombre', 'proyecto', 'fecha']
    if sort_by not in valid_sort_fields:
        sort_by = 'nombre'

    if order not in ['asc', 'desc']:
        order = 'asc'

    especificaciones = _get_especificaciones_accesibles(request)

    key_map = {
        'nombre': lambda e: e.titulo.lower(),
        'proyecto': lambda e: e.proyecto.nombre.lower(),
        'fecha': lambda e: e.fecha_creacion,
    }

    especificaciones.sort(key=key_map[sort_by], reverse=(order == 'desc'))

    if dest_id:
        try:
            dest_project = Proyecto.objects.get(id=dest_id, activo=True, creado_por=request.user)
        except Proyecto.DoesNotExist:
            dest_project = None

    mis_proyectos = Proyecto.objects.filter(activo=True, creado_por=request.user).order_by('nombre')
    return render(request, 'main/especificaciones_disponibles.html', {
        'especificaciones': especificaciones,
        'mis_proyectos': mis_proyectos,
        'sort_by': sort_by,
        'order': order,
        'dest_id': dest_id,
        'dest_project': dest_project,
    })


@login_required
def ver_especificacion_view(request, especificacion_id):
    especificacion = get_object_or_404(
        Especificacion.objects.select_related('proyecto'),
        id=especificacion_id,
        proyecto__activo=True
    )

    if not (especificacion.proyecto.publico or especificacion.proyecto.creado_por == request.user):
        messages.error(request, 'No tienes permisos para ver esta especificación.')
        return redirect('main:proyecto_main')

    origin = request.GET.get('from')
    if origin not in ('disponibles', 'proyecto'):
        origin = 'proyecto'

    dest_id = request.GET.get('dest')
    dest_project = None
    if origin == 'disponibles' and dest_id:
        try:
            dest_project = Proyecto.objects.get(id=dest_id, activo=True, creado_por=request.user)
        except Proyecto.DoesNotExist:
            dest_project = None

    preview_html = markdown(especificacion.contenido or '', extensions=['extra'])
    preview_html = mark_safe(preview_html)

    return render(request, 'main/ver_especificacion.html', {
        'especificacion': especificacion,
        'preview_html': preview_html,
        'breadcrumbs_origin': origin,
        'dest_project': dest_project,
    })


@login_required
def copiar_especificacion_view(request, especificacion_id):
    if request.method != 'POST':
        messages.error(request, 'Acción inválida al intentar copiar la especificación.')
        return redirect('main:proyecto_main')

    proyecto_destino_id = request.POST.get('proyecto_destino')
    if not proyecto_destino_id:
        messages.error(request, 'Debes seleccionar un proyecto destino.')
        return redirect('main:proyecto_main')

    try:
        proyecto_destino = Proyecto.objects.get(
            id=proyecto_destino_id,
            activo=True,
            creado_por=request.user
        )
    except Proyecto.DoesNotExist:
        messages.error(request, 'Solo puedes copiar especificaciones a tus propios proyectos activos.')
        return redirect('main:proyecto_main')

    copiados = _copiar_especificaciones(request.user, [str(especificacion_id)], proyecto_destino)
    if copiados:
        messages.success(
            request,
            f'Se copió la especificación al proyecto "{proyecto_destino.nombre}".'
        )
    else:
        messages.warning(request, 'No se copiaron especificaciones. Verifica la selección y tus permisos.')

    next_url = request.POST.get('next')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect('main:proyecto_detalle', proyecto_destino.id)


@login_required
def copiar_especificaciones_view(request):
    if request.method != 'POST':
        messages.error(request, 'Acción inválida al intentar copiar especificaciones.')
        return redirect('main:proyecto_main')

    especificaciones_ids = request.POST.getlist('especificaciones')
    if not especificaciones_ids:
        messages.error(request, 'Selecciona al menos una especificación.')
        return redirect('main:proyecto_main')
    especificaciones_ids = list(dict.fromkeys(str(e) for e in especificaciones_ids))

    proyecto_destino_id = request.POST.get('proyecto_destino')
    if not proyecto_destino_id:
        messages.error(request, 'Debes seleccionar un proyecto destino.')
        return redirect('main:proyecto_main')

    try:
        proyecto_destino = Proyecto.objects.get(
            id=proyecto_destino_id,
            activo=True,
            creado_por=request.user
        )
    except Proyecto.DoesNotExist:
        messages.error(request, 'Solo puedes copiar especificaciones a tus propios proyectos activos.')
        return redirect('main:proyecto_main')

    copiados = _copiar_especificaciones(request.user, especificaciones_ids, proyecto_destino)

    if copiados:
        messages.success(
            request,
            f'Se copiaron {copiados} especificación(es) al proyecto "{proyecto_destino.nombre}".'
        )
    else:
        messages.warning(request, 'No se copiaron especificaciones. Verifica la selección y tus permisos.')

    next_url = request.POST.get('next')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect('main:proyecto_detalle', proyecto_destino.id)


@login_required
def editar_proyecto_view(request, proyecto_id):
    """
    Vista para editar un proyecto existente
    """
    proyecto = get_object_or_404(Proyecto, id=proyecto_id, activo=True)
    
    if proyecto.creado_por != request.user:
        messages.error(request, 'Solo puedes editar proyectos que pertenecen a tu cuenta.')
        return redirect('main:proyecto_main')

    if request.method == 'POST':
        form = ProyectoForm(request.POST, instance=proyecto)
        if form.is_valid():
            proyecto = form.save()
            messages.success(request, f'Proyecto "{proyecto.nombre}" actualizado exitosamente.')
            return redirect('main:proyecto_main')
    else:
        form = ProyectoForm(instance=proyecto)
    
    return render(request, 'main/editar_proyecto.html', {
        'form': form,
        'proyecto': proyecto
    })

