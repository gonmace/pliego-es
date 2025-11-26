#!/bin/bash
# Script wrapper para ejecutar backup_data.py desde el contenedor Docker

echo "Copiando scripts al contenedor..."
echo ""

# Copiar los scripts al contenedor
docker compose cp backup_data.py pliego-django:/app/ 2>/dev/null || true
docker compose cp load_data.py pliego-django:/app/ 2>/dev/null || true

echo "Ejecutando backup_data.py en el contenedor..."
echo ""

# Ejecutar el script dentro del contenedor
docker compose exec pliego-django python backup_data.py

# Copiar el archivo de backup generado al host
echo ""
echo "Copiando archivo de backup al host..."
LATEST_BACKUP=$(docker compose exec -T pliego-django sh -c "ls -t backup_data_*.json 2>/dev/null | head -1" | tr -d '\r\n')

if [ -n "$LATEST_BACKUP" ]; then
    docker compose cp pliego-django:/app/"$LATEST_BACKUP" .
    echo "✓ Backup copiado: $LATEST_BACKUP"
else
    echo "⚠ No se encontró archivo de backup en el contenedor"
fi

