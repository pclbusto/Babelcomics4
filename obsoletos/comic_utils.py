#!/usr/bin/env python3

import os
import sys
import json
from pathlib import Path
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gdk


class ConfigManager:
    """Gestor de configuración de la aplicación"""
    
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "comic-manager"
        self.config_file = self.config_dir / "config.json"
        self.default_config = {
            "database_path": "comics.db",
            "thumbnail_cache_path": "data/thumbnails",
            "default_view": "grid",
            "items_per_page": 50,
            "window_width": 1200,
            "window_height": 800,
            "sidebar_width": 250,
            "dark_theme": False,
            "auto_scan_directories": [],
            "supported_formats": [".cbr", ".cbz", ".pdf", ".zip", ".rar"],
            "last_section": "comics",
            "search_history": [],
            "max_search_history": 10
        }
        
        self.config = self.load_config()
        
    def ensure_config_dir(self):
        """Asegurar que el directorio de configuración existe"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
    def load_config(self):
        """Cargar configuración desde archivo"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Fusionar con configuración por defecto para nuevas opciones
                    merged_config = self.default_config.copy()
                    merged_config.update(config)
                    return merged_config
            except Exception as e:
                print(f"Error cargando configuración: {e}")
                
        return self.default_config.copy()
        
    def save_config(self):
        """Guardar configuración a archivo"""
        try:
            self.ensure_config_dir()
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando configuración: {e}")
            
    def get(self, key, default=None):
        """Obtener valor de configuración"""
        return self.config.get(key, default)
        
    def set(self, key, value):
        """Establecer valor de configuración"""
        self.config[key] = value
        
    def add_to_search_history(self, query):
        """Añadir consulta al historial de búsqueda"""
        if not query.strip():
            return
            
        history = self.config.get("search_history", [])
        
        # Remover si ya existe
        if query in history:
            history.remove(query)
            
        # Añadir al inicio
        history.insert(0, query)
        
        # Limitar tamaño del historial
        max_history = self.config.get("max_search_history", 10)
        self.config["search_history"] = history[:max_history]
        

class ImageLoader:
    """Cargador de imágenes con caché y redimensionado"""
    
    def __init__(self, cache_size=100):
        self.cache = {}
        self.cache_size = cache_size
        
    def load_image(self, path, width=None, height=None):
        """Cargar imagen con caché opcional"""
        if not path or not os.path.exists(path):
            return None
            
        cache_key = f"{path}_{width}_{height}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        try:
            from gi.repository import GdkPixbuf, Gdk
            
            if width and height:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    path, width, height, True
                )
            else:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(path)
                
            texture = Gdk.Texture.new_for_pixbuf(pixbuf)
            
            # Añadir al caché
            if len(self.cache) >= self.cache_size:
                # Remover elemento más antiguo
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                
            self.cache[cache_key] = texture
            return texture
            
        except Exception as e:
            print(f"Error cargando imagen {path}: {e}")
            return None
            
    def clear_cache(self):
        """Limpiar caché de imágenes"""
        self.cache.clear()


class FileUtils:
    """Utilidades para manejo de archivos"""
    
    COMIC_EXTENSIONS = {'.cbr', '.cbz', '.pdf', '.zip', '.rar', '.7z'}
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    
    @staticmethod
    def is_comic_file(filepath):
        """Verificar si un archivo es un comic"""
        return Path(filepath).suffix.lower() in FileUtils.COMIC_EXTENSIONS
        
    @staticmethod
    def is_image_file(filepath):
        """Verificar si un archivo es una imagen"""
        return Path(filepath).suffix.lower() in FileUtils.IMAGE_EXTENSIONS
        
    @staticmethod
    def get_file_size_readable(filepath):
        """Obtener tamaño de archivo en formato legible"""
        try:
            size = os.path.getsize(filepath)
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        except:
            return "Unknown"
            
    @staticmethod
    def scan_directory_for_comics(directory):
        """Escanear directorio buscando archivos de comics"""
        comics = []
        directory = Path(directory)
        
        if not directory.exists():
            return comics
            
        for file_path in directory.rglob("*"):
            if file_path.is_file() and FileUtils.is_comic_file(file_path):
                comics.append(str(file_path))
                
        return sorted(comics)


class ToastManager:
    """Gestor de notificaciones toast para la aplicación"""
    
    def __init__(self, window):
        self.window = window
        self.toast_overlay = None
        self.setup_toast_overlay()
        
    def setup_toast_overlay(self):
        """Configurar el overlay para toasts"""
        # Si la ventana ya tiene un ToastOverlay, usarlo
        if hasattr(self.window, 'toast_overlay'):
            self.toast_overlay = self.window.toast_overlay
        else:
            # Crear nuevo ToastOverlay
            self.toast_overlay = Adw.ToastOverlay()
            
    def show_toast(self, message, timeout=3):
        """Mostrar notificación toast"""
        if self.toast_overlay:
            toast = Adw.Toast.new(message)
            toast.set_timeout(timeout)
            self.toast_overlay.add_toast(toast)
        else:
            print(f"Toast: {message}")  # Fallback a consola
            
    def show_success(self, message):
        """Mostrar toast de éxito"""
        self.show_toast(f"✓ {message}")
        
    def show_error(self, message):
        """Mostrar toast de error"""
        self.show_toast(f"✗ {message}", timeout=5)
        
    def show_warning(self, message):
        """Mostrar toast de advertencia"""
        self.show_toast(f"⚠ {message}", timeout=4)


class KeyboardShortcuts:
    """Gestor de atajos de teclado"""
    
    def __init__(self, window):
        self.window = window
        self.setup_shortcuts()
        
    def setup_shortcuts(self):
        """Configurar atajos de teclado"""
        # Crear controlador de teclado
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self.on_key_pressed)
        self.window.add_controller(key_controller)
        
    def on_key_pressed(self, controller, keyval, keycode, state):
        """Manejar teclas presionadas"""
        # Ctrl+F - Enfocar búsqueda
        if keyval == Gdk.KEY_f and state & Gdk.ModifierType.CONTROL_MASK:
            if hasattr(self.window, 'quick_search_bar'):
                self.window.quick_search_bar.search_entry.grab_focus()
            return True
            
        # Escape - Limpiar búsqueda
        if keyval == Gdk.KEY_Escape:
            if hasattr(self.window, 'quick_search_bar'):
                self.window.quick_search_bar.search_entry.set_text("")
            return True
            
        # F5 - Actualizar
        if keyval == Gdk.KEY_F5:
            if hasattr(self.window, 'load_section_data'):
                self.window.load_section_data(self.window.current_section)
            return True
            
        # Ctrl+1, Ctrl+2, etc. - Cambiar sección
        if state & Gdk.ModifierType.CONTROL_MASK:
            section_keys = {
                Gdk.KEY_1: "comics",
                Gdk.KEY_2: "volumes", 
                Gdk.KEY_3: "publishers",
                Gdk.KEY_4: "arcs"
            }
            
            if keyval in section_keys:
                section = section_keys[keyval]
                if hasattr(self.window, 'nav_rows'):
                    # Simular click en la navegación
                    nav_list = self.window.nav_rows[section].get_parent()
                    nav_list.select_row(self.window.nav_rows[section])
                return True
                
        return False


class DatabaseManager:
    """Gestor de base de datos con utilidades adicionales"""
    
    def __init__(self, db_path="comics.db"):
        self.db_path = db_path
        self.engine = None
        self.session = None
        
    def connect(self):
        """Conectar a la base de datos"""
        try:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            from entidades import Base
            
            self.engine = create_engine(f'sqlite:///{self.db_path}', echo=False)
            Base.metadata.create_all(self.engine)
            Session = sessionmaker(bind=self.engine)
            self.session = Session()
            return True
        except Exception as e:
            print(f"Error conectando a la base de datos: {e}")
            return False
            
    def disconnect(self):
        """Desconectar de la base de datos"""
        if self.session:
            self.session.close()
            
    def backup_database(self, backup_path):
        """Crear backup de la base de datos"""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            return True
        except Exception as e:
            print(f"Error creando backup: {e}")
            return False
            
    def get_stats(self):
        """Obtener estadísticas de la base de datos"""
        if not self.session:
            return {}
            
        try:
            from entidades.comicbook_model import Comicbook
            from entidades.volume_model import Volume
            from entidades.publisher_model import Publisher
            
            stats = {
                "comics_count": self.session.query(Comicbook).count(),
                "volumes_count": self.session.query(Volume).count(),
                "publishers_count": self.session.query(Publisher).count(),
                "classified_comics": self.session.query(Comicbook).filter(
                    Comicbook.id_comicbook_info != ''
                ).count()
            }
            
            # Calcular porcentaje de clasificación
            if stats["comics_count"] > 0:
                stats["classification_percentage"] = (
                    stats["classified_comics"] / stats["comics_count"]
                ) * 100
            else:
                stats["classification_percentage"] = 0
                
            return stats
            
        except Exception as e:
            print(f"Error obteniendo estadísticas: {e}")
            return {}


class ProgressDialog(Adw.Dialog):
    """Diálogo de progreso para operaciones largas"""
    
    def __init__(self, parent_window, title="Procesando..."):
        super().__init__()
        self.set_title(title)
        self.set_modal(True)
        self.set_default_size(400, 150)
        
        # No permitir cerrar el diálogo durante la operación
        self.set_can_close(False)
        
        self.create_content()
        
    def create_content(self):
        """Crear contenido del diálogo"""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        main_box.set_margin_top(24)
        main_box.set_margin_bottom(24)
        main_box.set_margin_start(24)
        main_box.set_margin_end(24)
        
        # Label de estado
        self.status_label = Gtk.Label(label="Inicializando...")
        self.status_label.set_wrap(True)
        main_box.append(self.status_label)
        
        # Barra de progreso
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        main_box.append(self.progress_bar)
        
        # Botón cancelar (opcional)
        self.cancel_button = Gtk.Button.new_with_label("Cancelar")
        self.cancel_button.add_css_class("destructive-action")
        self.cancel_button.set_halign(Gtk.Align.CENTER)
        self.cancel_button.connect("clicked", self.on_cancel_clicked)
        main_box.append(self.cancel_button)
        
        self.set_child(main_box)
        
        # Flag para cancelación
        self.cancelled = False
        
    def update_progress(self, progress, status_text=""):
        """Actualizar progreso (0.0 a 1.0)"""
        GLib.idle_add(self._update_progress_ui, progress, status_text)
        
    def _update_progress_ui(self, progress, status_text):
        """Actualizar UI del progreso (ejecutar en hilo principal)"""
        self.progress_bar.set_fraction(progress)
        if status_text:
            self.status_label.set_text(status_text)
        return False  # No repetir
        
    def on_cancel_clicked(self, button):
        """Manejar cancelación"""
        self.cancelled = True
        self.cancel_button.set_sensitive(False)
        self.status_label.set_text("Cancelando...")
        
    def finish(self, success=True, message=""):
        """Finalizar el diálogo"""
        def _finish():
            if success:
                self.set_can_close(True)
                self.close()
            else:
                self.status_label.set_text(message or "Error en la operación")
                self.cancel_button.set_label("Cerrar")
                self.cancel_button.set_sensitive(True)
                self.cancel_button.remove_css_class("destructive-action")
            return False
            
        GLib.idle_add(_finish)


class ComicScanner:
    """Escáner de archivos de comics"""
    
    def __init__(self, database_manager, progress_callback=None):
        self.db_manager = database_manager
        self.progress_callback = progress_callback
        
    def scan_directories(self, directories, update_existing=False):
        """Escanear directorios en busca de comics"""
        if not self.db_manager.session:
            return False
            
        try:
            from entidades.comicbook_model import Comicbook
            
            all_files = []
            
            # Recopilar archivos de todos los directorios
            for directory in directories:
                if self.progress_callback:
                    self.progress_callback(0, f"Escaneando {directory}...")
                    
                files = FileUtils.scan_directory_for_comics(directory)
                all_files.extend(files)
                
            if not all_files:
                return True
                
            # Obtener comics existentes si no se van a actualizar
            existing_paths = set()
            if not update_existing:
                existing = self.db_manager.session.query(Comicbook.path).all()
                existing_paths = {path[0] for path in existing}
                
            # Procesar archivos
            new_comics = 0
            for i, file_path in enumerate(all_files):
                if self.progress_callback:
                    progress = i / len(all_files)
                    self.progress_callback(
                        progress, 
                        f"Procesando {os.path.basename(file_path)}..."
                    )
                    
                # Verificar si ya existe
                if not update_existing and file_path in existing_paths:
                    continue
                    
                # Crear nuevo comic
                comic = Comicbook(
                    path=file_path,
                    id_comicbook_info='',
                    calidad=0,
                    en_papelera=False
                )
                
                self.db_manager.session.add(comic)
                new_comics += 1
                
                # Commit cada 100 items
                if new_comics % 100 == 0:
                    self.db_manager.session.commit()
                    
            # Commit final
            self.db_manager.session.commit()
            
            if self.progress_callback:
                self.progress_callback(
                    1.0, 
                    f"Completado: {new_comics} comics añadidos"
                )
                
            return True
            
        except Exception as e:
            print(f"Error escaneando directorios: {e}")
            if self.progress_callback:
                self.progress_callback(1.0, f"Error: {e}")
            return False


# Funciones de utilidad globales
def format_file_size(size_bytes):
    """Formatear tamaño de archivo"""
    if size_bytes == 0:
        return "0 B"
        
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"


def get_comic_reader_command():
    """Obtener comando para abrir comics según el sistema"""
    import platform
    
    system = platform.system().lower()
    
    if system == "linux":
        # Buscar lectores comunes en Linux
        readers = ["evince", "okular", "atril", "mcomix", "qcomicbook"]
        for reader in readers:
            import shutil
            if shutil.which(reader):
                return reader
                
    elif system == "windows":
        return "start"  # Usar aplicación predeterminada
        
    elif system == "darwin":  # macOS
        return "open"  # Usar aplicación predeterminada
        
    return None


def open_comic_file(file_path):
    """Abrir archivo de comic con el lector predeterminado"""
    reader_command = get_comic_reader_command()
    
    if not reader_command:
        print("No se encontró un lector de comics")
        return False
        
    try:
        import subprocess
        subprocess.Popen([reader_command, file_path])
        return True
    except Exception as e:
        print(f"Error abriendo comic: {e}")
        return False