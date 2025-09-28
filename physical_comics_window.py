#!/usr/bin/env python3
"""
physical_comics_window.py - Vista para mostrar cómics físicos de un ComicbookInfo específico
"""

import gi
import os
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GdkPixbuf, Gdk, Pango, GLib, GObject, Gio

try:
    from entidades.comicbook_model import Comicbook
    from comic_cards import ComicCard
except ImportError as e:
    print(f"Error importando entidades: {e}")


class PhysicalComicsWindow(Adw.ApplicationWindow):
    """Vista para mostrar los cómics físicos de un ComicbookInfo específico"""

    def __init__(self, comic_info, session, thumbnail_generator, **kwargs):
        super().__init__(**kwargs)

        self.comic_info = comic_info
        self.session = session
        self.thumbnail_generator = thumbnail_generator

        # Configurar ventana
        title = f"Físicos: {comic_info.titulo or f'Issue #{comic_info.numero}'}"
        self.set_title(title)
        self.set_default_size(1000, 600)
        self.set_resizable(True)

        # Crear interfaz
        self.setup_ui()

        # Cargar físicos
        self.load_physical_comics()

    def setup_ui(self):
        """Crear la interfaz de usuario"""
        # Header bar
        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label=self.comic_info.titulo or f"Issue #{self.comic_info.numero}"))

        # Botón cerrar
        close_button = Gtk.Button.new_from_icon_name("window-close-symbolic")
        close_button.connect("clicked", lambda x: self.close())
        header.pack_end(close_button)

        # Container principal
        window_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        window_box.append(header)

        # Área de contenido con scroll
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)

        # Box principal
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)

        # Crear secciones
        self.create_header_section(main_box)
        self.create_physical_comics_section(main_box)

        scrolled.set_child(main_box)
        window_box.append(scrolled)
        self.set_content(window_box)

    def create_header_section(self, parent):
        """Crear sección de información del ComicbookInfo"""
        # Frame de información
        info_frame = Adw.PreferencesGroup()
        info_frame.set_title("Información del Issue")

        # Título
        if self.comic_info.titulo:
            title_row = Adw.ActionRow()
            title_row.set_title("Título")
            title_row.set_subtitle(self.comic_info.titulo)
            info_frame.add(title_row)

        # Número
        number_row = Adw.ActionRow()
        number_row.set_title("Número")
        number_row.set_subtitle(f"#{self.comic_info.numero}")
        info_frame.add(number_row)

        # Fecha de portada
        if self.comic_info.fecha_tapa > 0:
            date_row = Adw.ActionRow()
            date_row.set_title("Fecha de portada")
            date_row.set_subtitle(str(self.comic_info.fecha_tapa))
            info_frame.add(date_row)

        # Calificación
        if self.comic_info.calificacion > 0:
            rating_row = Adw.ActionRow()
            rating_row.set_title("Calificación")
            stars = "★" * int(self.comic_info.calificacion) + "☆" * (5 - int(self.comic_info.calificacion))
            rating_row.set_subtitle(f"{stars} ({self.comic_info.calificacion}/5)")
            info_frame.add(rating_row)

        # Resumen si existe
        if self.comic_info.resumen:
            summary_row = Adw.ExpanderRow()
            summary_row.set_title("Resumen")
            summary_row.set_subtitle("Click para expandir")

            # Contenido del resumen
            summary_label = Gtk.Label(label=self.comic_info.resumen)
            summary_label.set_wrap(True)
            summary_label.set_selectable(True)
            summary_label.set_margin_start(12)
            summary_label.set_margin_end(12)
            summary_label.set_margin_top(12)
            summary_label.set_margin_bottom(12)
            summary_row.add_row(summary_label)

            info_frame.add(summary_row)

        parent.append(info_frame)

    def create_physical_comics_section(self, parent):
        """Crear sección de cómics físicos"""
        # Frame de físicos
        physical_frame = Adw.PreferencesGroup()
        physical_frame.set_title("Archivos Físicos")
        physical_frame.set_vexpand(True)

        # Contenedor para las cards
        self.physical_flow_box = Gtk.FlowBox()
        self.physical_flow_box.set_valign(Gtk.Align.START)
        self.physical_flow_box.set_max_children_per_line(4)
        self.physical_flow_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.physical_flow_box.set_homogeneous(True)
        self.physical_flow_box.set_column_spacing(15)
        self.physical_flow_box.set_row_spacing(15)
        self.physical_flow_box.set_margin_top(10)
        self.physical_flow_box.set_margin_start(10)
        self.physical_flow_box.set_margin_end(10)
        self.physical_flow_box.set_margin_bottom(10)

        # Scroll para los físicos
        physical_scroll = Gtk.ScrolledWindow()
        physical_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        physical_scroll.set_vexpand(True)
        physical_scroll.set_min_content_height(300)
        physical_scroll.set_child(self.physical_flow_box)

        physical_frame.add(physical_scroll)
        parent.append(physical_frame)

    def load_physical_comics(self):
        """Cargar cómics físicos del ComicbookInfo"""
        try:
            if not Comicbook:
                print("No se pueden cargar físicos - falta Comicbook")
                return

            # Obtener todos los físicos para este ComicbookInfo
            physical_comics = self.session.query(Comicbook).filter(
                Comicbook.id_comicbook_info == self.comic_info.id_comicbook_info
            ).all()

            print(f"Encontrados {len(physical_comics)} físicos para {self.comic_info.titulo} #{self.comic_info.numero}")

            if not physical_comics:
                # Mostrar mensaje de que no hay físicos
                no_physical_label = Gtk.Label(label="No hay archivos físicos para este issue")
                no_physical_label.add_css_class("dim-label")
                no_physical_label.set_margin_top(50)
                self.physical_flow_box.append(no_physical_label)
                return

            # Agregar cada físico como card
            for physical_comic in physical_comics:
                try:
                    # Crear card más grande para mejor visualización
                    comic_card = ComicCard(physical_comic, self.thumbnail_generator)
                    comic_card.set_size_request(250, 400)

                    # Hacer clickeable para acciones futuras (abrir archivo, editar, etc.)
                    click_gesture = Gtk.GestureClick()
                    click_gesture.connect("pressed", self.on_physical_comic_clicked, physical_comic)
                    comic_card.add_controller(click_gesture)

                    self.physical_flow_box.append(comic_card)

                except Exception as e:
                    print(f"Error creando card para físico {physical_comic.id_comicbook}: {e}")

        except Exception as e:
            print(f"Error cargando físicos: {e}")

    def on_physical_comic_clicked(self, gesture, n_press, x, y, physical_comic):
        """Manejar click en un cómic físico"""
        if n_press == 2:  # Doble click
            print(f"Doble click en físico: {physical_comic.nombre_archivo}")
            # Aquí podrías:
            # - Abrir el archivo con la aplicación predeterminada
            # - Mostrar un visor de cómics integrado
            # - Abrir una ventana de propiedades/edición del archivo

            # Por ahora, intentar abrir con la aplicación predeterminada
            try:
                import subprocess
                subprocess.run(['xdg-open', physical_comic.path], check=True)
            except Exception as e:
                print(f"Error abriendo archivo: {e}")
        elif n_press == 1:  # Click simple
            print(f"Click en: {physical_comic.nombre_archivo} (Calidad: {physical_comic.calidad})")