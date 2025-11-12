import os
import sys
from pathlib import Path

import django
from django.utils import timezone
from django.utils.text import slugify

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.dev")
django.setup()

from django.core.files.base import ContentFile  # noqa: E402
from main.models import Proyecto, Especificacion  # noqa: E402

MAX_SPECS = 10


def build_markdown(project, spec_number):
    titulo = f"Especificación {spec_number} - {project.nombre}"
    contenido = (
        f"# Especificación {spec_number}\n\n"
        f"Proyecto: **{project.nombre}**\n\n"
        "## Resumen\n\n"
        "Este contenido es generado automáticamente para pruebas.\n\n"
        "## Alcance\n\n"
        "- Objetivo principal del proyecto\n"
        "- Requerimientos clave\n"
        "- Consideraciones técnicas\n\n"
        f"Generado en: {timezone.now():%Y-%m-%d %H:%M}.\n"
    )
    return titulo, contenido


def create_specs_for_project(project, count):
    existing_titles = set(
        Especificacion.objects.filter(proyecto=project).values_list("titulo", flat=True)
    )
    created = 0
    for idx in range(1, count + 1):
        titulo, contenido = build_markdown(project, idx)
        if titulo in existing_titles:
            continue

        especificacion = Especificacion(
            proyecto=project,
            titulo=titulo,
            contenido=contenido,
        )
        slug = slugify(titulo) or f"especificacion-{idx}"
        filename = f"{slug}-{timezone.now():%Y%m%d%H%M%S}.md"
        especificacion.archivo.save(filename, ContentFile(contenido), save=False)
        especificacion.save()
        created += 1
        print(f"  - Creada especificación '{titulo}'")
    return created


def main():
    projects = list(Proyecto.objects.filter(activo=True).order_by("id"))
    if not projects:
        print("No hay proyectos activos. Ejecuta primero create_test_projects.py.")
        return

    total_created = 0
    for index, project in enumerate(projects):
        specs_to_create = max(MAX_SPECS - index, 1)
        print(f"Procesando proyecto '{project.nombre}' (crear {specs_to_create})")
        created = create_specs_for_project(project, specs_to_create)
        total_created += created
        if created == 0:
            print("  * No se crearon nuevas especificaciones (ya existían).")

    print(f"Especificaciones creadas en total: {total_created}")


if __name__ == "__main__":
    main()
