#!/usr/bin/env python3
"""
Comic Reader - Lector integrado de comics para Babelcomics4
Soporta CBZ, CBR, CB7 y navegación fluida entre páginas
"""

import gi
import os
import tempfile
import threading
import time
import shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GdkPixbuf, Gdk, GLib, GObject, Gio

try:
    from helpers.comic_extractor import ComicExtractor
except ImportError:
    print("Error: No se puede importar ComicExtractor")
    ComicExtractor = None


def cleanup_old_temp_files(temp_dir):
    """Limpiar archivos temporales viejos de babelcomics"""
    try:
        for item in os.listdir(temp_dir):
            if item.startswith("babelcomics_reader_"):
                item_path = os.path.join(temp_dir, item)
                # Eliminar directorios temporales más viejos de 1 hora
                if os.path.isdir(item_path):
                    stat = os.stat(item_path)
                    age_hours = (time.time() - stat.st_mtime) / 3600
                    if age_hours > 1:
                        shutil.rmtree(item_path, ignore_errors=True)
                        print(f"🗑️ Eliminado directorio temporal viejo: {item_path}")
    except Exception as e:
        print(f"⚠️ Error limpiando archivos temporales: {e}")


def find_temp_directory_with_space(required_mb=500):
    """Encontrar directorio temporal con espacio suficiente"""
    # Lista de directorios candidatos en orden de preferencia
    temp_dirs = [
        "/tmp/claude",
        "/tmp",
        os.path.expanduser("~/tmp"),
        os.path.expanduser("~/.cache/babelcomics"),
        "/var/tmp"
    ]

    for temp_dir in temp_dirs:
        try:
            # Crear directorio si no existe
            os.makedirs(temp_dir, exist_ok=True)

            # Limpiar archivos temporales viejos primero
            cleanup_old_temp_files(temp_dir)

            # Verificar espacio disponible
            total, used, free = shutil.disk_usage(temp_dir)
            free_mb = free // (1024 * 1024)

            print(f"Verificando {temp_dir}: {free_mb} MB libres")

            if free_mb >= required_mb:
                print(f"✅ Usando directorio temporal: {temp_dir} ({free_mb} MB libres)")
                return temp_dir
            else:
                print(f"⚠️ Poco espacio en {temp_dir}: {free_mb} MB < {required_mb} MB requeridos")

        except Exception as e:
            print(f"❌ Error verificando {temp_dir}: {e}")
            continue

    # Si no se encuentra ninguno con suficiente espacio, usar el primero disponible
    print("⚠️ No se encontró directorio con espacio suficiente, usando el primero disponible")
    return temp_dirs[0]


class ComicReader(Adw.ApplicationWindow):
    """Lector de comics integrado con navegación fluida"""

    def __init__(self, comic_path, comic_title="Comic", parent_window=None,
                 scroll_threshold=None, scroll_cooldown=None):
        # Crear aplicación si no existe
        app = Gio.Application.get_default()
        if app is None:
            app = Adw.Application()
        super().__init__(application=app)

        self.comic_path = comic_path
        self.comic_title = comic_title
        self.parent_window = parent_window

        # Parámetros de configuración de scroll
        self.scroll_threshold = scroll_threshold if scroll_threshold and scroll_threshold > 0 else 1.0
        self.scroll_cooldown = scroll_cooldown if scroll_cooldown and scroll_cooldown > 0 else 100

        # Estado del lector
        self.pages = []  # Lista de rutas de páginas extraídas
        self.current_page = 0
        self.zoom_level = 1.0
        self.fit_mode = "width"  # "width", "height", "original", "page"
        self.interpolation_mode = "nearest"  # "nearest", "bilinear", "hyper"
        self.loading = False
        self.temp_dir = None

        # Configurar ventana
        self.setup_window()

        # Crear interfaz
        self.setup_ui()

        # Extraer páginas en hilo separado
        self.extract_pages()

    def setup_window(self):
        """Configurar propiedades de la ventana"""
        self.set_title(f"Lector - {self.comic_title}")
        self.set_default_size(1000, 700)

        # Configuraciones esenciales para fullscreen
        self.set_resizable(True)
        self.set_can_focus(True)

        # Solo hacer transient si no queremos fullscreen independiente
        # (comentado para permitir fullscreen completo)
        # if self.parent_window:
        #     self.set_transient_for(self.parent_window)

        print(f"Window configurada: {self.get_title()}")
        print(f"Resizable: {self.get_resizable()}")
        print(f"Can focus: {self.get_can_focus()}")

    def setup_ui(self):
        """Crear interfaz del lector"""
        # Toast overlay para notificaciones
        self.toast_overlay = Adw.ToastOverlay()

        # Overlay split para sidebar
        self.overlay_split_view = Adw.OverlaySplitView()
        self.overlay_split_view.set_collapsed(True)  # Inicialmente colapsado
        self.overlay_split_view.set_sidebar_position(Gtk.PackType.START)
        self.overlay_split_view.set_max_sidebar_width(300)
        self.overlay_split_view.set_min_sidebar_width(200)

        # Box principal
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # Header bar
        self.create_header_bar()
        main_box.append(self.header_bar)

        # Área principal con imagen
        self.create_image_area()
        main_box.append(self.image_area)

        # Barra de navegación removida - navegación ahora es por scroll y sidebar

        # Crear sidebar con thumbnails
        self.create_thumbnail_sidebar()

        # Configurar split view
        self.overlay_split_view.set_content(main_box)
        self.overlay_split_view.set_sidebar(self.sidebar_box)

        # Configurar jerarquía
        self.toast_overlay.set_child(self.overlay_split_view)
        self.set_content(self.toast_overlay)

        # Configurar atajos de teclado
        self.setup_keyboard_shortcuts()

        # Conectar señales para reajuste automático
        self.scrolled_window.connect("notify::width", self.on_window_size_changed)
        self.scrolled_window.connect("notify::height", self.on_window_size_changed)

    def create_header_bar(self):
        """Crear barra de herramientas superior"""
        self.header_bar = Adw.HeaderBar()

        # Título del comic
        title_label = Gtk.Label(label=self.comic_title)
        title_label.add_css_class("title-2")

        # Solo título en el centro
        title_label.set_halign(Gtk.Align.CENTER)
        self.header_bar.set_title_widget(title_label)

        # Botón cerrar (izquierda)
        close_button = Gtk.Button()
        close_button.set_icon_name("window-close-symbolic")
        close_button.set_tooltip_text("Cerrar lector")
        close_button.connect("clicked", self.on_close_clicked)
        self.header_bar.pack_start(close_button)

        # Botón para mostrar/ocultar sidebar de thumbnails
        self.sidebar_button = Gtk.ToggleButton()
        self.sidebar_button.set_icon_name("sidebar-show-symbolic")
        self.sidebar_button.set_tooltip_text("Mostrar/ocultar vista de páginas (T)")
        self.sidebar_button.connect("toggled", self.on_toggle_sidebar)
        self.header_bar.pack_start(self.sidebar_button)

        # Navegación de página al lado del botón sidebar
        page_navigation_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        page_navigation_box.set_margin_start(6)

        # Entrada de número de página
        self.page_entry = Gtk.SpinButton()
        self.page_entry.set_range(1, 1)  # Se actualizará cuando se carguen las páginas
        self.page_entry.set_increments(1, 10)
        self.page_entry.set_numeric(True)
        self.page_entry.set_width_chars(4)
        self.page_entry.set_tooltip_text("Ir a página específica")
        self.page_entry.connect("value-changed", self.on_page_entry_changed)
        self.page_entry.connect("activate", self.on_page_entry_activate)

        # Label "de XXX"
        self.total_pages_label = Gtk.Label(label="de --")
        self.total_pages_label.add_css_class("caption")
        self.total_pages_label.set_margin_start(4)

        page_navigation_box.append(self.page_entry)
        page_navigation_box.append(self.total_pages_label)
        self.header_bar.pack_start(page_navigation_box)

        # Botón de ajustes con popover
        self.settings_button = Gtk.MenuButton()
        self.settings_button.set_icon_name("preferences-other-symbolic")
        self.settings_button.set_tooltip_text("Ajustes de visualización")

        # Crear popover con controles
        self.settings_popover = Gtk.Popover()
        self.settings_button.set_popover(self.settings_popover)

        # Contenido del popover
        popover_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        popover_box.set_margin_start(12)
        popover_box.set_margin_end(12)
        popover_box.set_margin_top(12)
        popover_box.set_margin_bottom(12)

        # Sección de zoom
        zoom_label = Gtk.Label(label="Zoom")
        zoom_label.add_css_class("heading")
        zoom_label.set_halign(Gtk.Align.START)
        popover_box.append(zoom_label)

        zoom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        zoom_box.add_css_class("linked")

        # Zoom out
        zoom_out_button = Gtk.Button()
        zoom_out_button.set_icon_name("zoom-out-symbolic")
        zoom_out_button.set_tooltip_text("Alejar")
        zoom_out_button.connect("clicked", self.on_zoom_out)
        zoom_box.append(zoom_out_button)

        # Zoom 100% (indicador actual)
        self.zoom_indicator_button = Gtk.Button()
        self.zoom_indicator_button.set_label("100%")
        self.zoom_indicator_button.set_tooltip_text("Resetear a zoom 100%")
        self.zoom_indicator_button.connect("clicked", self.on_zoom_100)
        zoom_box.append(self.zoom_indicator_button)

        # Zoom in
        zoom_in_button = Gtk.Button()
        zoom_in_button.set_icon_name("zoom-in-symbolic")
        zoom_in_button.set_tooltip_text("Acercar")
        zoom_in_button.connect("clicked", self.on_zoom_in)
        zoom_box.append(zoom_in_button)

        popover_box.append(zoom_box)

        # Separador
        separator = Gtk.Separator()
        popover_box.append(separator)

        # Sección de ajuste
        fit_label = Gtk.Label(label="Ajuste")
        fit_label.add_css_class("heading")
        fit_label.set_halign(Gtk.Align.START)
        popover_box.append(fit_label)

        fit_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        # Ajustar a ancho
        fit_width_button = Gtk.Button()
        fit_width_button.set_label("Ajustar al ancho")
        fit_width_button.connect("clicked", lambda btn: self.set_fit_mode("width"))
        fit_box.append(fit_width_button)

        # Ajustar a altura
        fit_height_button = Gtk.Button()
        fit_height_button.set_label("Ajustar a altura")
        fit_height_button.connect("clicked", lambda btn: self.set_fit_mode("height"))
        fit_box.append(fit_height_button)

        # Ajustar a página
        fit_page_button = Gtk.Button()
        fit_page_button.set_label("Página completa")
        fit_page_button.connect("clicked", lambda btn: self.set_fit_mode("page"))
        fit_box.append(fit_page_button)

        # Tamaño original
        fit_original_button = Gtk.Button()
        fit_original_button.set_label("Tamaño original")
        fit_original_button.connect("clicked", lambda btn: self.set_fit_mode("original"))
        fit_box.append(fit_original_button)

        popover_box.append(fit_box)
        self.settings_popover.set_child(popover_box)

        # Menu button con opciones adicionales
        self.menu_button = Gtk.MenuButton()
        self.menu_button.set_icon_name("open-menu-symbolic")
        self.menu_button.set_tooltip_text("Opciones")

        # Crear popover de menú
        self.menu_popover = Gtk.Popover()
        self.menu_button.set_popover(self.menu_popover)

        menu_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        menu_box.set_margin_start(12)
        menu_box.set_margin_end(12)
        menu_box.set_margin_top(12)
        menu_box.set_margin_bottom(12)

        # Opción continuo (CheckButton)
        self.continuous_check = Gtk.CheckButton()
        self.continuous_check.set_label("Modo continuo")
        self.continuous_check.set_active(False)  # Por defecto desactivado
        menu_box.append(self.continuous_check)

        # Separador
        menu_separator = Gtk.Separator()
        menu_box.append(menu_separator)

        # Sección de calidad de imagen
        quality_label = Gtk.Label(label="Calidad de imagen")
        quality_label.add_css_class("heading")
        quality_label.set_halign(Gtk.Align.START)
        menu_box.append(quality_label)

        # Opciones de interpolación
        interp_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)

        # Nítido (Nearest)
        sharp_button = Gtk.Button()
        sharp_button.set_label("Nítido (recomendado para cómics)")
        sharp_button.connect("clicked", lambda btn: self.set_interpolation_mode("nearest"))
        interp_box.append(sharp_button)

        # Suavizado (Bilinear)
        smooth_button = Gtk.Button()
        smooth_button.set_label("Suavizado")
        smooth_button.connect("clicked", lambda btn: self.set_interpolation_mode("bilinear"))
        interp_box.append(smooth_button)

        # Alta calidad (Hyper)
        quality_button = Gtk.Button()
        quality_button.set_label("Alta calidad (más lento)")
        quality_button.connect("clicked", lambda btn: self.set_interpolation_mode("hyper"))
        interp_box.append(quality_button)

        menu_box.append(interp_box)

        # Separador
        menu_separator2 = Gtk.Separator()
        menu_box.append(menu_separator2)

        # Botón pantalla completa en el menú
        fullscreen_button = Gtk.Button()
        fullscreen_button.set_label("Pantalla completa (F11)")
        fullscreen_button.connect("clicked", self.on_toggle_fullscreen)
        menu_box.append(fullscreen_button)

        self.menu_popover.set_child(menu_box)

        # Empacar botones en la headerbar
        self.header_bar.pack_end(self.menu_button)
        self.header_bar.pack_end(self.settings_button)

    def create_image_area(self):
        """Crear área scrolleable para mostrar la imagen"""
        # ScrolledWindow para permitir zoom y navegación
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.scrolled_window.set_vexpand(True)
        self.scrolled_window.set_hexpand(True)
        # Permitir contenido más grande que la ventana
        self.scrolled_window.set_propagate_natural_width(False)
        self.scrolled_window.set_propagate_natural_height(False)

        # Volver a usar Gtk.Picture que es más estable para mostrar imágenes
        self.comic_image = Gtk.Picture()
        self.comic_image.set_can_shrink(False)  # PERMITIR CRECER más allá del contenedor
        self.comic_image.set_keep_aspect_ratio(True)
        self.comic_image.set_content_fit(Gtk.ContentFit.FILL)  # Sin restricciones de tamaño
        self.comic_image.set_halign(Gtk.Align.CENTER)
        self.comic_image.set_valign(Gtk.Align.CENTER)

        # Configurar tamaño mínimo pero sin máximo
        self.comic_image.set_size_request(200, 300)  # Mínimo
        # NO establecer tamaño máximo para permitir zoom completo

        # Variables para la imagen actual
        self.current_pixbuf = None
        self.original_pixbuf = None
        self.current_page_path = None

        # Sistema de precarga para transiciones rápidas
        self.preload_cache = {}  # Cache de pixbufs precargados
        self.preload_buffer = 3  # Precargar 3 páginas antes y después
        self.loading_pool = None  # Pool de threads para precarga

        # Sistema de thumbnails progresivos
        self.thumbnail_pool = None  # Pool dedicado para thumbnails
        self.thumbnail_rows = []   # Referencias a rows de thumbnails
        self.thumbnail_futures = []  # Futures de carga de thumbnails

        # Control de scroll para navegación (valores configurables en constructor)
        self.scroll_accumulator = 0.0  # Acumulador de scroll
        self.last_scroll_time = 0  # Timestamp del último scroll

        # Scroll inteligente para cambio de página
        self.page_change_accumulator = 0.0  # Scroll acumulado en el borde
        self.page_change_threshold = 3.0  # Scroll necesario para cambiar página
        self.at_bottom = False  # ¿Estamos en el fondo de la página?
        self.at_top = False     # ¿Estamos en el inicio de la página?

        # Conectar eventos de mouse para navegación
        self.setup_mouse_events()

        self.scrolled_window.set_child(self.comic_image)

        # Contenedor para centrar y mensaje de carga
        self.image_area = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.image_area.set_vexpand(True)

        # Mensaje de carga
        self.loading_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.loading_box.set_halign(Gtk.Align.CENTER)
        self.loading_box.set_valign(Gtk.Align.CENTER)

        loading_spinner = Gtk.Spinner()
        loading_spinner.set_spinning(True)
        loading_spinner.set_size_request(48, 48)

        loading_label = Gtk.Label(label="Extrayendo páginas del comic...")
        loading_label.add_css_class("title-2")

        self.loading_box.append(loading_spinner)
        self.loading_box.append(loading_label)

        self.image_area.append(self.loading_box)

        # Tamaño mínimo inicial - se puede cambiar dinámicamente
        self.comic_image.set_size_request(200, 300)

    def create_thumbnail_sidebar(self):
        """Crear sidebar con thumbnails de todas las páginas"""
        self.sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.sidebar_box.set_margin_start(6)
        self.sidebar_box.set_margin_end(6)
        self.sidebar_box.set_margin_top(6)
        self.sidebar_box.set_margin_bottom(6)

        # Encabezado del sidebar
        sidebar_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        sidebar_header.set_margin_bottom(6)

        sidebar_title = Gtk.Label(label="Páginas")
        sidebar_title.add_css_class("heading")
        sidebar_title.set_halign(Gtk.Align.START)
        sidebar_header.append(sidebar_title)

        self.sidebar_box.append(sidebar_header)

        # ScrolledWindow para la lista de thumbnails
        self.thumbnail_scroll = Gtk.ScrolledWindow()
        self.thumbnail_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.thumbnail_scroll.set_vexpand(True)

        # Lista de thumbnails
        self.thumbnail_list = Gtk.ListBox()
        self.thumbnail_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.thumbnail_list.connect("row-selected", self.on_thumbnail_selected)
        self.thumbnail_list.add_css_class("navigation-sidebar")

        self.thumbnail_scroll.set_child(self.thumbnail_list)
        self.sidebar_box.append(self.thumbnail_scroll)

    def on_toggle_sidebar(self, button):
        """Mostrar/ocultar sidebar de thumbnails"""
        is_active = button.get_active()
        self.overlay_split_view.set_show_sidebar(is_active)

        if is_active and not hasattr(self, '_thumbnails_loaded'):
            # Cargar thumbnails la primera vez que se abre
            self.load_thumbnails()

    def load_thumbnails(self):
        """Cargar thumbnails con placeholders inmediatos y carga progresiva"""
        if not self.pages:
            return

        self._thumbnails_loaded = True
        page_count = len(self.pages)

        print(f"🔄 Inicializando thumbnails para {page_count} páginas...")

        # Limpiar lista existente
        while self.thumbnail_list.get_first_child():
            self.thumbnail_list.remove(self.thumbnail_list.get_first_child())

        # Fase 1: Crear TODOS los placeholders inmediatamente
        self.thumbnail_rows = []  # Guardar referencias para actualizar después
        for i in range(page_count):
            row = self._create_placeholder_row(i)
            self.thumbnail_list.append(row)
            self.thumbnail_rows.append(row)

        print(f"✅ {page_count} placeholders creados")

        # Fase 2: Iniciar carga asíncrona progresiva
        self._start_progressive_thumbnail_loading()

    def _create_placeholder_row(self, page_num):
        """Crear row con placeholder para thumbnail"""
        row = Gtk.ListBoxRow()
        row.set_selectable(True)
        row.page_number = page_num

        # Box para el contenido del thumbnail
        thumb_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        thumb_box.set_margin_start(4)
        thumb_box.set_margin_end(4)
        thumb_box.set_margin_top(4)
        thumb_box.set_margin_bottom(4)

        # Placeholder visual - tamaño fijo 180x240 (doble de grande)
        placeholder_image = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        placeholder_image.set_size_request(180, 240)
        placeholder_image.set_halign(Gtk.Align.CENTER)
        placeholder_image.set_valign(Gtk.Align.CENTER)
        placeholder_image.add_css_class("thumbnail-placeholder")

        # Fondo gris claro neutro
        placeholder_image.set_css_classes(["thumbnail-placeholder"])

        # Icono de carga pequeño
        loading_icon = Gtk.Spinner()
        loading_icon.set_spinning(True)
        loading_icon.set_size_request(16, 16)
        placeholder_image.append(loading_icon)

        thumb_box.append(placeholder_image)

        # Número de página
        page_label = Gtk.Label(label=f"Página {page_num + 1}")
        page_label.add_css_class("caption")
        page_label.set_halign(Gtk.Align.CENTER)
        thumb_box.append(page_label)

        row.set_child(thumb_box)

        # Guardar referencia al placeholder para reemplazar después
        row.placeholder_image = placeholder_image
        row.thumb_box = thumb_box

        return row

    def _start_progressive_thumbnail_loading(self):
        """Iniciar carga progresiva con pool de hilos optimizado"""
        if not self.pages:
            return

        page_count = len(self.pages)

        # Crear pool de hilos optimizado para thumbnails
        if hasattr(self, 'thumbnail_pool') and self.thumbnail_pool:
            self.thumbnail_pool.shutdown(wait=False)

        # 10-15 hilos concurrentes según el número de páginas
        max_workers = min(15, max(10, page_count // 10))
        print(f"🚀 Iniciando carga con {max_workers} hilos para {page_count} páginas")

        self.thumbnail_pool = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="thumbnail_loader"
        )

        # Enviar tareas de carga de thumbnails con priorización
        self.thumbnail_futures = []

        # Priorizar páginas cercanas a la actual
        current_page = getattr(self, 'current_page', 0)
        priority_range = 10  # Priorizar 10 páginas antes y después

        # Lista priorizada: páginas cercanas primero
        priority_pages = []
        other_pages = []

        for i in range(page_count):
            if abs(i - current_page) <= priority_range:
                priority_pages.append(i)
            else:
                other_pages.append(i)

        # Ordenar páginas prioritarias por cercanía
        priority_pages.sort(key=lambda x: abs(x - current_page))

        # Combinar listas: prioritarias primero
        all_pages = priority_pages + other_pages

        # Enviar tareas en orden de prioridad
        for i in all_pages:
            future = self.thumbnail_pool.submit(self._load_single_thumbnail, i)
            self.thumbnail_futures.append(future)

        print(f"📤 {page_count} tareas enviadas (priorizando página {current_page + 1})")

    def _load_single_thumbnail(self, page_num):
        """Cargar un single thumbnail en hilo separado"""
        if page_num >= len(self.pages):
            return

        page_path = self.pages[page_num]

        try:
            # Cargar imagen con tamaño fijo (doble de grande)
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                page_path, 180, 240, True
            )

            # Programar reemplazo en hilo principal
            GLib.idle_add(self._replace_placeholder_with_thumbnail, page_num, pixbuf)

            print(f"✅ Thumbnail {page_num + 1} cargado")

        except Exception as e:
            print(f"❌ Error cargando thumbnail {page_num + 1}: {e}")
            # Programar placeholder de error
            GLib.idle_add(self._replace_placeholder_with_error, page_num)

    def _replace_placeholder_with_thumbnail(self, page_num, pixbuf):
        """Reemplazar placeholder con thumbnail real (hilo principal)"""
        if page_num >= len(self.thumbnail_rows):
            return False

        try:
            row = self.thumbnail_rows[page_num]
            thumb_box = row.thumb_box

            # Remover placeholder anterior
            if row.placeholder_image and row.placeholder_image.get_parent() == thumb_box:
                thumb_box.remove(row.placeholder_image)

            # Crear nueva imagen con thumbnail real
            thumb_image = Gtk.Picture()
            thumb_image.set_pixbuf(pixbuf)
            thumb_image.set_size_request(180, 240)
            thumb_image.set_can_shrink(False)
            thumb_image.set_content_fit(Gtk.ContentFit.COVER)
            thumb_image.set_halign(Gtk.Align.CENTER)
            thumb_image.set_valign(Gtk.Align.CENTER)

            # Insertar antes del label de página
            thumb_box.prepend(thumb_image)

            # Limpiar referencia
            row.placeholder_image = None

        except Exception as e:
            print(f"Error reemplazando placeholder {page_num + 1}: {e}")

        return False  # No repetir

    def _replace_placeholder_with_error(self, page_num):
        """Reemplazar placeholder con indicador de error"""
        if page_num >= len(self.thumbnail_rows):
            return False

        try:
            row = self.thumbnail_rows[page_num]
            thumb_box = row.thumb_box

            # Remover placeholder anterior
            if row.placeholder_image and row.placeholder_image.get_parent() == thumb_box:
                thumb_box.remove(row.placeholder_image)

            # Crear placeholder de error
            error_placeholder = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            error_placeholder.set_size_request(180, 240)
            error_placeholder.set_halign(Gtk.Align.CENTER)
            error_placeholder.set_valign(Gtk.Align.CENTER)
            error_placeholder.add_css_class("thumbnail-error")

            error_icon = Gtk.Image()
            error_icon.set_from_icon_name("image-missing-symbolic")
            error_icon.set_pixel_size(32)
            error_placeholder.append(error_icon)

            thumb_box.prepend(error_placeholder)
            row.placeholder_image = None

        except Exception as e:
            print(f"Error creando placeholder de error {page_num + 1}: {e}")

        return False  # No repetir


    def on_thumbnail_selected(self, listbox, row):
        """Manejar selección de thumbnail para saltar a página"""
        if row:
            page_num = row.page_number
            self.go_to_page(page_num)
            # No cerrar sidebar automáticamente - el usuario lo controla manualmente

    def on_toggle_sidebar_key(self, *args):
        """Toggle sidebar via teclado"""
        current_state = self.sidebar_button.get_active()
        self.sidebar_button.set_active(not current_state)

    def update_thumbnail_selection(self):
        """Actualizar la selección del thumbnail según página actual"""
        if hasattr(self, 'thumbnail_list') and hasattr(self, '_thumbnails_loaded') and self._thumbnails_loaded:
            # Buscar el row correspondiente a la página actual
            row = self.thumbnail_list.get_row_at_index(self.current_page)
            if row:
                self.thumbnail_list.select_row(row)

    def create_navigation_bar(self):
        """Crear barra de navegación inferior"""
        self.navigation_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.navigation_bar.set_margin_start(12)
        self.navigation_bar.set_margin_end(12)
        self.navigation_bar.set_margin_top(8)
        self.navigation_bar.set_margin_bottom(8)
        self.navigation_bar.add_css_class("toolbar")

        # Botón página anterior
        self.prev_button = Gtk.Button()
        self.prev_button.set_icon_name("go-previous-symbolic")
        self.prev_button.set_tooltip_text("Página anterior (←)")
        self.prev_button.connect("clicked", self.on_prev_page)
        self.prev_button.set_sensitive(False)
        self.navigation_bar.append(self.prev_button)

        # Indicador de página movido a headerbar

        # Botón página siguiente
        self.next_button = Gtk.Button()
        self.next_button.set_icon_name("go-next-symbolic")
        self.next_button.set_tooltip_text("Página siguiente (→)")
        self.next_button.connect("clicked", self.on_next_page)
        self.next_button.set_sensitive(False)
        self.navigation_bar.append(self.next_button)

    def setup_mouse_events(self):
        """Configurar eventos de mouse para navegación"""
        # Click controller para navegación con mouse
        click_controller = Gtk.GestureClick()
        click_controller.connect("pressed", self.on_image_clicked)
        self.comic_image.add_controller(click_controller)

        # Scroll controller para zoom
        scroll_controller = Gtk.EventControllerScroll()
        scroll_controller.set_flags(Gtk.EventControllerScrollFlags.VERTICAL)
        scroll_controller.connect("scroll", self.on_image_scroll)
        self.comic_image.add_controller(scroll_controller)

    def setup_keyboard_shortcuts(self):
        """Configurar atajos de teclado"""
        controller = Gtk.ShortcutController()

        # Navegación
        shortcuts = [
            ("Left", self.on_prev_page),
            ("Right", self.on_next_page),
            ("space", self.on_next_page),
            ("Page_Down", self.on_next_page),
            ("Page_Up", self.on_prev_page),
            ("Home", lambda: self.go_to_page(0)),
            ("End", lambda: self.go_to_page(len(self.pages) - 1)),
            # Zoom
            ("equal", self.on_zoom_in),
            ("minus", self.on_zoom_out),
            ("0", self.on_zoom_100),
            # Ajuste
            ("w", lambda: self.set_fit_mode("width")),
            ("h", lambda: self.set_fit_mode("height")),
            ("p", lambda: self.set_fit_mode("page")),
            # Cerrar
            ("Escape", self.on_close_clicked),
            ("<Control>w", self.on_close_clicked),
            # Pantalla completa - múltiples atajos
            ("F11", self.on_toggle_fullscreen),
            ("<Alt>Return", self.on_toggle_fullscreen),  # Alt+Enter común en muchas apps
            ("F", self.on_toggle_fullscreen),  # F simple también
            # Sidebar de thumbnails
            ("T", self.on_toggle_sidebar_key),  # T para toggle sidebar
            # Control de sensibilidad de scroll
            ("<Control>plus", lambda: self.adjust_scroll_sensitivity("decrease")),  # Más sensible
            ("<Control>minus", lambda: self.adjust_scroll_sensitivity("increase")),  # Menos sensible
            ("<Control>0", self.reset_scroll_sensitivity),  # Reset sensibilidad
        ]

        for key_combination, callback in shortcuts:
            shortcut = Gtk.Shortcut()
            shortcut.set_trigger(Gtk.ShortcutTrigger.parse_string(key_combination))
            shortcut.set_action(Gtk.CallbackAction.new(lambda w, args, cb=callback: cb() or True))
            controller.add_shortcut(shortcut)

        self.add_controller(controller)

    def extract_pages(self):
        """Extraer páginas del comic en hilo separado"""
        def extraction_worker():
            try:
                if not ComicExtractor:
                    GLib.idle_add(self.on_extraction_error, "ComicExtractor no disponible")
                    return

                print(f"Extrayendo páginas de: {self.comic_path}")

                # Limpiar caches antiguos antes de empezar
                self.cleanup_old_comic_caches()

                # Crear directorio cache basado en el comic
                cache_dir = self.get_or_create_comic_cache_dir()
                if not cache_dir:
                    GLib.idle_add(self.on_extraction_error, "No se pudo crear directorio de cache")
                    return

                # Actualizar timestamp del directorio actual (touch)
                self.touch_cache_directory(cache_dir)

                # Verificar si ya está en cache y es válido
                if self.is_cache_valid(cache_dir):
                    print(f"✅ Usando cache existente: {cache_dir}")
                    cached_pages = self.load_cached_pages(cache_dir)
                    if cached_pages:
                        GLib.idle_add(self.on_extraction_complete, cached_pages)
                        return
                    else:
                        print("⚠️ Cache corrupto, re-extrayendo...")

                print(f"📦 Extrayendo a directorio cache: {cache_dir}")
                self.temp_dir = cache_dir

                # Callbacks para progreso
                def progress_callback(progress):
                    percent = int(progress * 100)
                    GLib.idle_add(self.update_extraction_progress, percent)

                def status_callback(message):
                    GLib.idle_add(self.update_extraction_status, message)

                # Crear extractor con callbacks
                extractor = ComicExtractor(progress_callback, status_callback)

                # Verificar si el formato es soportado
                comic_format = extractor.detect_comic_format(self.comic_path)
                if not comic_format:
                    GLib.idle_add(self.on_extraction_error, "Formato de archivo no soportado")
                    return

                print(f"Formato detectado: {comic_format}")

                # Extraer páginas usando el método correcto
                extracted_pages = extractor.extract_comic_pages(self.comic_path, self.temp_dir)

                if extracted_pages:
                    print(f"Páginas extraídas: {len(extracted_pages)}")
                    # Las páginas ya están ordenadas por el extractor
                    GLib.idle_add(self.on_extraction_complete, extracted_pages)
                else:
                    GLib.idle_add(self.on_extraction_error, "No se encontraron páginas válidas o error en extracción")

            except Exception as e:
                print(f"Error en extracción: {e}")
                GLib.idle_add(self.on_extraction_error, str(e))

        # Ejecutar en hilo separado
        threading.Thread(target=extraction_worker, daemon=True).start()

    def on_extraction_complete(self, pages):
        """Callback cuando la extracción se completa exitosamente"""
        self.pages = pages
        page_count = len(self.pages)
        print(f"Extracción completa: {page_count} páginas")

        # Ajustar buffer de precarga según el número de páginas
        if page_count > 100:
            self.preload_buffer = 2  # Menos buffer para comics grandes
            print(f"📚 Comic grande ({page_count} páginas) - buffer reducido a {self.preload_buffer}")
        elif page_count > 50:
            self.preload_buffer = 3  # Buffer normal
            print(f"📖 Comic mediano ({page_count} páginas) - buffer normal {self.preload_buffer}")
        else:
            self.preload_buffer = 5  # Más buffer para comics pequeños
            print(f"📰 Comic pequeño ({page_count} páginas) - buffer amplio {self.preload_buffer}")

        # Ocultar mensaje de carga y mostrar imagen
        if self.loading_box.get_parent() == self.image_area:
            self.image_area.remove(self.loading_box)
        self.image_area.append(self.scrolled_window)

        # Mostrar primera página
        self.go_to_page(0)

        # Habilitar controles
        self.update_navigation_buttons()

        # Guardar información de cache para validación futura
        if hasattr(self, 'temp_dir') and self.temp_dir:
            self.save_cache_info(self.temp_dir)

        # Actualizar indicador de zoom inicial
        self.update_zoom_indicator()

        self.show_toast(f"Comic cargado: {page_count} páginas", "success")

    def update_extraction_progress(self, percent):
        """Actualizar progreso de extracción"""
        if hasattr(self, 'loading_box'):
            # Buscar label en loading_box y actualizarlo
            child = self.loading_box.get_first_child()
            while child:
                if isinstance(child, Gtk.Label):
                    child.set_text(f"Extrayendo páginas... {percent}%")
                    break
                child = child.get_next_sibling()

    def update_extraction_status(self, message):
        """Actualizar estado de extracción"""
        print(f"Estado extracción: {message}")
        if hasattr(self, 'loading_box'):
            # Buscar label en loading_box y actualizarlo si no es de progreso
            child = self.loading_box.get_first_child()
            while child:
                if isinstance(child, Gtk.Label) and "%" not in child.get_text():
                    child.set_text(message)
                    break
                child = child.get_next_sibling()

    def on_extraction_error(self, error_message):
        """Callback cuando hay error en la extracción"""
        print(f"Error extrayendo páginas: {error_message}")

        # Mostrar mensaje de error
        error_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        error_box.set_halign(Gtk.Align.CENTER)
        error_box.set_valign(Gtk.Align.CENTER)

        error_icon = Gtk.Image.new_from_icon_name("dialog-error-symbolic")
        error_icon.set_icon_size(Gtk.IconSize.LARGE)

        error_label = Gtk.Label(label="Error cargando comic")
        error_label.add_css_class("title-2")

        error_detail = Gtk.Label(label=error_message)
        error_detail.add_css_class("dim-label")

        retry_button = Gtk.Button(label="Reintentar")
        retry_button.connect("clicked", lambda btn: self.extract_pages())
        retry_button.add_css_class("suggested-action")

        error_box.append(error_icon)
        error_box.append(error_label)
        error_box.append(error_detail)
        error_box.append(retry_button)

        if self.loading_box.get_parent() == self.image_area:
            self.image_area.remove(self.loading_box)
        self.image_area.append(error_box)

        self.show_toast("Error cargando comic", "error")

    def go_to_page(self, page_number):
        """Ir a una página específica"""
        if not self.pages or page_number < 0 or page_number >= len(self.pages):
            return

        self.current_page = page_number
        page_path = self.pages[page_number]
        self.current_page_path = page_path

        print(f"📄 Mostrando página {page_number + 1}: {page_path}")
        print(f"🎛️ Estado actual - Modo: {self.fit_mode}, Zoom: {self.zoom_level}")

        try:
            # Verificar que el archivo existe
            if not os.path.exists(page_path):
                print(f"Archivo no existe: {page_path}")
                self.show_toast(f"Página {page_number + 1} no encontrada", "error")
                return

            # Primero cargar el pixbuf para tener control total
            print(f"📂 Cargando página {page_number + 1}")
            try:
                self.original_pixbuf = GdkPixbuf.Pixbuf.new_from_file(page_path)
                orig_w = self.original_pixbuf.get_width()
                orig_h = self.original_pixbuf.get_height()
                file_size_mb = os.path.getsize(page_path) / (1024 * 1024)
                print(f"🖼️ Imagen cargada: {orig_w}x{orig_h} píxeles ({file_size_mb:.1f} MB)")
                print(f"📁 Archivo: {os.path.basename(page_path)}")

                # Aplicar configuración inmediatamente CON control total
                self.apply_current_view_settings()

            except Exception as e:
                print(f"Error cargando pixbuf: {e}")
                self.original_pixbuf = None
                # Fallback a método anterior si falla
                print(f"🔄 Fallback: usando set_filename")
                self.comic_image.set_filename(page_path)
                self.configure_image_size()

            # Actualizar interfaz
            self.update_page_label()
            self.update_navigation_buttons()
            # Actualizar selección en sidebar de thumbnails
            self.update_thumbnail_selection()

            # RESETEAR posición de scroll al inicio de la nueva página (con delay)
            GLib.idle_add(self.reset_scroll_position)

            # Resetear acumulador de scroll inteligente
            self.page_change_accumulator = 0.0

            # Iniciar precarga de páginas adyacentes para transiciones rápidas
            self.start_preload_adjacent_pages()

            print(f"Página {page_number + 1} cargada exitosamente")

        except Exception as e:
            print(f"Error cargando página {page_number}: {e}")
            import traceback
            traceback.print_exc()
            self.show_toast(f"Error cargando página {page_number + 1}", "error")

    def apply_current_view_settings(self):
        """Aplicar configuración actual de zoom y ajuste"""
        if not self.original_pixbuf or not self.current_page_path:
            print("❌ No hay imagen original o ruta disponible")
            return

        print(f"🔧 APLICANDO configuración: Modo={self.fit_mode}, Zoom={self.zoom_level}")
        print(f"📄 Página actual: {os.path.basename(self.current_page_path)}")

        try:
            # Obtener dimensiones de la ventana
            widget_width = self.scrolled_window.get_allocated_width()
            widget_height = self.scrolled_window.get_allocated_height()

            # Si no tenemos dimensiones aún, usar valores por defecto
            if widget_width <= 1 or widget_height <= 1:
                print("Usando dimensiones por defecto")
                widget_width = 800
                widget_height = 600

            print(f"Área disponible: {widget_width}x{widget_height}")

            # Obtener dimensiones originales
            orig_width = self.original_pixbuf.get_width()
            orig_height = self.original_pixbuf.get_height()

            print(f"Imagen original: {orig_width}x{orig_height}, Modo: {self.fit_mode}, Zoom: {self.zoom_level}")

            # Si zoom es diferente de 1.0 O modo es "original", usarlo directamente
            if abs(self.zoom_level - 1.0) > 0.01 or self.fit_mode == "original":
                # Zoom manual o tamaño original: usar tamaño original * zoom
                new_width = int(orig_width * self.zoom_level)
                new_height = int(orig_height * self.zoom_level)
                if self.fit_mode == "original" and abs(self.zoom_level - 1.0) < 0.01:
                    print(f"📏 Tamaño original: {orig_width}x{orig_height} (sin escalar)")
                else:
                    print(f"🔍 Zoom manual: {orig_width}x{orig_height} → {new_width}x{new_height} (factor: {self.zoom_level})")
            else:
                # Otros modos de ajuste automático
                new_width, new_height = self.calculate_size_for_mode(
                    orig_width, orig_height, widget_width, widget_height
                )
                print(f"📐 Ajuste automático: {orig_width}x{orig_height} → {new_width}x{new_height} (modo: {self.fit_mode})")

            print(f"Nuevo tamaño calculado: {new_width}x{new_height}")

            # Configurar Picture según el modo
            if abs(self.zoom_level - 1.0) > 0.01 or self.fit_mode == "original":
                # Zoom manual O tamaño original: sin restricciones
                self.comic_image.set_content_fit(Gtk.ContentFit.FILL)
                self.comic_image.set_can_shrink(False)  # NO reducir tamaño
                # Quitar restricciones de tamaño para permitir tamaño real
                self.comic_image.set_size_request(-1, -1)  # Sin restricciones

                if self.fit_mode == "original" and abs(self.zoom_level - 1.0) < 0.01:
                    print(f"📏 Tamaño original: FILL + can_shrink=False + sin restricciones")
                else:
                    print(f"🔓 Zoom manual: FILL + can_shrink=False + sin restricciones (zoom: {self.zoom_level})")
            else:
                # Otros ajustes automáticos: permitir reducción
                self.comic_image.set_can_shrink(True)  # Permitir reducir para ajustes
                if self.fit_mode == "width":
                    self.comic_image.set_content_fit(Gtk.ContentFit.SCALE_DOWN)
                elif self.fit_mode == "height":
                    self.comic_image.set_content_fit(Gtk.ContentFit.SCALE_DOWN)
                elif self.fit_mode == "page":
                    self.comic_image.set_content_fit(Gtk.ContentFit.CONTAIN)
                print(f"📐 Ajuste automático: {self.fit_mode} + can_shrink=True")

            # Si necesitamos redimensionar
            if new_width != orig_width or new_height != orig_height:
                try:
                    interp_type = self.get_interpolation_type()
                    scaled_pixbuf = self.original_pixbuf.scale_simple(
                        new_width, new_height, interp_type
                    )
                    texture = Gdk.Texture.new_for_pixbuf(scaled_pixbuf)
                    self.comic_image.set_paintable(texture)
                    self.current_pixbuf = scaled_pixbuf

                    print(f"Imagen escalada aplicada: {new_width}x{new_height}")

                except Exception as e:
                    print(f"Error escalando imagen: {e}")
                    # Fallback: usar imagen original
                    texture = Gdk.Texture.new_for_pixbuf(self.original_pixbuf)
                    self.comic_image.set_paintable(texture)
            else:
                # Usar imagen original sin escalar
                texture = Gdk.Texture.new_for_pixbuf(self.original_pixbuf)
                self.comic_image.set_paintable(texture)
                self.current_pixbuf = self.original_pixbuf

                print("Usando imagen original sin escalado")

        except Exception as e:
            print(f"Error aplicando configuración de vista: {e}")
            import traceback
            traceback.print_exc()

            # Fallback: cargar imagen directamente
            if self.current_page_path and os.path.exists(self.current_page_path):
                print("Fallback: cargando imagen directamente")
                self.comic_image.set_filename(self.current_page_path)

    def configure_image_size(self):
        """Configurar tamaño de imagen de manera simple"""
        if not self.comic_image:
            return

        try:
            # Configurar el ContentFit según el modo
            if self.fit_mode == "width":
                self.comic_image.set_content_fit(Gtk.ContentFit.SCALE_DOWN)
                print("Configurado para ajustar al ancho")
            elif self.fit_mode == "height":
                self.comic_image.set_content_fit(Gtk.ContentFit.SCALE_DOWN)
                print("Configurado para ajustar a la altura")
            elif self.fit_mode == "page":
                self.comic_image.set_content_fit(Gtk.ContentFit.CONTAIN)
                print("Configurado para ajustar la página completa")
            else:  # original
                self.comic_image.set_content_fit(Gtk.ContentFit.FILL)
                print("Configurado para tamaño original")

            # Si tenemos zoom diferente de 1.0, aplicar zoom personalizado
            if self.zoom_level != 1.0 and self.original_pixbuf:
                self.apply_zoom_to_image()

        except Exception as e:
            print(f"Error configurando tamaño de imagen: {e}")

    def apply_zoom_to_image(self):
        """Aplicar zoom a la imagen actual"""
        if not self.original_pixbuf:
            return

        try:
            orig_width = self.original_pixbuf.get_width()
            orig_height = self.original_pixbuf.get_height()

            new_width = int(orig_width * self.zoom_level)
            new_height = int(orig_height * self.zoom_level)

            print(f"Aplicando zoom {self.zoom_level}: {orig_width}x{orig_height} -> {new_width}x{new_height}")

            interp_type = self.get_interpolation_type()
            scaled_pixbuf = self.original_pixbuf.scale_simple(
                new_width, new_height, interp_type
            )

            texture = Gdk.Texture.new_for_pixbuf(scaled_pixbuf)
            self.comic_image.set_paintable(texture)
            self.current_pixbuf = scaled_pixbuf

        except Exception as e:
            print(f"Error aplicando zoom: {e}")

    def calculate_size_for_mode(self, orig_width, orig_height, widget_width, widget_height):
        """Calcular tamaño según el modo de ajuste"""
        if self.fit_mode == "width":
            # Ajustar al ancho, mantener proporción
            scale = widget_width / orig_width
            return widget_width, int(orig_height * scale)

        elif self.fit_mode == "height":
            # Ajustar a la altura, mantener proporción
            scale = widget_height / orig_height
            return int(orig_width * scale), widget_height

        elif self.fit_mode == "page":
            # Ajustar toda la página (el menor de los escalados)
            scale_width = widget_width / orig_width
            scale_height = widget_height / orig_height
            scale = min(scale_width, scale_height)
            return int(orig_width * scale), int(orig_height * scale)

        else:
            # Tamaño original
            return orig_width, orig_height

    def set_fit_mode(self, mode):
        """Cambiar modo de ajuste"""
        self.fit_mode = mode
        print(f"Modo de ajuste cambiado a: {mode}")

        # Aplicar inmediatamente si tenemos una imagen cargada
        if self.current_page_path and self.original_pixbuf:
            self.apply_current_view_settings()
        elif self.current_page_path:
            # Fallback si no tenemos original_pixbuf aún
            self.configure_image_size()

        self.show_toast(f"Ajuste: {mode}", "info")

    def start_preload_adjacent_pages(self):
        """Iniciar precarga de páginas adyacentes para transiciones rápidas"""
        if not self.pages:
            return

        # Crear pool de threads si no existe
        if self.loading_pool is None:
            self.loading_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="preload")

        # Determinar rango de páginas a precargar
        start_page = max(0, self.current_page - self.preload_buffer)
        end_page = min(len(self.pages), self.current_page + self.preload_buffer + 1)

        # Precargar páginas que no están en cache
        for page_num in range(start_page, end_page):
            if page_num != self.current_page and page_num not in self.preload_cache:
                self.loading_pool.submit(self.preload_page, page_num)

        # Limpiar cache de páginas lejanas para liberar memoria
        self.cleanup_distant_pages()

    def preload_page(self, page_num):
        """Precargar una página específica en hilo separado"""
        if page_num < 0 or page_num >= len(self.pages):
            return

        page_path = self.pages[page_num]

        try:
            print(f"Precargando página {page_num + 1}...")

            # Cargar solo si el archivo existe
            if os.path.exists(page_path):
                # Para precarga, cargamos una versión optimizada
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    page_path, 1920, 1080, True  # Tamaño máximo razonable
                )

                # Guardar en cache
                self.preload_cache[page_num] = {
                    'path': page_path,
                    'pixbuf': pixbuf,
                    'timestamp': threading.current_thread().ident
                }

                print(f"✅ Página {page_num + 1} precargada")
            else:
                print(f"❌ Página {page_num + 1} no existe: {page_path}")

        except Exception as e:
            print(f"Error precargando página {page_num + 1}: {e}")

    def cleanup_distant_pages(self):
        """Limpiar páginas lejanas del cache para liberar memoria"""
        if not self.preload_cache:
            return

        # Mantener solo páginas dentro del buffer + margen extra
        keep_range = self.preload_buffer + 2
        pages_to_remove = []

        for page_num in self.preload_cache.keys():
            if abs(page_num - self.current_page) > keep_range:
                pages_to_remove.append(page_num)

        for page_num in pages_to_remove:
            del self.preload_cache[page_num]
            print(f"🗑️ Página {page_num + 1} removida del cache")

    def get_fast_page(self, page_num):
        """Obtener página desde cache o cargar rápidamente"""
        if page_num in self.preload_cache:
            print(f"⚡ Página {page_num + 1} desde cache")
            return self.preload_cache[page_num]['path']
        else:
            # Fallback a carga normal
            if page_num < len(self.pages):
                return self.pages[page_num]
        return None

    def update_page_label(self):
        """Actualizar etiqueta de página actual"""
        if self.pages:
            # Actualizar entrada de página (sin triggerar el callback)
            self.page_entry.set_range(1, len(self.pages))

            # Temporalmente desconectar el callback para evitar recursión
            self.page_entry.handler_block_by_func(self.on_page_entry_changed)
            self.page_entry.set_value(self.current_page + 1)
            self.page_entry.handler_unblock_by_func(self.on_page_entry_changed)

            # Actualizar label de total de páginas
            self.total_pages_label.set_text(f"de {len(self.pages)}")
        else:
            self.page_entry.set_range(1, 1)
            self.page_entry.set_value(1)
            self.total_pages_label.set_text("de --")

    def update_navigation_buttons(self):
        """Actualizar estado de botones de navegación"""
        # Solo actualizar si existen los botones
        if hasattr(self, 'prev_button') and self.prev_button:
            self.prev_button.set_sensitive(self.current_page > 0)
        if hasattr(self, 'next_button') and self.next_button:
            self.next_button.set_sensitive(self.current_page < len(self.pages) - 1)

    def on_page_entry_changed(self, spin_button):
        """Manejar cambio en la entrada de página"""
        # No hacer nada durante el cambio automático
        pass

    def on_page_entry_activate(self, entry):
        """Manejar activación de la entrada de página (Enter)"""
        page_number = int(self.page_entry.get_value()) - 1  # Convertir a índice base 0
        if 0 <= page_number < len(self.pages):
            self.go_to_page(page_number)

    def on_prev_page(self, *args):
        """Ir a página anterior"""
        if self.current_page > 0:
            self.go_to_page(self.current_page - 1)

    def on_next_page(self, *args):
        """Ir a página siguiente"""
        if self.current_page < len(self.pages) - 1:
            self.go_to_page(self.current_page + 1)

    def on_zoom_in(self, *args):
        """Acercar zoom"""
        old_zoom = self.zoom_level
        self.zoom_level = min(self.zoom_level * 1.25, 5.0)
        print(f"🔍 ZOOM IN: {old_zoom:.2f} → {self.zoom_level:.2f}")
        self.apply_zoom()

    def on_zoom_out(self, *args):
        """Alejar zoom"""
        old_zoom = self.zoom_level
        self.zoom_level = max(self.zoom_level / 1.25, 0.1)
        print(f"🔍 ZOOM OUT: {old_zoom:.2f} → {self.zoom_level:.2f}")
        self.apply_zoom()

    def on_zoom_100(self, *args):
        """Zoom 100%"""
        old_zoom = self.zoom_level
        self.zoom_level = 1.0
        print(f"🔍 ZOOM 100%: {old_zoom:.2f} → {self.zoom_level:.2f}")
        self.apply_zoom()

    def apply_zoom(self):
        """Aplicar nivel de zoom actual"""
        # Aplicar inmediatamente si tenemos una imagen cargada
        if self.current_page_path and self.original_pixbuf:
            self.apply_current_view_settings()
        elif self.current_page_path:
            # Fallback si no tenemos original_pixbuf aún
            self.configure_image_size()

        print(f"Zoom aplicado: {self.zoom_level:.2f}")

        # Actualizar indicador de zoom en la UI
        self.update_zoom_indicator()

        # Calcular zoom real vs zoom solicitado
        actual_zoom_percent = int(self.zoom_level * 100)

        # Si hay imagen, calcular el zoom efectivo
        if self.original_pixbuf and self.current_pixbuf:
            orig_width = self.original_pixbuf.get_width()
            current_width = self.current_pixbuf.get_width()
            effective_zoom = (current_width / orig_width) if orig_width > 0 else 1.0
            effective_percent = int(effective_zoom * 100)

            if abs(effective_percent - actual_zoom_percent) > 5:
                self.show_toast(f"Zoom: {actual_zoom_percent}% (efectivo: {effective_percent}%)", "info")
            else:
                self.show_toast(f"Zoom: {actual_zoom_percent}%", "info")

            print(f"🔍 Zoom solicitado: {actual_zoom_percent}%, efectivo: {effective_percent}%")
        else:
            self.show_toast(f"Zoom: {actual_zoom_percent}%", "info")

    def on_image_clicked(self, gesture, n_press, x, y):
        """Manejar click en imagen para navegación"""
        if n_press == 1:  # Click simple
            width = self.comic_image.get_width()

            # Dividir imagen en zonas para navegación
            if x < width / 3:
                # Click izquierdo - página anterior
                self.on_prev_page()
            elif x > width * 2 / 3:
                # Click derecho - página siguiente
                self.on_next_page()
            # Click centro - no hacer nada

    def on_image_scroll(self, controller, dx, dy):
        """Manejar scroll inteligente: normal + acumulación en bordes"""
        # Obtener el estado de las teclas modificadoras
        modifiers = controller.get_current_event_state()

        # Si Ctrl está presionado, hacer zoom (inmediato, sin threshold)
        if modifiers & Gdk.ModifierType.CONTROL_MASK:
            if dy > 0.1:  # Threshold mínimo para zoom
                self.on_zoom_out()
            elif dy < -0.1:
                self.on_zoom_in()
            return True

        # Scroll inteligente: permitir scroll normal + cambio de página en bordes
        else:
            return self._handle_smart_scroll(dy)

    def _handle_smart_scroll(self, dy):
        """Scroll inteligente: normal en página, acumulación en bordes"""
        # Primero, obtener información del scroll actual
        v_adjustment = self.scrolled_window.get_vadjustment()
        if not v_adjustment:
            return False  # No hay scroll disponible

        current_value = v_adjustment.get_value()
        lower = v_adjustment.get_lower()
        upper = v_adjustment.get_upper()
        page_size = v_adjustment.get_page_size()

        # Calcular posiciones de borde
        max_scroll = upper - page_size
        tolerance = 5  # Píxeles de tolerancia

        # Detectar si estamos en los bordes
        self.at_top = current_value <= (lower + tolerance)
        self.at_bottom = current_value >= (max_scroll - tolerance)

        # Debug información
        if abs(dy) > 0.1:  # Solo mostrar si hay scroll real
            print(f"📜 Scroll: dy={dy:.2f}, pos={current_value:.0f}/{max_scroll:.0f}, top={self.at_top}, bottom={self.at_bottom}")

        # SCROLL HACIA ABAJO
        if dy > 0:
            if self.at_bottom:
                # Estamos en el fondo: acumular para cambio de página
                self.page_change_accumulator += dy
                print(f"🔄 Acumulando en fondo: {self.page_change_accumulator:.2f}/{self.page_change_threshold}")

                if self.page_change_accumulator >= self.page_change_threshold:
                    # Suficiente acumulación: ir a página siguiente
                    if self.current_page < len(self.pages) - 1:
                        print(f"➡️ Página siguiente por acumulación")
                        self.go_to_page(self.current_page + 1)
                        self.page_change_accumulator = 0.0
                    else:
                        print("🚫 Ya en última página")
                        self.page_change_accumulator = 0.0

                return True  # Consumir el evento
            else:
                # No estamos en el fondo: resetear acumulador y permitir scroll normal
                self.page_change_accumulator = 0.0
                return False  # Permitir scroll normal

        # SCROLL HACIA ARRIBA
        elif dy < 0:
            if self.at_top:
                # Estamos en el inicio: acumular para página anterior
                self.page_change_accumulator += abs(dy)  # Usar valor absoluto
                print(f"🔄 Acumulando en inicio: {self.page_change_accumulator:.2f}/{self.page_change_threshold}")

                if self.page_change_accumulator >= self.page_change_threshold:
                    # Suficiente acumulación: ir a página anterior
                    if self.current_page > 0:
                        print(f"⬅️ Página anterior por acumulación")
                        self.go_to_page(self.current_page - 1)
                        self.page_change_accumulator = 0.0
                    else:
                        print("🚫 Ya en primera página")
                        self.page_change_accumulator = 0.0

                return True  # Consumir el evento
            else:
                # No estamos en el inicio: resetear acumulador y permitir scroll normal
                self.page_change_accumulator = 0.0
                return False  # Permitir scroll normal

        return False  # Permitir scroll normal por defecto

    def adjust_scroll_sensitivity(self, direction):
        """Ajustar sensibilidad del scroll"""
        if direction == "increase":
            self.scroll_threshold = min(self.scroll_threshold + 0.5, 5.0)
            self.show_toast(f"Sensibilidad scroll: {self.scroll_threshold:.1f} (menos sensible)", "info")
        elif direction == "decrease":
            self.scroll_threshold = max(self.scroll_threshold - 0.5, 0.3)
            self.show_toast(f"Sensibilidad scroll: {self.scroll_threshold:.1f} (más sensible)", "info")

        print(f"Nuevo threshold de scroll: {self.scroll_threshold}")

    def reset_scroll_sensitivity(self):
        """Resetear sensibilidad a valor por defecto"""
        self.scroll_threshold = 1.0
        self.scroll_accumulator = 0.0
        self.show_toast("Sensibilidad de scroll reseteada", "info")
        print(f"Threshold reseteado a: {self.scroll_threshold}")

    def on_toggle_fullscreen(self, *args):
        """Alternar pantalla completa con múltiples enfoques"""
        try:
            print(f"=== TOGGLE FULLSCREEN CALLED ===")
            print(f"Window type: {type(self)}")

            # Comprobar estado actual
            current_maximized = self.is_maximized()
            current_fullscreen = self.is_fullscreen()

            print(f"Estado actual - Maximized: {current_maximized}, Fullscreen: {current_fullscreen}")

            if current_fullscreen or current_maximized:
                print("→ Restaurando ventana normal")
                # Salir de ambos estados
                if current_fullscreen:
                    self.unfullscreen()
                if current_maximized:
                    self.unmaximize()

                # Establecer tamaño normal
                self.set_default_size(1200, 800)
                self.show_toast("Ventana restaurada", "info")

            else:
                print("→ Intentando pantalla completa")
                # Primero intentar fullscreen real
                self.fullscreen()

                # Si no funciona, usar maximize como alternativa
                GLib.timeout_add(100, self._try_maximize_fallback)
                self.show_toast("Pantalla completa", "info")

        except Exception as e:
            print(f"❌ Error en toggle_fullscreen: {e}")
            import traceback
            traceback.print_exc()
            # Fallback: al menos maximizar
            try:
                if self.is_maximized():
                    self.unmaximize()
                else:
                    self.maximize()
                self.show_toast("Ventana maximizada (alternativa)", "info")
            except:
                self.show_toast("Error con pantalla completa", "error")

    def _try_maximize_fallback(self):
        """Fallback: si fullscreen no funciona, usar maximize"""
        if not self.is_fullscreen():
            print("Fullscreen no funcionó, usando maximize como alternativa")
            self.maximize()
        return False  # No repetir el timeout

    def verify_fullscreen_change(self, expected_state):
        """Verificar que el cambio de pantalla completa funcionó"""
        actual_state = self.is_fullscreen()
        print(f"Estado esperado: {expected_state}, Estado actual: {actual_state}")

        if actual_state != expected_state:
            print("⚠️ El cambio de pantalla completa no funcionó!")
            if expected_state:
                self.show_toast("Error: No se pudo entrar en pantalla completa", "error")
            else:
                self.show_toast("Error: No se pudo salir de pantalla completa", "error")
        else:
            print("✅ Cambio de pantalla completa exitoso")

        return False  # No repetir el timeout

    def on_window_size_changed(self, *args):
        """Reajustar imagen cuando cambia el tamaño de ventana"""
        # Solo reajustar si tenemos una imagen y el modo de ajuste no es original
        if self.original_pixbuf and self.fit_mode != "original":
            GLib.idle_add(self.apply_current_view_settings)

    def on_close_clicked(self, *args):
        """Cerrar lector"""
        self.cleanup()
        self.close()

    def cleanup(self):
        """Limpiar archivos temporales y recursos"""
        # Cerrar pool de threads de precarga
        if self.loading_pool:
            print("🔄 Cerrando pool de precarga...")
            self.loading_pool.shutdown(wait=False)
            self.loading_pool = None

        # Cerrar pool de thumbnails
        if self.thumbnail_pool:
            print("🔄 Cerrando pool de thumbnails...")
            self.thumbnail_pool.shutdown(wait=False)
            self.thumbnail_pool = None

        # Limpiar cache de precarga
        if self.preload_cache:
            print("🗑️ Limpiando cache de precarga...")
            self.preload_cache.clear()

        # Limpiar thumbnails
        if hasattr(self, 'thumbnail_rows'):
            self.thumbnail_rows.clear()
        if hasattr(self, 'thumbnail_futures'):
            self.thumbnail_futures.clear()

        # NO limpiar archivos temporales de cache (para reutilizar)
        # Solo limpiar si es directorio temporal aleatorio (no cache)
        if self.temp_dir and Path(self.temp_dir).exists():
            try:
                # Solo limpiar si es directorio temporal aleatorio (babelcomics_reader_XXXXXX)
                dir_name = os.path.basename(self.temp_dir)
                if dir_name.startswith("babelcomics_reader_") and len(dir_name) > 25:
                    # Es directorio temporal aleatorio, limpiar
                    import shutil
                    shutil.rmtree(self.temp_dir)
                    print(f"🗑️ Directorio temporal limpiado: {self.temp_dir}")
                else:
                    # Es directorio cache, mantener para reutilizar
                    print(f"💾 Directorio cache mantenido: {self.temp_dir}")
            except Exception as e:
                print(f"Error procesando directorio temporal: {e}")

    def get_or_create_comic_cache_dir(self):
        """Crear directorio de cache basado en el comic"""
        try:
            import hashlib

            # Crear nombre limpio del comic
            comic_name = Path(self.comic_path).stem
            # Limpiar caracteres especiales
            clean_name = "".join(c for c in comic_name if c.isalnum() or c in (' ', '-', '_')).strip()
            clean_name = clean_name.replace(' ', '_')[:50]  # Limitar longitud

            # Crear hash del path completo para unicidad
            path_hash = hashlib.md5(self.comic_path.encode()).hexdigest()[:8]

            # Nombre final: nombrecomic_hash8chars
            cache_folder_name = f"{clean_name}_{path_hash}"

            # Encontrar directorio base con espacio suficiente
            try:
                comic_size_mb = os.path.getsize(self.comic_path) // (1024 * 1024)
                required_space = max(500, comic_size_mb * 3)
            except:
                required_space = 500

            temp_base_dir = find_temp_directory_with_space(required_mb=required_space)
            cache_dir = os.path.join(temp_base_dir, cache_folder_name)

            print(f"📁 Directorio cache: {cache_dir}")

            # Crear directorio si no existe
            os.makedirs(cache_dir, exist_ok=True)

            return cache_dir

        except Exception as e:
            print(f"Error creando directorio cache: {e}")
            return None

    def is_cache_valid(self, cache_dir):
        """Verificar si el cache es válido (archivo no cambió)"""
        try:
            cache_info_file = os.path.join(cache_dir, ".babelcomics_cache_info")

            if not os.path.exists(cache_info_file):
                return False

            # Leer información del cache
            with open(cache_info_file, 'r') as f:
                cache_info = f.read().strip().split('\n')
                if len(cache_info) < 2:
                    return False

                cached_path = cache_info[0]
                cached_mtime = float(cache_info[1])

            # Verificar que el archivo no cambió
            if cached_path != self.comic_path:
                return False

            current_mtime = os.path.getmtime(self.comic_path)

            # Cache válido si el archivo no cambió
            is_valid = abs(current_mtime - cached_mtime) < 1.0  # Tolerancia de 1 segundo

            if is_valid:
                print(f"✅ Cache válido para: {os.path.basename(self.comic_path)}")
            else:
                print(f"❌ Cache inválido (archivo modificado): {os.path.basename(self.comic_path)}")

            return is_valid

        except Exception as e:
            print(f"Error verificando cache: {e}")
            return False

    def load_cached_pages(self, cache_dir):
        """Cargar páginas desde cache existente"""
        try:
            # Buscar archivos de imagen en el cache
            image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')
            cached_pages = []

            for filename in os.listdir(cache_dir):
                if filename.lower().endswith(image_extensions):
                    page_path = os.path.join(cache_dir, filename)
                    if os.path.exists(page_path):
                        cached_pages.append(page_path)

            # Ordenar páginas naturalmente
            cached_pages.sort(key=lambda x: self.natural_sort_key(os.path.basename(x)))

            if cached_pages:
                print(f"📚 Cargadas {len(cached_pages)} páginas desde cache")
                return cached_pages
            else:
                print("❌ No se encontraron páginas en cache")
                return None

        except Exception as e:
            print(f"Error cargando cache: {e}")
            return None

    def natural_sort_key(self, text):
        """Clave para ordenamiento natural (1, 2, 10 en lugar de 1, 10, 2)"""
        import re
        return [int(x) if x.isdigit() else x.lower() for x in re.split(r'(\d+)', text)]

    def save_cache_info(self, cache_dir):
        """Guardar información del cache para validación futura"""
        try:
            cache_info_file = os.path.join(cache_dir, ".babelcomics_cache_info")
            current_mtime = os.path.getmtime(self.comic_path)

            with open(cache_info_file, 'w') as f:
                f.write(f"{self.comic_path}\n")
                f.write(f"{current_mtime}\n")

            print(f"💾 Info de cache guardada: {cache_info_file}")

        except Exception as e:
            print(f"Error guardando info de cache: {e}")

    def cleanup_old_comic_caches(self):
        """Limpiar caches de cómics antiguos (>1 hora) de todos los directorios temporales"""
        try:
            import time
            current_time = time.time()
            max_age_hours = 1
            max_age_seconds = max_age_hours * 3600

            # Lista de directorios temporales a revisar
            temp_dirs_to_check = [
                "/tmp/claude",
                "/tmp",
                os.path.expanduser("~/tmp"),
                os.path.expanduser("~/.cache/babelcomics"),
                "/var/tmp"
            ]

            total_cleaned = 0
            total_kept = 0

            for temp_base_dir in temp_dirs_to_check:
                if not os.path.exists(temp_base_dir):
                    continue

                try:
                    print(f"🔍 Revisando: {temp_base_dir}")

                    for item in os.listdir(temp_base_dir):
                        item_path = os.path.join(temp_base_dir, item)

                        # Solo procesar directorios que son caches de cómics
                        if not os.path.isdir(item_path):
                            continue

                        # Identificar directorios de cache (tienen _ y no son aleatorios largos)
                        is_comic_cache = (
                            "_" in item and
                            not (item.startswith("babelcomics_reader_") and len(item) > 25) and
                            not item.startswith(".")  # Evitar directorios ocultos del sistema
                        )

                        if is_comic_cache:
                            try:
                                # Obtener tiempo de modificación del directorio
                                dir_mtime = os.path.getmtime(item_path)
                                age_seconds = current_time - dir_mtime
                                age_hours = age_seconds / 3600

                                if age_seconds > max_age_seconds:
                                    # Cache viejo, eliminar
                                    import shutil
                                    shutil.rmtree(item_path, ignore_errors=True)
                                    print(f"🗑️ Cache eliminado (edad: {age_hours:.1f}h): {item}")
                                    total_cleaned += 1
                                else:
                                    # Cache reciente, mantener
                                    print(f"💾 Cache mantenido (edad: {age_hours:.1f}h): {item}")
                                    total_kept += 1

                            except Exception as e:
                                print(f"⚠️ Error procesando {item}: {e}")

                except Exception as e:
                    print(f"⚠️ Error accediendo a {temp_base_dir}: {e}")

            if total_cleaned > 0 or total_kept > 0:
                print(f"📊 Limpieza completada: {total_cleaned} eliminados, {total_kept} mantenidos")

        except Exception as e:
            print(f"❌ Error en limpieza de caches: {e}")

    def touch_cache_directory(self, cache_dir):
        """Actualizar timestamp del directorio (touch) para marcar como usado recientemente"""
        try:
            import time
            current_time = time.time()

            # Actualizar tiempo de modificación del directorio
            os.utime(cache_dir, (current_time, current_time))

            print(f"👆 Timestamp actualizado: {os.path.basename(cache_dir)}")

        except Exception as e:
            print(f"⚠️ Error actualizando timestamp: {e}")

    def get_interpolation_type(self):
        """Obtener tipo de interpolación según configuración"""
        if self.interpolation_mode == "nearest":
            return GdkPixbuf.InterpType.NEAREST
        elif self.interpolation_mode == "bilinear":
            return GdkPixbuf.InterpType.BILINEAR
        elif self.interpolation_mode == "hyper":
            return GdkPixbuf.InterpType.HYPER
        else:
            # Fallback por defecto para cómics
            return GdkPixbuf.InterpType.NEAREST

    def set_interpolation_mode(self, mode):
        """Cambiar modo de interpolación de imagen"""
        old_mode = self.interpolation_mode
        self.interpolation_mode = mode

        print(f"🎨 Interpolación cambiada: {old_mode} → {mode}")

        # Verificar si necesitamos escalar para ver la diferencia
        if self.original_pixbuf:
            orig_width = self.original_pixbuf.get_width()
            orig_height = self.original_pixbuf.get_height()

            widget_width = self.scrolled_window.get_allocated_width()
            widget_height = self.scrolled_window.get_allocated_height()

            print(f"🖼️ DEBUG - Imagen original: {orig_width}x{orig_height}")
            print(f"🖼️ DEBUG - Área ventana: {widget_width}x{widget_height}")
            print(f"🖼️ DEBUG - Modo ajuste: {self.fit_mode}")
            print(f"🖼️ DEBUG - Zoom actual: {self.zoom_level}")

            # Verificar si se está escalando
            if widget_width > 1 and widget_height > 1:
                new_width, new_height = self.calculate_size_for_mode(
                    orig_width, orig_height, widget_width, widget_height
                )
                new_width = int(new_width * self.zoom_level)
                new_height = int(new_height * self.zoom_level)

                is_scaling = (new_width != orig_width or new_height != orig_height)
                scale_factor = new_width / orig_width if orig_width > 0 else 1.0

                print(f"🖼️ DEBUG - Tamaño final: {new_width}x{new_height}")
                print(f"🖼️ DEBUG - ¿Se está escalando?: {is_scaling}")
                print(f"🖼️ DEBUG - Factor escala: {scale_factor:.2f}")

                if not is_scaling:
                    self.show_toast("⚠️ Sin escalado - no se verá diferencia", "info")
                    print("⚠️ La imagen NO se está escalando, la interpolación no tendrá efecto visible")
                elif abs(scale_factor - 1.0) < 0.1:
                    self.show_toast("⚠️ Escalado mínimo - diferencia sutil", "info")
                    print(f"⚠️ Escalado muy pequeño ({scale_factor:.2f}x), diferencia puede ser sutil")
                else:
                    print(f"✅ Escalado significativo ({scale_factor:.2f}x), diferencia debería ser visible")

        # Aplicar inmediatamente si tenemos una imagen cargada
        if self.current_page_path and self.original_pixbuf:
            self.apply_current_view_settings()
        elif self.current_page_path:
            # Fallback si no tenemos original_pixbuf aún
            self.configure_image_size()

        # Mensajes descriptivos
        mode_names = {
            "nearest": "Nítido",
            "bilinear": "Suavizado",
            "hyper": "Alta calidad"
        }
        mode_name = mode_names.get(mode, mode)
        self.show_toast(f"Calidad: {mode_name}", "info")

    def update_zoom_indicator(self):
        """Actualizar el indicador de zoom en la UI"""
        try:
            if hasattr(self, 'zoom_indicator_button'):
                zoom_percent = int(self.zoom_level * 100)
                self.zoom_indicator_button.set_label(f"{zoom_percent}%")
                print(f"🔄 Indicador UI actualizado: {zoom_percent}%")
        except Exception as e:
            print(f"Error actualizando indicador de zoom: {e}")

    def reset_scroll_position(self):
        """Resetear posición de scroll al inicio de la página"""
        try:
            # Obtener los adjustments del ScrolledWindow
            h_adjustment = self.scrolled_window.get_hadjustment()
            v_adjustment = self.scrolled_window.get_vadjustment()

            if h_adjustment and v_adjustment:
                # Obtener valores actuales para debug
                old_h = h_adjustment.get_value()
                old_v = v_adjustment.get_value()

                # Ir al inicio (0, 0)
                h_adjustment.set_value(0)
                v_adjustment.set_value(0)

                print(f"📜 Scroll reseteado: ({old_h:.0f}, {old_v:.0f}) → (0, 0)")
            else:
                print(f"⚠️ No se pudieron obtener adjustments del scroll")
                # Fallback: intentar con scroll_to si está disponible
                try:
                    # Algunas versiones de GTK tienen métodos alternativos
                    self.scrolled_window.emit("scroll-child", Gtk.ScrollType.START, False)
                    print(f"📜 Scroll reseteado usando scroll-child")
                except:
                    print(f"❌ No se pudo resetear scroll con ningún método")

        except Exception as e:
            print(f"Error reseteando scroll: {e}")

        return False  # No repetir el idle_add

    def show_toast(self, message, toast_type="info"):
        """Mostrar notificación toast"""
        toast = Adw.Toast()
        toast.set_title(message)
        toast.set_timeout(2)
        self.toast_overlay.add_toast(toast)


def open_comic_with_reader(comic_path, comic_title="Comic", parent_window=None,
                          scroll_threshold=None, scroll_cooldown=None):
    """Función helper para abrir comic con el lector"""
    if not os.path.exists(comic_path):
        print(f"Archivo no existe: {comic_path}")
        return None

    try:
        reader = ComicReader(comic_path, comic_title, parent_window,
                           scroll_threshold, scroll_cooldown)
        reader.present()
        return reader
    except Exception as e:
        print(f"Error abriendo lector: {e}")
        return None


if __name__ == "__main__":
    # Prueba independiente
    app = Adw.Application(application_id="test.comic.reader")

    def on_activate(app):
        import sys
        if len(sys.argv) > 1:
            comic_path = sys.argv[1]
            open_comic_with_reader(comic_path, os.path.basename(comic_path))
        else:
            print("Uso: python comic_reader.py <ruta_del_comic>")

    app.connect("activate", on_activate)
    app.run()