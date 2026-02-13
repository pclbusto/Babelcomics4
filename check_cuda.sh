#!/bin/bash
# Script para verificar la versión de CUDA instalada

echo "=========================================="
echo "  Verificación de CUDA para Babelcomics4"
echo "=========================================="
echo ""

# Verificar nvidia-smi
if command -v nvidia-smi &> /dev/null; then
    echo "✓ nvidia-smi encontrado"
    echo ""
    echo "Información de la GPU:"
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
    echo ""

    # Obtener versión de CUDA
    echo "Versión de CUDA disponible:"
    nvidia-smi | grep -i "cuda version" || echo "  No se pudo detectar automáticamente"

    # Verificar nvcc
    if command -v nvcc &> /dev/null; then
        echo ""
        echo "CUDA Toolkit instalado:"
        nvcc --version | grep "release"
    else
        echo ""
        echo "⚠ nvcc no encontrado (CUDA Toolkit no instalado)"
        echo "  Esto está bien si solo necesitas el driver"
    fi

    echo ""
    echo "=========================================="
    echo "Recomendaciones para tu GPU:"
    echo "=========================================="
    echo ""

    # Detectar versión y recomendar
    cuda_version=$(nvidia-smi | grep -oP "CUDA Version: \K[0-9]+\.[0-9]+")
    if [ ! -z "$cuda_version" ]; then
        major_version=$(echo $cuda_version | cut -d. -f1)

        echo "Tu driver soporta CUDA: $cuda_version"
        echo ""

        if [ "$major_version" -ge 12 ]; then
            echo "👉 Recomendación: Opción 3 (CUDA 12.1)"
            echo "   .venv/bin/pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121"
        elif [ "$major_version" -eq 11 ]; then
            echo "👉 Recomendación: Opción 2 (CUDA 11.8)"
            echo "   .venv/bin/pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118"
        else
            echo "👉 Recomendación: Opción 1 (CPU)"
            echo "   Tu versión de CUDA es antigua, mejor usar CPU"
        fi
    fi

else
    echo "❌ nvidia-smi no encontrado"
    echo ""
    echo "Posibles razones:"
    echo "  1. No tienes GPU NVIDIA"
    echo "  2. Los drivers NVIDIA no están instalados"
    echo "  3. La GPU no está siendo reconocida"
    echo ""
    echo "👉 Recomendación: Opción 1 (CPU)"
    echo ""
    echo "Para instalar drivers NVIDIA:"
    echo "  Arch Linux: sudo pacman -S nvidia nvidia-utils"
    echo "  Ubuntu:     sudo apt install nvidia-driver-XXX"
    echo "  Fedora:     sudo dnf install akmod-nvidia"
fi

echo ""
echo "=========================================="
echo ""
echo "Ejecutá la instalación con:"
echo "  python3 install.py --embeddings"
echo ""
