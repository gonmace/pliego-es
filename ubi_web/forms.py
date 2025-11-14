from django import forms
from .models import Ubicacion


class UbicacionForm(forms.ModelForm):
    class Meta:
        model = Ubicacion
        fields = ['nombre', 'descripcion', 'latitud', 'longitud', 'ciudad']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Ingrese el nombre de la ubicación'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 4,
                'placeholder': 'Ingrese una descripción de la ubicación (opcional)'
            }),
            'latitud': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Ej: -33.4489',
                'step': 'any'
            }),
            'longitud': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Ej: -70.6693',
                'step': 'any'
            }),
            'ciudad': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Ej: Santiago'
            }),
        }
        labels = {
            'nombre': 'Nombre de la Ubicación',
            'descripcion': 'Descripción',
            'latitud': 'Latitud',
            'longitud': 'Longitud',
            'ciudad': 'Ciudad',
        }


class UbicacionContenidoForm(forms.ModelForm):
    class Meta:
        model = Ubicacion
        fields = ['contenido']
        widgets = {
            'contenido': forms.Textarea(attrs={
                'class': 'hidden',
            }),
        }
        labels = {
            'contenido': 'Contenido (Markdown)',
        }
