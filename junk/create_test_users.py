import os
import sys
from pathlib import Path
import django

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.dev')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

USERS = [
    {"username": "alice", "first_name": "Alice", "last_name": "García", "email": "alice@example.com"},
    {"username": "bob", "first_name": "Bob", "last_name": "Martínez", "email": "bob@example.com"},
    {"username": "carla", "first_name": "Carla", "last_name": "Pérez", "email": "carla@example.com"},
    {"username": "diego", "first_name": "Diego", "last_name": "Suárez", "email": "diego@example.com"},
    {"username": "gmartinez", "first_name": "Gonzalo", "last_name": "Martínez", "email": "gmartinez@ip-40.com"},
]

def main():
    created = 0
    for data in USERS:
        if not User.objects.filter(username=data["username"]).exists():
            user = User.objects.create_user(**data, password="changeme123")
            created += 1
            print(f"Creado usuario: {user.username}")
        else:
            print(f"Usuario ya existe: {data['username']}")
    print(f"Total creados: {created}")

if __name__ == "__main__":
    main()
