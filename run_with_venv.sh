#!/bin/bash
# Script helper para ejecutar comandos Python con el virtual environment

# Activar el venv
source venv/bin/activate

# Ejecutar el comando pasado como parámetro
"$@"

# Desactivar venv
deactivate
