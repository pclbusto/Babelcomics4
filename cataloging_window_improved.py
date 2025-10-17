#!/usr/bin/env python3
"""
Ventana de catalogación mejorada con diseño de dos columnas y previews de covers
"""

import gi
import os
import re
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GObject, Pango, GdkPixbuf, Gdk, GLib, Gio
from entidades.comicbook_model import Comicbook
from entidades.volume_model import Volume
from entidades.comicbook_info_model import ComicbookInfo
from comicvine_download_window import ComicVineDownloadWindow


class VolumeSelectionDialog(Adw.Window):
    """Diálogo para seleccionar volumen mejorado"""

    __gsignals__ = {
        'volume-selected': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
    }

    def __init__(self, parent_window, session):
        super().__init__()
        self.session = session

        self.set_title("Seleccionar Volumen")
        self.set_default_size(800, 600)
        self.set_transient_for(parent_window)
        self.set_modal(True)

        self.setup_ui()
        self.load_volumes()

    def setup_ui(self):
        """Configurar interfaz del diálogo"""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # Header
        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label="Seleccionar Volumen"))

        cancel_button = Gtk.Button.new_with_label("Cancelar")
        cancel_button.connect("clicked", lambda b: self.close())
        header.pack_start(cancel_button)

        main_box.append(header)

        # Búsqueda
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        search_box.set_margin_start(12)
        search_box.set_margin_end(12)
        search_box.set_margin_top(12)
        search_box.set_margin_bottom(8)

        search_label = Gtk.Label(label="Buscar:")
        search_box.append(search_label)

        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Nombre del volumen...")
        self.search_entry.set_hexpand(True)
        self.search_entry.connect("search-changed", self.on_search_changed)
        search_box.append(self.search_entry)

        main_box.append(search_box)

        # Lista de volúmenes
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.volume_list = Gtk.ListBox()
        self.volume_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.volume_list.add_css_class("boxed-list")
        self.volume_list.set_margin_start(12)
        self.volume_list.set_margin_end(12)
        self.volume_list.connect("row-activated", self.on_volume_activated)

        scrolled.set_child(self.volume_list)
        main_box.append(scrolled)

        self.set_content(main_box)

    def load_volumes(self):
        """Cargar volúmenes"""
        try:
            volumes = self.session.query(Volume).order_by(Volume.nombre).all()

            for volume in volumes:
                row = VolumeRowWidget(volume)
                self.volume_list.append(row)

        except Exception as e:
            print(f"Error cargando volúmenes: {e}")

    def on_search_changed(self, entry):
        """Filtrar volúmenes por búsqueda"""
        search_text = entry.get_text().lower()

        row = self.volume_list.get_first_child()
        while row:
            if hasattr(row, 'volume'):
                volume_name = row.volume.nombre.lower()
                row.set_visible(search_text in volume_name)
            row = row.get_next_sibling()

    def on_volume_activated(self, listbox, row):
        """Volumen seleccionado"""
        if hasattr(row, 'volume'):
            self.emit('volume-selected', row.volume)
            self.close()


class VolumeRowWidget(Gtk.ListBoxRow):
    """Widget para mostrar un volumen en la lista"""

    def __init__(self, volume):
        super().__init__()
        self.volume = volume

        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        main_box.set_margin_start(8)
        main_box.set_margin_end(8)
        main_box.set_margin_top(8)
        main_box.set_margin_bottom(8)

        # Thumbnail del volumen
        image = Gtk.Picture()
        image.set_size_request(40, 60)
        image.set_can_shrink(True)
        image.set_keep_aspect_ratio(True)

        # Cargar thumbnail si existe
        thumb_path = f"data/thumbnails/volumes/{volume.id_volume}.jpg"
        if os.path.exists(thumb_path):
            image.set_filename(thumb_path)
        else:
            # Placeholder
            pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 40, 60)
            pixbuf.fill(0x33D17AFF)  # Verde
            texture = Gdk.Texture.new_for_pixbuf(pixbuf)
            image.set_paintable(texture)

        main_box.append(image)

        # Info del volumen
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        info_box.set_hexpand(True)

        # Título
        title_label = Gtk.Label(label=volume.nombre)
        title_label.set_wrap(True)
        title_label.set_lines(2)
        title_label.set_ellipsize(Pango.EllipsizeMode.END)
        title_label.set_halign(Gtk.Align.START)
        title_label.add_css_class("heading")
        info_box.append(title_label)

        # Detalles
        details = []
        if volume.anio_inicio > 0:
            details.append(str(volume.anio_inicio))
        details.append(f"{volume.cantidad_numeros} números")

        details_label = Gtk.Label(label=" • ".join(details))
        details_label.set_halign(Gtk.Align.START)
        details_label.add_css_class("dim-label")
        details_label.add_css_class("caption")
        info_box.append(details_label)

        main_box.append(info_box)

        # ID
        id_label = Gtk.Label(label=f"#{volume.id_volume}")
        id_label.add_css_class("title-3")
        id_label.add_css_class("accent")
        main_box.append(id_label)

        self.set_child(main_box)


class PhysicalComicItem(Gtk.ListBoxRow):
    """Item para comic físico en la lista"""

    __gsignals__ = {
        'number-changed': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    def __init__(self, comicbook, thumbnail_generator):
        super().__init__()
        self.comicbook = comicbook
        self.thumbnail_generator = thumbnail_generator
        self.assigned_number = ""

        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        main_box.set_margin_start(8)
        main_box.set_margin_end(8)
        main_box.set_margin_top(4)
        main_box.set_margin_bottom(4)

        # Thumbnail pequeño
        self.image = Gtk.Picture()
        self.image.set_size_request(30, 40)
        self.image.set_can_shrink(True)
        self.image.set_keep_aspect_ratio(True)
        self.load_thumbnail()
        main_box.append(self.image)

        # Info del archivo
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        info_box.set_hexpand(True)

        # Nombre del archivo
        filename = os.path.basename(self.comicbook.path)
        name_label = Gtk.Label(label=filename)
        name_label.set_wrap(True)
        name_label.set_lines(1)
        name_label.set_ellipsize(Pango.EllipsizeMode.END)
        name_label.set_halign(Gtk.Align.START)
        name_label.add_css_class("body")
        info_box.append(name_label)

        # Tamaño
        try:
            size_mb = os.path.getsize(self.comicbook.path) / (1024 * 1024)
            size_label = Gtk.Label(label=f"{size_mb:.1f} MB")
            size_label.set_halign(Gtk.Align.START)
            size_label.add_css_class("dim-label")
            size_label.add_css_class("caption")
            info_box.append(size_label)
        except:
            pass

        main_box.append(info_box)

        # Campo de número
        self.number_entry = Gtk.Entry()
        self.number_entry.set_placeholder_text("#")
        self.number_entry.set_size_request(60, -1)
        self.number_entry.set_max_length(8)  # Permitir más caracteres para números+letras
        self.number_entry.connect("changed", self.on_number_changed)

        # Auto-detectar número del filename
        auto_number = self.extract_number_from_filename(filename)
        if auto_number:
            self.number_entry.set_text(auto_number)
            self.assigned_number = auto_number

        main_box.append(self.number_entry)

        self.set_child(main_box)

    def load_thumbnail(self):
        """Cargar thumbnail del comic"""
        try:
            thumb_path = self.thumbnail_generator.get_cached_thumbnail_path(
                self.comicbook.id_comicbook, "comics"
            )
            if thumb_path and os.path.exists(str(thumb_path)):
                self.image.set_filename(str(thumb_path))
            else:
                # Placeholder
                pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 30, 40)
                pixbuf.fill(0x3584E4FF)  # Azul
                texture = Gdk.Texture.new_for_pixbuf(pixbuf)
                self.image.set_paintable(texture)
        except Exception as e:
            print(f"Error cargando thumbnail: {e}")

    def extract_number_from_filename(self, filename):
        """Extraer número del nombre de archivo (números y letras, sin zeros a la izquierda)"""
        patterns = [
            r'#([0-9]+[A-Za-z]*)',           # Comic #123A
            r'#([A-Za-z]*[0-9]+[A-Za-z]*)',  # Comic #A123B
            r'\s([0-9]+[A-Za-z]*)\s',        # Comic 123A (2023)
            r'\s([0-9]+[A-Za-z]*)\.',        # Comic 123B.cbr
            r'\s([0-9]+[A-Za-z]*)$',         # Comic 123C
            r'([0-9]+[A-Za-z]*)\.cb[rz]$',   # 123D.cbr
            r'([0-9]+)',                     # Cualquier número (solo números)
        ]

        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                result = match.group(1)
                # Quitar zeros a la izquierda pero preservar letras
                if result.isdigit():
                    return str(int(result))  # Convierte "007" -> "7"
                else:
                    # Si tiene letras, quitar zeros solo de la parte numérica inicial
                    digit_match = re.match(r'^0*(\d.*)', result)
                    if digit_match:
                        return digit_match.group(1)
                    return result
        return None

    def on_number_changed(self, entry):
        """Número cambiado"""
        self.assigned_number = entry.get_text().strip()
        self.emit('number-changed', self.assigned_number)


class MetadataComicItem(Gtk.ListBoxRow):
    """Item para metadata de comic en la lista"""

    def __init__(self, comicbook_info):
        super().__init__()
        self.comicbook_info = comicbook_info

        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        main_box.set_margin_start(8)
        main_box.set_margin_end(8)
        main_box.set_margin_top(4)
        main_box.set_margin_bottom(4)

        # Thumbnail de la portada
        self.image = Gtk.Picture()
        self.image.set_size_request(30, 40)
        self.image.set_can_shrink(True)
        self.image.set_keep_aspect_ratio(True)
        self.load_cover()
        main_box.append(self.image)

        # Info del issue
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        info_box.set_hexpand(True)

        # Título
        title_text = comicbook_info.titulo or f"Issue #{comicbook_info.numero}"
        title_label = Gtk.Label(label=title_text)
        title_label.set_wrap(True)
        title_label.set_lines(1)
        title_label.set_ellipsize(Pango.EllipsizeMode.END)
        title_label.set_halign(Gtk.Align.START)
        title_label.add_css_class("body")
        info_box.append(title_label)

        # Fecha
        if comicbook_info.fecha_tapa:
            date_label = Gtk.Label(label=str(comicbook_info.fecha_tapa))
            date_label.set_halign(Gtk.Align.START)
            date_label.add_css_class("dim-label")
            date_label.add_css_class("caption")
            info_box.append(date_label)

        main_box.append(info_box)

        # Número destacado
        number_label = Gtk.Label(label=f"#{comicbook_info.numero}")
        number_label.add_css_class("title-3")
        number_label.add_css_class("accent")
        main_box.append(number_label)

        self.set_child(main_box)

    def load_cover(self):
        """Cargar cover del issue"""
        try:
            # Buscar cover en directorio de issues
            if hasattr(self.comicbook_info, 'volume') and self.comicbook_info.volume:
                volume_name = self.comicbook_info.volume.nombre.replace("/", "_").replace("\\", "_")
                cover_dir = f"data/thumbnails/comicbook_info/{volume_name}_{self.comicbook_info.volume.id_volume}"
                cover_path = f"{cover_dir}/{self.comicbook_info.id_comicbook_info}-{self.comicbook_info.numero}.jpg"

                if os.path.exists(cover_path):
                    self.image.set_filename(cover_path)
                    return

            # Placeholder
            pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 30, 40)
            pixbuf.fill(0x9141ACFF)  # Púrpura
            texture = Gdk.Texture.new_for_pixbuf(pixbuf)
            self.image.set_paintable(texture)

        except Exception as e:
            print(f"Error cargando cover: {e}")


class CoverPreviewWidget(Gtk.Box):
    """Widget para mostrar preview grande del cover seleccionado"""

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.set_size_request(80, 120)
        self.set_halign(Gtk.Align.CENTER)

        # Imagen compacta
        self.image = Gtk.Picture()
        self.image.set_size_request(70, 90)
        self.image.set_can_shrink(True)
        self.image.set_keep_aspect_ratio(True)
        self.image.add_css_class("cover-image")

        self.append(self.image)

        # Label de información
        self.info_label = Gtk.Label()
        self.info_label.set_wrap(True)
        self.info_label.set_justify(Gtk.Justification.CENTER)
        self.info_label.add_css_class("caption")
        self.info_label.add_css_class("dim-label")
        self.append(self.info_label)

        # Crear placeholder inicial (después de crear todos los widgets)
        self.set_placeholder()

    def set_placeholder(self):
        """Mostrar placeholder"""
        pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 180, 240)
        pixbuf.fill(0x808080FF)  # Gris
        texture = Gdk.Texture.new_for_pixbuf(pixbuf)
        self.image.set_paintable(texture)
        self.info_label.set_text("Selecciona un item para ver el cover")

    def show_physical_comic(self, comicbook, thumbnail_generator):
        """Mostrar cover de comic físico"""
        try:
            thumb_path = thumbnail_generator.get_cached_thumbnail_path(
                comicbook.id_comicbook, "comics"
            )
            if thumb_path and os.path.exists(str(thumb_path)):
                self.image.set_filename(str(thumb_path))
            else:
                self.set_placeholder()

            filename = os.path.basename(comicbook.path)
            self.info_label.set_text(f"Físico: {filename}")

        except Exception as e:
            print(f"Error mostrando cover físico: {e}")
            self.set_placeholder()

    def show_metadata_comic(self, comicbook_info):
        """Mostrar cover de metadata"""
        try:
            # Buscar cover en directorio de issues
            if hasattr(comicbook_info, 'volume') and comicbook_info.volume:
                volume_name = comicbook_info.volume.nombre.replace("/", "_").replace("\\", "_")
                cover_dir = f"data/thumbnails/comicbook_info/{volume_name}_{comicbook_info.volume.id_volume}"
                cover_path = f"{cover_dir}/{comicbook_info.id_comicbook_info}-{comicbook_info.numero}.jpg"

                print(f"DEBUG Metadata: Buscando cover en: {cover_path}")
                print(f"DEBUG Metadata: Existe? {os.path.exists(cover_path)}")

                if os.path.exists(cover_path):
                    self.image.set_filename(cover_path)
                    print(f"DEBUG Metadata: Cover cargado: {cover_path}")
                else:
                    # Intentar también buscar usando la función obtener_portada_principal
                    try:
                        cover_path_alt = comicbook_info.obtener_portada_principal()
                        print(f"DEBUG Metadata: Ruta alternativa: {cover_path_alt}")
                        if cover_path_alt and os.path.exists(cover_path_alt) and not cover_path_alt.endswith("Comic_sin_caratula.png"):
                            self.image.set_filename(cover_path_alt)
                            print(f"DEBUG Metadata: Cover alternativo cargado: {cover_path_alt}")
                        else:
                            self.set_placeholder()
                    except:
                        self.set_placeholder()
            else:
                self.set_placeholder()

            title = comicbook_info.titulo or f"Issue #{comicbook_info.numero}"
            date_info = f" ({comicbook_info.fecha_tapa})" if comicbook_info.fecha_tapa else ""
            self.info_label.set_text(f"Metadata: {title}{date_info}")

        except Exception as e:
            print(f"Error mostrando cover metadata: {e}")
            self.set_placeholder()


class ImprovedCatalogingWindow(Adw.Window):
    """Ventana de catalogación mejorada"""

    def __init__(self, parent_window, comicbook_ids, session):
        super().__init__()
        self.parent_window = parent_window
        self.comicbook_ids = comicbook_ids
        self.session = session

        # Estado
        self.comicbooks = []
        self.selected_volume = None
        self.comicbook_infos = []

        self.set_title("Catalogar Comics")
        self.set_default_size(1400, 800)
        self.set_transient_for(parent_window)
        self.set_modal(True)

        self.setup_ui()
        self.load_comicbooks()

    def setup_ui(self):
        """Configurar interfaz mejorada"""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # Header
        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label="Catalogar Comics"))

        cancel_button = Gtk.Button.new_with_label("Cancelar")
        cancel_button.connect("clicked", lambda b: self.close())
        header.pack_start(cancel_button)

        self.save_button = Gtk.Button.new_with_label("Guardar")
        self.save_button.add_css_class("suggested-action")
        self.save_button.connect("clicked", self.on_save_cataloging)
        self.save_button.set_sensitive(False)
        header.pack_end(self.save_button)

        main_box.append(header)

        # Selección de volumen
        volume_group = Adw.PreferencesGroup()

        self.volume_row = Adw.ActionRow()
        self.volume_row.set_title("Volumen seleccionado")
        self.volume_row.set_subtitle("Ninguno seleccionado")

        select_button = Gtk.Button.new_with_label("Seleccionar")
        select_button.set_valign(Gtk.Align.CENTER)
        select_button.set_tooltip_text("Selecciona el volumen de destino con el que hacer el matching")
        select_button.connect("clicked", self.on_select_volume)
        self.volume_row.add_suffix(select_button)

        download_button = Gtk.Button.new_with_label("Buscar en ComicVine")
        download_button.set_valign(Gtk.Align.CENTER)
        download_button.set_tooltip_text("Buscar y descargar volúmenes desde ComicVine")
        download_button.connect("clicked", self.on_download_volumes_clicked)
        self.volume_row.add_suffix(download_button)

        volume_group.add(self.volume_row)
        main_box.append(volume_group)

        # Área principal con dos columnas
        content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        content_box.set_margin_start(16)
        content_box.set_margin_end(16)
        content_box.set_margin_top(16)
        content_box.set_margin_bottom(16)
        content_box.set_vexpand(True)

        # Columna izquierda - Comics físicos
        self.setup_physical_column(content_box)

        # Separador
        separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        content_box.append(separator)

        # Columna derecha - Metadata
        self.setup_metadata_column(content_box)

        main_box.append(content_box)

        self.set_content(main_box)

    def setup_physical_column(self, parent):
        """Configurar columna de comics físicos"""
        physical_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        physical_box.set_hexpand(True)

        # Header reorganizado: título con botón arriba, preview abajo
        header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        header_box.set_margin_bottom(8)

        # Fila de título y botón
        title_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        title_label = Gtk.Label(label="Comics Físicos")
        title_label.add_css_class("title-3")
        title_label.set_halign(Gtk.Align.START)
        title_row.append(title_label)

        auto_button = Gtk.Button.new_with_label("Auto #")
        auto_button.set_tooltip_text("Extraer números automáticamente")
        auto_button.connect("clicked", self.on_auto_extract_numbers)
        title_row.append(auto_button)

        header_box.append(title_row)

        # Preview del físico seleccionado (debajo del título)
        self.physical_preview = CoverPreviewWidget()
        header_box.append(self.physical_preview)

        physical_box.append(header_box)

        # Lista de físicos
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_min_content_height(300)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.physical_list = Gtk.ListBox()
        self.physical_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.physical_list.add_css_class("boxed-list")
        self.physical_list.connect("row-selected", self.on_physical_selected)

        # Configurar menú contextual
        self.setup_context_menu()

        # Configurar tecla Delete
        self.setup_delete_key_handler()

        scrolled.set_child(self.physical_list)
        physical_box.append(scrolled)

        parent.append(physical_box)

    def setup_metadata_column(self, parent):
        """Configurar columna de metadata"""
        metadata_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        metadata_box.set_hexpand(True)

        # Header reorganizado: título arriba, preview abajo
        header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        header_box.set_margin_bottom(8)

        # Título simple
        self.metadata_title = Gtk.Label(label="Metadata")
        self.metadata_title.add_css_class("title-3")
        self.metadata_title.set_halign(Gtk.Align.START)
        header_box.append(self.metadata_title)

        # Preview del metadata seleccionado (debajo del título)
        self.metadata_preview = CoverPreviewWidget()
        header_box.append(self.metadata_preview)

        metadata_box.append(header_box)

        # Lista de metadata
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_min_content_height(300)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.metadata_list = Gtk.ListBox()
        self.metadata_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.metadata_list.add_css_class("boxed-list")
        self.metadata_list.connect("row-selected", self.on_metadata_selected)

        scrolled.set_child(self.metadata_list)
        metadata_box.append(scrolled)

        parent.append(metadata_box)

    def load_comicbooks(self):
        """Cargar comics físicos"""
        try:
            for comic_id in self.comicbook_ids:
                comicbook = self.session.query(Comicbook).get(comic_id)
                if comicbook:
                    self.comicbooks.append(comicbook)

            self.create_physical_items()

        except Exception as e:
            print(f"Error cargando comicbooks: {e}")

    def create_physical_items(self):
        """Crear items para comics físicos"""
        for comicbook in self.comicbooks:
            item = PhysicalComicItem(comicbook, self.parent_window.thumbnail_generator)
            item.connect('number-changed', self.on_number_changed)
            self.physical_list.append(item)

    def on_select_volume(self, button):
        """Abrir selector de volumen"""
        dialog = VolumeSelectionDialog(self, self.session)
        dialog.connect('volume-selected', self.on_volume_selected)
        dialog.present()

    def on_volume_selected(self, dialog, volume):
        """Volumen seleccionado"""
        self.selected_volume = volume

        # Actualizar UI
        subtitle_text = f"{volume.nombre} ({volume.cantidad_numeros} números)"
        self.volume_row.set_subtitle(subtitle_text)

        # Cargar metadata del volumen
        self.load_volume_metadata()

        # Habilitar botón guardar
        self.save_button.set_sensitive(True)

    def on_download_volumes_clicked(self, button):
        """Abrir ventana de descarga de volúmenes"""
        try:
            download_window = ComicVineDownloadWindow(
                self,
                self.session,
                selected_volume_callback=self.on_volume_downloaded
            )
            download_window.present()
        except Exception as e:
            print(f"Error abriendo ventana de descarga: {e}")

    def on_volume_downloaded(self, volume):
        """Callback cuando se descarga un volumen desde ComicVine"""
        # Auto-seleccionar el volumen recién descargado
        self.on_volume_selected(None, volume)

    def get_physical_comic_numbers(self):
        """Obtener los números asignados a los comics físicos"""
        assigned_numbers = set()
        row = self.physical_list.get_first_child()
        while row:
            if hasattr(row, 'assigned_number') and row.assigned_number.strip():
                assigned_numbers.add(row.assigned_number.strip())
            # También incluir números extraídos automáticamente
            if hasattr(row, 'number_entry'):
                current_text = row.number_entry.get_text().strip()
                if current_text:
                    assigned_numbers.add(current_text)
            row = row.get_next_sibling()
        return assigned_numbers

    def load_volume_metadata(self):
        """Cargar metadata del volumen filtrado por números de comics físicos"""
        try:
            # Limpiar lista anterior
            while True:
                child = self.metadata_list.get_first_child()
                if child:
                    self.metadata_list.remove(child)
                else:
                    break

            # Obtener números de comics físicos
            physical_numbers = self.get_physical_comic_numbers()
            print(f"DEBUG: Números de comics físicos: {physical_numbers}")

            # Cargar todos los items del volumen
            all_infos = self.session.query(ComicbookInfo).filter(
                ComicbookInfo.id_volume == self.selected_volume.id_volume
            ).order_by(ComicbookInfo.numero).all()

            # Filtrar solo los que coinciden con números físicos
            if physical_numbers:
                # Convertir números a strings para comparación
                physical_numbers_str = {str(num) for num in physical_numbers}
                self.comicbook_infos = [
                    info for info in all_infos
                    if str(info.numero) in physical_numbers_str
                ]
                print(f"DEBUG: Issues filtrados: {len(self.comicbook_infos)} de {len(all_infos)} total")
            else:
                # Si no hay números asignados, mostrar todos
                self.comicbook_infos = all_infos
                print(f"DEBUG: Sin filtros, mostrando todos los {len(all_infos)} issues")

            # Agregar items a la lista
            for info in self.comicbook_infos:
                item = MetadataComicItem(info)
                self.metadata_list.append(item)

            # Actualizar título con información de filtro
            total_count = len(all_infos)
            filtered_count = len(self.comicbook_infos)
            if physical_numbers and filtered_count < total_count:
                self.metadata_title.set_text(f"Metadata ({filtered_count}/{total_count})")
            else:
                self.metadata_title.set_text("Metadata")

        except Exception as e:
            print(f"Error cargando metadata: {e}")

    def on_physical_selected(self, listbox, row):
        """Comic físico seleccionado"""
        if row and hasattr(row, 'comicbook'):
            # Mostrar cover del físico
            self.physical_preview.show_physical_comic(
                row.comicbook,
                self.parent_window.thumbnail_generator
            )

            # Buscar y seleccionar metadata que haga match
            self.auto_select_matching_metadata(row)

    def auto_select_matching_metadata(self, physical_row):
        """Buscar y seleccionar automáticamente metadata que coincida con el número del físico"""
        try:
            if not hasattr(physical_row, 'assigned_number') and not hasattr(physical_row, 'number_entry'):
                return

            # Obtener el número del físico
            physical_number = None
            if hasattr(physical_row, 'assigned_number') and physical_row.assigned_number.strip():
                physical_number = physical_row.assigned_number.strip()
            elif hasattr(physical_row, 'number_entry'):
                physical_number = physical_row.number_entry.get_text().strip()

            if not physical_number:
                print("DEBUG: No hay número asignado para buscar metadata")
                return

            print(f"DEBUG: Buscando metadata con número: {physical_number}")

            # Buscar en la lista de metadata
            metadata_row = self.metadata_list.get_first_child()
            while metadata_row:
                if (hasattr(metadata_row, 'comicbook_info') and
                    str(metadata_row.comicbook_info.numero) == str(physical_number)):

                    print(f"DEBUG: Encontrado match! Seleccionando issue #{metadata_row.comicbook_info.numero}")
                    # Seleccionar automáticamente esta fila
                    self.metadata_list.select_row(metadata_row)
                    # Mostrar preview del metadata
                    self.metadata_preview.show_metadata_comic(metadata_row.comicbook_info)
                    return

                metadata_row = metadata_row.get_next_sibling()

            print(f"DEBUG: No se encontró metadata con número {physical_number}")

        except Exception as e:
            print(f"Error en auto_select_matching_metadata: {e}")

    def on_metadata_selected(self, listbox, row):
        """Metadata seleccionado"""
        if row and hasattr(row, 'comicbook_info'):
            self.metadata_preview.show_metadata_comic(row.comicbook_info)

    def on_number_changed(self, item, number):
        """Número de comic cambiado"""
        # Recargar metadata filtrado cuando cambien los números
        if hasattr(self, 'selected_volume') and self.selected_volume:
            self.load_volume_metadata()

    def on_auto_extract_numbers(self, button):
        """Extraer números automáticamente"""
        row = self.physical_list.get_first_child()
        numbers_changed = False
        while row:
            if hasattr(row, 'number_entry') and hasattr(row, 'comicbook'):
                if not row.number_entry.get_text().strip():
                    filename = os.path.basename(row.comicbook.path)
                    auto_number = row.extract_number_from_filename(filename)
                    if auto_number:
                        row.number_entry.set_text(auto_number)
                        numbers_changed = True
            row = row.get_next_sibling()

        # Recargar metadata si se extrajeron números
        if numbers_changed and hasattr(self, 'selected_volume') and self.selected_volume:
            self.load_volume_metadata()

    def setup_context_menu(self):
        """Configurar menú contextual para la lista de físicos"""
        # Crear gestor de click derecho
        gesture = Gtk.GestureClick.new()
        gesture.set_button(3)  # Botón derecho
        gesture.connect("pressed", self.on_right_click)
        self.physical_list.add_controller(gesture)

        # Crear menú contextual simple usando Gtk.Popover
        self.context_menu = Gtk.Popover()

        # Crear contenido del menú
        menu_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        menu_box.add_css_class("menu")

        remove_button = Gtk.Button.new_with_label("Eliminar de la lista")
        remove_button.add_css_class("flat")
        remove_button.add_css_class("menu-item")
        remove_button.connect("clicked", self.on_remove_button_clicked)

        menu_box.append(remove_button)
        self.context_menu.set_child(menu_box)

    def setup_delete_key_handler(self):
        """Configurar manejo de la tecla Delete"""
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self.on_key_pressed)
        self.physical_list.add_controller(key_controller)

    def on_right_click(self, gesture, n_press, x, y):
        """Manejar click derecho en la lista"""
        # Obtener el row bajo el cursor
        row = self.physical_list.get_row_at_y(int(y))
        if row:
            self.physical_list.select_row(row)
            # Posicionar y mostrar menú contextual
            rect = Gdk.Rectangle()
            rect.x = int(x)
            rect.y = int(y)
            self.context_menu.set_pointing_to(rect)
            self.context_menu.set_parent(self.physical_list)
            self.context_menu.popup()

    def on_key_pressed(self, controller, keyval, keycode, state):
        """Manejar teclas presionadas"""
        if keyval == Gdk.KEY_Delete:
            self.remove_selected_from_list()
            return True
        return False

    def on_remove_button_clicked(self, button):
        """Manejar click en el botón eliminar del menú contextual"""
        self.context_menu.popdown()
        self.remove_selected_from_list()

    def remove_selected_from_list(self):
        """Eliminar el elemento seleccionado de la lista"""
        selected_row = self.physical_list.get_selected_row()
        if selected_row and hasattr(selected_row, 'comicbook'):
            # Remover de la lista de comics
            if selected_row.comicbook in self.comicbooks:
                self.comicbooks.remove(selected_row.comicbook)

            # Remover de la lista visual
            self.physical_list.remove(selected_row)

            # Limpiar preview si era el seleccionado
            self.physical_preview.set_placeholder()

            print(f"Comic {selected_row.comicbook.nombre} eliminado de la lista de catalogación")

    def on_save_cataloging(self, button):
        """Guardar catalogación"""
        if not self.selected_volume:
            return

        # Aquí implementar la lógica de guardado
        # Iterar sobre los items físicos y sus números asignados
        # Hacer el matching con la metadata
        # Guardar las asociaciones en la BD

        saved_count = 0

        row = self.physical_list.get_first_child()
        while row:
            if hasattr(row, 'assigned_number') and hasattr(row, 'comicbook'):
                number = row.assigned_number.strip()
                if number:
                    try:
                        # Buscar metadata correspondiente
                        matching_info = None
                        for info in self.comicbook_infos:
                            if str(info.numero) == number:
                                matching_info = info
                                break

                        if matching_info:
                            # Actualizar comicbook con la asociación
                            row.comicbook.id_comicbook_info = matching_info.id_comicbook_info
                            saved_count += 1

                    except Exception as e:
                        print(f"Error guardando comic {row.comicbook.id_comicbook}: {e}")

            row = row.get_next_sibling()

        # Commit cambios
        try:
            self.session.commit()
            print(f"Guardados {saved_count} comics catalogados")

            # Mostrar confirmación y cerrar
            toast = Adw.Toast()
            toast.set_title(f"✅ {saved_count} comics catalogados exitosamente")
            toast.set_timeout(3)

            if hasattr(self.parent_window, 'toast_overlay'):
                self.parent_window.toast_overlay.add_toast(toast)

            self.close()

        except Exception as e:
            print(f"Error guardando en BD: {e}")
            self.session.rollback()


def create_improved_cataloging_window(parent_window, comic_ids, session):
    """Función factory para crear la ventana mejorada"""
    if not comic_ids:
        print("No hay comics para catalogar")
        return None

    window = ImprovedCatalogingWindow(parent_window, comic_ids, session)
    return window