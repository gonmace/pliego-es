from django.db import models

# Create your models here.

class DocumentoGenerico(models.Model):
    titulo = models.CharField(max_length=200, verbose_name="Título")
    comentarios = models.TextField(verbose_name="Comentarios", null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = "Documento Genérico"
        verbose_name_plural = "Documentos Genéricos"

class ArchivoAdjunto(models.Model):
    documento = models.ForeignKey(DocumentoGenerico, on_delete=models.CASCADE, related_name='archivos')
    archivo = models.FileField(upload_to='documentos/')
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Archivo de {self.documento.titulo}"
