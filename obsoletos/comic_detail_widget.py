#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GdkPixbuf, Gdk, GLib, Gio, GObject
import os
import datetime
import platform
import subprocess


class ComicDetailDialog(Adw.Dialog):
    """Diálogo para mostrar detalles completos de un comic/volumen/editorial"""
    
    def __init__(self, parent_window, item_data, item_type="comic"):
        super().__init__()
        self.parent_window = parent_window
        self.item_data = item_data
        self.item_type = item_type
        
        self.set_title("Detalles")
        self.set_default_size(700, 500)
        
        self.create_content()
        
    def create_content(self):
        """Crear el contenido del diálogo"""
        # Contenedor principal
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Header
        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label=self.get_title_text()))
        
        close_button = Gtk.Button.new_with_label("Cerrar")
        close_button.connect("clicked", lambda b: self.close())
        header.pack_start(close_button)
        
        # Botón editar
        if self.item_type == "comic":
            edit_button = Gtk.Button.new_with_label("Editar")
            edit_button.add_css_class("suggested-action")
            edit_button.connect("clicked", self.on_edit_clicked)
            header.pack_end(edit_button)
        
        main_box.append(header)
        
        # Contenido scrollable
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=24)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        
        # Panel izquierdo: imagen y acciones
        left_panel = self.create_left_panel()
        content_box.append(left_panel)
        
        # Panel derecho: información
        right_panel = self.create_right_panel()
        content_box.append(right_panel)
        
        scrolled.set_child(content_box)
        main_box.append(scrolled)
        
        self.set_child(main_box)
        
    def get_title_text(self):
        """Obtener el título según el tipo de item"""
        if self.item_type == "comic":
            return getattr(self.item_data, 'nombre_archivo', f"Comic {self.item_data.id_comicbook}")
        elif self.item_type == "volume":
            return self.item_data.nombre
        elif self.item_type == "publisher":
            return self.item_data.nombre
        return "Detalles"
        
    def create_left_panel(self):
        """Crear panel izquierdo con imagen y acciones"""
        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        left_box.set_size_request(250, -1)
        
        # Contenedor de imagen con click para vista previa
        image_button = Gtk.Button()
        image_button.add_css_class("flat")
        image_button.connect("clicked", self.on_image_clicked)
        
        self.cover_image = Gtk.Picture()
        self.cover_image.set_size_request(200, 300)
        self.cover_image.set_can_shrink(False)
        self.cover_image.add_css_class("card")
        
        self.load_cover_image()
        
        image_button.set_child(self.cover_image)
        left_box.append(image_button)
        
        # Botones de acción
        if self.item_type == "comic":
            action_box = self.create_comic_actions()
            left_box.append(action_box)
        
        return left_box
        
    def create_comic_actions(self):
        """Crear botones de acción para comics"""
        action_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        
        # Botón leer
        read_button = Gtk.Button.new_with_label("Abrir Comic")
        read_button.set_icon_name("media-playback-start-symbolic")
        read_button.add_css_class("suggested-action")
        read_button.connect("clicked", self.on_read_clicked)
        action_box.append(read_button)
        
        # Botón mostrar en carpeta
        folder_button = Gtk.Button.new_with_label("Mostrar en Carpeta")
        folder_button.set_icon_name("folder-open-symbolic")
        folder_button.connect("clicked", self.on_show_folder_clicked)
        action_box.append(folder_button)
        
        # Estado de clasificación
        if hasattr(self.item_data, 'is_classified'):
            status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            status_box.set_halign(Gtk.Align.CENTER)
            
            if self.item_data.is_classified:
                status_icon = Gtk.Image.new_from_icon_name("emblem-ok-symbolic")
                status_label = Gtk.Label(label="Clasificado")
                status_box.add_css_class("success")
            else:
                status_icon = Gtk.Image.new_from_icon_name("dialog-warning-symbolic")
                status_label = Gtk.Label(label="Sin Clasificar")
                status_box.add_css_class("warning")
            
            status_box.append(status_icon)
            status_box.append(status_label)
            action_box.append(status_box)
        
        return action_box
        
    def create_right_panel(self):
        """Crear panel derecho con información"""
        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        right_box.set_hexpand(True)
        
        # Crear grupos de información según el tipo
        if self.item_type == "comic":
            self.create_comic_info(right_box)
        elif self.item_type == "volume":
            self.create_volume_info(right_box)
        elif self.item_type == "publisher":
            self.create_publisher_info(right_box)
            
        return right_box
        
    def create_comic_info(self, container):
        """Crear información para comics"""
        # Información básica
        basic_group = Adw.PreferencesGroup()
        basic_group.set_title("Información Básica")
        
        # ID del comic
        id_row = Adw.ActionRow()
        id_row.set_title("ID")
        id_row.set_subtitle(str(self.item_data.id_comicbook))
        basic_group.add(id_row)
        
        # Ruta del archivo
        path_row = Adw.ActionRow()
        path_row.set_title("Archivo")
        path_row.set_subtitle(self.item_data.path)
        basic_group.add(path_row)
        
        # Nombre del archivo
        filename_row = Adw.ActionRow()
        filename_row.set_title("Nombre del archivo")
        filename_row.set_subtitle(os.path.basename(self.item_data.path))
        basic_group.add(filename_row)
        
        # Calidad
        quality_row = Adw.ActionRow()
        quality_row.set_title("Calidad")
        quality_stars = "★" * self.item_data.calidad + "☆" * (5 - self.item_data.calidad)
        quality_row.set_subtitle(f"{quality_stars} ({self.item_data.calidad}/5)")
        basic_group.add(quality_row)
        
        # Estado de clasificación
        classified_row = Adw.ActionRow()
        classified_row.set_title("Estado")
        if hasattr(self.item_data, 'is_classified'):
            status = "Clasificado" if self.item_data.is_classified else "Sin clasificar"
            classified_row.set_subtitle(status)
        else:
            classified_row.set_subtitle("Desconocido")
        basic_group.add(classified_row)
        
        # ID de ComicBook Info
        if self.item_data.id_comicbook_info:
            info_id_row = Adw.ActionRow()
            info_id_row.set_title("Comic Info ID")
            info_id_row.set_subtitle(str(self.item_data.id_comicbook_info))
            basic_group.add(info_id_row)
            
        container.append(basic_group)
        
        # Información del archivo
        file_group = Adw.PreferencesGroup()
        file_group.set_title("Información del Archivo")
        
        try:
            # Tamaño del archivo
            file_size = os.path.getsize(self.item_data.path)
            size_mb = file_size / (1024 * 1024)
            size_row = Adw.ActionRow()
            size_row.set_title("Tamaño")
            size_row.set_subtitle(f"{size_mb:.2f} MB ({file_size:,} bytes)")
            file_group.add(size_row)
            
            # Fecha de modificación
            mtime = os.path.getmtime(self.item_data.path)
            date_modified = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            date_row = Adw.ActionRow()
            date_row.set_title("Fecha de modificación")
            date_row.set_subtitle(date_modified)
            file_group.add(date_row)
            
            # Fecha de acceso
            atime = os.path.getatime(self.item_data.path)
            date_accessed = datetime.datetime.fromtimestamp(atime).strftime("%Y-%m-%d %H:%M:%S")
            access_row = Adw.ActionRow()
            access_row.set_title("Último acceso")
            access_row.set_subtitle(date_accessed)
            file_group.add(access_row)
            
            # Extensión del archivo
            ext = os.path.splitext(self.item_data.path)[1].lower()
            ext_row = Adw.ActionRow()
            ext_row.set_title("Formato")
            format_name = {
                '.cbr': 'Comic Book RAR',
                '.cbz': 'Comic Book ZIP', 
                '.pdf': 'Portable Document Format',
                '.zip': 'ZIP Archive',
                '.rar': 'RAR Archive'
            }.get(ext, ext.upper())
            ext_row.set_subtitle(format_name)
            file_group.add(ext_row)
            
        except OSError as e:
            error_row = Adw.ActionRow()
            error_row.set_title("Error")
            error_row.set_subtitle(f"No se pudo acceder al archivo: {str(e)}")
            file_group.add(error_row)
            
        container.append(file_group)
        
        # Estado en la base de datos
        db_group = Adw.PreferencesGroup()
        db_group.set_title("Estado en la Base de Datos")
        
        trash_row = Adw.ActionRow()
        trash_row.set_title("En papelera")
        trash_row.set_subtitle("Sí" if self.item_data.en_papelera else "No")
        db_group.add(trash_row)
        
        container.append(db_group)
        
    def create_volume_info(self, container):
        """Crear información para volúmenes"""
        # Información básica
        basic_group = Adw.PreferencesGroup()
        basic_group.set_title("Información del Volumen")
        
        # ID
        id_row = Adw.ActionRow()
        id_row.set_title("ID")
        id_row.set_subtitle(str(self.item_data.id_volume))
        basic_group.add(id_row)
        
        # Nombre
        name_row = Adw.ActionRow()
        name_row.set_title("Nombre")
        name_row.set_subtitle(self.item_data.nombre)
        basic_group.add(name_row)
        
        # Año de inicio
        year_row = Adw.ActionRow()
        year_row.set_title("Año de inicio")
        year_row.set_subtitle(str(self.item_data.anio_inicio) if self.item_data.anio_inicio > 0 else "No especificado")
        basic_group.add(year_row)
        
        # Cantidad de números
        count_row = Adw.ActionRow()
        count_row.set_title("Cantidad de números")
        count_row.set_subtitle(str(self.item_data.cantidad_numeros))
        basic_group.add(count_row)
        
        # ID de editorial
        publisher_row = Adw.ActionRow()
        publisher_row.set_title("ID Editorial")
        publisher_row.set_subtitle(str(self.item_data.id_publisher) if self.item_data.id_publisher > 0 else "Sin editorial")
        basic_group.add(publisher_row)
        
        # URL
        if self.item_data.url:
            url_row = Adw.ActionRow()
            url_row.set_title("URL")
            url_row.set_subtitle(self.item_data.url)
            basic_group.add(url_row)
        
        container.append(basic_group)
        
        # Descripción
        if self.item_data.deck or self.item_data.descripcion:
            desc_group = Adw.PreferencesGroup()
            desc_group.set_title("Descripción")
            
            if self.item_data.deck:
                deck_expander = Adw.ExpanderRow()
                deck_expander.set_title("Resumen")
                deck_expander.set_subtitle(self.item_data.deck[:100] + "..." if len(self.item_data.deck) > 100 else self.item_data.deck)
                
                # Contenido completo del deck
                deck_label = Gtk.Label()
                deck_label.set_text(self.item_data.deck)
                deck_label.set_wrap(True)
                deck_label.set_selectable(True)
                deck_label.set_margin_top(12)
                deck_label.set_margin_bottom(12)
                deck_label.set_margin_start(12)
                deck_label.set_margin_end(12)
                deck_expander.add_row(deck_label)
                
                desc_group.add(deck_expander)
                
            if self.item_data.descripcion:
                desc_expander = Adw.ExpanderRow()
                desc_expander.set_title("Descripción completa")
                desc_expander.set_subtitle("Ver descripción detallada")
                
                # ScrolledWindow para descripción larga
                scrolled_desc = Gtk.ScrolledWindow()
                scrolled_desc.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
                scrolled_desc.set_max_content_height(200)
                scrolled_desc.set_margin_top(12)
                scrolled_desc.set_margin_bottom(12)
                scrolled_desc.set_margin_start(12)
                scrolled_desc.set_margin_end(12)
                
                desc_textview = Gtk.TextView()
                desc_textview.set_editable(False)
                desc_textview.set_wrap_mode(Gtk.WrapMode.WORD)
                desc_textview.get_buffer().set_text(self.item_data.descripcion)
                
                scrolled_desc.set_child(desc_textview)
                desc_expander.add_row(scrolled_desc)
                
                desc_group.add(desc_expander)
                
            container.append(desc_group)
            
    def create_publisher_info(self, container):
        """Crear información para editoriales"""
        # Información básica
        basic_group = Adw.PreferencesGroup()
        basic_group.set_title("Información de la Editorial")
        
        # ID
        id_row = Adw.ActionRow()
        id_row.set_title("ID")
        id_row.set_subtitle(str(self.item_data.id_publisher))
        basic_group.add(id_row)
        
        # Nombre
        name_row = Adw.ActionRow()
        name_row.set_title("Nombre")
        name_row.set_subtitle(self.item_data.nombre)
        basic_group.add(name_row)
        
        # Deck (resumen corto)
        if self.item_data.deck:
            deck_row = Adw.ActionRow()
            deck_row.set_title("Resumen")
            deck_row.set_subtitle(self.item_data.deck)
            basic_group.add(deck_row)
            
        # Sitio web
        if self.item_data.sitio_web:
            web_row = Adw.ActionRow()
            web_row.set_title("Sitio Web")
            web_row.set_subtitle(self.item_data.sitio_web)
            basic_group.add(web_row)
            
        # URL del logo
        if self.item_data.url_logo:
            logo_row = Adw.ActionRow()
            logo_row.set_title("URL del Logo")
            logo_row.set_subtitle(self.item_data.url_logo)
            basic_group.add(logo_row)
            
        container.append(basic_group)
        
        # Descripción completa
        if self.item_data.descripcion:
            desc_group = Adw.PreferencesGroup()
            desc_group.set_title("Descripción")
            
            desc_expander = Adw.ExpanderRow()
            desc_expander.set_title("Descripción completa")
            desc_expander.set_subtitle("Ver descripción detallada")
            
            scrolled_desc = Gtk.ScrolledWindow()
            scrolled_desc.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            scrolled_desc.set_max_content_height(200)
            scrolled_desc.set_margin_top(12)
            scrolled_desc.set_margin_bottom(12)
            scrolled_desc.set_margin_start(12)
            scrolled_desc.set_margin_end(12)
            
            desc_textview = Gtk.TextView()
            desc_textview.set_editable(False)
            desc_textview.set_wrap_mode(Gtk.WrapMode.WORD)
            desc_textview.get_buffer().set_text(self.item_data.descripcion)
            
            scrolled_desc.set_child(desc_textview)
            desc_expander.add_row(scrolled_desc)
            desc_group.add(desc_expander)
            
            container.append(desc_group)
            
    def load_cover_image(self):
        """Cargar la imagen de portada con mejor manejo de errores"""
        try:
            cover_path = None
            
            if self.item_data:
                if self.item_type == "comic":
                    cover_path = self.item_data.obtener_cover()
                elif self.item_type == "volume":
                    cover_path = self.item_data.obtener_cover()
                elif self.item_type == "publisher":
                    cover_path = self.item_data.obtener_nombre_logo()
                    
            if cover_path and os.path.exists(cover_path):
                self.cover_image.set_filename(cover_path)
                self.cover_image.set_tooltip_text(f"Click para vista previa: {os.path.basename(cover_path)}")
            else:
                self.create_default_image()
                self.cover_image.set_tooltip_text("Imagen no disponible")
                
        except Exception as e:
            print(f"Error cargando imagen: {e}")
            self.create_default_image()
            
    def create_default_image(self):
        """Crear imagen por defecto más elegante"""
        try:
            # Colores diferentes según el tipo
            if self.item_type == "comic":
                color = 0x3584E4ff  # Azul
            elif self.item_type == "volume":
                color = 0x33D17Aff  # Verde
            elif self.item_type == "publisher":
                color = 0xF66151ff  # Rojo
            else:
                color = 0x808080ff  # Gris
                
            pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 200, 300)
            pixbuf.fill(color)
            texture = Gdk.Texture.new_for_pixbuf(pixbuf)
            self.cover_image.set_paintable(texture)
            
        except Exception as e:
            print(f"Error creando imagen por defecto: {e}")
            
    def on_image_clicked(self, button):
        """Mostrar vista previa de la imagen"""
        cover_path = None
        
        if self.item_data:
            if self.item_type == "comic":
                cover_path = self.item_data.obtener_cover()
            elif self.item_type == "volume":
                cover_path = self.item_data.obtener_cover()
            elif self.item_type == "publisher":
                cover_path = self.item_data.obtener_nombre_logo()
                
        if cover_path and os.path.exists(cover_path):
            preview_dialog = ImagePreviewDialog(self.parent_window, cover_path, self.get_title_text())
            preview_dialog.present(self)
            
    def on_read_clicked(self, button):
        """Abrir comic con aplicación predeterminada"""
        try:
            success = open_comic_file(self.item_data.path)
            if not success and hasattr(self.parent_window, 'toast_manager'):
                self.parent_window.toast_manager.show_error("No se pudo abrir el comic")
        except Exception as e:
            print(f"Error abriendo comic: {e}")
            if hasattr(self.parent_window, 'toast_manager'):
                self.parent_window.toast_manager.show_error(f"Error: {e}")
                
    def on_show_folder_clicked(self, button):
        """Mostrar archivo en el explorador"""
        try:
            show_file_in_folder(self.item_data.path)
        except Exception as e:
            print(f"Error abriendo carpeta: {e}")
            if hasattr(self.parent_window, 'toast_manager'):
                self.parent_window.toast_manager.show_error(f"Error abriendo carpeta: {e}")
                
    def on_edit_clicked(self, button):
        """Abrir diálogo de edición"""
        edit_dialog = EditComicDialog(self.parent_window, self.item_data)
        edit_dialog.present(self)


class ImprovedComicCoverWidget(Gtk.Box):
    """Widget mejorado para mostrar covers con más información y funcionalidad"""
    
    def __init__(self, comic_data, item_type="comic", parent_window=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.comic_data = comic_data
        self.item_type = item_type
        self.parent_window = parent_window
        
        self.set_size_request(160, 280)
        self.add_css_class("comic-card")
        
        # Crear contenedor principal
        self.main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        
        # Crear gesture para detectar clicks
        click_gesture = Gtk.GestureClick.new()
        click_gesture.connect("pressed", self.on_item_clicked)
        self.add_controller(click_gesture)
        
        # Crear menú contextual
        right_click = Gtk.GestureClick.new()
        right_click.set_button(3)  # Botón derecho
        right_click.connect("pressed", self.on_right_click)
        self.add_controller(right_click)
        
        # Crear imagen de portada con overlay para estado
        self.image_overlay = Gtk.Overlay()
        
        self.image = Gtk.Picture()
        self.image.set_size_request(140, 210)
        self.image.set_can_shrink(False)
        self.image.add_css_class("comic-cover")
        
        # Badge para estado (clasificado, calidad, etc.)
        self.status_badge = Gtk.Label()
        self.status_badge.add_css_class("badge")
        self.status_badge.set_halign(Gtk.Align.END)
        self.status_badge.set_valign(Gtk.Align.START)
        self.status_badge.set_margin_top(6)
        self.status_badge.set_margin_end(6)
        
        self.image_overlay.set_child(self.image)
        self.image_overlay.add_overlay(self.status_badge)
        
        # Información del título
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        
        # Título principal
        self.title_label = Gtk.Label()
        self.title_label.set_wrap(True)
        self.title_label.set_max_width_chars(18)
        self.title_label.add_css_class("comic-title")
        self.title_label.set_justify(Gtk.Justification.CENTER)
        
        # Subtítulo/información adicional
        self.subtitle_label = Gtk.Label()
        self.subtitle_label.set_wrap(True)
        self.subtitle_label.set_max_width_chars(18)
        self.subtitle_label.add_css_class("comic-subtitle")
        self.subtitle_label.set_justify(Gtk.Justification.CENTER)
        
        title_box.append(self.title_label)
        title_box.append(self.subtitle_label)
        
        # Barra de progreso/rating (opcional)
        if self.item_type == "comic" and self.comic_data and hasattr(self.comic_data, 'calidad'):
            self.progress_bar = Gtk.ProgressBar()
            self.progress_bar.set_fraction(self.comic_data.calidad / 5.0)
            self.progress_bar.add_css_class("quality-bar")
            title_box.append(self.progress_bar)
        
        # Añadir todo al contenedor principal
        self.main_container.append(self.image_overlay)
        self.main_container.append(title_box)
        
        self.append(self.main_container)
        
        # Inicializar contenido
        if self.comic_data:
            self.load_cover_image()
            self.update_labels()
            self.setup_status_badge()
        
    def setup_status_badge(self):
        """Configurar el badge de estado"""
        if self.item_type == "comic" and self.comic_data:
            if hasattr(self.comic_data, 'is_classified') and self.comic_data.is_classified:
                self.status_badge.set_text("✓")
                self.status_badge.add_css_class("badge-success")
                self.status_badge.set_tooltip_text("Clasificado")
            else:
                self.status_badge.set_text("?")
                self.status_badge.add_css_class("badge-warning")
                self.status_badge.set_tooltip_text("Sin clasificar")
        elif self.item_type == "volume" and self.comic_data:
            if hasattr(self.comic_data, 'cantidad_numeros') and self.comic_data.cantidad_numeros > 0:
                self.status_badge.set_text(str(self.comic_data.cantidad_numeros))
                self.status_badge.add_css_class("badge-info")
                self.status_badge.set_tooltip_text(f"{self.comic_data.cantidad_numeros} números")
        elif self.item_type == "publisher" and self.comic_data:
            # Para editoriales, mostrar primera letra del nombre
            if self.comic_data.nombre:
                self.status_badge.set_text(self.comic_data.nombre[0].upper())
                self.status_badge.add_css_class("badge-info")
                self.status_badge.set_tooltip_text(self.comic_data.nombre)
        else:
            self.status_badge.set_visible(False)
            
    def update_labels(self):
        """Actualizar los labels con información del item"""
        if not self.comic_data:
            self.title_label.set_text("Sin datos")
            self.subtitle_label.set_text("")
            return
            
        if self.item_type == "comic":
            # Título: nombre del archivo
            title = getattr(self.comic_data, 'nombre_archivo', f"Comic {self.comic_data.id_comicbook}")
            self.title_label.set_text(title)
            
            # Subtítulo: información adicional
            subtitle_parts = []
            if hasattr(self.comic_data, 'calidad') and self.comic_data.calidad > 0:
                subtitle_parts.append(f"★ {self.comic_data.calidad}/5")
            if hasattr(self.comic_data, 'is_classified'):
                subtitle_parts.append("Clasificado" if self.comic_data.is_classified else "Sin clasificar")
            
            self.subtitle_label.set_text(" • ".join(subtitle_parts))
            
        elif self.item_type == "volume":
            self.title_label.set_text(self.comic_data.nombre)
            
            subtitle_parts = []
            if self.comic_data.anio_inicio > 0:
                subtitle_parts.append(str(self.comic_data.anio_inicio))
            if self.comic_data.cantidad_numeros > 0:
                subtitle_parts.append(f"{self.comic_data.cantidad_numeros} nums")
                
            self.subtitle_label.set_text(" • ".join(subtitle_parts))
            
        elif self.item_type == "publisher":
            self.title_label.set_text(self.comic_data.nombre)
            if self.comic_data.deck:
                # Limitar longitud del deck
                deck_text = self.comic_data.deck
                if len(deck_text) > 50:
                    deck_text = deck_text[:47] + "..."
                self.subtitle_label.set_text(deck_text)
            else:
                self.subtitle_label.set_text("")
                
    def load_cover_image(self):
        """Cargar la imagen de portada con mejor manejo de errores"""
        try:
            cover_path = None
            
            if self.comic_data:
                if self.item_type == "comic":
                    cover_path = self.comic_data.obtener_cover()
                elif self.item_type == "volume":
                    cover_path = self.comic_data.obtener_cover()
                elif self.item_type == "publisher":
                    cover_path = self.comic_data.obtener_nombre_logo()
                    
            if cover_path and os.path.exists(cover_path):
                self.image.set_filename(cover_path)
                self.image.set_tooltip_text(f"Imagen: {os.path.basename(cover_path)}")
            else:
                self.create_default_image()
                self.image.set_tooltip_text("Imagen no disponible")
                
        except Exception as e:
            print(f"Error cargando imagen: {e}")
            self.create_default_image()
            
    def create_default_image(self):
        """Crear imagen por defecto más elegante"""
        try:
            # Colores diferentes según el tipo
            if self.item_type == "comic":
                color = 0x3584E4ff  # Azul
            elif self.item_type == "volume":
                color = 0x33D17Aff  # Verde
            elif self.item_type == "publisher":
                color = 0xF66151ff  # Rojo
            else:
                color = 0x808080ff  # Gris
                
            pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 140, 210)
            pixbuf.fill(color)
            texture = Gdk.Texture.new_for_pixbuf(pixbuf)
            self.image.set_paintable(texture)
            
        except Exception as e:
            print(f"Error creando imagen por defecto: {e}")
            
    def on_item_clicked(self, gesture, n_press, x, y):
        """Manejar click en el item"""
        if n_press == 2:  # Doble click
            self.show_details()
        elif n_press == 1:  # Click simple
            self.select_item()
            
    def on_right_click(self, gesture, n_press, x, y):
        """Manejar click derecho para menú contextual"""
        if self.comic_data:
            menu = self.create_context_menu()
            popover = Gtk.PopoverMenu()
            popover.set_menu_model(menu)
            popover.set_parent(self)
            popover.popup()
            
    def create_context_menu(self):
        """Crear menú contextual"""
        menu = Gio.Menu()
        
        if self.item_type == "comic":
            menu.append("Ver detalles", "item.details")
            menu.append("Abrir comic", "item.open")
            menu.append("Mostrar en carpeta", "item.folder")
            menu.append("Editar", "item.edit")
        elif self.item_type == "volume":
            menu.append("Ver detalles", "item.details")
            menu.append("Buscar números", "item.find")
        elif self.item_type == "publisher":
            menu.append("Ver detalles", "item.details")
            menu.append("Ver volúmenes", "item.volumes")
            
        return menu
            
    def show_details(self):
        """Mostrar diálogo de detalles"""
        if self.comic_data and self.parent_window:
            detail_dialog = ComicDetailDialog(
                self.parent_window, 
                self.comic_data, 
                self.item_type
            )
            detail_dialog.present(self.parent_window)
            
    def select_item(self):
        """Seleccionar el item"""
        if self.comic_data:
            print(f"Seleccionado: {self.item_type} - {getattr(self.comic_data, 'nombre', 'Unknown')}")
        
    def update_data(self, new_data):
        """Actualizar los datos del widget"""
        self.comic_data = new_data
        if new_data:
            self.load_cover_image()
            self.update_labels()
            self.setup_status_badge()


class EditComicDialog(Adw.Dialog):
    """Diálogo para editar información de comics"""
    
    def __init__(self, parent_window, comic_data):
        super().__init__()
        self.parent_window = parent_window
        self.comic_data = comic_data
        
        self.set_title("Editar Comic")
        self.set_default_size(500, 600)
        
        self.create_content()
        
    def create_content(self):
        """Crear contenido del diálogo"""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Header
        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label="Editar Comic"))
        
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
        
        # Información básica
        basic_group = Adw.PreferencesGroup()
        basic_group.set_title("Información Básica")
        
        # Ruta del archivo (solo lectura)
        path_row = Adw.ActionRow()
        path_row.set_title("Archivo")
        path_row.set_subtitle(self.comic_data.path)
        basic_group.add(path_row)
        
        # Calidad
        self.quality_spin = Adw.SpinRow()
        self.quality_spin.set_title("Calidad")
        self.quality_spin.set_subtitle("Calidad del archivo (0-5)")
        self.quality_spin.set_range(0, 5)
        self.quality_spin.set_increments(1, 1)
        self.quality_spin.set_value(self.comic_data.calidad)
        basic_group.add(self.quality_spin)
        
        # ID de Comic Info
        self.comic_info_entry = Adw.EntryRow()
        self.comic_info_entry.set_title("Comic Info ID")
        self.comic_info_entry.set_text(str(self.comic_data.id_comicbook_info))
        basic_group.add(self.comic_info_entry)
        
        # En papelera
        self.trash_switch = Adw.SwitchRow()
        self.trash_switch.set_title("En papelera")
        self.trash_switch.set_subtitle("Marcar como eliminado")
        self.trash_switch.set_active(self.comic_data.en_papelera)
        basic_group.add(self.trash_switch)
        
        content_box.append(basic_group)
        
        # Información del archivo (solo lectura)
        self.create_file_info_group(content_box)
        
        scrolled.set_child(content_box)
        main_box.append(scrolled)
        self.set_child(main_box)
        
    def create_file_info_group(self, container):
        """Crear grupo de información del archivo"""
        file_group = Adw.PreferencesGroup()
        file_group.set_title("Información del Archivo")
        
        try:
            # Tamaño
            file_size = os.path.getsize(self.comic_data.path)
            size_mb = file_size / (1024 * 1024)
            size_row = Adw.ActionRow()
            size_row.set_title("Tamaño")
            size_row.set_subtitle(f"{size_mb:.2f} MB")
            file_group.add(size_row)
            
            # Fecha de modificación
            mtime = os.path.getmtime(self.comic_data.path)
            date_modified = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
            date_row = Adw.ActionRow()
            date_row.set_title("Última modificación")
            date_row.set_subtitle(date_modified)
            file_group.add(date_row)
            
            # Formato
            ext = os.path.splitext(self.comic_data.path)[1].lower()
            format_row = Adw.ActionRow()
            format_row.set_title("Formato")
            format_row.set_subtitle(ext.upper())
            file_group.add(format_row)
            
        except Exception as e:
            error_row = Adw.ActionRow()
            error_row.set_title("Error")
            error_row.set_subtitle("No se pudo leer información del archivo")
            file_group.add(error_row)
            
        container.append(file_group)
        
    def on_save_clicked(self, button):
        """Guardar cambios"""
        try:
            # Actualizar datos del comic
            self.comic_data.calidad = int(self.quality_spin.get_value())
            self.comic_data.id_comicbook_info = self.comic_info_entry.get_text().strip()
            self.comic_data.en_papelera = self.trash_switch.get_active()
            
            # Guardar en base de datos si hay sesión disponible
            if hasattr(self.parent_window, 'session') and self.parent_window.session:
                self.parent_window.session.commit()
                
            # Mostrar confirmación
            if hasattr(self.parent_window, 'toast_manager'):
                self.parent_window.toast_manager.show_success("Comic actualizado correctamente")
                
            # Recargar vista si es necesario
            if hasattr(self.parent_window, 'load_comics') and self.parent_window.current_section == "comics":
                self.parent_window.load_comics()
                
            self.close()
            
        except Exception as e:
            print(f"Error guardando comic: {e}")
            if hasattr(self.parent_window, 'toast_manager'):
                self.parent_window.toast_manager.show_error(f"Error guardando: {e}")


class ImagePreviewDialog(Adw.Dialog):
    """Diálogo para previsualizar imágenes en tamaño completo"""
    
    def __init__(self, parent_window, image_path, title="Vista Previa"):
        super().__init__()
        self.parent_window = parent_window
        self.image_path = image_path
        
        self.set_title(title)
        self.set_default_size(800, 600)
        
        self.create_content()
        
    def create_content(self):
        """Crear contenido del diálogo"""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Header
        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label="Vista Previa"))
        
        close_button = Gtk.Button.new_with_label("Cerrar")
        close_button.connect("clicked", lambda b: self.close())
        header.pack_start(close_button)
        
        # Botón de zoom (futuro)
        zoom_button = Gtk.Button.new_from_icon_name("zoom-in-symbolic")
        zoom_button.set_tooltip_text("Ajustar zoom")
        header.pack_end(zoom_button)
        
        main_box.append(header)
        
        if not os.path.exists(self.image_path):
            # Mostrar mensaje de error
            error_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
            error_box.set_valign(Gtk.Align.CENTER)
            error_box.set_halign(Gtk.Align.CENTER)
            
            error_icon = Gtk.Image.new_from_icon_name("dialog-error-symbolic")
            error_icon.set_icon_size(Gtk.IconSize.LARGE)
            error_box.append(error_icon)
            
            error_label = Gtk.Label(label="Imagen no encontrada")
            error_label.add_css_class("title-2")
            error_box.append(error_label)
            
            path_label = Gtk.Label(label=self.image_path)
            path_label.add_css_class("dim-label")
            error_box.append(path_label)
            
            main_box.append(error_box)
            self.set_child(main_box)
            return
            
        # Imagen scrollable
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        self.image = Gtk.Picture()
        self.image.set_can_shrink(True)
        self.image.set_keep_aspect_ratio(True)
        self.image.set_filename(self.image_path)
        
        scrolled.set_child(self.image)
        main_box.append(scrolled)
        
        # Barra de información
        info_bar = self.create_info_bar()
        main_box.append(info_bar)
        
        self.set_child(main_box)
        
    def create_info_bar(self):
        """Crear barra de información de la imagen"""
        info_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        info_box.set_margin_start(12)
        info_box.set_margin_end(12)
        info_box.set_margin_top(8)
        info_box.set_margin_bottom(8)
        info_box.add_css_class("toolbar")
        
        # Nombre del archivo
        filename_label = Gtk.Label(label=os.path.basename(self.image_path))
        filename_label.add_css_class("caption")
        filename_label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        filename_label.set_hexpand(True)
        info_box.append(filename_label)
        
        try:
            # Tamaño del archivo
            file_size = os.path.getsize(self.image_path)
            if file_size < 1024:
                size_text = f"{file_size} B"
            elif file_size < 1024 * 1024:
                size_text = f"{file_size / 1024:.1f} KB"
            else:
                size_text = f"{file_size / (1024 * 1024):.1f} MB"
                
            size_label = Gtk.Label(label=size_text)
            size_label.add_css_class("caption")
            size_label.add_css_class("dim-label")
            info_box.append(size_label)
            
            # Dimensiones de la imagen (si se puede obtener)
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(self.image_path)
                width = pixbuf.get_width()
                height = pixbuf.get_height()
                
                dimensions_label = Gtk.Label(label=f"{width}×{height}")
                dimensions_label.add_css_class("caption")
                dimensions_label.add_css_class("dim-label")
                info_box.append(dimensions_label)
            except:
                pass
                
        except OSError:
            pass
            
        return info_box


# Funciones auxiliares
def open_comic_file(file_path):
    """Abrir archivo de comic con el lector predeterminado"""
    try:
        system = platform.system().lower()
        
        if system == "linux":
            # Buscar lectores comunes en Linux
            readers = ["evince", "okular", "atril", "mcomix", "qcomicbook"]
            for reader in readers:
                if subprocess.run(["which", reader], capture_output=True).returncode == 0:
                    subprocess.Popen([reader, file_path])
                    return True
            # Fallback a xdg-open
            subprocess.Popen(["xdg-open", file_path])
            return True
            
        elif system == "windows":
            os.startfile(file_path)
            return True
            
        elif system == "darwin":  # macOS
            subprocess.Popen(["open", file_path])
            return True
            
        return False
        
    except Exception as e:
        print(f"Error abriendo comic: {e}")
        return False


def show_file_in_folder(file_path):
    """Mostrar archivo en el explorador/administrador de archivos"""
    try:
        system = platform.system().lower()
        folder_path = os.path.dirname(file_path)
        
        if system == "linux":
            # Intentar con diferentes administradores de archivos
            file_managers = ["nautilus", "dolphin", "thunar", "pcmanfm", "nemo"]
            for fm in file_managers:
                if subprocess.run(["which", fm], capture_output=True).returncode == 0:
                    subprocess.Popen([fm, folder_path])
                    return True
            # Fallback a xdg-open
            subprocess.Popen(["xdg-open", folder_path])
            return True
            
        elif system == "windows":
            subprocess.Popen(["explorer", "/select,", file_path])
            return True
            
        elif system == "darwin":  # macOS
            subprocess.Popen(["open", "-R", file_path])
            return True
            
        return False
        
    except Exception as e:
        print(f"Error abriendo carpeta: {e}")
        return False


def create_placeholder_image(width=140, height=210, color=0x808080ff):
    """Crear imagen placeholder"""
    try:
        pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, width, height)
        pixbuf.fill(color)
        return Gdk.Texture.new_for_pixbuf(pixbuf)
    except Exception as e:
        print(f"Error creando placeholder: {e}")
        return None


# Clase auxiliar para datos de elementos en el GridView
class GridItemData(GObject.Object):
    """Wrapper para datos de elementos del GridView"""
    
    def __init__(self, data, item_type="comic"):
        super().__init__()
        self.data = data
        self.item_type = item_type
        
    def get_title(self):
        """Obtener título del elemento"""
        if self.item_type == "comic":
            return getattr(self.data, 'nombre_archivo', f"Comic {self.data.id_comicbook}")
        elif self.item_type == "volume":
            return self.data.nombre
        elif self.item_type == "publisher":
            return self.data.nombre
        return "Unknown"
        
    def get_subtitle(self):
        """Obtener subtítulo del elemento"""
        if self.item_type == "comic":
            parts = []
            if hasattr(self.data, 'calidad') and self.data.calidad > 0:
                parts.append(f"★ {self.data.calidad}/5")
            if hasattr(self.data, 'is_classified'):
                parts.append("Clasificado" if self.data.is_classified else "Sin clasificar")
            return " • ".join(parts)
        elif self.item_type == "volume":
            parts = []
            if self.data.anio_inicio > 0:
                parts.append(str(self.data.anio_inicio))
            if self.data.cantidad_numeros > 0:
                parts.append(f"{self.data.cantidad_numeros} nums")
            return " • ".join(parts)
        elif self.item_type == "publisher":
            return self.data.deck if self.data.deck else ""
        return ""
        
    def get_cover_path(self):
        """Obtener ruta de la portada"""
        if self.item_type == "comic":
            return self.data.obtener_cover()
        elif self.item_type == "volume":
            return self.data.obtener_cover()
        elif self.item_type == "publisher":
            return self.data.obtener_nombre_logo()
        return None