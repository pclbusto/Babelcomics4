#!/usr/bin/env python3
"""
Helper para acceder a la configuración de la aplicación desde cualquier parte del código.
"""

import sys
from pathlib import Path

# Agregar el directorio padre al path para importar entidades
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import sessionmaker
from entidades import engine
from entidades.setup_model import Setup
from entidades.setup_directorio_model import SetupDirectorio

class ConfigHelper:
    """Helper para acceso fácil a la configuración de la aplicación"""

    @staticmethod
    def get_setup_config():
        """Obtener la configuración de setup de la BD"""
        try:
            Session = sessionmaker(bind=engine)
            session = Session()

            config = session.query(Setup).first()

            # Cerrar sesión (los datos quedan en el objeto)
            session.close()

            return config
        except Exception as e:
            print(f"❌ Error obteniendo configuración: {e}")
            return None

    @staticmethod
    def get_scan_directories():
        """Obtener lista de directorios configurados para escanear"""
        try:
            Session = sessionmaker(bind=engine)
            session = Session()

            # Obtener directorios activos (para escaneo)
            scan_dirs = session.query(SetupDirectorio).filter_by(activo=True).all()

            # Convertir a lista de paths
            directories = [d.directorio_path for d in scan_dirs if d.is_valid_path()]

            session.close()

            return directories
        except Exception as e:
            print(f"❌ Error obteniendo directorios de escaneo: {e}")
            return []

    @staticmethod
    def get_api_key():
        """Obtener API key desencriptada"""
        config = ConfigHelper.get_setup_config()
        if config:
            return config.get_api_key()
        return ""

    @staticmethod
    def get_thumbnail_size():
        """Obtener tamaño configurado para thumbnails"""
        config = ConfigHelper.get_setup_config()
        if config:
            return config.thumbnail_size
        return 200  # Valor por defecto

    @staticmethod
    def get_items_per_batch():
        """Obtener cantidad de items por lote para lazy loading"""
        config = ConfigHelper.get_setup_config()
        if config:
            return config.items_per_batch
        return 20  # Valor por defecto

    @staticmethod
    def get_workers_count():
        """Obtener cantidad de workers concurrentes"""
        config = ConfigHelper.get_setup_config()
        if config:
            return config.workers_concurrentes
        return 5  # Valor por defecto

    @staticmethod
    def get_rate_limit_interval():
        """Obtener intervalo entre requests a API"""
        config = ConfigHelper.get_setup_config()
        if config:
            return config.rate_limit_interval
        return 0.5  # Valor por defecto

    @staticmethod
    def is_dark_mode():
        """Verificar si está activado el modo oscuro"""
        config = ConfigHelper.get_setup_config()
        if config:
            return config.modo_oscuro
        return False  # Valor por defecto

    @staticmethod
    def should_cache_thumbnails():
        """Verificar si debe usar cache de thumbnails"""
        config = ConfigHelper.get_setup_config()
        if config:
            return config.cache_thumbnails
        return True  # Valor por defecto

    @staticmethod
    def should_auto_cleanup():
        """Verificar si debe hacer limpieza automática"""
        config = ConfigHelper.get_setup_config()
        if config:
            return config.limpieza_automatica
        return True  # Valor por defecto

# Función de conveniencia para importar fácilmente
def get_scan_directories():
    """Función rápida para obtener directorios de escaneo"""
    return ConfigHelper.get_scan_directories()

def get_api_key():
    """Función rápida para obtener API key"""
    return ConfigHelper.get_api_key()

if __name__ == "__main__":
    # Test del helper
    print("🔧 Testing ConfigHelper...")

    print(f"📁 Directorios de escaneo: {get_scan_directories()}")
    print(f"🔑 API Key: {'***' if get_api_key() else 'vacío'}")
    print(f"🖼️  Thumbnail size: {ConfigHelper.get_thumbnail_size()}px")
    print(f"📦 Items per batch: {ConfigHelper.get_items_per_batch()}")
    print(f"⚡ Workers: {ConfigHelper.get_workers_count()}")
    print(f"⏱️  Rate limit: {ConfigHelper.get_rate_limit_interval()}s")
    print(f"🌙 Dark mode: {ConfigHelper.is_dark_mode()}")
    print(f"💾 Cache thumbnails: {ConfigHelper.should_cache_thumbnails()}")
    print(f"🧹 Auto cleanup: {ConfigHelper.should_auto_cleanup()}")

    print("✅ ConfigHelper funcionando correctamente!")