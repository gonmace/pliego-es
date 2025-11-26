#!/bin/bash
# Script wrapper para ejecutar load_data.py desde el contenedor Docker

if [ $# -lt 1 ]; then
    echo "Uso: $0 <archivo_backup.json>"
    echo ""
    echo "Ejemplo:"
    echo "  $0 backup_data_20251118_202433.json"
    exit 1
fi

BACKUP_FILE="$1"

# Verificar que el archivo existe
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: El archivo '$BACKUP_FILE' no existe"
    exit 1
fi

echo "Copiando scripts y archivo de backup al contenedor..."
echo ""

# Copiar los scripts al contenedor si no existen
docker compose cp backup_data.py pliego-django:/app/ 2>/dev/null || true
docker compose cp load_data.py pliego-django:/app/ 2>/dev/null || true

# Copiar el archivo de backup al contenedor
BACKUP_FILENAME=$(basename "$BACKUP_FILE")
docker compose cp "$BACKUP_FILE" pliego-django:/app/"$BACKUP_FILENAME"

echo "Ejecutando load_data.py en el contenedor..."
echo ""

# Ejecutar el script dentro del contenedor (con --yes para modo no interactivo)
docker compose exec -T pliego-django python load_data.py "$BACKUP_FILENAME" --yes

# Limpiar archivo temporal del contenedor (opcional)
# docker compose exec pliego-django rm -f "/app/$BACKUP_FILENAME"

