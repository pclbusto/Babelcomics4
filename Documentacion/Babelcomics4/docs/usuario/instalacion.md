# Instalación

Esta guía te ayudará a instalar y configurar Babelcomics4 en tu sistema.

## 📋 Requisitos del Sistema

### Requisitos Mínimos
- **Sistema Operativo**: Linux (recomendado: Ubuntu 22.04+, Fedora 38+, Arch Linux)
- **Python**: 3.11 o superior (probado con Python 3.13)
- **RAM**: 2GB mínimo, 4GB recomendado
- **Almacenamiento**: 500MB para la aplicación + espacio para tu colección
- **GTK4**: Versión 4.6 o superior

### Requisitos de Desarrollo
- **Git**: Para clonar el repositorio
- **pip**: Gestor de paquetes de Python
- **venv**: Para entornos virtuales
- **GTK4 Development**: Librerías de desarrollo de GTK4

## 🔧 Instalación en Ubuntu/Debian

### 1. Actualizar el Sistema
```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Instalar Dependencias del Sistema
```bash
# GTK4 y libadwaita
sudo apt install libgtk-4-dev libadwaita-1-dev

# Python y herramientas de desarrollo
sudo apt install python3 python3-pip python3-venv python3-dev

# Dependencias adicionales
sudo apt install gobject-introspection libgirepository1.0-dev

# Soporte para archivos RAR (opcional)
sudo apt install unrar-free

# ImageMagick (para procesamiento de iconos)
sudo apt install imagemagick
```

### 3. Clonar el Repositorio
```bash
cd ~/
git clone <url-del-repositorio> Babelcomics4
cd Babelcomics4
```

### 4. Crear Entorno Virtual
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 5. Instalar Dependencias Python
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 🔧 Instalación en Fedora

### 1. Instalar Dependencias del Sistema
```bash
# GTK4 y libadwaita
sudo dnf install gtk4-devel libadwaita-devel

# Python y herramientas
sudo dnf install python3 python3-pip python3-devel

# Dependencias adicionales
sudo dnf install gobject-introspection-devel

# Soporte RAR (opcional)
sudo dnf install unrar

# ImageMagick (para procesamiento de iconos)
sudo dnf install ImageMagick
```

### 2. Seguir pasos 3-5 de Ubuntu

## 🔧 Instalación en Arch Linux

### 1. Instalar Dependencias del Sistema
```bash
# GTK4 y libadwaita
sudo pacman -S gtk4 libadwaita

# Python y herramientas
sudo pacman -S python python-pip

# Dependencias adicionales
sudo pacman -S gobject-introspection

# Soporte RAR (opcional)
sudo pacman -S unrar

# ImageMagick (para procesamiento de iconos)
sudo pacman -S imagemagick
```

### 2. Seguir pasos 3-5 de Ubuntu

## 📦 Dependencias Python

El archivo `requirements.txt` incluye todas las dependencias necesarias:

```txt
# Base de datos y ORM
sqlalchemy>=2.0.0
alembic>=1.12.0

# Interfaz gráfica GTK4
pygobject>=3.46.0

# Procesamiento de imágenes
pillow>=10.0.0

# API ComicVine
requests>=2.31.0

# Compresión de archivos
rarfile>=4.0

# Documentación (opcional)
mkdocs>=1.5.0
mkdocs-material>=9.4.0
```

## ⚙️ Configuración Inicial

### Script de Setup Automático (Recomendado)

Babelcomics4 incluye un script de configuración automática que configura todo lo necesario:

```bash
# Ejecutar script de setup
python setup.py
```

**El script automáticamente:**
- ✅ Verifica dependencias del sistema
- ✅ Crea estructura de directorios necesarios
- ✅ Instala dependencias Python
- ✅ Configura la base de datos SQLite
- ✅ Instala iconos en el sistema (múltiples resoluciones)
- ✅ Crea entrada en el menú de aplicaciones
- ✅ Genera script de inicio ejecutable

### Configuración Manual (Alternativa)

Si prefieres configurar manualmente:

#### 1. Verificar Instalación
```bash
# Activar entorno virtual
source .venv/bin/activate

# Verificar dependencias GTK4
python -c "import gi; gi.require_version('Gtk', '4.0'); from gi.repository import Gtk; print('GTK4 OK')"

# Verificar dependencias adicionales
python -c "import sqlalchemy, requests, PIL; print('Dependencias OK')"
```

#### 2. Crear Directorios Necesarios
```bash
# Crear estructura de directorios
mkdir -p data/thumbnails/{comics,volumes,publishers,comicbookinfo_issues}
mkdir -p logs config backup
```

#### 3. Configurar Base de Datos
```bash
# La base de datos se crea automáticamente en el primer inicio
# Ubicación: ./data/babelcomics.db
```

#### 4. Instalar Iconos del Sistema
```bash
# Crear directorios de iconos
mkdir -p ~/.local/share/icons/hicolor/{48x48,64x64,128x128,256x256}/apps

# Instalar iconos (requiere ImageMagick)
magick images/icon.png -resize 48x48 ~/.local/share/icons/hicolor/48x48/apps/babelcomics4.png
magick images/icon.png -resize 64x64 ~/.local/share/icons/hicolor/64x64/apps/babelcomics4.png
cp images/icon.png ~/.local/share/icons/hicolor/128x128/apps/babelcomics4.png
cp images/icon.png ~/.local/share/icons/hicolor/256x256/apps/babelcomics4.png

# Actualizar cache de iconos
gtk-update-icon-cache ~/.local/share/icons/hicolor/ || true
```

#### 5. Primer Inicio
```bash
python Babelcomic4.py
```

## 🗂️ Estructura de Directorios

Después de la instalación, tu proyecto tendrá esta estructura:

```
Babelcomics4/
├── 📄 Babelcomic4.py              # Aplicación principal
├── 📁 entidades/                  # Modelos de datos
├── 📁 repositories/               # Capa de acceso a datos
├── 📁 helpers/                    # Utilidades ComicVine
├── 📁 data/                       # Base de datos y cache
│   ├── babelcomics.db            # Base de datos SQLite
│   └── thumbnails/               # Cache de miniaturas
│       ├── comics/               # Thumbnails de archivos
│       ├── volumes/              # Portadas de volúmenes
│       ├── publishers/           # Logos de editoriales
│       └── comicbookinfo_issues/ # Portadas de issues
├── 📁 images/                     # Recursos de interfaz
│   └── icon.png                  # Icono de la aplicación
├── 📁 logs/                      # Archivos de registro
├── 📁 config/                    # Configuración personalizada
├── 📁 backup/                    # Respaldos automáticos
├── 📁 Documentacion/             # Documentación MkDocs
├── 📄 setup.py                   # Script de configuración automática
├── 📄 babelcomics4.sh            # Script de inicio (generado por setup)
├── 📄 requirements.txt           # Dependencias Python
└── 📄 README.md                  # Información del proyecto
```

## 🛠️ Desarrollo

### Configurar Entorno de Desarrollo
```bash
# Instalar dependencias adicionales para desarrollo
pip install mkdocs mkdocs-material

# Ejecutar documentación en desarrollo
cd Documentacion/Babelcomics4
mkdocs serve
```

### Variables de Entorno
```bash
# ComicVine API (opcional, pero recomendado)
export COMICVINE_API_KEY="tu-api-key-aqui"

# Directorio de comics (opcional)
export COMICS_PATH="/ruta/a/tus/comics"
```

## 🔍 Verificación de la Instalación

### Test Básico
```bash
# Ejecutar aplicación
python Babelcomic4.py

# Deberías ver:
# ✓ Pango disponible
# ✓ Todos los archivos requeridos encontrados
# ✓ Base de datos encontrada
# ✓ Aplicación creada
```

### Test de ComicVine (Opcional)
```bash
# Con API key configurada
python -c "
from helpers.comicvine_client import ComicVineClient;
client = ComicVineClient();
print('ComicVine OK' if client else 'ComicVine Error')
"
```

## ❗ Solución de Problemas

### Error: No module named 'gi'
```bash
# Ubuntu/Debian
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0

# Fedora
sudo dnf install python3-gobject gtk4

# Arch
sudo pacman -S python-gobject gtk4
```

### Error: GTK4 not found
```bash
# Verificar instalación GTK4
pkg-config --modversion gtk4

# Si no está instalado, instalar desde repositorios del sistema
```

### Error: Permission denied al ejecutar
```bash
# Dar permisos de ejecución
chmod +x Babelcomic4.py

# O ejecutar con Python directamente
python Babelcomic4.py
```

### Base de datos bloqueada
```bash
# Verificar que no hay otra instancia ejecutándose
ps aux | grep Babelcomic4

# Si es necesario, eliminar archivo de lock
rm -f data/babelcomics.db.lock
```

## 🎯 Siguientes Pasos

Una vez completada la instalación:

1. **[Primeros Pasos](primeros-pasos.md)**: Aprende lo básico de la interfaz
2. **[Gestión de Comics](gestion-comics.md)**: Importa tu colección
3. **[ComicVine](comicvine.md)**: Configura la integración con ComicVine
4. **[Filtros](filtros-busqueda.md)**: Domina el sistema de búsqueda

---

¿Problemas con la instalación? Consulta el [Troubleshooting](../referencia/troubleshooting.md) o las [FAQ](../referencia/faq.md).