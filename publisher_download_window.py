#!/usr/bin/env python3
"""
Ventana para buscar y descargar editoriales desde ComicVine
"""

import gi
import os
import threading
from pathlib import Path

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib, GdkPixbuf, Gdk, Pango, GObject

from helpers.comicvine_cliente import ComicVineClient
from helpers.image_downloader import download_image
from repositories.publisher_repository import PublisherRepository


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
                import tempfile
                temp_dir = tempfile.gettempdir()
                image_path = download_image(image_url, temp_dir)

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


# Registrar señal personalizada
GObject.signal_new('selection-changed', PublisherSearchCard, GObject.SignalFlags.RUN_FIRST, None, (bool,))


class PublisherDownloadWindow(Adw.Window):
    """Ventana para buscar y descargar editoriales desde ComicVine"""

    def __init__(self, parent_window, session):
        super().__init__()
        self.parent_window = parent_window
        self.session = session

        self.comicvine_client = None
        self.search_results = []
        self.publisher_cards = []

        self.set_title("Descargar Editoriales de ComicVine")
        self.set_default_size(800, 600)
        self.set_modal(True)
        self.set_transient_for(parent_window)

        self.setup_ui()
        self.setup_keyboard_shortcuts()
        self.init_comicvine_client()

    def init_comicvine_client(self):
        """Inicializar cliente de ComicVine"""
        try:
            from repositories.setup_repository import SetupRepository
            from sqlalchemy.orm import sessionmaker
            from entidades import engine

            Session = sessionmaker(bind=engine)
            temp_session = Session()
            setup_repo = SetupRepository(temp_session)
            config = setup_repo.obtener_o_crear_configuracion()

            api_key = config.get_api_key()
            temp_session.close()

            if not api_key:
                self.show_error("No hay API Key configurada.\n\nVe a Configuración y agrega tu API Key de ComicVine.")
                return

            self.comicvine_client = ComicVineClient(api_key)
            print("✅ Cliente ComicVine inicializado")

        except Exception as e:
            print(f"Error inicializando ComicVine: {e}")
            self.show_error(f"Error inicializando ComicVine:\n{e}")

    def setup_ui(self):
        """Configurar la interfaz de usuario"""

        # Box principal
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # HeaderBar
        header_bar = Adw.HeaderBar()
        header_bar.set_title_widget(Gtk.Label(label="Descargar Editoriales de ComicVine"))

        # Botones de acción en el header
        actions_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        # Botón descargar seleccionadas
        self.download_button = Gtk.Button(label="Descargar Seleccionadas")
        self.download_button.add_css_class("suggested-action")
        self.download_button.connect("clicked", self.on_download_clicked)
        self.download_button.set_sensitive(False)
        actions_box.append(self.download_button)

        # Botón seleccionar todas
        select_all_button = Gtk.Button(label="Seleccionar Todas")
        select_all_button.connect("clicked", self.on_select_all_clicked)
        actions_box.append(select_all_button)

        header_bar.pack_start(actions_box)
        main_box.append(header_bar)

        # Barra de búsqueda
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        search_box.set_margin_start(12)
        search_box.set_margin_end(12)
        search_box.set_margin_top(12)
        search_box.set_margin_bottom(12)

        # Entry de búsqueda
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Buscar editorial...")
        self.search_entry.set_hexpand(True)
        self.search_entry.connect("activate", self.on_search_clicked)
        search_box.append(self.search_entry)

        # Botón buscar
        search_button = Gtk.Button(label="Buscar")
        search_button.add_css_class("suggested-action")
        search_button.connect("clicked", self.on_search_clicked)
        search_box.append(search_button)

        main_box.append(search_box)

        # Área de resultados
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)

        # FlowBox para los resultados
        self.results_flowbox = Gtk.FlowBox()
        self.results_flowbox.set_valign(Gtk.Align.START)
        self.results_flowbox.set_max_children_per_line(10)
        self.results_flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.results_flowbox.set_margin_start(12)
        self.results_flowbox.set_margin_end(12)
        self.results_flowbox.set_margin_top(12)
        self.results_flowbox.set_margin_bottom(12)

        scrolled.set_child(self.results_flowbox)
        main_box.append(scrolled)

        # Status bar
        self.status_label = Gtk.Label()
        self.status_label.set_margin_start(12)
        self.status_label.set_margin_end(12)
        self.status_label.set_margin_top(6)
        self.status_label.set_margin_bottom(6)
        self.status_label.add_css_class("dim-label")
        main_box.append(self.status_label)

        # Progress bar (oculta inicialmente)
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_margin_start(12)
        self.progress_bar.set_margin_end(12)
        self.progress_bar.set_margin_bottom(12)
        self.progress_bar.set_visible(False)
        main_box.append(self.progress_bar)

        self.set_content(main_box)

    def setup_keyboard_shortcuts(self):
        """Configurar atajos de teclado"""
        # ESC para cerrar la ventana
        event_controller = Gtk.EventControllerKey.new()
        event_controller.connect("key-pressed", self.on_key_pressed)
        self.add_controller(event_controller)

    def on_key_pressed(self, controller, keyval, keycode, state):
        """Manejar teclas presionadas"""
        # ESC para cerrar
        if keyval == Gdk.KEY_Escape:
            self.close()
            return True
        return False

    def on_search_clicked(self, widget):
        """Buscar editoriales"""
        query = self.search_entry.get_text().strip()

        if not query:
            self.show_error("Por favor ingresa un término de búsqueda")
            return

        if not self.comicvine_client:
            self.show_error("Cliente ComicVine no inicializado")
            return

        # Limpiar resultados previos
        self.clear_results()
        self.status_label.set_text("Buscando...")

        # Buscar en hilo de fondo
        threading.Thread(
            target=self.search_publishers_background,
            args=(query,),
            daemon=True
        ).start()

    def search_publishers_background(self, query):
        """Buscar editoriales en hilo de fondo"""
        try:
            # Reemplazar espacios con + para búsquedas múltiples
            # Ejemplo: "Dynamite Entertainment" -> "Dynamite+Entertainment"
            # URL: https://comicvine.gamespot.com/api/publishers/?filter=name:Dynamite+Entertainment&limit=100&api_key=...&format=json
            query_formatted = query.replace(' ', '+')

            print(f"DEBUG Publisher Search - Query original: '{query}'")
            print(f"DEBUG Publisher Search - Query formateado: '{query_formatted}'")

            results = self.comicvine_client.get_publishers(
                limit=100,
                name_filter=query_formatted
            )

            if results:
                GLib.idle_add(lambda: self.display_search_results(results))
            else:
                GLib.idle_add(lambda: self.status_label.set_text("No se encontraron resultados"))

        except Exception as e:
            print(f"Error buscando editoriales: {e}")
            import traceback
            traceback.print_exc()
            GLib.idle_add(lambda: self.show_error(f"Error en la búsqueda:\n{e}"))

    def display_search_results(self, publishers):
        """Mostrar resultados de búsqueda"""
        self.search_results = publishers
        self.clear_results()

        if not publishers:
            self.status_label.set_text("No se encontraron resultados")
            return

        # Obtener IDs de editoriales ya descargadas
        publisher_repo = PublisherRepository(self.session)
        downloaded_ids = set()
        try:
            all_publishers = publisher_repo.obtener_todas()
            for pub in all_publishers:
                if pub.id_comicvine:
                    downloaded_ids.add(pub.id_comicvine)
        except Exception as e:
            print(f"Error obteniendo editoriales descargadas: {e}")

        # Crear cards
        for publisher_data in publishers:
            publisher_id = publisher_data.get('id')
            is_downloaded = publisher_id in downloaded_ids

            card = PublisherSearchCard(publisher_data, is_downloaded)
            card.connect('selection-changed', self.on_card_selection_changed)
            self.publisher_cards.append(card)
            self.results_flowbox.append(card)

        self.status_label.set_text(f"{len(publishers)} editoriales encontradas")

    def clear_results(self):
        """Limpiar resultados"""
        while self.results_flowbox.get_first_child():
            self.results_flowbox.remove(self.results_flowbox.get_first_child())
        self.publisher_cards = []
        self.download_button.set_sensitive(False)

    def on_card_selection_changed(self, card, selected):
        """Cambio en selección de card"""
        # Actualizar estado del botón de descarga
        has_selection = any(card.selected for card in self.publisher_cards)
        self.download_button.set_sensitive(has_selection)

    def on_select_all_clicked(self, button):
        """Seleccionar todas las editoriales"""
        for card in self.publisher_cards:
            if not card.is_downloaded:
                card.set_selected(True)

    def on_download_clicked(self, button):
        """Descargar editoriales seleccionadas"""
        selected_publishers = [
            card.publisher_data
            for card in self.publisher_cards
            if card.selected and not card.is_downloaded
        ]

        if not selected_publishers:
            self.show_error("No hay editoriales seleccionadas para descargar")
            return

        # Confirmación
        count = len(selected_publishers)
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading("Confirmar Descarga")
        dialog.set_body(f"¿Descargar {count} editorial(es) desde ComicVine?")
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("download", "Descargar")
        dialog.set_response_appearance("download", Adw.ResponseAppearance.SUGGESTED)
        dialog.connect("response", lambda d, r, pubs=selected_publishers: self.on_download_confirmed(d, r, pubs))
        dialog.present()

    def on_download_confirmed(self, dialog, response, publishers):
        """Confirmar y comenzar descarga"""
        if response == "download":
            self.start_download(publishers)

    def start_download(self, publishers):
        """Iniciar descarga de editoriales"""
        # Deshabilitar controles
        self.download_button.set_sensitive(False)
        self.search_entry.set_sensitive(False)
        self.progress_bar.set_visible(True)
        self.status_label.set_text("Descargando editoriales...")

        # Descargar en hilo de fondo
        threading.Thread(
            target=self.download_publishers_background,
            args=(publishers,),
            daemon=True
        ).start()

    def download_publishers_background(self, publishers):
        """Descargar editoriales en hilo de fondo"""
        downloaded = 0
        failed = 0
        total = len(publishers)

        for idx, publisher_data in enumerate(publishers):
            try:
                # Actualizar progreso
                progress = (idx + 1) / total
                GLib.idle_add(lambda p=progress: self.progress_bar.set_fraction(p))
                GLib.idle_add(
                    lambda i=idx+1, t=total: self.status_label.set_text(
                        f"Descargando editorial {i}/{t}..."
                    )
                )

                # Descargar editorial
                success = self.download_single_publisher(publisher_data)
                if success:
                    downloaded += 1
                else:
                    failed += 1

            except Exception as e:
                print(f"Error descargando editorial: {e}")
                failed += 1

        # Finalizar
        GLib.idle_add(lambda: self.download_completed(downloaded, failed, total))

    def download_single_publisher(self, publisher_data):
        """Descargar una editorial individual"""
        try:
            from entidades.publisher_model import Publisher

            # Crear objeto Publisher
            publisher = Publisher()
            publisher.nombre = publisher_data.get('name', '')
            publisher.deck = publisher_data.get('deck', '')
            publisher.descripcion = publisher_data.get('description', '')
            publisher.sitio_web = publisher_data.get('site_detail_url', '')
            publisher.id_comicvine = publisher_data.get('id')

            # Guardar logo si está disponible
            image_data = publisher_data.get('image')
            if image_data:
                image_url = image_data.get('medium_url') or image_data.get('small_url')
                if image_url:
                    publisher.url_logo = image_url

                    # Descargar imagen
                    try:
                        logo_path = self.download_publisher_logo(publisher, image_url)
                        if logo_path:
                            print(f"✅ Logo descargado: {logo_path}")
                    except Exception as e:
                        print(f"Error descargando logo: {e}")

            # Guardar en BD
            self.session.add(publisher)
            self.session.commit()

            print(f"✅ Editorial guardada: {publisher.nombre}")
            return True

        except Exception as e:
            print(f"❌ Error guardando editorial: {e}")
            import traceback
            traceback.print_exc()
            self.session.rollback()
            return False

    def download_publisher_logo(self, publisher, image_url):
        """Descargar logo de editorial"""
        try:
            # Crear directorio si no existe
            logo_dir = Path("data/thumbnails/editoriales")
            logo_dir.mkdir(parents=True, exist_ok=True)

            # Descargar imagen directamente a la carpeta de editoriales
            filename = Path(image_url).name
            if not filename:
                filename = f"{publisher.id_comicvine}.jpg"

            dest_path = download_image(image_url, str(logo_dir), filename)

            if dest_path and os.path.exists(dest_path):
                return dest_path

        except Exception as e:
            print(f"Error descargando logo: {e}")

        return None

    def download_completed(self, downloaded, failed, total):
        """Finalizar descarga"""
        # Restaurar controles
        self.search_entry.set_sensitive(True)
        self.progress_bar.set_visible(False)
        self.progress_bar.set_fraction(0)

        # Mostrar resultado
        message = f"Descarga completada:\n\n"
        message += f"✅ Exitosas: {downloaded}\n"
        if failed > 0:
            message += f"❌ Fallidas: {failed}\n"

        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading("Descarga Completada")
        dialog.set_body(message)
        dialog.add_response("ok", "OK")
        dialog.present()

        # Actualizar resultados
        if downloaded > 0:
            # Recargar para mostrar estado actualizado
            self.status_label.set_text(f"Descarga completada: {downloaded}/{total} editoriales")

    def show_error(self, message):
        """Mostrar mensaje de error"""
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading("Error")
        dialog.set_body(message)
        dialog.add_response("ok", "OK")
        dialog.set_response_appearance("ok", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.present()


def show_publisher_download_window(parent_window, session):
    """Helper para mostrar la ventana de descarga de editoriales"""
    window = PublisherDownloadWindow(parent_window, session)
    window.present()
    return window
