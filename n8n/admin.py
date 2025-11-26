from django.contrib import admin
from .models import EspecificacionTecnica, Parametros


@admin.register(EspecificacionTecnica)
class EspecificacionTecnicaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo_servicio', 'creado_por', 'fecha_creacion', 'sessionID')
    list_filter = ('tipo_servicio', 'fecha_creacion', 'creado_por')
    search_fields = ('titulo', 'descripcion', 'sessionID')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    list_per_page = 25
    date_hierarchy = 'fecha_creacion'
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('titulo', 'descripcion', 'tipo_servicio')
        }),
        ('Sesión', {
            'fields': ('sessionID',)
        }),
        ('Auditoría', {
            'fields': ('creado_por', 'fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Parametros)
class ParametrosAdmin(admin.ModelAdmin):
    list_display = ('parametro', 'valor', 'unidad', 'especificacion_tecnica', 'sessionID')
    list_filter = ('especificacion_tecnica',)
    search_fields = ('parametro', 'valor', 'detalle', 'sessionID')
    list_per_page = 25
    
    fieldsets = (
        ('Información del Parámetro', {
            'fields': ('parametro', 'valor', 'unidad', 'detalle')
        }),
        ('Relación', {
            'fields': ('especificacion_tecnica', 'sessionID')
        }),
    )








