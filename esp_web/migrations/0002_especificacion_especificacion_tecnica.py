# Generated manually

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('esp_web', '0001_initial'),
        ('n8n', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='especificacion',
            name='especificacion_tecnica',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='especificaciones',
                to='n8n.especificaciontecnica',
                verbose_name='Especificación Técnica (n8n)'
            ),
        ),
    ]

