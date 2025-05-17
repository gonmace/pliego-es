from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field
from multiupload_plus.fields import MultiFileField

class GenericoForm(forms.Form):
    titulo = forms.CharField(max_length=255)
    archivos_md = MultiFileField(min_num=1, max_num=4, max_file_size=1024*1024*5)
    aclaraciones = forms.CharField(widget=forms.Textarea, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('titulo', css_class='!text-black'),
            Field('archivos_md', css_class='!file-input !file-input-primary !file-input-lg !w-full'),
            Field('aclaraciones', css_class='!h-32 !text-black'),
            Submit('submit', 'Generar Documento', css_class='!btn !btn-primary !btn-lg !w-full')
        )