#!/usr/bin/env python3
"""
Ventana para buscar y descargar volúmenes desde ComicVine
"""

import gi
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib, GdkPixbuf, Gdk, Pango, GObject

from helpers.comicvine_cliente import ComicVineClient
from helpers.image_downloader import download_image
from repositories.volume_repository import VolumeRepository


class VolumeSearchCard(Gtk.Box):
    """Card para mostrar un volumen en los resultados de búsqueda"""

    def __init__(self, volume_data, is_downloaded=False, is_grouped=False):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.volume_data = volume_data
        self.is_downloaded = is_downloaded
        self.selected = False

        self.is_grouped = is_grouped

        if not self.is_grouped:
            self.set_size_request(200, 320)
            self.add_css_class("card")
            self.set_margin_top(8)
            self.set_margin_bottom(8)
            self.set_margin_start(8)
            self.set_margin_end(8)
        else:
            self.set_size_request(200, 320)
            self.set_margin_top(4)
            self.set_margin_bottom(4)
            self.set_margin_start(4)
            self.set_margin_end(4)

        self.create_ui()

    def create_ui(self):
        """Crear la interfaz del card"""

        # Cover del volumen
        self.cover_image = Gtk.Picture()
        self.cover_image.set_size_request(150, 200)
        self.cover_image.set_can_shrink(True)
        self.cover_image.set_keep_aspect_ratio(True)
        self.cover_image.set_content_fit(Gtk.ContentFit.CONTAIN)

        # Cargar cover si está disponible
        self.load_cover()

        self.append(self.cover_image)

        # Información del volumen
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)

        # Título
        title_label = Gtk.Label(label=self.volume_data.get('name', 'Sin título'))
        title_label.set_wrap(True)
        title_label.set_lines(2)
        title_label.set_ellipsize(Pango.EllipsizeMode.END)
        title_label.add_css_class("title-4")
        title_label.set_halign(Gtk.Align.START)
        info_box.append(title_label)

        # Editorial y año
        publisher_name = "Desconocida"
        if self.volume_data.get('publisher'):
            publisher_name = self.volume_data['publisher'].get('name', 'Desconocida')

        start_year = self.volume_data.get('start_year', 'N/A')
        subtitle = f"{publisher_name} ({start_year})"

        subtitle_label = Gtk.Label(label=subtitle)
        subtitle_label.set_wrap(True)
        subtitle_label.add_css_class("caption")
        subtitle_label.set_halign(Gtk.Align.START)
        info_box.append(subtitle_label)

        # Cantidad de issues
        issue_count = self.volume_data.get('count_of_issues', 0)
        issues_label = Gtk.Label(label=f"{issue_count} issues")
        issues_label.add_css_class("caption")
        issues_label.set_halign(Gtk.Align.START)
        info_box.append(issues_label)

        # Estado y checkbox
        controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        controls_box.set_margin_top(8)

        # Checkbox para selección
        self.checkbox = Gtk.CheckButton()
        self.checkbox.connect("toggled", self.on_checkbox_toggled)
        controls_box.append(self.checkbox)

        # Estado
        if self.is_downloaded:
            status_label = Gtk.Label(label="Descargado")
            status_label.add_css_class("success")
        else:
            status_label = Gtk.Label(label="Nuevo")
            status_label.add_css_class("accent")

        status_label.add_css_class("caption")
        controls_box.append(status_label)

        info_box.append(controls_box)
        self.append(info_box)

    def load_cover(self):
        """Cargar cover del volumen"""
        try:
            if self.volume_data.get('image') and self.volume_data['image'].get('medium_url'):
                # Crear placeholder mientras carga
                self.set_placeholder_cover()
                # Cargar imagen en background
                image_url = self.volume_data['image']['medium_url']
                threading.Thread(
                    target=self.download_cover_background,
                    args=(image_url,),
                    daemon=True
                ).start()
            else:
                self.set_placeholder_cover()
        except Exception as e:
            print(f"Error cargando cover: {e}")
            self.set_placeholder_cover()

    def download_cover_background(self, image_url):
        """Descargar cover en background thread"""
        try:
            import requests
            from io import BytesIO

            # Headers completos de Chrome para evitar bloqueos 403 Forbidden
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,es;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://comicvine.gamespot.com/',
                'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Linux"',
                'sec-fetch-dest': 'image',
                'sec-fetch-mode': 'no-cors',
                'sec-fetch-site': 'same-origin',
                'DNT': '1',
                'Connection': 'keep-alive',
            }

            # Descargar imagen con headers correctos
            response = requests.get(image_url, headers=headers, timeout=30)
            response.raise_for_status()

            # Crear pixbuf desde bytes
            loader = GdkPixbuf.PixbufLoader()
            loader.write(response.content)
            loader.close()
            pixbuf = loader.get_pixbuf()

            if pixbuf:
                # Redimensionar si es necesario
                width = pixbuf.get_width()
                height = pixbuf.get_height()

                # Mantener aspect ratio, max 130x180
                if width > 130 or height > 180:
                    if width > height:
                        new_width = 130
                        new_height = int((height * 130) / width)
                    else:
                        new_height = 180
                        new_width = int((width * 180) / height)

                    pixbuf = pixbuf.scale_simple(new_width, new_height, GdkPixbuf.InterpType.BILINEAR)

                # Actualizar UI en main thread
                GLib.idle_add(self.set_cover_from_pixbuf, pixbuf)
            else:
                pass

        except Exception as e:
            print(f"Error descargando cover {image_url}: {e}")
            # Mantener placeholder en caso de error

    def set_cover_from_pixbuf(self, pixbuf):
        """Configurar cover desde pixbuf en main thread"""
        try:
            texture = Gdk.Texture.new_for_pixbuf(pixbuf)
            self.cover_image.set_paintable(texture)
        except Exception as e:
            print(f"Error configurando cover: {e}")

    def set_placeholder_cover(self):
        """Configurar placeholder para el cover"""
        try:
            # Crear un placeholder más atractivo
            pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 130, 180)
            pixbuf.fill(0x3584E4FF)  # Azul como en otros placeholders

            # Crear textura
            texture = Gdk.Texture.new_for_pixbuf(pixbuf)
            self.cover_image.set_paintable(texture)
        except Exception as e:
            print(f"Error creando placeholder: {e}")

    def on_checkbox_toggled(self, checkbox):
        """Checkbox cambiado"""
        self.selected = checkbox.get_active()
        self.emit('selection-changed', self.selected)

    def set_selected(self, selected):
        """Programáticamente seleccionar/deseleccionar"""
        self.checkbox.set_active(selected)


# Registrar señal personalizada
GObject.signal_new('selection-changed', VolumeSearchCard, GObject.SignalFlags.RUN_FIRST, None, (bool,))

class VolumeGroupCard(Gtk.Box):
    """Card que agrupa múltiples variantes del mismo volumen en un Adw.Carousel"""

    def __init__(self, volumes_data, downloaded_cv_ids):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.volumes_data = volumes_data
        self.cards = []

        self.set_size_request(200, 320)
        self.add_css_class("card")
        self.set_margin_top(8)
        self.set_margin_bottom(8)
        self.set_margin_start(8)
        self.set_margin_end(8)

        self.create_ui(downloaded_cv_ids)

    def create_ui(self, downloaded_cv_ids):
        """Crear el carousel y agregar las cards"""
        # Contenedor para el carousel con indicadores
        carousel_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        
        # Ocultar botones de navegación si solo hay uno
        interactive = len(self.volumes_data) > 1

        self.carousel = Adw.Carousel()
        self.carousel.set_allow_scroll_wheel(interactive)
        self.carousel.set_allow_mouse_drag(interactive)
        self.carousel.set_allow_long_swipes(interactive)
        self.carousel.set_interactive(interactive)

        for volume in self.volumes_data:
            is_downloaded = volume.get('id') in downloaded_cv_ids
            card = VolumeSearchCard(volume, is_downloaded, is_grouped=True)
            card.connect('selection-changed', self.on_card_selection_changed)
            self.cards.append(card)
            self.carousel.append(card)

        carousel_box.append(self.carousel)

        if interactive:
            indicators = Adw.CarouselIndicatorDots()
            indicators.set_carousel(self.carousel)
            indicators.set_margin_bottom(4)
            carousel_box.append(indicators)
            
            # Controles overlay para prev/next opcionales
            # (No estrictamente requeridos ya que el mouse drag/scroll funciona en el carousel)

        self.append(carousel_box)

    def on_card_selection_changed(self, card, selected):
        """Re-emitir evento cuando uno de los cards internos cambia"""
        self.emit('selection-changed', selected)
        
    def get_selected_volumes(self):
        """Obtener la lista de volumenes internos seleccionados"""
        return [card.volume_data for card in self.cards if card.selected]
        
    def get_selected_new_volumes(self):
        """Obtener la lista de volumenes internos seleccionados y no descargados"""
        return [card.volume_data for card in self.cards if card.selected and not card.is_downloaded]
        
    def select_all_new(self):
        """Seleccionar todos los items internos no descargados"""
        for card in self.cards:
            if not card.is_downloaded:
                card.set_selected(True)
                
    def deselect_all(self):
        """Deseleccionar todos los items internos"""
        for card in self.cards:
            card.set_selected(False)
            
    def has_any_selected(self):
        """Retorna True si al menos un item interno esta seleccionado"""
        return any(card.selected for card in self.cards)
        
    def get_internal_cards(self):
        return self.cards

GObject.signal_new('selection-changed', VolumeGroupCard, GObject.SignalFlags.RUN_FIRST, None, (bool,))

class PublisherSearchCard(Gtk.Box):
    """Card para mostrar una editorial en los resultados de búsqueda"""

    def __init__(self, publisher_data, is_downloaded=False):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.publisher_data = publisher_data
        self.is_downloaded = is_downloaded
        self.selected = False

        self.set_size_request(200, 280)
        self.add_css_class("card")
        self.set_margin_top(8)
        self.set_margin_bottom(8)
        self.set_margin_start(8)
        self.set_margin_end(8)

        self.create_ui()

    def create_ui(self):
        """Crear la interfaz del card"""

        # Logo de la editorial
        self.logo_image = Gtk.Picture()
        self.logo_image.set_size_request(150, 150)
        self.logo_image.set_can_shrink(True)
        self.logo_image.set_keep_aspect_ratio(True)
        self.logo_image.set_content_fit(Gtk.ContentFit.CONTAIN)

        # Cargar logo si está disponible
        self.load_logo()

        self.append(self.logo_image)

        # Información de la editorial
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)

        # Nombre
        title_label = Gtk.Label(label=self.publisher_data.get('name', 'Sin nombre'))
        title_label.set_wrap(True)
        title_label.set_lines(2)
        title_label.set_ellipsize(Pango.EllipsizeMode.END)
        title_label.add_css_class("title-4")
        title_label.set_halign(Gtk.Align.START)
        info_box.append(title_label)

        # Información adicional
        aliases = self.publisher_data.get('aliases')
        if aliases:
            aliases_text = aliases if isinstance(aliases, str) else aliases[0] if isinstance(aliases, list) and aliases else ""
            if aliases_text:
                aliases_label = Gtk.Label(label=f"aka: {aliases_text}")
                aliases_label.set_wrap(True)
                aliases_label.set_lines(1)
                aliases_label.set_ellipsize(Pango.EllipsizeMode.END)
                aliases_label.add_css_class("caption")
                aliases_label.set_halign(Gtk.Align.START)
                info_box.append(aliases_label)

        # Controles
        controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        controls_box.set_margin_top(8)

        # Checkbox para selección
        self.checkbox = Gtk.CheckButton()
        self.checkbox.connect("toggled", self.on_checkbox_toggled)
        controls_box.append(self.checkbox)

        # Estado
        if self.is_downloaded:
            status_label = Gtk.Label(label="Descargada")
            status_label.add_css_class("success")
        else:
            status_label = Gtk.Label(label="No descargada")
            status_label.add_css_class("dim-label")

        controls_box.append(status_label)
        info_box.append(controls_box)

        self.append(info_box)

    def load_logo(self):
        """Cargar logo de la editorial"""
        image_data = self.publisher_data.get('image')
        if image_data and image_data.get('small_url'):
            image_url = image_data['small_url']
            self.download_logo_background(image_url)
        else:
            self.show_placeholder()

    def download_logo_background(self, image_url):
        """Descargar logo en hilo de fondo"""
        def worker():
            try:
                from helpers.image_downloader import download_image
                image_path = download_image(image_url, temp=True)

                if image_path and os.path.exists(image_path):
                    GLib.idle_add(lambda: self.set_logo_from_file(image_path))
                else:
                    GLib.idle_add(self.show_placeholder)
            except Exception as e:
                print(f"Error descargando logo: {e}")
                GLib.idle_add(self.show_placeholder)

        threading.Thread(target=worker, daemon=True).start()

    def set_logo_from_file(self, image_path):
        """Establecer logo desde archivo"""
        try:
            self.logo_image.set_filename(image_path)
        except Exception as e:
            print(f"Error cargando imagen: {e}")
            self.show_placeholder()

    def show_placeholder(self):
        """Mostrar placeholder cuando no hay logo"""
        try:
            pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 150, 150)
            pixbuf.fill(0x9A9996FF)  # Gris

            texture = Gdk.Texture.new_for_pixbuf(pixbuf)
            self.logo_image.set_paintable(texture)
        except Exception as e:
            print(f"Error creando placeholder: {e}")

    def on_checkbox_toggled(self, checkbox):
        """Checkbox cambiado"""
        self.selected = checkbox.get_active()
        self.emit('selection-changed', self.selected)

    def set_selected(self, selected):
        """Programáticamente seleccionar/deseleccionar"""
        self.checkbox.set_active(selected)


# Registrar señal personalizada para PublisherSearchCard
GObject.signal_new('selection-changed', PublisherSearchCard, GObject.SignalFlags.RUN_FIRST, None, (bool,))


class ComicVineDownloadWindow(Adw.Window):
    """Ventana para buscar y descargar volúmenes y editoriales desde ComicVine"""
    def __init__(self, parent_window, session, selected_volume_callback=None):
        super().__init__()
        self.parent_window = parent_window
        self.session = session
        self.selected_volume_callback = selected_volume_callback  # Callback para auto-seleccionar volumen

        self.comicvine_client = None
        self.search_results = []
        self.filtered_results = []  # Resultados después de aplicar filtros y ordenamiento
        self.volume_cards = []

        self.set_title("Descargar Volúmenes de ComicVine")
        self.set_default_size(800, 600)
        self.set_modal(True)
        self.set_transient_for(parent_window)

        self.setup_ui()
        self.init_comicvine_client()
        self.setup_keyboard_shortcuts()

    def _safe_int(self, value, default=0):
        """Convierte un valor a entero de forma segura"""
        if value is None:
            return default
        try:
            if isinstance(value, str):
                # Remover espacios y caracteres no numéricos comunes
                value = value.strip()
                if not value:
                    return default
            return int(value)
        except (ValueError, TypeError):
            return default

    def load_publishers_from_results(self):
        """Cargar editoriales encontradas en los resultados de búsqueda"""

        # Guardar referencia a los resultados para evitar que se pierdan
        if hasattr(self, 'publisher_combo'):
            # Desconectar temporalmente el callback para evitar filtrado prematuro
            try:
                self.publisher_combo.disconnect_by_func(self.on_publisher_filter_changed)
            except:
                pass  # Si no estaba conectado, continuar

        # Limpiar combobox actual (excepto "Todas las editoriales")
        self.publisher_combo.remove_all()
        self.publisher_combo.append("", "Todas las editoriales")

        if not self.search_results:
            self.publisher_combo.set_active(0)
            # Reconectar callback incluso en caso de error
            self.publisher_combo.connect("changed", self.on_publisher_filter_changed)
            return

        # Recopilar editoriales únicas de los resultados
        publishers_found = {}

        for volume in self.search_results:
            publisher = volume.get('publisher')
            if publisher and publisher.get('name'):
                publisher_name = publisher['name']
                publisher_id = str(publisher.get('id', publisher_name))
                if publisher_name not in publishers_found:
                    publishers_found[publisher_name] = publisher_id

        # Agregar editoriales al combobox ordenadas alfabéticamente
        for publisher_name in sorted(publishers_found.keys()):
            publisher_id = publishers_found[publisher_name]
            self.publisher_combo.append(publisher_id, publisher_name)

        self.publisher_combo.set_active(0)  # Seleccionar "Todas las editoriales"

        # Conectar/reconectar TODOS los callbacks de filtros
        self.publisher_combo.connect("changed", self.on_publisher_filter_changed)

        # Conectar callbacks de año si no están conectados
        try:
            print("Conectando callbacks de filtros...")
            self.year_from_spin.connect("value-changed", self.on_year_filter_changed)
            self.year_to_spin.connect("value-changed", self.on_year_filter_changed)
            self.issues_from_spin.connect("value-changed", self.on_issues_filter_changed)
            self.issues_to_spin.connect("value-changed", self.on_issues_filter_changed)
            self.downloaded_combo.connect("changed", self.on_downloaded_filter_changed)
            self.sort_combo.connect("changed", self.on_sort_changed)
        except:
            pass

    def setup_ui(self):
        """Configurar la interfaz de usuario"""

        # HeaderBar con botón cerrar
        header_bar = Adw.HeaderBar()
        header_bar.set_title_widget(Gtk.Label(label="Descargar Volúmenes de ComicVine"))

        # Botones de acción en el header (lado izquierdo)
        actions_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        # Seleccionar todos
        select_all_button = Gtk.Button.new_with_label("Seleccionar Todos")
        select_all_button.set_tooltip_text("Seleccionar todos los volúmenes no descargados")
        select_all_button.connect("clicked", self.on_select_all_clicked)
        actions_box.append(select_all_button)

        # Deseleccionar todos
        deselect_all_button = Gtk.Button.new_with_label("Deseleccionar")
        deselect_all_button.set_tooltip_text("Deseleccionar todos los volúmenes")
        deselect_all_button.connect("clicked", self.on_deselect_all_clicked)
        actions_box.append(deselect_all_button)

        # Botón de descarga
        self.download_button = Gtk.Button.new_with_label("Descargar Seleccionados")
        self.download_button.add_css_class("suggested-action")
        self.download_button.set_sensitive(False)
        self.download_button.set_tooltip_text("Descargar volúmenes seleccionados")
        self.download_button.connect("clicked", self.on_download_clicked)
        actions_box.append(self.download_button)

        header_bar.pack_start(actions_box)

        # Botón cerrar explícito
        close_button = Gtk.Button()
        close_button.set_icon_name("window-close-symbolic")
        close_button.set_tooltip_text("Cerrar ventana")
        close_button.connect("clicked", lambda btn: self.close())
        header_bar.pack_end(close_button)

        # Contenedor principal
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        main_box.append(header_bar)

        # Fila superior fija (Búsqueda)
        search_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        search_box.set_margin_start(12)
        search_box.set_margin_end(12)
        search_box.set_margin_top(12)
        search_box.set_margin_bottom(0)
        # Header con búsqueda (compacto y fijo)
        self.create_search_header(search_box)
        main_box.append(search_box)

        # Contenedor scrollable SÓLO para el área de resultados
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_vexpand(True)

        results_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        results_box.set_margin_start(12)
        results_box.set_margin_end(12)
        results_box.set_margin_top(12)
        results_box.set_margin_bottom(12)
        # Área de resultados (scrollable)
        self.create_results_area(results_box)
        scrolled_window.set_child(results_box)
        main_box.append(scrolled_window)

        # Fila inferior fija (Footer)
        footer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        footer_box.set_margin_start(12)
        footer_box.set_margin_end(12)
        footer_box.set_margin_top(0)
        footer_box.set_margin_bottom(12)
        # Footer con controles de descarga (compacto y fijo)
        self.create_download_footer(footer_box)
        main_box.append(footer_box)

        self.set_content(main_box)

    def create_search_header(self, parent):
        """Crear header con controles de búsqueda"""

        # Contenedor compacto de búsqueda
        search_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)

        # Título
        title_label = Gtk.Label(label="Buscar Volúmenes")
        title_label.add_css_class("title-2")
        title_label.set_halign(Gtk.Align.START)
        search_box.append(title_label)

        # Primera fila: Búsqueda principal
        main_search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        # Entry de búsqueda
        self.search_entry = Gtk.Entry()
        self.search_entry.set_placeholder_text("Nombre del volumen (ej: Batman, Spider-Man...)")
        self.search_entry.set_hexpand(True)
        self.search_entry.connect("activate", self.on_search_clicked)
        main_search_box.append(self.search_entry)


        # Botón buscar
        self.search_button = Gtk.Button.new_with_label("Buscar")
        self.search_button.add_css_class("suggested-action")
        self.search_button.connect("clicked", self.on_search_clicked)
        main_search_box.append(self.search_button)

        # Spinner
        self.search_spinner = Gtk.Spinner()
        main_search_box.append(self.search_spinner)

        search_box.append(main_search_box)

        # Segunda fila: Filtros y ordenamiento
        filters_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        filters_box.set_halign(Gtk.Align.CENTER)

        # Filtros por fecha
        date_filter_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        date_label = Gtk.Label(label="Año:")
        date_filter_box.append(date_label)

        # Año desde
        self.year_from_spin = Gtk.SpinButton()
        self.year_from_spin.set_range(1900, 2030)   
        self.year_from_spin.set_value(1950)  # Valor más restrictivo por defecto
        self.year_from_spin.set_tooltip_text("Año desde")
        # NO conectar callback aún - se conectará después de la primera búsqueda
        date_filter_box.append(self.year_from_spin)

        dash_label = Gtk.Label(label="—")
        date_filter_box.append(dash_label)

        # Año hasta
        self.year_to_spin = Gtk.SpinButton()
        self.year_to_spin.set_range(1900, 2030)
        self.year_to_spin.set_value(2025)  # Valor más restrictivo por defecto
        self.year_to_spin.set_tooltip_text("Año hasta")
        # NO conectar callback aún - se conectará después de la primera búsqueda
        date_filter_box.append(self.year_to_spin)

        filters_box.append(date_filter_box)

        # Separador visual
        separator1 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        filters_box.append(separator1)

        # Filtro por editorial
        publisher_filter_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        publisher_label = Gtk.Label(label="Editorial:")
        publisher_filter_box.append(publisher_label)

        # ComboBox de editorial (se populará con resultados de búsqueda)
        self.publisher_combo = Gtk.ComboBoxText()
        self.publisher_combo.append("", "Todas las editoriales")
        self.publisher_combo.set_active(0)
        self.publisher_combo.set_size_request(150, -1)
        # NO conectar callback aún - se conectará después de la primera búsqueda
        publisher_filter_box.append(self.publisher_combo)

        filters_box.append(publisher_filter_box)

        # Separador visual
        separator1_5 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        filters_box.append(separator1_5)

        # Filtros por cantidad de comics
        issues_filter_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        issues_label = Gtk.Label(label="Números:")
        issues_filter_box.append(issues_label)

        # Cantidad desde
        self.issues_from_spin = Gtk.SpinButton()
        self.issues_from_spin.set_range(1, 10000)
        self.issues_from_spin.set_value(1)
        self.issues_from_spin.set_tooltip_text("Mínimo de números")
        issues_filter_box.append(self.issues_from_spin)

        dash_label_issues = Gtk.Label(label="—")
        issues_filter_box.append(dash_label_issues)

        # Cantidad hasta
        self.issues_to_spin = Gtk.SpinButton()
        self.issues_to_spin.set_range(1, 10000)
        self.issues_to_spin.set_value(5000)
        self.issues_to_spin.set_tooltip_text("Máximo de números")
        issues_filter_box.append(self.issues_to_spin)

        filters_box.append(issues_filter_box)

        # Separador visual
        separator1_6 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        filters_box.append(separator1_6)

        # Filtro por estado de descarga
        downloaded_filter_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        downloaded_label = Gtk.Label(label="Estado:")
        downloaded_filter_box.append(downloaded_label)

        self.downloaded_combo = Gtk.ComboBoxText()
        self.downloaded_combo.append("todos", "Todos")
        self.downloaded_combo.append("descargados", "Descargados")
        self.downloaded_combo.append("no_descargados", "No descargados")
        self.downloaded_combo.set_active(0)
        downloaded_filter_box.append(self.downloaded_combo)

        filters_box.append(downloaded_filter_box)

        # Separador visual
        separator1_7 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        filters_box.append(separator1_7)

        # Ordenamiento
        sort_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        sort_icon = Gtk.Image.new_from_icon_name("view-sort-descending-symbolic")
        sort_icon.set_tooltip_text("Ordenar resultados")
        sort_box.append(sort_icon)

        self.sort_combo = Gtk.ComboBoxText()
        self.sort_combo.append("date_desc", "Fecha (más reciente)")
        self.sort_combo.append("date_asc", "Fecha (más antiguo)")
        self.sort_combo.append("name_asc", "Nombre (A-Z)")
        self.sort_combo.append("name_desc", "Nombre (Z-A)")
        self.sort_combo.append("count_desc", "Más números")
        self.sort_combo.append("count_asc", "Menos números")
        self.sort_combo.append("publisher_asc", "Editorial (A-Z)")
        self.sort_combo.set_active(0)  # Por defecto: fecha más reciente
        # NO conectar callback aún - se conectará después de la primera búsqueda
        sort_box.append(self.sort_combo)

        filters_box.append(sort_box)

        # Separador visual
        separator2 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        filters_box.append(separator2)

        # Botón para resetear filtros y label informativo
        reset_and_info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)

        # Botón resetear filtros
        reset_filters_button = Gtk.Button()
        reset_filters_button.set_icon_name("edit-clear-all-symbolic")
        reset_filters_button.set_tooltip_text("Limpiar todos los filtros")
        reset_filters_button.connect("clicked", self.on_reset_filters_clicked)
        # Hacer que el botón no ocupe todo el ancho
        reset_filters_button.set_halign(Gtk.Align.CENTER)
        reset_and_info_box.append(reset_filters_button)

        # Label informativo de filtros (automáticos)
        self.filter_info_label = Gtk.Label(label="Filtros automáticos")
        self.filter_info_label.add_css_class("caption")
        self.filter_info_label.add_css_class("dim-label")
        reset_and_info_box.append(self.filter_info_label)

        filters_box.append(reset_and_info_box)

        search_box.append(filters_box)
        parent.append(search_box)

    def create_results_area(self, parent):
        """Crear área de resultados"""

        # Contenedor de resultados
        results_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        # Label de resultados
        self.results_label = Gtk.Label(label="Busca volúmenes para ver resultados")
        self.results_label.add_css_class("dim-label")
        self.results_label.set_halign(Gtk.Align.START)
        results_container.append(self.results_label)

        # FlowBox para mostrar cards en grid 3x con filas dinámicas
        self.results_flowbox = Gtk.FlowBox()
        self.results_flowbox.set_valign(Gtk.Align.START)
        self.results_flowbox.set_max_children_per_line(3)
        self.results_flowbox.set_min_children_per_line(1)  # Permitir adaptarse a pantallas pequeñas
        self.results_flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.results_flowbox.set_homogeneous(True)
        self.results_flowbox.set_column_spacing(15)
        self.results_flowbox.set_row_spacing(15)
        # Agregar márgenes para la cuadrícula
        self.results_flowbox.set_margin_start(12)
        self.results_flowbox.set_margin_end(12)

        results_container.append(self.results_flowbox)
        parent.append(results_container)

    def create_download_footer(self, parent):
        """Crear footer con controles de descarga"""

        # Contenedor de footer compacto
        footer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        # Opciones
        options_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        options_box.set_halign(Gtk.Align.CENTER)

        # Opción de covers
        covers_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        covers_label = Gtk.Label(label="Incluir covers:")
        covers_box.append(covers_label)
        self.download_covers_switch = Gtk.Switch()
        self.download_covers_switch.set_active(True)
        covers_box.append(self.download_covers_switch)
        options_box.append(covers_box)

        # Opción de actualizar existentes
        update_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        update_label = Gtk.Label(label="Actualizar existentes:")
        update_label.set_tooltip_text("Sobreescribir información de volúmenes ya descargados")
        update_box.append(update_label)
        self.update_existing_switch = Gtk.Switch()
        self.update_existing_switch.set_active(True)
        self.update_existing_switch.set_tooltip_text("Actualizar cantidad de números, descripción y demás información de volúmenes existentes")
        update_box.append(self.update_existing_switch)
        options_box.append(update_box)

        footer_box.append(options_box)

        # Los botones de acción ahora están en el header

        # Progress bar
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_visible(False)
        footer_box.append(self.progress_bar)

        parent.append(footer_box)

    def setup_keyboard_shortcuts(self):
        """Configurar atajos de teclado"""
        # Escape para cerrar
        escape_shortcut = Gtk.Shortcut()
        escape_shortcut.set_trigger(Gtk.ShortcutTrigger.parse_string("Escape"))
        escape_shortcut.set_action(Gtk.CallbackAction.new(self.on_escape_shortcut))

        # Ctrl+A para seleccionar todos
        select_all_shortcut = Gtk.Shortcut()
        select_all_shortcut.set_trigger(Gtk.ShortcutTrigger.parse_string("<Control>a"))
        select_all_shortcut.set_action(Gtk.CallbackAction.new(self.on_select_all_shortcut))

        # Shift+Ctrl+A para deseleccionar todos
        deselect_all_shortcut = Gtk.Shortcut()
        deselect_all_shortcut.set_trigger(Gtk.ShortcutTrigger.parse_string("<Shift><Control>a"))
        deselect_all_shortcut.set_action(Gtk.CallbackAction.new(self.on_deselect_all_shortcut))

        # Ctrl+Enter para descargar
        download_shortcut = Gtk.Shortcut()
        download_shortcut.set_trigger(Gtk.ShortcutTrigger.parse_string("<Control>Return"))
        download_shortcut.set_action(Gtk.CallbackAction.new(self.on_download_shortcut))

        # Ctrl+F para enfocar búsqueda
        focus_search_shortcut = Gtk.Shortcut()
        focus_search_shortcut.set_trigger(Gtk.ShortcutTrigger.parse_string("<Control>f"))
        focus_search_shortcut.set_action(Gtk.CallbackAction.new(self.on_focus_search_shortcut))

        # Enter para buscar (cuando campo está enfocado)
        search_shortcut = Gtk.Shortcut()
        search_shortcut.set_trigger(Gtk.ShortcutTrigger.parse_string("Return"))
        search_shortcut.set_action(Gtk.CallbackAction.new(self.on_search_shortcut))

        controller = Gtk.ShortcutController()
        controller.add_shortcut(escape_shortcut)
        controller.add_shortcut(select_all_shortcut)
        controller.add_shortcut(deselect_all_shortcut)
        controller.add_shortcut(download_shortcut)
        controller.add_shortcut(focus_search_shortcut)
        controller.add_shortcut(search_shortcut)

        self.add_controller(controller)

    def on_escape_shortcut(self, widget, args):
        """Cerrar con Escape"""
        self.close()
        return True

    def on_select_all_shortcut(self, widget, args):
        """Seleccionar todos con Ctrl+A"""
        if hasattr(self, 'select_all_button'):
            self.select_all_button.emit('clicked')
        return True

    def on_deselect_all_shortcut(self, widget, args):
        """Deseleccionar todos con Ctrl+Shift+A"""
        if hasattr(self, 'deselect_all_button'):
            self.deselect_all_button.emit('clicked')
        return True

    def on_download_shortcut(self, widget, args):
        """Descargar con Ctrl+Enter"""
        if hasattr(self, 'download_button'):
            self.download_button.emit('clicked')
        return True

    def on_focus_search_shortcut(self, widget, args):
        """Enfocar búsqueda con Ctrl+F"""
        if hasattr(self, 'search_entry'):
            self.search_entry.grab_focus()
        return True

    def on_search_shortcut(self, widget, args):
        """Buscar con Enter (solo si el campo de búsqueda está enfocado)"""
        if hasattr(self, 'search_entry') and self.search_entry.has_focus():
            if hasattr(self, 'search_button'):
                self.search_button.emit('clicked')
            return True
        return False

    def init_comicvine_client(self):
        """Inicializar cliente de ComicVine"""
        try:
            # TODO: Obtener API key de configuración
            api_key = "7e4368b71c5a66d710a62e996a660024f6a868d4"
            self.comicvine_client = ComicVineClient(api_key)
        except Exception as e:
            print(f"Error inicializando ComicVine client: {e}")
            self.show_error("Error de configuración", "No se pudo conectar con ComicVine. Verifica la configuración.")

    def on_search_clicked(self, widget):
        """Buscar volúmenes"""
        query = self.search_entry.get_text().strip()
        publisher_id = self.publisher_combo.get_active_id()

        if not query:
            self.show_error("Error de búsqueda", "Ingresa un nombre de volumen para buscar")
            return

        # Deshabilitar búsqueda y mostrar spinner
        self.search_button.set_sensitive(False)
        self.search_spinner.start()
        self.results_label.set_text("Buscando...")

        # Limpiar resultados anteriores
        self.clear_all_results()

        # Buscar en background
        threading.Thread(
            target=self.search_volumes_background,
            args=(query, publisher_id),
            daemon=True
        ).start()

    def search_volumes_background(self, query, publisher_id):
        """Buscar volúmenes en background thread"""
        try:
            if not self.comicvine_client:
                GLib.idle_add(self.show_search_error, "Cliente ComicVine no disponible")
                return


            # Buscar volúmenes
            if publisher_id and publisher_id.strip():
                volumes = self.comicvine_client.get_volumes(query=query, publisher_id=publisher_id)
            else:
                volumes = self.comicvine_client.get_volumes(query=query)

            # Verificar cuáles ya están descargados
            volume_repo = VolumeRepository(self.session)
            downloaded_cv_ids = set()

            for volume in volumes:
                if volume.get('id'):
                    existing = volume_repo.get_by_comicvine_id(volume['id'])
                    if existing:
                        downloaded_cv_ids.add(volume['id'])

            # Actualizar UI en main thread
            GLib.idle_add(self.show_search_results, volumes, downloaded_cv_ids)

        except Exception as e:
            print(f"Error en búsqueda: {e}")
            GLib.idle_add(self.show_search_error, f"Error en la búsqueda: {str(e)}")

    def show_search_results(self, volumes, downloaded_cv_ids):
        """Mostrar resultados de búsqueda en UI"""
        try:
            self.search_results = volumes
            self.volume_cards = []

            if not volumes:
                self.results_label.set_text("No se encontraron volúmenes")
                self.filtered_results = []
            else:
                # Cargar editoriales encontradas en los resultados
                self.load_publishers_from_results()
                # Aplicar filtros y ordenamiento automáticamente
                self.apply_filters_and_sorting()

        except Exception as e:
            print(f"Error mostrando resultados: {e}")
            self.results_label.set_text("Error mostrando resultados")

        finally:
            # Rehabilitar búsqueda
            self.search_button.set_sensitive(True)
            self.search_spinner.stop()

    def show_search_error(self, message):
        """Mostrar error de búsqueda"""
        self.results_label.set_text(f"Error: {message}")
        self.search_button.set_sensitive(True)
        self.search_spinner.stop()

    def clear_results(self):
        """Limpiar solo la visualización de resultados"""
        child = self.results_flowbox.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.results_flowbox.remove(child)
            child = next_child

        self.volume_cards = []

    def clear_all_results(self):
        """Limpiar resultados y datos completamente (nueva búsqueda)"""
        self.clear_results()
        self.search_results = []
        self.filtered_results = []

    def on_card_selection_changed(self, card, selected):
        """Card seleccionado/deseleccionado"""
        self.download_button.set_sensitive(any(c.has_any_selected() for c in self.volume_cards))

    def on_select_all_clicked(self, button):
        """Seleccionar todos los volúmenes descubiertos recientemente"""
        for card in self.volume_cards:
            card.select_all_new()

    def on_deselect_all_clicked(self, button):
        """Deseleccionar todos los volúmenes"""
        for card in self.volume_cards:
            card.deselect_all()

    def on_download_clicked(self, button):
        """Descargar volúmenes seleccionados"""
        update_existing = self.update_existing_switch.get_active()

        selected_volumes = []
        for card in self.volume_cards:
            if update_existing:
                selected_volumes.extend(card.get_selected_volumes())
            else:
                selected_volumes.extend(card.get_selected_new_volumes())

        action_text = "descargar/actualizar" if update_existing else "descargar"

        if not selected_volumes:
            message = "Selecciona al menos un volumen para descargar"
            if update_existing:
                message = "Selecciona al menos un volumen para descargar o actualizar"
            self.show_error("Sin selección", message)
            return

        # Confirmar descarga
        total_issues = sum(vol.get('count_of_issues', 0) for vol in selected_volumes)

        # Contar nuevos vs existentes en todo el conjunto
        new_volumes = 0
        existing_volumes = 0
        for card in self.volume_cards:
            for v_card in card.get_internal_cards():
                if v_card.selected:
                    if not v_card.is_downloaded:
                        new_volumes += 1
                    else:
                        existing_volumes += 1

        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading("Confirmar Descarga")

        message_parts = []
        if new_volumes > 0:
            message_parts.append(f"{new_volumes} volúmenes nuevos")
        if existing_volumes > 0 and update_existing:
            message_parts.append(f"{existing_volumes} volúmenes existentes (actualizar)")

        # Mensaje detallado sobre lo que se descargará
        base_message = f"¿{action_text.capitalize()} {' y '.join(message_parts)} con aproximadamente {total_issues} issues?"

        detail_message = "\n\n📥 DESCARGA COMPLETA incluye:"
        detail_message += "\n• Información completa del volumen"
        detail_message += "\n• Todos los issues del volumen"
        detail_message += "\n• Covers del volumen e issues"
        detail_message += "\n• Metadatos completos"

        full_message = base_message + detail_message
        dialog.set_body(full_message)
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("download", action_text.capitalize())
        dialog.set_response_appearance("download", Adw.ResponseAppearance.SUGGESTED)
        dialog.connect("response", self.on_download_confirmed, selected_volumes)
        dialog.present()

    def on_download_confirmed(self, dialog, response, selected_volumes):
        """Descarga confirmada"""
        if response == "download":
            self.start_download(selected_volumes)

    def start_download(self, selected_volumes):
        """Iniciar descarga de volúmenes a través del DownloadManager"""
        # Guardar texto original para restaurar después
        self._original_results_text = self.results_label.get_text()

        # Deshabilitar controles
        self.download_button.set_sensitive(False)
        self.search_button.set_sensitive(False)

        try:
            from helpers.download_manager import DownloadManager
            manager = DownloadManager.get_instance()
            download_covers = self.download_covers_switch.get_active()

            total_volumes = len(selected_volumes)
            
            for volume_data in selected_volumes:
                manager.add_download(volume_data, self.comicvine_client, download_covers)

            self.results_label.set_text(f"{total_volumes} volúmenes en cola...")
            
            # Notificar al usuario que la descarga ha sido encolada
            self.show_success(
                "Descargas en cola", 
                f"Se han añadido {total_volumes} volúmenes a la cola de descargas.\nPuedes ver el progreso detallado en la solapa 'Descargas' del menú principal."
            )
            
        except Exception as e:
            print(f"Error encolando descargas: {e}")
            self.show_error("Error", f"No se pudieron encolar las descargas: {e}")
            
        finally:
            self.download_button.set_sensitive(True)
            self.search_button.set_sensitive(True)

    def download_volume_cover(self, volume, volume_details):
        """Descargar cover del volumen"""
        try:
            if (volume_details.get('image') and
                volume_details['image'].get('medium_url')):

                cover_url = volume_details['image']['medium_url']
                from helpers.thumbnail_path import get_thumbnails_base_path
                cover_path = download_image(
                    cover_url,
                    os.path.join(get_thumbnails_base_path(), "volumes"),
                    f"{volume.id_volume}.jpg"
                )

                if cover_path:
                    volume.image_url = cover_url
                    self.session.commit()
                    print(f"Cover descargado: {cover_path}")

        except Exception as e:
            print(f"Error descargando cover: {e}")

    def update_download_progress(self, progress, message):
        """Actualizar progreso de descarga"""
        self.progress_bar.set_fraction(progress)
        # Actualizar label de resultados con el progreso
        base_text = getattr(self, '_original_results_text', 'Descargando...')
        self.results_label.set_text(f"{base_text} - {message}")

    def download_completed(self, downloaded_volumes, total_requested):
        """Descarga completada"""
        self.progress_bar.set_visible(False)
        self.download_button.set_sensitive(True)
        self.search_button.set_sensitive(True)

        success_count = len(downloaded_volumes)

        if success_count == total_requested:
            message = f"¡Descarga completada! {success_count} volúmenes descargados."
        else:
            message = f"Descarga completada con errores. {success_count}/{total_requested} volúmenes descargados."

        self.show_success("Descarga Completada", message)

        # Auto-seleccionar primer volumen descargado si hay callback
        if (self.selected_volume_callback and downloaded_volumes):
            first_downloaded = downloaded_volumes[0]
            # Buscar en BD el volumen recién creado
            volume_repo = VolumeRepository(self.session)
            saved_volume = volume_repo.get_by_comicvine_id(first_downloaded['id'])
            if saved_volume:
                self.selected_volume_callback(saved_volume)

        # No cerrar la ventana automáticamente para permitir más búsquedas
        # self.close()

    def download_error(self, error_message):
        """Error en descarga"""
        self.progress_bar.set_visible(False)
        self.download_button.set_sensitive(True)
        self.search_button.set_sensitive(True)

        self.show_error("Error de Descarga", f"Error durante la descarga: {error_message}")

    def show_error(self, title, message):
        """Mostrar diálogo de error"""
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading(title)
        dialog.set_body(message)
        dialog.add_response("ok", "OK")
        dialog.present()

    def show_success(self, title, message):
        """Mostrar diálogo de éxito"""
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading(title)
        dialog.set_body(message)
        dialog.add_response("ok", "OK")
        dialog.present()

    def on_sort_changed(self, combo):
        """Cambio en ordenamiento - aplicar automáticamente"""
        print("Ordenamiento cambiado")
        if self.search_results:
            self.apply_filters_and_sorting()
        else:
            print("No hay resultados para ordenar")

    def on_publisher_filter_changed(self, combo):
        """Filtro de editorial cambió"""
        if self.search_results:
            self.apply_filters_and_sorting()

    def on_year_filter_changed(self, spin_button):
        """Filtro de año cambió"""
        if self.search_results:
            self.apply_filters_and_sorting()

    def on_issues_filter_changed(self, spin_button):
        """Filtro de cantidad de issues cambió"""
        if self.search_results:
            self.apply_filters_and_sorting()

    def on_downloaded_filter_changed(self, combo):
        """Filtro de estado de descarga cambió"""
        if self.search_results:
            self.apply_filters_and_sorting()

    def on_reset_filters_clicked(self, button):
        """Resetear todos los filtros para mostrar todo"""
        # Resetear filtros de año a valores amplios
        self.year_from_spin.set_value(1900)
        self.year_to_spin.set_value(2030)

        # Resetear filtros de issues a valores amplios
        self.issues_from_spin.set_value(1)
        self.issues_to_spin.set_value(5000)

        # Resetear filtro de estado a "Todos"
        self.downloaded_combo.set_active(0)

        # Resetear filtro de editorial a "Todas las editoriales"
        self.publisher_combo.set_active(0)

        # Los filtros se aplicarán automáticamente por los callbacks

    def apply_filters_and_sorting(self):
        """Aplicar filtros por fecha, editorial y ordenamiento a los resultados"""
        if not self.search_results:
            print("No hay resultados para filtrar")
            return
        print("Aplicando filtros y ordenamiento...")

        # Obtener valores de filtros
        year_from = int(self.year_from_spin.get_value())
        year_to = int(self.year_to_spin.get_value())
        issues_from = int(self.issues_from_spin.get_value())
        issues_to = int(self.issues_to_spin.get_value())
        selected_publisher_id = self.publisher_combo.get_active_id()
        downloaded_status = self.downloaded_combo.get_active_id()

        # Obtener IDs ya descargados si necesitamos filtrar por estado de descarga
        volume_repo = VolumeRepository(self.session)
        downloaded_cv_ids = set()
        if downloaded_status in ["descargados", "no_descargados"]:
            for volume in self.search_results:
                if volume.get('id'):
                    existing = volume_repo.get_by_comicvine_id(volume['id'])
                    if existing:
                        downloaded_cv_ids.add(volume['id'])

        filtered_volumes = []
        for volume in self.search_results:
            # Filtrar por año
            # print(f"Volumen: {volume.get('name')} - Año inicio: {volume.get('start_year')}")
            volume_year = volume.get('start_year')
            year_passes = True

            if volume_year and isinstance(volume_year, (int, str)):
                try:
                    year = int(str(volume_year))
                    if not (year_from <= year <= year_to):
                        year_passes = False
                except (ValueError, TypeError):
                    # Si no se puede convertir el año, incluir el volumen
                    pass
            # Si no tiene año, incluir el volumen (year_passes permanece True)

            # Filtrar por cantidad de números
            issues_passes = True
            volume_issues = volume.get('count_of_issues')
            if volume_issues is not None:
                try:
                    issues = int(str(volume_issues))
                    if not (issues_from <= issues <= issues_to):
                        issues_passes = False
                except (ValueError, TypeError):
                    pass

            # Filtrar por editorial
            publisher_passes = True
            if selected_publisher_id and selected_publisher_id != "":  # No es "Todas las editoriales"
                publisher = volume.get('publisher')
                if publisher:
                    publisher_id = str(publisher.get('id', ''))
                    publisher_name = publisher.get('name', '')
                    # Comparar tanto por ID como por nombre para flexibilidad
                    if selected_publisher_id != publisher_id and selected_publisher_id != publisher_name:
                        publisher_passes = False
                else:
                    publisher_passes = False

            # Filtrar por estado de descarga
            downloaded_passes = True
            if downloaded_status == "descargados":
                if volume.get('id') not in downloaded_cv_ids:
                    downloaded_passes = False
            elif downloaded_status == "no_descargados":
                if volume.get('id') in downloaded_cv_ids:
                    downloaded_passes = False

            # Solo incluir si pasa todos los filtros
            if year_passes and issues_passes and publisher_passes and downloaded_passes:
                filtered_volumes.append(volume)

        # Ordenar resultados
        sort_option = self.sort_combo.get_active_id()
        if sort_option == "date_desc":
            filtered_volumes.sort(key=lambda x: self._safe_int(x.get('start_year'), 0), reverse=True)
        elif sort_option == "date_asc":
            filtered_volumes.sort(key=lambda x: self._safe_int(x.get('start_year'), 0))
        elif sort_option == "name_asc":
            filtered_volumes.sort(key=lambda x: (x.get('name') or '').lower())
        elif sort_option == "name_desc":
            filtered_volumes.sort(key=lambda x: (x.get('name') or '').lower(), reverse=True)
        elif sort_option == "count_desc":
            filtered_volumes.sort(key=lambda x: self._safe_int(x.get('count_of_issues'), 0), reverse=True)
        elif sort_option == "count_asc":
            filtered_volumes.sort(key=lambda x: self._safe_int(x.get('count_of_issues'), 0))
        elif sort_option == "publisher_asc":
            filtered_volumes.sort(key=lambda x: (x.get('publisher', {}).get('name') or '').lower())

        self.filtered_results = filtered_volumes

        # Actualizar label informativo de filtros
        publisher_name = self.publisher_combo.get_active_text()
        downloaded_name = self.downloaded_combo.get_active_text()

        filter_info = f"Año: {year_from}-{year_to} | Números: {issues_from}-{issues_to}"
        if publisher_name and publisher_name != "Todas las editoriales":
            filter_info += f" | Editorial: {publisher_name}"
        if downloaded_name and downloaded_name != "Todos":
            filter_info += f" | Estado: {downloaded_name}"

        filter_info += f" | {len(filtered_volumes)}/{len(self.search_results)} resultados"
        self.filter_info_label.set_text(filter_info)


        # Actualizar la visualización
        self.update_results_display()

    def update_results_display(self):
        """Actualizar la visualización de resultados filtrados"""
        try:
            # Limpiar resultados anteriores
            self.clear_results()

            if not self.filtered_results:
                self.results_label.set_text("No hay volúmenes que coincidan con los filtros")
                return

            # Verificar cuáles ya están descargados
            volume_repo = VolumeRepository(self.session)
            downloaded_cv_ids = set()

            for volume in self.filtered_results:
                if volume.get('id'):
                    existing = volume_repo.get_by_comicvine_id(volume['id'])
                    if existing:
                        downloaded_cv_ids.add(volume['id'])

            # Actualizar label
            total_results = len(self.search_results)
            filtered_count = len(self.filtered_results)

            if filtered_count == total_results:
                self.results_label.set_text(f"Mostrando {filtered_count} volúmenes")
            else:
                self.results_label.set_text(f"Mostrando {filtered_count} de {total_results} volúmenes")

            # Crear cards para volúmenes filtrados agrupando duplicados
            
            from collections import OrderedDict
            grouped_volumes = OrderedDict()
            
            for volume in self.filtered_results:
                v_name = (volume.get('name') or '').lower().strip()
                publisher_data = volume.get('publisher') or {}
                v_publisher = (publisher_data.get('name') or '').lower().strip()
                group_key = f"{v_name}::{v_publisher}"
                
                if group_key not in grouped_volumes:
                    grouped_volumes[group_key] = []
                grouped_volumes[group_key].append(volume)
            
            for group_key, volumes_in_group in grouped_volumes.items():
                card = VolumeGroupCard(volumes_in_group, downloaded_cv_ids)
                card.connect('selection-changed', self.on_card_selection_changed)

                self.volume_cards.append(card)
                self.results_flowbox.append(card)

        except Exception as e:
            print(f"Error actualizando visualización: {e}")
            self.results_label.set_text("Error actualizando resultados")