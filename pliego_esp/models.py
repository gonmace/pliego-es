from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class TokenCost(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        null=True,  # Permitir valores nulos para usuarios no autenticados
        blank=True  # Permitir valores en blanco en formularios
    )
    credits = models.FloatField(default=0.5)
    total_cost = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        if self.user:
            return f"TokenCost: {self.user.username} - {self.total_cost}"
        else:
            return f"TokenCost: Usuario anónimo - {self.total_cost}"
    
    
