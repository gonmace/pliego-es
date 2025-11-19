# Scripts de Backup y Restauración de Datos

Este directorio contiene scripts para hacer backup y restaurar datos importantes de la aplicación en el orden correcto.

## Scripts Disponibles

### Opción A: Ejecutar desde el Host (Recomendado)

Si tienes acceso directo a la base de datos desde el host, puedes ejecutar los scripts directamente.

### Opción B: Ejecutar desde Docker

Si estás usando Docker, usa los scripts wrapper que copian los archivos al contenedor automáticamente.

---

### 1. `backup_data.py` - Script de Backup

Crea un backup de usuarios, proyectos y especificaciones en el orden correcto.

**Uso (desde el host):**
```bash
source .venv/bin/activate
python backup_data.py
```

**Uso (desde Docker):**
```bash
./backup_data_docker.sh
# O manualmente:
docker compose cp backup_data.py pliego-django:/app/
docker compose exec pliego-django python backup_data.py
docker compose cp pliego-django:/app/backup_data_*.json .
```

**Qué hace:**
1. Hace backup de **usuarios** (`auth.user`)
2. Hace backup de **proyectos** (`esp_web.proyecto`)
3. Hace backup de **especificaciones** e imágenes (`esp_web.especificacion`, `esp_web.especificacionimagen`)

**Salida:**
- Crea un archivo JSON con formato: `backup_data_YYYYMMDD_HHMMSS.json`
- El archivo contiene todos los datos en el orden correcto

---

### 2. `load_data.py` - Script de Restauración

Carga datos desde un archivo de backup en el orden correcto.

**Uso (desde el host):**
```bash
source .venv/bin/activate
python load_data.py <archivo_backup.json>
```

**Ejemplo:**
```bash
python load_data.py backup_data_20251118_202433.json
```

**Uso (desde Docker):**
```bash
./load_data_docker.sh backup_data_20251118_202433.json
# O manualmente:
docker compose cp load_data.py pliego-django:/app/
docker compose cp backup_data_20251118_202433.json pliego-django:/app/
docker compose exec pliego-django python load_data.py backup_data_20251118_202433.json
```

**Qué hace:**
1. Carga **usuarios** primero (necesarios para proyectos)
2. Carga **proyectos** después (necesarios para especificaciones)
3. Carga **especificaciones** e imágenes al final

**Importante:**
- El script pedirá confirmación antes de cargar los datos
- Asegúrate de que la base de datos esté lista y vacía (o que no haya conflictos)
- Los datos se cargarán en el orden correcto respetando las dependencias

---

## Orden de Dependencias

Los datos deben cargarse en este orden debido a las relaciones:

```
Usuarios (auth.user)
    ↓
Proyectos (esp_web.proyecto) - depende de usuarios (creado_por)
    ↓
Especificaciones (esp_web.especificacion) - depende de proyectos
    ↓
Imágenes de Especificaciones (esp_web.especificacionimagen) - depende de especificaciones
```

---

## Ejemplo de Flujo Completo

### 1. Hacer Backup
```bash
# Activar entorno virtual
source .venv/bin/activate

# Ejecutar backup
python backup_data.py
```

Salida esperada:
```
✓ Backup completado exitosamente!
Archivo generado: backup_data_20251118_202433.json
```

### 2. Restaurar Datos
```bash
# Activar entorno virtual
source .venv/bin/activate

# Ejecutar restauración
python load_data.py backup_data_20251118_202433.json
```

El script pedirá confirmación antes de proceder.

---

## Notas Importantes

- ⚠️ **Los backups NO incluyen archivos multimedia** (imágenes, PDFs, etc.). Solo se respaldan las referencias en la base de datos.
- ⚠️ **Los backups NO incluyen sesiones** ni datos temporales.
- ✅ Los backups incluyen todas las relaciones necesarias usando `--natural-foreign` y `--natural-primary`.
- ✅ Los scripts manejan errores y muestran mensajes informativos.

---

## Solución de Problemas

### Error: "No se encontraron usuarios/proyectos/especificaciones"
- Verifica que haya datos en la base de datos antes de hacer backup
- Verifica que el archivo de backup contenga los datos esperados

### Error al cargar datos
- Verifica que la base de datos esté vacía o que no haya conflictos de IDs
- Verifica que todas las migraciones estén aplicadas: `python manage.py migrate`
- Revisa los mensajes de error para más detalles

### Los datos no se cargan en el orden correcto
- Los scripts están diseñados para cargar en el orden correcto automáticamente
- Si hay problemas, verifica que el archivo JSON esté bien formateado

---

## Archivos Relacionados

- `backup_data.py` - Script de backup (Python)
- `load_data.py` - Script de restauración (Python)
- `backup_data_docker.sh` - Wrapper para ejecutar backup desde Docker
- `load_data_docker.sh` - Wrapper para ejecutar carga desde Docker
- `fix_migration.py` - Script de diagnóstico de migraciones (creado anteriormente)

---

## Solución de Problemas con Docker

### Error: "can't open file '/app/load_data.py'"

Los scripts no están en el contenedor porque fueron creados después de construir la imagen. Soluciones:

**Opción 1: Usar los scripts wrapper (Recomendado)**
```bash
./load_data_docker.sh backup_data_20251118_202433.json
```

**Opción 2: Copiar manualmente los scripts**
```bash
docker compose cp backup_data.py pliego-django:/app/
docker compose cp load_data.py pliego-django:/app/
docker compose exec pliego-django python load_data.py backup_data_20251118_202433.json
```

**Opción 3: Reconstruir la imagen Docker**
```bash
docker compose build pliego-django
docker compose up -d pliego-django
```

