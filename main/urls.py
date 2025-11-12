from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.proyecto_main_view, name='proyecto_main'),
    path('crear/', views.crear_proyecto_view, name='crear_proyecto'),
    path('lista/', views.lista_proyectos_view, name='lista_proyectos'),
    path('seleccionar/<int:proyecto_id>/', views.seleccionar_proyecto_view, name='seleccionar_proyecto'),
    path('editar/<int:proyecto_id>/', views.editar_proyecto_view, name='editar_proyecto'),
    path('eliminar/<int:proyecto_id>/', views.eliminar_proyecto_view, name='eliminar_proyecto'),
    path('especificaciones/', views.especificaciones_disponibles_view, name='especificaciones_disponibles'),
    path('<int:proyecto_id>/', views.proyecto_detalle_view, name='proyecto_detalle'),
    path('<int:proyecto_id>/nueva-especificacion/', views.ingresar_proyecto_view, name='nueva_especificacion'),
    path('especificacion/<int:especificacion_id>/ver/', views.ver_especificacion_view, name='ver_especificacion'),
    path('especificacion/<int:especificacion_id>/editar/', views.editar_especificacion_view, name='editar_especificacion'),
    path('especificacion/<int:especificacion_id>/eliminar/', views.eliminar_especificacion_view, name='eliminar_especificacion'),
    path('especificacion/<int:especificacion_id>/copiar/', views.copiar_especificacion_view, name='copiar_especificacion'),
    path('especificaciones/copiar/', views.copiar_especificaciones_view, name='copiar_especificaciones'),
]

