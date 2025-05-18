from django.urls import path

from . import views

urlpatterns = [
    path("", views.embeddings_view, name="embeddings_view"),
] 