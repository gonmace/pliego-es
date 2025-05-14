# forms.py
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field

class DocumentoForm(forms.Form):
    archivo = forms.FileField(
        label="",
        required=True,
        widget=forms.ClearableFileInput(attrs={
            "class": "hidden",
            "accept": ".docx,.doc"
        })
    )
    
class HTMLForm(forms.Form):
    archivo = forms.FileField(
        label="",
        required=True,
        widget=forms.ClearableFileInput(attrs={
            "class": "hidden",
            "accept": ".html"
        })
    )

class HTMLTagForm(forms.Form):
    archivo = forms.FileField(
        label="",
        required=True,
        widget=forms.ClearableFileInput(attrs={
            "class": "hidden",
            "accept": ".html"
        })
    )
    etiqueta = forms.ChoiceField(
        label="",
        required=True,
        choices=[
            ('h1', 'H1'),
            ('h2', 'H2'),
            ('h3', 'H3'),
            ('h4', 'H4'),
            ('h5', 'H5'),
        ],
        initial='h2',
        widget=forms.Select(attrs={
            "class": "form-select w-full",
            "placeholder": "Selecciona la etiqueta para dividir"
        })
    )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field('archivo'),
            Field('etiqueta')
        )

class TagsForm(forms.Form):
    archivo = forms.FileField(
        label="",
        required=True,
        widget=forms.ClearableFileInput(attrs={
            "class": "hidden",
            "accept": ".html"
        })
    )
    etiquetas = forms.CharField(
        label="",
        required=True,
        widget=forms.TextInput(attrs={
            "class": "form-control", 
            "placeholder": "Tags a eliminar, separados por espacios",
            "name": "etiquetas"  # Asegurarnos de que el nombre del campo sea único
        })
    )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field('archivo'),
            Field('etiquetas')
        )