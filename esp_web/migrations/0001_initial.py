# Generated manually - tables already exist from main app

from django.db import migrations


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        # Las tablas ya existen en la base de datos desde la app 'main'
        # Esta migración solo marca que los modelos están bajo 'esp_web'
        # Las tablas físicas siguen siendo main_proyecto, main_especificacion, etc.
        # debido a db_table en los modelos
    ]

