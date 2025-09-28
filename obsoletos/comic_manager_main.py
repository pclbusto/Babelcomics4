#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GdkPixbuf, Gio, GLib, Gdk, GObject
import os
import sys
from pathlib import Path

# Importar los modelos y repositorios
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from entidades import Base
from entidades.comicbook_model import Comicbook
from entidades.volume_model import Volume
from entidades.publisher_model import Publisher
from repositories.comicbook_repository_gtk4 import ComicbookRepository
from repositories.volume_repository import VolumeRepository
from repositories.publisher_repository import PublisherRepository

# Importar componentes adicionales
from comic_detail_widget import ComicDetailDialog, ImprovedComicCoverWidget
from obsoletos.comic_search_filter import SearchFilterDialog, QuickSearchBar


# La clase ComicCoverWidget se reemplaza por ImprovedComicCoverWidget del módulo importado


class ComicManagerWindow(Adw.ApplicationWindow):
    """Ventana principal de la aplicación"""
    
    def __init__(self, app):
        super().__init__(application=app)
        self.app = app
        
        # Configurar la ventana
        self.set_title("Comic Manager")
        self.set_default_size(1200, 800)
        
        # Inicializar base de datos
        self.init_database()
        
        # Variables de estado
        self.current_section = "comics"
        self.current_data = []
        self.current_filters = {}
        self.current_sort_field = "id_comicbook"
        self.current_sort_direction = "asc"
        
        # Crear la interfaz
        self.setup_ui()
        self.setup_css()
        
        # Cargar datos iniciales
        self.load_comics()
        
    def init_database(self):
        """Inicializar conexión a la base de datos"""
        try:
            # Ajusta la ruta de tu base de datos
            engine = create_engine('sqlite:///comics.db', echo=False)
            Base.metadata.create_all(engine)
            Session = sessionmaker(bind=engine)
            self.session = Session()
            
            # Inicializar repositorios
            self.comic_repository = ComicbookRepository(self.session)
            self.volume_repository = VolumeRepository(self.session)
            self.publisher_repository = PublisherRepository(self.session)
            
        except Exception as e:
            print(f"Error inicializando base de datos: {e}")
            # Crear repositorios mock para desarrollo
            self.session = None
            
    def setup_ui(self):
        """Configurar la interfaz de usuario"""
        # Layout principal con Adw.OverlaySplitView
        self.split_view = Adw.OverlaySplitView()
        self.split_view.set_sidebar_width_fraction(0.2)
        self.set_content(self.split_view)
        
        # Crear sidebar
        self.create_sidebar()
        
        # Crear área principal
        self.create_main_area()
        
    def create_sidebar(self):
        """Crear el sidebar de navegación"""
        sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        sidebar_box.add_css_class("sidebar")
        
        # Header del sidebar
        header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        header_box.set_margin_top(24)
        header_box.set_margin_bottom(24)
        header_box.set_margin_start(16)
        header_box.set_margin_end(16)
        
        app_title = Gtk.Label(label="Comic Manager")
        app_title.add_css_class("title-2")
        header_box.append(app_title)
        
        sidebar_box.append(header_box)
        
        # Lista de navegación
        nav_list = Gtk.ListBox()
        nav_list.add_css_class("navigation-sidebar")
        nav_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        nav_list.connect("row-activated", self.on_navigation_activated)
        
        # Elementos de navegación
        nav_items = [
            ("comics", "Comics", "media-optical-symbolic"),
            ("volumes", "Volúmenes", "folder-symbolic"),
            ("publishers", "Editoriales", "building-symbolic"),
            ("arcs", "Arcos Argumentales", "view-list-symbolic"),
        ]
        
        self.nav_rows = {}
        for item_id, title, icon_name in nav_items:
            row = Adw.ActionRow()
            row.set_title(title)
            row.set_icon_name(icon_name)
            row.item_id = item_id
            nav_list.append(row)
            self.nav_rows[item_id] = row
            
        # Seleccionar el primer elemento por defecto
        nav_list.select_row(self.nav_rows["comics"])
        
        sidebar_box.append(nav_list)
        
        # Configurar el sidebar en el split view
        self.split_view.set_sidebar(sidebar_box)
        
    def create_main_area(self):
        """Crear el área principal con GridView"""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        main_box.add_css_class("main-content")
        
        # Header bar con título y controles
        self.header_bar = Adw.HeaderBar()
        self.header_bar.add_css_class("flat")
        
        # Título dinámico
        self.section_title = Gtk.Label(label="Comics")
        self.section_title.add_css_class("title-1")
        self.header_bar.set_title_widget(self.section_title)
        
        # Botón de búsqueda (reemplazado por barra de búsqueda rápida)
        # search_button = Gtk.Button.new_from_icon_name("system-search-symbolic")
        # search_button.add_css_class("flat")
        # search_button.connect("clicked", self.on_search_clicked)
        # self.header_bar.pack_end(search_button)
        
        # Botón de filtros avanzados
        filter_button = Gtk.Button.new_from_icon_name("funnel-symbolic")
        filter_button.add_css_class("flat")
        filter_button.set_tooltip_text("Filtros avanzados")
        filter_button.connect("clicked", self.on_advanced_search_clicked)
        self.header_bar.pack_end(filter_button)
        
        # Botón de vista
        view_button = Gtk.Button.new_from_icon_name("view-grid-symbolic")
        view_button.add_css_class("flat")
        self.header_bar.pack_end(view_button)
        
        main_box.append(self.header_bar)
        
        # Barra de búsqueda rápida
        self.quick_search_bar = QuickSearchBar(
            on_search_callback=self.on_quick_search,
            on_filter_callback=self.on_advanced_search_clicked
        )
        main_box.append(self.quick_search_bar)
        
        # Área de contenido principal con scroll
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_vexpand(True)
        self.scrolled_window.set_hexpand(True)
        
        # GridView para mostrar los covers
        self.setup_gridview()
        
        self.scrolled_window.set_child(self.grid_view)
        main_box.append(self.scrolled_window)
        
        # Status bar
        self.status_bar = Gtk.Label(label="Cargando...")
        self.status_bar.add_css_class("dim-label")
        self.status_bar.set_margin_top(6)
        self.status_bar.set_margin_bottom(6)
        main_box.append(self.status_bar)
        
        self.split_view.set_content(main_box)
        
    def setup_gridview(self):
        """Configurar el GridView para mostrar covers"""
        # Crear el modelo de datos
        self.list_store = Gio.ListStore.new(GObject.Object)
        
        # Crear selección
        self.selection_model = Gtk.SingleSelection.new(self.list_store)
        
        # Crear GridView
        self.grid_view = Gtk.GridView.new(self.selection_model, None)
        self.grid_view.set_max_columns(8)
        self.grid_view.set_min_columns(2)
        
        # Factory para crear los widgets de cada item
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self.on_item_setup)
        factory.connect("bind", self.on_item_bind)
        factory.connect("unbind", self.on_item_unbind)
        
        self.grid_view.set_factory(factory)
        
    def on_item_setup(self, factory, list_item):
        """Configurar cada item del GridView"""
        # Crear el widget mejorado para el item
        widget = ImprovedComicCoverWidget(None, self.current_section.rstrip('s'), self)
        list_item.set_child(widget)
        
    def on_item_bind(self, factory, list_item):
        """Vincular datos con cada item"""
        item = list_item.get_item()
        widget = list_item.get_child()
        
        if item and hasattr(item, 'data'):
            widget.update_data(item.data)
            
    def on_item_unbind(self, factory, list_item):
        """Limpiar vinculación de datos"""
        pass
        
    def on_navigation_activated(self, listbox, row):
        """Manejar cambio de sección en el sidebar"""
        section = row.item_id
        if section != self.current_section:
            self.current_section = section
            self.section_title.set_text(row.get_title())
            self.load_section_data(section)
            
    def load_section_data(self, section):
        """Cargar datos según la sección seleccionada"""
        if section == "comics":
            self.load_comics()
        elif section == "volumes":
            self.load_volumes()
        elif section == "publishers":
            self.load_publishers()
        elif section == "arcs":
            self.load_arcs()
            
    def load_comics(self):
        """Cargar lista de comics"""
        if self.session and self.comic_repository:
            try:
                # Aplicar filtros actuales
                self.comic_repository.limpiar_filtros()
                if self.current_filters:
                    self.apply_repository_filters()
                    
                comics = self.comic_repository.obtener_todos_los_comics(
                    orden=self.current_sort_field, 
                    direccion=self.current_sort_direction
                )
                self.update_gridview_data(comics)
                count = len(comics)
                self.quick_search_bar.update_results_count(count)
                
                # Actualizar barra de estado
                if self.current_filters:
                    self.status_bar.set_text(f"{count} comics encontrados (filtrado)")
                else:
                    self.status_bar.set_text(f"{count} comics encontrados")
                    
            except Exception as e:
                print(f"Error cargando comics: {e}")
                self.status_bar.set_text("Error cargando comics")
                self.quick_search_bar.update_results_count(0)
        else:
            # Datos mock para desarrollo
            self.status_bar.set_text("0 comics (sin base de datos)")
            self.quick_search_bar.update_results_count(0)
            
    def load_volumes(self):
        """Cargar lista de volúmenes"""
        if self.session and self.volume_repository:
            try:
                # Aplicar filtros actuales
                self.volume_repository.limpiar_filtros()
                if self.current_filters:
                    self.apply_repository_filters()
                    
                volumes = self.volume_repository.obtener_pagina(
                    0, 1000, 
                    self.current_sort_field, 
                    self.current_sort_direction
                )
                self.update_gridview_data(volumes)
                count = len(volumes)
                self.quick_search_bar.update_results_count(count)
                
                if self.current_filters:
                    self.status_bar.set_text(f"{count} volúmenes encontrados (filtrado)")
                else:
                    self.status_bar.set_text(f"{count} volúmenes encontrados")
                    
            except Exception as e:
                print(f"Error cargando volúmenes: {e}")
                self.status_bar.set_text("Error cargando volúmenes")
                self.quick_search_bar.update_results_count(0)
        else:
            self.status_bar.set_text("0 volúmenes (sin base de datos)")
            self.quick_search_bar.update_results_count(0)
            
    def load_publishers(self):
        """Cargar lista de editoriales"""
        if self.session and self.publisher_repository:
            try:
                # Aplicar filtros actuales
                self.publisher_repository.limpiar_filtros()
                if self.current_filters:
                    self.apply_repository_filters()
                    
                publishers = self.publisher_repository.obtener_pagina(
                    0, 1000, 
                    self.current_sort_field, 
                    self.current_sort_direction
                )
                self.update_gridview_data(publishers)
                count = len(publishers)
                self.quick_search_bar.update_results_count(count)
                
                if self.current_filters:
                    self.status_bar.set_text(f"{count} editoriales encontradas (filtrado)")
                else:
                    self.status_bar.set_text(f"{count} editoriales encontradas")
                    
            except Exception as e:
                print(f"Error cargando editoriales: {e}")
                self.status_bar.set_text("Error cargando editoriales")
                self.quick_search_bar.update_results_count(0)
        else:
            self.status_bar.set_text("0 editoriales (sin base de datos)")
            self.quick_search_bar.update_results_count(0)
            
    def load_arcs(self):
        """Cargar lista de arcos argumentales (placeholder)"""
        self.list_store.remove_all()
        self.status_bar.set_text("Arcos argumentales - Próximamente")
        self.quick_search_bar.update_results_count(0)
        
    def update_gridview_data(self, data):
        """Actualizar datos del GridView"""
        self.list_store.remove_all()
        
        # Wrapper class para los datos
        class DataWrapper(GLib.Object):
            def __init__(self, data):
                super().__init__()
                self.data = data
                
        for item in data:
            wrapper = DataWrapper(item)
            self.list_store.append(wrapper)
            
    def on_quick_search(self, query):
        """Manejar búsqueda rápida"""
        if query.strip():
            # Aplicar filtro de búsqueda rápida
            if self.current_section == "comics":
                self.current_filters = {'path': query}
            elif self.current_section == "volumes":
                self.current_filters = {'nombre': query}
            elif self.current_section == "publishers":
                self.current_filters = {'nombre': query}
        else:
            # Limpiar filtros si no hay texto de búsqueda
            self.current_filters = {}
            
        # Recargar datos con nuevos filtros
        self.load_section_data(self.current_section)
        
    def on_advanced_search_clicked(self, button=None):
        """Mostrar diálogo de filtros avanzados"""
        dialog = SearchFilterDialog(self, self.current_section)
        dialog.present(self)
        
    def apply_filters_and_sort(self, filters, sort_field, sort_direction):
        """Aplicar filtros y ordenamiento desde el diálogo de filtros"""
        self.current_filters = filters
        self.current_sort_field = sort_field
        self.current_sort_direction = sort_direction
        
        # Recargar datos
        self.load_section_data(self.current_section)
        
        # Actualizar la barra de búsqueda rápida si hay filtro de texto
        search_text = ""
        if self.current_section == "comics" and 'path' in filters:
            search_text = filters['path']
        elif self.current_section in ["volumes", "publishers"] and 'nombre' in filters:
            search_text = filters['nombre']
            
        if search_text != self.quick_search_bar.get_search_text():
            self.quick_search_bar.set_search_text(search_text)
            
    def apply_repository_filters(self):
        """Aplicar filtros al repositorio actual"""
        if not self.current_filters:
            return
            
        if self.current_section == "comics":
            # Filtros específicos para comics
            if 'path' in self.current_filters:
                self.comic_repository.filtrar(path=self.current_filters['path'])
            if 'is_classified' in self.current_filters:
                self.comic_repository.filtrar(is_classified=self.current_filters['is_classified'])
                
        elif self.current_section == "volumes":
            # Filtros específicos para volúmenes
            if 'nombre' in self.current_filters:
                self.volume_repository.filtrar(nombre=self.current_filters['nombre'])
                
        elif self.current_section == "publishers":
            # Filtros específicos para editoriales
            if 'nombre' in self.current_filters:
                self.publisher_repository.filtrar(nombre=self.current_filters['nombre'])
            
    def on_search_clicked(self, button):
        """Método legacy - reemplazado por búsqueda rápida"""
        self.on_advanced_search_clicked()
        
    def setup_css(self):
        """Configurar estilos CSS"""
        css = """
        .sidebar {
            background-color: @sidebar_bg_color;
            border-right: 1px solid @borders;
        }
        
        .main-content {
            background-color: @view_bg_color;
        }
        
        .comic-card {
            margin: 8px;
            padding: 8px;
            border-radius: 8px;
            background-color: @card_bg_color;
            border: 1px solid alpha(@borders, 0.5);
        }
        
        .comic-cover {
            border-radius: 6px;
            border: 1px solid alpha(@borders, 0.3);
        }
        
        .comic-title {
            font-size: 0.9em;
            text-align: center;
        }
        
        .navigation-sidebar row {
            padding: 8px 16px;
        }
        
        .badge {
            background-color: @accent_bg_color;
            color: @accent_fg_color;
            border-radius: 10px;
            padding: 2px 6px;
            font-size: 0.8em;
            font-weight: bold;
            min-width: 16px;
            text-align: center;
        }
        
        .badge-success {
            background-color: @success_color;
            color: white;
        }
        
        .badge-warning {
            background-color: @warning_color;
            color: white;
        }
        
        .badge-info {
            background-color: @accent_bg_color;
            color: @accent_fg_color;
        }
        
        .quality-bar {
            margin: 4px 8px 0 8px;
            height: 4px;
        }
        
        .toolbar {
            background-color: alpha(@card_bg_color, 0.5);
            border-bottom: 1px solid alpha(@borders, 0.5);
        }
        """
        
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )


class ComicManagerApp(Adw.Application):
    """Aplicación principal"""
    
    def __init__(self):
        super().__init__(application_id="com.comicmanager.app")
        
    def do_activate(self):
        window = ComicManagerWindow(self)
        window.present()


def main():
    """Función principal"""
    app = ComicManagerApp()
    return app.run(sys.argv)


if __name__ == '__main__':
    main()