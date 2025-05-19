from django.urls import path

from . import views

urlpatterns = [
    path("prueba", views.pliego_especificaciones_view, name="pliego_especificaciones_view"),
    path("nuevo-pliego/", views.nuevo_pliego_view, name="nuevo_pliego_view"),
    path('api/mejorar-titulo/', views.mejorar_titulo, name='mejorar_titulo'),
] 