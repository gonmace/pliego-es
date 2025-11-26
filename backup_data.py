#!/usr/bin/env python
"""
Script para hacer backup de usuarios, proyectos y especificaciones.
Orden: usuarios -> proyectos -> especificaciones
"""
import os
import sys
import django
import json
import tempfile
from datetime import datetime
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.dev')
django.setup()

from django.core.management import call_command
from django.contrib.auth.models import User
from esp_web.models import Proyecto, Especificacion


def backup_users(output_file):
    """Hacer backup de usuarios"""
    print("=" * 60)
    print("1. Haciendo backup de USUARIOS...")
    print("=" * 60)
    
    user_count = User.objects.count()
    print(f"   Total de usuarios encontrados: {user_count}")
    
    if user_count == 0:
        print("   ⚠ No hay usuarios para respaldar")
        return False
    
    # Hacer backup solo de usuarios
    call_command(
        'dumpdata',
        'auth.user',
        '--natural-foreign',
        '--natural-primary',
        '--indent', '2',
        '--output', output_file,
        verbosity=1
    )
    
    print(f"   ✓ Backup de usuarios guardado en: {output_file}")
    return True


def backup_proyectos(output_file):
    """Hacer backup de proyectos"""
    print("\n" + "=" * 60)
    print("2. Haciendo backup de PROYECTOS...")
    print("=" * 60)
    
    proyecto_count = Proyecto.objects.count()
    print(f"   Total de proyectos encontrados: {proyecto_count}")
    
    if proyecto_count == 0:
        print("   ⚠ No hay proyectos para respaldar")
        return False
    
    # Crear archivo temporal para proyectos
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
        temp_path = temp_file.name
    
    try:
        # Hacer backup de proyectos en archivo temporal
        call_command(
            'dumpdata',
            'esp_web.proyecto',
            '--natural-foreign',
            '--natural-primary',
            '--indent', '2',
            '--output', temp_path,
            verbosity=0
        )
        
        # Leer datos existentes y nuevos, combinarlos
        with open(output_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        
        with open(temp_path, 'r', encoding='utf-8') as f:
            new_data = json.load(f)
        
        # Combinar arrays
        combined_data = existing_data + new_data
        
        # Escribir archivo combinado
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, indent=2, ensure_ascii=False)
        
        print(f"   ✓ Backup de proyectos agregado a: {output_file}")
        return True
    finally:
        # Limpiar archivo temporal
        if os.path.exists(temp_path):
            os.remove(temp_path)


def backup_especificaciones(output_file):
    """Hacer backup de especificaciones e imágenes"""
    print("\n" + "=" * 60)
    print("3. Haciendo backup de ESPECIFICACIONES...")
    print("=" * 60)
    
    especificacion_count = Especificacion.objects.count()
    print(f"   Total de especificaciones encontradas: {especificacion_count}")
    
    if especificacion_count == 0:
        print("   ⚠ No hay especificaciones para respaldar")
        return False
    
    # Crear archivo temporal para especificaciones
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
        temp_path = temp_file.name
    
    try:
        # Hacer backup de especificaciones e imágenes en archivo temporal
        call_command(
            'dumpdata',
            'esp_web.especificacion',
            'esp_web.especificacionimagen',
            '--natural-foreign',
            '--natural-primary',
            '--indent', '2',
            '--output', temp_path,
            verbosity=0
        )
        
        # Leer datos existentes y nuevos, combinarlos
        with open(output_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        
        with open(temp_path, 'r', encoding='utf-8') as f:
            new_data = json.load(f)
        
        # Combinar arrays
        combined_data = existing_data + new_data
        
        # Escribir archivo combinado
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, indent=2, ensure_ascii=False)
        
        print(f"   ✓ Backup de especificaciones agregado a: {output_file}")
        return True
    finally:
        # Limpiar archivo temporal
        if os.path.exists(temp_path):
            os.remove(temp_path)


def main():
    """Función principal"""
    print("\n" + "=" * 60)
    print("SCRIPT DE BACKUP DE DATOS")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Crear nombre de archivo con timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'backup_data_{timestamp}.json'
    
    print(f"\nArchivo de salida: {output_file}")
    print("\nIniciando backup en orden:")
    print("  1. Usuarios")
    print("  2. Proyectos")
    print("  3. Especificaciones")
    
    # Si el archivo existe, eliminarlo primero para empezar limpio
    if os.path.exists(output_file):
        os.remove(output_file)
    
    # Hacer backups en orden
    users_backed = backup_users(output_file)
    proyectos_backed = backup_proyectos(output_file)
    especificaciones_backed = backup_especificaciones(output_file)
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN DEL BACKUP")
    print("=" * 60)
    print(f"Archivo generado: {output_file}")
    print(f"Usuarios respaldados: {'✓' if users_backed else '✗'}")
    print(f"Proyectos respaldados: {'✓' if proyectos_backed else '✗'}")
    print(f"Especificaciones respaldadas: {'✓' if especificaciones_backed else '✗'}")
    
    if os.path.exists(output_file):
        file_size = os.path.getsize(output_file)
        print(f"Tamaño del archivo: {file_size:,} bytes ({file_size / 1024:.2f} KB)")
    
    print("\n✓ Backup completado exitosamente!")
    print(f"\nPara restaurar los datos, ejecuta:")
    print(f"  python load_data.py {output_file}")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Backup cancelado por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Error durante el backup: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

