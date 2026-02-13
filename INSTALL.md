# Instalación de Babelcomics4

Guía de instalación completa para Babelcomics4, el gestor de comics digital con GTK4.

## Requisitos del Sistema

### Dependencias del Sistema (Requeridas)

Antes de instalar, asegúrate de tener instaladas las siguientes dependencias del sistema:

#### Arch Linux / Manjaro
```bash
sudo pacman -S python gtk4 libadwaita gobject-introspection python-gobject
```

#### Ubuntu / Debian
```bash
sudo apt install python3 python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1 libgirepository1.0-dev
```

#### Fedora
```bash
sudo dnf install python3 python3-gobject gtk4-devel libadwaita-devel gobject-introspection-devel
```

### Herramientas de Extracción (Opcionales pero Recomendadas)

Para soporte completo de formatos de comics:

```bash
# Arch Linux
sudo pacman -S unrar p7zip

# Ubuntu/Debian
sudo apt install unrar-free p7zip-full

# Fedora
sudo dnf install unrar p7zip
```

## Instalación

### Método 1: Instalador Automático (Recomendado)

El instalador automático configura todo por ti: entorno virtual, dependencias, iconos y entrada en el menú.

```bash
# 1. Clonar o descargar el repositorio
cd "/home/pedro/Documents/Python Projects/Babelcomics4"

# 2. Ejecutar el instalador
python3 install.py
```

El instalador:
- ✅ Verifica dependencias del sistema
- ✅ Crea entorno virtual en `.venv/`
- ✅ Instala todas las dependencias Python necesarias
- ✅ Configura la base de datos
- ✅ Actualiza el script de lanzamiento
- ✅ Instala iconos en el sistema
- ✅ Crea entrada en el menú de aplicaciones

### Método 2: Instalación Manual

Si preferís tener más control:

```bash
# 1. Crear entorno virtual
python3 -m venv .venv

# 2. Activar entorno virtual
source .venv/bin/activate

# 3. Instalar dependencias core
pip install --upgrade pip
pip install SQLAlchemy>=2.0.0 requests>=2.31.0 Pillow>=10.0.0
pip install rarfile>=4.0 py7zr>=0.20.0 PyGObject>=3.42.0 numpy

# 4. Ejecutar setup inicial
python setup.py

# 5. Ejecutar la aplicación
python Babelcomic4.py
```

## Ejecutar la Aplicación

Después de la instalación, podés ejecutar Babelcomics4 de varias formas:

### 1. Desde el Menú de Aplicaciones
Buscá "Babelcomics4" en el menú de aplicaciones de tu escritorio.

### 2. Script de Lanzamiento
```bash
./babelcomics4.sh
```

### 3. Directamente con Python (requiere venv activado)
```bash
.venv/bin/python Babelcomic4.py
```

## Funciones Opcionales

### Clasificación Automática con IA (Embeddings)

Las funciones de clasificación automática por IA requieren PyTorch y Transformers (~2GB de descarga). Estas dependencias son opcionales.

#### Método 1: Durante la Instalación Inicial (Recomendado)

El instalador te preguntará si querés instalar embeddings:

```bash
python3 install.py
# Responde 'si' cuando te pregunte por embeddings
```

#### Método 2: Después de la Instalación

Si ya instalaste Babelcomics4 y ahora querés agregar IA:

**Opción A - Instalador Python (Recomendado):**
```bash
python3 install.py --embeddings
```

**Opción B - Script Bash (solo CPU):**
```bash
./setup_embeddings.sh
```

Ambos métodos:
- Te preguntarán qué versión de PyTorch instalar (CPU, CUDA 11.8, o CUDA 12.1)
- Instalarán Transformers
- Actualizarán el esquema de la base de datos
- Verificarán la instalación

**¿No estás seguro qué versión de CUDA necesitas?**
Ejecutá este script para verificar:
```bash
./check_cuda.sh
```
Te mostrará tu GPU, versión de CUDA disponible, y te recomendará qué opción elegir.

#### Instalación Manual de PyTorch

Si preferís control total:

**Para CPU:**
```bash
.venv/bin/pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
.venv/bin/pip install transformers
```

**Para GPU NVIDIA con CUDA 11.8 (GTX 1070, RTX 2000/3000/4000):**
```bash
.venv/bin/pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
.venv/bin/pip install transformers
```

**Para GPU NVIDIA con CUDA 12.1+ (RTX 4000+):**
```bash
.venv/bin/pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
.venv/bin/pip install transformers
```

Si no instalás estas dependencias, la aplicación funciona perfectamente pero las opciones de IA estarán deshabilitadas.

## Verificación de la Instalación

Para verificar que todo está instalado correctamente:

```bash
# 1. Activar venv
source .venv/bin/activate

# 2. Verificar módulos principales
python -c "import gi; gi.require_version('Gtk', '4.0'); print('GTK4: OK')"
python -c "import sqlalchemy; print(f'SQLAlchemy {sqlalchemy.__version__}: OK')"
python -c "from PIL import Image; print('Pillow: OK')"

# 3. Verificar soporte de formatos
python -c "import rarfile; print('CBR: OK')"
python -c "import py7zr; print('CB7: OK')"

# 4. Verificar funciones de IA (opcional)
python -c "import torch; print(f'PyTorch {torch.__version__}: OK')" 2>/dev/null || echo "IA: No instalada (opcional)"
```

## Solución de Problemas

### Error: "No module named 'gi'"

Instalá PyGObject y las dependencias del sistema:
```bash
# Arch
sudo pacman -S gobject-introspection python-gobject

# Debian/Ubuntu
sudo apt install libgirepository1.0-dev python3-gi
```

Luego reinstalá PyGObject en el venv:
```bash
.venv/bin/pip install PyGObject
```

### Error: "No module named 'sqlalchemy'"

Asegúrate de estar usando el Python del venv:
```bash
# Mal:
python Babelcomic4.py

# Bien:
.venv/bin/python Babelcomic4.py
# O mejor:
./babelcomics4.sh
```

### La aplicación no aparece en el menú

Actualizá las bases de datos del sistema:
```bash
update-desktop-database ~/.local/share/applications
gtk-update-icon-cache ~/.local/share/icons/hicolor
```

### Iconos no se muestran correctamente

Reinstalá los iconos ejecutando de nuevo el instalador:
```bash
python3 install.py
```

## Desinstalación

Para desinstalar Babelcomics4:

```bash
# 1. Eliminar entorno virtual
rm -rf .venv/

# 2. Eliminar entrada del menú
rm ~/.local/share/applications/com.babelcomics.manager.desktop

# 3. Eliminar iconos
rm -rf ~/.local/share/icons/hicolor/*/apps/babelcomics4.png
rm -rf ~/.local/share/icons/hicolor/*/apps/com.babelcomics.manager.png

# 4. Actualizar caches
update-desktop-database ~/.local/share/applications
gtk-update-icon-cache ~/.local/share/icons/hicolor

# 5. (Opcional) Eliminar datos de la aplicación
rm -rf data/
```

## Más Información

- **Documentación completa**: Ver `CLAUDE.md` para detalles técnicos
- **Reporte de bugs**: Crear issue en el repositorio
- **Características**: Ver README.md

---

**Nota**: Esta aplicación está en desarrollo activo. Si encontrás problemas, por favor reportalos para que podamos mejorarla.
