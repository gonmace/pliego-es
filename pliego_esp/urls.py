from django.urls import path

from . import views

urlpatterns = [
    path("", views.pliego_especificaciones_view, name="pliego_especificaciones_view"),
    path("gracias/", views.gracias_view, name="gracias"),
] 