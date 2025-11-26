#!/usr/bin/env python
"""
Script to fix the migration issue where ubi_web_ubicacion table already exists.
Run this script to check and fix the migration state.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.dev')
django.setup()

from django.db import connection
from django.core.management import call_command

def check_table_exists(table_name):
    """Check if the table exists in the database"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            );
        """, [table_name])
        exists = cursor.fetchone()[0]
        return exists

def check_migration_applied(app_name, migration_name):
    """Check if the migration is recorded in django_migrations"""
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM django_migrations 
                WHERE app = %s 
                AND name = %s
            );
        """, [app_name, migration_name])
        exists = cursor.fetchone()[0]
        return exists

def list_all_tables():
    """List all tables in the database"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        tables = [row[0] for row in cursor.fetchall()]
        return tables

def main():
    print("Checking migration state...")
    print("=" * 60)
    
    # Check ubi_web_ubicacion
    print("\n1. Checking ubi_web_ubicacion:")
    table_exists = check_table_exists('ubi_web_ubicacion')
    migration_applied = check_migration_applied('ubi_web', '0001_initial')
    print(f"   Table exists: {table_exists}")
    print(f"   Migration applied: {migration_applied}")
    
    # Check main_proyecto
    print("\n2. Checking main_proyecto:")
    proyecto_table_exists = check_table_exists('main_proyecto')
    proyecto_migration_applied = check_migration_applied('esp_web', '0001_initial')
    print(f"   Table exists: {proyecto_table_exists}")
    print(f"   Migration applied: {proyecto_migration_applied}")
    
    # List all tables
    print("\n3. All tables in database:")
    all_tables = list_all_tables()
    main_tables = [t for t in all_tables if 'main_' in t or 'ubi_' in t]
    for table in main_tables:
        print(f"   - {table}")
    
    print("\n" + "=" * 60)
    print("\nDiagnosis:")
    
    if not proyecto_table_exists:
        print("\n⚠ PROBLEM: main_proyecto table does NOT exist!")
        print("Solution: Run migrations to create the table:")
        print("  python manage.py migrate esp_web")
    elif proyecto_table_exists and not proyecto_migration_applied:
        print("\n⚠ Table exists but migration is not recorded.")
        print("Solution: Fake the migration:")
        print("  python manage.py migrate --fake esp_web 0001_initial")
    elif proyecto_table_exists and proyecto_migration_applied:
        print("\n✓ Table and migration both exist.")
        print("If you're still getting errors, check:")
        print("  - Database connection settings")
        print("  - Schema permissions")
        print("  - Try: python manage.py migrate --run-syncdb")

if __name__ == '__main__':
    main()

