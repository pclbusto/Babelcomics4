#!/bin/bash
# Script de instalación para soporte GPU (GTX 1070)
# Requiere Python 3.11

echo "=========================================="
echo "Instalación GPU Support para GTX 1070"
echo "=========================================="
echo ""

# Verificar Python 3.11
if ! command -v python3.11 &> /dev/null; then
    echo "❌ Python 3.11 no encontrado"
    echo "   Instalalo con: sudo pacman -S python311"
    exit 1
fi

echo "✓ Python 3.11 encontrado"
echo ""

# Crear venv con Python 3.11 si no existe
if [ ! -d ".venv" ]; then
    echo "Creando virtual environment con Python 3.11..."
    python3.11 -m venv .venv
    echo "✓ Virtual environment creado"
else
    echo "✓ Virtual environment ya existe"
fi

echo ""
echo "Instalando dependencias..."
echo ""

# Instalar PyTorch con CUDA 11.7 (compatible con GTX 1070)
echo "1. Instalando PyTorch 1.13.1 + CUDA 11.7..."
./.venv/bin/pip install -q torch==1.13.1+cu117 --extra-index-url https://download.pytorch.org/whl/cu117

# Instalar transformers compatible
echo "2. Instalando Transformers 4.25.1..."
./.venv/bin/pip install -q transformers==4.25.1

# Instalar NumPy compatible
echo "3. Instalando NumPy < 2..."
./.venv/bin/pip install -q "numpy<2"

# Instalar otras dependencias
echo "4. Instalando dependencias adicionales..."
./.venv/bin/pip install -q pillow sqlalchemy requests rarfile py7zr

# Instalar PyGObject para GTK4
echo "5. Instalando PyGObject (requiere dependencias del sistema)..."
if ./.venv/bin/pip install -q PyGObject; then
    echo "   ✓ PyGObject instalado"
else
    echo "   ⚠ PyGObject falló (instala dependencias del sistema primero):"
    echo "      sudo pacman -S python-gobject gtk4 libadwaita gobject-introspection"
fi

echo ""
echo "Verificando instalación..."
echo ""

# Verificar PyTorch y CUDA
./.venv/bin/python -c "
import torch
print(f'✓ PyTorch: {torch.__version__}')
print(f'✓ CUDA disponible: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'✓ GPU: {torch.cuda.get_device_name(0)}')
else:
    print('❌ CUDA no disponible')
"

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ INSTALACIÓN COMPLETADA"
    echo "=========================================="
    echo ""
    echo "Actualizar esquema de base de datos:"
    echo "  ./.venv/bin/python -c \"from sqlalchemy import create_engine, text; engine = create_engine('sqlite:///data/babelcomics.db'); conn = engine.connect(); conn.execute(text('ALTER TABLE comicbooks_info_covers ADD COLUMN embedding TEXT')); conn.execute(text('ALTER TABLE comicbooks ADD COLUMN embedding TEXT')); conn.close()\""
    echo ""
    echo "Probar sistema:"
    echo "  ./.venv/bin/python test_embeddings.py"
    echo ""
    echo "Generar embeddings:"
    echo "  ./.venv/bin/python generate_cover_embeddings.py"
    echo ""
else
    echo ""
    echo "❌ ERROR en la instalación"
    exit 1
fi
