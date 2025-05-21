from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field
from multiupload_plus.fields import MultiFileField

CATEGORIAS = [
    ('muros', 'Muros'),
    ('pisos', 'Pisos'),
    ('diseno', 'Diseno'),
    ('trabajos_previos', 'Trabajos previos'),
    ('movimiento_tierras', 'Movimiento de tierras'),
    ('estructuras', 'Estructuras'),
    ('revoques', 'Revoques'),
    ('revestimientos', 'Revestimientos'),
    ('materiales_de_construccion', 'Materiales de construcción'),
    ('mesones', 'Mesones'),
    ('cielos', 'Cielos'),
    ('carpinteria_de_madera', 'Carpintería de madera'),
    ('carpinteria_en_melamina', 'Carpintería en melamina'),
    ('aceros_estructuras_metalicas', 'Aceros y estructuras metalicas'),
    ('cubiertas', 'Cubiertas'),
    ('impermeabilizaciones', 'Impermeabilizaciones'),
    ('instalaciones_electricas', 'Instalaciones eléctricas'),
    ('instalaciones_sanitarias', 'Instalaciones sanitarias'),
    ('instalaciones_de_gas', 'Instalaciones de gas'),
    ('instalaciones_de_aire_acondicionado', 'Instalaciones de aire acondicionado'),
    ('limpieza', 'Limpieza'),
    ('albañileria', 'Albañilería'),
    ('mobiliario', 'Mobiliario'),
    ('transporte', 'Transporte'),
    ('asistencia_en_otras_ciudades', 'Asistencia en otras ciudades'),
    ('carpinteria_vidrio_aluminio', 'Carpintería de vidrio y aluminio'),
    ('demoliciones', 'Demoliciones'),
    ('otros', 'Otros')
]

class EmbeddingsForm(forms.Form):
    archivos_md = MultiFileField(
        min_num=1,
        max_num=20,
        max_file_size=1024*1024*5,  # 5MB
        label="Archivos Markdown"
    )
    categoria = forms.ChoiceField(
        choices=sorted(CATEGORIAS, key=lambda x: x[1]),
        label="Categoría"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('archivos_md', css_class='!file-input !file-input-primary !file-input-lg !w-full'),
            Field('categoria', css_class='!select !select-primary !select-lg !w-full'),
            Submit('submit', 'Procesar Archivos', css_class='!btn !btn-primary !btn-lg !w-full')
        ) 