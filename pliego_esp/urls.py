from django.urls import path

from . import views

urlpatterns = [
    path("", views.pliego_especificaciones, name="pliego_especificaciones"),
] 