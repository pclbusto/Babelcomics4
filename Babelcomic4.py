#!/usr/bin/env python3
"""
Comic Manager - Aplicación principal modularizada con funcionalidad de catalogación
Versión limpia que usa los módulos separados: selectable_card.py y thumbnail_generator.py
"""

import gi
import sys
import os
from pathlib import Path

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib, GObject, Pango, Gdk, Gio

# Importar SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Importar entidades y repositorios
try:
    from entidades import Base
    from entidades.comicbook_model import Comicbook
    from entidades.volume_model import Volume
    from entidades.publisher_model import Publisher
    from repositories.comicbook_repository_gtk4 import ComicbookRepository
    from repositories.volume_repository import VolumeRepository
    from repositories.publisher_repository import PublisherRepository
    from repositories.setup_repository import SetupRepository
    
    # Importar ComicbookInfo si está disponible
    try:
        from entidades.comicbook_info_model import ComicbookInfo
        print("ComicbookInfo importado correctamente")
    except ImportError:
        print("ComicbookInfo no disponible - funcionalidad de completitud limitada")
        ComicbookInfo = None
        
except ImportError as e:
    print(f"Error importando entidades: {e}")
    sys.exit(1)

# Importar módulos locales
try:
    from comic_cards import ComicCard, VolumeCard, PublisherCard
    from filter_dialog import AdvancedFilterDialog
    from selectable_card import SelectableCard, SelectionManager
    from thumbnail_generator import ThumbnailGenerator
    from about_dialog import show_about_dialog
    from comicvine_download_window import ComicVineDownloadWindow
    print("Módulos locales importados correctamente")
except ImportError as e:
    print(f"Error importando módulos locales: {e}")
    print("Asegúrate de tener todos los archivos: comic_cards.py, filter_dialog.py, selectable_card.py, thumbnail_generator.py")
    sys.exit(1)

# Intentar importar cataloging_window
try:
    from new_cataloging_window import CatalogingWindow
    print("Módulo de catalogación importado correctamente")
    CATALOGING_AVAILABLE = True
except ImportError as e:
    print(f"Módulo de catalogación no disponible: {e}")
    print("Funcionalidad de catalogación deshabilitada")
    CATALOGING_AVAILABLE = False
    CatalogingWindow = None

# Importar ventana de detalle de volumen
try:
    from volume_detail_window import VolumeDetailWindow
    print("Ventana de detalle de volumen importada correctamente")
    VOLUME_DETAIL_AVAILABLE = True
except ImportError as e:
    print(f"Error importando ventana de detalle: {e}")
    VOLUME_DETAIL_AVAILABLE = False

# Importar página de detalle de cómic
try:
    from comic_detail_page import create_comic_detail_page
    print("Página de detalle de cómic importada correctamente")
    COMIC_DETAIL_AVAILABLE = True
except ImportError as e:
    print(f"Error importando página de detalle de cómic: {e}")
    COMIC_DETAIL_AVAILABLE = False

# Importar lector de comics
try:
    from comic_reader import open_comic_with_reader
    print("Lector de comics importado correctamente")
    COMIC_READER_AVAILABLE = True
except ImportError as e:
    print(f"Error importando lector de comics: {e}")
    COMIC_READER_AVAILABLE = False


class ComicManagerWindow(Adw.ApplicationWindow):
    """Ventana principal modularizada"""
    
    def __init__(self, app):
        super().__init__(application=app)
        
        # Configurar ventana
        self.set_title("Comic Manager")
        self.maximize()
        
        # Estado de la aplicación
        self.current_view = "comics"
        self.current_filters = {}

        # Filtros independientes por vista
        self.search_states = {
            "comics": {"text": "", "filters": {}},
            "volumes": {"text": "", "filters": {}},
            "publishers": {"text": "", "filters": {}},
            "arcs": {"text": "", "filters": {}}
        }
        
        # Inicializar gestores
        self.selection_manager = SelectionManager()
        
        # Variables para lazy loading
        self.items_data = []
        self.loaded_items = 0
        self.batch_size = 20
        
        # Inicializar componentes
        self.init_database()
        self.thumbnail_generator = ThumbnailGenerator()
        self.thumbnail_generator.set_session(self.session)
        
        # Configurar callbacks del selection manager
        self.selection_manager.add_callback('selection_changed', self.on_selection_changed)
        self.selection_manager.add_callback('mode_changed', self.on_selection_mode_changed)
        
        # Crear interfaz
        self.setup_ui()
        
        # Configurar acciones y atajos
        self.setup_actions()
        self.setup_keyboard_shortcuts()
        
        # Cargar contenido inicial
        self.load_items_batch()
        
    def init_database(self):
        """Inicializar base de datos"""
        try:
            # Ruta de la base de datos
            db_path = "data/babelcomics.db"
            
            # Crear directorio si no existe
            os.makedirs("data", exist_ok=True)
            
            engine = create_engine(f'sqlite:///{db_path}', echo=False)
            Base.metadata.create_all(engine)
            Session = sessionmaker(bind=engine)
            self.session = Session()
            
            # Repositorios
            self.comic_repository = ComicbookRepository(self.session)
            self.volume_repository = VolumeRepository(self.session)
            self.publisher_repository = PublisherRepository(self.session)
            self.setup_repository = SetupRepository(self.session)

            # Cargar configuración
            self.config = self.setup_repository.obtener_o_crear_configuracion()
            
            print(f"Base de datos inicializada: {db_path}")
            
        except Exception as e:
            print(f"Error base de datos: {e}")
            self.session = None
            
    def setup_actions(self):
        """Configurar acciones GIO para los popovers"""
        # Crear acciones para el menú contextual
        catalog_action = Gio.SimpleAction.new("catalog_item", GLib.VariantType.new("s"))
        catalog_action.connect("activate", self.on_catalog_item_action)
        self.add_action(catalog_action)
        
        trash_action = Gio.SimpleAction.new("trash_item", GLib.VariantType.new("s"))
        trash_action.connect("activate", self.on_trash_item_action)
        self.add_action(trash_action)
        
        details_action = Gio.SimpleAction.new("show_details", GLib.VariantType.new("s"))
        details_action.connect("activate", self.on_show_details_action)
        self.add_action(details_action)

        # Acción para mostrar About
        about_action = Gio.SimpleAction.new("show_about", None)
        about_action.connect("activate", self.on_show_about_action)
        self.add_action(about_action)

        # Acción para mostrar Configuración
        config_action = Gio.SimpleAction.new("show_config", None)
        config_action.connect("activate", self.on_show_config_action)
        self.add_action(config_action)

        # Acción para descargar volúmenes
        download_volumes_action = Gio.SimpleAction.new("download_volumes", None)
        download_volumes_action.connect("activate", self.on_download_volumes_action)
        self.add_action(download_volumes_action)

        # Acción para regenerar portada
        regenerate_cover_action = Gio.SimpleAction.new("regenerate_cover", GLib.VariantType.new("s"))
        regenerate_cover_action.connect("activate", self.on_regenerate_cover_action)
        self.add_action(regenerate_cover_action)

        # Acción para abrir lector de comics
        read_comic_action = Gio.SimpleAction.new("read_comic", GLib.VariantType.new("s"))
        read_comic_action.connect("activate", self.on_read_comic_action)
        self.add_action(read_comic_action)

        # Acción para actualizar volumen desde ComicVine
        update_volume_action = Gio.SimpleAction.new("update_volume", GLib.VariantType.new("s"))
        update_volume_action.connect("activate", self.on_update_volume_action)
        self.add_action(update_volume_action)

        # Acciones para multiselección
        catalog_selected_action = Gio.SimpleAction.new("catalog_selected", None)
        catalog_selected_action.connect("activate", lambda action, param: self.on_catalog_selected(None))
        self.add_action(catalog_selected_action)

        trash_selected_action = Gio.SimpleAction.new("trash_selected", None)
        trash_selected_action.connect("activate", lambda action, param: self.on_trash_selected(None))
        self.add_action(trash_selected_action)
        
    def setup_keyboard_shortcuts(self):
        """Configurar atajos de teclado"""
        # Ctrl+A para seleccionar todo en modo selección
        select_all = Gtk.Shortcut()
        select_all.set_trigger(Gtk.ShortcutTrigger.parse_string("<Control>a"))
        select_all.set_action(Gtk.CallbackAction.new(self.on_select_all))
        
        # Escape para salir del modo selección
        escape = Gtk.Shortcut()
        escape.set_trigger(Gtk.ShortcutTrigger.parse_string("Escape"))
        escape.set_action(Gtk.CallbackAction.new(self.on_escape_pressed))
        
        # Delete para mover a papelera
        delete = Gtk.Shortcut()
        delete.set_trigger(Gtk.ShortcutTrigger.parse_string("Delete"))
        delete.set_action(Gtk.CallbackAction.new(self.on_delete_pressed))
        
        # Ctrl+M para alternar modo multiselección
        toggle_multiselect = Gtk.Shortcut()
        toggle_multiselect.set_trigger(Gtk.ShortcutTrigger.parse_string("<Control>m"))
        toggle_multiselect.set_action(Gtk.CallbackAction.new(self.on_toggle_multiselect))

        # Shift+Ctrl+C para abrir catalogación
        open_cataloging = Gtk.Shortcut()
        open_cataloging.set_trigger(Gtk.ShortcutTrigger.parse_string("<Shift><Control>c"))
        open_cataloging.set_action(Gtk.CallbackAction.new(self.on_open_cataloging_shortcut))

        # F5 para refresh/actualizar
        refresh = Gtk.Shortcut()
        refresh.set_trigger(Gtk.ShortcutTrigger.parse_string("F5"))
        refresh.set_action(Gtk.CallbackAction.new(self.on_refresh_shortcut))

        # Ctrl+F para enfocar búsqueda
        focus_search = Gtk.Shortcut()
        focus_search.set_trigger(Gtk.ShortcutTrigger.parse_string("<Control>f"))
        focus_search.set_action(Gtk.CallbackAction.new(self.on_focus_search_shortcut))

        # F1 para mostrar ayuda de shortcuts
        show_help = Gtk.Shortcut()
        show_help.set_trigger(Gtk.ShortcutTrigger.parse_string("F1"))
        show_help.set_action(Gtk.CallbackAction.new(self.on_show_shortcuts_help))

        # Ctrl+D para abrir ComicVine
        open_comicvine = Gtk.Shortcut()
        open_comicvine.set_trigger(Gtk.ShortcutTrigger.parse_string("<Control>d"))
        open_comicvine.set_action(Gtk.CallbackAction.new(self.on_open_comicvine_shortcut))

        # Shift+Ctrl+F para filtros avanzados
        open_filters = Gtk.Shortcut()
        open_filters.set_trigger(Gtk.ShortcutTrigger.parse_string("<Shift><Control>f"))
        open_filters.set_action(Gtk.CallbackAction.new(self.on_open_filters_shortcut))

        # Números 1-4 para cambiar vistas
        view1 = Gtk.Shortcut()
        view1.set_trigger(Gtk.ShortcutTrigger.parse_string("1"))
        view1.set_action(Gtk.CallbackAction.new(lambda w, a: self.on_switch_view_shortcut("comics")))

        view2 = Gtk.Shortcut()
        view2.set_trigger(Gtk.ShortcutTrigger.parse_string("2"))
        view2.set_action(Gtk.CallbackAction.new(lambda w, a: self.on_switch_view_shortcut("volumes")))

        view3 = Gtk.Shortcut()
        view3.set_trigger(Gtk.ShortcutTrigger.parse_string("3"))
        view3.set_action(Gtk.CallbackAction.new(lambda w, a: self.on_switch_view_shortcut("publishers")))

        view4 = Gtk.Shortcut()
        view4.set_trigger(Gtk.ShortcutTrigger.parse_string("4"))
        view4.set_action(Gtk.CallbackAction.new(lambda w, a: self.on_switch_view_shortcut("arcs")))

        # Space para toggle selección en modo multiselección (TEMPORALMENTE DESHABILITADO)
        # toggle_selection = Gtk.Shortcut()
        # toggle_selection.set_trigger(Gtk.ShortcutTrigger.parse_string("space"))
        # toggle_selection.set_action(Gtk.CallbackAction.new(self.on_space_toggle_selection))

        controller = Gtk.ShortcutController()
        controller.add_shortcut(select_all)
        controller.add_shortcut(escape)
        controller.add_shortcut(delete)
        controller.add_shortcut(toggle_multiselect)
        controller.add_shortcut(open_cataloging)
        controller.add_shortcut(refresh)
        controller.add_shortcut(focus_search)
        controller.add_shortcut(show_help)
        controller.add_shortcut(open_comicvine)
        controller.add_shortcut(open_filters)
        controller.add_shortcut(view1)
        controller.add_shortcut(view2)
        controller.add_shortcut(view3)
        controller.add_shortcut(view4)
        # controller.add_shortcut(toggle_selection)  # TEMPORALMENTE DESHABILITADO
        
        self.add_controller(controller)
            
    def setup_ui(self):
        """Configurar interfaz con sidebar overlay y Navigation View"""
        # Toast overlay para notificaciones
        self.toast_overlay = Adw.ToastOverlay()

        # Navigation View para la navegación fluida
        self.navigation_view = Adw.NavigationView()

        # Contenedor principal con overlay split view
        self.overlay_split_view = Adw.OverlaySplitView()
        self.overlay_split_view.set_sidebar_width_fraction(0.25)

        # Crear sidebar
        self.create_sidebar()

        # Crear página principal (grilla de volúmenes/comics)
        self.create_main_page()

        # Configurar área principal con NavigationView
        self.overlay_split_view.set_content(self.navigation_view)

        # Configurar jerarquía
        self.toast_overlay.set_child(self.overlay_split_view)
        self.set_content(self.toast_overlay)

        # CSS personalizado
        self.setup_css()

    def create_main_page(self):
        """Crear página principal como NavigationPage"""
        # Crear el contenido principal (sin el header, que va en NavigationPage)
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # Header bar
        header = Adw.HeaderBar()

        # Botón toggle del sidebar
        sidebar_button = Gtk.ToggleButton()
        sidebar_button.set_icon_name("sidebar-show-symbolic")
        sidebar_button.set_tooltip_text("Mostrar/ocultar sidebar")
        sidebar_button.bind_property("active", self.overlay_split_view, "show-sidebar",
                                   GObject.BindingFlags.BIDIRECTIONAL | GObject.BindingFlags.SYNC_CREATE)
        sidebar_button.set_active(True)
        header.pack_start(sidebar_button)

        # Botón de selección múltiple
        self.selection_button = Gtk.ToggleButton()
        self.selection_button.set_icon_name("object-select-symbolic")
        self.selection_button.set_tooltip_text("Modo selección (Ctrl+M)")
        self.selection_button.connect("toggled", self.on_selection_mode_toggled)
        header.pack_start(self.selection_button)

        # Entrada de búsqueda
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Buscar...")
        self.search_entry.set_size_request(300, -1)
        self.search_entry.connect("search-changed", self.on_search_changed)
        header.set_title_widget(self.search_entry)

        # Botones de acción (inicialmente ocultos)
        self.action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.action_box.set_visible(False)
        self.action_box.add_css_class("action-buttons-box")

        # Botón catalogar
        if CATALOGING_AVAILABLE:
            catalog_button = Gtk.Button()
            catalog_button.set_icon_name("view-grid-symbolic")
            catalog_button.set_tooltip_text("Catalogar seleccionados (Shift+Ctrl+C)")
            catalog_button.connect("clicked", self.on_catalog_selected)
            self.action_box.append(catalog_button)

        # Botón papelera
        trash_button = Gtk.Button()
        trash_button.set_icon_name("user-trash-symbolic")
        trash_button.set_tooltip_text("Mover a papelera")
        trash_button.connect("clicked", self.on_trash_selected)
        self.action_box.append(trash_button)

        header.pack_end(self.action_box)

        # Botón descargar volúmenes
        download_volumes_button = Gtk.Button()
        download_volumes_button.set_icon_name("folder-download-symbolic")
        download_volumes_button.set_tooltip_text("Descargar volúmenes de ComicVine")
        download_volumes_button.connect("clicked", self.on_download_volumes_clicked)
        header.pack_end(download_volumes_button)

        # Botón filtros avanzados
        self.filter_button = Gtk.Button()
        self.filter_button.set_icon_name("preferences-system-symbolic")
        self.filter_button.set_tooltip_text("Filtros avanzados")
        self.filter_button.connect("clicked", self.on_advanced_filters_clicked)
        # Agregar una clase CSS para asegurar que sea visible
        self.filter_button.add_css_class("suggested-action")
        header.pack_end(self.filter_button)

        # Botón actualizar
        refresh_button = Gtk.Button()
        refresh_button.set_icon_name("view-refresh-symbolic")
        refresh_button.set_tooltip_text("Actualizar")
        refresh_button.connect("clicked", self.on_refresh_clicked)
        header.pack_end(refresh_button)

        # Botón de menú principal
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        menu_button.set_tooltip_text("Menú principal")

        # Crear menú
        menu_model = Gio.Menu()
        menu_model.append("Descargar Volúmenes", "win.download_volumes")
        menu_model.append("Configuración", "win.show_config")
        menu_model.append("Acerca de", "win.show_about")

        menu_button.set_menu_model(menu_model)
        header.pack_end(menu_button)

        main_box.append(header)

        # Separador
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        main_box.append(separator)

        # Barra de estado
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        status_box.set_margin_start(12)
        status_box.set_margin_end(12)
        status_box.set_margin_top(8)
        status_box.set_margin_bottom(8)

        self.status_label = Gtk.Label(label="Cargando...")
        self.status_label.set_hexpand(True)
        self.status_label.set_halign(Gtk.Align.START)

        self.count_label = Gtk.Label(label="0 items")
        self.count_label.add_css_class("dim-label")

        # Label para selección
        self.selection_label = Gtk.Label(label="")
        self.selection_label.add_css_class("accent")
        self.selection_label.set_visible(False)

        status_box.append(self.status_label)
        status_box.append(self.selection_label)
        status_box.append(self.count_label)
        main_box.append(status_box)

        # Área de contenido scrollable
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scrolled_window.set_vexpand(True)

        # FlowBox para las cards
        self.flow_box = Gtk.FlowBox()
        self.flow_box.set_valign(Gtk.Align.START)
        self.flow_box.set_max_children_per_line(6)
        self.flow_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.flow_box.set_homogeneous(True)
        self.flow_box.set_margin_start(20)
        self.flow_box.set_margin_end(20)
        self.flow_box.set_margin_top(20)
        self.flow_box.set_margin_bottom(20)
        self.flow_box.set_column_spacing(15)
        self.flow_box.set_row_spacing(15)

        # Conectar scroll
        self.scrolled_window.connect("edge-reached", self.on_edge_reached)

        self.scrolled_window.set_child(self.flow_box)
        main_box.append(self.scrolled_window)

        # Crear NavigationPage principal
        self.main_page = Adw.NavigationPage()
        self.main_page.set_title("Comic Manager")
        self.main_page.set_child(main_box)

        # Agregar a NavigationView
        self.navigation_view.add(self.main_page)

        # Inicializar datos
        GLib.idle_add(self.load_items_batch)

    def create_sidebar(self):
        """Crear sidebar de navegación"""
        sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        sidebar_box.add_css_class("sidebar")
        
        # Header del sidebar
        sidebar_header = Adw.HeaderBar()
        sidebar_header.set_title_widget(Gtk.Label(label="Navegación"))
        sidebar_header.add_css_class("flat")
        sidebar_box.append(sidebar_header)
        
        # Lista de navegación
        self.nav_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.nav_list.add_css_class("navigation-sidebar")
        self.nav_list.set_margin_start(8)
        self.nav_list.set_margin_end(8)
        self.nav_list.set_margin_top(12)
        
        # Items de navegación
        nav_items = [
            ("comics", "Comics", "media-optical-symbolic"),
            ("volumes", "Volúmenes", "folder-symbolic"),
            ("publishers", "Editoriales", "building-symbolic"),
            ("arcs", "Arcos", "view-list-symbolic"),  # Para el futuro
        ]
        
        self.nav_rows = {}
        for item_id, title, icon_name in nav_items:
            # Crear el botón
            button = Gtk.Button()
            button.set_has_frame(False)
            button.add_css_class("navigation-button")
            
            # Contenido del botón
            button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            button_box.set_margin_start(12)
            button_box.set_margin_end(12)
            button_box.set_margin_top(8)
            button_box.set_margin_bottom(8)
            
            # Icono
            icon = Gtk.Image.new_from_icon_name(icon_name)
            button_box.append(icon)
            
            # Texto
            label = Gtk.Label(label=title)
            label.set_hexpand(True)
            label.set_halign(Gtk.Align.START)
            button_box.append(label)
            
            button.set_child(button_box)
            
            # Conectar evento
            button.connect("clicked", self.on_navigation_button_clicked, item_id)
            
            # Deshabilitar arcs por ahora
            if item_id == "arcs":
                button.set_sensitive(False)
                subtitle_label = Gtk.Label(label="Próximamente")
                subtitle_label.add_css_class("dim-label")
                subtitle_label.add_css_class("caption")
                button_box.append(subtitle_label)
            
            self.nav_list.append(button)
            self.nav_rows[item_id] = button
            
        # Marcar comics como seleccionado por defecto
        self.nav_rows["comics"].add_css_class("selected")
        self.selected_nav_button = self.nav_rows["comics"]
        sidebar_box.append(self.nav_list)
        
        # Estadísticas en sidebar
        stats_group = Adw.PreferencesGroup()
        stats_group.set_title("Estadísticas")
        stats_group.set_margin_top(20)
        
        self.stats_comics = Adw.ActionRow()
        self.stats_comics.set_title("Comics")
        self.stats_comics.set_subtitle("Cargando...")
        stats_group.add(self.stats_comics)
        
        self.stats_volumes = Adw.ActionRow()
        self.stats_volumes.set_title("Volúmenes")
        self.stats_volumes.set_subtitle("Cargando...")
        stats_group.add(self.stats_volumes)
        
        self.stats_publishers = Adw.ActionRow()
        self.stats_publishers.set_title("Editoriales")
        self.stats_publishers.set_subtitle("Cargando...")
        stats_group.add(self.stats_publishers)
        
        sidebar_box.append(stats_group)
        
        # Configurar sidebar
        self.overlay_split_view.set_sidebar(sidebar_box)

    def on_navigation_button_clicked(self, button, item_id):
        """Manejar click en botones de navegación"""
        print(f"BOTÓN CLICKEADO: {item_id}")
        
        new_view = item_id
        
        if new_view != self.current_view and button.get_sensitive():
            print(f"Cambiando vista de {self.current_view} → {new_view}")
            
            # Actualizar botón seleccionado visualmente
            if hasattr(self, 'selected_nav_button'):
                self.selected_nav_button.remove_css_class("selected")
            
            button.add_css_class("selected")
            self.selected_nav_button = button
            
            # Cambiar vista
            self.current_view = new_view
            
            # Salir del modo selección al cambiar vista
            if self.selection_manager.selection_mode:
                self.selection_button.set_active(False)
            
            # Limpiar contenido actual
            self.clear_content()
            
            # Actualizar interfaz para la nueva vista
            self.update_ui_for_view(new_view)
            
    def update_ui_for_view(self, view):
        """Actualizar UI según la vista"""
        placeholders = {
            "comics": "Buscar comics (ej: Superman+2015)...",
            "volumes": "Buscar volúmenes...",
            "publishers": "Buscar editoriales...",
            "arcs": "Buscar arcos..."
        }

        self.search_entry.set_placeholder_text(placeholders.get(view, "Buscar..."))

        # Guardar el estado actual antes de cambiar
        if hasattr(self, 'current_view') and self.current_view in self.search_states:
            self.search_states[self.current_view]["filters"] = self.current_filters.copy()
            print(f"💾 Guardando filtros para {self.current_view}: {self.current_filters}")

        # Restaurar estado de búsqueda de esta vista
        search_state = self.search_states.get(view, {"text": "", "filters": {}})
        self.search_entry.set_text(search_state["text"])
        self.current_filters = search_state["filters"].copy()
        print(f"🔄 Restaurando filtros para {view}: {self.current_filters}")

        # Actualizar estado visual del botón de filtros
        self.update_filter_button_state()

        # Cargar contenido para la nueva vista
        print(f"Cargando contenido para: {view}")
        self.load_items_batch()
        
    def clear_content(self):
        """Limpiar contenido actual"""
        while True:
            child = self.flow_box.get_first_child()
            if child:
                self.flow_box.remove(child)
            else:
                break

        self.items_data = []
        self.loaded_items = 0
        # NOTA: No limpiar current_filters aquí - los filtros persisten entre recargas
        self.selection_manager.clear_cards()
        
    def load_items_batch(self):
        """Cargar lote de items según la vista actual"""
        if not self.session:
            self.show_toast("Error: No hay conexión a la base de datos", "error")
            return
            
        try:
            # Si es la primera carga, obtener todos los items
            if not self.items_data:
                print(f"Primera carga para vista: {self.current_view}")
                
                if self.current_view == "comics":
                    self.items_data = self.get_filtered_comics()
                elif self.current_view == "volumes":
                    self.items_data = self.get_filtered_volumes()
                elif self.current_view == "publishers":
                    self.items_data = self.get_filtered_publishers()
                else:
                    print(f"Vista no implementada: {self.current_view}")
                    self.items_data = []
                    
                print(f"Items obtenidos: {len(self.items_data)}")
                    
                if not self.items_data:
                    self.show_empty_message()
                    return
                    
                # Actualizar estadísticas
                self.update_stats()
            
            # Cargar siguiente lote
            start_idx = self.loaded_items
            end_idx = min(start_idx + self.batch_size, len(self.items_data))
            
            if start_idx >= len(self.items_data):
                self.status_label.set_text("Todos los items cargados")
                return
                
            # Crear widgets para el lote actual
            print(f"Creando cards {start_idx}-{end_idx} para {self.current_view}")
            
            for i in range(start_idx, end_idx):
                item = self.items_data[i]
                try:
                    # Crear la card original
                    if self.current_view == "comics":
                        original_card = ComicCard(item, self.thumbnail_generator)
                        item_id = item.id_comicbook
                    elif self.current_view == "volumes":
                        original_card = VolumeCard(item, self.thumbnail_generator, self.session)
                        item_id = item.id_volume
                    elif self.current_view == "publishers":
                        original_card = PublisherCard(item, self.thumbnail_generator, self.session)
                        item_id = item.id_publisher
                    else:
                        print(f"Tipo de card no implementado: {self.current_view}")
                        continue
                        
                    # Envolver en SelectableCard
                    selectable_card = SelectableCard(original_card, item_id, self.current_view)

                    # Conectar señal de activación (doble click)
                    selectable_card.connect('item-activated', self.on_item_activated, item)

                    # Agregar al selection manager
                    self.selection_manager.add_card(selectable_card)

                    # Agregar al flow box
                    self.flow_box.append(selectable_card)
                    
                    print(f"Card seleccionable creada para {self.current_view}: {getattr(item, 'nombre', getattr(item, 'path', 'unknown'))}")
                    
                except Exception as e:
                    print(f"Error creando card seleccionable para {self.current_view}: {e}")
                    import traceback
                    traceback.print_exc()
            
            self.loaded_items = end_idx
            
            # Actualizar interfaz
            self.count_label.set_text(f"{self.loaded_items}/{len(self.items_data)} items")
            
            if self.loaded_items >= len(self.items_data):
                self.status_label.set_text("Todos los items cargados")
            else:
                self.status_label.set_text(f"Cargados {self.loaded_items} de {len(self.items_data)}")
                
        except Exception as e:
            print(f"Error cargando items: {e}")
            self.show_toast(f"Error cargando contenido: {e}", "error")
    
    def on_selection_mode_toggled(self, button):
        """Alternar modo de selección"""
        selection_mode = button.get_active()
        self.selection_manager.set_selection_mode(selection_mode)
        
    def on_selection_changed(self, selected_items):
        """Callback cuando cambia la selección"""
        count = len(selected_items)
        if count > 0:
            self.selection_label.set_text(f"{count} seleccionados")
            self.selection_label.set_visible(True)
        else:
            self.selection_label.set_visible(False)
            
    def on_selection_mode_changed(self, enabled):
        """Callback cuando cambia el modo de selección"""
        # Mostrar/ocultar botones de acción
        self.action_box.set_visible(enabled)
        
        # Agregar clase CSS al flowbox
        if enabled:
            self.flow_box.add_css_class("selection-mode-active")
        else:
            self.flow_box.remove_css_class("selection-mode-active")
            
        print(f"Modo selección: {'activado' if enabled else 'desactivado'}")
        
    def on_catalog_selected(self, button):
        """Catalogar items seleccionados"""
        selected_items = self.selection_manager.get_selected_items()
        
        if not selected_items:
            self.show_toast("No hay items seleccionados", "warning")
            return
            
        # Filtrar solo comics para catalogación
        comics_to_catalog = [item_id for item_id in selected_items 
                           if self.current_view == "comics"]
        
        if not comics_to_catalog:
            self.show_toast("Selecciona comics para catalogar", "warning")
            return
            
        print(f"Catalogando {len(comics_to_catalog)} comics...")
        self.open_cataloging_window(comics_to_catalog)
        
    def on_trash_selected(self, button):
        """Mover items seleccionados a papelera"""
        selected_items = self.selection_manager.get_selected_items()
        
        if not selected_items:
            self.show_toast("No hay items seleccionados", "warning")
            return
            
        # Confirmar acción
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading("Mover a papelera")
        dialog.set_body(f"¿Mover {len(selected_items)} items a la papelera?")
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("confirm", "Mover a papelera")
        dialog.set_response_appearance("confirm", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        
        dialog.connect("response", self.on_trash_confirmed)
        dialog.present()
        
    def on_trash_confirmed(self, dialog, response):
        """Confirmar movimiento a papelera"""
        if response == "confirm":
            selected_items = self.selection_manager.get_selected_items()
            self.move_items_to_trash(list(selected_items))

        # Salir del modo selección
        self.selection_button.set_active(False)
        
    def show_item_popover(self, card_widget, item_id, item_type, x, y):
        """Mostrar popover de acciones para un item"""
        popover = Gtk.PopoverMenu()
        popover.set_parent(card_widget)

        # Verificar si hay multiselección activa
        has_multiselection = self.selection_manager.selection_mode and self.selection_manager.get_selection_count() > 0
        selected_count = self.selection_manager.get_selection_count()

        # Crear menú
        menu = Gio.Menu()

        if has_multiselection:
            # Menú para multiselección
            if item_type == "comics" and CATALOGING_AVAILABLE:
                menu.append(f"Catalogar {selected_count} comics", "win.catalog_selected")

            menu.append(f"Mover {selected_count} items a papelera", "win.trash_selected")

        else:
            # Menú para item individual
            if item_type == "comics" and COMIC_READER_AVAILABLE:
                menu.append("Leer Comic", f"win.read_comic('{item_id}')")

            if item_type == "comics" and CATALOGING_AVAILABLE:
                menu.append("Catalogar", f"win.catalog_item('{item_id}')")

            if item_type == "comics":
                menu.append("Regenerar Portada", f"win.regenerate_cover('{item_id}')")

            if item_type == "volumes":
                menu.append("Actualizar desde ComicVine", f"win.update_volume('{item_id}')")

            menu.append("Mover a papelera", f"win.trash_item('{item_id}')")
            menu.append("Ver detalles", f"win.show_details('{item_id}')")

        popover.set_menu_model(menu)

        # Posicionar el popover
        rect = Gdk.Rectangle()
        rect.x = int(x)
        rect.y = int(y)
        rect.width = 1
        rect.height = 1
        popover.set_pointing_to(rect)

        popover.popup()
        
    def on_catalog_item_action(self, action, parameter):
        """Manejar acción de catalogar item individual"""
        if not CATALOGING_AVAILABLE:
            self.show_toast("Módulo de catalogación no disponible", "error")
            return
            
        item_id = parameter.get_string()
        try:
            item_id_int = int(item_id)
            if self.current_view == "comics":
                self.open_cataloging_window([item_id_int])
            else:
                self.show_toast("Solo se pueden catalogar comics", "warning")
        except ValueError:
            self.show_toast("ID de item inválido", "error")
            
    def on_trash_item_action(self, action, parameter):
        """Manejar acción de papelera para item individual"""
        item_id = parameter.get_string()
        try:
            item_id_int = int(item_id)
            self.move_items_to_trash(item_id_int)
        except ValueError:
            self.show_toast("ID de item inválido", "error")
            
    def on_show_details_action(self, action, parameter):
        """Mostrar detalles de un item"""
        item_id = parameter.get_string()
        # Implementar diálogo de detalles
        self.show_toast(f"Detalles de item {item_id} (por implementar)", "info")

    def on_regenerate_cover_action(self, action, parameter):
        """Regenerar portada/thumbnail de un comic"""
        item_id = parameter.get_string()
        try:
            item_id_int = int(item_id)
            self.regenerate_comic_cover(item_id_int)
        except ValueError:
            self.show_toast("ID de item inválido", "error")

    def on_read_comic_action(self, action, parameter):
        """Abrir comic con el lector integrado"""
        if not COMIC_READER_AVAILABLE:
            self.show_toast("Lector de comics no disponible", "error")
            return

        item_id = parameter.get_string()
        try:
            item_id_int = int(item_id)
            self.open_comic_reader(item_id_int)
        except ValueError:
            self.show_toast("ID de item inválido", "error")

    def on_update_volume_action(self, action, parameter):
        """Actualizar volumen desde ComicVine"""
        item_id = parameter.get_string()
        try:
            item_id_int = int(item_id)

            # Obtener el volumen desde la base de datos
            from entidades.volume_model import Volume
            volume = self.session.query(Volume).filter(Volume.id_volume == item_id_int).first()

            if not volume:
                self.show_toast("Volumen no encontrado", "error")
                return

            # Importar la función de actualización
            from volume_detail_page import update_volume_from_comicvine

            # Llamar a la función de actualización (sin tab_view ya que es desde el menú contextual)
            update_volume_from_comicvine(volume, self.session, self, None)

        except ValueError:
            self.show_toast("ID de volumen inválido", "error")
        except Exception as e:
            print(f"Error actualizando volumen: {e}")
            self.show_toast(f"Error actualizando volumen: {str(e)}", "error")

    def on_show_about_action(self, action, parameter):
        """Mostrar diálogo Acerca de (acción)"""
        show_about_dialog(self)

    def on_show_config_action(self, action, parameter):
        """Mostrar ventana de configuración (acción)"""
        self.show_config_window()

    def on_download_volumes_action(self, action, parameter):
        """Mostrar ventana de descarga de volúmenes (acción)"""
        self.on_download_volumes_clicked(None)

    def show_config_window(self):
        """Mostrar ventana de configuración"""
        try:
            from config_window import show_config_window
            show_config_window(self)
        except ImportError as e:
            print(f"Error importando ventana de configuración: {e}")
            self.show_toast("Error cargando configuración", "error")
        
    def move_items_to_trash(self, item_ids):
        """Mover items a papelera (acepta lista o ID único)"""
        # Si es un solo ID, convertir a lista
        if isinstance(item_ids, int):
            item_ids = [item_ids]

        if not item_ids:
            self.show_toast("No hay items para mover", "warning")
            return

        moved_count = 0

        try:
            for item_id in item_ids:
                if self.current_view == "comics":
                    comic = self.session.query(Comicbook).get(item_id)
                    if comic:
                        comic.en_papelera = True
                        moved_count += 1
                # Agregar lógica para otros tipos de items si es necesario

            if moved_count > 0:
                self.session.commit()
                if moved_count == 1:
                    self.show_toast("Comic movido a papelera", "success")
                else:
                    self.show_toast(f"{moved_count} items movidos a papelera", "success")

                # Refrescar vista
                self.clear_content()
                self.load_items_batch()
            else:
                self.show_toast("No se encontraron items válidos", "error")

        except Exception as e:
            print(f"Error moviendo items a papelera: {e}")
            self.show_toast(f"Error: {e}", "error")

    def regenerate_comic_cover(self, comic_id):
        """Regenerar thumbnail/portada de un comic específico"""
        try:
            print(f"\n=== REGENERANDO COVER PARA COMIC {comic_id} ===")

            # Obtener el comic de la base de datos
            comic = self.session.query(Comicbook).get(comic_id)
            if not comic:
                self.show_toast("Comic no encontrado", "error")
                return

            print(f"Comic encontrado: {comic.nombre_archivo}")
            print(f"Ruta del archivo: {comic.path}")

            # Verificar que el archivo existe
            if not os.path.exists(comic.path):
                self.show_toast("Archivo de comic no encontrado", "error")
                return

            print(f"Archivo existe: ✓")

            # Obtener ruta del thumbnail actual
            thumbnail_path = self.thumbnail_generator.get_cached_thumbnail_path(comic_id, "comics")
            print(f"Ruta del thumbnail: {thumbnail_path}")
            print(f"Thumbnail existe antes: {'✓' if thumbnail_path.exists() else '✗'}")

            # Limpiar thumbnail existente para forzar regeneración
            self.thumbnail_generator.clear_cache_for_item(comic_id, "comics")
            print(f"Cache limpiado: ✓")

            # Usar el flujo normal del ThumbnailGenerator que ahora tiene lógica inteligente
            print(f"Regenerando usando flujo normal con lógica inteligente...")
            self.thumbnail_generator.request_thumbnail(
                comic.path,
                comic.id_comicbook,
                "comics",
                lambda path: print(f"✓ Thumbnail regenerado: {path}" if path else "✗ Error regenerando")
            )

            # Verificar resultado después de un momento
            import time
            time.sleep(0.5)  # Dar tiempo al worker thread
            print(f"Thumbnail regenerado: {'✓' if thumbnail_path.exists() else '✗'}")

            self.show_toast("Portada regenerada exitosamente", "success")

            # Refrescar la vista actual para mostrar el nuevo thumbnail
            self.clear_content()
            self.load_items_batch()

        except Exception as e:
            print(f"Error regenerando portada: {e}")
            import traceback
            traceback.print_exc()
            self.show_toast(f"Error regenerando portada: {e}", "error")

    def open_comic_reader(self, comic_id):
        """Abrir comic con el lector integrado"""
        try:
            print(f"\n=== ABRIENDO LECTOR PARA COMIC {comic_id} ===")

            # Obtener el comic de la base de datos
            comic = self.session.query(Comicbook).get(comic_id)
            if not comic:
                self.show_toast("Comic no encontrado", "error")
                return

            print(f"Comic encontrado: {comic.nombre_archivo}")
            print(f"Ruta del archivo: {comic.path}")

            # Verificar que el archivo existe
            if not os.path.exists(comic.path):
                self.show_toast("Archivo de comic no encontrado", "error")
                return

            print(f"Archivo existe: ✓")

            # Obtener nombre del comic para el título
            comic_title = os.path.basename(comic.path)

            # Abrir el lector
            print(f"Abriendo lector para: {comic_title}")
            reader = open_comic_with_reader(
                comic.path,
                comic_title,
                self,
                scroll_threshold=self.config.scroll_threshold,
                scroll_cooldown=self.config.scroll_cooldown
            )

            if reader:
                self.show_toast("Abriendo lector de comics...", "info")
                print(f"✓ Lector abierto exitosamente")
            else:
                self.show_toast("Error abriendo lector de comics", "error")
                print(f"✗ Error abriendo lector")

        except Exception as e:
            print(f"Error abriendo lector: {e}")
            import traceback
            traceback.print_exc()
            self.show_toast(f"Error abriendo lector: {e}", "error")

    def on_select_all(self, widget, args):
        """Seleccionar todos los items en modo selección"""
        if self.selection_manager.selection_mode:
            self.selection_manager.select_all(visible_only=True)
            selected_count = self.selection_manager.get_selection_count()
            self.show_toast(f"{selected_count} items seleccionados", "info")
        return True
        
    def on_escape_pressed(self, widget, args):
        """Manejar tecla Escape"""
        if self.selection_manager.selection_mode:
            self.selection_button.set_active(False)
            return True
        return False
        
    def on_delete_pressed(self, widget, args):
        """Manejar tecla Delete"""
        if self.selection_manager.selection_mode and self.selection_manager.get_selection_count() > 0:
            self.on_trash_selected(None)
            return True
        return False

    def on_toggle_multiselect(self, widget, args):
        """Alternar modo multiselección con Ctrl+M"""
        current_state = self.selection_button.get_active()
        self.selection_button.set_active(not current_state)

        if not current_state:
            self.show_toast("Modo multiselección activado", "info")
        else:
            self.show_toast("Modo multiselección desactivado", "info")

        return True

    def on_open_cataloging_shortcut(self, widget, args):
        """Abrir catalogación con Ctrl+Shift+C"""
        # Solo funciona si estamos en vista de comics
        if self.current_view != "comics":
            self.show_toast("La catalogación solo está disponible para comics", "warning")
            return True

        # Si hay selección múltiple activa, catalogar los seleccionados
        if self.selection_manager.selection_mode:
            selected_items = self.selection_manager.get_selected_items()
            if selected_items:
                comic_ids = [int(item_id) for item_id in selected_items]
                self.show_toast(f"Abriendo catalogación para {len(comic_ids)} comics", "info")
                self.open_cataloging_window(comic_ids)
            else:
                self.show_toast("No hay comics seleccionados para catalogar", "warning")
        else:
            # Si no hay selección múltiple, activarla primero
            self.selection_button.set_active(True)
            self.show_toast("Activa la multiselección y selecciona comics para catalogar", "info")

        return True

    def on_refresh_shortcut(self, widget, args):
        """Actualizar contenido con F5"""
        self.on_refresh_clicked(None)
        self.show_toast("Contenido actualizado", "info")
        return True

    def on_focus_search_shortcut(self, widget, args):
        """Enfocar campo de búsqueda con Ctrl+F"""
        self.search_entry.grab_focus()
        return True

    def on_show_shortcuts_help(self, widget, args):
        """Mostrar ventana de ayuda de shortcuts con F1"""
        try:
            from shortcuts_help_window import create_shortcuts_help_window
            help_window = create_shortcuts_help_window(self)
            help_window.present()
        except ImportError as e:
            print(f"Error importando ventana de ayuda: {e}")
            self.show_toast("Error abriendo ayuda de shortcuts", "error")
        return True

    def on_open_comicvine_shortcut(self, widget, args):
        """Abrir ComicVine con Ctrl+D"""
        try:
            from comicvine_download_window import ComicVineDownloadWindow
            comicvine_window = ComicVineDownloadWindow(self, self.session)
            comicvine_window.present()
            self.show_toast("Ventana ComicVine abierta", "info")
        except ImportError as e:
            print(f"Error importando ComicVine: {e}")
            self.show_toast("Error abriendo ComicVine", "error")
        return True

    def on_open_filters_shortcut(self, widget, args):
        """Abrir filtros avanzados con Ctrl+Shift+F"""
        try:
            from filter_dialog import AdvancedFilterDialog
            filter_dialog = AdvancedFilterDialog(self, self.current_view)
            filter_dialog.connect('filters-applied', self.on_filters_applied)
            filter_dialog.present()
            self.show_toast("Filtros avanzados abiertos", "info")
        except ImportError as e:
            print(f"Error importando filtros: {e}")
            self.show_toast("Error abriendo filtros avanzados", "error")
        return True

    def on_space_toggle_selection(self, widget, args):
        """Toggle selección del item actual con Espacio (solo en modo multiselección)"""
        # Solo funciona en modo multiselección
        if not self.selection_manager.selection_mode:
            return False

        # Obtener el widget con foco o el primer widget visible
        focused_widget = self.get_focused_selectable_card()
        if focused_widget and hasattr(focused_widget, 'item_id'):
            # Toggle la selección del item
            if self.selection_manager.is_selected(focused_widget.item_id):
                self.selection_manager.deselect_item(focused_widget.item_id)
                self.show_toast("Item deseleccionado", "info")
            else:
                self.selection_manager.select_item(focused_widget.item_id)
                self.show_toast("Item seleccionado", "info")
            return True
        else:
            self.show_toast("No hay item activo para seleccionar", "warning")
            return False

    def get_focused_selectable_card(self):
        """Obtener el SelectableCard que tiene el foco o está destacado"""
        # Buscar en el flow_box el primer card visible o con foco
        if hasattr(self, 'flow_box'):
            child = self.flow_box.get_first_child()
            while child:
                if hasattr(child, 'get_child'):
                    selectable_card = child.get_child()
                    if hasattr(selectable_card, 'item_id'):
                        # Retornar el primero por ahora
                        # En el futuro se podría implementar navegación con flechas
                        return selectable_card
                child = child.get_next_sibling()
        return None

    def on_switch_view_shortcut(self, view_name):
        """Cambiar vista con números 1-4"""
        if hasattr(self, 'nav_rows') and view_name in self.nav_rows:
            button = self.nav_rows[view_name]
            if button.get_sensitive():
                # Simular click del botón de navegación
                self.on_navigation_button_clicked(button, view_name)
                self.show_toast(f"Vista cambiada a {view_name.title()}", "info")
            else:
                self.show_toast(f"Vista {view_name.title()} no disponible", "warning")
        return True

    def open_cataloging_window(self, comic_ids):
        try:
            from cataloging_window_improved import create_improved_cataloging_window
            window = create_improved_cataloging_window(self, comic_ids, self.session)
            if window:
                window.present()
        except ImportError:
            # Fallback a la ventana original
            from new_cataloging_window import create_cataloging_window
            window = create_cataloging_window(self, comic_ids, self.session)
            if window:
                window.present()
            
    def get_filtered_comics(self):
        """Obtener comics filtrados"""
        try:
            self.comic_repository.limpiar_filtros()

            # Aplicar filtro de búsqueda usando estado de la vista actual
            search_text = self.search_states["comics"]["text"]
            if search_text:
                # Soporte para búsquedas avanzadas con "+"
                self.apply_advanced_comic_search(search_text)

            # Aplicar filtros avanzados y rápidos
            print(f"🎯 Justo antes de apply_comic_filters(), current_filters = {self.current_filters}")
            self.apply_comic_filters()

            comics = self.comic_repository.obtener_todos_los_comics()
            print(f"Obtenidos {len(comics)} comics")
            return comics
        except Exception as e:
            print(f"Error obteniendo comics: {e}")
            return []
            
    def get_filtered_volumes(self):
        """Obtener volúmenes filtrados"""
        try:
            self.volume_repository.limpiar_filtros()

            # Aplicar filtro de búsqueda usando estado de la vista actual
            search_text = self.search_states["volumes"]["text"]
            if search_text:
                # Soporte para búsquedas avanzadas con "+" y "-"
                self.apply_advanced_volume_search(search_text)

            # Aplicar filtros avanzados
            self.apply_volume_filters()

            volumes = self.volume_repository.obtener_pagina(0, 1000, "nombre", "asc")
            print(f"Obtenidos {len(volumes)} volúmenes")
            return volumes
        except Exception as e:
            print(f"Error obteniendo volúmenes: {e}")
            return []
            
    def get_filtered_publishers(self):
        """Obtener editoriales filtradas"""
        try:
            self.publisher_repository.limpiar_filtros()

            # Aplicar filtro de búsqueda usando estado de la vista actual
            search_text = self.search_states["publishers"]["text"]
            if search_text:
                self.publisher_repository.filtrar(nombre=search_text)

            publishers = self.publisher_repository.obtener_pagina(0, 1000, "nombre", "asc")
            print(f"Obtenidas {len(publishers)} editoriales")
            return publishers
        except Exception as e:
            print(f"Error obteniendo editoriales: {e}")
            return []

    def apply_advanced_comic_search(self, search_text):
        """Aplicar búsqueda avanzada para comics con soporte para operadores"""
        try:
            # Si contiene "+" o "-", es una búsqueda con operadores
            if "+" in search_text or "-" in search_text:
                print(f"🔍 Búsqueda avanzada con operadores: {search_text}")

                # Separar términos por operadores
                include_terms = []
                exclude_terms = []

                # Primero dividir por "+" para obtener segmentos
                plus_segments = search_text.split("+")

                for segment in plus_segments:
                    segment = segment.strip()
                    if not segment:
                        continue

                    # Si el segmento contiene "-", dividirlo
                    if "-" in segment:
                        # Dividir por "-" y procesar
                        minus_parts = segment.split("-")
                        # El primer elemento es inclusión, el resto son exclusiones
                        if minus_parts[0].strip():
                            include_terms.append(minus_parts[0].strip())

                        for exclude_part in minus_parts[1:]:
                            if exclude_part.strip():
                                exclude_terms.append(exclude_part.strip())
                    else:
                        # Término simple de inclusión
                        include_terms.append(segment)

                print(f"  📥 Términos a incluir: {include_terms}")
                print(f"  📤 Términos a excluir: {exclude_terms}")

                # Separar términos numéricos y de texto para inclusión
                numeric_include = [int(term) for term in include_terms if term.isdigit()]
                text_include = [term for term in include_terms if not term.isdigit()]

                # Separar términos numéricos y de texto para exclusión
                numeric_exclude = [int(term) for term in exclude_terms if term.isdigit()]
                text_exclude = [term for term in exclude_terms if not term.isdigit()]

                # Aplicar filtros de inclusión
                for year in numeric_include:
                    self.comic_repository.filtrar_año_o_numero(year)
                    print(f"  ✅ Incluyendo año/número: {year}")

                if text_include:
                    self.comic_repository.filtrar_multiple_path_terms(text_include)
                    print(f"  ✅ Incluyendo términos (AND): {text_include}")

                # Aplicar filtros de exclusión
                if text_exclude:
                    self.comic_repository.filtrar_path_exclude_terms(text_exclude)
                    print(f"  ❌ Excluyendo términos: {text_exclude}")

                # Para números en exclusión, usar filtro especial si es necesario
                # (por ahora solo manejamos texto en exclusión)

            else:
                # Búsqueda simple
                self.comic_repository.filtrar(path=search_text)
                print(f"🔍 Búsqueda simple: {search_text}")

        except Exception as e:
            print(f"Error en búsqueda avanzada: {e}")
            # Fallback a búsqueda simple
            self.comic_repository.filtrar(path=search_text)

    def apply_advanced_volume_search(self, search_text):
        """Aplicar búsqueda avanzada para volúmenes con soporte para operadores"""
        try:
            # Si contiene "+" o "-", es una búsqueda con operadores
            if "+" in search_text or "-" in search_text:
                print(f"🔍 Búsqueda avanzada de volúmenes con operadores: {search_text}")

                # Separar términos por operadores
                include_terms = []
                exclude_terms = []

                # Primero dividir por "+" para obtener segmentos
                plus_segments = search_text.split("+")

                for segment in plus_segments:
                    segment = segment.strip()
                    if not segment:
                        continue

                    # Si el segmento contiene "-", dividirlo
                    if "-" in segment:
                        # Dividir por "-" y procesar
                        minus_parts = segment.split("-")
                        # El primer elemento es inclusión, el resto son exclusiones
                        if minus_parts[0].strip():
                            include_terms.append(minus_parts[0].strip())

                        for exclude_part in minus_parts[1:]:
                            if exclude_part.strip():
                                exclude_terms.append(exclude_part.strip())
                    else:
                        # Término simple de inclusión
                        include_terms.append(segment)

                print(f"  📥 Términos a incluir en volúmenes: {include_terms}")
                print(f"  📤 Términos a excluir en volúmenes: {exclude_terms}")

                # Separar términos numéricos y de texto para inclusión
                numeric_include = [int(term) for term in include_terms if term.isdigit()]
                text_include = [term for term in include_terms if not term.isdigit()]

                # Separar términos numéricos y de texto para exclusión
                text_exclude = [term for term in exclude_terms if not term.isdigit()]

                # Aplicar filtros de inclusión
                for year in numeric_include:
                    self.volume_repository.filtrar_año_o_numero(year)
                    print(f"  ✅ Incluyendo año/número en volumen: {year}")

                if text_include:
                    self.volume_repository.filtrar_multiple_name_terms(text_include)
                    print(f"  ✅ Incluyendo términos en volumen (AND): {text_include}")

                # Aplicar filtros de exclusión
                if text_exclude:
                    self.volume_repository.filtrar_name_exclude_terms(text_exclude)
                    print(f"  ❌ Excluyendo términos en volumen: {text_exclude}")

            else:
                # Búsqueda simple
                self.volume_repository.filtrar(nombre=search_text)
                print(f"🔍 Búsqueda simple de volumen: {search_text}")

        except Exception as e:
            print(f"Error en búsqueda avanzada de volúmenes: {e}")
            # Fallback a búsqueda simple
            self.volume_repository.filtrar(nombre=search_text)

    def apply_comic_filters(self):
        """Aplicar filtros para comics"""
        print(f"🔍 Aplicando filtros de comics. Filtros actuales: {self.current_filters}")

        # Manejar filtro de papelera
        if 'include_trash' in self.current_filters:
            print(f"🗑️ Incluyendo elementos en papelera")
            # No aplicar filtro de papelera - mostrar todos
        elif 'exclude_trash' in self.current_filters:
            print(f"🗑️ Aplicando filtro de papelera: exclude_trash=True")
            self.comic_repository.filtrar(en_papelera=False)
        else:
            # Si no hay filtro explícito, por defecto excluir papelera
            print(f"🗑️ Aplicando filtro por defecto: excluyendo papelera")
            self.comic_repository.filtrar(en_papelera=False)

        # Filtros avanzados
        if 'classification' in self.current_filters:
            classification_value = self.current_filters['classification']
            print(f"📋 Aplicando filtro de clasificación: is_classified={classification_value}")
            self.comic_repository.filtrar(is_classified=classification_value)

        if 'quality_range' in self.current_filters:
            min_quality, max_quality = self.current_filters['quality_range']
            print(f"⭐ Aplicando filtro de calidad: {min_quality}-{max_quality}")
            # Aquí necesitarías implementar el filtro de calidad en el repositorio

        print(f"✅ Filtros finales aplicados al repositorio: {self.comic_repository.filtros}")
        
    def apply_volume_filters(self):
        """Aplicar filtros para volúmenes"""
        print(f"🔍 Aplicando filtros de volúmenes. Filtros actuales: {self.current_filters}")

        if 'year_range' in self.current_filters:
            min_year, max_year = self.current_filters['year_range']
            print(f"📅 Aplicando filtro de rango de años: {min_year}-{max_year}")
            self.volume_repository.filtros['year_range'] = (min_year, max_year)

        if 'count_range' in self.current_filters:
            min_count, max_count = self.current_filters['count_range']
            print(f"📊 Aplicando filtro de cantidad de números: {min_count}-{max_count}")
            self.volume_repository.filtros['count_range'] = (min_count, max_count)

        if 'completion' in self.current_filters:
            completion_level = self.current_filters['completion']
            print(f"✅ Aplicando filtro de completitud: nivel {completion_level}")
            # This filter would need special handling based on completion percentage
            # For now, we'll log it but not implement the complex logic

        if 'publisher_name' in self.current_filters:
            publisher_filter = self.current_filters['publisher_name']
            print(f"🏢 Aplicando filtro de editorial: {publisher_filter}")
            self.volume_repository.filtros['publisher_name'] = publisher_filter

        print(f"✅ Filtros finales aplicados al repositorio de volúmenes: {self.volume_repository.filtros}")
            
    def show_empty_message(self):
        """Mostrar mensaje cuando no hay items"""
        message_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        message_box.set_halign(Gtk.Align.CENTER)
        message_box.set_valign(Gtk.Align.CENTER)
        message_box.set_margin_top(100)
        
        icons = {
            "comics": "media-optical-symbolic",
            "volumes": "folder-symbolic", 
            "publishers": "building-symbolic",
            "arcs": "view-list-symbolic"
        }
        
        icon = Gtk.Image.new_from_icon_name(icons.get(self.current_view, "folder-open-symbolic"))
        icon.set_icon_size(Gtk.IconSize.LARGE)
        icon.add_css_class("dim-label")
        
        title_label = Gtk.Label(label=f"No hay {self.current_view}")
        title_label.add_css_class("title-2")
        title_label.add_css_class("dim-label")
        
        subtitle_label = Gtk.Label(label="Intenta cambiar los filtros o añadir contenido")
        subtitle_label.add_css_class("dim-label")
        
        message_box.append(icon)
        message_box.append(title_label)
        message_box.append(subtitle_label)
        
        self.flow_box.append(message_box)
        self.status_label.set_text("Sin contenido")
        self.count_label.set_text("0 items")
        
    def update_stats(self):
        """Actualizar estadísticas en el sidebar"""
        try:
            # Contar items
            comic_count = self.session.query(Comicbook).count()
            self.stats_comics.set_subtitle(f"{comic_count} comics")
            
            volume_count = self.session.query(Volume).count()
            self.stats_volumes.set_subtitle(f"{volume_count} volúmenes")
            
            publisher_count = self.session.query(Publisher).count()
            self.stats_publishers.set_subtitle(f"{publisher_count} editoriales")
            
        except Exception as e:
            print(f"Error actualizando estadísticas: {e}")
            
    def on_search_changed(self, entry):
        """Manejar cambio en búsqueda"""
        new_text = entry.get_text().strip()

        # Obtener texto actual de la vista
        current_search = self.search_states[self.current_view]["text"]

        # Solo buscar si el texto cambió significativamente
        if new_text != current_search:
            # Guardar estado de búsqueda para esta vista
            self.search_states[self.current_view]["text"] = new_text

            # Debounce: usar timeout para evitar demasiadas búsquedas
            if hasattr(self, 'search_timeout'):
                GLib.source_remove(self.search_timeout)

            self.search_timeout = GLib.timeout_add(300, self.perform_search)
        
    def perform_search(self):
        """Ejecutar búsqueda"""
        search_text = self.search_states[self.current_view]["text"]
        print(f"Buscando: '{search_text}' en {self.current_view}")
        self.clear_content()
        self.load_items_batch()
        return False  # No repetir timeout
        
    def on_advanced_filters_clicked(self, button):
        """Abrir filtros avanzados"""
        try:
            dialog = AdvancedFilterDialog(self, self.current_view)
            dialog.present()
            print(f"Abriendo filtros avanzados para {self.current_view}")
        except Exception as e:
            print(f"Error abriendo filtros: {e}")
            self.show_toast(f"Error abriendo filtros: {e}", "error")

    def on_download_volumes_clicked(self, button):
        """Abrir ventana de descarga de volúmenes"""
        try:
            download_window = ComicVineDownloadWindow(self, self.session)
            download_window.present()
            print("Abriendo ventana de descarga de volúmenes")
        except Exception as e:
            print(f"Error abriendo ventana de descarga: {e}")
            self.show_toast(f"Error abriendo descarga de volúmenes: {e}", "error")
        
    def apply_advanced_filters(self, filters):
        """Aplicar filtros avanzados desde el diálogo"""
        print(f"🎛️ Filtros recibidos desde diálogo: {filters}")
        print(f"🗂️ Filtros actuales antes de actualizar: {self.current_filters}")

        self.current_filters.update(filters)
        print(f"🔄 Filtros actuales después de actualizar: {self.current_filters}")

        # Guardar los filtros en el estado de la vista actual
        if self.current_view in self.search_states:
            self.search_states[self.current_view]["filters"] = self.current_filters.copy()
            print(f"💾 Filtros guardados en estado de {self.current_view}")

        # Actualizar indicador visual del botón de filtros
        self.update_filter_button_state()

        self.clear_content()
        self.load_items_batch()

        # Mostrar confirmación
        self.show_toast(f"Filtros aplicados para {self.current_view}", "success")

    def update_filter_button_state(self):
        """Actualizar el estado visual del botón de filtros"""
        try:
            if self.current_filters:
                # Hay filtros activos - mostrar como activo
                self.filter_button.remove_css_class("suggested-action")
                self.filter_button.add_css_class("accent")
                filter_count = len(self.current_filters)
                self.filter_button.set_tooltip_text(f"Filtros avanzados ({filter_count} activos)")
            else:
                # Sin filtros - mostrar normal
                self.filter_button.remove_css_class("accent")
                self.filter_button.add_css_class("suggested-action")
                self.filter_button.set_tooltip_text("Filtros avanzados")
        except Exception as e:
            print(f"Error actualizando estado del botón de filtros: {e}")

    def on_filters_applied(self, dialog, filters):
        """Callback cuando se aplican filtros desde el diálogo"""
        self.apply_advanced_filters(filters)
        # Recargar contenido con los nuevos filtros
        self.clear_content()
        GLib.idle_add(self.load_items_batch)
        # Mostrar notificación
        filter_count = len(filters)
        if filter_count > 0:
            self.show_toast(f"✅ {filter_count} filtros aplicados", "info")
        else:
            self.show_toast("Filtros limpiados", "info")

    def show_toast(self, message, toast_type="info"):
        """Mostrar notificación toast"""
        toast = Adw.Toast()
        toast.set_title(message)
        toast.set_timeout(3)
        
        if toast_type == "error":
            toast.set_button_label("OK")
            
        self.toast_overlay.add_toast(toast)
        
    def on_edge_reached(self, scrolled, position):
        """Auto-cargar al llegar al final"""
        if position == Gtk.PositionType.BOTTOM:
            if self.loaded_items < len(self.items_data):
                GLib.idle_add(self.load_items_batch)
        
    def on_refresh_clicked(self, button):
        """Actualizar contenido"""
        print(f"Actualizando {self.current_view}")
        self.show_toast("Actualizando contenido...", "info")
        self.clear_content()
        GLib.idle_add(self.load_items_batch)

    def on_item_activated(self, selectable_card, item):
        """Manejar activación de item (doble click)"""
        print(f"Item activado: {getattr(item, 'nombre', 'Unknown')} (tipo: {self.current_view})")

        if self.current_view == "volumes" and VOLUME_DETAIL_AVAILABLE:
            # Navegar al detalle del volumen
            try:
                self.navigate_to_volume_detail(item)
                print(f"Navegando al detalle del volumen: {item.nombre}")
            except Exception as e:
                print(f"Error navegando al detalle del volumen: {e}")
                self.show_toast("Error abriendo detalle del volumen", "error")

        elif self.current_view == "comics" and COMIC_DETAIL_AVAILABLE:
            # Navegar al detalle del cómic
            try:
                self.navigate_to_comic_detail(item)
                print(f"Navegando al detalle del cómic: {os.path.basename(item.path)}")
            except Exception as e:
                print(f"Error navegando al detalle del cómic: {e}")
                self.show_toast("Error abriendo detalle del cómic", "error")

        elif self.current_view == "publishers":
            # Aquí podrías agregar detalle de editorial en el futuro
            print(f"Detalle de editorial no implementado aún")
            self.show_toast("Detalle de editorial no implementado", "info")

        else:
            print(f"Detalle no disponible para: {self.current_view}")

    def navigate_to_volume_detail(self, volume):
        """Navegar al detalle del volumen usando NavigationView"""
        try:
            # Crear página de detalle del volumen
            volume_detail_page = self.create_volume_detail_page(volume)

            # Navegar a la página
            self.navigation_view.push(volume_detail_page)

        except Exception as e:
            print(f"Error creando página de detalle: {e}")
            import traceback
            traceback.print_exc()

    def create_volume_detail_page(self, volume):
        """Crear página de detalle del volumen como NavigationPage"""
        from volume_detail_page import create_volume_detail_page_with_header

        # Crear página completa con header y botón de actualización
        detail_page = create_volume_detail_page_with_header(volume, self.session, self.thumbnail_generator, self)

        # Guardar referencia al volumen para uso posterior
        detail_page.volume = volume
        detail_page.main_window = self

        return detail_page

    def navigate_to_physical_comics(self, comic_info):
        """Navegar a la vista de cómics físicos"""
        try:
            # Crear página de cómics físicos
            physical_page = self.create_physical_comics_page(comic_info)

            # Navegar a la página
            self.navigation_view.push(physical_page)

        except Exception as e:
            print(f"Error creando página de físicos: {e}")
            import traceback
            traceback.print_exc()

    def create_physical_comics_page(self, comic_info):
        """Crear página de cómics físicos como NavigationPage"""
        from physical_comics_page import create_physical_comics_content

        # Crear contenido de físicos
        content = create_physical_comics_content(comic_info, self.session, self.thumbnail_generator)

        # Crear NavigationPage
        physical_page = Adw.NavigationPage()
        title = f"Físicos: {comic_info.titulo or f'Issue #{comic_info.numero}'}"
        physical_page.set_title(title)
        physical_page.set_child(content)

        # Guardar referencia para uso posterior
        physical_page.comic_info = comic_info
        physical_page.main_window = self

        return physical_page

    def navigate_to_comic_detail(self, comic):
        """Navegar al detalle del cómic usando NavigationView"""
        try:
            # Crear página de detalle del cómic
            comic_detail_page = create_comic_detail_page(comic, self.session, self.thumbnail_generator, self)
            # Navegar a la página
            self.navigation_view.push(comic_detail_page)
        except Exception as e:
            print(f"Error creando página de detalle del cómic: {e}")
            import traceback
            traceback.print_exc()

    def setup_css(self):
        """Configurar CSS personalizado"""
        css_provider = Gtk.CssProvider()
        css = """
        .sidebar {
            background-color: @sidebar_bg_color;
            border-right: 1px solid @borders;
        }
        
        .navigation-sidebar {
            background: transparent;
        }
        
        .navigation-button {
            border-radius: 6px;
            margin: 2px 0;
            padding: 0;
        }
        
        .navigation-button:hover {
            background-color: alpha(@accent_bg_color, 0.1);
        }
        
        .navigation-button.selected {
            background-color: @accent_bg_color;
            color: @accent_fg_color;
        }
        
        .navigation-button.selected:hover {
            background-color: @accent_bg_color;
        }
        
        .cover-image {
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            border: 1px solid alpha(@borders, 0.3);
        }
        
        .card {
            transition: all 200ms ease;
            background-color: @card_bg_color;
            border-radius: 12px;
        }
        
        .card:hover {
            box-shadow: 0 8px 16px rgba(0,0,0,0.2);
            transform: translateY(-2px);
        }
        
        .success {
            color: @success_color;
        }
        
        .warning {
            color: @warning_color;
        }
        
        .accent {
            color: @accent_bg_color;
        }
        
        .completion-bar {
            border-radius: 4px;
            min-height: 6px;
        }
        
        .completion-bar progress {
            border-radius: 4px;
        }
        
        /* Estilos para selección múltiple */
        .selection-checkbox {
            background: rgba(0, 0, 0, 0.8);
            border-radius: 12px;
            min-width: 24px;
            min-height: 24px;
            border: 2px solid white;
        }
        
        .selection-checkbox:checked {
            background: @accent_bg_color;
            color: white;
        }
        
        .selected-item {
            box-shadow: 0 0 0 3px @accent_bg_color;
            border-radius: 12px;
            transform: scale(0.98);
            transition: all 200ms ease;
        }
        
        .selected-item .card {
            opacity: 0.9;
        }
        
        .action-buttons-box {
            background: @headerbar_bg_color;
            border-radius: 8px;
            padding: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .selection-mode-active {
            background: alpha(@accent_bg_color, 0.05);
            border-radius: 8px;
        }
        
        /* Animaciones */
        .fade-in {
            animation: fadeIn 300ms ease;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        """
        css_provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )


class ComicManagerApp(Adw.Application):
    """Aplicación principal"""
    
    def __init__(self):
        super().__init__(application_id="Babelcomics4")
        
    def do_activate(self):
        """Activar aplicación"""
        window = ComicManagerWindow(self)
        window.present()


def check_requirements():
    """Verificar requisitos antes de ejecutar"""
    print("Verificando requisitos...")
    
    # Verificar dependencias
    try:
        from gi.repository import Pango
        print("✓ Pango disponible")
    except ImportError:
        print("✗ Pango requerido")
        return False
    
    # Verificar archivos requeridos
    required_files = [
        "entidades/__init__.py",
        "entidades/comicbook_model.py",
        "entidades/volume_model.py",
        "entidades/publisher_model.py",
        "repositories/__init__.py",
        "repositories/comicbook_repository_gtk4.py",
        "repositories/volume_repository.py",
        "repositories/publisher_repository.py"
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"✗ Archivo requerido no encontrado: {file_path}")
            return False
        else:
            print(f"✓ {file_path}")
            
    # Verificar módulos locales
    module_files = [
        "comic_cards.py",
        "filter_dialog.py",
        "selectable_card.py",
        "thumbnail_generator.py"
    ]
    
    missing_modules = []
    for file_path in module_files:
        if not os.path.exists(file_path):
            missing_modules.append(file_path)
        else:
            print(f"✓ {file_path}")
            
    if missing_modules:
        print(f"✗ Módulos no encontrados: {missing_modules}")
        print("Asegúrate de tener todos los archivos de módulos")
        return False
            
    print("✓ Todos los archivos requeridos encontrados")
    return True


def main():
    """Función principal"""
    print("Iniciando Comic Manager modularizado...")
    
    # Verificar requisitos
    if not check_requirements():
        print("Faltan requisitos. No se puede ejecutar la aplicación.")
        return 1
    
    # Crear directorios necesarios
    directories = [
        "data",
        "data/thumbnails",
        "data/thumbnails/comics",
        "data/thumbnails/volumes", 
        "data/thumbnails/publishers"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        
    print("✓ Directorios creados/verificados")
    
    # Verificar si existe la base de datos
    db_path = "data/babelcomics.db"
    if os.path.exists(db_path):
        print(f"✓ Base de datos encontrada: {db_path}")
    else:
        print(f"⚠ Base de datos no encontrada: {db_path}")
        print("  Se creará automáticamente si es necesario")
    
    # Crear aplicación
    try:
        app = ComicManagerApp()
        print("✓ Aplicación creada")
        exit_code = app.run(sys.argv)
        print("✓ Aplicación cerrada correctamente")
        return exit_code
        
    except Exception as e:
        print(f"✗ Error ejecutando aplicación: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)