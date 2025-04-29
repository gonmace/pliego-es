from django import forms
from pathlib import Path
import os
import json

PLIEGO_BASE_PATH = Path(__file__).resolve().parent / "pliegos_base" / "pintado_de_piso_industrial[].md"

def load_pliego_base():
    if os.path.exists(PLIEGO_BASE_PATH):
        with open(PLIEGO_BASE_PATH, 'r', encoding='utf-8') as file:
            return file.read()
    else:
        return "Pliego de especificaciones base."
    
class PliegoForm(forms.Form):
    pliego_base = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 10
            }
        ),
        initial=load_pliego_base()
    )
    titulo = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Título del pliego'
            }
        ),
        initial="Pintado de piso industrial"
    )
    parametros_clave = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Parámetros clave'
            }
        ),
        initial="Acabado texturizado, Pintura de 3 colores, Empleo de compresor, Realizar revoque"
    )
    adicionales = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Adicionales'
            }
        ),
        initial="Retiro de recubrimientos antiguos únicamente con métodos mecánicos no deben usarse quimicos, colocación de barreras de protección para evitar choque de los montacargas"
    )