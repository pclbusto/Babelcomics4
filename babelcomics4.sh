#!/bin/bash
# Script de inicio para Babelcomics4

cd "/home/pedro/Documents/Python Projects/Babelcomics4"

# Activar entorno virtual si existe
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ Entorno virtual activado"
fi

# Verificar dependencias básicas
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 no encontrado"
    exit 1
fi

# Ejecutar aplicación
echo "🚀 Iniciando Babelcomics4..."
python Babelcomic4.py

# Desactivar entorno virtual
if [ -d ".venv" ]; then
    deactivate
fi
