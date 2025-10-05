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

    def __init__(self, volume_data, is_downloaded=False):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.volume_data = volume_data
        self.is_downloaded = is_downloaded
        self.selected = False

        self.set_size_request(200, 320)
        self.add_css_class("card")
        self.set_margin_top(8)
        self.set_margin_bottom(8)
        self.set_margin_start(8)
        self.set_margin_end(8)

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

            print(f"DEBUG: Descargando cover: {image_url}")

            # Descargar imagen
            response = requests.get(image_url, timeout=10)
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
                print(f"DEBUG: No se pudo crear pixbuf para {image_url}")

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


class ComicVineDownloadWindow(Adw.Window):
    """Ventana para buscar y descargar volúmenes desde ComicVine"""

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

    def load_publishers(self):
        """Cargar editoriales en el ComboBox"""
        try:
            from repositories.publisher_repository import PublisherRepository
            publisher_repo = PublisherRepository(self.session)
            publishers = publisher_repo.obtener_todas()

            for publisher in publishers:
                # Solo agregar editoriales que tengan ID de ComicVine
                if publisher.id_comicvine:
                    self.publisher_combo.append(str(publisher.id_comicvine), publisher.nombre)
        except Exception as e:
            print(f"Error cargando editoriales: {e}")

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

        # Contenedor scrollable para todo el contenido
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_vexpand(True)

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content_box.set_margin_start(12)
        content_box.set_margin_end(12)
        content_box.set_margin_top(12)
        content_box.set_margin_bottom(12)

        # Header con búsqueda (compacto)
        self.create_search_header(content_box)

        # Área de resultados
        self.create_results_area(content_box)

        # Footer con controles de descarga (compacto)
        self.create_download_footer(content_box)

        scrolled_window.set_child(content_box)
        main_box.append(scrolled_window)

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

        # ComboBox de editorial
        self.publisher_combo = Gtk.ComboBoxText()
        self.publisher_combo.append("", "Todas las editoriales")
        self.publisher_combo.set_active(0)
        self.publisher_combo.set_size_request(150, -1)
        self.load_publishers()
        main_search_box.append(self.publisher_combo)

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
        self.year_from_spin.set_value(1900)
        self.year_from_spin.set_tooltip_text("Año desde")
        date_filter_box.append(self.year_from_spin)

        dash_label = Gtk.Label(label="—")
        date_filter_box.append(dash_label)

        # Año hasta
        self.year_to_spin = Gtk.SpinButton()
        self.year_to_spin.set_range(1900, 2030)
        self.year_to_spin.set_value(2030)
        self.year_to_spin.set_tooltip_text("Año hasta")
        date_filter_box.append(self.year_to_spin)

        filters_box.append(date_filter_box)

        # Separador visual
        separator1 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        filters_box.append(separator1)

        # Ordenamiento
        sort_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        sort_label = Gtk.Label(label="Ordenar por:")
        sort_box.append(sort_label)

        self.sort_combo = Gtk.ComboBoxText()
        self.sort_combo.append("date_desc", "Fecha (más reciente)")
        self.sort_combo.append("date_asc", "Fecha (más antiguo)")
        self.sort_combo.append("name_asc", "Nombre (A-Z)")
        self.sort_combo.append("name_desc", "Nombre (Z-A)")
        self.sort_combo.append("count_desc", "Más números")
        self.sort_combo.append("count_asc", "Menos números")
        self.sort_combo.append("publisher_asc", "Editorial (A-Z)")
        self.sort_combo.set_active(0)  # Por defecto: fecha más reciente
        self.sort_combo.connect("changed", self.on_sort_changed)
        sort_box.append(self.sort_combo)

        filters_box.append(sort_box)

        # Separador visual
        separator2 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        filters_box.append(separator2)

        # Botón aplicar filtros
        apply_filters_button = Gtk.Button.new_with_label("Aplicar Filtros")
        apply_filters_button.connect("clicked", self.on_apply_filters_clicked)
        filters_box.append(apply_filters_button)

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
        controller = Gtk.EventControllerKey()
        controller.connect("key-pressed", self.on_key_pressed)
        self.add_controller(controller)

    def on_key_pressed(self, controller, keyval, keycode, state):
        """Manejar teclas presionadas"""
        if keyval == 65307:  # Escape key
            self.close()
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
        self.clear_results()

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

            print(f"DEBUG: Buscando '{query}' en ComicVine...")

            # Buscar volúmenes
            if publisher_id and publisher_id.strip():
                print(f"DEBUG: Filtrando por editorial ID: {publisher_id}")
                volumes = self.comicvine_client.get_volumes(query=query, publisher_id=publisher_id)
            else:
                volumes = self.comicvine_client.get_volumes(query=query)

            print(f"DEBUG: Encontrados {len(volumes)} volúmenes")

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
                print(f"DEBUG: Encontrados {len(volumes)} volúmenes, aplicando filtros...")
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
        """Limpiar resultados anteriores"""
        child = self.results_flowbox.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.results_flowbox.remove(child)
            child = next_child

        self.volume_cards = []
        self.search_results = []

    def on_card_selection_changed(self, card, selected):
        """Card seleccionado/deseleccionado"""
        selected_count = sum(1 for card in self.volume_cards if card.selected)
        self.download_button.set_sensitive(selected_count > 0)

    def on_select_all_clicked(self, button):
        """Seleccionar todos los volúmenes"""
        for card in self.volume_cards:
            if not card.is_downloaded:  # Solo seleccionar los no descargados
                card.set_selected(True)

    def on_deselect_all_clicked(self, button):
        """Deseleccionar todos los volúmenes"""
        for card in self.volume_cards:
            card.set_selected(False)

    def on_download_clicked(self, button):
        """Descargar volúmenes seleccionados"""
        update_existing = self.update_existing_switch.get_active()

        # Si la opción de actualizar está activada, incluir también volúmenes ya descargados
        if update_existing:
            selected_volumes = [
                card.volume_data for card in self.volume_cards
                if card.selected
            ]
            action_text = "descargar/actualizar"
        else:
            selected_volumes = [
                card.volume_data for card in self.volume_cards
                if card.selected and not card.is_downloaded
            ]
            action_text = "descargar"

        if not selected_volumes:
            message = "Selecciona al menos un volumen para descargar"
            if update_existing:
                message = "Selecciona al menos un volumen para descargar o actualizar"
            self.show_error("Sin selección", message)
            return

        # Confirmar descarga
        total_issues = sum(vol.get('count_of_issues', 0) for vol in selected_volumes)

        # Contar nuevos vs existentes
        new_volumes = sum(1 for card in self.volume_cards if card.selected and not card.is_downloaded)
        existing_volumes = sum(1 for card in self.volume_cards if card.selected and card.is_downloaded)

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
        """Iniciar descarga de volúmenes CON INFORMACIÓN COMPLETA"""
        # Guardar texto original para restaurar después
        self._original_results_text = self.results_label.get_text()

        # Deshabilitar controles
        self.download_button.set_sensitive(False)
        self.search_button.set_sensitive(False)
        self.progress_bar.set_visible(True)

        # Actualizar mensaje inicial
        total_volumes = len(selected_volumes)
        self.results_label.set_text(f"Iniciando descarga completa de {total_volumes} volúmenes...")

        # Descargar en background
        threading.Thread(
            target=self.download_volumes_background,
            args=(selected_volumes,),
            daemon=True
        ).start()

    def download_volumes_background(self, selected_volumes):
        """Descargar volúmenes en background"""
        try:
            total_volumes = len(selected_volumes)
            downloaded_volumes = []

            for i, volume_data in enumerate(selected_volumes):
                try:
                    progress = (i + 1) / total_volumes
                    GLib.idle_add(self.update_download_progress, progress, f"Descargando {volume_data.get('name', 'volumen')}...")

                    # Descargar volumen
                    success = self.download_single_volume(volume_data)
                    if success:
                        downloaded_volumes.append(volume_data)

                except Exception as e:
                    print(f"Error descargando volumen {volume_data.get('name', 'N/A')}: {e}")

            # Completado
            GLib.idle_add(self.download_completed, downloaded_volumes, total_volumes)

        except Exception as e:
            print(f"Error en descarga background: {e}")
            GLib.idle_add(self.download_error, str(e))

    def download_single_volume(self, volume_data):
        """Descargar un solo volumen CON INFORMACIÓN COMPLETA"""
        try:
            volume_repo = VolumeRepository(self.session)
            download_covers = self.download_covers_switch.get_active()

            # Usar la nueva función de descarga completa que incluye:
            # - Información del volumen
            # - Todos los issues
            # - Covers del volumen e issues
            def progress_callback(message):
                # Actualizar progreso en la interfaz
                progress_message = f"[{volume_data.get('name', 'Volumen')}] {message}"
                print(progress_message)

            print(f"🚀 Iniciando descarga completa de: {volume_data.get('name', 'Volumen')}")

            # Usar la función de descarga completa del repositorio
            saved_volume = volume_repo.download_complete_volume_data(
                volume_data=volume_data,
                comicvine_client=self.comicvine_client,
                download_covers=download_covers,
                progress_callback=progress_callback
            )

            print(f"✅ Descarga completa exitosa: '{saved_volume.nombre}'")
            print(f"   - Volumen creado/actualizado")
            print(f"   - Issues descargados e integrados")
            if download_covers:
                print(f"   - Covers descargándose en segundo plano")

            return True

        except Exception as e:
            print(f"❌ Error en descarga completa del volumen: {e}")
            import traceback
            traceback.print_exc()
            return False

    def download_volume_cover(self, volume, volume_details):
        """Descargar cover del volumen"""
        try:
            if (volume_details.get('image') and
                volume_details['image'].get('medium_url')):

                cover_url = volume_details['image']['medium_url']
                cover_path = download_image(
                    cover_url,
                    "data/thumbnails/volumes",
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

        # Cerrar ventana
        self.close()

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
        if self.search_results:
            self.apply_filters_and_sorting()

    def on_apply_filters_clicked(self, button):
        """Aplicar filtros de fecha"""
        if self.search_results:
            self.apply_filters_and_sorting()

    def apply_filters_and_sorting(self):
        """Aplicar filtros por fecha y ordenamiento a los resultados"""
        if not self.search_results:
            return

        # Filtrar por año
        year_from = int(self.year_from_spin.get_value())
        year_to = int(self.year_to_spin.get_value())

        filtered_volumes = []
        for volume in self.search_results:
            volume_year = volume.get('start_year')
            if volume_year and isinstance(volume_year, (int, str)):
                try:
                    year = int(str(volume_year))
                    if year_from <= year <= year_to:
                        filtered_volumes.append(volume)
                except (ValueError, TypeError):
                    # Si no se puede convertir el año, incluir el volumen
                    filtered_volumes.append(volume)
            else:
                # Si no tiene año, incluir el volumen
                filtered_volumes.append(volume)

        # Ordenar resultados
        sort_option = self.sort_combo.get_active_id()
        if sort_option == "date_desc":
            filtered_volumes.sort(key=lambda x: x.get('start_year') or 0, reverse=True)
        elif sort_option == "date_asc":
            filtered_volumes.sort(key=lambda x: x.get('start_year') or 0)
        elif sort_option == "name_asc":
            filtered_volumes.sort(key=lambda x: (x.get('name') or '').lower())
        elif sort_option == "name_desc":
            filtered_volumes.sort(key=lambda x: (x.get('name') or '').lower(), reverse=True)
        elif sort_option == "count_desc":
            filtered_volumes.sort(key=lambda x: x.get('count_of_issues') or 0, reverse=True)
        elif sort_option == "count_asc":
            filtered_volumes.sort(key=lambda x: x.get('count_of_issues') or 0)
        elif sort_option == "publisher_asc":
            filtered_volumes.sort(key=lambda x: (x.get('publisher', {}).get('name') or '').lower())

        self.filtered_results = filtered_volumes

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

            # Crear cards para volúmenes filtrados
            for volume in self.filtered_results:
                is_downloaded = volume.get('id') in downloaded_cv_ids
                card = VolumeSearchCard(volume, is_downloaded)
                card.connect('selection-changed', self.on_card_selection_changed)

                self.volume_cards.append(card)
                self.results_flowbox.append(card)

        except Exception as e:
            print(f"Error actualizando visualización: {e}")
            self.results_label.set_text("Error actualizando resultados")