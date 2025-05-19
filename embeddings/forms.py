from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field
from multiupload_plus.fields import MultiFileField

class EmbeddingsForm(forms.Form):
    archivos_md = MultiFileField(
        min_num=1,
        max_num=20,
        max_file_size=1024*1024*5,  # 5MB
        label="Archivos Markdown"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('archivos_md', css_class='!file-input !file-input-primary !file-input-lg !w-full'),
            Submit('submit', 'Procesar Archivos', css_class='!btn !btn-primary !btn-lg !w-full')
        ) 