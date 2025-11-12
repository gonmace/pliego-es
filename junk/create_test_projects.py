import os
import sys
from pathlib import Path

import django
from django.utils.text import slugify

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.dev")
django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from django.utils import timezone  # noqa: E402

from main.models import Proyecto  # noqa: E402

User = get_user_model()

PROJECT_NAMES = [
    "Residencial Altamira",
    "Parque Industrial Norte",
    "Centro Comercial Aurora",
    "Hospital San Martín",
    "Colegio Horizonte",
    "Piscina Olímpica Municipal",
    "Biblioteca Central",
    "Estadio Metropolitano",
    "Complejo Deportivo Sur",
    "Museo de Arte Moderno",
    "Planta de Tratamiento",
    "Residencial Los Robles",
    "Torre Empresarial Andina",
    "Hotel Laguna Azul",
    "Centro Logístico Andino",
    "Universidad Tecnológica",
    "Terminal Terrestre",
    "Pasarela Peatonal Norte",
    "Parque Lineal del Río",
    "Condominio Vista Verde",
]

SOLICITANTES = [
    "Gobierno Municipal",
    "Constructora Andina",
    "Inversiones Atlas",
    "Fundación Futuro",
    "Ministerio de Infraestructura",
]

UBICACIONES = [
    "La Paz",
    "Santa Cruz",
    "Cochabamba",
    "Tarija",
    "Sucre",
    "Potosí",
]

DESCRIPCION_BASE = (
    "Proyecto generado para pruebas del sistema Pliego-ES. "
    "Incluye requisitos técnicos, cronograma y presupuesto estimado."
)


def main():
    users = list(User.objects.order_by("id"))
    if not users:
        print("No existen usuarios. Ejecuta create_test_users.py primero.")
        return

    created = 0
    for index, nombre in enumerate(PROJECT_NAMES):
        solicitante = SOLICITANTES[index % len(SOLICITANTES)]
        ubicacion = UBICACIONES[index % len(UBICACIONES)]
        usuario = users[index % len(users)]
        defaults = {
            "solicitante": solicitante,
            "ubicacion": ubicacion,
            "descripcion": f"{DESCRIPCION_BASE} (Código: {slugify(nombre)})",
            "creado_por": usuario,
            "publico": index % 2 == 0,
        }

        proyecto, was_created = Proyecto.objects.get_or_create(
            nombre=nombre,
            defaults=defaults,
        )

        if was_created:
            created += 1
            print(
                f"Creado proyecto '{proyecto.nombre}' asignado a "
                f"{proyecto.creado_por.get_full_name() or proyecto.creado_por.username}"
            )
        else:
            # Actualiza creador si está vacío
            if proyecto.creado_por is None:
                proyecto.creado_por = usuario
                for field, value in defaults.items():
                    if getattr(proyecto, field) in (None, ""):
                        setattr(proyecto, field, value)
                proyecto.save(update_fields=[
                    "creado_por", "solicitante", "ubicacion", "descripcion", "publico"
                ])
                print(f"Actualizado proyecto existente '{proyecto.nombre}' con datos de prueba")
            else:
                print(f"Proyecto ya existe: {proyecto.nombre}")

    print(f"Total de proyectos creados: {created}")


if __name__ == "__main__":
    main()
