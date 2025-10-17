#!/usr/bin/env python3
"""
volume_detail_window.py - Ventana de detalle para volúmenes
"""

import gi
import os
import re
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GdkPixbuf, Gdk, Pango, GLib, GObject, Gio

try:
    from entidades.comicbook_model import Comicbook
    from entidades.comicbook_info_model import ComicbookInfo
    from entidades.publisher_model import Publisher
    from comic_cards import ComicCard
    from sqlalchemy import Integer
    from physical_comics_window import PhysicalComicsWindow
except ImportError as e:
    print(f"Error importando entidades: {e}")


class VolumeDetailWindow(Adw.ApplicationWindow):
    """Ventana de detalle para mostrar información completa de un volumen"""

    def __init__(self, volume, session, thumbnail_generator, **kwargs):
        super().__init__(**kwargs)

        self.volume = volume
        self.session = session
        self.thumbnail_generator = thumbnail_generator

        # Configurar ventana
        self.set_title(f"Detalle: {volume.nombre}")
        self.set_default_size(1200, 800)
        self.set_resizable(True)

        # Crear interfaz
        self.setup_ui()

        # Cargar datos
        self.load_volume_data()

    def clean_html_text(self, text):
        """Limpiar texto HTML para mostrar solo texto plano"""
        if not text:
            return ""

        # Remover tags HTML
        clean_text = re.sub(r'<[^>]+>', '', text)

        # Decodificar entidades HTML comunes
        clean_text = clean_text.replace('&nbsp;', ' ')
        clean_text = clean_text.replace('&amp;', '&')
        clean_text = clean_text.replace('&lt;', '<')
        clean_text = clean_text.replace('&gt;', '>')
        clean_text = clean_text.replace('&quot;', '"')
        clean_text = clean_text.replace('&#39;', "'")

        # Escapar cualquier & restante que no sea una entidad válida
        clean_text = re.sub(r'&(?![a-zA-Z0-9#]{1,7};)', '&amp;', clean_text)

        # Limpiar espacios múltiples y saltos de línea
        clean_text = re.sub(r'\s+', ' ', clean_text)
        clean_text = clean_text.strip()

        return clean_text

    def setup_ui(self):
        """Crear la interfaz de usuario"""
        # Header bar (solo para AdwApplicationWindow, no usar set_titlebar)
        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label=self.volume.nombre))

        # Botón cerrar
        close_button = Gtk.Button.new_from_icon_name("window-close-symbolic")
        close_button.connect("clicked", lambda x: self.close())
        header.pack_end(close_button)

        # Container principal que incluye header y contenido
        window_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        window_box.append(header)

        # Contenedor principal con scroll
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)  # Expandir verticalmente

        # Crear TabView y TabBar para organizar el contenido
        self.tab_view = Adw.TabView()
        self.tab_view.set_vexpand(True)

        # Crear TabBar para mostrar las pestañas
        tab_bar = Adw.TabBar()
        tab_bar.set_view(self.tab_view)

        # Contenedor para tab bar y contenido
        tab_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        tab_container.append(tab_bar)
        tab_container.append(self.tab_view)
        tab_container.set_vexpand(True)

        # Crear pestañas
        self.create_info_tab()
        self.create_comics_tab()

        scrolled.set_child(tab_container)
        window_box.append(scrolled)
        self.set_content(window_box)

    def create_info_tab(self):
        """Crear pestaña de información del volumen"""
        # Crear contenido de la pestaña de información
        info_scroll = Gtk.ScrolledWindow()
        info_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        info_box.set_margin_start(20)
        info_box.set_margin_end(20)
        info_box.set_margin_top(20)
        info_box.set_margin_bottom(20)

        # Crear secciones de información
        self.create_header_section(info_box)
        self.create_info_section(info_box)
        self.create_publisher_section(info_box)

        info_scroll.set_child(info_box)

        # Crear pestaña
        info_page = self.tab_view.append(info_scroll)
        info_page.set_title("Información")
        info_page.set_icon(Gio.ThemedIcon.new("info-outline-symbolic"))

    def create_comics_tab(self):
        """Crear pestaña dedicada a los cómics"""
        # Crear contenido de la pestaña de cómics
        comics_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        comics_box.set_margin_start(20)
        comics_box.set_margin_end(20)
        comics_box.set_margin_top(20)
        comics_box.set_margin_bottom(20)
        comics_box.set_vexpand(True)

        # Título de la sección
        comics_title = Gtk.Label(label=f"Issues de {self.volume.nombre}")
        comics_title.add_css_class("title-2")
        comics_title.set_halign(Gtk.Align.START)
        comics_title.set_margin_bottom(10)
        comics_box.append(comics_title)

        # FlowBox para los cómics - ahora usa toda la pestaña
        self.comics_flow_box = Gtk.FlowBox()
        self.comics_flow_box.set_valign(Gtk.Align.START)
        self.comics_flow_box.set_max_children_per_line(5)  # Ajustado para thumbnails más grandes
        self.comics_flow_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.comics_flow_box.set_homogeneous(True)
        self.comics_flow_box.set_column_spacing(15)
        self.comics_flow_box.set_row_spacing(15)
        self.comics_flow_box.set_vexpand(True)

        # Scroll para los cómics
        comics_scroll = Gtk.ScrolledWindow()
        comics_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        comics_scroll.set_vexpand(True)
        comics_scroll.set_child(self.comics_flow_box)

        comics_box.append(comics_scroll)

        # Crear pestaña
        comics_page = self.tab_view.append(comics_box)
        comics_page.set_title("Issues")
        comics_page.set_icon(Gio.ThemedIcon.new("view-list-symbolic"))

        # Cargar cómics (de forma asíncrona)
        GLib.idle_add(self.load_comics)

    def create_header_section(self, parent):
        """Crear sección de cabecera con imagen y datos básicos"""
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        header_box.set_margin_bottom(20)
        header_box.set_halign(Gtk.Align.FILL)
        header_box.set_hexpand(True)

        # Contenedor de imagen
        image_container = Gtk.Box()
        image_container.set_size_request(125, 175)

        # Imagen del volumen
        self.volume_image = Gtk.Picture()
        self.volume_image.set_can_shrink(True)
        self.volume_image.set_keep_aspect_ratio(True)
        self.volume_image.set_content_fit(Gtk.ContentFit.CONTAIN)
        self.volume_image.add_css_class("volume-detail-image")

        # Cargar imagen del volumen
        self.load_volume_image()

        image_container.append(self.volume_image)

        # Información básica
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        info_box.set_hexpand(True)
        info_box.set_vexpand(True)
        info_box.set_valign(Gtk.Align.START)

        # Título
        title_label = Gtk.Label(label=self.volume.nombre)
        title_label.set_halign(Gtk.Align.START)
        title_label.add_css_class("title-1")
        title_label.set_wrap(True)
        title_label.set_selectable(True)

        # Información básica en grid
        info_grid = self.create_info_grid()

        # Deck (descripción corta)
        if self.volume.deck:
            clean_deck = self.clean_html_text(self.volume.deck)
            deck_frame = self.create_info_frame("Resumen", clean_deck)
            info_box.append(deck_frame)

        info_box.append(title_label)
        info_box.append(info_grid)

        header_box.append(image_container)
        header_box.append(info_box)

        parent.append(header_box)

    def create_info_grid(self):
        """Crear grid con información básica del volumen"""
        grid = Gtk.Grid()
        grid.set_row_spacing(8)
        grid.set_column_spacing(20)

        row = 0

        # ID
        self.add_info_row(grid, row, "ID", f"#{self.volume.id_volume}")
        row += 1

        # Año de inicio
        if self.volume.anio_inicio > 0:
            self.add_info_row(grid, row, "Año de inicio", str(self.volume.anio_inicio))
            row += 1

        # Total de números
        self.add_info_row(grid, row, "Total de números", str(self.volume.cantidad_numeros))
        row += 1

        # Completitud (se calculará dinámicamente)
        self.completion_label = Gtk.Label()
        self.completion_label.set_halign(Gtk.Align.START)
        self.add_info_row(grid, row, "Completitud", "Calculando...")
        grid.attach(self.completion_label, 1, row, 1, 1)
        row += 1

        # URL si existe
        if self.volume.url:
            url_label = Gtk.Label(label=self.volume.url)
            url_label.set_halign(Gtk.Align.START)
            url_label.add_css_class("link")
            url_label.set_selectable(True)
            self.add_info_row(grid, row, "URL", "")
            grid.attach(url_label, 1, row, 1, 1)
            row += 1

        return grid

    def add_info_row(self, grid, row, label_text, value_text):
        """Agregar una fila de información al grid"""
        # Label
        label = Gtk.Label(label=f"{label_text}:")
        label.set_halign(Gtk.Align.END)
        label.add_css_class("caption-heading")
        grid.attach(label, 0, row, 1, 1)

        # Valor
        if value_text:
            value = Gtk.Label(label=value_text)
            value.set_halign(Gtk.Align.START)
            value.set_selectable(True)
            grid.attach(value, 1, row, 1, 1)

    def create_info_section(self, parent):
        """Crear sección de descripción detallada"""
        if self.volume.descripcion:
            clean_desc = self.clean_html_text(self.volume.descripcion)
            desc_frame = self.create_info_frame("Descripción", clean_desc)
            parent.append(desc_frame)

    def create_publisher_section(self, parent):
        """Crear sección de editorial"""
        try:
            if self.volume.id_publisher > 0:
                publisher = self.session.query(Publisher).filter(
                    Publisher.id_publisher == self.volume.id_publisher
                ).first()

                if publisher:
                    # Frame de editorial
                    publisher_frame = Adw.PreferencesGroup()
                    publisher_frame.set_title("Editorial")
                    publisher_frame.set_margin_top(20)

                    # Crear fila de editorial
                    publisher_row = Adw.ActionRow()
                    publisher_row.set_title(publisher.nombre)
                    if hasattr(publisher, 'deck') and publisher.deck:
                        publisher_row.set_subtitle(publisher.deck)

                    # Icono de editorial
                    publisher_icon = Gtk.Image.new_from_icon_name("folder-symbolic")
                    publisher_row.add_prefix(publisher_icon)

                    publisher_frame.add(publisher_row)
                    parent.append(publisher_frame)

        except Exception as e:
            print(f"Error cargando editorial: {e}")


    def create_info_frame(self, title, content):
        """Crear un frame de información con título y contenido"""
        frame = Adw.PreferencesGroup()
        frame.set_title(title)
        frame.set_margin_top(20)

        # Para contenido largo, usar scroll con altura limitada
        if len(content) > 200:
            # Crear ScrolledWindow con altura limitada
            desc_scroll = Gtk.ScrolledWindow()
            desc_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            desc_scroll.set_max_content_height(150)  # Limitar altura
            desc_scroll.set_propagate_natural_height(True)

            content_label = Gtk.Label(label=content)
            content_label.set_wrap(True)
            content_label.set_halign(Gtk.Align.START)
            content_label.set_valign(Gtk.Align.START)
            content_label.set_selectable(True)
            content_label.set_margin_start(12)
            content_label.set_margin_end(12)
            content_label.set_margin_top(12)
            content_label.set_margin_bottom(12)

            desc_scroll.set_child(content_label)
            frame.add(desc_scroll)

        elif len(content) > 100:
            # Contenido mediano sin scroll
            content_label = Gtk.Label(label=content)
            content_label.set_wrap(True)
            content_label.set_halign(Gtk.Align.START)
            content_label.set_selectable(True)
            content_label.set_margin_start(12)
            content_label.set_margin_end(12)
            content_label.set_margin_top(12)
            content_label.set_margin_bottom(12)

            frame.add(content_label)
        else:
            # Contenido corto en ActionRow
            content_row = Adw.ActionRow()
            content_row.set_title(content)
            frame.add(content_row)

        return frame

    def load_volume_image(self):
        """Cargar imagen del volumen"""
        try:
            cover_path = self.volume.obtener_cover()
            if cover_path and os.path.exists(cover_path):
                # Si tenemos imagen real, cargarla
                if not cover_path.endswith("Volumen_sin_caratula.png"):
                    self.volume_image.set_filename(cover_path)
                else:
                    # Usar placeholder
                    self.set_placeholder_image()
            else:
                self.set_placeholder_image()
        except Exception as e:
            print(f"Error cargando imagen del volumen: {e}")
            self.set_placeholder_image()

    def set_placeholder_image(self):
        """Configurar imagen placeholder"""
        try:
            pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 250, 350)
            pixbuf.fill(0x33D17AFF)  # Verde para volúmenes
            texture = Gdk.Texture.new_for_pixbuf(pixbuf)
            self.volume_image.set_paintable(texture)
        except Exception as e:
            print(f"Error creando placeholder: {e}")

    def load_volume_data(self):
        """Cargar datos adicionales del volumen"""
        GLib.idle_add(self.calculate_completion)

    def calculate_completion(self):
        """Calcular completitud del volumen"""
        try:
            owned_count = 0
            percentage = 0

            if Comicbook and ComicbookInfo:
                # Contar comics físicos para este volumen usando subquery
                subquery = self.session.query(ComicbookInfo.id_comicbook_info).filter(
                    ComicbookInfo.id_volume == self.volume.id_volume
                ).subquery()

                owned_count = self.session.query(Comicbook).filter(
                    Comicbook.id_comicbook_info.in_(
                        self.session.query(subquery.c.id_comicbook_info)
                    )
                ).count()

            # Calcular porcentaje
            if self.volume.cantidad_numeros > 0:
                percentage = (owned_count / self.volume.cantidad_numeros) * 100
                completion_text = f"{owned_count}/{self.volume.cantidad_numeros} ({percentage:.1f}%)"
            else:
                completion_text = f"{owned_count}/? cómics"

            # Actualizar label
            self.completion_label.set_text(completion_text)

            # Colorear según completitud
            if percentage == 100:
                self.completion_label.add_css_class("success")
            elif percentage >= 50:
                self.completion_label.add_css_class("accent")
            elif percentage > 0:
                self.completion_label.add_css_class("warning")
            else:
                self.completion_label.add_css_class("dim-label")

        except Exception as e:
            print(f"Error calculando completitud: {e}")
            self.completion_label.set_text("Error calculando")

        return False  # No repetir

    def load_comics(self):
        """Cargar cómics del volumen (físicos y metadata)"""
        try:
            if not ComicbookInfo:
                print("No se pueden cargar cómics - faltan dependencias")
                return False

            # Obtener todos los ComicbookInfo para este volumen
            comic_infos = self.session.query(ComicbookInfo).filter(
                ComicbookInfo.id_volume == self.volume.id_volume
            ).order_by(ComicbookInfo.numero.cast(Integer), ComicbookInfo.numero).all()

            print(f"Encontrados {len(comic_infos)} cómics info para el volumen {self.volume.nombre}")

            # Agregar cada comic_info como card con contador de físicos
            for comic_info in comic_infos:
                try:
                    # Contar cómics físicos asociados a este metadata
                    physical_count = 0
                    if Comicbook:
                        physical_count = self.session.query(Comicbook).filter(
                            Comicbook.id_comicbook_info == comic_info.id_comicbook_info
                        ).count()

                    # Crear card para metadata con contador
                    comic_card = self.create_issue_card(comic_info, physical_count)

                    # Tamaños reducidos para mejor visualización
                    comic_card.set_size_request(110, 175)

                    # Hacer que sea clickeable para ver físicos de este issue
                    click_gesture = Gtk.GestureClick()
                    click_gesture.connect("pressed", self.on_issue_clicked, comic_info, physical_count)
                    comic_card.add_controller(click_gesture)

                    self.comics_flow_box.append(comic_card)

                except Exception as e:
                    print(f"Error creando card para comic_info {comic_info.id_comicbook_info}: {e}")

        except Exception as e:
            print(f"Error cargando cómics: {e}")
            # Como fallback, mostrar mensaje de que no se pudieron cargar
            error_label = Gtk.Label(label="No se pudieron cargar los cómics de este volumen")
            error_label.add_css_class("dim-label")
            error_label.set_margin_top(20)
            self.comics_flow_box.append(error_label)

        return False  # No repetir

    def create_issue_card(self, comic_info, physical_count):
        """Crear card para issue con contador de cómics físicos"""
        # Usar BaseCard como base
        from comic_cards import BaseCard

        class IssueCard(BaseCard):
            def __init__(self, comic_info, physical_count, thumbnail_generator):
                self.physical_count = physical_count
                super().__init__(comic_info, "issue", thumbnail_generator)

            def create_info_box(self):
                """Crear información del issue"""
                info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
                info_box.set_margin_start(8)
                info_box.set_margin_end(8)
                info_box.set_margin_bottom(8)

                # Título
                title = self.item.titulo or f"Issue #{self.item.numero}"
                title_label = Gtk.Label(label=title)
                title_label.set_wrap(True)
                title_label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
                title_label.set_width_chars(35)
                title_label.set_max_width_chars(35)
                title_label.set_lines(2)
                title_label.set_ellipsize(Pango.EllipsizeMode.END)
                title_label.set_justify(Gtk.Justification.CENTER)
                title_label.add_css_class("heading")

                # Información adicional
                extra_info = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                extra_info.set_halign(Gtk.Align.CENTER)

                # Número
                numero_label = Gtk.Label(label=f"#{self.item.numero}")
                numero_label.add_css_class("dim-label")
                numero_label.add_css_class("caption")

                # Contador de físicos
                status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
                if self.physical_count > 0:
                    status_icon = Gtk.Image.new_from_icon_name("folder-documents-symbolic")
                    status_text = f"{self.physical_count} físico{'s' if self.physical_count != 1 else ''}"
                    status_box.add_css_class("success")
                else:
                    status_icon = Gtk.Image.new_from_icon_name("folder-symbolic")
                    status_text = "Sin físicos"
                    status_box.add_css_class("dim-label")

                status_icon.set_icon_size(Gtk.IconSize.INHERIT)
                status_label = Gtk.Label(label=status_text)
                status_label.add_css_class("caption")
                status_box.append(status_icon)
                status_box.append(status_label)

                # Calificación si existe
                if self.item.calificacion > 0:
                    stars = int(self.item.calificacion)
                    rating_text = "★" * stars + "☆" * (5 - stars)
                    rating_label = Gtk.Label(label=rating_text)
                    rating_label.add_css_class("caption")
                    rating_label.add_css_class("accent")
                    extra_info.append(rating_label)

                extra_info.append(numero_label)
                extra_info.append(status_box)

                info_box.append(title_label)
                info_box.append(extra_info)

                return info_box

            def request_thumbnail(self):
                """Solicitar thumbnail del issue"""
                try:
                    cover_path = self.item.obtener_portada_principal()
                    if cover_path and os.path.exists(cover_path) and not cover_path.endswith("Comic_sin_caratula.png"):
                        # Generar thumbnail para la portada del issue
                        self.thumbnail_generator.request_thumbnail(
                            cover_path,
                            f"issue_{self.item.id_comicbook_info}",
                            "comicinfo",
                            self.load_thumbnail
                        )
                    else:
                        # Usar placeholder con color según si tiene físicos
                        self.set_issue_placeholder()
                except Exception as e:
                    print(f"Error cargando thumbnail de issue: {e}")
                    self.set_issue_placeholder()

            def set_issue_placeholder(self):
                """Placeholder específico para issues"""
                try:
                    # Color verde si tiene físicos, gris si no tiene
                    color = 0x33D17AFF if self.physical_count > 0 else 0x808080FF
                    pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 250, 350)
                    pixbuf.fill(color)
                    texture = Gdk.Texture.new_for_pixbuf(pixbuf)
                    self.image.set_paintable(texture)
                except Exception as e:
                    print(f"Error creando placeholder de issue: {e}")

        return IssueCard(comic_info, physical_count, self.thumbnail_generator)

    def on_issue_clicked(self, gesture, n_press, x, y, comic_info, physical_count):
        """Manejar click en un issue (ComicbookInfo)"""
        if n_press == 2:  # Doble click
            print(f"Doble click en issue: {comic_info.titulo} #{comic_info.numero} ({physical_count} físicos)")

            if physical_count > 0:
                # Abrir vista de físicos para este issue
                self.show_physical_comics_view(comic_info)
            else:
                # Mostrar mensaje de que no hay físicos
                print(f"No hay cómics físicos para este issue")
                # Aquí podrías mostrar un diálogo para asociar archivos físicos

    def show_physical_comics_view(self, comic_info):
        """Mostrar vista de cómics físicos para un ComicbookInfo específico"""
        print(f"Navegando a vista de físicos para: {comic_info.titulo} #{comic_info.numero}")

        try:
            # Si estamos en NavigationView, usar navegación
            root = self.get_root()
            if hasattr(root, 'navigate_to_physical_comics'):
                root.navigate_to_physical_comics(comic_info)
                print(f"Navegación a físicos para issue #{comic_info.numero}")
            else:
                # Fallback: crear ventana separada (modo legacy)
                physical_window = PhysicalComicsWindow(
                    comic_info=comic_info,
                    session=self.session,
                    thumbnail_generator=self.thumbnail_generator,
                    application=self.get_application()
                )
                physical_window.present()
                print(f"Vista de físicos abierta en ventana separada para issue #{comic_info.numero}")

        except Exception as e:
            print(f"Error abriendo vista de físicos: {e}")
            import traceback
            traceback.print_exc()