#!/usr/bin/env python3
"""
Nueva ventana de catalogación desde cero - Versión mejorada con comparación visual
Permite seleccionar un volumen y asignar números a comics físicos para hacer matching con metadata
"""

import gi
import os
import re
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GObject, Pango, GdkPixbuf, Gdk, GLib
from entidades.comicbook_model import Comicbook
from entidades.volume_model import Volume
from entidades.comicbook_info_model import ComicbookInfo
from comic_cards import ComicCard

# Tamaño estándar para todos los thumbnails
THUMBNAIL_WIDTH = 40
THUMBNAIL_HEIGHT = 50


class PhysicalComicRow(Gtk.ListBoxRow):
    """Fila que representa un comic físico con su número asignado"""
    
    __gsignals__ = {
        'number-changed': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'selected': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }
    
    def __init__(self, comicbook, thumbnail_generator):
        super().__init__()
        self.comicbook = comicbook
        self.thumbnail_generator = thumbnail_generator
        self.assigned_number = ""
        
        # Crear contenido de la fila
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        main_box.set_margin_start(8)
        main_box.set_margin_end(8)
        main_box.set_margin_top(4)
        main_box.set_margin_bottom(4)
        
        # Thumbnail (tamaño estándar)
        self.image = Gtk.Picture()
        self.image.set_size_request(THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT)
        self.image.set_can_shrink(True)
        self.image.set_keep_aspect_ratio(True)
        self.image.add_css_class("cover-image")
        self.load_thumbnail()
        main_box.append(self.image)
        
        # Info del comic
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        info_box.set_hexpand(True)
        info_box.set_valign(Gtk.Align.CENTER)
        
        # Nombre del archivo
        filename = os.path.basename(self.comicbook.path)
        self.name_label = Gtk.Label(label=filename)
        self.name_label.set_wrap(True)
        self.name_label.set_lines(1)
        self.name_label.set_ellipsize(Pango.EllipsizeMode.END)
        self.name_label.set_halign(Gtk.Align.START)
        self.name_label.add_css_class("body")
        info_box.append(self.name_label)
        
        # ID
        id_label = Gtk.Label(label=f"ID: {self.comicbook.id_comicbook}")
        id_label.add_css_class("dim-label")
        id_label.add_css_class("caption")
        id_label.set_halign(Gtk.Align.START)
        info_box.append(id_label)
        
        main_box.append(info_box)
        
        # Campo número
        number_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        
        self.number_entry = Gtk.Entry()
        self.number_entry.set_placeholder_text("Núm")
        self.number_entry.set_size_request(60, -1)
        self.number_entry.connect("changed", self.on_number_changed)
        number_box.append(self.number_entry)
        
        # Botón extraer
        extract_button = Gtk.Button()
        extract_button.set_icon_name("find-location-symbolic")
        extract_button.set_tooltip_text("Extraer del nombre")
        extract_button.add_css_class("flat")
        extract_button.connect("clicked", self.on_extract_number)
        number_box.append(extract_button)
        
        main_box.append(number_box)
        
        # Status
        self.status_icon = Gtk.Image()
        self.status_icon.set_icon_name("dialog-question-symbolic")
        main_box.append(self.status_icon)
        
        self.set_child(main_box)
        
        # Click gesture para selección
        click = Gtk.GestureClick()
        click.connect("pressed", self.on_clicked)
        self.add_controller(click)
        
    def load_thumbnail(self):
        """Cargar thumbnail del comic"""
        try:
            cover_path = self.comicbook.obtener_cover()
            if os.path.exists(cover_path):
                self.image.set_filename(cover_path)
            else:
                self.set_placeholder_image()
        except:
            self.set_placeholder_image()
            
    def set_placeholder_image(self):
        """Establecer imagen placeholder"""
        try:
            pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT)
            pixbuf.fill(0x3584E4FF)
            texture = Gdk.Texture.new_for_pixbuf(pixbuf)
            self.image.set_paintable(texture)
        except:
            pass
            
    def on_clicked(self, gesture, n_press, x, y):
        """Manejar click en la fila"""
        self.emit('selected')
        
    def on_number_changed(self, entry):
        """Manejar cambio en el número"""
        self.assigned_number = entry.get_text().strip()
        self.update_status()
        self.emit('number-changed', self.assigned_number)
        
    def on_extract_number(self, button):
        """Extraer número automáticamente del nombre del archivo"""
        filename = os.path.basename(self.comicbook.path)
        number = self.extract_number_from_filename(filename)
        
        if number:
            self.number_entry.set_text(number)
        
    def extract_number_from_filename(self, filename):
        """Extraer número del filename usando patrones comunes"""
        patterns = [
            r'#(\d+)',           # Comic #123
            r'\s(\d+)\s',        # Comic 123 (2023)
            r'\s(\d+)\.',        # Comic 123.cbr
            r'\s(\d+)#!/usr/bin/env python3']
"""
Nueva ventana de catalogación desde cero - Versión compacta con comparación
Permite seleccionar un volumen y asignar números a comics físicos para hacer matching con metadata
"""

import gi
import os
import re
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GObject, Pango, GdkPixbuf, Gdk, GLib
from entidades.comicbook_model import Comicbook
from entidades.volume_model import Volume
from entidades.comicbook_info_model import ComicbookInfo
from comic_cards import ComicCard


class PhysicalComicRow(Gtk.ListBoxRow):
    """Fila que representa un comic físico con su número asignado"""
    
    __gsignals__ = {
        'number-changed': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'selected': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }
    
    def __init__(self, comicbook, thumbnail_generator):
        super().__init__()
        self.comicbook = comicbook
        self.thumbnail_generator = thumbnail_generator
        self.assigned_number = ""
        
        # Crear contenido de la fila
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        main_box.set_margin_start(8)
        main_box.set_margin_end(8)
        main_box.set_margin_top(4)
        main_box.set_margin_bottom(4)
        
        # Thumbnail pequeño
        self.image = Gtk.Picture()
        self.image.set_size_request(32, 40)
        self.image.set_can_shrink(True)
        self.image.set_keep_aspect_ratio(True)
        self.image.add_css_class("cover-image")
        self.load_thumbnail()
        main_box.append(self.image)
        
        # Info del comic
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        info_box.set_hexpand(True)
        info_box.set_valign(Gtk.Align.CENTER)
        
        # Nombre del archivo
        filename = os.path.basename(self.comicbook.path)
        self.name_label = Gtk.Label(label=filename)
        self.name_label.set_wrap(True)
        self.name_label.set_lines(1)
        self.name_label.set_ellipsize(Pango.EllipsizeMode.END)
        self.name_label.set_halign(Gtk.Align.START)
        self.name_label.add_css_class("body")
        info_box.append(self.name_label)
        
        # ID
        id_label = Gtk.Label(label=f"ID: {self.comicbook.id_comicbook}")
        id_label.add_css_class("dim-label")
        id_label.add_css_class("caption")
        id_label.set_halign(Gtk.Align.START)
        info_box.append(id_label)
        
        main_box.append(info_box)
        
        # Campo número
        number_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        
        self.number_entry = Gtk.Entry()
        self.number_entry.set_placeholder_text("Núm")
        self.number_entry.set_size_request(60, -1)
        self.number_entry.connect("changed", self.on_number_changed)
        number_box.append(self.number_entry)
        
        # Botón extraer
        extract_button = Gtk.Button()
        extract_button.set_icon_name("find-location-symbolic")
        extract_button.set_tooltip_text("Extraer del nombre")
        extract_button.add_css_class("flat")
        extract_button.connect("clicked", self.on_extract_number)
        number_box.append(extract_button)
        
        main_box.append(number_box)
        
        # Status
        self.status_icon = Gtk.Image()
        self.status_icon.set_icon_name("dialog-question-symbolic")
        main_box.append(self.status_icon)
        
        self.set_child(main_box)
        
        # Click gesture para selección
        click = Gtk.GestureClick()
        click.connect("pressed", self.on_clicked)
        self.add_controller(click)
        
    def load_thumbnail(self):
        """Cargar thumbnail del comic"""
        try:
            cover_path = self.comicbook.obtener_cover()
            if os.path.exists(cover_path):
                self.image.set_filename(cover_path)
            else:
                self.set_placeholder_image()
        except:
            self.set_placeholder_image()
            
    def set_placeholder_image(self):
        """Establecer imagen placeholder"""
        try:
            pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 32, 40)
            pixbuf.fill(0x3584E4FF)
            texture = Gdk.Texture.new_for_pixbuf(pixbuf)
            self.image.set_paintable(texture)
        except:
            pass
            
    def on_clicked(self, gesture, n_press, x, y):
        """Manejar click en la fila"""
        self.emit('selected')
        
    def on_number_changed(self, entry):
        """Manejar cambio en el número"""
        self.assigned_number = entry.get_text().strip()
        self.update_status()
        self.emit('number-changed', self.assigned_number)
        
    def on_extract_number(self, button):
        """Extraer número automáticamente del nombre del archivo"""
        filename = os.path.basename(self.comicbook.path)
        number = self.extract_number_from_filename(filename)
        
        if number:
            self.number_entry.set_text(number)
        
    def extract_number_from_filename(self, filename):
        """Extraer número del filename usando patrones comunes"""
        patterns = [
            r'#(\d+)',           # Comic #123
            r'\s(\d+)\s',        # Comic 123 (2023)
            r'\s(\d+)\.',        # Comic 123.cbr
            r'\s(\d+)$',         # Comic 123
            r'(\d+)\.cb[rz]$',   # 123.cbr
            r'(\d+)',            # Cualquier número
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                return match.group(1)
        return None
        
    def get_assigned_number(self):
        """Obtener número asignado"""
        return self.assigned_number
        
    def set_assigned_number(self, number):
        """Establecer número asignado"""
        self.assigned_number = str(number) if number else ""
        self.number_entry.set_text(self.assigned_number)
        
    def update_status(self):
        """Actualizar status del matching"""
        if self.assigned_number:
            self.status_icon.set_icon_name("emblem-ok-symbolic")
            self.status_icon.add_css_class("success")
        else:
            self.status_icon.set_icon_name("dialog-question-symbolic")
            self.status_icon.remove_css_class("success")
            
    def set_selected(self, selected):
        """Marcar como seleccionado"""
        if selected:
            self.add_css_class("selected-row")
        else:
            self.remove_css_class("selected-row")


class MetadataComicRow(Gtk.ListBoxRow):
    """Fila que representa un ComicbookInfo (metadata)"""
    
    __gsignals__ = {
        'selected': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }
    
    def __init__(self, comicbook_info):
        super().__init__()
        self.comicbook_info = comicbook_info
        
        # Crear contenido de la fila
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        main_box.set_margin_start(8)
        main_box.set_margin_end(8)
        main_box.set_margin_top(4)
        main_box.set_margin_bottom(4)
        
        # Thumbnail de la portada
        self.image = Gtk.Picture()
        self.image.set_size_request(32, 40)
        self.image.set_can_shrink(True)
        self.image.set_keep_aspect_ratio(True)
        self.image.add_css_class("cover-image")
        self.load_cover()
        main_box.append(self.image)
        
        # Info del comic
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        info_box.set_hexpand(True)
        info_box.set_valign(Gtk.Align.CENTER)
        
        # Título y número
        title_text = f"#{comicbook_info.numero}"
        if comicbook_info.titulo:
            title_text += f" - {comicbook_info.titulo}"
        
        self.title_label = Gtk.Label(label=title_text)
        self.title_label.set_wrap(True)
        self.title_label.set_lines(1)
        self.title_label.set_ellipsize(Pango.EllipsizeMode.END)
        self.title_label.set_halign(Gtk.Align.START)
        self.title_label.add_css_class("body")
        info_box.append(self.title_label)
        
        # Fecha
        if comicbook_info.fecha_tapa:
            date_label = Gtk.Label(label=f"Fecha: {comicbook_info.fecha_tapa}")
            date_label.add_css_class("dim-label")
            date_label.add_css_class("caption")
            date_label.set_halign(Gtk.Align.START)
            info_box.append(date_label)
        
        main_box.append(info_box)
        
        # Número destacado
        number_label = Gtk.Label(label=str(comicbook_info.numero))
        number_label.add_css_class("title-2")
        number_label.add_css_class("accent")
        main_box.append(number_label)
        
        self.set_child(main_box)
        
        # Click gesture
        click = Gtk.GestureClick()
        click.connect("pressed", self.on_clicked)
        self.add_controller(click)
        
    def load_cover(self):
        """Cargar portada del ComicbookInfo"""
        try:
            if self.comicbook_info.portadas and len(self.comicbook_info.portadas) > 0:
                cover_path = self.comicbook_info.portadas[0].obtener_ruta_local()
                if os.path.exists(cover_path):
                    self.image.set_filename(cover_path)
                    return
        except:
            pass
            
        # Placeholder
        try:
            pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 32, 40)
            pixbuf.fill(0x33D17AFF)  # Verde
            texture = Gdk.Texture.new_for_pixbuf(pixbuf)
            self.image.set_paintable(texture)
        except:
            pass
            
    def on_clicked(self, gesture, n_press, x, y):
        """Manejar click en la fila"""
        self.emit('selected')
        
    def set_selected(self, selected):
        """Marcar como seleccionado"""
        if selected:
            self.add_css_class("selected-row")
        else:
            self.remove_css_class("selected-row")


class ComparisonPanel(Gtk.Box):
    """Panel de comparación de covers"""
    
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        self.add_css_class("comparison-panel")
        self.set_margin_top(12)
        self.set_margin_bottom(12)
        self.set_margin_start(12)
        self.set_margin_end(12)
        self.set_halign(Gtk.Align.CENTER)
        
        # Panel físico
        physical_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        physical_box.set_halign(Gtk.Align.CENTER)
        
        physical_title = Gtk.Label(label="Físico")
        physical_title.add_css_class("title-4")
        physical_box.append(physical_title)
        
        self.physical_image = Gtk.Picture()
        self.physical_image.set_size_request(120, 160)
        self.physical_image.set_can_shrink(True)
        self.physical_image.set_keep_aspect_ratio(True)
        self.physical_image.add_css_class("cover-image")
        physical_box.append(self.physical_image)
        
        self.physical_label = Gtk.Label()
        self.physical_label.add_css_class("caption")
        self.physical_label.set_justify(Gtk.Justification.CENTER)
        physical_box.append(self.physical_label)
        
        self.append(physical_box)
        
        # Separador
        separator = Gtk.Separator.new(Gtk.Orientation.VERTICAL)
        self.append(separator)
        
        # Panel metadata
        metadata_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        metadata_box.set_halign(Gtk.Align.CENTER)
        
        metadata_title = Gtk.Label(label="Metadata")
        metadata_title.add_css_class("title-4")
        metadata_box.append(metadata_title)
        
        self.metadata_image = Gtk.Picture()
        self.metadata_image.set_size_request(120, 160)
        self.metadata_image.set_can_shrink(True)
        self.metadata_image.set_keep_aspect_ratio(True)
        self.metadata_image.add_css_class("cover-image")
        metadata_box.append(self.metadata_image)
        
        self.metadata_label = Gtk.Label()
        self.metadata_label.add_css_class("caption")
        self.metadata_label.set_justify(Gtk.Justification.CENTER)
        metadata_box.append(self.metadata_label)
        
        self.append(metadata_box)
        
        # Estado inicial
        self.clear_comparison()
        
    def show_physical_comic(self, comicbook):
        """Mostrar comic físico"""
        try:
            cover_path = comicbook.obtener_cover()
            if os.path.exists(cover_path):
                self.physical_image.set_filename(cover_path)
            else:
                self.set_physical_placeholder()
        except:
            self.set_physical_placeholder()
            
        filename = os.path.basename(comicbook.path)
        self.physical_label.set_text(filename)
        
    def show_metadata_comic(self, comicbook_info):
        """Mostrar metadata comic"""
        try:
            if comicbook_info.portadas and len(comicbook_info.portadas) > 0:
                cover_path = comicbook_info.portadas[0].obtener_ruta_local()
                if os.path.exists(cover_path):
                    self.metadata_image.set_filename(cover_path)
                    self.metadata_label.set_text(f"#{comicbook_info.numero} - {comicbook_info.titulo}")
                    return
        except:
            pass
            
        self.set_metadata_placeholder()
        self.metadata_label.set_text(f"#{comicbook_info.numero} - Sin portada")
        
    def set_physical_placeholder(self):
        """Placeholder para físico"""
        try:
            pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 120, 160)
            pixbuf.fill(0x3584E4FF)
            texture = Gdk.Texture.new_for_pixbuf(pixbuf)
            self.physical_image.set_paintable(texture)
        except:
            pass
            
    def set_metadata_placeholder(self):
        """Placeholder para metadata"""
        try:
            pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 120, 160)
            pixbuf.fill(0x33D17AFF)
            texture = Gdk.Texture.new_for_pixbuf(pixbuf)
            self.metadata_image.set_paintable(texture)
        except:
            pass
            
    def clear_comparison(self):
        """Limpiar comparación"""
        self.set_physical_placeholder()
        self.set_metadata_placeholder()
        self.physical_label.set_text("Selecciona un comic físico")
        self.metadata_label.set_text("Selecciona metadata")


class VolumeSelectionRow(Adw.ActionRow):
    """Fila compacta para selección de volumen"""
    
    __gsignals__ = {
        'volume-selected': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
    }
    
    def __init__(self, session):
        super().__init__()
        self.session = session
        self.selected_volume = None
        
        self.set_title("Volumen para catalogación")
        self.set_subtitle("Ningún volumen seleccionado")
        
        # Botón buscar
        search_button = Gtk.Button.new_with_label("Buscar")
        search_button.add_css_class("suggested-action")
        search_button.connect("clicked", self.on_search_volume)
        self.add_suffix(search_button)
        
    def on_search_volume(self, button):
        """Abrir diálogo de búsqueda"""
        dialog = VolumeSearchDialog(self.get_root(), self.session)
        dialog.connect('volume-selected', self.on_volume_selected)
        dialog.present()
        
    def on_volume_selected(self, dialog, volume):
        """Manejar selección de volumen"""
        self.selected_volume = volume
        self.set_subtitle(f"{volume.nombre} ({volume.cantidad_numeros} números)")
        self.emit('volume-selected', volume)
        
    def get_selected_volume(self):
        """Obtener volumen seleccionado"""
        return self.selected_volume


class VolumeSearchDialog(Adw.Window):
    """Diálogo para buscar y seleccionar un volumen"""
    
    __gsignals__ = {
        'volume-selected': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
    }
    
    def __init__(self, parent_window, session):
        super().__init__()
        self.session = session
        
        self.set_title("Buscar volumen")
        self.set_default_size(700, 500)
        self.set_transient_for(parent_window)
        self.set_modal(True)
        
        self.setup_ui()
        self.load_volumes()
        
    def setup_ui(self):
        """Configurar interfaz"""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Header
        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label="Buscar volumen"))
        
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
        
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Buscar por nombre...")
        self.search_entry.set_hexpand(True)
        self.search_entry.connect("search-changed", self.on_search_changed)
        search_box.append(self.search_entry)
        
        main_box.append(search_box)
        
        # Lista de volúmenes
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        self.volumes_list = Gtk.ListBox()
        self.volumes_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.volumes_list.connect("row-activated", self.on_volume_activated)
        self.volumes_list.add_css_class("boxed-list")
        self.volumes_list.set_margin_start(12)
        self.volumes_list.set_margin_end(12)
        self.volumes_list.set_margin_bottom(12)
        
        scrolled.set_child(self.volumes_list)
        main_box.append(scrolled)
        
        self.set_content(main_box)
        
    def load_volumes(self):
        """Cargar lista de volúmenes"""
        try:
            volumes = self.session.query(Volume).order_by(Volume.nombre).limit(1000).all()
            
            for volume in volumes:
                row = Adw.ActionRow()
                row.set_title(volume.nombre)
                row.set_subtitle(f"ID: {volume.id_volume} | Año: {volume.anio_inicio} | {volume.cantidad_numeros} números")
                row.volume = volume
                
                select_button = Gtk.Button.new_with_label("Seleccionar")
                select_button.add_css_class("suggested-action")
                select_button.connect("clicked", self.on_select_volume, volume)
                row.add_suffix(select_button)
                
                self.volumes_list.append(row)
                
        except Exception as e:
            print(f"Error cargando volúmenes: {e}")
            
    def on_search_changed(self, entry):
        """Filtrar volúmenes por búsqueda"""
        search_text = entry.get_text().lower()
        
        row = self.volumes_list.get_first_child()
        while row:
            if hasattr(row, 'volume'):
                visible = search_text in row.volume.nombre.lower()
                row.set_visible(visible)
            row = row.get_next_sibling()
            
    def on_volume_activated(self, list_box, row):
        """Manejar activación de fila"""
        if hasattr(row, 'volume'):
            self.select_volume(row.volume)
            
    def on_select_volume(self, button, volume):
        """Manejar selección de volumen"""
        self.select_volume(volume)
        
    def select_volume(self, volume):
        """Seleccionar volumen y cerrar diálogo"""
        self.emit('volume-selected', volume)
        self.close()


class CatalogingWindow(Adw.Window):
    """Ventana principal de catalogación - versión compacta"""
    
    def __init__(self, parent_window, comicbook_ids, session):
        super().__init__()
        self.parent_window = parent_window
        self.comicbook_ids = comicbook_ids
        self.session = session
        
        # Estado
        self.comicbooks = []
        self.physical_rows = []
        self.metadata_rows = []
        self.selected_volume = None
        self.comicbook_infos = []
        self.selected_physical = None
        self.selected_metadata = None
        
        self.set_title("Catalogar comics")
        self.set_default_size(1200, 700)
        self.set_transient_for(parent_window)
        self.set_modal(True)
        
        self.setup_ui()
        self.load_comicbooks()
        
    def setup_ui(self):
        """Configurar interfaz"""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Header
        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label="Catalogar comics"))
        
        cancel_button = Gtk.Button.new_with_label("Cancelar")
        cancel_button.connect("clicked", lambda b: self.close())
        header.pack_start(cancel_button)
        
        self.process_button = Gtk.Button.new_with_label("Procesar")
        self.process_button.add_css_class("suggested-action")
        self.process_button.connect("clicked", self.on_process_cataloging)
        self.process_button.set_sensitive(False)
        header.pack_end(self.process_button)
        
        main_box.append(header)
        
        # Selección de volumen compacta
        volume_group = Adw.PreferencesGroup()
        self.volume_selector = VolumeSelectionRow(self.session)
        self.volume_selector.connect('volume-selected', self.on_volume_selected)
        volume_group.add(self.volume_selector)
        main_box.append(volume_group)
        
        # Panel principal dividido
        paned = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)
        paned.set_vexpand(True)
        
        # Panel izquierdo - Comics físicos
        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        left_box.set_size_request(400, -1)
        
        # Header izquierdo
        left_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        left_header.set_margin_start(12)
        left_header.set_margin_end(12)
        left_header.set_margin_top(12)
        left_header.set_margin_bottom(8)
        
        left_title = Gtk.Label(label="Comics físicos")
        left_title.add_css_class("title-4")
        left_title.set_hexpand(True)
        left_title.set_halign(Gtk.Align.START)
        left_header.append(left_title)
        
        auto_button = Gtk.Button.new_with_label("Auto números")
        auto_button.connect("clicked", self.on_auto_extract_numbers)
        left_header.append(auto_button)
        
        left_box.append(left_header)
        
        # Lista física
        left_scrolled = Gtk.ScrolledWindow()
        left_scrolled.set_vexpand(True)
        left_scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        self.physical_list = Gtk.ListBox()
        self.physical_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.physical_list.add_css_class("boxed-list")
        self.physical_list.set_margin_start(12)
        self.physical_list.set_margin_end(8)
        
        left_scrolled.set_child(self.physical_list)
        left_box.append(left_scrolled)
        
        paned.set_start_child(left_box)
        
        # Panel derecho dividido verticalmente
        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Metadata arriba
        metadata_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        metadata_header.set_margin_start(8)
        metadata_header.set_margin_end(12)
        metadata_header.set_margin_top(12)
        metadata_header.set_margin_bottom(8)
        
        self.metadata_title = Gtk.Label(label="Metadata (selecciona volumen)")
        self.metadata_title.add_css_class("title-4")
        self.metadata_title.set_hexpand(True)
        self.metadata_title.set_halign(Gtk.Align.START)
        metadata_header.append(self.metadata_title)
        
        right_box.append(metadata_header)
        
        metadata_scrolled = Gtk.ScrolledWindow()
        metadata_scrolled.set_vexpand(True)
        metadata_scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        self.metadata_list = Gtk.ListBox()
        self.metadata_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.metadata_list.add_css_class("boxed-list")
        self.metadata_list.set_margin_start(8)
        self.metadata_list.set_margin_end(12)
        
        metadata_scrolled.set_child(self.metadata_list)
        right_box.append(metadata_scrolled)
        
        # Panel de comparación abajo
        self.comparison_panel = ComparisonPanel()
        right_box.append(self.comparison_panel)
        
        paned.set_end_child(right_box)
        main_box.append(paned)
        
        # Status bar
        self.status_bar = Adw.ActionRow()
        self.status_bar.set_title("Estado")
        self.update_status()
        main_box.append(self.status_bar)
        
        self.set_content(main_box)
        
    def load_comicbooks(self):
        """Cargar comicbooks desde los IDs"""
        try:
            for comic_id in self.comicbook_ids:
                comicbook = self.session.query(Comicbook).get(comic_id)
                if comicbook:
                    self.comicbooks.append(comicbook)
                    
            print(f"Cargados {len(self.comicbooks)} comicbooks para catalogar")
            self.create_physical_rows()
            
        except Exception as e:
            print(f"Error cargando comicbooks: {e}")
            
    def create_physical_rows(self):
        """Crear filas para cada comic físico"""
        for comicbook in self.comicbooks:
            row = PhysicalComicRow(comicbook, self.parent_window.thumbnail_generator)
            row.connect('number-changed', self.on_comic_number_changed)
            row.connect('selected', self.on_physical_selected)
            
            self.physical_rows.append(row)
            self.physical_list.append(row)
            
        self.update_status()
        
    def on_volume_selected(self, volume_selector, volume):
        """Manejar selección de volumen"""
        self.selected_volume = volume
        
        # Cargar ComicbookInfos del volumen
        try:
            self.comicbook_infos = self.session.query(ComicbookInfo).filter(
                ComicbookInfo.id_volume == volume.id_volume
            ).order_by(ComicbookInfo.orden_clasificacion).all()
            
            print(f"Cargados {len(self.comicbook_infos)} ComicbookInfos para el volumen {volume.nombre}")
            
            # Limpiar lista anterior
            while True:
                child = self.metadata_list.get_first_child()
                if child:
                    self.metadata_list.remove(child)
                else:
                    break
                    
            self.metadata_rows = []
            
            # Crear filas de metadata
            for cbi in self.comicbook_infos:
                row = MetadataComicRow(cbi)
                row.connect('selected', self.on_metadata_selected)
                self.metadata_rows.append(row)
                self.metadata_list.append(row)
                
            self.metadata_title.set_text(f"Metadata ({len(self.comicbook_infos)} números)")
            
        except Exception as e:
            print(f"Error cargando ComicbookInfos: {e}")
            self.comicbook_infos = []
            
        self.update_status()
        self.check_process_ready()
        
    def on_comic_number_changed(self, row, number):
        """Manejar cambio de número en un comic físico"""
        # Buscar metadata con el mismo número
        if number and self.comicbook_infos:
            matching_metadata = None
            for metadata_row in self.metadata_rows:
                if str(metadata_row.comicbook_info.numero) == str(number):
                    matching_metadata = metadata_row
                    break
                    
            # Destacar la metadata que coincide
            for metadata_row in self.metadata_rows:
                if metadata_row == matching_metadata:
                    metadata_row.add_css_class("matching-number")
                else:
                    metadata_row.remove_css_class("matching-number")
        else:
            # Quitar destacados
            for metadata_row in self.metadata_rows:
                metadata_row.remove_css_class("matching-number")
                
        self.update_status()
        self.check_process_ready()
        
    def on_physical_selected(self, selected_row):
        """Manejar selección de comic físico"""
        # Limpiar selección anterior
        if self.selected_physical:
            self.selected_physical.set_selected(False)
            
        # Establecer nueva selección
        self.selected_physical = selected_row
        selected_row.set_selected(True)
        
        # Buscar metadata correspondiente por número
        number = selected_row.get_assigned_number()
        matching_metadata = None
        
        if number and self.comicbook_infos:
            for metadata_row in self.metadata_rows:
                if str(metadata_row.comicbook_info.numero) == str(number):
                    matching_metadata = metadata_row
                    break
                    
        # Actualizar comparación
        self.update_comparison(selected_row.comicbook, 
                              matching_metadata.comicbook_info if matching_metadata else None)
        
        # Auto-seleccionar metadata si hay coincidencia
        if matching_metadata:
            self.select_metadata_row(matching_metadata)
            
    def on_metadata_selected(self, selected_row):
        """Manejar selección de metadata"""
        self.select_metadata_row(selected_row)
        
        # Buscar comic físico correspondiente por número
        number = str(selected_row.comicbook_info.numero)
        matching_physical = None
        
        for physical_row in self.physical_rows:
            if physical_row.get_assigned_number() == number:
                matching_physical = physical_row
                break
                
        # Actualizar comparación
        self.update_comparison(matching_physical.comicbook if matching_physical else None,
                              selected_row.comicbook_info)
        
        # Auto-seleccionar físico si hay coincidencia
        if matching_physical:
            self.select_physical_row(matching_physical)
            
    def select_physical_row(self, row):
        """Seleccionar una fila física programáticamente"""
        if self.selected_physical:
            self.selected_physical.set_selected(False)
        self.selected_physical = row
        row.set_selected(True)
        
    def select_metadata_row(self, row):
        """Seleccionar una fila de metadata programáticamente"""
        if self.selected_metadata:
            self.selected_metadata.set_selected(False)
        self.selected_metadata = row
        row.set_selected(True)
        
    def update_comparison(self, comicbook, comicbook_info):
        """Actualizar panel de comparación"""
        if comicbook:
            self.comparison_panel.show_physical_comic(comicbook)
        else:
            self.comparison_panel.set_physical_placeholder()
            self.comparison_panel.physical_label.set_text("Sin comic físico")
            
        if comicbook_info:
            self.comparison_panel.show_metadata_comic(comicbook_info)
        else:
            self.comparison_panel.set_metadata_placeholder()
            self.comparison_panel.metadata_label.set_text("Sin metadata")
            
    def on_auto_extract_numbers(self, button):
        """Extraer números automáticamente de todos los comics"""
        extracted_count = 0
        
        for row in self.physical_rows:
            current_number = row.get_assigned_number()
            if not current_number:  # Solo si no tiene número asignado
                row.on_extract_number(None)
                if row.get_assigned_number():
                    extracted_count += 1
                    
        if extracted_count > 0:
            self.parent_window.show_toast(f"Extraídos {extracted_count} números", "success")
        else:
            self.parent_window.show_toast("No se pudieron extraer números", "warning")
            
        self.update_status()
        
    def update_status(self):
        """Actualizar barra de estado"""
        total_comics = len(self.physical_rows)
        comics_with_numbers = len([row for row in self.physical_rows if row.get_assigned_number()])
        
        # Calcular matches potenciales
        potential_matches = 0
        if self.selected_volume and self.comicbook_infos:
            for row in self.physical_rows:
                number = row.get_assigned_number()
                if number and self.find_comicbook_info_by_number(number):
                    potential_matches += 1
                    
        status_text = f"{total_comics} comics | {comics_with_numbers} con números | {potential_matches} matches"
        
        if self.selected_volume:
            status_text += f" | Volumen: {self.selected_volume.nombre}"
        
        self.status_bar.set_subtitle(status_text)
        
    def check_process_ready(self):
        """Verificar si se puede procesar la catalogación"""
        ready = (
            self.selected_volume is not None and
            len(self.comicbook_infos) > 0 and
            any(row.get_assigned_number() for row in self.physical_rows)
        )
        
        self.process_button.set_sensitive(ready)
        
    def find_comicbook_info_by_number(self, number):
        """Buscar ComicbookInfo por número"""
        for cbi in self.comicbook_infos:
            if str(cbi.numero) == str(number):
                return cbi
        return None
        
    def on_process_cataloging(self, button):
        """Procesar catalogación"""
        if not self.selected_volume:
            self.parent_window.show_toast("No hay volumen seleccionado", "error")
            return
            
        # Recopilar asociaciones a realizar
        associations = []
        skipped_comics = []
        
        for row in self.physical_rows:
            number = row.get_assigned_number()
            if number:
                # Buscar ComicbookInfo correspondiente
                cbi = self.find_comicbook_info_by_number(number)
                if cbi:
                    associations.append({
                        'comicbook': row.comicbook,
                        'comicbook_info': cbi,
                        'number': number
                    })
                else:
                    skipped_comics.append({
                        'comicbook': row.comicbook,
                        'number': number,
                        'reason': f'No existe metadata para el número {number}'
                    })
            else:
                skipped_comics.append({
                    'comicbook': row.comicbook,
                    'number': '',
                    'reason': 'Sin número asignado'
                })
                
        # Mostrar confirmación
        self.show_confirmation_dialog(associations, skipped_comics)
        
    def show_confirmation_dialog(self, associations, skipped_comics):
        """Mostrar diálogo de confirmación antes de procesar"""
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading("Confirmar catalogación")
        
        # Construir mensaje
        message_parts = []
        
        if associations:
            message_parts.append(f"✓ {len(associations)} comics serán catalogados")
            
        if skipped_comics:
            message_parts.append(f"⚠ {len(skipped_comics)} comics serán omitidos:")
            for comic in skipped_comics[:3]:  # Mostrar solo los primeros 3
                filename = os.path.basename(comic['comicbook'].path)
                message_parts.append(f"  • {filename}: {comic['reason']}")
            if len(skipped_comics) > 3:
                message_parts.append(f"  • ... y {len(skipped_comics) - 3} más")
                
        if not associations:
            message_parts.append("No se realizarán asociaciones.")
            
        dialog.set_body("\n".join(message_parts))
        
        dialog.add_response("cancel", "Cancelar")
        if associations:
            dialog.add_response("confirm", "Procesar")
            dialog.set_response_appearance("confirm", Adw.ResponseAppearance.SUGGESTED)
            dialog.set_default_response("confirm")
        else:
            dialog.set_default_response("cancel")
            
        def on_response(dialog, response):
            if response == "confirm" and associations:
                self.execute_associations(associations)
            dialog.close()
            
        dialog.connect("response", on_response)
        dialog.present()
        
    def execute_associations(self, associations):
        """Ejecutar las asociaciones"""
        success_count = 0
        error_count = 0
        errors = []
        
        try:
            for association in associations:
                try:
                    comicbook = association['comicbook']
                    cbi = association['comicbook_info']
                    
                    # Realizar la asociación
                    comicbook.id_comicbook_info = str(cbi.id_comicbook_info)
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    filename = os.path.basename(association['comicbook'].path)
                    errors.append(f"{filename}: {str(e)}")
                    
            # Guardar cambios
            if success_count > 0:
                self.session.commit()
                
            # Mostrar resultado
            self.show_result_dialog(success_count, error_count, errors)
            
        except Exception as e:
            self.parent_window.show_toast(f"Error durante la catalogación: {e}", "error")
            
    def show_result_dialog(self, success_count, error_count, errors):
        """Mostrar resultado de la catalogación"""
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading("Catalogación completada")
        
        # Construir mensaje de resultado
        message_parts = []
        
        if success_count > 0:
            message_parts.append(f"✅ {success_count} comics catalogados exitosamente")
            
        if error_count > 0:
            message_parts.append(f"❌ {error_count} errores:")
            for error in errors[:3]:  # Mostrar solo los primeros 3 errores
                message_parts.append(f"  • {error}")
            if len(errors) > 3:
                message_parts.append(f"  • ... y {len(errors) - 3} errores más")
                
        dialog.set_body("\n".join(message_parts))
        
        dialog.add_response("close", "Cerrar")
        dialog.set_default_response("close")
        
        def on_response(dialog, response):
            dialog.close()
            if success_count > 0:
                # Refrescar la vista principal
                if hasattr(self.parent_window, 'clear_content'):
                    self.parent_window.clear_content()
                    self.parent_window.load_items_batch()
                    
                # Mostrar toast de éxito
                self.parent_window.show_toast(f"{success_count} comics catalogados", "success")
                
                # Cerrar la ventana de catalogación
                self.close()
                
        dialog.connect("response", on_response)
        dialog.present()


# Función para integrar con la ventana principal
def create_cataloging_window(parent_window, comic_ids, session):
    """
    Función factory para crear la ventana de catalogación
    Esta función reemplaza la importación de cataloging_window en Babelcomic4.py
    """
    if not comic_ids:
        parent_window.show_toast("No hay comics seleccionados para catalogar", "warning")
        return None
        
    try:
        window = CatalogingWindow(parent_window, comic_ids, session)
        return window
    except Exception as e:
        parent_window.show_toast(f"Error creando ventana de catalogación: {e}", "error")
        print(f"Error creando CatalogingWindow: {e}")
        return None


# CSS adicional para los nuevos estilos
ADDITIONAL_CSS = """
.selected-row {
    background-color: alpha(@accent_bg_color, 0.2);
    border-left: 3px solid @accent_bg_color;
}

.matching-number {
    background-color: alpha(@success_color, 0.1);
    border-left: 3px solid @success_color;
}

.comparison-panel {
    background-color: @view_bg_color;
    border: 1px solid @borders;
    border-radius: 12px;
    padding: 16px;
}
"""

# Ejemplo de integración en Babelcomic4.py:
"""
# En lugar de:
# from cataloging_window import CatalogingWindow

# Usar:
# from new_cataloging_window import create_cataloging_window

# Y en el método open_cataloging_window:
def open_cataloging_window(self, comic_ids):
    from new_cataloging_window import create_cataloging_window
    window = create_cataloging_window(self, comic_ids, self.session)
    if window:
        window.present()
"",         # Comic 123
            r'(\d+)\.cb[rz]#!/usr/bin/env python3
""
Nueva ventana de catalogación desde cero - Versión compacta con comparación
Permite seleccionar un volumen y asignar números a comics físicos para hacer matching con metadata
"""

import gi
import os
import re
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GObject, Pango, GdkPixbuf, Gdk, GLib
from entidades.comicbook_model import Comicbook
from entidades.volume_model import Volume
from entidades.comicbook_info_model import ComicbookInfo
from comic_cards import ComicCard


class PhysicalComicRow(Gtk.ListBoxRow):
    """Fila que representa un comic físico con su número asignado"""
    
    __gsignals__ = {
        'number-changed': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'selected': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }
    
    def __init__(self, comicbook, thumbnail_generator):
        super().__init__()
        self.comicbook = comicbook
        self.thumbnail_generator = thumbnail_generator
        self.assigned_number = ""
        
        # Crear contenido de la fila
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        main_box.set_margin_start(8)
        main_box.set_margin_end(8)
        main_box.set_margin_top(4)
        main_box.set_margin_bottom(4)
        
        # Thumbnail pequeño
        self.image = Gtk.Picture()
        self.image.set_size_request(32, 40)
        self.image.set_can_shrink(True)
        self.image.set_keep_aspect_ratio(True)
        self.image.add_css_class("cover-image")
        self.load_thumbnail()
        main_box.append(self.image)
        
        # Info del comic
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        info_box.set_hexpand(True)
        info_box.set_valign(Gtk.Align.CENTER)
        
        # Nombre del archivo
        filename = os.path.basename(self.comicbook.path)
        self.name_label = Gtk.Label(label=filename)
        self.name_label.set_wrap(True)
        self.name_label.set_lines(1)
        self.name_label.set_ellipsize(Pango.EllipsizeMode.END)
        self.name_label.set_halign(Gtk.Align.START)
        self.name_label.add_css_class("body")
        info_box.append(self.name_label)
        
        # ID
        id_label = Gtk.Label(label=f"ID: {self.comicbook.id_comicbook}")
        id_label.add_css_class("dim-label")
        id_label.add_css_class("caption")
        id_label.set_halign(Gtk.Align.START)
        info_box.append(id_label)
        
        main_box.append(info_box)
        
        # Campo número
        number_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        
        self.number_entry = Gtk.Entry()
        self.number_entry.set_placeholder_text("Núm")
        self.number_entry.set_size_request(60, -1)
        self.number_entry.connect("changed", self.on_number_changed)
        number_box.append(self.number_entry)
        
        # Botón extraer
        extract_button = Gtk.Button()
        extract_button.set_icon_name("find-location-symbolic")
        extract_button.set_tooltip_text("Extraer del nombre")
        extract_button.add_css_class("flat")
        extract_button.connect("clicked", self.on_extract_number)
        number_box.append(extract_button)
        
        main_box.append(number_box)
        
        # Status
        self.status_icon = Gtk.Image()
        self.status_icon.set_from_icon_name("dialog-question-symbolic")
        main_box.append(self.status_icon)
        
        self.set_child(main_box)
        
        # Click gesture para selección
        click = Gtk.GestureClick()
        click.connect("pressed", self.on_clicked)
        self.add_controller(click)
        
    def load_thumbnail(self):
        """Cargar thumbnail del comic"""
        try:
            cover_path = self.comicbook.obtener_cover()
            if os.path.exists(cover_path):
                self.image.set_filename(cover_path)
            else:
                self.set_placeholder_image()
        except:
            self.set_placeholder_image()
            
    def set_placeholder_image(self):
        """Establecer imagen placeholder"""
        try:
            pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 32, 40)
            pixbuf.fill(0x3584E4FF)
            texture = Gdk.Texture.new_for_pixbuf(pixbuf)
            self.image.set_paintable(texture)
        except:
            pass
            
    def on_clicked(self, gesture, n_press, x, y):
        """Manejar click en la fila"""
        self.emit('selected')
        
    def on_number_changed(self, entry):
        """Manejar cambio en el número"""
        self.assigned_number = entry.get_text().strip()
        self.update_status()
        self.emit('number-changed', self.assigned_number)
        
    def on_extract_number(self, button):
        """Extraer número automáticamente del nombre del archivo"""
        filename = os.path.basename(self.comicbook.path)
        number = self.extract_number_from_filename(filename)
        
        if number:
            self.number_entry.set_text(number)
        
    def extract_number_from_filename(self, filename):
        """Extraer número del filename usando patrones comunes"""
        patterns = [
            r'#(\d+)',           # Comic #123
            r'\s(\d+)\s',        # Comic 123 (2023)
            r'\s(\d+)\.',        # Comic 123.cbr
            r'\s(\d+)$',         # Comic 123
            r'(\d+)\.cb[rz]$',   # 123.cbr
            r'(\d+)',            # Cualquier número
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                return match.group(1)
        return None
        
    def get_assigned_number(self):
        """Obtener número asignado"""
        return self.assigned_number
        
    def set_assigned_number(self, number):
        """Establecer número asignado"""
        self.assigned_number = str(number) if number else ""
        self.number_entry.set_text(self.assigned_number)
        
    def update_status(self):
        """Actualizar status del matching"""
        if self.assigned_number:
            self.status_icon.set_icon_name("emblem-ok-symbolic")
            self.status_icon.add_css_class("success")
        else:
            self.status_icon.set_icon_name("dialog-question-symbolic")
            self.status_icon.remove_css_class("success")
            
    def set_selected(self, selected):
        """Marcar como seleccionado"""
        if selected:
            self.add_css_class("selected-row")
        else:
            self.remove_css_class("selected-row")


class MetadataComicRow(Gtk.ListBoxRow):
    """Fila que representa un ComicbookInfo (metadata)"""
    
    __gsignals__ = {
        'selected': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }
    
    def __init__(self, comicbook_info):
        super().__init__()
        self.comicbook_info = comicbook_info
        
        # Crear contenido de la fila
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        main_box.set_margin_start(8)
        main_box.set_margin_end(8)
        main_box.set_margin_top(4)
        main_box.set_margin_bottom(4)
        
        # Thumbnail de la portada
        self.image = Gtk.Picture()
        self.image.set_size_request(32, 40)
        self.image.set_can_shrink(True)
        self.image.set_keep_aspect_ratio(True)
        self.image.add_css_class("cover-image")
        self.load_cover()
        main_box.append(self.image)
        
        # Info del comic
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        info_box.set_hexpand(True)
        info_box.set_valign(Gtk.Align.CENTER)
        
        # Título y número
        title_text = f"#{comicbook_info.numero}"
        if comicbook_info.titulo:
            title_text += f" - {comicbook_info.titulo}"
        
        self.title_label = Gtk.Label(label=title_text)
        self.title_label.set_wrap(True)
        self.title_label.set_lines(1)
        self.title_label.set_ellipsize(Pango.EllipsizeMode.END)
        self.title_label.set_halign(Gtk.Align.START)
        self.title_label.add_css_class("body")
        info_box.append(self.title_label)
        
        # Fecha
        if comicbook_info.fecha_tapa:
            date_label = Gtk.Label(label=f"Fecha: {comicbook_info.fecha_tapa}")
            date_label.add_css_class("dim-label")
            date_label.add_css_class("caption")
            date_label.set_halign(Gtk.Align.START)
            info_box.append(date_label)
        
        main_box.append(info_box)
        
        # Número destacado
        number_label = Gtk.Label(label=str(comicbook_info.numero))
        number_label.add_css_class("title-2")
        number_label.add_css_class("accent")
        main_box.append(number_label)
        
        self.set_child(main_box)
        
        # Click gesture
        click = Gtk.GestureClick()
        click.connect("pressed", self.on_clicked)
        self.add_controller(click)
        
    def load_cover(self):
        """Cargar portada del ComicbookInfo"""
        try:
            if self.comicbook_info.portadas and len(self.comicbook_info.portadas) > 0:
                cover_path = self.comicbook_info.portadas[0].obtener_ruta_local()
                if os.path.exists(cover_path):
                    self.image.set_filename(cover_path)
                    return
        except:
            pass
            
        # Placeholder
        try:
            pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 32, 40)
            pixbuf.fill(0x33D17AFF)  # Verde
            texture = Gdk.Texture.new_for_pixbuf(pixbuf)
            self.image.set_paintable(texture)
        except:
            pass
            
    def on_clicked(self, gesture, n_press, x, y):
        """Manejar click en la fila"""
        self.emit('selected')
        
    def set_selected(self, selected):
        """Marcar como seleccionado"""
        if selected:
            self.add_css_class("selected-row")
        else:
            self.remove_css_class("selected-row")


class ComparisonPanel(Gtk.Box):
    """Panel de comparación de covers"""
    
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        self.add_css_class("comparison-panel")
        self.set_margin_top(12)
        self.set_margin_bottom(12)
        self.set_margin_start(12)
        self.set_margin_end(12)
        self.set_halign(Gtk.Align.CENTER)
        
        # Panel físico
        physical_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        physical_box.set_halign(Gtk.Align.CENTER)
        
        physical_title = Gtk.Label(label="Físico")
        physical_title.add_css_class("title-4")
        physical_box.append(physical_title)
        
        self.physical_image = Gtk.Picture()
        self.physical_image.set_size_request(120, 160)
        self.physical_image.set_can_shrink(True)
        self.physical_image.set_keep_aspect_ratio(True)
        self.physical_image.add_css_class("cover-image")
        physical_box.append(self.physical_image)
        
        self.physical_label = Gtk.Label()
        self.physical_label.add_css_class("caption")
        self.physical_label.set_justify(Gtk.Justification.CENTER)
        physical_box.append(self.physical_label)
        
        self.append(physical_box)
        
        # Separador
        separator = Gtk.Separator.new(Gtk.Orientation.VERTICAL)
        self.append(separator)
        
        # Panel metadata
        metadata_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        metadata_box.set_halign(Gtk.Align.CENTER)
        
        metadata_title = Gtk.Label(label="Metadata")
        metadata_title.add_css_class("title-4")
        metadata_box.append(metadata_title)
        
        self.metadata_image = Gtk.Picture()
        self.metadata_image.set_size_request(120, 160)
        self.metadata_image.set_can_shrink(True)
        self.metadata_image.set_keep_aspect_ratio(True)
        self.metadata_image.add_css_class("cover-image")
        metadata_box.append(self.metadata_image)
        
        self.metadata_label = Gtk.Label()
        self.metadata_label.add_css_class("caption")
        self.metadata_label.set_justify(Gtk.Justification.CENTER)
        metadata_box.append(self.metadata_label)
        
        self.append(metadata_box)
        
        # Estado inicial
        self.clear_comparison()
        
    def show_physical_comic(self, comicbook):
        """Mostrar comic físico"""
        try:
            cover_path = comicbook.obtener_cover()
            if os.path.exists(cover_path):
                self.physical_image.set_filename(cover_path)
            else:
                self.set_physical_placeholder()
        except:
            self.set_physical_placeholder()
            
        filename = os.path.basename(comicbook.path)
        self.physical_label.set_text(filename)
        
    def show_metadata_comic(self, comicbook_info):
        """Mostrar metadata comic"""
        try:
            if comicbook_info.portadas and len(comicbook_info.portadas) > 0:
                cover_path = comicbook_info.portadas[0].obtener_ruta_local()
                if os.path.exists(cover_path):
                    self.metadata_image.set_filename(cover_path)
                    self.metadata_label.set_text(f"#{comicbook_info.numero} - {comicbook_info.titulo}")
                    return
        except:
            pass
            
        self.set_metadata_placeholder()
        self.metadata_label.set_text(f"#{comicbook_info.numero} - Sin portada")
        
    def set_physical_placeholder(self):
        """Placeholder para físico"""
        try:
            pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 120, 160)
            pixbuf.fill(0x3584E4FF)
            texture = Gdk.Texture.new_for_pixbuf(pixbuf)
            self.physical_image.set_paintable(texture)
        except:
            pass
            
    def set_metadata_placeholder(self):
        """Placeholder para metadata"""
        try:
            pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 120, 160)
            pixbuf.fill(0x33D17AFF)
            texture = Gdk.Texture.new_for_pixbuf(pixbuf)
            self.metadata_image.set_paintable(texture)
        except:
            pass
            
    def clear_comparison(self):
        """Limpiar comparación"""
        self.set_physical_placeholder()
        self.set_metadata_placeholder()
        self.physical_label.set_text("Selecciona un comic físico")
        self.metadata_label.set_text("Selecciona metadata")


class VolumeSelectionRow(Adw.ActionRow):
    """Fila compacta para selección de volumen"""
    
    __gsignals__ = {
        'volume-selected': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
    }
    
    def __init__(self, session):
        super().__init__()
        self.session = session
        self.selected_volume = None
        
        self.set_title("Volumen para catalogación")
        self.set_subtitle("Ningún volumen seleccionado")
        
        # Botón buscar
        search_button = Gtk.Button.new_with_label("Buscar")
        search_button.add_css_class("suggested-action")
        search_button.connect("clicked", self.on_search_volume)
        self.add_suffix(search_button)
        
    def on_search_volume(self, button):
        """Abrir diálogo de búsqueda"""
        dialog = VolumeSearchDialog(self.get_root(), self.session)
        dialog.connect('volume-selected', self.on_volume_selected)
        dialog.present()
        
    def on_volume_selected(self, dialog, volume):
        """Manejar selección de volumen"""
        self.selected_volume = volume
        self.set_subtitle(f"{volume.nombre} ({volume.cantidad_numeros} números)")
        self.emit('volume-selected', volume)
        
    def get_selected_volume(self):
        """Obtener volumen seleccionado"""
        return self.selected_volume


class VolumeSearchDialog(Adw.Window):
    """Diálogo para buscar y seleccionar un volumen"""
    
    __gsignals__ = {
        'volume-selected': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
    }
    
    def __init__(self, parent_window, session):
        super().__init__()
        self.session = session
        
        self.set_title("Buscar volumen")
        self.set_default_size(700, 500)
        self.set_transient_for(parent_window)
        self.set_modal(True)
        
        self.setup_ui()
        self.load_volumes()
        
    def setup_ui(self):
        """Configurar interfaz"""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Header
        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label="Buscar volumen"))
        
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
        
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Buscar por nombre...")
        self.search_entry.set_hexpand(True)
        self.search_entry.connect("search-changed", self.on_search_changed)
        search_box.append(self.search_entry)
        
        main_box.append(search_box)
        
        # Lista de volúmenes
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        self.volumes_list = Gtk.ListBox()
        self.volumes_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.volumes_list.connect("row-activated", self.on_volume_activated)
        self.volumes_list.add_css_class("boxed-list")
        self.volumes_list.set_margin_start(12)
        self.volumes_list.set_margin_end(12)
        self.volumes_list.set_margin_bottom(12)
        
        scrolled.set_child(self.volumes_list)
        main_box.append(scrolled)
        
        self.set_content(main_box)
        
    def load_volumes(self):
        """Cargar lista de volúmenes"""
        try:
            volumes = self.session.query(Volume).order_by(Volume.nombre).limit(1000).all()
            
            for volume in volumes:
                row = Adw.ActionRow()
                row.set_title(volume.nombre)
                row.set_subtitle(f"ID: {volume.id_volume} | Año: {volume.anio_inicio} | {volume.cantidad_numeros} números")
                row.volume = volume
                
                select_button = Gtk.Button.new_with_label("Seleccionar")
                select_button.add_css_class("suggested-action")
                select_button.connect("clicked", self.on_select_volume, volume)
                row.add_suffix(select_button)
                
                self.volumes_list.append(row)
                
        except Exception as e:
            print(f"Error cargando volúmenes: {e}")
            
    def on_search_changed(self, entry):
        """Filtrar volúmenes por búsqueda"""
        search_text = entry.get_text().lower()
        
        row = self.volumes_list.get_first_child()
        while row:
            if hasattr(row, 'volume'):
                visible = search_text in row.volume.nombre.lower()
                row.set_visible(visible)
            row = row.get_next_sibling()
            
    def on_volume_activated(self, list_box, row):
        """Manejar activación de fila"""
        if hasattr(row, 'volume'):
            self.select_volume(row.volume)
            
    def on_select_volume(self, button, volume):
        """Manejar selección de volumen"""
        self.select_volume(volume)
        
    def select_volume(self, volume):
        """Seleccionar volumen y cerrar diálogo"""
        self.emit('volume-selected', volume)
        self.close()


class CatalogingWindow(Adw.Window):
    """Ventana principal de catalogación - versión compacta"""
    
    def __init__(self, parent_window, comicbook_ids, session):
        super().__init__()
        self.parent_window = parent_window
        self.comicbook_ids = comicbook_ids
        self.session = session
        
        # Estado
        self.comicbooks = []
        self.physical_rows = []
        self.metadata_rows = []
        self.selected_volume = None
        self.comicbook_infos = []
        self.selected_physical = None
        self.selected_metadata = None
        
        self.set_title("Catalogar comics")
        self.set_default_size(1200, 700)
        self.set_transient_for(parent_window)
        self.set_modal(True)
        
        self.setup_ui()
        self.load_comicbooks()
        
    def setup_ui(self):
        """Configurar interfaz"""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Header
        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label="Catalogar comics"))
        
        cancel_button = Gtk.Button.new_with_label("Cancelar")
        cancel_button.connect("clicked", lambda b: self.close())
        header.pack_start(cancel_button)
        
        self.process_button = Gtk.Button.new_with_label("Procesar")
        self.process_button.add_css_class("suggested-action")
        self.process_button.connect("clicked", self.on_process_cataloging)
        self.process_button.set_sensitive(False)
        header.pack_end(self.process_button)
        
        main_box.append(header)
        
        # Selección de volumen compacta
        volume_group = Adw.PreferencesGroup()
        self.volume_selector = VolumeSelectionRow(self.session)
        self.volume_selector.connect('volume-selected', self.on_volume_selected)
        volume_group.add(self.volume_selector)
        main_box.append(volume_group)
        
        # Panel principal dividido
        paned = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)
        paned.set_vexpand(True)
        
        # Panel izquierdo - Comics físicos
        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        left_box.set_size_request(400, -1)
        
        # Header izquierdo
        left_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        left_header.set_margin_start(12)
        left_header.set_margin_end(12)
        left_header.set_margin_top(12)
        left_header.set_margin_bottom(8)
        
        left_title = Gtk.Label(label="Comics físicos")
        left_title.add_css_class("title-4")
        left_title.set_hexpand(True)
        left_title.set_halign(Gtk.Align.START)
        left_header.append(left_title)
        
        auto_button = Gtk.Button.new_with_label("Auto números")
        auto_button.connect("clicked", self.on_auto_extract_numbers)
        left_header.append(auto_button)
        
        left_box.append(left_header)
        
        # Lista física
        left_scrolled = Gtk.ScrolledWindow()
        left_scrolled.set_vexpand(True)
        left_scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        self.physical_list = Gtk.ListBox()
        self.physical_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.physical_list.add_css_class("boxed-list")
        self.physical_list.set_margin_start(12)
        self.physical_list.set_margin_end(8)
        
        left_scrolled.set_child(self.physical_list)
        left_box.append(left_scrolled)
        
        paned.set_start_child(left_box)
        
        # Panel derecho dividido verticalmente
        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Metadata arriba
        metadata_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        metadata_header.set_margin_start(8)
        metadata_header.set_margin_end(12)
        metadata_header.set_margin_top(12)
        metadata_header.set_margin_bottom(8)
        
        self.metadata_title = Gtk.Label(label="Metadata (selecciona volumen)")
        self.metadata_title.add_css_class("title-4")
        self.metadata_title.set_hexpand(True)
        self.metadata_title.set_halign(Gtk.Align.START)
        metadata_header.append(self.metadata_title)
        
        right_box.append(metadata_header)
        
        metadata_scrolled = Gtk.ScrolledWindow()
        metadata_scrolled.set_vexpand(True)
        metadata_scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        self.metadata_list = Gtk.ListBox()
        self.metadata_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.metadata_list.add_css_class("boxed-list")
        self.metadata_list.set_margin_start(8)
        self.metadata_list.set_margin_end(12)
        
        metadata_scrolled.set_child(self.metadata_list)
        right_box.append(metadata_scrolled)
        
        # Panel de comparación abajo
        self.comparison_panel = ComparisonPanel()
        right_box.append(self.comparison_panel)
        
        paned.set_end_child(right_box)
        main_box.append(paned)
        
        # Status bar
        self.status_bar = Adw.ActionRow()
        self.status_bar.set_title("Estado")
        self.update_status()
        main_box.append(self.status_bar)
        
        self.set_content(main_box)
        
    def load_comicbooks(self):
        """Cargar comicbooks desde los IDs"""
        try:
            for comic_id in self.comicbook_ids:
                comicbook = self.session.query(Comicbook).get(comic_id)
                if comicbook:
                    self.comicbooks.append(comicbook)
                    
            print(f"Cargados {len(self.comicbooks)} comicbooks para catalogar")
            self.create_physical_rows()
            
        except Exception as e:
            print(f"Error cargando comicbooks: {e}")
            
    def create_physical_rows(self):
        """Crear filas para cada comic físico"""
        for comicbook in self.comicbooks:
            row = PhysicalComicRow(comicbook, self.parent_window.thumbnail_generator)
            row.connect('number-changed', self.on_comic_number_changed)
            row.connect('selected', self.on_physical_selected)
            
            self.physical_rows.append(row)
            self.physical_list.append(row)
            
        self.update_status()
        
    def on_volume_selected(self, volume_selector, volume):
        """Manejar selección de volumen"""
        self.selected_volume = volume
        
        # Cargar ComicbookInfos del volumen
        try:
            self.comicbook_infos = self.session.query(ComicbookInfo).filter(
                ComicbookInfo.id_volume == volume.id_volume
            ).order_by(ComicbookInfo.orden_clasificacion).all()
            
            print(f"Cargados {len(self.comicbook_infos)} ComicbookInfos para el volumen {volume.nombre}")
            
            # Limpiar lista anterior
            while True:
                child = self.metadata_list.get_first_child()
                if child:
                    self.metadata_list.remove(child)
                else:
                    break
                    
            self.metadata_rows = []
            
            # Crear filas de metadata
            for cbi in self.comicbook_infos:
                row = MetadataComicRow(cbi)
                row.connect('selected', self.on_metadata_selected)
                self.metadata_rows.append(row)
                self.metadata_list.append(row)
                
            self.metadata_title.set_text(f"Metadata ({len(self.comicbook_infos)} números)")
            
        except Exception as e:
            print(f"Error cargando ComicbookInfos: {e}")
            self.comicbook_infos = []
            
        self.update_status()
        self.check_process_ready()
        
    def on_comic_number_changed(self, row, number):
        """Manejar cambio de número en un comic físico"""
        # Buscar metadata con el mismo número
        if number and self.comicbook_infos:
            matching_metadata = None
            for metadata_row in self.metadata_rows:
                if str(metadata_row.comicbook_info.numero) == str(number):
                    matching_metadata = metadata_row
                    break
                    
            # Destacar la metadata que coincide
            for metadata_row in self.metadata_rows:
                if metadata_row == matching_metadata:
                    metadata_row.add_css_class("matching-number")
                else:
                    metadata_row.remove_css_class("matching-number")
        else:
            # Quitar destacados
            for metadata_row in self.metadata_rows:
                metadata_row.remove_css_class("matching-number")
                
        self.update_status()
        self.check_process_ready()
        
    def on_physical_selected(self, selected_row):
        """Manejar selección de comic físico"""
        # Limpiar selección anterior
        if self.selected_physical:
            self.selected_physical.set_selected(False)
            
        # Establecer nueva selección
        self.selected_physical = selected_row
        selected_row.set_selected(True)
        
        # Buscar metadata correspondiente por número
        number = selected_row.get_assigned_number()
        matching_metadata = None
        
        if number and self.comicbook_infos:
            for metadata_row in self.metadata_rows:
                if str(metadata_row.comicbook_info.numero) == str(number):
                    matching_metadata = metadata_row
                    break
                    
        # Actualizar comparación
        self.update_comparison(selected_row.comicbook, 
                              matching_metadata.comicbook_info if matching_metadata else None)
        
        # Auto-seleccionar metadata si hay coincidencia
        if matching_metadata:
            self.select_metadata_row(matching_metadata)
            
    def on_metadata_selected(self, selected_row):
        """Manejar selección de metadata"""
        self.select_metadata_row(selected_row)
        
        # Buscar comic físico correspondiente por número
        number = str(selected_row.comicbook_info.numero)
        matching_physical = None
        
        for physical_row in self.physical_rows:
            if physical_row.get_assigned_number() == number:
                matching_physical = physical_row
                break
                
        # Actualizar comparación
        self.update_comparison(matching_physical.comicbook if matching_physical else None,
                              selected_row.comicbook_info)
        
        # Auto-seleccionar físico si hay coincidencia
        if matching_physical:
            self.select_physical_row(matching_physical)
            
    def select_physical_row(self, row):
        """Seleccionar una fila física programáticamente"""
        if self.selected_physical:
            self.selected_physical.set_selected(False)
        self.selected_physical = row
        row.set_selected(True)
        
    def select_metadata_row(self, row):
        """Seleccionar una fila de metadata programáticamente"""
        if self.selected_metadata:
            self.selected_metadata.set_selected(False)
        self.selected_metadata = row
        row.set_selected(True)
        
    def update_comparison(self, comicbook, comicbook_info):
        """Actualizar panel de comparación"""
        if comicbook:
            self.comparison_panel.show_physical_comic(comicbook)
        else:
            self.comparison_panel.set_physical_placeholder()
            self.comparison_panel.physical_label.set_text("Sin comic físico")
            
        if comicbook_info:
            self.comparison_panel.show_metadata_comic(comicbook_info)
        else:
            self.comparison_panel.set_metadata_placeholder()
            self.comparison_panel.metadata_label.set_text("Sin metadata")
            
    def on_auto_extract_numbers(self, button):
        """Extraer números automáticamente de todos los comics"""
        extracted_count = 0
        
        for row in self.physical_rows:
            current_number = row.get_assigned_number()
            if not current_number:  # Solo si no tiene número asignado
                row.on_extract_number(None)
                if row.get_assigned_number():
                    extracted_count += 1
                    
        if extracted_count > 0:
            self.parent_window.show_toast(f"Extraídos {extracted_count} números", "success")
        else:
            self.parent_window.show_toast("No se pudieron extraer números", "warning")
            
        self.update_status()
        
    def update_status(self):
        """Actualizar barra de estado"""
        total_comics = len(self.physical_rows)
        comics_with_numbers = len([row for row in self.physical_rows if row.get_assigned_number()])
        
        # Calcular matches potenciales
        potential_matches = 0
        if self.selected_volume and self.comicbook_infos:
            for row in self.physical_rows:
                number = row.get_assigned_number()
                if number and self.find_comicbook_info_by_number(number):
                    potential_matches += 1
                    
        status_text = f"{total_comics} comics | {comics_with_numbers} con números | {potential_matches} matches"
        
        if self.selected_volume:
            status_text += f" | Volumen: {self.selected_volume.nombre}"
        
        self.status_bar.set_subtitle(status_text)
        
    def check_process_ready(self):
        """Verificar si se puede procesar la catalogación"""
        ready = (
            self.selected_volume is not None and
            len(self.comicbook_infos) > 0 and
            any(row.get_assigned_number() for row in self.physical_rows)
        )
        
        self.process_button.set_sensitive(ready)
        
    def find_comicbook_info_by_number(self, number):
        """Buscar ComicbookInfo por número"""
        for cbi in self.comicbook_infos:
            if str(cbi.numero) == str(number):
                return cbi
        return None
        
    def on_process_cataloging(self, button):
        """Procesar catalogación"""
        if not self.selected_volume:
            self.parent_window.show_toast("No hay volumen seleccionado", "error")
            return
            
        # Recopilar asociaciones a realizar
        associations = []
        skipped_comics = []
        
        for row in self.physical_rows:
            number = row.get_assigned_number()
            if number:
                # Buscar ComicbookInfo correspondiente
                cbi = self.find_comicbook_info_by_number(number)
                if cbi:
                    associations.append({
                        'comicbook': row.comicbook,
                        'comicbook_info': cbi,
                        'number': number
                    })
                else:
                    skipped_comics.append({
                        'comicbook': row.comicbook,
                        'number': number,
                        'reason': f'No existe metadata para el número {number}'
                    })
            else:
                skipped_comics.append({
                    'comicbook': row.comicbook,
                    'number': '',
                    'reason': 'Sin número asignado'
                })
                
        # Mostrar confirmación
        self.show_confirmation_dialog(associations, skipped_comics)
        
    def show_confirmation_dialog(self, associations, skipped_comics):
        """Mostrar diálogo de confirmación antes de procesar"""
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading("Confirmar catalogación")
        
        # Construir mensaje
        message_parts = []
        
        if associations:
            message_parts.append(f"✓ {len(associations)} comics serán catalogados")
            
        if skipped_comics:
            message_parts.append(f"⚠ {len(skipped_comics)} comics serán omitidos:")
            for comic in skipped_comics[:3]:  # Mostrar solo los primeros 3
                filename = os.path.basename(comic['comicbook'].path)
                message_parts.append(f"  • {filename}: {comic['reason']}")
            if len(skipped_comics) > 3:
                message_parts.append(f"  • ... y {len(skipped_comics) - 3} más")
                
        if not associations:
            message_parts.append("No se realizarán asociaciones.")
            
        dialog.set_body("\n".join(message_parts))
        
        dialog.add_response("cancel", "Cancelar")
        if associations:
            dialog.add_response("confirm", "Procesar")
            dialog.set_response_appearance("confirm", Adw.ResponseAppearance.SUGGESTED)
            dialog.set_default_response("confirm")
        else:
            dialog.set_default_response("cancel")
            
        def on_response(dialog, response):
            if response == "confirm" and associations:
                self.execute_associations(associations)
            dialog.close()
            
        dialog.connect("response", on_response)
        dialog.present()
        
    def execute_associations(self, associations):
        """Ejecutar las asociaciones"""
        success_count = 0
        error_count = 0
        errors = []
        
        try:
            for association in associations:
                try:
                    comicbook = association['comicbook']
                    cbi = association['comicbook_info']
                    
                    # Realizar la asociación
                    comicbook.id_comicbook_info = str(cbi.id_comicbook_info)
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    filename = os.path.basename(association['comicbook'].path)
                    errors.append(f"{filename}: {str(e)}")
                    
            # Guardar cambios
            if success_count > 0:
                self.session.commit()
                
            # Mostrar resultado
            self.show_result_dialog(success_count, error_count, errors)
            
        except Exception as e:
            self.parent_window.show_toast(f"Error durante la catalogación: {e}", "error")
            
    def show_result_dialog(self, success_count, error_count, errors):
        """Mostrar resultado de la catalogación"""
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading("Catalogación completada")
        
        # Construir mensaje de resultado
        message_parts = []
        
        if success_count > 0:
            message_parts.append(f"✅ {success_count} comics catalogados exitosamente")
            
        if error_count > 0:
            message_parts.append(f"❌ {error_count} errores:")
            for error in errors[:3]:  # Mostrar solo los primeros 3 errores
                message_parts.append(f"  • {error}")
            if len(errors) > 3:
                message_parts.append(f"  • ... y {len(errors) - 3} errores más")
                
        dialog.set_body("\n".join(message_parts))
        
        dialog.add_response("close", "Cerrar")
        dialog.set_default_response("close")
        
        def on_response(dialog, response):
            dialog.close()
            if success_count > 0:
                # Refrescar la vista principal
                if hasattr(self.parent_window, 'clear_content'):
                    self.parent_window.clear_content()
                    self.parent_window.load_items_batch()
                    
                # Mostrar toast de éxito
                self.parent_window.show_toast(f"{success_count} comics catalogados", "success")
                
                # Cerrar la ventana de catalogación
                self.close()
                
        dialog.connect("response", on_response)
        dialog.present()


# Función para integrar con la ventana principal
def create_cataloging_window(parent_window, comic_ids, session):
    """
    Función factory para crear la ventana de catalogación
    Esta función reemplaza la importación de cataloging_window en Babelcomic4.py
    """
    if not comic_ids:
        parent_window.show_toast("No hay comics seleccionados para catalogar", "warning")
        return None
        
    try:
        window = CatalogingWindow(parent_window, comic_ids, session)
        return window
    except Exception as e:
        parent_window.show_toast(f"Error creando ventana de catalogación: {e}", "error")
        print(f"Error creando CatalogingWindow: {e}")
        return None


# CSS adicional para los nuevos estilos
ADDITIONAL_CSS = """
.selected-row {
    background-color: alpha(@accent_bg_color, 0.2);
    border-left: 3px solid @accent_bg_color;
}

.matching-number {
    background-color: alpha(@success_color, 0.1);
    border-left: 3px solid @success_color;
}

.comparison-panel {
    background-color: @view_bg_color;
    border: 1px solid @borders;
    border-radius: 12px;
    padding: 16px;
}
"""

