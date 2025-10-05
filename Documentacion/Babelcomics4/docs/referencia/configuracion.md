# Configuración

Babelcomics4 ofrece un sistema de configuración flexible que permite personalizar el comportamiento de la aplicación, desde directorios de comics hasta parámetros de la API de ComicVine y preferencias de interfaz.

## 📁 Archivos de Configuración

### Ubicaciones de Configuración

#### Directorios del Sistema
```bash
# Configuración de usuario (Linux)
~/.config/babelcomics4/
├── config.json          # Configuración principal
├── database.conf         # Configuración de base de datos
├── comicvine.conf        # Configuración API ComicVine
├── thumbnails.conf       # Configuración de thumbnails
└── filters.json          # Filtros guardados

# Configuración del sistema (Linux)
/etc/babelcomics4/
├── default.conf          # Configuración por defecto
└── system.conf           # Configuración del sistema

# Datos de aplicación
~/.local/share/babelcomics4/
├── database/
│   └── babelcomics.db    # Base de datos SQLite
├── thumbnails/           # Cache de thumbnails
├── covers/               # Portadas descargadas
└── logs/                 # Archivos de log
```

#### Windows
```powershell
# Configuración de usuario
%APPDATA%\Babelcomics4\
├── config.json
├── database.conf
└── ...

# Datos de aplicación
%LOCALAPPDATA%\Babelcomics4\
├── database\
├── thumbnails\
└── logs\
```

#### macOS
```bash
# Configuración de usuario
~/Library/Preferences/com.babelcomics4/
├── config.json
└── ...

# Datos de aplicación
~/Library/Application Support/Babelcomics4/
├── database/
├── thumbnails/
└── logs/
```

### Configuración Principal

#### config.json
```json
{
  "version": "4.0.0",
  "application": {
    "language": "auto",
    "theme": "auto",
    "startup_scan": true,
    "minimize_to_tray": false,
    "remember_window_state": true,
    "auto_backup": true,
    "backup_frequency": "weekly"
  },
  "directories": {
    "comics_paths": [
      "~/Comics",
      "/media/comics",
      "~/Documents/Comic Books"
    ],
    "watch_directories": true,
    "recursive_scan": true,
    "follow_symlinks": false,
    "excluded_patterns": [
      "*.tmp",
      "*.part",
      "Thumbs.db",
      ".DS_Store"
    ]
  },
  "database": {
    "path": "~/.local/share/babelcomics4/database/babelcomics.db",
    "backup_path": "~/.local/share/babelcomics4/database/backups/",
    "auto_backup": true,
    "backup_retention_days": 30,
    "vacuum_frequency": "monthly"
  },
  "comicvine": {
    "api_key": "",
    "auto_catalog": false,
    "confidence_threshold": 0.7,
    "batch_size": 50,
    "request_delay": 0.5,
    "cache_enabled": true,
    "cache_ttl": 3600,
    "download_covers": true,
    "max_cover_size": "2MB"
  },
  "thumbnails": {
    "enabled": true,
    "size": "medium",
    "quality": "balanced",
    "cache_size_limit": "1GB",
    "auto_cleanup": true,
    "effects": {
      "uncataloged_grayscale": true,
      "quality_overlay": true,
      "border_effects": true
    }
  },
  "interface": {
    "default_view": "grid",
    "items_per_page": 50,
    "show_tooltips": true,
    "animate_transitions": true,
    "card_size": "medium",
    "sort_order": "filename",
    "remember_filters": true
  },
  "advanced": {
    "logging_level": "INFO",
    "max_log_size": "10MB",
    "log_retention_days": 7,
    "parallel_processing": true,
    "max_workers": 4,
    "memory_cache_size": "256MB"
  }
}
```

## ⚙️ Configuración de Módulos

### Configuración de Base de Datos

#### database.conf
```ini
[database]
# Configuración de SQLite
path = ~/.local/share/babelcomics4/database/babelcomics.db
journal_mode = WAL
synchronous = NORMAL
cache_size = 10000
temp_store = MEMORY
mmap_size = 268435456

[backup]
# Configuración de respaldos
enabled = true
frequency = daily
retention_days = 30
compress = true
backup_path = ~/.local/share/babelcomics4/database/backups/

[maintenance]
# Mantenimiento automático
auto_vacuum = true
vacuum_frequency = weekly
analyze_frequency = daily
integrity_check = weekly
```

### Configuración de ComicVine

#### comicvine.conf
```ini
[api]
# Configuración de la API
base_url = https://comicvine.gamespot.com/api/
api_key = YOUR_API_KEY_HERE
user_agent = Babelcomics4/4.0
timeout = 30
retries = 3

[rate_limiting]
# Control de frecuencia de peticiones
requests_per_hour = 200
request_delay = 0.5
burst_limit = 10
burst_window = 60

[caching]
# Cache de respuestas
enabled = true
cache_size = 1000
ttl = 3600
invalidate_on_error = true

[cataloging]
# Configuración de catalogación
auto_catalog = false
confidence_threshold = 0.7
batch_size = 50
update_existing = false
download_covers = true
download_character_info = false
download_creator_info = false

[search]
# Configuración de búsqueda
fuzzy_matching = true
year_tolerance = 2
publisher_weight = 0.3
series_weight = 0.5
issue_weight = 0.2
```

### Configuración de Thumbnails

#### thumbnails.conf
```ini
[generation]
# Generación de thumbnails
enabled = true
format = JPEG
quality = 85
progressive = true
optimize = true

[sizes]
# Tamaños disponibles
small = 150x225
medium = 200x300
large = 300x450
extra_large = 400x600
default = medium

[effects]
# Efectos visuales
uncataloged_grayscale = true
trash_desaturate = true
quality_overlay = true
border_effects = true
hover_effects = true

[cache]
# Gestión de cache
cache_size_limit = 1073741824  # 1GB en bytes
auto_cleanup = true
cleanup_frequency = weekly
orphan_cleanup = true

[performance]
# Optimización
lazy_loading = true
batch_generation = true
max_workers = 2
memory_limit = 256MB
```

## 🔧 Configuración Avanzada

### Variables de Entorno

#### Variables del Sistema
```bash
# Directorio base de configuración
export BABELCOMICS4_CONFIG_DIR="/path/to/config"

# Directorio de datos
export BABELCOMICS4_DATA_DIR="/path/to/data"

# Nivel de logging
export BABELCOMICS4_LOG_LEVEL="DEBUG"

# Clave API de ComicVine
export COMICVINE_API_KEY="your_api_key_here"

# Directorio principal de comics
export COMICS_PATH="/path/to/comics"

# Modo de desarrollo
export BABELCOMICS4_DEV_MODE="false"

# Configuración de base de datos
export DATABASE_URL="sqlite:///path/to/database.db"

# Proxy para conexiones HTTP
export HTTP_PROXY="http://proxy.example.com:8080"
export HTTPS_PROXY="http://proxy.example.com:8080"
```

### Configuración por Línea de Comandos

#### Argumentos de Inicio
```bash
# Especificar archivo de configuración
babelcomics4 --config /path/to/config.json

# Nivel de logging
babelcomics4 --log-level DEBUG

# Modo de desarrollo
babelcomics4 --dev-mode

# Directorio de datos personalizado
babelcomics4 --data-dir /path/to/data

# Sin interfaz gráfica (modo headless)
babelcomics4 --headless

# Escaneo inicial
babelcomics4 --scan /path/to/comics

# Catalogación en lote
babelcomics4 --catalog-all --confidence 0.8

# Backup de base de datos
babelcomics4 --backup

# Verificación de integridad
babelcomics4 --verify

# Ejemplos de uso
babelcomics4 --config ~/my_config.json --log-level DEBUG
babelcomics4 --scan ~/Comics --catalog-all
babelcomics4 --headless --backup --verify
```

## 🎨 Configuración de Interfaz

### Configuración de Tema

#### Personalización Visual
```json
{
  "theme": {
    "name": "custom",
    "colors": {
      "primary": "#3498db",
      "secondary": "#2ecc71",
      "accent": "#e74c3c",
      "background": "#ffffff",
      "surface": "#f8f9fa",
      "text": "#212529",
      "text_secondary": "#6c757d"
    },
    "fonts": {
      "primary": "Inter, sans-serif",
      "monospace": "JetBrains Mono, monospace",
      "size_base": 14,
      "size_small": 12,
      "size_large": 16
    },
    "spacing": {
      "unit": 8,
      "small": 4,
      "medium": 8,
      "large": 16,
      "extra_large": 24
    },
    "borders": {
      "radius": 8,
      "width": 1,
      "color": "#dee2e6"
    },
    "shadows": {
      "small": "0 2px 4px rgba(0,0,0,0.1)",
      "medium": "0 4px 8px rgba(0,0,0,0.15)",
      "large": "0 8px 16px rgba(0,0,0,0.2)"
    }
  }
}
```

### Configuración de Filtros

#### filters.json
```json
{
  "saved_filters": [
    {
      "id": "high_quality_dc",
      "name": "Comics DC Alta Calidad",
      "description": "Comics de DC de 4-5 estrellas",
      "filters": {
        "publishers": ["DC Comics"],
        "quality_range": [4, 5],
        "classification": "cataloged"
      },
      "sort": {
        "field": "title",
        "order": "asc"
      },
      "created_at": "2024-03-15T10:30:00Z",
      "last_used": "2024-03-20T14:45:00Z",
      "use_count": 25
    },
    {
      "id": "uncataloged_recent",
      "name": "Sin Catalogar Recientes",
      "description": "Comics agregados en los últimos 30 días sin catalogar",
      "filters": {
        "classification": "uncataloged",
        "date_added_range": ["30_days_ago", "now"]
      },
      "sort": {
        "field": "date_added",
        "order": "desc"
      },
      "created_at": "2024-03-10T09:15:00Z",
      "last_used": "2024-03-21T16:20:00Z",
      "use_count": 12
    }
  ],
  "quick_filters": [
    {
      "name": "Todos",
      "icon": "list-all",
      "filters": {}
    },
    {
      "name": "Catalogados",
      "icon": "check-circle",
      "filters": {
        "classification": "cataloged"
      }
    },
    {
      "name": "Sin Catalogar",
      "icon": "question-circle",
      "filters": {
        "classification": "uncataloged"
      }
    },
    {
      "name": "Alta Calidad",
      "icon": "star",
      "filters": {
        "quality_range": [4, 5]
      }
    },
    {
      "name": "Agregados Hoy",
      "icon": "calendar",
      "filters": {
        "date_added_range": ["today", "now"]
      }
    }
  ]
}
```

## 🔧 Herramientas de Configuración

### Editor de Configuración

#### ConfigurationManager
```python
import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
import configparser

class ConfigurationManager:
    """Gestor de configuración de Babelcomics4"""

    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir or self._get_default_config_dir())
        self.config_file = self.config_dir / "config.json"
        self.config = {}

        self._ensure_config_dir()
        self._load_config()

    def _get_default_config_dir(self) -> str:
        """Obtener directorio de configuración por defecto"""
        import platform

        system = platform.system()
        if system == "Linux":
            return os.path.expanduser("~/.config/babelcomics4")
        elif system == "Windows":
            return os.path.expandvars("%APPDATA%\\Babelcomics4")
        elif system == "Darwin":  # macOS
            return os.path.expanduser("~/Library/Preferences/com.babelcomics4")
        else:
            return os.path.expanduser("~/.babelcomics4")

    def _ensure_config_dir(self):
        """Crear directorio de configuración si no existe"""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self):
        """Cargar configuración desde archivo"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error cargando configuración: {e}")
                self.config = self._get_default_config()
        else:
            self.config = self._get_default_config()
            self.save_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Obtener configuración por defecto"""
        return {
            "version": "4.0.0",
            "application": {
                "language": "auto",
                "theme": "auto",
                "startup_scan": True,
                "minimize_to_tray": False,
                "remember_window_state": True
            },
            "directories": {
                "comics_paths": [os.path.expanduser("~/Comics")],
                "watch_directories": True,
                "recursive_scan": True,
                "follow_symlinks": False
            },
            "comicvine": {
                "api_key": "",
                "auto_catalog": False,
                "confidence_threshold": 0.7,
                "request_delay": 0.5
            },
            "thumbnails": {
                "enabled": True,
                "size": "medium",
                "quality": "balanced"
            },
            "interface": {
                "default_view": "grid",
                "items_per_page": 50,
                "card_size": "medium"
            }
        }

    def get(self, key_path: str, default=None):
        """Obtener valor de configuración usando path separado por puntos"""
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, key_path: str, value: Any):
        """Establecer valor de configuración usando path separado por puntos"""
        keys = key_path.split('.')
        target = self.config

        # Navegar hasta el penúltimo nivel
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]

        # Establecer el valor final
        target[keys[-1]] = value

    def save_config(self):
        """Guardar configuración a archivo"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error guardando configuración: {e}")

    def reset_to_defaults(self):
        """Resetear configuración a valores por defecto"""
        self.config = self._get_default_config()
        self.save_config()

    def export_config(self, export_path: str):
        """Exportar configuración a archivo"""
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error exportando configuración: {e}")

    def import_config(self, import_path: str):
        """Importar configuración desde archivo"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)

            # Validar configuración importada
            if self._validate_config(imported_config):
                self.config = imported_config
                self.save_config()
                return True
            else:
                print("Configuración importada no válida")
                return False

        except (json.JSONDecodeError, IOError) as e:
            print(f"Error importando configuración: {e}")
            return False

    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """Validar estructura de configuración"""
        required_sections = ['application', 'directories', 'comicvine', 'thumbnails', 'interface']

        for section in required_sections:
            if section not in config:
                return False

        return True

    def get_comics_directories(self) -> List[str]:
        """Obtener directorios de comics configurados"""
        return self.get('directories.comics_paths', [])

    def add_comics_directory(self, path: str):
        """Añadir directorio de comics"""
        directories = self.get_comics_directories()
        if path not in directories:
            directories.append(path)
            self.set('directories.comics_paths', directories)
            self.save_config()

    def remove_comics_directory(self, path: str):
        """Remover directorio de comics"""
        directories = self.get_comics_directories()
        if path in directories:
            directories.remove(path)
            self.set('directories.comics_paths', directories)
            self.save_config()

    def is_comicvine_configured(self) -> bool:
        """Verificar si ComicVine está configurado"""
        api_key = self.get('comicvine.api_key', '')
        return bool(api_key and api_key.strip())

    def set_comicvine_api_key(self, api_key: str):
        """Establecer clave API de ComicVine"""
        self.set('comicvine.api_key', api_key.strip())
        self.save_config()
```

### Migración de Configuración

#### ConfigMigrator
```python
class ConfigMigrator:
    """Migrador de configuración entre versiones"""

    VERSION_MIGRATIONS = {
        "3.0.0": "migrate_from_3_0_0",
        "3.5.0": "migrate_from_3_5_0",
        "4.0.0": "migrate_from_4_0_0"
    }

    def __init__(self, config_manager: ConfigurationManager):
        self.config_manager = config_manager

    def migrate_if_needed(self):
        """Migrar configuración si es necesario"""
        current_version = self.config_manager.get('version', '1.0.0')
        target_version = "4.0.0"

        if current_version != target_version:
            self._perform_migration(current_version, target_version)

    def _perform_migration(self, from_version: str, to_version: str):
        """Realizar migración entre versiones"""
        # Crear backup de configuración actual
        backup_path = self.config_manager.config_dir / f"config_backup_{from_version}.json"
        self.config_manager.export_config(str(backup_path))

        # Aplicar migraciones en orden
        versions_to_migrate = self._get_migration_path(from_version, to_version)

        for version in versions_to_migrate:
            if version in self.VERSION_MIGRATIONS:
                migration_method = getattr(self, self.VERSION_MIGRATIONS[version])
                migration_method()

        # Actualizar versión
        self.config_manager.set('version', to_version)
        self.config_manager.save_config()

    def migrate_from_3_0_0(self):
        """Migrar desde versión 3.0.0"""
        # Migrar estructura de directorios
        old_comics_dir = self.config_manager.get('comics_directory')
        if old_comics_dir:
            self.config_manager.set('directories.comics_paths', [old_comics_dir])

        # Migrar configuración de thumbnails
        old_thumb_size = self.config_manager.get('thumbnail_size', 200)
        if old_thumb_size <= 150:
            new_size = "small"
        elif old_thumb_size <= 250:
            new_size = "medium"
        else:
            new_size = "large"

        self.config_manager.set('thumbnails.size', new_size)

    def migrate_from_3_5_0(self):
        """Migrar desde versión 3.5.0"""
        # Migrar configuración de ComicVine
        old_auto_download = self.config_manager.get('auto_download_metadata', False)
        self.config_manager.set('comicvine.auto_catalog', old_auto_download)

        # Migrar configuración de interfaz
        old_view_mode = self.config_manager.get('view_mode', 'grid')
        self.config_manager.set('interface.default_view', old_view_mode)
```

---

**¿Necesitas solucionar problemas?** 👉 [Troubleshooting](troubleshooting.md)