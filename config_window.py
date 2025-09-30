#!/usr/bin/env python3
"""
Ventana de Configuración para Babelcomics4
Maneja settings globales de la aplicación incluyendo ComicVine API
"""

import gi
import os
import sys
import shutil
import requests
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib, Gio


class ConfigWindow(Adw.PreferencesWindow):
    """Ventana de configuración usando Adwaita PreferencesWindow"""

    def __init__(self, parent_window=None):
        super().__init__()

        # Configuración básica de la ventana
        self.set_title("Configuración de Babelcomics4")
        self.set_default_size(600, 500)
        self.set_modal(True)

        if parent_window:
            self.set_transient_for(parent_window)

        # Crear las páginas de configuración
        self.setup_pages()

    def setup_pages(self):
        """Configurar las páginas de preferencias"""

        # Página General
        general_page = Adw.PreferencesPage()
        general_page.set_title("General")
        general_page.set_icon_name("preferences-system-symbolic")

        # Grupo ComicVine API
        self.setup_comicvine_group(general_page)

        # Grupo Directorios
        self.setup_directories_group(general_page)

        # Grupo Interface
        self.setup_interface_group(general_page)

        self.add(general_page)

        # Página Avanzada
        advanced_page = Adw.PreferencesPage()
        advanced_page.set_title("Avanzado")
        advanced_page.set_icon_name("applications-engineering-symbolic")

        # Grupo Base de Datos
        self.setup_database_group(advanced_page)

        # Grupo Rendimiento
        self.setup_performance_group(advanced_page)

        self.add(advanced_page)

    def setup_comicvine_group(self, page):
        """Configurar grupo de ComicVine API"""
        comicvine_group = Adw.PreferencesGroup()
        comicvine_group.set_title("ComicVine API")
        comicvine_group.set_description("Configuración para la integración con ComicVine. Obtén tu API Key en comicvine.gamespot.com")

        # API Key
        self.api_key_row = Adw.PasswordEntryRow()
        self.api_key_row.set_title("API Key de ComicVine")
        # PasswordEntryRow no tiene set_subtitle, usar descripción del grupo

        # Cargar API key actual si existe
        current_api_key = self.get_current_api_key()
        if current_api_key:
            self.api_key_row.set_text(current_api_key)

        comicvine_group.add(self.api_key_row)

        # Botón para validar conexión
        validate_row = Adw.ActionRow()
        validate_row.set_title("Validar Conexión")
        validate_row.set_subtitle("Probar la conexión con ComicVine")

        validate_button = Gtk.Button()
        validate_button.set_label("Probar")
        validate_button.set_valign(Gtk.Align.CENTER)
        validate_button.add_css_class("suggested-action")
        validate_button.connect("clicked", self.on_validate_api_key)
        validate_row.add_suffix(validate_button)

        # Status de la conexión
        self.connection_status = Gtk.Label()
        self.connection_status.set_halign(Gtk.Align.START)
        validate_row.add_suffix(self.connection_status)

        comicvine_group.add(validate_row)

        # Rate limiting
        rate_limit_row = Adw.SpinRow()
        rate_limit_row.set_title("Intervalo entre requests")
        rate_limit_row.set_subtitle("Segundos entre llamadas a la API (mín: 0.5)")
        rate_limit_adjustment = Gtk.Adjustment(value=0.5, lower=0.5, upper=5.0, step_increment=0.1)
        rate_limit_row.set_adjustment(rate_limit_adjustment)
        rate_limit_row.set_digits(1)

        comicvine_group.add(rate_limit_row)

        page.add(comicvine_group)

    def setup_directories_group(self, page):
        """Configurar grupo de directorios"""
        dirs_group = Adw.PreferencesGroup()
        dirs_group.set_title("Directorios")
        dirs_group.set_description("Configuración de rutas y directorios")

        # Directorio de datos
        data_dir_row = Adw.ActionRow()
        data_dir_row.set_title("Directorio de datos")
        data_dir_row.set_subtitle(str(Path("data").absolute()))

        data_button = Gtk.Button()
        data_button.set_icon_name("folder-open-symbolic")
        data_button.set_valign(Gtk.Align.CENTER)
        data_button.connect("clicked", self.on_open_data_directory)
        data_dir_row.add_suffix(data_button)

        dirs_group.add(data_dir_row)

        # Directorio de thumbnails
        thumb_dir_row = Adw.ActionRow()
        thumb_dir_row.set_title("Directorio de thumbnails")
        thumb_dir_row.set_subtitle(str(Path("data/thumbnails").absolute()))

        thumb_button = Gtk.Button()
        thumb_button.set_icon_name("folder-open-symbolic")
        thumb_button.set_valign(Gtk.Align.CENTER)
        thumb_button.connect("clicked", self.on_open_thumbnails_directory)
        thumb_dir_row.add_suffix(thumb_button)

        dirs_group.add(thumb_dir_row)

        page.add(dirs_group)

    def setup_interface_group(self, page):
        """Configurar grupo de interfaz"""
        interface_group = Adw.PreferencesGroup()
        interface_group.set_title("Interfaz")
        interface_group.set_description("Configuración de la interfaz de usuario")

        # Modo oscuro/claro
        theme_row = Adw.ComboRow()
        theme_row.set_title("Tema")
        theme_row.set_subtitle("Apariencia de la aplicación")

        theme_model = Gtk.StringList()
        theme_model.append("Seguir sistema")
        theme_model.append("Claro")
        theme_model.append("Oscuro")
        theme_row.set_model(theme_model)
        theme_row.set_selected(0)

        interface_group.add(theme_row)

        # Tamaño de thumbnails
        thumbnail_size_row = Adw.SpinRow()
        thumbnail_size_row.set_title("Tamaño de thumbnails")
        thumbnail_size_row.set_subtitle("Píxeles para las miniaturas")
        size_adjustment = Gtk.Adjustment(value=200, lower=100, upper=400, step_increment=10)
        thumbnail_size_row.set_adjustment(size_adjustment)

        interface_group.add(thumbnail_size_row)

        # Items por página
        items_per_page_row = Adw.SpinRow()
        items_per_page_row.set_title("Items por lote")
        items_per_page_row.set_subtitle("Cantidad de items a cargar por vez")
        items_adjustment = Gtk.Adjustment(value=20, lower=10, upper=100, step_increment=5)
        items_per_page_row.set_adjustment(items_adjustment)

        interface_group.add(items_per_page_row)

        page.add(interface_group)

    def setup_database_group(self, page):
        """Configurar grupo de base de datos"""
        db_group = Adw.PreferencesGroup()
        db_group.set_title("Base de Datos")
        db_group.set_description("Configuración y mantenimiento de la base de datos")

        # Información de la BD
        db_info_row = Adw.ActionRow()
        db_info_row.set_title("Base de datos")

        db_path = Path("data/babelcomics.db")
        if db_path.exists():
            size_mb = db_path.stat().st_size / (1024 * 1024)
            db_info_row.set_subtitle(f"{db_path} ({size_mb:.1f} MB)")
        else:
            db_info_row.set_subtitle("No encontrada")

        # Botón para abrir directorio de la BD
        db_button = Gtk.Button()
        db_button.set_icon_name("folder-open-symbolic")
        db_button.set_valign(Gtk.Align.CENTER)
        db_button.connect("clicked", self.on_open_database_directory)
        db_info_row.add_suffix(db_button)

        db_group.add(db_info_row)

        # Backup
        backup_row = Adw.ActionRow()
        backup_row.set_title("Backup de base de datos")
        backup_row.set_subtitle("Crear copia de seguridad")

        backup_button = Gtk.Button()
        backup_button.set_label("Crear Backup")
        backup_button.set_valign(Gtk.Align.CENTER)
        backup_button.connect("clicked", self.on_create_backup)
        backup_row.add_suffix(backup_button)

        db_group.add(backup_row)

        # Optimizar BD
        optimize_row = Adw.ActionRow()
        optimize_row.set_title("Optimizar base de datos")
        optimize_row.set_subtitle("Ejecutar VACUUM para optimizar")

        optimize_button = Gtk.Button()
        optimize_button.set_label("Optimizar")
        optimize_button.set_valign(Gtk.Align.CENTER)
        optimize_button.connect("clicked", self.on_optimize_database)
        optimize_row.add_suffix(optimize_button)

        db_group.add(optimize_row)

        page.add(db_group)

    def setup_performance_group(self, page):
        """Configurar grupo de rendimiento"""
        perf_group = Adw.PreferencesGroup()
        perf_group.set_title("Rendimiento")
        perf_group.set_description("Configuraciones que afectan el rendimiento")

        # Workers concurrentes
        workers_row = Adw.SpinRow()
        workers_row.set_title("Workers concurrentes")
        workers_row.set_subtitle("Número de hilos para descargas paralelas")
        workers_adjustment = Gtk.Adjustment(value=5, lower=1, upper=20, step_increment=1)
        workers_row.set_adjustment(workers_adjustment)

        perf_group.add(workers_row)

        # Cache de thumbnails
        cache_row = Adw.SwitchRow()
        cache_row.set_title("Cache de thumbnails")
        cache_row.set_subtitle("Mantener thumbnails en memoria")
        cache_row.set_active(True)

        perf_group.add(cache_row)

        # Limpieza automática
        cleanup_row = Adw.SwitchRow()
        cleanup_row.set_title("Limpieza automática")
        cleanup_row.set_subtitle("Limpiar archivos temporales al cerrar")
        cleanup_row.set_active(True)

        perf_group.add(cleanup_row)

        page.add(perf_group)

        # Grupo Thumbnails
        self.setup_thumbnails_group(page)

    def setup_thumbnails_group(self, page):
        """Configurar grupo de gestión de thumbnails"""
        thumbnails_group = Adw.PreferencesGroup()
        thumbnails_group.set_title("Thumbnails")
        thumbnails_group.set_description("Gestión y regeneración de miniaturas de covers")

        # Regenerar thumbnails de volúmenes
        self.regen_row = Adw.ActionRow()
        self.regen_row.set_title("Regenerar Covers de Volúmenes")
        self.regen_row.set_subtitle("Descargar nuevamente todas las portadas de volúmenes desde ComicVine")

        self.regen_button = Gtk.Button()
        self.regen_button.set_label("Regenerar")
        self.regen_button.set_valign(Gtk.Align.CENTER)
        self.regen_button.add_css_class("destructive-action")
        self.regen_button.connect("clicked", self.on_regenerate_thumbnails)
        self.regen_row.add_suffix(self.regen_button)

        # Progress bar para regeneración (inicialmente oculta)
        self.regen_progress = Gtk.ProgressBar()
        self.regen_progress.set_visible(False)
        self.regen_progress.set_valign(Gtk.Align.CENTER)
        self.regen_progress.set_hexpand(True)
        self.regen_row.add_suffix(self.regen_progress)

        # Label de estado
        self.regen_status = Gtk.Label()
        self.regen_status.set_visible(False)
        self.regen_status.set_halign(Gtk.Align.START)
        self.regen_status.add_css_class("dim-label")
        self.regen_row.add_suffix(self.regen_status)

        thumbnails_group.add(self.regen_row)

        # Limpiar cache de thumbnails
        clear_cache_row = Adw.ActionRow()
        clear_cache_row.set_title("Limpiar Cache de Thumbnails")
        clear_cache_row.set_subtitle("Eliminar todas las miniaturas almacenadas localmente")

        clear_button = Gtk.Button()
        clear_button.set_label("Limpiar")
        clear_button.set_valign(Gtk.Align.CENTER)
        clear_button.add_css_class("destructive-action")
        clear_button.connect("clicked", self.on_clear_thumbnail_cache)
        clear_cache_row.add_suffix(clear_button)

        thumbnails_group.add(clear_cache_row)

        # Estadísticas de thumbnails
        stats_row = Adw.ActionRow()
        stats_row.set_title("Estadísticas de Thumbnails")

        # Calcular estadísticas
        stats_text = self.get_thumbnail_stats()
        stats_row.set_subtitle(stats_text)

        refresh_stats_button = Gtk.Button()
        refresh_stats_button.set_icon_name("view-refresh-symbolic")
        refresh_stats_button.set_valign(Gtk.Align.CENTER)
        refresh_stats_button.set_tooltip_text("Actualizar estadísticas")
        refresh_stats_button.connect("clicked", self.on_refresh_thumbnail_stats, stats_row)
        stats_row.add_suffix(refresh_stats_button)

        thumbnails_group.add(stats_row)

        page.add(thumbnails_group)

    def get_current_api_key(self):
        """Obtener API key actual desde el archivo"""
        try:
            from helpers.comicvine_cliente import ComicVineClient
            # Intentar leer desde el archivo directamente
            with open("helpers/comicvine_cliente.py", "r") as f:
                content = f.read()
                # Buscar la línea con MY_API_KEY
                for line in content.split('\n'):
                    if 'MY_API_KEY = ' in line and not line.strip().startswith('#'):
                        # Extraer la clave entre comillas
                        start = line.find("'") + 1
                        end = line.rfind("'")
                        if start > 0 and end > start:
                            api_key = line[start:end]
                            if api_key != 'TU_API_KEY':
                                return api_key
        except Exception as e:
            print(f"Error leyendo API key: {e}")
        return ""

    def on_validate_api_key(self, button):
        """Validar la API key ingresada"""
        api_key = self.api_key_row.get_text().strip()

        if not api_key:
            self.connection_status.set_markup('<span color="red">❌ API Key vacía</span>')
            return

        # Mostrar spinner mientras valida
        self.connection_status.set_markup('<span color="blue">🔄 Validando...</span>')

        # Validar en un hilo separado
        def validate_worker():
            try:
                from helpers.comicvine_cliente import ComicVineClient
                client = ComicVineClient(api_key)

                # Hacer una llamada simple para validar
                result = client.get_publishers(limit=1)

                if result:
                    GLib.idle_add(lambda: self.connection_status.set_markup(
                        '<span color="green">✅ Conexión exitosa</span>'
                    ))

                    # Guardar la API key
                    GLib.idle_add(lambda: self.save_api_key(api_key))
                else:
                    GLib.idle_add(lambda: self.connection_status.set_markup(
                        '<span color="red">❌ Error de conexión</span>'
                    ))

            except Exception as e:
                GLib.idle_add(lambda: self.connection_status.set_markup(
                    f'<span color="red">❌ Error: {str(e)[:30]}...</span>'
                ))

        import threading
        threading.Thread(target=validate_worker, daemon=True).start()

    def save_api_key(self, api_key):
        """Guardar API key en el archivo"""
        try:
            # Leer el archivo actual
            with open("helpers/comicvine_cliente.py", "r") as f:
                content = f.read()

            # Reemplazar la línea de MY_API_KEY
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'MY_API_KEY = ' in line and not line.strip().startswith('#'):
                    lines[i] = f"    MY_API_KEY = '{api_key}'"
                    break

            # Escribir de vuelta
            with open("helpers/comicvine_cliente.py", "w") as f:
                f.write('\n'.join(lines))

            print(f"API Key guardada exitosamente")

        except Exception as e:
            print(f"Error guardando API key: {e}")

    def on_open_data_directory(self, button):
        """Abrir directorio de datos"""
        self.open_directory("data")

    def on_open_thumbnails_directory(self, button):
        """Abrir directorio de thumbnails"""
        self.open_directory("data/thumbnails")

    def on_open_database_directory(self, button):
        """Abrir directorio de la base de datos"""
        self.open_directory("data")

    def open_directory(self, path):
        """Abrir un directorio en el explorador de archivos"""
        try:
            import subprocess
            abs_path = Path(path).absolute()

            if abs_path.exists():
                if sys.platform == "linux":
                    subprocess.run(["xdg-open", str(abs_path)])
                elif sys.platform == "darwin":
                    subprocess.run(["open", str(abs_path)])
                elif sys.platform == "win32":
                    subprocess.run(["explorer", str(abs_path)])
            else:
                print(f"Directorio no existe: {abs_path}")

        except Exception as e:
            print(f"Error abriendo directorio: {e}")

    def on_create_backup(self, button):
        """Crear backup de la base de datos"""
        try:
            from datetime import datetime
            import shutil

            # Crear directorio de backups si no existe
            backup_dir = Path("backup")
            backup_dir.mkdir(exist_ok=True)

            # Nombre del backup con timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"babelcomics_backup_{timestamp}.db"
            backup_path = backup_dir / backup_filename

            # Copiar la base de datos
            db_path = Path("data/babelcomics.db")
            if db_path.exists():
                shutil.copy2(db_path, backup_path)
                print(f"Backup creado: {backup_path}")

                # Mostrar toast o dialog de confirmación
                self.show_success_message(f"Backup creado exitosamente:\n{backup_filename}")
            else:
                self.show_error_message("No se encontró la base de datos")

        except Exception as e:
            print(f"Error creando backup: {e}")
            self.show_error_message(f"Error creando backup: {e}")

    def on_optimize_database(self, button):
        """Optimizar la base de datos"""
        try:
            from sqlalchemy import create_engine

            db_path = "data/babelcomics.db"
            engine = create_engine(f'sqlite:///{db_path}')

            with engine.connect() as connection:
                connection.execute("VACUUM;")

            print("Base de datos optimizada")
            self.show_success_message("Base de datos optimizada exitosamente")

        except Exception as e:
            print(f"Error optimizando base de datos: {e}")
            self.show_error_message(f"Error optimizando base de datos: {e}")

    def show_success_message(self, message):
        """Mostrar mensaje de éxito"""
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading("Operación exitosa")
        dialog.set_body(message)
        dialog.add_response("ok", "OK")
        dialog.set_default_response("ok")
        dialog.present()

    def show_error_message(self, message):
        """Mostrar mensaje de error"""
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading("Error")
        dialog.set_body(message)
        dialog.add_response("ok", "OK")
        dialog.set_default_response("ok")
        dialog.set_response_appearance("ok", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.present()

    def get_thumbnail_stats(self):
        """Obtener estadísticas de thumbnails"""
        try:
            thumb_dir = Path("data/thumbnails/volumes")
            if thumb_dir.exists():
                volume_thumbs = len(list(thumb_dir.glob("*.jpg")))
                total_size = sum(f.stat().st_size for f in thumb_dir.glob("*.jpg"))
                size_mb = total_size / (1024 * 1024)
                return f"{volume_thumbs} covers, {size_mb:.1f} MB"
            else:
                return "0 covers, 0 MB"
        except Exception as e:
            return f"Error: {e}"

    def on_refresh_thumbnail_stats(self, button, stats_row):
        """Actualizar estadísticas de thumbnails"""
        stats_text = self.get_thumbnail_stats()
        stats_row.set_subtitle(stats_text)

    def on_clear_thumbnail_cache(self, button):
        """Limpiar cache de thumbnails"""
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading("Limpiar Cache de Thumbnails")
        dialog.set_body("¿Estás seguro de que quieres eliminar todas las miniaturas?\nSe regenerarán automáticamente cuando sea necesario.")
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("clear", "Limpiar")
        dialog.set_response_appearance("clear", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.connect("response", self.on_clear_cache_confirmed)
        dialog.present()

    def on_clear_cache_confirmed(self, dialog, response):
        """Confirmar limpieza de cache"""
        if response == "clear":
            try:
                thumb_dir = Path("data/thumbnails")
                if thumb_dir.exists():
                    shutil.rmtree(thumb_dir)
                    thumb_dir.mkdir(parents=True, exist_ok=True)
                    (thumb_dir / "volumes").mkdir(exist_ok=True)
                    (thumb_dir / "comics").mkdir(exist_ok=True)
                    (thumb_dir / "publishers").mkdir(exist_ok=True)
                    (thumb_dir / "comicbookinfo_issues").mkdir(exist_ok=True)

                self.show_success_message("Cache de thumbnails limpiado exitosamente")
            except Exception as e:
                self.show_error_message(f"Error limpiando cache: {e}")

    def on_regenerate_thumbnails(self, button):
        """Iniciar regeneración de thumbnails"""
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading("Regenerar Thumbnails de Volúmenes")
        dialog.set_body("¿Quieres regenerar todas las portadas de volúmenes desde ComicVine?\n\nEsto puede tardar varios minutos dependiendo de la cantidad de volúmenes.")
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("regenerate", "Regenerar")
        dialog.set_response_appearance("regenerate", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("cancel")
        dialog.connect("response", self.on_regenerate_confirmed)
        dialog.present()

    def on_regenerate_confirmed(self, dialog, response):
        """Confirmar regeneración de thumbnails"""
        if response == "regenerate":
            self.start_thumbnail_regeneration()

    def start_thumbnail_regeneration(self):
        """Iniciar proceso de regeneración en hilo separado"""
        # Cambiar UI a modo procesando
        self.regen_button.set_visible(False)
        self.regen_progress.set_visible(True)
        self.regen_status.set_visible(True)
        self.regen_status.set_text("Inicializando...")

        # Variables de progreso
        self.total_volumes = 0
        self.processed_volumes = 0
        self.successful_downloads = 0
        self.failed_downloads = 0
        self.ssl_errors = 0
        self.forbidden_errors = 0
        self.not_found_errors = 0

        # Iniciar en hilo separado
        threading.Thread(target=self.regenerate_thumbnails_worker, daemon=True).start()

    def regenerate_thumbnails_worker(self):
        """Worker que maneja la regeneración de thumbnails"""
        try:
            # Obtener volúmenes de la base de datos
            GLib.idle_add(lambda: self.regen_status.set_text("Obteniendo volúmenes..."))

            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            from entidades.volume_model import Volume

            # Conectar a la base de datos
            db_path = "data/babelcomics.db"
            engine = create_engine(f'sqlite:///{db_path}')
            Session = sessionmaker(bind=engine)
            session = Session()

            # Obtener volúmenes que tienen URL de imagen guardada
            volumes = session.query(Volume).filter(
                Volume.image_url.isnot(None),
                Volume.image_url != ''
            ).all()

            self.total_volumes = len(volumes)
            session.close()

            if self.total_volumes == 0:
                GLib.idle_add(lambda: self.regen_status.set_text("No hay volúmenes con URLs de imagen"))
                GLib.idle_add(self.finish_regeneration)
                return

            GLib.idle_add(lambda: self.regen_status.set_text(f"Regenerando {self.total_volumes} covers..."))

            # Procesar en lotes de 10 (sin necesidad de ComicVine client)
            batch_size = 10
            for i in range(0, self.total_volumes, batch_size):
                batch = volumes[i:i + batch_size]
                self.process_volume_batch(batch)

                # Actualizar progreso
                progress = min(self.processed_volumes / self.total_volumes, 1.0)
                GLib.idle_add(lambda p=progress: self.regen_progress.set_fraction(p))

            # Finalizar
            GLib.idle_add(self.finish_regeneration)

        except Exception as e:
            print(f"Error en regeneración de thumbnails: {e}")
            GLib.idle_add(lambda: self.regen_status.set_text(f"Error: {e}"))
            GLib.idle_add(self.finish_regeneration)

    def process_volume_batch(self, volumes):
        """Procesar un lote de volúmenes en paralelo"""
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_volume = {
                executor.submit(self.download_volume_cover, volume): volume
                for volume in volumes
            }

            for future in as_completed(future_to_volume):
                volume = future_to_volume[future]
                try:
                    result = future.result()
                    if result == True:
                        self.successful_downloads += 1
                    elif result == "forbidden":
                        self.forbidden_errors += 1
                        self.failed_downloads += 1
                    elif result == "not_found":
                        self.not_found_errors += 1
                        self.failed_downloads += 1
                    elif result == "ssl_error":
                        self.ssl_errors += 1
                        self.failed_downloads += 1
                    else:
                        self.failed_downloads += 1
                except Exception as e:
                    print(f"Error descargando cover para {volume.nombre}: {e}")
                    self.failed_downloads += 1

                self.processed_volumes += 1

                # Actualizar status cada volumen procesado
                status_text = f"Procesados: {self.processed_volumes}/{self.total_volumes} (✓{self.successful_downloads} ✗{self.failed_downloads})"
                if self.forbidden_errors > 0 or self.ssl_errors > 0 or self.not_found_errors > 0:
                    error_details = []
                    if self.forbidden_errors > 0:
                        error_details.append(f"403:{self.forbidden_errors}")
                    if self.not_found_errors > 0:
                        error_details.append(f"404:{self.not_found_errors}")
                    if self.ssl_errors > 0:
                        error_details.append(f"SSL:{self.ssl_errors}")
                    status_text += f" ({', '.join(error_details)})"

                GLib.idle_add(lambda text=status_text: self.regen_status.set_text(text))

    def download_volume_cover(self, volume):
        """Descargar cover de un volumen específico usando URL guardada en BD"""
        try:
            # Usar la URL de imagen guardada en la base de datos
            image_url = volume.image_url
            if not image_url:
                print(f"No hay URL de imagen guardada para volumen {volume.nombre}")
                return False

            # Descargar imagen con headers y configuración SSL
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }

            # Intentar con verificación SSL, si falla intentar sin verificación
            try:
                response = requests.get(image_url, timeout=30, headers=headers, verify=True)
                response.raise_for_status()
            except (requests.exceptions.SSLError, requests.exceptions.ConnectionError) as ssl_error:
                print(f"SSL Error para {volume.nombre}, intentando sin verificación SSL: {ssl_error}")
                try:
                    response = requests.get(image_url, timeout=30, headers=headers, verify=False)
                    response.raise_for_status()
                except Exception as fallback_error:
                    print(f"Error también sin SSL para {volume.nombre}: {fallback_error}")
                    return False

            # Crear directorio si no existe
            thumb_dir = Path("data/thumbnails/volumes")
            thumb_dir.mkdir(parents=True, exist_ok=True)

            # Guardar imagen
            thumb_path = thumb_dir / f"{volume.id_volume}.jpg"
            with open(thumb_path, 'wb') as f:
                f.write(response.content)

            print(f"✓ Cover descargado para {volume.nombre}")
            return True

        except requests.exceptions.HTTPError as http_err:
            if response.status_code == 403:
                print(f"❌ Acceso denegado (403) para {volume.nombre} - URL posiblemente expirada")
                return "forbidden"
            elif response.status_code == 404:
                print(f"❌ Imagen no encontrada (404) para {volume.nombre}")
                return "not_found"
            else:
                print(f"❌ Error HTTP {response.status_code} para {volume.nombre}: {http_err}")
                return False
        except (requests.exceptions.SSLError, requests.exceptions.ConnectionError) as ssl_err:
            print(f"❌ Error SSL/Conexión para {volume.nombre}: {ssl_err}")
            return "ssl_error"
        except requests.exceptions.Timeout:
            print(f"❌ Timeout descargando cover para {volume.nombre}")
            return False
        except Exception as e:
            print(f"❌ Error inesperado descargando cover para {volume.nombre}: {e}")
            return False

    def finish_regeneration(self):
        """Finalizar proceso de regeneración"""
        # Restaurar UI
        self.regen_button.set_visible(True)
        self.regen_progress.set_visible(False)
        self.regen_progress.set_fraction(0)

        # Mostrar resultado final
        if hasattr(self, 'total_volumes') and self.total_volumes > 0:
            final_text = f"Completado: ✓{self.successful_downloads} ✗{self.failed_downloads}"
            self.regen_status.set_text(final_text)

            # Ocultar status después de 10 segundos
            GLib.timeout_add_seconds(10, lambda: self.regen_status.set_visible(False))

            # Mostrar mensaje detallado de resultado
            message_parts = [f"Regeneración completada.", f"✓ {self.successful_downloads} covers descargados exitosamente"]

            if self.failed_downloads > 0:
                message_parts.append(f"✗ {self.failed_downloads} errores:")
                if self.forbidden_errors > 0:
                    message_parts.append(f"  • {self.forbidden_errors} URLs con acceso denegado (403)")
                if self.not_found_errors > 0:
                    message_parts.append(f"  • {self.not_found_errors} imágenes no encontradas (404)")
                if self.ssl_errors > 0:
                    message_parts.append(f"  • {self.ssl_errors} errores SSL/conexión")

                other_errors = self.failed_downloads - (self.forbidden_errors + self.not_found_errors + self.ssl_errors)
                if other_errors > 0:
                    message_parts.append(f"  • {other_errors} otros errores")

            if self.successful_downloads > 0 or self.failed_downloads == 0:
                self.show_success_message("\n".join(message_parts))
            else:
                self.show_error_message("\n".join(message_parts))
        else:
            self.regen_status.set_visible(False)


def show_config_window(parent_window=None):
    """Función helper para mostrar la ventana de configuración"""
    config_window = ConfigWindow(parent_window)
    config_window.present()
    return config_window


if __name__ == "__main__":
    # Test de la ventana de configuración
    app = Adw.Application()

    def on_activate(app):
        window = Adw.ApplicationWindow(application=app)
        window.set_title("Test Config Window")
        window.set_default_size(400, 300)

        button = Gtk.Button(label="Abrir Configuración")
        button.connect('clicked', lambda b: show_config_window(window))

        window.set_content(button)
        window.present()

    app.connect('activate', on_activate)
    app.run(sys.argv)