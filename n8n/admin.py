from django.contrib import admin
from .models import EspecificacionTecnica, Parametros, ActividadesAdicionales


class ParametrosInline(admin.TabularInline):
    """Inline para mostrar parámetros relacionados con la especificación técnica"""
    model = Parametros
    extra = 0
    fields = ('parametro', 'valor', 'unidad', 'detalle')
    verbose_name = 'Parámetro'
    verbose_name_plural = 'Parámetros Técnicos'


class ActividadesAdicionalesInline(admin.TabularInline):
    """Inline para mostrar actividades adicionales relacionadas con la especificación técnica"""
    model = ActividadesAdicionales
    extra = 0
    fields = ('nombre', 'valor_recomendado', 'unidad_medida', 'descripcion')
    verbose_name = 'Actividad Adicional'
    verbose_name_plural = 'Actividades Adicionales'


@admin.register(EspecificacionTecnica)
class EspecificacionTecnicaAdmin(admin.ModelAdmin):
    list_display = ('id', 'titulo', 'tipo_servicio', 'creado_por', 'fecha_creacion')
    list_filter = ('tipo_servicio', 'fecha_creacion', 'creado_por')
    search_fields = ('titulo', 'descripcion')
    readonly_fields = ('id', 'fecha_creacion', 'fecha_actualizacion')
    list_per_page = 25
    date_hierarchy = 'fecha_creacion'
    inlines = [ParametrosInline, ActividadesAdicionalesInline]
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('id', 'titulo', 'descripcion', 'tipo_servicio')
        }),
        ('Auditoría', {
            'fields': ('creado_por', 'fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Parametros)
class ParametrosAdmin(admin.ModelAdmin):
    list_display = ('id', 'parametro', 'valor', 'unidad', 'especificacion_tecnica')
    list_filter = ('especificacion_tecnica',)
    search_fields = ('parametro', 'valor', 'detalle')
    readonly_fields = ('id',)
    list_per_page = 25
    
    fieldsets = (
        ('Información del Parámetro', {
            'fields': ('parametro', 'valor', 'unidad', 'detalle')
        }),
        ('Relación', {
            'fields': ('especificacion_tecnica', 'id')
        }),
    )


@admin.register(ActividadesAdicionales)
class ActividadesAdicionalesAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'valor_recomendado', 'unidad_medida', 'especificacion_tecnica')
    list_filter = ('especificacion_tecnica',)
    search_fields = ('nombre', 'valor_recomendado', 'descripcion')
    readonly_fields = ('id',)
    list_per_page = 25
    
    fieldsets = (
        ('Información de la Actividad', {
            'fields': ('nombre', 'valor_recomendado', 'unidad_medida', 'descripcion')
        }),
        ('Relación', {
            'fields': ('especificacion_tecnica', 'id')
        }),
    )








