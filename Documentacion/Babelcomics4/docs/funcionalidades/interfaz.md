# Interfaz GTK4

Babelcomics4 utiliza GTK4 y libadwaita para proporcionar una interfaz moderna, nativa y responsive que sigue las directrices de diseño de GNOME, ofreciendo una experiencia de usuario fluida y accesible.

## 🎨 Arquitectura de la Interfaz

### Stack Tecnológico

#### Componentes Principales
```python
UI_STACK = {
    'Toolkit': 'GTK 4.8+',
    'Design_System': 'libadwaita 1.2+',
    'Language': 'Python 3.13',
    'Binding': 'PyGObject (gi)',
    'Icons': 'Adwaita Icon Theme',
    'Styling': 'CSS + Adwaita Styles',
    'Accessibility': 'ATK + screen readers'
}

# Dependencias principales
DEPENDENCIES = {
    'gtk4': '>=4.8.0',
    'libadwaita': '>=1.2.0',
    'pygobject': '>=3.42.0',
    'cairo': '>=1.20.0',
    'pango': '>=1.50.0'
}
```

### Patrones de Diseño

#### Model-View-Controller (MVC)
```python
from gi.repository import Gtk, Adw, GObject, Gio
from abc import ABC, abstractmethod

class BaseController(ABC):
    """Controlador base para todas las vistas"""

    def __init__(self, application, model=None):
        self.application = application
        self.model = model
        self.view = None

    @abstractmethod
    def create_view(self):
        """Crear la vista asociada"""
        pass

    @abstractmethod
    def setup_signals(self):
        """Configurar señales y eventos"""
        pass

    def show(self):
        """Mostrar la vista"""
        if not self.view:
            self.view = self.create_view()
            self.setup_signals()
        return self.view

class BaseView(Gtk.Widget):
    """Vista base con funcionalidad común"""

    def __init__(self, controller=None):
        super().__init__()
        self.controller = controller
        self.setup_ui()

    @abstractmethod
    def setup_ui(self):
        """Configurar elementos de la interfaz"""
        pass

    def show_error(self, message: str, details: str = None):
        """Mostrar diálogo de error"""
        dialog = Adw.MessageDialog.new(
            self.get_root(),
            _("Error"),
            message
        )
        if details:
            dialog.set_body(details)
        dialog.add_response("ok", _("OK"))
        dialog.present()

    def show_confirmation(self, message: str, callback=None):
        """Mostrar diálogo de confirmación"""
        dialog = Adw.MessageDialog.new(
            self.get_root(),
            _("Confirmación"),
            message
        )
        dialog.add_response("cancel", _("Cancelar"))
        dialog.add_response("confirm", _("Confirmar"))
        dialog.set_response_appearance("confirm", Adw.ResponseAppearance.DESTRUCTIVE)

        if callback:
            dialog.connect("response", callback)

        dialog.present()
```

## 🏗️ Estructura de la Aplicación

### Aplicación Principal

#### ComicManagerApplication
```python
@Gtk.Template(resource_path='/org/gnome/Babelcomics4/ui/application.ui')
class ComicManagerApplication(Adw.Application):
    """Aplicación principal de Babelcomics4"""

    __gtype_name__ = 'ComicManagerApplication'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_application_id("org.gnome.Babelcomics4")
        self.set_flags(Gio.ApplicationFlags.HANDLES_OPEN)

        # Controladores principales
        self.main_controller = None
        self.preferences_controller = None
        self.comic_detail_controller = None

        # Servicios
        self.database_manager = None
        self.comic_repository = None
        self.thumbnail_generator = None

        self.setup_actions()
        self.setup_services()

    def do_activate(self):
        """Activar aplicación (primera vez o enfoque)"""
        if not self.main_controller:
            self.main_controller = MainController(self)

        window = self.main_controller.show()
        window.present()

    def setup_actions(self):
        """Configurar acciones de la aplicación"""
        actions = [
            ("preferences", self.on_preferences),
            ("about", self.on_about),
            ("quit", self.on_quit),
            ("import_comics", self.on_import_comics),
            ("scan_directory", self.on_scan_directory),
            ("update_comicvine", self.on_update_comicvine)
        ]

        for action_name, callback in actions:
            action = Gio.SimpleAction.new(action_name, None)
            action.connect("activate", callback)
            self.add_action(action)

    def setup_services(self):
        """Inicializar servicios de la aplicación"""
        from .services import DatabaseManager, ComicRepository, ThumbnailGenerator

        self.database_manager = DatabaseManager()
        self.comic_repository = ComicRepository(self.database_manager.get_session())
        self.thumbnail_generator = ThumbnailGenerator()

    def on_preferences(self, action, param):
        """Mostrar ventana de preferencias"""
        if not self.preferences_controller:
            self.preferences_controller = PreferencesController(self)

        window = self.preferences_controller.show()
        window.set_transient_for(self.get_active_window())
        window.present()
```

### Ventana Principal

#### MainWindow
```python
@Gtk.Template(resource_path='/org/gnome/Babelcomics4/ui/main_window.ui')
class MainWindow(Adw.ApplicationWindow):
    """Ventana principal de la aplicación"""

    __gtype_name__ = 'MainWindow'

    # Referencias a widgets del template
    header_bar = Gtk.Template.Child()
    navigation_view = Gtk.Template.Child()
    search_entry = Gtk.Template.Child()
    filter_button = Gtk.Template.Child()
    view_switcher = Gtk.Template.Child()

    # Páginas principales
    library_page = Gtk.Template.Child()
    volumes_page = Gtk.Template.Child()
    collection_page = Gtk.Template.Child()

    def __init__(self, application, controller):
        super().__init__(application=application)
        self.controller = controller

        self.setup_header_bar()
        self.setup_navigation()
        self.setup_search()
        self.setup_shortcuts()

    def setup_header_bar(self):
        """Configurar barra de título"""
        # Botón de menú principal
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        menu_button.set_menu_model(self.create_primary_menu())
        self.header_bar.pack_end(menu_button)

        # Botón de filtros
        self.filter_button.connect("clicked", self.on_filter_clicked)

        # Botón de vista
        self.view_switcher.connect("notify::selected-page", self.on_view_changed)

    def setup_navigation(self):
        """Configurar navegación entre páginas"""
        # Configurar páginas
        self.library_controller = LibraryController(self.controller.application)
        self.volumes_controller = VolumesController(self.controller.application)

        # Añadir controladores a las páginas
        self.library_page.set_child(self.library_controller.show())
        self.volumes_page.set_child(self.volumes_controller.show())

    def setup_search(self):
        """Configurar búsqueda global"""
        self.search_entry.connect("search-changed", self.on_search_changed)
        self.search_entry.connect("activate", self.on_search_activate)

        # Configurar timeout para búsqueda en tiempo real
        self.search_timeout_id = None

    def create_primary_menu(self):
        """Crear menú principal"""
        menu = Gio.Menu()

        # Sección de archivos
        file_section = Gio.Menu()
        file_section.append(_("Import Comics"), "app.import_comics")
        file_section.append(_("Scan Directory"), "app.scan_directory")
        menu.append_section(None, file_section)

        # Sección de herramientas
        tools_section = Gio.Menu()
        tools_section.append(_("Update ComicVine"), "app.update_comicvine")
        tools_section.append(_("Preferences"), "app.preferences")
        menu.append_section(None, tools_section)

        # Sección de ayuda
        help_section = Gio.Menu()
        help_section.append(_("About Babelcomics4"), "app.about")
        menu.append_section(None, help_section)

        return menu

    def on_search_changed(self, search_entry):
        """Manejar cambios en la búsqueda"""
        if self.search_timeout_id:
            GLib.source_remove(self.search_timeout_id)

        # Delay de 300ms para evitar búsquedas excesivas
        self.search_timeout_id = GLib.timeout_add(
            300,
            self.perform_search,
            search_entry.get_text()
        )

    def perform_search(self, search_term):
        """Realizar búsqueda"""
        self.search_timeout_id = None

        # Aplicar búsqueda al controlador activo
        active_page = self.view_switcher.get_selected_page()
        if active_page == 0:  # Library
            self.library_controller.set_search_term(search_term)
        elif active_page == 1:  # Volumes
            self.volumes_controller.set_search_term(search_term)

        return GLib.SOURCE_REMOVE
```

## 📚 Vistas de Contenido

### Vista de Biblioteca

#### LibraryView
```python
@Gtk.Template(resource_path='/org/gnome/Babelcomics4/ui/library_view.ui')
class LibraryView(Gtk.Box):
    """Vista principal de la biblioteca de comics"""

    __gtype_name__ = 'LibraryView'

    # Widgets del template
    scrolled_window = Gtk.Template.Child()
    grid_view = Gtk.Template.Child()
    list_view = Gtk.Template.Child()
    view_stack = Gtk.Template.Child()
    status_page = Gtk.Template.Child()

    def __init__(self, controller):
        super().__init__()
        self.controller = controller

        # Modelos de datos
        self.comic_model = Gio.ListStore.new(ComicItem)
        self.filter_model = Gtk.FilterListModel.new(self.comic_model, None)
        self.sort_model = Gtk.SortListModel.new(self.filter_model, None)

        self.setup_views()
        self.setup_selection()
        self.load_comics()

    def setup_views(self):
        """Configurar vistas de grid y lista"""
        # Vista de grid (por defecto)
        grid_factory = Gtk.SignalListItemFactory()
        grid_factory.connect("setup", self.on_grid_item_setup)
        grid_factory.connect("bind", self.on_grid_item_bind)
        grid_factory.connect("unbind", self.on_grid_item_unbind)

        self.grid_view.set_factory(grid_factory)
        self.grid_view.set_model(self.sort_model)

        # Vista de lista
        list_factory = Gtk.SignalListItemFactory()
        list_factory.connect("setup", self.on_list_item_setup)
        list_factory.connect("bind", self.on_list_item_bind)

        self.list_view.set_factory(list_factory)
        self.list_view.set_model(self.sort_model)

    def on_grid_item_setup(self, factory, list_item):
        """Configurar elemento de grid"""
        card = ComicCard()
        list_item.set_child(card)

    def on_grid_item_bind(self, factory, list_item):
        """Vincular datos a elemento de grid"""
        comic_item = list_item.get_item()
        card = list_item.get_child()
        card.bind_comic(comic_item)

        # Configurar eventos
        card.connect("clicked", self.on_comic_clicked, comic_item)
        card.connect("secondary-clicked", self.on_comic_secondary_clicked, comic_item)

    def load_comics(self, filters=None):
        """Cargar comics desde la base de datos"""
        def load_comics_thread():
            comics = self.controller.get_comics(filters)
            GLib.idle_add(self.update_comic_model, comics)

        # Cargar en hilo separado para no bloquear UI
        thread = threading.Thread(target=load_comics_thread)
        thread.daemon = True
        thread.start()

    def update_comic_model(self, comics):
        """Actualizar modelo con comics cargados"""
        self.comic_model.remove_all()

        for comic in comics:
            comic_item = ComicItem(comic)
            self.comic_model.append(comic_item)

        # Mostrar página apropiada
        if len(comics) > 0:
            self.view_stack.set_visible_child(self.scrolled_window)
        else:
            self.status_page.set_title(_("No comics found"))
            self.status_page.set_description(_("Try adjusting your search or filters"))
            self.view_stack.set_visible_child(self.status_page)

        return GLib.SOURCE_REMOVE
```

### Tarjeta de Comic

#### ComicCard
```python
@Gtk.Template(resource_path='/org/gnome/Babelcomics4/ui/comic_card.ui')
class ComicCard(Gtk.Box):
    """Tarjeta individual de comic"""

    __gtype_name__ = 'ComicCard'

    # Widgets del template
    thumbnail_image = Gtk.Template.Child()
    title_label = Gtk.Template.Child()
    subtitle_label = Gtk.Template.Child()
    quality_box = Gtk.Template.Child()
    status_overlay = Gtk.Template.Child()

    def __init__(self):
        super().__init__()
        self.comic_item = None
        self.setup_gestures()

    def setup_gestures(self):
        """Configurar gestos y eventos"""
        # Click principal
        click_gesture = Gtk.GestureClick()
        click_gesture.set_button(1)  # Botón izquierdo
        click_gesture.connect("pressed", self.on_primary_click)
        self.add_controller(click_gesture)

        # Click secundario (menú contextual)
        right_click = Gtk.GestureClick()
        right_click.set_button(3)  # Botón derecho
        right_click.connect("pressed", self.on_secondary_click)
        self.add_controller(right_click)

        # Hover para feedback visual
        motion_controller = Gtk.EventControllerMotion()
        motion_controller.connect("enter", self.on_hover_enter)
        motion_controller.connect("leave", self.on_hover_leave)
        self.add_controller(motion_controller)

    def bind_comic(self, comic_item):
        """Vincular datos del comic a la tarjeta"""
        self.comic_item = comic_item
        comic = comic_item.comic

        # Título y subtítulo
        if comic.is_cataloged and comic.comic_info:
            self.title_label.set_text(comic.comic_info.display_title)
            publisher = comic.comic_info.volume.publisher.nombre if comic.comic_info.volume and comic.comic_info.volume.publisher else ""
            self.subtitle_label.set_text(publisher)
        else:
            self.title_label.set_text(comic.filename)
            self.subtitle_label.set_text(f"{comic.file_size_mb} MB")

        # Thumbnail
        self.load_thumbnail_async(comic)

        # Indicadores de calidad
        self.update_quality_indicators(comic)

        # Estado visual
        self.update_visual_state(comic)

    def load_thumbnail_async(self, comic):
        """Cargar thumbnail de forma asíncrona"""
        def load_thumbnail():
            thumbnail_path = self.get_application().thumbnail_generator.get_thumbnail_path(comic)
            GLib.idle_add(self.set_thumbnail, thumbnail_path)

        thread = threading.Thread(target=load_thumbnail)
        thread.daemon = True
        thread.start()

    def set_thumbnail(self, thumbnail_path):
        """Establecer imagen del thumbnail"""
        if thumbnail_path and os.path.exists(thumbnail_path):
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                thumbnail_path, 200, 300, True
            )
            texture = Gdk.Texture.new_for_pixbuf(pixbuf)
            self.thumbnail_image.set_from_paintable(texture)
        else:
            self.thumbnail_image.set_from_icon_name("image-missing-symbolic")

        return GLib.SOURCE_REMOVE

    def update_quality_indicators(self, comic):
        """Actualizar indicadores de calidad"""
        # Limpiar indicadores existentes
        child = self.quality_box.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.quality_box.remove(child)
            child = next_child

        # Añadir estrellas de calidad
        for i in range(5):
            star = Gtk.Image()
            if i < comic.calidad:
                star.set_from_icon_name("starred-symbolic")
                star.add_css_class("star-filled")
            else:
                star.set_from_icon_name("non-starred-symbolic")
                star.add_css_class("star-empty")

            self.quality_box.append(star)

    def update_visual_state(self, comic):
        """Actualizar estado visual de la tarjeta"""
        # Limpiar clases CSS existentes
        self.remove_css_class("comic-cataloged")
        self.remove_css_class("comic-uncataloged")
        self.remove_css_class("comic-trash")

        # Aplicar clase apropiada
        if comic.en_papelera:
            self.add_css_class("comic-trash")
        elif comic.is_cataloged:
            self.add_css_class("comic-cataloged")
        else:
            self.add_css_class("comic-uncataloged")

    def on_primary_click(self, gesture, n_press, x, y):
        """Manejar click principal"""
        if n_press == 2:  # Doble click
            self.emit("activated", self.comic_item)
        else:  # Click simple
            self.emit("clicked", self.comic_item)

    def on_secondary_click(self, gesture, n_press, x, y):
        """Manejar click secundario (menú contextual)"""
        self.emit("secondary-clicked", self.comic_item)

    def on_hover_enter(self, controller, x, y):
        """Efecto visual al pasar el mouse"""
        self.add_css_class("card-hover")

    def on_hover_leave(self, controller):
        """Quitar efecto visual al salir el mouse"""
        self.remove_css_class("card-hover")

    # Señales personalizadas
    @GObject.Signal(arg_types=(object,))
    def clicked(self, comic_item):
        pass

    @GObject.Signal(arg_types=(object,))
    def activated(self, comic_item):
        pass

    @GObject.Signal(arg_types=(object,))
    def secondary_clicked(self, comic_item):
        pass
```

## 🎨 Theming y Estilos

### Estilos CSS Personalizados

#### Archivo style.css
```css
/* Estilos para tarjetas de comics */
.comic-card {
    border-radius: 12px;
    margin: 6px;
    transition: all 200ms ease-in-out;
    background: @card_bg_color;
    border: 1px solid @card_border_color;
}

.comic-card:hover,
.comic-card.card-hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
}

.comic-card.comic-cataloged {
    border-left: 4px solid @success_color;
}

.comic-card.comic-uncataloged {
    border-left: 4px solid @warning_color;
}

.comic-card.comic-uncataloged image {
    filter: grayscale(100%);
    opacity: 0.8;
}

.comic-card.comic-trash {
    opacity: 0.6;
    filter: grayscale(50%);
    border-left: 4px solid @error_color;
}

/* Indicadores de calidad */
.star-filled {
    color: @accent_color;
}

.star-empty {
    color: @insensitive_fg_color;
    opacity: 0.5;
}

/* Vista de volúmenes */
.volume-row {
    padding: 12px;
    border-radius: 8px;
    margin: 4px 0;
    transition: background-color 200ms ease;
}

.volume-row:hover {
    background-color: @card_hover_bg_color;
}

.volume-complete {
    background: linear-gradient(
        90deg,
        transparent 0%,
        @success_bg_color 100%
    );
}

.volume-progress {
    background: linear-gradient(
        90deg,
        transparent 0%,
        @accent_bg_color 100%
    );
}

/* Filtros y controles */
.filter-chip {
    border-radius: 16px;
    padding: 6px 12px;
    margin: 2px;
    background: @accent_bg_color;
    color: @accent_fg_color;
    border: 1px solid @accent_color;
}

.filter-chip.active {
    background: @accent_color;
    color: @accent_fg_color;
}

/* Animaciones de carga */
.loading-spinner {
    animation: spin 1s linear infinite;
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

/* Responsive design */
@media (max-width: 768px) {
    .comic-card {
        margin: 3px;
    }

    .volume-row {
        padding: 8px;
    }
}

/* Dark mode adaptations */
@media (prefers-color-scheme: dark) {
    .comic-card {
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    }

    .comic-card:hover {
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4);
    }
}
```

### Sistema de Iconos

#### Iconos Personalizados
```python
class IconManager:
    """Gestor de iconos de la aplicación"""

    ICON_MAPPINGS = {
        'comic-cataloged': 'emblem-ok-symbolic',
        'comic-uncataloged': 'dialog-question-symbolic',
        'comic-trash': 'user-trash-symbolic',
        'comic-error': 'dialog-error-symbolic',
        'quality-1': 'starred-symbolic',
        'quality-2': 'starred-symbolic',
        'quality-3': 'starred-symbolic',
        'quality-4': 'starred-symbolic',
        'quality-5': 'starred-symbolic',
        'publisher-dc': 'applications-graphics-symbolic',
        'publisher-marvel': 'applications-graphics-symbolic',
        'format-cbz': 'package-x-generic-symbolic',
        'format-cbr': 'package-x-generic-symbolic',
        'format-pdf': 'application-pdf-symbolic'
    }

    @classmethod
    def get_icon_name(cls, icon_key, fallback='image-missing-symbolic'):
        """Obtener nombre de icono por clave"""
        return cls.ICON_MAPPINGS.get(icon_key, fallback)

    @classmethod
    def load_custom_icons(cls):
        """Cargar iconos personalizados de la aplicación"""
        icon_theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())

        # Añadir directorio de iconos de la aplicación
        icon_theme.add_resource_path("/org/gnome/Babelcomics4/icons")

        # Registrar iconos personalizados si están disponibles
        custom_icons = [
            'babelcomics4-app-icon',
            'comic-book-symbolic',
            'volume-symbolic',
            'collection-symbolic'
        ]

        for icon_name in custom_icons:
            if icon_theme.has_icon(icon_name):
                print(f"Icono personalizado cargado: {icon_name}")
```

## 🚀 Optimización de Rendimiento

### Lazy Loading

#### Carga Diferida de Contenido
```python
class LazyComicLoader:
    """Cargador lazy de contenido de comics"""

    def __init__(self, batch_size=50):
        self.batch_size = batch_size
        self.loading_batches = set()

    def setup_lazy_loading(self, list_view, model):
        """Configurar carga lazy en vista de lista"""

        def on_items_changed(list_model, position, removed, added):
            # Verificar si necesitamos cargar más elementos
            last_visible = position + added
            total_items = list_model.get_n_items()

            # Si estamos cerca del final, cargar más
            if last_visible > total_items - 10:
                self.load_next_batch(list_model)

        model.connect("items-changed", on_items_changed)

    def load_next_batch(self, model):
        """Cargar siguiente lote de elementos"""
        current_size = model.get_n_items()
        batch_start = current_size

        # Evitar cargas duplicadas
        if batch_start in self.loading_batches:
            return

        self.loading_batches.add(batch_start)

        def load_batch_async():
            # Simular carga de datos
            new_items = self.fetch_comics_batch(batch_start, self.batch_size)
            GLib.idle_add(self.add_items_to_model, model, new_items, batch_start)

        thread = threading.Thread(target=load_batch_async)
        thread.daemon = True
        thread.start()

    def add_items_to_model(self, model, items, batch_start):
        """Añadir elementos al modelo"""
        for item in items:
            model.append(item)

        self.loading_batches.discard(batch_start)
        return GLib.SOURCE_REMOVE
```

### Virtualización

#### Vista Virtualizada para Grandes Colecciones
```python
class VirtualizedComicView(Gtk.ScrolledWindow):
    """Vista virtualizada para manejar grandes colecciones"""

    def __init__(self, controller):
        super().__init__()
        self.controller = controller

        # Configurar scrolling
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.set_kinetic_scrolling(True)
        self.set_overlay_scrolling(True)

        # Modelo virtual
        self.virtual_model = VirtualComicModel(controller)

        # Vista con soporte de virtualización
        self.list_view = Gtk.ListView()
        self.list_view.set_model(self.virtual_model)
        self.list_view.set_single_click_activate(True)

        # Factory para elementos
        self.setup_item_factory()

        self.set_child(self.list_view)

    def setup_item_factory(self):
        """Configurar factory de elementos con pooling"""
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self.on_item_setup)
        factory.connect("bind", self.on_item_bind)
        factory.connect("unbind", self.on_item_unbind)
        factory.connect("teardown", self.on_item_teardown)

        self.list_view.set_factory(factory)

    def on_item_setup(self, factory, list_item):
        """Setup con pooling de widgets"""
        widget = self.get_pooled_widget() or ComicCard()
        list_item.set_child(widget)

    def get_pooled_widget(self):
        """Obtener widget reutilizable del pool"""
        # Implementar pool de widgets para mejor rendimiento
        if hasattr(self, '_widget_pool') and self._widget_pool:
            return self._widget_pool.pop()
        return None

    def return_to_pool(self, widget):
        """Devolver widget al pool"""
        if not hasattr(self, '_widget_pool'):
            self._widget_pool = []

        if len(self._widget_pool) < 100:  # Límite del pool
            widget.unbind_comic()  # Limpiar datos
            self._widget_pool.append(widget)
```

## 🌍 Internacionalización

### Soporte Multi-idioma

#### Configuración de i18n
```python
import gettext
import locale
import os

class InternationalizationManager:
    """Gestor de internacionalización"""

    def __init__(self):
        self.domain = 'babelcomics4'
        self.localedir = os.path.join(os.path.dirname(__file__), 'locale')
        self.current_locale = None

        self.setup_locale()

    def setup_locale(self):
        """Configurar locale del sistema"""
        try:
            # Detectar locale del sistema
            locale.setlocale(locale.LC_ALL, '')
            system_locale = locale.getlocale()[0]

            # Configurar gettext
            gettext.bindtextdomain(self.domain, self.localedir)
            gettext.textdomain(self.domain)

            # Instalar función _ globalmente
            gettext.install(self.domain, self.localedir)

            self.current_locale = system_locale
            print(f"Locale configurado: {system_locale}")

        except locale.Error as e:
            print(f"Error configurando locale: {e}")
            # Fallback a inglés
            self.current_locale = 'en_US'

    def get_available_locales(self):
        """Obtener locales disponibles"""
        locales = []

        if os.path.exists(self.localedir):
            for item in os.listdir(self.localedir):
                locale_path = os.path.join(self.localedir, item, 'LC_MESSAGES', f'{self.domain}.mo')
                if os.path.exists(locale_path):
                    locales.append(item)

        return locales

    def change_locale(self, locale_code):
        """Cambiar locale de la aplicación"""
        try:
            translation = gettext.translation(self.domain, self.localedir, [locale_code])
            translation.install()
            self.current_locale = locale_code
            return True
        except FileNotFoundError:
            print(f"Traducción no encontrada para: {locale_code}")
            return False
```

## 🆕 Nuevas Funcionalidades de UI

### Multiselección y Context Menu Unificado

#### Implementación de Multiselección
```python
class SelectableCard(Gtk.Box):
    """Card base con soporte de multiselección"""

    def __init__(self, item, selection_manager):
        super().__init__()
        self.item = item
        self.selection_manager = selection_manager
        self.setup_selection_handling()

    def setup_selection_handling(self):
        """Configurar manejo de selección"""
        # Ctrl+A para seleccionar todo
        self.add_shortcut(Gtk.Shortcut.new(
            Gtk.ShortcutTrigger.parse_string("<Control>a"),
            Gtk.CallbackAction.new(self.select_all)
        ))

        # Context menu unificado
        self.setup_context_menu()

    def select_all(self, widget, args):
        """Seleccionar todos los elementos visibles"""
        self.selection_manager.select_all()
        return True
```

#### Context Menu Inteligente
```python
def create_context_menu(self, selected_items):
    """Crear menú contextual adaptado al número de elementos"""

    item_count = len(selected_items)
    menu = Gio.Menu()

    if item_count == 1:
        # Menú para elemento individual
        menu.append("Abrir", "app.open_comic")
        menu.append("Ver detalles", "app.show_details")

    # Acciones para 1 o múltiples elementos
    trash_label = f"Enviar {item_count} elemento(s) a papelera"
    catalog_label = f"Catalogar {item_count} elemento(s)"

    menu.append(trash_label, "app.move_to_trash")
    menu.append(catalog_label, "app.catalog_items")

    return menu
```

### Carrusel de Portadas Múltiples

#### Implementación con Adw.Carousel
```python
def create_covers_carousel(comicbook_info):
    """Crear carrusel para múltiples portadas"""

    carousel = Adw.Carousel()
    carousel.set_size_request(200, 280)
    carousel.set_allow_mouse_drag(True)
    carousel.set_allow_scroll_wheel(True)

    # Agregar cada portada
    for cover in comicbook_info.portadas:
        cover_image = Gtk.Picture()
        cover_image.set_content_fit(Gtk.ContentFit.CONTAIN)

        # Carga robusta de imagen
        load_cover_image_robust(cover_image, cover)
        carousel.append(cover_image)

    # Indicador de páginas
    if len(comicbook_info.portadas) > 1:
        dots = Adw.CarouselIndicatorDots()
        dots.set_carousel(carousel)
        return create_carousel_container(carousel, dots)

    return carousel

def load_cover_image_robust(image_widget, cover):
    """Carga robusta con patrones de búsqueda"""

    patterns = [
        f"data/thumbnails/comicbook_info/*/{cover.filename}",
        f"data/thumbnails/comicbook_info/*/{cover.base_name}_variant_*.{cover.extension}",
        f"data/thumbnails/comicbook_info/*/{cover.base_name}.{cover.extension}"
    ]

    for pattern in patterns:
        files = glob.glob(pattern)
        if files:
            image_widget.set_filename(files[0])
            return

    # Fallback a placeholder
    image_widget.set_filename("images/Comic_sin_caratula.png")
```

### Navegación Mejorada

#### Flujo de Navegación Anidada
```python
def setup_navigation_flow(main_window):
    """Configurar navegación entre páginas relacionadas"""

    # Volume Details → ComicbookInfo Details → Physical Comics
    navigation_view = main_window.get_navigation_view()

    # Handlers de navegación
    def navigate_to_comicbook_info(comic_info):
        detail_page = create_comicbook_info_detail_page(comic_info)
        navigation_view.push(detail_page)

    def navigate_to_physical_comics(comic_info):
        physical_page = create_physical_comics_page(comic_info)
        navigation_view.push(physical_page)

    return {
        'to_comicbook_info': navigate_to_comicbook_info,
        'to_physical_comics': navigate_to_physical_comics
    }
```

### Mejoras de Rendimiento

#### Carga Asíncrona de Thumbnails
```python
async def load_thumbnails_async(self, items):
    """Cargar thumbnails de forma asíncrona"""

    tasks = []
    for item in items:
        task = asyncio.create_task(self.load_single_thumbnail(item))
        tasks.append(task)

    # Procesar en lotes
    batch_size = 10
    for i in range(0, len(tasks), batch_size):
        batch = tasks[i:i + batch_size]
        await asyncio.gather(*batch, return_exceptions=True)

        # Actualizar UI cada lote
        GLib.idle_add(self.update_progress, i + batch_size, len(tasks))
```

---

**¿Quieres conocer más sobre el desarrollo?** 👉 [Modelos de Datos](../desarrollo/modelos.md)