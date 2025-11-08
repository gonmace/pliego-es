import os
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify


class Proyecto(models.Model):
    nombre = models.CharField(max_length=200, verbose_name="Nombre de Proyecto")
    solicitante = models.CharField(max_length=200, verbose_name="Solicitante")
    ubicacion = models.CharField(max_length=200, verbose_name="Ubicación")
    descripcion = models.TextField(verbose_name="Descripción", blank=True)
    creado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='proyectos_creados'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)
    publico = models.BooleanField(default=False, verbose_name="Público")

    class Meta:
        verbose_name = "Proyecto"
        verbose_name_plural = "Proyectos"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return self.nombre


def especificacion_upload_path(instance, filename):
    base, ext = os.path.splitext(filename)
    slug = slugify(instance.titulo) or 'especificacion'
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
    return f'especificaciones/{instance.proyecto_id}/{slug}-{timestamp}.md'


class Especificacion(models.Model):
    proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.CASCADE,
        related_name='especificaciones'
    )
    titulo = models.CharField(max_length=255)
    contenido = models.TextField(blank=True)
    archivo = models.FileField(upload_to=especificacion_upload_path, blank=True, null=True)
    token_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.titulo} ({self.proyecto.nombre})"

