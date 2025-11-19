#!/usr/bin/env python
"""
Script para cargar datos de backup en el orden correcto.
Orden: usuarios -> proyectos -> especificaciones
"""
import os
import sys
import django
import json
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.dev')
django.setup()

from django.core.management import call_command
from django.contrib.auth.models import User
from esp_web.models import Proyecto, Especificacion


def load_users_from_file(input_file):
    """Cargar usuarios desde el archivo JSON"""
    print("=" * 60)
    print("1. Cargando USUARIOS...")
    print("=" * 60)
    
    # Leer el archivo y filtrar solo usuarios
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    users_data = [item for item in data if item.get('model') == 'auth.user']
    
    if not users_data:
        print("   ⚠ No se encontraron usuarios en el archivo")
        return False
    
    print(f"   Usuarios encontrados en el archivo: {len(users_data)}")
    
    # Crear archivo temporal solo con usuarios
    temp_file = 'temp_users.json'
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(users_data, f, indent=2, ensure_ascii=False)
    
    try:
        # Cargar usuarios
        call_command('loaddata', temp_file, verbosity=1)
        print(f"   ✓ Usuarios cargados exitosamente")
        
        # Verificar
        user_count = User.objects.count()
        print(f"   Total de usuarios en la base de datos: {user_count}")
        return True
    except Exception as e:
        print(f"   ✗ Error al cargar usuarios: {e}")
        return False
    finally:
        # Limpiar archivo temporal
        if os.path.exists(temp_file):
            os.remove(temp_file)


def load_proyectos_from_file(input_file):
    """Cargar proyectos desde el archivo JSON"""
    print("\n" + "=" * 60)
    print("2. Cargando PROYECTOS...")
    print("=" * 60)
    
    # Leer el archivo y filtrar solo proyectos
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    proyectos_data = [item for item in data if item.get('model') == 'esp_web.proyecto']
    
    if not proyectos_data:
        print("   ⚠ No se encontraron proyectos en el archivo")
        return False
    
    print(f"   Proyectos encontrados en el archivo: {len(proyectos_data)}")
    
    # Crear archivo temporal solo con proyectos
    temp_file = 'temp_proyectos.json'
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(proyectos_data, f, indent=2, ensure_ascii=False)
    
    try:
        # Cargar proyectos
        call_command('loaddata', temp_file, verbosity=1)
        print(f"   ✓ Proyectos cargados exitosamente")
        
        # Verificar
        proyecto_count = Proyecto.objects.count()
        print(f"   Total de proyectos en la base de datos: {proyecto_count}")
        return True
    except Exception as e:
        print(f"   ✗ Error al cargar proyectos: {e}")
        return False
    finally:
        # Limpiar archivo temporal
        if os.path.exists(temp_file):
            os.remove(temp_file)


def load_especificaciones_from_file(input_file):
    """Cargar especificaciones e imágenes desde el archivo JSON"""
    print("\n" + "=" * 60)
    print("3. Cargando ESPECIFICACIONES...")
    print("=" * 60)
    
    # Leer el archivo y filtrar especificaciones e imágenes
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    especificaciones_data = [
        item for item in data 
        if item.get('model') in ['esp_web.especificacion', 'esp_web.especificacionimagen']
    ]
    
    if not especificaciones_data:
        print("   ⚠ No se encontraron especificaciones en el archivo")
        return False
    
    espec_count = len([item for item in especificaciones_data if item.get('model') == 'esp_web.especificacion'])
    img_count = len([item for item in especificaciones_data if item.get('model') == 'esp_web.especificacionimagen'])
    
    print(f"   Especificaciones encontradas: {espec_count}")
    print(f"   Imágenes encontradas: {img_count}")
    
    # Crear archivo temporal solo con especificaciones
    temp_file = 'temp_especificaciones.json'
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(especificaciones_data, f, indent=2, ensure_ascii=False)
    
    try:
        # Cargar especificaciones
        call_command('loaddata', temp_file, verbosity=1)
        print(f"   ✓ Especificaciones cargadas exitosamente")
        
        # Verificar
        especificacion_count = Especificacion.objects.count()
        print(f"   Total de especificaciones en la base de datos: {especificacion_count}")
        return True
    except Exception as e:
        print(f"   ✗ Error al cargar especificaciones: {e}")
        return False
    finally:
        # Limpiar archivo temporal
        if os.path.exists(temp_file):
            os.remove(temp_file)


def main():
    """Función principal"""
    print("\n" + "=" * 60)
    print("SCRIPT DE CARGA DE DATOS")
    print("=" * 60)
    
    # Verificar argumentos
    if len(sys.argv) < 2:
        print("\n✗ Error: Debes especificar el archivo de backup")
        print("\nUso:")
        print("  python load_data.py <archivo_backup.json>")
        print("\nEjemplo:")
        print("  python load_data.py backup_data_20241118_120000.json")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # Verificar que el archivo existe
    if not os.path.exists(input_file):
        print(f"\n✗ Error: El archivo '{input_file}' no existe")
        sys.exit(1)
    
    print(f"\nArchivo de entrada: {input_file}")
    print("\nCargando datos en orden:")
    print("  1. Usuarios")
    print("  2. Proyectos")
    print("  3. Especificaciones")
    
    # Confirmación
    print("\n⚠ ADVERTENCIA: Este proceso cargará datos en la base de datos actual.")
    print("   Asegúrate de que la base de datos esté lista.")
    
    try:
        response = input("\n¿Continuar? (s/N): ").strip().lower()
        if response not in ['s', 'si', 'sí', 'y', 'yes']:
            print("\nOperación cancelada")
            sys.exit(0)
    except KeyboardInterrupt:
        print("\n\nOperación cancelada")
        sys.exit(0)
    
    # Cargar datos en orden
    users_loaded = load_users_from_file(input_file)
    
    if not users_loaded:
        print("\n⚠ Advertencia: No se pudieron cargar usuarios.")
        print("   Continuando con proyectos...")
    
    proyectos_loaded = load_proyectos_from_file(input_file)
    
    if not proyectos_loaded:
        print("\n⚠ Advertencia: No se pudieron cargar proyectos.")
        print("   Continuando con especificaciones...")
    
    especificaciones_loaded = load_especificaciones_from_file(input_file)
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN DE LA CARGA")
    print("=" * 60)
    print(f"Usuarios cargados: {'✓' if users_loaded else '✗'}")
    print(f"Proyectos cargados: {'✓' if proyectos_loaded else '✗'}")
    print(f"Especificaciones cargadas: {'✓' if especificaciones_loaded else '✗'}")
    
    if users_loaded and proyectos_loaded and especificaciones_loaded:
        print("\n✓ Todos los datos fueron cargados exitosamente!")
    else:
        print("\n⚠ Algunos datos no pudieron ser cargados. Revisa los mensajes anteriores.")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Carga cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Error durante la carga: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

