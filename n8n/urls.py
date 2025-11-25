from django.urls import path
from . import views

app_name = 'n8n'

urlpatterns = [
    path('', views.n8n_pasos_view, name='pasos'),
    path('guardar-paso1/', views.guardar_paso1_view, name='guardar_paso1'),
    path('enviar-especificacion/', views.enviar_especificacion_view, name='enviar_especificacion'),
    path('enviar-parametros/', views.enviar_parametros_seleccionados_view, name='enviar_parametros'),
    path('enviar-titulo-ajustado/', views.enviar_titulo_ajustado_view, name='enviar_titulo_ajustado'),
    path('enviar-actividades/', views.enviar_actividades_view, name='enviar_actividades'),
]






