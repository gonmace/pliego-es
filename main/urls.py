from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.proyecto_main_view, name='proyecto_main'),
]

