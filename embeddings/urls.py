from django.urls import path

from . import views

app_name = 'embeddings'

urlpatterns = [
    path("", views.embeddings_view, name="embeddings_view"),
    path('delete/', views.delete_embeddings, name='delete_embeddings'),
] 