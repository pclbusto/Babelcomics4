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

# Importaciones para la base de datos
from sqlalchemy.orm import sessionmaker
from entidades import engine
from entidades.setup_model import Setup
from entidades.setup_directorio_model import SetupDirectorio
from repositories.setup_repository import SetupRepository


class ConfigWindow(Adw.PreferencesWindow):
    """Ventana de configuración usando Adwaita PreferencesWindow"""

    def __init__(self, parent_window=None):
        super().__init__()

        # Configuración básica de la ventana
        self.set_title("Configuración de Babelcomics4")
        self.set_default_size(600, 1200)
        self.set_modal(True)

        if parent_window:
            self.set_transient_for(parent_window)

        # Inicializar conexión a BD
        self.setup_database()

        # Crear las páginas de configuración
        self.setup_pages()

    def setup_database(self):
        """Inicializar conexión a la base de datos"""
        try:
            Session = sessionmaker(bind=engine)
            self.session = Session()
            self.setup_repo = SetupRepository(self.session)

            # Obtener o crear configuración
            self.config = self.setup_repo.obtener_o_crear_configuracion()
            print("✅ Configuración cargada desde BD")

        except Exception as e:
            print(f"❌ Error conectando a BD: {e}")
            self.config = None
            self.session = None
            self.setup_repo = None

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

        # Cargar API key desde BD
        if self.config:
            current_api_key = self.config.get_api_key()
            if current_api_key:
                self.api_key_row.set_text(current_api_key)

        # Conectar cambios para guardar automáticamente
        self.api_key_row.connect("changed", self.on_api_key_changed)

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
        self.rate_limit_row = Adw.SpinRow()
        self.rate_limit_row.set_title("Intervalo entre requests")
        self.rate_limit_row.set_subtitle("Segundos entre llamadas a la API (mín: 0.5)")

        # Cargar valor desde BD
        current_rate = 0.5
        if self.config:
            current_rate = self.config.rate_limit_interval

        rate_limit_adjustment = Gtk.Adjustment(value=current_rate, lower=0.5, upper=5.0, step_increment=0.1)
        self.rate_limit_row.set_adjustment(rate_limit_adjustment)
        self.rate_limit_row.set_digits(1)

        # Conectar cambios
        self.rate_limit_row.connect("changed", self.on_rate_limit_changed)

        comicvine_group.add(self.rate_limit_row)

        # Carpeta de organización de cómics
        self.organize_folder_row = Adw.ActionRow()
        self.organize_folder_row.set_title("Carpeta de Organización")
        self.organize_folder_row.set_subtitle("Carpeta donde se organizarán los cómics por editorial y volumen")

        # Cargar valor desde BD
        if self.config and self.config.carpeta_organizacion:
            self.organize_folder_row.set_subtitle(self.config.carpeta_organizacion)

        # Botón para seleccionar carpeta
        select_folder_button = Gtk.Button()
        select_folder_button.set_icon_name("folder-open-symbolic")
        select_folder_button.set_valign(Gtk.Align.CENTER)
        select_folder_button.set_tooltip_text("Seleccionar carpeta")
        select_folder_button.connect("clicked", self.on_select_organize_folder)
        self.organize_folder_row.add_suffix(select_folder_button)

        # Botón para limpiar selección
        clear_folder_button = Gtk.Button()
        clear_folder_button.set_icon_name("edit-clear-symbolic")
        clear_folder_button.set_valign(Gtk.Align.CENTER)
        clear_folder_button.set_tooltip_text("Limpiar selección")
        clear_folder_button.connect("clicked", self.on_clear_organize_folder)
        self.organize_folder_row.add_suffix(clear_folder_button)

        comicvine_group.add(self.organize_folder_row)

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
        self.thumb_dir_row = Adw.ActionRow()
        self.thumb_dir_row.set_title("Directorio de thumbnails")
        from helpers.thumbnail_path import get_thumbnails_base_path
        self.thumb_dir_row.set_subtitle(str(Path(get_thumbnails_base_path()).absolute()))

        thumb_edit_button = Gtk.Button()
        thumb_edit_button.set_icon_name("document-edit-symbolic")
        thumb_edit_button.set_valign(Gtk.Align.CENTER)
        thumb_edit_button.set_tooltip_text("Cambiar carpeta de thumbnails")
        thumb_edit_button.connect("clicked", self.on_change_thumbnails_directory)
        self.thumb_dir_row.add_suffix(thumb_edit_button)

        thumb_button = Gtk.Button()
        thumb_button.set_icon_name("folder-open-symbolic")
        thumb_button.set_valign(Gtk.Align.CENTER)
        thumb_button.connect("clicked", self.on_open_thumbnails_directory)
        self.thumb_dir_row.add_suffix(thumb_button)

        dirs_group.add(self.thumb_dir_row)

        page.add(dirs_group)

        # Grupo Directorios de Escaneo
        self.setup_scan_directories_group(page)

    def setup_scan_directories_group(self, page):
        """Configurar grupo de directorios para escanear cómics"""
        scan_dirs_group = Adw.PreferencesGroup()
        scan_dirs_group.set_title("Directorios de Escaneo")
        scan_dirs_group.set_description("Carpetas donde buscar archivos de cómics para catalogar")

        # Agregar nuevo directorio
        add_dir_row = Adw.ActionRow()
        add_dir_row.set_title("Agregar directorio")
        add_dir_row.set_subtitle("Seleccionar nueva carpeta para escanear")

        add_button = Gtk.Button()
        add_button.set_icon_name("folder-new-symbolic")
        add_button.set_valign(Gtk.Align.CENTER)
        add_button.add_css_class("suggested-action")
        add_button.connect("clicked", self.on_add_scan_directory)
        add_dir_row.add_suffix(add_button)

        scan_dirs_group.add(add_dir_row)

        # Botón para escanear directorios
        scan_row = Adw.ActionRow()
        scan_row.set_title("Escanear directorios")
        scan_row.set_subtitle("Buscar nuevos cómics en los directorios configurados")

        self.scan_button = Gtk.Button()
        self.scan_button.set_label("Escanear")
        self.scan_button.set_valign(Gtk.Align.CENTER)
        self.scan_button.add_css_class("suggested-action")
        self.scan_button.connect("clicked", self.on_scan_directories)
        scan_row.add_suffix(self.scan_button)

        # Progress bar para escaneo (inicialmente oculta)
        self.scan_progress = Gtk.ProgressBar()
        self.scan_progress.set_visible(False)
        self.scan_progress.set_valign(Gtk.Align.CENTER)
        self.scan_progress.set_hexpand(True)
        scan_row.add_suffix(self.scan_progress)

        # Botón cancelar escaneo (inicialmente oculto)
        self.cancel_scan_button = Gtk.Button()
        self.cancel_scan_button.set_label("Cancelar")
        self.cancel_scan_button.set_valign(Gtk.Align.CENTER)
        self.cancel_scan_button.add_css_class("destructive-action")
        self.cancel_scan_button.set_visible(False)
        self.cancel_scan_button.connect("clicked", self.on_cancel_scan)
        scan_row.add_suffix(self.cancel_scan_button)

        # Label de estado del escaneo
        self.scan_status = Gtk.Label()
        self.scan_status.set_visible(False)
        self.scan_status.set_halign(Gtk.Align.START)
        self.scan_status.add_css_class("dim-label")
        scan_row.add_suffix(self.scan_status)

        scan_dirs_group.add(scan_row)

        # Lista de directorios configurados
        self.scan_dirs_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.refresh_scan_directories_list()

        # Agregar la lista al grupo usando una fila expandible
        dirs_list_row = Adw.ActionRow()
        dirs_list_row.set_title("Directorios configurados")
        dirs_list_row.set_child(self.scan_dirs_box)
        scan_dirs_group.add(dirs_list_row)

        page.add(scan_dirs_group)

    def refresh_scan_directories_list(self):
        """Actualizar la lista de directorios de escaneo"""
        # Limpiar lista actual
        while self.scan_dirs_box.get_first_child():
            self.scan_dirs_box.remove(self.scan_dirs_box.get_first_child())

        if not self.config:
            return

        # Obtener directorios de escaneo (activo=True)
        scan_directories = [d for d in self.config.directorios if d.activo]

        if not scan_directories:
            # Mostrar mensaje si no hay directorios
            no_dirs_label = Gtk.Label()
            no_dirs_label.set_markup("<i>No hay directorios configurados para escanear</i>")
            no_dirs_label.set_halign(Gtk.Align.START)
            no_dirs_label.add_css_class("dim-label")
            self.scan_dirs_box.append(no_dirs_label)
            return

        # Mostrar cada directorio
        for directory in scan_directories:
            dir_row = self.create_scan_directory_row(directory)
            self.scan_dirs_box.append(dir_row)

    def create_scan_directory_row(self, directory):
        """Crear una fila para un directorio de escaneo"""
        row = Adw.ActionRow()

        # Verificar si el directorio existe
        path_exists = directory.is_valid_path()

        row.set_title(Path(directory.directorio_path).name)
        row.set_subtitle(directory.directorio_path)

        if not path_exists:
            row.add_css_class("error")
            row.set_subtitle(f"❌ {directory.directorio_path} (no encontrado)")

        # Botón para abrir directorio
        if path_exists:
            open_button = Gtk.Button()
            open_button.set_icon_name("folder-open-symbolic")
            open_button.set_valign(Gtk.Align.CENTER)
            open_button.set_tooltip_text("Abrir directorio")
            open_button.connect("clicked", lambda btn, path=directory.directorio_path: self.open_directory(path))
            row.add_suffix(open_button)

        # Botón para eliminar
        remove_button = Gtk.Button()
        remove_button.set_icon_name("user-trash-symbolic")
        remove_button.set_valign(Gtk.Align.CENTER)
        remove_button.add_css_class("destructive-action")
        remove_button.set_tooltip_text("Eliminar directorio")
        remove_button.connect("clicked", lambda btn, dir_id=directory.id: self.on_remove_scan_directory(dir_id))
        row.add_suffix(remove_button)

        return row

    def setup_interface_group(self, page):
        """Configurar grupo de interfaz"""
        interface_group = Adw.PreferencesGroup()
        interface_group.set_title("Interfaz")
        interface_group.set_description("Configuración de la interfaz de usuario")

        # Modo oscuro/claro
        self.theme_row = Adw.ComboRow()
        self.theme_row.set_title("Tema")
        self.theme_row.set_subtitle("Apariencia de la aplicación")

        theme_model = Gtk.StringList()
        theme_model.append("Seguir sistema")
        theme_model.append("Claro")
        theme_model.append("Oscuro")
        self.theme_row.set_model(theme_model)

        # Cargar tema desde BD
        if self.config:
            if self.config.modo_oscuro:
                self.theme_row.set_selected(2)  # Oscuro
            else:
                self.theme_row.set_selected(1)  # Claro
        else:
            self.theme_row.set_selected(0)  # Seguir sistema

        self.theme_row.connect("notify::selected-item", self.on_theme_changed)
        interface_group.add(self.theme_row)

        # Tamaño de thumbnails
        self.thumbnail_size_row = Adw.SpinRow()
        self.thumbnail_size_row.set_title("Tamaño de thumbnails")
        self.thumbnail_size_row.set_subtitle("Píxeles para las miniaturas")

        # Cargar valor desde BD
        current_size = 200
        if self.config:
            try:
                current_size = int(self.config.thumbnail_size)
            except (ValueError, TypeError):
                current_size = 200

        size_adjustment = Gtk.Adjustment(value=current_size, lower=100, upper=400, step_increment=10)
        self.thumbnail_size_row.set_adjustment(size_adjustment)
        self.thumbnail_size_row.connect("changed", self.on_thumbnail_size_changed)

        interface_group.add(self.thumbnail_size_row)

        # Items por lote
        self.items_per_batch_row = Adw.SpinRow()
        self.items_per_batch_row.set_title("Items por lote")
        self.items_per_batch_row.set_subtitle("Cantidad de items a cargar por vez")

        # Cargar valor desde BD
        current_batch = 20
        if self.config:
            try:
                current_batch = int(self.config.items_per_batch)
            except (ValueError, TypeError):
                current_batch = 20

        items_adjustment = Gtk.Adjustment(value=current_batch, lower=10, upper=100, step_increment=5)
        self.items_per_batch_row.set_adjustment(items_adjustment)
        self.items_per_batch_row.connect("changed", self.on_items_per_batch_changed)

        interface_group.add(self.items_per_batch_row)

        # Configuración del lector de comics
        # Scroll threshold
        self.scroll_threshold_row = Adw.SpinRow()
        self.scroll_threshold_row.set_title("Sensibilidad de scroll")
        self.scroll_threshold_row.set_subtitle("Umbral para cambiar página con scroll (menor = más sensible)")

        # Cargar valor desde BD
        current_threshold = 1.0
        if self.config:
            try:
                current_threshold = float(self.config.scroll_threshold)
            except (ValueError, TypeError):
                current_threshold = 1.0

        threshold_adjustment = Gtk.Adjustment(value=current_threshold, lower=0.1, upper=5.0, step_increment=0.1)
        self.scroll_threshold_row.set_adjustment(threshold_adjustment)
        self.scroll_threshold_row.set_digits(1)
        self.scroll_threshold_row.connect("changed", self.on_scroll_threshold_changed)

        interface_group.add(self.scroll_threshold_row)

        # Scroll cooldown
        self.scroll_cooldown_row = Adw.SpinRow()
        self.scroll_cooldown_row.set_title("Cooldown de scroll")
        self.scroll_cooldown_row.set_subtitle("Milisegundos de espera entre cambios de página")

        # Cargar valor desde BD
        current_cooldown = 100
        if self.config:
            try:
                current_cooldown = int(self.config.scroll_cooldown)
            except (ValueError, TypeError):
                current_cooldown = 100

        cooldown_adjustment = Gtk.Adjustment(value=current_cooldown, lower=50, upper=1000, step_increment=50)
        self.scroll_cooldown_row.set_adjustment(cooldown_adjustment)
        self.scroll_cooldown_row.connect("changed", self.on_scroll_cooldown_changed)

        interface_group.add(self.scroll_cooldown_row)

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
        self.workers_row = Adw.SpinRow()
        self.workers_row.set_title("Workers concurrentes")
        self.workers_row.set_subtitle("Número de hilos para descargas paralelas")

        # Cargar valor desde BD
        current_workers = 5
        if self.config:
            current_workers = self.config.workers_concurrentes

        workers_adjustment = Gtk.Adjustment(value=current_workers, lower=1, upper=20, step_increment=1)
        self.workers_row.set_adjustment(workers_adjustment)
        self.workers_row.connect("changed", self.on_workers_changed)

        perf_group.add(self.workers_row)

        # Cache de thumbnails
        self.cache_row = Adw.SwitchRow()
        self.cache_row.set_title("Cache de thumbnails")
        self.cache_row.set_subtitle("Mantener thumbnails en memoria")

        # Cargar valor desde BD
        if self.config:
            self.cache_row.set_active(self.config.cache_thumbnails)
        else:
            self.cache_row.set_active(True)

        self.cache_row.connect("notify::active", self.on_cache_changed)
        perf_group.add(self.cache_row)

        # Limpieza automática
        self.cleanup_row = Adw.SwitchRow()
        self.cleanup_row.set_title("Limpieza automática")
        self.cleanup_row.set_subtitle("Limpiar archivos temporales al cerrar")

        # Cargar valor desde BD
        if self.config:
            self.cleanup_row.set_active(self.config.limpieza_automatica)
        else:
            self.cleanup_row.set_active(True)

        self.cleanup_row.connect("notify::active", self.on_cleanup_changed)
        perf_group.add(self.cleanup_row)

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

    # Métodos callback para cambios de configuración
    def on_api_key_changed(self, entry):
        """Callback cuando cambia la API key"""
        if not self.config:
            return

        api_key = entry.get_text().strip()
        self.config.set_api_key(api_key)
        self.save_config()

    def on_rate_limit_changed(self, spin_row):
        """Callback cuando cambia el rate limit"""
        if not self.config:
            return

        self.config.rate_limit_interval = spin_row.get_value()
        self.save_config()

    def on_select_organize_folder(self, button):
        """Abrir diálogo para seleccionar carpeta de organización"""
        dialog = Gtk.FileDialog()
        dialog.set_title("Seleccionar carpeta de organización")
        dialog.select_folder(
            parent=self,
            cancellable=None,
            callback=self.on_organize_folder_selected
        )

    def on_organize_folder_selected(self, dialog, result):
        """Callback cuando se selecciona carpeta de organización"""
        try:
            folder = dialog.select_folder_finish(result)
            if folder:
                folder_path = folder.get_path()
                abs_path = str(Path(folder_path).absolute())

                # Verificar que el directorio existe
                if Path(abs_path).exists() and Path(abs_path).is_dir():
                    # Actualizar BD
                    if self.config:
                        self.config.carpeta_organizacion = abs_path
                        self.save_config()

                        # Actualizar UI
                        self.organize_folder_row.set_subtitle(abs_path)
                        print(f"✅ Carpeta de organización configurada: {abs_path}")
                else:
                    self.show_error_message(f"El directorio no existe o no es válido:\n{abs_path}")
        except Exception as e:
            if "cancelled" not in str(e).lower():
                print(f"Error seleccionando carpeta de organización: {e}")

    def on_clear_organize_folder(self, button):
        """Limpiar carpeta de organización"""
        if self.config:
            self.config.carpeta_organizacion = ''
            self.save_config()

            # Actualizar UI
            self.organize_folder_row.set_subtitle("Carpeta donde se organizarán los cómics por editorial y volumen")
            print("✅ Carpeta de organización limpiada")

    def on_theme_changed(self, combo_row, param):
        """Callback cuando cambia el tema"""
        if not self.config:
            return

        selected = combo_row.get_selected()
        if selected == 0:  # Seguir sistema
            # Por ahora mantener como False, después se puede implementar detección de sistema
            self.config.modo_oscuro = False
        elif selected == 1:  # Claro
            self.config.modo_oscuro = False
        elif selected == 2:  # Oscuro
            self.config.modo_oscuro = True

        self.save_config()

    def on_thumbnail_size_changed(self, spin_row):
        """Callback cuando cambia el tamaño de thumbnails"""
        if not self.config:
            return

        self.config.thumbnail_size = int(spin_row.get_value())
        self.save_config()

    def on_items_per_batch_changed(self, spin_row):
        """Callback cuando cambia items por lote"""
        if not self.config:
            return

        self.config.items_per_batch = int(spin_row.get_value())
        self.save_config()

    def on_workers_changed(self, spin_row):
        """Callback cuando cambia workers concurrentes"""
        if not self.config:
            return

        self.config.workers_concurrentes = int(spin_row.get_value())
        self.save_config()

    def on_cache_changed(self, switch_row, param):
        """Callback cuando cambia cache de thumbnails"""
        if not self.config:
            return

        self.config.cache_thumbnails = switch_row.get_active()
        self.save_config()

    def on_cleanup_changed(self, switch_row, param):
        """Callback cuando cambia limpieza automática"""
        if not self.config:
            return

        self.config.limpieza_automatica = switch_row.get_active()
        self.save_config()

    def on_scroll_threshold_changed(self, spin_row):
        """Callback cuando cambia el threshold de scroll"""
        if not self.config:
            return

        self.config.scroll_threshold = spin_row.get_value()
        self.save_config()

    def on_scroll_cooldown_changed(self, spin_row):
        """Callback cuando cambia el cooldown de scroll"""
        if not self.config:
            return

        self.config.scroll_cooldown = int(spin_row.get_value())
        self.save_config()

    def save_config(self):
        """Guardar configuración en la base de datos"""
        if self.setup_repo and self.session:
            try:
                self.setup_repo.guardar_configuracion(self.config)
                print("🔧 Configuración guardada")
            except Exception as e:
                print(f"❌ Error guardando configuración: {e}")

    # Métodos para gestión de directorios de escaneo
    def on_add_scan_directory(self, button):
        """Abrir diálogo para seleccionar directorio de escaneo"""
        dialog = Gtk.FileDialog()
        dialog.set_title("Seleccionar directorio para escanear")
        dialog.select_folder(
            parent=self,
            cancellable=None,
            callback=self.on_folder_selected
        )

    def on_folder_selected(self, dialog, result):
        """Callback cuando se selecciona un directorio"""
        try:
            folder = dialog.select_folder_finish(result)
            if folder:
                folder_path = folder.get_path()
                self.add_scan_directory(folder_path)
        except Exception as e:
            if "cancelled" not in str(e).lower():
                print(f"Error seleccionando directorio: {e}")

    def add_scan_directory(self, directory_path):
        """Agregar un nuevo directorio de escaneo"""
        if not self.config or not self.session:
            return

        abs_path = str(Path(directory_path).absolute())

        # Verificar que no exista ya
        existing = any(d.directorio_path == abs_path for d in self.config.directorios)
        if existing:
            self.show_error_message(f"El directorio ya está configurado:\n{abs_path}")
            return

        # Verificar que el directorio existe
        if not Path(abs_path).exists() or not Path(abs_path).is_dir():
            self.show_error_message(f"El directorio no existe o no es válido:\n{abs_path}")
            return

        try:
            # Crear nuevo directorio en BD
            new_directory = SetupDirectorio(
                setup_id=self.config.setupkey,
                directorio_path=abs_path,
                activo=True  # Para escaneo
            )
            self.session.add(new_directory)
            self.session.commit()

            # Actualizar la configuración cargada
            self.config.directorios.append(new_directory)

            # Actualizar la UI
            self.refresh_scan_directories_list()

            print(f"✅ Directorio agregado: {abs_path}")
            self.show_success_message(f"Directorio agregado exitosamente:\n{abs_path}")

        except Exception as e:
            print(f"❌ Error agregando directorio: {e}")
            self.show_error_message(f"Error agregando directorio:\n{e}")

    def on_remove_scan_directory(self, directory_id):
        """Mostrar confirmación para eliminar directorio"""
        # Buscar el directorio
        directory = None
        for d in self.config.directorios:
            if d.id == directory_id:
                directory = d
                break

        if not directory:
            return

        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading("Eliminar directorio de escaneo")
        dialog.set_body(f"¿Estás seguro de que quieres eliminar este directorio?\n\n{directory.directorio_path}\n\nEsto no eliminará los archivos, solo dejará de escanearlo.")
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("remove", "Eliminar")
        dialog.set_response_appearance("remove", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.connect("response", lambda d, r, dir_id=directory_id: self.on_remove_directory_confirmed(d, r, dir_id))
        dialog.present()

    def on_remove_directory_confirmed(self, dialog, response, directory_id):
        """Confirmar eliminación de directorio"""
        if response == "remove":
            self.remove_scan_directory(directory_id)

    def remove_scan_directory(self, directory_id):
        """Eliminar directorio de escaneo de la BD"""
        if not self.session:
            return

        try:
            # Eliminar de BD
            directory = self.session.query(SetupDirectorio).filter_by(id=directory_id).first()
            if directory:
                directory_path = directory.directorio_path
                self.session.delete(directory)
                self.session.commit()

                # Actualizar configuración en memoria
                self.config.directorios = [d for d in self.config.directorios if d.id != directory_id]

                # Actualizar UI
                self.refresh_scan_directories_list()

                print(f"✅ Directorio eliminado: {directory_path}")
                self.show_success_message(f"Directorio eliminado exitosamente:\n{directory_path}")

        except Exception as e:
            print(f"❌ Error eliminando directorio: {e}")
            self.show_error_message(f"Error eliminando directorio:\n{e}")

    # Métodos para escaneo de directorios
    def on_scan_directories(self, button):
        """Iniciar escaneo de directorios configurados"""
        # Verificar que hay directorios configurados
        if not self.config:
            self.show_error_message("No se pudo cargar la configuración")
            return

        scan_directories = [d for d in self.config.directorios if d.activo]
        if not scan_directories:
            self.show_error_message("No hay directorios configurados para escanear.\n\nAgrega al menos un directorio antes de escanear.")
            return

        # Mostrar confirmación
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading("Escanear directorios de cómics")

        dir_list = "\n".join([f"• {Path(d.directorio_path).name}" for d in scan_directories[:5]])
        if len(scan_directories) > 5:
            dir_list += f"\n... y {len(scan_directories) - 5} más"

        dialog.set_body(f"¿Quieres escanear los siguientes directorios en busca de nuevos cómics?\n\n{dir_list}\n\nEsto puede tardar varios minutos dependiendo del tamaño de las carpetas.")

        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("scan", "Escanear")
        dialog.set_response_appearance("scan", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("cancel")
        dialog.connect("response", self.on_scan_directories_confirmed)
        dialog.present()

    def on_scan_directories_confirmed(self, dialog, response):
        """Confirmar inicio de escaneo"""
        if response == "scan":
            self.start_directory_scan()

    def start_directory_scan(self):
        """Iniciar proceso de escaneo en hilo separado"""
        # Cambiar UI a modo escaneando
        self.scan_button.set_visible(False)
        self.scan_progress.set_visible(True)
        self.cancel_scan_button.set_visible(True)
        self.scan_status.set_visible(True)
        self.scan_status.set_text("Iniciando escaneo...")

        # Variables de estado
        self.scan_cancelled = False
        self.current_scanner = None

        # Iniciar en hilo separado
        import threading
        threading.Thread(target=self.scan_directories_worker, daemon=True).start()

    def scan_directories_worker(self):
        """Worker que maneja el escaneo de directorios"""
        try:
            from helpers.comic_scanner import ComicScanner

            # Crear scanner con callbacks
            self.current_scanner = ComicScanner(
                progress_callback=self.on_scan_progress,
                status_callback=self.on_scan_status
            )

            # Ejecutar escaneo
            stats = self.current_scanner.scan_directories(skip_existing=True)

            # Mostrar resultado final en el hilo principal
            GLib.idle_add(lambda: self.finish_directory_scan(stats))

        except Exception as e:
            print(f"Error en escaneo de directorios: {e}")
            import traceback
            traceback.print_exc()
            GLib.idle_add(lambda: self.scan_status.set_text(f"Error: {e}"))
            GLib.idle_add(self.finish_directory_scan_with_error)

    def on_scan_progress(self, progress):
        """Callback para progreso del escaneo (0.0-1.0)"""
        GLib.idle_add(lambda: self.scan_progress.set_fraction(progress))

    def on_scan_status(self, message):
        """Callback para estado del escaneo"""
        GLib.idle_add(lambda: self.scan_status.set_text(message))

    def on_cancel_scan(self, button):
        """Cancelar escaneo en progreso"""
        if self.current_scanner:
            self.current_scanner.cancel_scan()
            self.scan_cancelled = True
            self.scan_status.set_text("Cancelando...")

    def finish_directory_scan(self, stats):
        """Finalizar proceso de escaneo exitoso"""
        # Restaurar UI
        self.scan_button.set_visible(True)
        self.scan_progress.set_visible(False)
        self.cancel_scan_button.set_visible(False)
        self.scan_progress.set_fraction(0)

        # Mostrar resultado final
        final_text = f"Completado: +{stats['comics_added']} cómics"
        if stats['comics_skipped'] > 0:
            final_text += f" (omitidos: {stats['comics_skipped']})"

        self.scan_status.set_text(final_text)

        # Ocultar status después de 10 segundos
        GLib.timeout_add_seconds(10, lambda: self.scan_status.set_visible(False))

        # Mostrar mensaje detallado de resultado
        message_parts = [
            "Escaneo de directorios completado.",
            f"📁 Archivos encontrados: {stats['total_files_found']}",
            f"✅ Cómics agregados: {stats['comics_added']}",
        ]

        if stats['comics_skipped'] > 0:
            message_parts.append(f"⏭️ Cómics omitidos (ya existían): {stats['comics_skipped']}")

        if stats['errors'] > 0:
            message_parts.append(f"❌ Errores: {stats['errors']}")

        elapsed_min = stats['elapsed_time'] / 60
        if elapsed_min >= 1:
            message_parts.append(f"⏱️ Tiempo: {elapsed_min:.1f} minutos")
        else:
            message_parts.append(f"⏱️ Tiempo: {stats['elapsed_time']:.1f} segundos")

        if stats['comics_added'] > 0:
            self.show_success_message("\n".join(message_parts))
        elif stats['comics_skipped'] > 0:
            # Solo cómics omitidos, no es error pero tampoco gran éxito
            message_parts.insert(1, "ℹ️ No se encontraron cómics nuevos.")
            dialog = Adw.MessageDialog.new(self)
            dialog.set_heading("Escaneo completado")
            dialog.set_body("\n".join(message_parts))
            dialog.add_response("ok", "OK")
            dialog.present()
        else:
            message_parts.insert(1, "ℹ️ No se encontraron archivos de cómics.")
            self.show_success_message("\n".join(message_parts))

    def finish_directory_scan_with_error(self):
        """Finalizar proceso de escaneo con error"""
        # Restaurar UI
        self.scan_button.set_visible(True)
        self.scan_progress.set_visible(False)
        self.cancel_scan_button.set_visible(False)
        self.scan_progress.set_fraction(0)

        # Ocultar status después de 5 segundos
        GLib.timeout_add_seconds(5, lambda: self.scan_status.set_visible(False))

    def __del__(self):
        """Cerrar conexión de BD al destruir la ventana"""
        if hasattr(self, 'session') and self.session:
            self.session.close()

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

                    # Guardar la API key en BD
                    if self.config:
                        GLib.idle_add(lambda: self.config.set_api_key(api_key))
                        GLib.idle_add(self.save_config)
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

    def on_open_data_directory(self, button):
        """Abrir directorio de datos"""
        self.open_directory("data")

    def on_open_thumbnails_directory(self, button):
        """Abrir directorio de thumbnails"""
        from helpers.thumbnail_path import get_thumbnails_base_path
        self.open_directory(get_thumbnails_base_path())

    def on_change_thumbnails_directory(self, button):
        """Abrir diálogo para cambiar la carpeta de thumbnails"""
        from helpers.thumbnail_path import get_thumbnails_base_path

        dialog = Gtk.FileDialog.new()
        dialog.set_title("Seleccionar nueva carpeta de thumbnails")

        # Intentar establecer la carpeta actual como inicial
        current_path = Path(get_thumbnails_base_path()).absolute()
        if current_path.exists():
            dialog.set_initial_folder(Gio.File.new_for_path(str(current_path)))

        dialog.select_folder(self, None, self._on_thumbnail_folder_selected)

    def _on_thumbnail_folder_selected(self, dialog, result):
        """Callback cuando se selecciona una nueva carpeta de thumbnails"""
        try:
            folder = dialog.select_folder_finish(result)
            if folder is None:
                return

            new_path = folder.get_path()
            if not new_path:
                return

            from helpers.thumbnail_path import get_thumbnails_base_path
            current_path = str(Path(get_thumbnails_base_path()).absolute())

            if new_path == current_path:
                self.show_success_message("La carpeta seleccionada es la misma que la actual.")
                return

            # Diálogo de confirmación
            confirm_dialog = Adw.MessageDialog.new(self)
            confirm_dialog.set_heading("Cambiar carpeta de thumbnails")
            confirm_dialog.set_body(
                f"Ruta actual:\n{current_path}\n\n"
                f"Nueva ruta:\n{new_path}\n\n"
                "Se copiarán todos los archivos existentes a la nueva ubicación. "
                "Los originales se borrarán solo tras completar la copia."
            )
            confirm_dialog.add_response("cancel", "Cancelar")
            confirm_dialog.add_response("migrate", "Migrar")
            confirm_dialog.set_response_appearance("migrate", Adw.ResponseAppearance.SUGGESTED)
            confirm_dialog.set_default_response("cancel")
            confirm_dialog.connect("response", self._on_migrate_thumbnails_confirmed, new_path)
            confirm_dialog.present()

        except GLib.Error:
            # El usuario canceló el diálogo
            pass

    def _on_migrate_thumbnails_confirmed(self, dialog, response, new_path):
        """Confirmar y ejecutar la migración de thumbnails"""
        if response != "migrate":
            return

        from helpers.thumbnail_path import get_thumbnails_base_path, set_thumbnails_base_path, ensure_directories_exist

        old_path = str(Path(get_thumbnails_base_path()).absolute())

        # Crear diálogo de progreso
        progress_dialog = Adw.MessageDialog.new(self)
        progress_dialog.set_heading("Migrando thumbnails...")
        progress_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        progress_box.set_margin_start(12)
        progress_box.set_margin_end(12)
        progress_label = Gtk.Label(label="Preparando...")
        progress_label.set_xalign(0)
        progress_bar = Gtk.ProgressBar()
        progress_box.append(progress_label)
        progress_box.append(progress_bar)
        progress_dialog.set_extra_child(progress_box)
        progress_dialog.set_body("")
        progress_dialog.present()

        def migrate_worker():
            import shutil as _shutil

            try:
                old_abs = Path(old_path)

                # Verificar espacio en disco destino
                dest_stat = _shutil.disk_usage(str(Path(new_path).parent))
                if old_abs.exists():
                    total_size = sum(f.stat().st_size for f in old_abs.rglob("*") if f.is_file())
                else:
                    total_size = 0

                if total_size > 0 and dest_stat.free < total_size * 1.1:
                    GLib.idle_add(lambda: self._finish_migration(progress_dialog, False,
                        f"Espacio insuficiente en destino.\n"
                        f"Necesario: {total_size / (1024*1024):.1f} MB\n"
                        f"Disponible: {dest_stat.free / (1024*1024):.1f} MB"))
                    return

                # Crear estructura de subdirectorios en destino
                GLib.idle_add(lambda: progress_label.set_text("Creando directorios..."))
                ensure_directories_exist(new_path)

                # Recopilar archivos a copiar
                if old_abs.exists():
                    files_to_copy = [f for f in old_abs.rglob("*") if f.is_file()]
                else:
                    files_to_copy = []

                total_files = len(files_to_copy)
                copied = 0
                errors = []

                for src_file in files_to_copy:
                    try:
                        rel = src_file.relative_to(old_abs)
                        dst_file = Path(new_path) / rel
                        dst_file.parent.mkdir(parents=True, exist_ok=True)
                        _shutil.copy2(str(src_file), str(dst_file))
                        copied += 1
                        if total_files > 0:
                            frac = copied / total_files
                            GLib.idle_add(lambda f=frac, c=copied, t=total_files:
                                (progress_bar.set_fraction(f),
                                 progress_label.set_text(f"Copiando: {c}/{t} archivos...")))
                    except Exception as copy_err:
                        errors.append(f"{src_file.name}: {copy_err}")

                if errors:
                    GLib.idle_add(lambda: self._finish_migration(progress_dialog, False,
                        f"Errores al copiar {len(errors)} archivos.\n"
                        "Los archivos originales no se han modificado.\n"
                        f"Primer error: {errors[0]}"))
                    return

                # Copia exitosa: actualizar BD y cache
                try:
                    if self.config:
                        self.config.carpeta_thumbnails = new_path
                        self.session.commit()
                    set_thumbnails_base_path(new_path)
                except Exception as db_err:
                    GLib.idle_add(lambda: self._finish_migration(progress_dialog, False,
                        f"Error actualizando configuración: {db_err}\n"
                        "Los archivos fueron copiados pero la configuración no se actualizó."))
                    return

                # Borrar originales
                if old_abs.exists() and str(old_abs) != new_path:
                    try:
                        _shutil.rmtree(str(old_abs))
                    except Exception as rm_err:
                        print(f"No se pudieron borrar los originales: {rm_err}")

                GLib.idle_add(lambda: self._finish_migration(progress_dialog, True,
                    f"Migración completada.\n{copied} archivos movidos a:\n{new_path}"))

            except Exception as e:
                GLib.idle_add(lambda: self._finish_migration(progress_dialog, False,
                    f"Error durante la migración: {e}"))

        threading.Thread(target=migrate_worker, daemon=True).start()

    def _finish_migration(self, progress_dialog, success, message):
        """Finalizar diálogo de migración"""
        progress_dialog.close()

        result_dialog = Adw.MessageDialog.new(self)
        if success:
            result_dialog.set_heading("Migración exitosa")
            from helpers.thumbnail_path import get_thumbnails_base_path
            self.thumb_dir_row.set_subtitle(str(Path(get_thumbnails_base_path()).absolute()))
        else:
            result_dialog.set_heading("Error en migración")
        result_dialog.set_body(message)
        result_dialog.add_response("ok", "OK")
        result_dialog.set_default_response("ok")
        result_dialog.present()

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
            from helpers.thumbnail_path import get_thumbnails_base_path
            thumb_dir = Path(get_thumbnails_base_path()) / "volumes"
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
                from helpers.thumbnail_path import get_thumbnails_base_path, ensure_directories_exist
                thumb_dir = Path(get_thumbnails_base_path())
                if thumb_dir.exists():
                    shutil.rmtree(thumb_dir)
                    ensure_directories_exist()

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
            from helpers.thumbnail_path import get_thumbnails_base_path
            thumb_dir = Path(get_thumbnails_base_path()) / "volumes"
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