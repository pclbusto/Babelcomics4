# Troubleshooting

Esta guía te ayudará a resolver los problemas más comunes que puedes encontrar al usar Babelcomics4, desde errores de instalación hasta problemas de rendimiento y configuración.

## 🚨 Problemas Comunes

### Problemas de Instalación

#### Error: No se pueden instalar las dependencias
```bash
# Error típico
ERROR: Could not install packages due to an EnvironmentError

# Soluciones
# 1. Actualizar pip
python -m pip install --upgrade pip

# 2. Instalar con usuario actual
pip install --user babelcomics4

# 3. Usar entorno virtual
python -m venv babelcomics_env
source babelcomics_env/bin/activate  # Linux/macOS
babelcomics_env\Scripts\activate     # Windows
pip install babelcomics4

# 4. Instalar dependencias del sistema (Ubuntu/Debian)
sudo apt update
sudo apt install python3-dev python3-pip python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adwaita-1

# 5. Instalar dependencias del sistema (Fedora)
sudo dnf install python3-devel python3-pip python3-gobject gtk4-devel libadwaita-devel

# 6. Instalar dependencias del sistema (Arch)
sudo pacman -S python-pip python-gobject gtk4 libadwaita
```

#### Error: GTK4 no encontrado
```bash
# Error
ImportError: cannot import name 'Gtk' from 'gi.repository'

# Verificar instalación de GTK4
pkg-config --modversion gtk4

# Si no está instalado (Ubuntu/Debian)
sudo apt install libgtk-4-dev libadwaita-1-dev

# Si no está instalado (Fedora)
sudo dnf install gtk4-devel libadwaita-devel

# Si no está instalado (macOS con Homebrew)
brew install gtk4 libadwaita

# Verificar PyGObject
python -c "from gi.repository import Gtk; print(Gtk._version)"
```

#### Error: Base de datos no accesible
```bash
# Error
sqlite3.OperationalError: unable to open database file

# Verificar permisos del directorio
ls -la ~/.local/share/babelcomics4/

# Crear directorio si no existe
mkdir -p ~/.local/share/babelcomics4/database/

# Verificar permisos de escritura
touch ~/.local/share/babelcomics4/database/test.db
rm ~/.local/share/babelcomics4/database/test.db

# Si hay problemas de permisos
chmod 755 ~/.local/share/babelcomics4/
chmod 644 ~/.local/share/babelcomics4/database/
```

### Problemas de Rendimiento

#### La aplicación se ejecuta lentamente
```python
# Diagnóstico de rendimiento
def diagnose_performance():
    """Diagnosticar problemas de rendimiento"""

    issues = []

    # 1. Verificar tamaño de base de datos
    db_size = get_database_size()
    if db_size > 500_000_000:  # 500MB
        issues.append("Base de datos muy grande (>500MB)")

    # 2. Verificar número de comics
    comic_count = get_comic_count()
    if comic_count > 50_000:
        issues.append(f"Colección muy grande ({comic_count:,} comics)")

    # 3. Verificar cache de thumbnails
    cache_size = get_thumbnail_cache_size()
    if cache_size > 2_000_000_000:  # 2GB
        issues.append("Cache de thumbnails muy grande (>2GB)")

    # 4. Verificar memoria disponible
    available_memory = get_available_memory()
    if available_memory < 1_000_000_000:  # 1GB
        issues.append("Poca memoria disponible (<1GB)")

    return issues

# Soluciones de rendimiento
def optimize_performance():
    """Optimizar rendimiento de la aplicación"""

    # 1. Limpiar cache de thumbnails
    clean_thumbnail_cache()

    # 2. Vacuum de base de datos
    vacuum_database()

    # 3. Reindexar base de datos
    reindex_database()

    # 4. Limpiar logs antiguos
    clean_old_logs()

    # 5. Optimizar configuración
    optimize_configuration()
```

#### Problemas con thumbnails
```bash
# Regenerar thumbnails corruptos
babelcomics4 --regenerate-thumbnails

# Limpiar cache de thumbnails
rm -rf ~/.local/share/babelcomics4/thumbnails/*

# Verificar espacio en disco
df -h ~/.local/share/babelcomics4/

# Optimizar configuración de thumbnails
# En config.json:
{
  "thumbnails": {
    "quality": "economy",  # Reducir calidad
    "cache_size_limit": "500MB",  # Limitar cache
    "lazy_loading": true  # Carga bajo demanda
  }
}
```

### Problemas con ComicVine

#### Error: API Key inválida
```python
# Verificar configuración de API
def check_comicvine_config():
    """Verificar configuración de ComicVine"""

    config = ConfigurationManager()
    api_key = config.get('comicvine.api_key')

    if not api_key:
        print("❌ API Key no configurada")
        print("Solución: Configurar API Key en Preferencias")
        return False

    # Probar conexión
    client = ComicVineClient(api_key)
    try:
        test_result = client.search_volumes("Batman", limit=1)
        if test_result:
            print("✅ API Key válida y funcionando")
            return True
        else:
            print("❌ API Key inválida o problema de conexión")
            return False
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

# Soluciones para problemas de ComicVine
def fix_comicvine_issues():
    """Solucionar problemas comunes de ComicVine"""

    # 1. Verificar límites de rate
    print("Verificando límites de rate...")

    # 2. Limpiar cache de API
    print("Limpiando cache de API...")

    # 3. Reintentar peticiones fallidas
    print("Reintentando peticiones fallidas...")

    # 4. Verificar conectividad de red
    print("Verificando conectividad...")
```

#### Error: Rate limit excedido
```bash
# Error típico
ComicVine API error: Rate limit exceeded

# Soluciones en config.json:
{
  "comicvine": {
    "request_delay": 2.0,        # Aumentar delay
    "requests_per_hour": 150,    # Reducir límite
    "batch_size": 25             # Reducir tamaño de lote
  }
}

# Monitorear uso de API
tail -f ~/.local/share/babelcomics4/logs/comicvine.log
```

### Problemas de Base de Datos

#### Error: Base de datos corrupta
```sql
-- Verificar integridad
PRAGMA integrity_check;

-- Si hay corrupción, intentar reparar
PRAGMA quick_check;

-- Backup antes de reparar
cp ~/.local/share/babelcomics4/database/babelcomics.db \
   ~/.local/share/babelcomics4/database/babelcomics_backup.db

-- Vacuum para optimizar
VACUUM;

-- Reindexar
REINDEX;
```

```python
# Script de reparación de base de datos
def repair_database():
    """Reparar base de datos corrupta"""

    import sqlite3
    import shutil
    from datetime import datetime

    db_path = "~/.local/share/babelcomics4/database/babelcomics.db"
    backup_path = f"~/.local/share/babelcomics4/database/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

    # 1. Crear backup
    shutil.copy2(db_path, backup_path)
    print(f"Backup creado: {backup_path}")

    # 2. Intentar reparación
    try:
        conn = sqlite3.connect(db_path)

        # Verificar integridad
        result = conn.execute("PRAGMA integrity_check").fetchone()
        if result[0] != "ok":
            print(f"❌ Base de datos corrupta: {result[0]}")

            # Intentar exportar/importar datos
            export_and_reimport_database(conn)
        else:
            print("✅ Base de datos íntegra")

        # Optimizar
        conn.execute("VACUUM")
        conn.execute("REINDEX")
        conn.close()

    except Exception as e:
        print(f"❌ Error reparando base de datos: {e}")
        print(f"Restaurando backup desde: {backup_path}")
        shutil.copy2(backup_path, db_path)
```

#### Problemas de migración
```python
# Verificar versión de esquema
def check_schema_version():
    """Verificar versión del esquema de base de datos"""

    try:
        conn = sqlite3.connect(db_path)

        # Verificar tabla de versiones
        result = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='alembic_version'
        """).fetchone()

        if result:
            version = conn.execute("SELECT version_num FROM alembic_version").fetchone()
            print(f"Versión de esquema: {version[0] if version else 'Unknown'}")
        else:
            print("❌ Tabla de versiones no encontrada")

        conn.close()

    except Exception as e:
        print(f"❌ Error verificando esquema: {e}")

# Aplicar migraciones manualmente
def manual_migration():
    """Aplicar migraciones manualmente"""

    # Backup automático
    create_database_backup()

    # Aplicar migraciones
    from alembic import command
    from alembic.config import Config

    alembic_cfg = Config("alembic.ini")

    try:
        command.upgrade(alembic_cfg, "head")
        print("✅ Migraciones aplicadas exitosamente")
    except Exception as e:
        print(f"❌ Error en migración: {e}")
        restore_database_backup()
```

## 🔧 Herramientas de Diagnóstico

### Script de Diagnóstico Automático

#### diagnostic.py
```python
#!/usr/bin/env python3
"""
Script de diagnóstico automático para Babelcomics4
"""

import os
import sys
import json
import sqlite3
import platform
import subprocess
from pathlib import Path
from datetime import datetime

class Babelcomics4Diagnostic:
    """Herramienta de diagnóstico para Babelcomics4"""

    def __init__(self):
        self.config_dir = self._get_config_dir()
        self.data_dir = self._get_data_dir()
        self.issues = []
        self.warnings = []
        self.info = []

    def run_full_diagnostic(self):
        """Ejecutar diagnóstico completo"""
        print("🔍 Ejecutando diagnóstico de Babelcomics4...")
        print("=" * 50)

        self.check_system_requirements()
        self.check_python_environment()
        self.check_configuration()
        self.check_database()
        self.check_file_permissions()
        self.check_disk_space()
        self.check_network_connectivity()

        self.print_summary()

        if self.issues:
            print("\n🔧 Ejecutar reparaciones automáticas? (y/n): ", end="")
            if input().lower() == 'y':
                self.auto_repair()

    def check_system_requirements(self):
        """Verificar requisitos del sistema"""
        print("\n📋 Verificando requisitos del sistema...")

        # Versión de Python
        python_version = sys.version_info
        if python_version < (3, 9):
            self.issues.append(f"Python {python_version.major}.{python_version.minor} es muy antiguo (mínimo: 3.9)")
        else:
            self.info.append(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")

        # Sistema operativo
        os_info = platform.platform()
        self.info.append(f"💻 Sistema: {os_info}")

        # Arquitectura
        arch = platform.machine()
        self.info.append(f"🏗️ Arquitectura: {arch}")

        # Verificar GTK4
        try:
            from gi.repository import Gtk
            gtk_version = f"{Gtk.get_major_version()}.{Gtk.get_minor_version()}.{Gtk.get_micro_version()}"
            self.info.append(f"✅ GTK {gtk_version}")
        except ImportError:
            self.issues.append("GTK4 no está instalado o no es accesible")

        # Verificar libadwaita
        try:
            from gi.repository import Adw
            self.info.append("✅ libadwaita disponible")
        except ImportError:
            self.warnings.append("libadwaita no disponible (interfaz limitada)")

    def check_python_environment(self):
        """Verificar entorno de Python"""
        print("🐍 Verificando entorno de Python...")

        # Verificar dependencias críticas
        critical_deps = [
            'sqlalchemy',
            'requests',
            'pillow',
            'gi'
        ]

        for dep in critical_deps:
            try:
                __import__(dep)
                self.info.append(f"✅ {dep}")
            except ImportError:
                self.issues.append(f"Dependencia faltante: {dep}")

        # Verificar versiones de dependencias
        try:
            import sqlalchemy
            if sqlalchemy.__version__ < "2.0":
                self.warnings.append(f"SQLAlchemy {sqlalchemy.__version__} es antigua (recomendado: 2.0+)")
        except:
            pass

    def check_configuration(self):
        """Verificar configuración"""
        print("⚙️ Verificando configuración...")

        config_file = self.config_dir / "config.json"

        if not config_file.exists():
            self.warnings.append("Archivo de configuración no existe (se creará automáticamente)")
            return

        try:
            with open(config_file, 'r') as f:
                config = json.load(f)

            # Verificar estructura básica
            required_sections = ['application', 'directories', 'comicvine']
            for section in required_sections:
                if section not in config:
                    self.warnings.append(f"Sección de configuración faltante: {section}")

            # Verificar directorios de comics
            comics_paths = config.get('directories', {}).get('comics_paths', [])
            if not comics_paths:
                self.warnings.append("No hay directorios de comics configurados")
            else:
                for path in comics_paths:
                    if not os.path.exists(os.path.expanduser(path)):
                        self.warnings.append(f"Directorio de comics no existe: {path}")

            # Verificar API de ComicVine
            api_key = config.get('comicvine', {}).get('api_key', '')
            if not api_key:
                self.warnings.append("API Key de ComicVine no configurada")

            self.info.append("✅ Configuración cargada correctamente")

        except json.JSONDecodeError:
            self.issues.append("Archivo de configuración corrupto")
        except Exception as e:
            self.issues.append(f"Error leyendo configuración: {e}")

    def check_database(self):
        """Verificar base de datos"""
        print("🗄️ Verificando base de datos...")

        db_path = self.data_dir / "database" / "babelcomics.db"

        if not db_path.exists():
            self.info.append("Base de datos no existe (se creará automáticamente)")
            return

        try:
            conn = sqlite3.connect(db_path)

            # Verificar integridad
            result = conn.execute("PRAGMA integrity_check").fetchone()
            if result[0] != "ok":
                self.issues.append(f"Base de datos corrupta: {result[0]}")
            else:
                self.info.append("✅ Integridad de base de datos OK")

            # Verificar tamaño
            db_size = os.path.getsize(db_path)
            self.info.append(f"📊 Tamaño de base de datos: {db_size / 1024 / 1024:.1f} MB")

            # Contar registros
            comic_count = conn.execute("SELECT COUNT(*) FROM comicbooks").fetchone()[0]
            self.info.append(f"📚 Comics en base de datos: {comic_count:,}")

            conn.close()

        except sqlite3.Error as e:
            self.issues.append(f"Error de base de datos: {e}")

    def check_file_permissions(self):
        """Verificar permisos de archivos"""
        print("🔐 Verificando permisos...")

        # Verificar permisos de directorios
        dirs_to_check = [
            self.config_dir,
            self.data_dir,
            self.data_dir / "database",
            self.data_dir / "thumbnails",
            self.data_dir / "logs"
        ]

        for directory in dirs_to_check:
            if directory.exists():
                if not os.access(directory, os.W_OK):
                    self.issues.append(f"Sin permisos de escritura: {directory}")
                else:
                    self.info.append(f"✅ Permisos OK: {directory.name}")
            else:
                try:
                    directory.mkdir(parents=True, exist_ok=True)
                    self.info.append(f"✅ Directorio creado: {directory}")
                except PermissionError:
                    self.issues.append(f"No se puede crear directorio: {directory}")

    def check_disk_space(self):
        """Verificar espacio en disco"""
        print("💾 Verificando espacio en disco...")

        try:
            if platform.system() == "Windows":
                import shutil
                total, used, free = shutil.disk_usage(self.data_dir)
            else:
                statvfs = os.statvfs(self.data_dir)
                free = statvfs.f_frsize * statvfs.f_bavail
                total = statvfs.f_frsize * statvfs.f_blocks

            free_gb = free / (1024**3)
            total_gb = total / (1024**3)

            self.info.append(f"💽 Espacio libre: {free_gb:.1f} GB de {total_gb:.1f} GB")

            if free_gb < 1:
                self.issues.append("Espacio en disco muy bajo (<1GB)")
            elif free_gb < 5:
                self.warnings.append("Espacio en disco bajo (<5GB)")

        except Exception as e:
            self.warnings.append(f"No se pudo verificar espacio en disco: {e}")

    def check_network_connectivity(self):
        """Verificar conectividad de red"""
        print("🌐 Verificando conectividad...")

        try:
            import requests

            # Probar conexión a ComicVine
            response = requests.get("https://comicvine.gamespot.com", timeout=10)
            if response.status_code == 200:
                self.info.append("✅ Conectividad a ComicVine OK")
            else:
                self.warnings.append(f"ComicVine responde con código: {response.status_code}")

        except requests.exceptions.RequestException as e:
            self.warnings.append(f"Problema de conectividad: {e}")
        except ImportError:
            self.warnings.append("Módulo requests no disponible")

    def print_summary(self):
        """Imprimir resumen del diagnóstico"""
        print("\n" + "=" * 50)
        print("📊 RESUMEN DEL DIAGNÓSTICO")
        print("=" * 50)

        if self.issues:
            print(f"\n❌ PROBLEMAS CRÍTICOS ({len(self.issues)}):")
            for issue in self.issues:
                print(f"   • {issue}")

        if self.warnings:
            print(f"\n⚠️ ADVERTENCIAS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   • {warning}")

        if self.info:
            print(f"\n✅ INFORMACIÓN ({len(self.info)}):")
            for info_item in self.info:
                print(f"   • {info_item}")

        # Estado general
        if not self.issues:
            if not self.warnings:
                print("\n🎉 ¡Todo funciona perfectamente!")
            else:
                print("\n👍 Sistema funcional con algunas advertencias")
        else:
            print(f"\n🔧 Se encontraron {len(self.issues)} problemas que requieren atención")

    def auto_repair(self):
        """Reparaciones automáticas"""
        print("\n🔧 Ejecutando reparaciones automáticas...")

        # Crear directorios faltantes
        for directory in [self.config_dir, self.data_dir]:
            if not directory.exists():
                try:
                    directory.mkdir(parents=True, exist_ok=True)
                    print(f"✅ Directorio creado: {directory}")
                except Exception as e:
                    print(f"❌ Error creando {directory}: {e}")

        # Reparar configuración
        config_file = self.config_dir / "config.json"
        if not config_file.exists():
            self._create_default_config()

        # Limpiar cache si hay problemas de espacio
        if any("espacio" in issue.lower() for issue in self.issues):
            self._clean_cache()

        print("🎯 Reparaciones completadas")

    def _get_config_dir(self):
        """Obtener directorio de configuración"""
        if platform.system() == "Windows":
            return Path(os.path.expandvars("%APPDATA%")) / "Babelcomics4"
        elif platform.system() == "Darwin":
            return Path.home() / "Library" / "Preferences" / "com.babelcomics4"
        else:
            return Path.home() / ".config" / "babelcomics4"

    def _get_data_dir(self):
        """Obtener directorio de datos"""
        if platform.system() == "Windows":
            return Path(os.path.expandvars("%LOCALAPPDATA%")) / "Babelcomics4"
        elif platform.system() == "Darwin":
            return Path.home() / "Library" / "Application Support" / "Babelcomics4"
        else:
            return Path.home() / ".local" / "share" / "babelcomics4"

if __name__ == "__main__":
    diagnostic = Babelcomics4Diagnostic()
    diagnostic.run_full_diagnostic()
```

### Recolección de Logs

#### Log Collector
```python
def collect_diagnostic_logs():
    """Recolectar logs para diagnóstico"""

    import zipfile
    from datetime import datetime, timedelta

    log_dir = Path.home() / ".local" / "share" / "babelcomics4" / "logs"
    output_file = f"babelcomics4_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"

    with zipfile.ZipFile(output_file, 'w') as zip_file:
        # Logs de aplicación
        for log_file in log_dir.glob("*.log"):
            zip_file.write(log_file, f"logs/{log_file.name}")

        # Configuración (sin datos sensibles)
        config_file = Path.home() / ".config" / "babelcomics4" / "config.json"
        if config_file.exists():
            # Censurar API keys antes de incluir
            with open(config_file, 'r') as f:
                config = json.load(f)

            if 'comicvine' in config and 'api_key' in config['comicvine']:
                config['comicvine']['api_key'] = '***CENSORED***'

            zip_file.writestr("config.json", json.dumps(config, indent=2))

        # Información del sistema
        system_info = {
            'platform': platform.platform(),
            'python_version': sys.version,
            'timestamp': datetime.now().isoformat()
        }
        zip_file.writestr("system_info.json", json.dumps(system_info, indent=2))

    print(f"📦 Logs recolectados en: {output_file}")
    return output_file
```

## 📞 Obtener Ayuda

### Recursos de Soporte

#### Documentación y Comunidad
- **📚 Documentación**: [docs.babelcomics.com](https://docs.babelcomics.com)
- **🐛 Reportar bugs**: [github.com/babelcomics4/issues](https://github.com/babelcomics4/issues)
- **💬 Foro de usuarios**: [forum.babelcomics.com](https://forum.babelcomics.com)
- **💡 Solicitar features**: [github.com/babelcomics4/discussions](https://github.com/babelcomics4/discussions)

#### Información para Reportes de Bugs
Cuando reportes un problema, incluye:

1. **Versión de Babelcomics4**: `babelcomics4 --version`
2. **Sistema operativo**: `uname -a` (Linux/macOS) o `systeminfo` (Windows)
3. **Versión de Python**: `python --version`
4. **Logs relevantes**: Usar el script de recolección de logs
5. **Pasos para reproducir**: Descripción detallada
6. **Comportamiento esperado vs actual**

#### Template para Issues
```markdown
## Descripción del Problema
[Descripción clara y concisa del problema]

## Pasos para Reproducir
1. Ir a '...'
2. Hacer click en '....'
3. Ejecutar '....'
4. Ver error

## Comportamiento Esperado
[Qué esperabas que pasara]

## Comportamiento Actual
[Qué pasó realmente]

## Información del Sistema
- Babelcomics4 versión: [ej. 4.0.1]
- OS: [ej. Ubuntu 22.04, Windows 11, macOS 13]
- Python: [ej. 3.11.2]

## Logs Adicionales
[Adjuntar archivo de logs o pegar logs relevantes]

## Capturas de Pantalla
[Si aplica, añadir capturas de pantalla]
```

---

**¿Tienes más preguntas?** 👉 [FAQ](faq.md)