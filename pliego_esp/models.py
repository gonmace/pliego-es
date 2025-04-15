from django.db import models
from django.contrib.auth.models import User

class TokenCost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    credits = models.FloatField(default=0.5)
    total_cost = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"TokenCost: {self.user.username} - {self.total_cost}"
    
    
