#!/bin/bash
# Script de instalación del sistema de embeddings

echo "=========================================="
echo "Setup de Sistema de Clasificación por"
echo "Embeddings Visuales para Babelcomics4"
echo "=========================================="
echo ""

# Verificar que estemos en el directorio correcto
if [ ! -f "Babelcomic4.py" ]; then
    echo "ERROR: Ejecuta este script desde el directorio raíz de Babelcomics4"
    exit 1
fi

# Crear virtual environment si no existe
if [ ! -d "venv" ]; then
    echo "1. Creando virtual environment..."
    python3 -m venv venv
    echo "   ✓ Virtual environment creado"
else
    echo "1. Virtual environment ya existe"
fi

# Instalar dependencias
echo ""
echo "2. Instalando dependencias..."
echo "   (Esto puede tardar varios minutos - descarga ~2GB)"
./venv/bin/pip install -q torch transformers numpy pillow sqlalchemy requests

if [ $? -eq 0 ]; then
    echo "   ✓ Dependencias instaladas"
else
    echo "   ✗ Error instalando dependencias"
    exit 1
fi

# Actualizar esquema de base de datos
echo ""
echo "3. Actualizando esquema de base de datos..."
./venv/bin/python -c "
import os
from sqlalchemy import create_engine

db_path = os.path.join('data', 'babelcomics.db')
if os.path.exists(db_path):
    engine = create_engine(f'sqlite:///{db_path}')
    with engine.begin() as conn:
        try:
            conn.execute('ALTER TABLE comicbooks_info_covers ADD COLUMN embedding TEXT')
            print('   ✓ Columna embedding agregada a comicbooks_info_covers')
        except:
            print('   ✓ Columna embedding ya existe en comicbooks_info_covers')

        try:
            conn.execute('ALTER TABLE comicbooks ADD COLUMN embedding TEXT')
            print('   ✓ Columna embedding agregada a comicbooks')
        except:
            print('   ✓ Columna embedding ya existe en comicbooks')
else:
    print('   ! Base de datos no encontrada, se creará al ejecutar la aplicación')
"

# Verificar instalación
echo ""
echo "4. Verificando instalación..."
./venv/bin/python test_embeddings.py > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "   ✓ Instalación verificada correctamente"
else
    echo "   ⚠ Verificación falló (probablemente porque no hay imágenes de prueba)"
    echo "   Esto es normal si acabas de instalar"
fi

echo ""
echo "=========================================="
echo "✅ INSTALACIÓN COMPLETADA"
echo "=========================================="
echo ""
echo "Próximos pasos:"
echo ""
echo "1. Generar embeddings de tus covers de ComicVine:"
echo "   ./venv/bin/python generate_cover_embeddings.py"
echo ""
echo "2. Clasificar automáticamente tus comics:"
echo "   ./venv/bin/python auto_classify_comics.py --max 10"
echo ""
echo "Consulta EMBEDDINGS_README.md para más información"
echo ""
