# Comic Manager GTK4

Una aplicación moderna para gestionar tu colección de comics desarrollada con GTK4 y libadwaita, diseñada para ser elegante, funcional y fácil de usar.

## Características

- 📚 **Gestión completa de comics**: Organiza tus archivos CBR, CBZ, PDF y otros formatos
- 🏢 **Gestión de volúmenes y editoriales**: Mantén organizados tus series y editoriales favoritas
- 🔍 **Búsqueda y filtros avanzados**: Encuentra rápidamente lo que buscas
- 🖼️ **Vista en cuadrícula con portadas**: Interfaz visual atractiva con miniaturas
- 📊 **Estadísticas de colección**: Conoce el estado de tu biblioteca
- 🎨 **Interfaz moderna**: Desarrollada con GTK4 y libadwaita
- 🌙 **Tema oscuro**: Soporte completo para modo oscuro
- ⚡ **Escaneo automático**: Detecta nuevos comics automáticamente
- 💾 **Base de datos SQLite**: Almacenamiento eficiente y confiable

## Capturas de Pantalla

*(Incluir capturas de pantalla aquí cuando tengas la aplicación funcionando)*

## Requisitos del Sistema

### Dependencias Python
- Python 3.8 o superior
- SQLAlchemy 2.0+
- PyGObject (gi)

### Dependencias del Sistema

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1 gir1.2-gdkpixbuf-2.0
sudo apt install python3-pip python3-sqlalchemy
```

#### Fedora
```bash
sudo dnf install python3-gobject gtk4-devel libadwaita-devel python3-sqlalchemy
```

#### Arch Linux
```bash
sudo pacman -S python-gobject gtk4 libadwaita python-sqlalchemy
```

## Instalación

### Instalación desde Código Fuente

1. **Clonar el repositorio**:
```bash
git clone https://github.com/tu-usuario/comic-manager-gtk4.git
cd comic-manager-gtk4
```

2. **Instalar dependencias Python**:
```bash
pip3 install sqlalchemy
```

3. **Verificar que tu estructura de archivos sea como sigue**:
```
comic-manager-gtk4/
├── main_application.py          # Archivo principal
├── comic_manager_main.py        # Ventana principal
├── comic_detail_widget.py       # Widgets de detalle
├── comic_search_filter.py       # Sistema de búsqueda
├── comic_utils.py              # Utilidades
├── entidades/                  # Modelos de base de datos
│   ├── __init__.py
│   ├── base_repository.py
│   ├── base_repository_gtk4.py
│   ├── comicbook_model.py
│   ├── comicbook_info_model.py
│   ├── comicbook_info_cover_model.py
│   ├── volume_model.py
│   ├── publisher_model.py
│   ├── setup_model.py
│   └── volume_search_model.py
├── repositories/               # Repositorios
│   ├── __init__.py
│   ├── comicbook_repository.py
│   ├── comicbook_repository_gtk4.py
│   ├── volume_repository.py
│   ├── publisher_repository.py
│   ├── setup_repository.py
│   └── volume_search_repository.py
├── data/                      # Datos y miniaturas
│   └── thumbnails/
│       ├── comics/
│       ├── comicbookinfo_issues/
│       ├── volumenes/
│       └── editoriales/
└── images/                    # Imágenes por defecto
```

4. **Crear archivo `entidades/__init__.py`**:
```python
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
```

5. **Crear archivo `repositories/__init__.py`**:
```python
# Archivo de inicialización de repositorios
```

6. **Ejecutar la aplicación**:
```bash
python3 main_application.py
```

## Uso Básico

### Primera Ejecución

1. **Configurar directorios**: Ve a Menú → Configuración → Añadir directorios de escaneo
2. **Escanear comics**: Menú → Escanear directorios para detectar tus archivos
3. **Navegar**: Usa el sidebar para alternar entre Comics, Volúmenes, Editoriales

### Navegación

- **Sidebar izquierdo**: Cambia entre diferentes secciones
- **Barra de búsqueda**: Búsqueda rápida en tiempo real
- **Botón de filtros**: Acceso a filtros avanzados
- **Doble click**: Ver detalles de cualquier elemento
- **Menú de aplicación**: Acceso a configuración y herramientas

### Atajos de Teclado

- `Ctrl+F`: Enfocar búsqueda
- `Escape`: Limpiar búsqueda
- `F5`: Actualizar vista actual
- `Ctrl+1`: Ir a Comics
- `Ctrl+2`: Ir a Volúmenes
- `Ctrl+3`: Ir a Editoriales
- `Ctrl+4`: Ir a Arcos Argumentales

## Configuración

### Archivos de Configuración

La aplicación guarda su configuración en:
- **Linux**: `~/.config/comic-manager/config.json`

### Opciones Principales

- **Ruta de base de datos**: Ubicación del archivo SQLite
- **Items por página**: Cantidad de elementos mostrados
- **Tema oscuro**: Alternar entre tema claro y oscuro
- **Directorios de escaneo**: Carpetas monitoreadas automáticamente
- **Formatos soportados**: Extensiones de archivo reconocidas

## Estructura de la Base de Datos

La aplicación utiliza SQLite con las siguientes tablas principales:

- `comicbooks`: Archivos de comics físicos
- `comicbooks_info`: Metadatos de comics
- `comicbooks_info_covers`: Portadas de comics
- `volumens`: Series/volúmenes
- `publishers`: Editoriales
- `setups`: Configuración de la aplicación

## Formatos Soportados

- **CBR/CBZ**: Archivos de comics comprimidos
- **PDF**: Documentos PDF
- **ZIP/RAR**: Archivos comprimidos con imágenes
- **7Z**: Archivos 7-Zip

## Solución de Problemas

### Error: "No module named 'gi'"
```bash
# Ubuntu/Debian
sudo apt install python3-gi python3-gi-cairo

# Fedora
sudo dnf install python3-gobject

# Arch Linux
sudo pacman -S python-gobject
```

### Error: "No module named 'Adw'"
```bash
# Ubuntu/Debian
sudo apt install gir1.2-adw-1

# Fedora
sudo dnf install libadwaita-devel

# Arch Linux
sudo pacman -S libadwaita
```

### La aplicación no encuentra comics
1. Verifica que los directorios estén configurados correctamente
2. Asegúrate de que los archivos tengan extensiones soportadas
3. Ejecuta un escaneo manual desde el menú

### Problemas de rendimiento
1. Reduce la cantidad de items por página en configuración
2. Limpia la caché de miniaturas
3. Verifica el espacio en disco disponible

## Desarrollo

### Estructura del Código

- `main_application.py`: Aplicación principal y punto de entrada
- `comic_manager_main.py`: Ventana principal básica
- `comic_detail_widget.py`: Widgets de detalle y diálogos
- `comic_search_filter.py`: Sistema de búsqueda y filtros
- `comic_utils.py`: Utilidades y configuración
- `entidades/`: Modelos de SQLAlchemy
- `repositories/`: Capa de acceso a datos

### Contribuir

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Añadir nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request

### Estilo de Código

- Usar PEP 8 para Python
- Comentarios en español para este proyecto
- Docstrings para todas las funciones públicas
- Type hints donde sea apropiado

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo LICENSE para detalles.

## Agradecimientos

- GTK4 y libadwaita por las herramientas de UI modernas
- SQLAlchemy por el ORM robusto
- La comunidad de GNOME por la documentación y ejemplos

## Roadmap

- [ ] Integración con Comic Vine API
- [ ] Sincronización en la nube
- [ ] Lector de comics integrado
- [ ] Gestión de arcos argumentales
- [ ] Exportar/importar colección
- [ ] Estadísticas avanzadas
- [ ] Soporte para bibliotecas compartidas
- [ ] Aplicación móvil complementaria

## Soporte

- **Issues**: Reporta bugs y solicita features en GitHub Issues
- **Discusiones**: Únete a las discusiones del proyecto
- **Wiki**: Documentación adicional en la Wiki del proyecto

---

**¿Te gusta Comic Manager?** ¡Dale una estrella ⭐ al repositorio y compártelo con otros coleccionistas de comics!