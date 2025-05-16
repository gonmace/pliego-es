from django.urls import path

from . import views

urlpatterns = [
    path("", views.esp_generica_view, name="esp_generica_view"),
] 