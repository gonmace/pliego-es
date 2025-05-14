from django.urls import path

from . import views

urlpatterns = [
    path("", views.prepare_doc_view, name="prepare_doc_view"),
    path("download/<str:filename>", views.download_file, name="download_file"),
] 