#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio
import sys
import os
import threading
from pathlib import Path

# Asegurar que los módulos locales estén en el path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Importar componentes de la aplicación
from obsoletos.comic_manager_main import ComicManagerApp, ComicManagerWindow
from obsoletos.comic_utils import ConfigManager, ToastManager, KeyboardShortcuts, DatabaseManager, ProgressDialog, ComicScanner


class EnhancedComicManagerWindow(ComicManagerWindow):
    """Ventana principal mejorada con funcionalidades adicionales"""
    
    def __init__(self, app):
        # Inicializar gestor de configuración primero
        self.config_manager = ConfigManager()
        
        super().__init__(app)
        
        # Inicializar componentes adicionales
        self.setup_enhanced_features()
        
        # Cargar configuración de ventana
        self.load_window_config()
        
    def setup_enhanced_features(self):
        """Configurar funcionalidades mejoradas"""
        # Gestor de toasts
        self.toast_overlay = Adw.ToastOverlay()
        current_content = self.get_content()
        self.toast_overlay.set_child(current_content)
        self.set_content(self.toast_overlay)
        
        self.toast_manager = ToastManager(self)
        
        # Atajos de teclado
        self.keyboard_shortcuts = KeyboardShortcuts(self)
        
        # Gestor de base de datos mejorado
        db_path = self.config_manager.get("database_path", "comics.db")
        self.enhanced_db_manager = DatabaseManager(db_path)
        
        # Conectar señales adicionales
        self.connect("close-request", self.on_close_request)
        
        # Configurar menú de aplicación
        self.setup_app_menu()
        
    def setup_app_menu(self):
        """Configurar menú de aplicación"""
        # Crear acciones
        scan_action = Gio.SimpleAction.new("scan_directories", None)
        scan_action.connect("activate", self.on_scan_directories)
        self.add_action(scan_action)
        
        stats_action = Gio.SimpleAction.new("show_stats", None)
        stats_action.connect("activate", self.on_show_stats)
        self.add_action(stats_action)
        
        settings_action = Gio.SimpleAction.new("show_settings", None)
        settings_action.connect("activate", self.on_show_settings)
        self.add_action(settings_action)
        
        about_action = Gio.SimpleAction.new("show_about", None)
        about_action.connect("activate", self.on_show_about)
        self.add_action(about_action)
        
        # Añadir botón de menú al header
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        menu_button.add_css_class("flat")
        
        # Crear menú
        menu = Gio.Menu()
        menu.append("Escanear directorios", "win.scan_directories")
        menu.append("Estadísticas", "win.show_stats")
        menu.append("Configuración", "win.show_settings")
        menu.append("Acerca de", "win.show_about")
        
        menu_button.set_menu_model(menu)
        self.header_bar.pack_end(menu_button)
        
    def load_window_config(self):
        """Cargar configuración de la ventana"""
        width = self.config_manager.get("window_width", 1200)
        height = self.config_manager.get("window_height", 800)
        self.set_default_size(width, height)
        
        # Recordar última sección
        last_section = self.config_manager.get("last_section", "comics")
        if last_section in self.nav_rows:
            nav_list = list(self.nav_rows.values())[0].get_parent()
            nav_list.select_row(self.nav_rows[last_section])
            
    def on_close_request(self, window):
        """Manejar cierre de ventana"""
        # Guardar configuración
        self.save_window_config()
        self.config_manager.save_config()
        
        # Desconectar base de datos
        if self.enhanced_db_manager:
            self.enhanced_db_manager.disconnect()
            
        return False  # Permitir cierre
        
    def save_window_config(self):
        """Guardar configuración de la ventana"""
        width, height = self.get_default_size()
        self.config_manager.set("window_width", width)
        self.config_manager.set("window_height", height)
        self.config_manager.set("last_section", self.current_section)
        
    def on_scan_directories(self, action, param):
        """Escanear directorios en busca de comics"""
        dialog = DirectoryScanDialog(self)
        dialog.present(self)
        
    def on_show_stats(self, action, param):
        """Mostrar estadísticas de la base de datos"""
        dialog = StatsDialog(self)
        dialog.present(self)
        
    def on_show_settings(self, action, param):
        """Mostrar configuración"""
        dialog = SettingsDialog(self, self.config_manager)
        dialog.present(self)
        
    def on_show_about(self, action, param):
        """Mostrar información sobre la aplicación"""
        about = Adw.AboutDialog()
        about.set_application_name("Comic Manager")
        about.set_version("1.0.0")
        about.set_developer_name("Comic Manager Team")
        about.set_license_type(Gtk.License.MIT_X11)
        about.set_comments("Gestor de colección de comics con interfaz moderna")
        about.set_website("https://github.com/comic-manager/comic-manager")
        about.set_issue_url("https://github.com/comic-manager/comic-manager/issues")
        
        about.present(self)


class DirectoryScanDialog(Adw.Dialog):
    """Diálogo para escanear directorios"""
    
    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window
        self.selected_directories = []
        
        self.set_title("Escanear Directorios")
        self.set_default_size(500, 400)
        
        self.create_content()
        
    def create_content(self):
        """Crear contenido del diálogo"""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Header
        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label="Escanear Directorios"))
        
        cancel_button = Gtk.Button.new_with_label("Cancelar")
        cancel_button.connect("clicked", lambda b: self.close())
        header.pack_start(cancel_button)
        
        scan_button = Gtk.Button.new_with_label("Escanear")
        scan_button.add_css_class("suggested-action")
        scan_button.connect("clicked", self.on_scan_clicked)
        header.pack_end(scan_button)
        
        main_box.append(header)
        
        # Contenido
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        
        # Instrucciones
        instructions = Gtk.Label()
        instructions.set_markup("<b>Selecciona los directorios a escanear:</b>")
        instructions.set_halign(Gtk.Align.START)
        content_box.append(instructions)
        
        # Lista de directorios
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_min_content_height(200)
        
        self.directory_listbox = Gtk.ListBox()
        self.directory_listbox.add_css_class("boxed-list")
        scrolled.set_child(self.directory_listbox)
        
        content_box.append(scrolled)
        
        # Botones para añadir/quitar directorios
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        
        add_button = Gtk.Button.new_with_label("Añadir Directorio")
        add_button.set_icon_name("list-add-symbolic")
        add_button.connect("clicked", self.on_add_directory)
        button_box.append(add_button)
        
        remove_button = Gtk.Button.new_with_label("Quitar Seleccionado")
        remove_button.set_icon_name("list-remove-symbolic")
        remove_button.connect("clicked", self.on_remove_directory)
        button_box.append(remove_button)
        
        content_box.append(button_box)
        
        # Opciones adicionales
        options_group = Adw.PreferencesGroup()
        options_group.set_title("Opciones")
        
        self.update_existing_switch = Adw.SwitchRow()
        self.update_existing_switch.set_title("Actualizar comics existentes")
        self.update_existing_switch.set_subtitle("Volver a procesar archivos ya en la base de datos")
        options_group.add(self.update_existing_switch)
        
        content_box.append(options_group)
        
        main_box.append(content_box)
        self.set_child(main_box)
        
    def on_add_directory(self, button):
        """Añadir directorio a la lista"""
        dialog = Gtk.FileDialog()
        dialog.set_title("Seleccionar Directorio")
        
        def on_response(dialog, result):
            try:
                folder = dialog.select_folder_finish(result)
                if folder:
                    path = folder.get_path()
                    if path not in self.selected_directories:
                        self.selected_directories.append(path)
                        self.update_directory_list()
            except:
                pass
                
        dialog.select_folder(self, None, on_response)
        
    def on_remove_directory(self, button):
        """Quitar directorio seleccionado"""
        selected_row = self.directory_listbox.get_selected_row()
        if selected_row:
            index = selected_row.get_index()
            del self.selected_directories[index]
            self.update_directory_list()
            
    def update_directory_list(self):
        """Actualizar lista de directorios"""
        # Limpiar lista actual
        while True:
            row = self.directory_listbox.get_first_child()
            if row:
                self.directory_listbox.remove(row)
            else:
                break
                
        # Añadir directorios
        for directory in self.selected_directories:
            row = Adw.ActionRow()
            row.set_title(os.path.basename(directory))
            row.set_subtitle(directory)
            self.directory_listbox.append(row)
            
    def on_scan_clicked(self, button):
        """Iniciar escaneo"""
        if not self.selected_directories:
            return
            
        # Cerrar diálogo y mostrar progreso
        self.close()
        
        # Crear diálogo de progreso
        progress_dialog = ProgressDialog(self.parent_window, "Escaneando Comics")
        progress_dialog.present(self.parent_window)
        
        # Ejecutar escaneo en hilo separado
        def scan_thread():
            try:
                scanner = ComicScanner(
                    self.parent_window.enhanced_db_manager,
                    progress_dialog.update_progress
                )
                
                update_existing = self.update_existing_switch.get_active()
                success = scanner.scan_directories(self.selected_directories, update_existing)
                
                GLib.idle_add(lambda: self.on_scan_completed(progress_dialog, success))
                
            except Exception as e:
                print(f"Error en escaneo: {e}")
                GLib.idle_add(lambda: self.on_scan_completed(progress_dialog, False, str(e)))
                
        thread = threading.Thread(target=scan_thread)
        thread.daemon = True
        thread.start()
        
    def on_scan_completed(self, progress_dialog, success, error_message=""):
        """Manejar finalización del escaneo"""
        progress_dialog.finish(success, error_message)
        
        if success:
            self.parent_window.toast_manager.show_success("Escaneo completado")
            # Recargar datos si estamos en la sección de comics
            if self.parent_window.current_section == "comics":
                self.parent_window.load_comics()
        else:
            self.parent_window.toast_manager.show_error(f"Error en escaneo: {error_message}")


class StatsDialog(Adw.Dialog):
    """Diálogo de estadísticas"""
    
    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window
        
        self.set_title("Estadísticas")
        self.set_default_size(400, 300)
        
        self.create_content()
        
    def create_content(self):
        """Crear contenido de estadísticas"""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Header
        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label="Estadísticas"))
        
        close_button = Gtk.Button.new_with_label("Cerrar")
        close_button.connect("clicked", lambda b: self.close())
        header.pack_start(close_button)
        
        main_box.append(header)
        
        # Obtener estadísticas
        stats = self.parent_window.enhanced_db_manager.get_stats()
        
        # Contenido
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        
        # Grupo de estadísticas generales
        general_group = Adw.PreferencesGroup()
        general_group.set_title("Estadísticas Generales")
        
        # Comics totales
        comics_row = Adw.ActionRow()
        comics_row.set_title("Comics totales")
        comics_row.set_subtitle(str(stats.get("comics_count", 0)))
        general_group.add(comics_row)
        
        # Volúmenes
        volumes_row = Adw.ActionRow()
        volumes_row.set_title("Volúmenes")
        volumes_row.set_subtitle(str(stats.get("volumes_count", 0)))
        general_group.add(volumes_row)
        
        # Editoriales
        publishers_row = Adw.ActionRow()
        publishers_row.set_title("Editoriales")
        publishers_row.set_subtitle(str(stats.get("publishers_count", 0)))
        general_group.add(publishers_row)
        
        content_box.append(general_group)
        
        # Grupo de clasificación
        classification_group = Adw.PreferencesGroup()
        classification_group.set_title("Estado de Clasificación")
        
        classified_row = Adw.ActionRow()
        classified_row.set_title("Comics clasificados")
        classified_row.set_subtitle(str(stats.get("classified_comics", 0)))
        classification_group.add(classified_row)
        
        percentage_row = Adw.ActionRow()
        percentage_row.set_title("Porcentaje de clasificación")
        percentage = stats.get("classification_percentage", 0)
        percentage_row.set_subtitle(f"{percentage:.1f}%")
        classification_group.add(percentage_row)
        
        # Barra de progreso de clasificación
        progress_bar = Gtk.ProgressBar()
        progress_bar.set_fraction(percentage / 100.0)
        progress_bar.set_margin_start(12)
        progress_bar.set_margin_end(12)
        progress_bar.set_margin_top(8)
        classification_group.add(progress_bar)
        
        content_box.append(classification_group)
        
        main_box.append(content_box)
        self.set_child(main_box)


class SettingsDialog(Adw.Dialog):
    """Diálogo de configuración"""
    
    def __init__(self, parent_window, config_manager):
        super().__init__()
        self.parent_window = parent_window
        self.config_manager = config_manager
        
        self.set_title("Configuración")
        self.set_default_size(500, 600)
        
        self.create_content()
        
    def create_content(self):
        """Crear contenido de configuración"""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Header
        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label="Configuración"))
        
        cancel_button = Gtk.Button.new_with_label("Cancelar")
        cancel_button.connect("clicked", lambda b: self.close())
        header.pack_start(cancel_button)
        
        save_button = Gtk.Button.new_with_label("Guardar")
        save_button.add_css_class("suggested-action")
        save_button.connect("clicked", self.on_save_clicked)
        header.pack_end(save_button)
        
        main_box.append(header)
        
        # Contenido scrollable
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        
        # Configuración general
        general_group = Adw.PreferencesGroup()
        general_group.set_title("General")
        
        # Ruta de base de datos
        self.db_path_row = Adw.EntryRow()
        self.db_path_row.set_title("Ruta de base de datos")
        self.db_path_row.set_text(self.config_manager.get("database_path", "comics.db"))
        general_group.add(self.db_path_row)
        
        # Items por página
        self.items_per_page_spin = Adw.SpinRow()
        self.items_per_page_spin.set_title("Items por página")
        self.items_per_page_spin.set_range(10, 200)
        self.items_per_page_spin.set_increments(10, 50)
        self.items_per_page_spin.set_value(self.config_manager.get("items_per_page", 50))
        general_group.add(self.items_per_page_spin)
        
        content_box.append(general_group)
        
        # Configuración de apariencia
        appearance_group = Adw.PreferencesGroup()
        appearance_group.set_title("Apariencia")
        
        # Tema oscuro
        self.dark_theme_switch = Adw.SwitchRow()
        self.dark_theme_switch.set_title("Tema oscuro")
        self.dark_theme_switch.set_subtitle("Usar tema oscuro para la aplicación")
        self.dark_theme_switch.set_active(self.config_manager.get("dark_theme", False))
        self.dark_theme_switch.connect("notify::active", self.on_theme_changed)
        appearance_group.add(self.dark_theme_switch)
        
        content_box.append(appearance_group)
        
        # Configuración de directorios
        directories_group = Adw.PreferencesGroup()
        directories_group.set_title("Directorios de Escaneo Automático")
        directories_group.set_description("Directorios que se escanearán automáticamente al iniciar")
        
        # Lista de directorios
        self.auto_scan_dirs = self.config_manager.get("auto_scan_directories", []).copy()
        
        # Botones para gestionar directorios
        dir_button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        dir_button_box.set_margin_top(12)
        
        add_dir_button = Gtk.Button.new_with_label("Añadir Directorio")
        add_dir_button.set_icon_name("list-add-symbolic")
        add_dir_button.connect("clicked", self.on_add_auto_scan_dir)
        dir_button_box.append(add_dir_button)
        
        remove_dir_button = Gtk.Button.new_with_label("Quitar")
        remove_dir_button.set_icon_name("list-remove-symbolic")
        remove_dir_button.connect("clicked", self.on_remove_auto_scan_dir)
        dir_button_box.append(remove_dir_button)
        
        directories_group.add(dir_button_box)
        
        # Lista de directorios actuales
        self.auto_scan_listbox = Gtk.ListBox()
        self.auto_scan_listbox.add_css_class("boxed-list")
        self.auto_scan_listbox.set_margin_top(12)
        directories_group.add(self.auto_scan_listbox)
        
        self.update_auto_scan_list()
        
        content_box.append(directories_group)
        
        # Configuración avanzada
        advanced_group = Adw.PreferencesGroup()
        advanced_group.set_title("Avanzado")
        
        # Formatos soportados
        supported_formats = ", ".join(self.config_manager.get("supported_formats", [".cbr", ".cbz", ".pdf"]))
        formats_row = Adw.ActionRow()
        formats_row.set_title("Formatos soportados")
        formats_row.set_subtitle(supported_formats)
        advanced_group.add(formats_row)
        
        # Botón de backup
        backup_row = Adw.ActionRow()
        backup_row.set_title("Crear backup de la base de datos")
        backup_row.set_subtitle("Guardar una copia de seguridad")
        
        backup_button = Gtk.Button.new_with_label("Crear Backup")
        backup_button.set_valign(Gtk.Align.CENTER)
        backup_button.connect("clicked", self.on_create_backup)
        backup_row.add_suffix(backup_button)
        advanced_group.add(backup_row)
        
        content_box.append(advanced_group)
        
        scrolled.set_child(content_box)
        main_box.append(scrolled)
        self.set_child(main_box)
        
    def update_auto_scan_list(self):
        """Actualizar lista de directorios de escaneo automático"""
        # Limpiar lista
        while True:
            row = self.auto_scan_listbox.get_first_child()
            if row:
                self.auto_scan_listbox.remove(row)
            else:
                break
                
        # Añadir directorios
        for directory in self.auto_scan_dirs:
            row = Adw.ActionRow()
            row.set_title(os.path.basename(directory))
            row.set_subtitle(directory)
            self.auto_scan_listbox.append(row)
            
    def on_add_auto_scan_dir(self, button):
        """Añadir directorio de escaneo automático"""
        dialog = Gtk.FileDialog()
        dialog.set_title("Seleccionar Directorio")
        
        def on_response(dialog, result):
            try:
                folder = dialog.select_folder_finish(result)
                if folder:
                    path = folder.get_path()
                    if path not in self.auto_scan_dirs:
                        self.auto_scan_dirs.append(path)
                        self.update_auto_scan_list()
            except:
                pass
                
        dialog.select_folder(self, None, on_response)
        
    def on_remove_auto_scan_dir(self, button):
        """Quitar directorio de escaneo automático"""
        selected_row = self.auto_scan_listbox.get_selected_row()
        if selected_row:
            index = selected_row.get_index()
            if 0 <= index < len(self.auto_scan_dirs):
                del self.auto_scan_dirs[index]
                self.update_auto_scan_list()
                
    def on_theme_changed(self, switch, param):
        """Cambiar tema"""
        style_manager = Adw.StyleManager.get_default()
        if switch.get_active():
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        else:
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
            
    def on_create_backup(self, button):
        """Crear backup de la base de datos"""
        dialog = Gtk.FileDialog()
        dialog.set_title("Guardar Backup")
        
        # Configurar filtro para archivos de base de datos
        filter_db = Gtk.FileFilter()
        filter_db.set_name("Base de datos SQLite")
        filter_db.add_pattern("*.db")
        filter_db.add_pattern("*.sqlite")
        
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_db)
        dialog.set_filters(filters)
        
        def on_save_response(dialog, result):
            try:
                file = dialog.save_finish(result)
                if file:
                    backup_path = file.get_path()
                    success = self.parent_window.enhanced_db_manager.backup_database(backup_path)
                    if success:
                        self.parent_window.toast_manager.show_success("Backup creado correctamente")
                    else:
                        self.parent_window.toast_manager.show_error("Error creando backup")
            except:
                pass
                
        dialog.save(self, None, on_save_response)
        
    def on_save_clicked(self, button):
        """Guardar configuración"""
        # Guardar valores
        self.config_manager.set("database_path", self.db_path_row.get_text())
        self.config_manager.set("items_per_page", int(self.items_per_page_spin.get_value()))
        self.config_manager.set("dark_theme", self.dark_theme_switch.get_active())
        self.config_manager.set("auto_scan_directories", self.auto_scan_dirs)
        
        # Guardar a archivo
        self.config_manager.save_config()
        
        self.parent_window.toast_manager.show_success("Configuración guardada")
        self.close()


class EnhancedComicManagerApp(ComicManagerApp):
    """Aplicación principal mejorada"""
    
    def __init__(self):
        super().__init__()
        
        # Configurar tema inicial
        style_manager = Adw.StyleManager.get_default()
        style_manager.set_color_scheme(Adw.ColorScheme.PREFER_LIGHT)
        
    def do_activate(self):
        """Activar aplicación"""
        # Usar ventana mejorada en lugar de la básica
        window = EnhancedComicManagerWindow(self)
        window.present()
        
        # Ejecutar escaneo automático si hay directorios configurados
        self.auto_scan_on_startup(window)
        
    def auto_scan_on_startup(self, window):
        """Ejecutar escaneo automático al iniciar"""
        auto_scan_dirs = window.config_manager.get("auto_scan_directories", [])
        
        if auto_scan_dirs:
            # Ejecutar después de un breve delay para que la UI se cargue
            def delayed_scan():
                try:
                    scanner = ComicScanner(window.enhanced_db_manager)
                    scanner.scan_directories(auto_scan_dirs, update_existing=False)
                    
                    GLib.idle_add(lambda: window.toast_manager.show_success("Escaneo automático completado"))
                    GLib.idle_add(lambda: window.load_comics() if window.current_section == "comics" else None)
                    
                except Exception as e:
                    print(f"Error en escaneo automático: {e}")
                    GLib.idle_add(lambda: window.toast_manager.show_warning("Error en escaneo automático"))
                    
            # Ejecutar en hilo separado después de 2 segundos
            def start_scan():
                thread = threading.Thread(target=delayed_scan)
                thread.daemon = True
                thread.start()
                return False
                
            GLib.timeout_add(2000, start_scan)


def setup_application():
    """Configurar la aplicación antes de ejecutar"""
    # Asegurar directorios necesarios
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    thumbnails_dir = data_dir / "thumbnails"
    thumbnails_dir.mkdir(exist_ok=True)
    
    for subdir in ["comics", "comicbookinfo_issues", "volumenes", "editoriales"]:
        (thumbnails_dir / subdir).mkdir(exist_ok=True)
        
    # Crear directorio de imágenes por defecto si no existe
    images_dir = Path("images")
    images_dir.mkdir(exist_ok=True)
    
    # Crear imágenes por defecto básicas si no existen
    create_default_images(images_dir)


def create_default_images(images_dir):
    """Crear imágenes por defecto básicas"""
    try:
        from gi.repository import GdkPixbuf
        
        # Imagen por defecto para comics
        comic_default = images_dir / "Comic_sin_caratula.png"
        if not comic_default.exists():
            pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 120, 180)
            pixbuf.fill(0x3584E4ff)  # Azul
            pixbuf.savev(str(comic_default), "png", [], [])
            
        # Imagen por defecto para volúmenes
        volume_default = images_dir / "Volumen_sin_caratula.png"
        if not volume_default.exists():
            pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 120, 180)
            pixbuf.fill(0x33D17Aff)  # Verde
            pixbuf.savev(str(volume_default), "png", [], [])
            
        # Imagen por defecto para editoriales
        publisher_default = images_dir / "publisher_sin_logo.png"
        if not publisher_default.exists():
            pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 100, 100)
            pixbuf.fill(0xF66151ff)  # Rojo
            pixbuf.savev(str(publisher_default), "png", [], [])
            
    except Exception as e:
        print(f"Warning: No se pudieron crear imágenes por defecto: {e}")


def main():
    """Función principal"""
    # Configurar aplicación
    setup_application()
    
    # Crear y ejecutar aplicación
    app = EnhancedComicManagerApp()
    return app.run(sys.argv)


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)