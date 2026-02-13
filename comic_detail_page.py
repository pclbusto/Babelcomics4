#!/usr/bin/env python3
"""
comic_detail_page.py - Página de detalle de cómic para Navigation View
"""

import gi
import os
import re
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GdkPixbuf, Gdk, Pango, GLib, GObject, Gio

try:
    from entidades.comicbook_model import Comicbook
    from entidades.comicbook_detail_model import Comicbook_Detail
    from comic_cards import ComicCard, BaseCard
except ImportError as e:
    print(f"Error importando entidades: {e}")


def create_comic_detail_page(comic, session, thumbnail_generator, main_window):
    """Crear página de detalle del cómic para NavigationView"""

    # Crear la página de navegación
    page = Adw.NavigationPage()
    page.set_title(f"Cómic #{comic.id_comicbook}")

    # Crear contenido principal
    content = create_comic_detail_content(comic, session, thumbnail_generator, main_window)
    page.set_child(content)

    return page


def create_comic_detail_content(comic, session, thumbnail_generator, main_window):
    """Crear contenido de detalle del cómic"""

    # Contenedor principal con scroll
    scrolled = Gtk.ScrolledWindow()
    scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scrolled.set_vexpand(True)

    # TabView y TabBar para organizar el contenido
    tab_view = Adw.TabView()
    tab_view.set_vexpand(True)

    tab_bar = Adw.TabBar()
    tab_bar.set_view(tab_view)

    # Contenedor para tab bar y contenido
    tab_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
    tab_container.append(tab_bar)
    tab_container.append(tab_view)
    tab_container.set_vexpand(True)

    # Crear pestañas
    create_info_tab(tab_view, comic, session, thumbnail_generator, main_window)
    create_pages_tab(tab_view, comic, session, thumbnail_generator, main_window)

    scrolled.set_child(tab_container)
    return scrolled


def create_info_tab(tab_view, comic, session, thumbnail_generator, main_window):
    """Crear pestaña de información del cómic"""
    info_scroll = Gtk.ScrolledWindow()
    info_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

    info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
    info_box.set_margin_start(20)
    info_box.set_margin_end(20)
    info_box.set_margin_top(20)
    info_box.set_margin_bottom(20)

    # Header section con imagen y datos básicos
    create_comic_header_section(info_box, comic, session, thumbnail_generator, main_window)

    # Información detallada
    create_comic_info_section(info_box, comic)

    info_scroll.set_child(info_box)

    # Crear pestaña
    info_page = tab_view.append(info_scroll)
    info_page.set_title("Información")
    info_page.set_icon(Gio.ThemedIcon.new("info-outline-symbolic"))


def create_pages_tab(tab_view, comic, session, thumbnail_generator, main_window):
    """Crear pestaña de páginas del cómic"""
    pages_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    pages_box.set_margin_start(20)
    pages_box.set_margin_end(20)
    pages_box.set_margin_top(20)
    pages_box.set_margin_bottom(20)
    pages_box.set_vexpand(True)

    # Título de la sección
    pages_title = Gtk.Label(label=f"Páginas del Cómic")
    pages_title.add_css_class("title-2")
    pages_title.set_halign(Gtk.Align.START)
    pages_title.set_margin_bottom(10)
    pages_box.append(pages_title)

    # FlowBox para las páginas
    pages_flow_box = Gtk.FlowBox()
    pages_flow_box.set_valign(Gtk.Align.START)
    pages_flow_box.set_max_children_per_line(6)
    pages_flow_box.set_selection_mode(Gtk.SelectionMode.NONE)
    pages_flow_box.set_homogeneous(True)
    pages_flow_box.set_column_spacing(10)
    pages_flow_box.set_row_spacing(10)
    pages_flow_box.set_vexpand(True)

    # Scroll para las páginas
    pages_scroll = Gtk.ScrolledWindow()
    pages_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    pages_scroll.set_vexpand(True)
    pages_scroll.set_child(pages_flow_box)

    pages_box.append(pages_scroll)

    # Crear pestaña
    pages_page = tab_view.append(pages_box)
    pages_page.set_title("Páginas")
    pages_page.set_icon(Gio.ThemedIcon.new("view-grid-symbolic"))

    # Cargar páginas automáticamente
    GLib.idle_add(load_comic_pages_auto, comic, session, thumbnail_generator, main_window, pages_flow_box)


def create_comic_header_section(parent, comic, session, thumbnail_generator, main_window):
    """Crear sección de cabecera con imagen y datos básicos"""
    header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
    header_box.set_margin_bottom(20)
    header_box.set_halign(Gtk.Align.FILL)
    header_box.set_hexpand(True)

    # Contenedor de imagen con carrusel para múltiples covers
    image_container = create_covers_carousel(comic, session)
    image_container.set_size_request(120, 160)

    # Información básica
    info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
    info_box.set_hexpand(True)
    info_box.set_vexpand(True)
    info_box.set_valign(Gtk.Align.START)

    # Título del archivo
    title_label = Gtk.Label(label=os.path.basename(comic.path))
    title_label.set_halign(Gtk.Align.START)
    title_label.add_css_class("title-1")
    title_label.set_wrap(True)
    title_label.set_selectable(True)

    # Información básica en grid
    info_grid = create_comic_info_grid(comic, session)

    # Botones de acción
    action_box = create_comic_action_buttons(comic, main_window)

    info_box.append(title_label)
    info_box.append(info_grid)
    info_box.append(action_box)

    header_box.append(image_container)
    header_box.append(info_box)

    parent.append(header_box)


def create_comic_action_buttons(comic, main_window):
    """Crear botones de acción para el comic"""
    action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
    action_box.set_margin_top(15)
    action_box.set_halign(Gtk.Align.START)

    # Botón Leer Comic
    read_button = Gtk.Button()
    read_button.set_label("📖 Leer Comic")
    read_button.add_css_class("suggested-action")
    read_button.set_tooltip_text("Abrir con el lector integrado")

    def on_read_comic(button):
        try:
            # Verificar si el lector está disponible
            try:
                from comic_reader import open_comic_with_reader

                print(f"\n🔧 DEBUG on_read_comic:")
                print(f"  comic.path: {comic.path}")
                print(f"  ¿Es absoluto?: {os.path.isabs(comic.path)}")
                print(f"  ¿Existe?: {os.path.exists(comic.path)}")

                # Verificar que el archivo existe
                if not os.path.exists(comic.path):
                    print(f"  ❌ Archivo NO existe en: {comic.path}")
                    if hasattr(main_window, 'show_toast'):
                        main_window.show_toast("Archivo de comic no encontrado", "error")
                    return

                print(f"  ✅ Archivo existe, abriendo lector...")

                # Obtener nombre del comic para el título
                comic_title = os.path.basename(comic.path)

                # Abrir el lector con configuración de scroll
                scroll_threshold = None
                scroll_cooldown = None
                if hasattr(main_window, 'config'):
                    scroll_threshold = main_window.config.scroll_threshold
                    scroll_cooldown = main_window.config.scroll_cooldown

                reader = open_comic_with_reader(
                    comic.path,
                    comic_title,
                    main_window,
                    scroll_threshold=scroll_threshold,
                    scroll_cooldown=scroll_cooldown
                )

                if reader:
                    if hasattr(main_window, 'show_toast'):
                        main_window.show_toast("Abriendo lector de comics...", "info")
                else:
                    if hasattr(main_window, 'show_toast'):
                        main_window.show_toast("Error abriendo lector de comics", "error")

            except ImportError:
                if hasattr(main_window, 'show_toast'):
                    main_window.show_toast("Lector de comics no disponible", "error")

        except Exception as e:
            print(f"Error abriendo lector: {e}")
            if hasattr(main_window, 'show_toast'):
                main_window.show_toast(f"Error abriendo lector: {e}", "error")

    read_button.connect("clicked", on_read_comic)
    action_box.append(read_button)

    # Botón Abrir Carpeta
    folder_button = Gtk.Button()
    folder_button.set_label("📁 Abrir Carpeta")
    folder_button.set_tooltip_text("Mostrar archivo en el explorador")

    def on_open_folder(button):
        try:
            import subprocess
            import sys
            folder_path = os.path.dirname(comic.path)

            if sys.platform == "linux":
                subprocess.run(["xdg-open", folder_path])
            elif sys.platform == "darwin":
                subprocess.run(["open", folder_path])
            elif sys.platform == "win32":
                subprocess.run(["explorer", folder_path])

            if hasattr(main_window, 'show_toast'):
                main_window.show_toast("Carpeta abierta", "info")

        except Exception as e:
            print(f"Error abriendo carpeta: {e}")
            if hasattr(main_window, 'show_toast'):
                main_window.show_toast(f"Error abriendo carpeta: {e}", "error")

    folder_button.connect("clicked", on_open_folder)
    action_box.append(folder_button)

    return action_box


def create_comic_info_grid(comic, session):
    """Crear grid con información básica del cómic"""
    grid = Gtk.Grid()
    grid.set_row_spacing(8)
    grid.set_column_spacing(20)

    row = 0

    # ID del cómic
    add_info_row(grid, row, "ID", f"#{comic.id_comicbook}")
    row += 1

    # Estado de clasificación
    classification_status = "Clasificado" if comic.id_comicbook_info else "Sin clasificar"
    add_info_row(grid, row, "Estado", classification_status)
    row += 1

    # Calidad
    add_info_row(grid, row, "Calidad", str(comic.calidad))
    row += 1

    # En papelera
    trash_status = "Sí" if comic.en_papelera else "No"
    add_info_row(grid, row, "En papelera", trash_status)
    row += 1

    # Path completo
    path_label = Gtk.Label(label=comic.path)
    path_label.set_halign(Gtk.Align.START)
    path_label.set_selectable(True)
    path_label.set_wrap(True)
    path_label.add_css_class("monospace")
    add_info_row(grid, row, "Archivo", "")
    grid.attach(path_label, 1, row, 1, 1)
    row += 1

    return grid


def add_info_row(grid, row, label_text, value_text):
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


def create_comic_info_section(parent, comic):
    """Crear sección de información adicional del cómic"""
    # Si hay ID de ComicbookInfo, mostrar información adicional
    if comic.id_comicbook_info:
        info_frame = Adw.PreferencesGroup()
        info_frame.set_title("Información de Catalogación")
        info_frame.set_margin_top(20)

        # ID de ComicbookInfo
        info_row = Adw.ActionRow()
        info_row.set_title("ID de ComicbookInfo")
        info_row.set_subtitle(comic.id_comicbook_info)

        info_frame.add(info_row)
        parent.append(info_frame)


def create_covers_carousel(comic, session):
    """Crear carrusel de covers para el comic"""
    try:
        # Contenedor principal del carrusel
        carousel_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)

        # Obtener covers de ComicbookInfo si existe
        covers = []
        if comic.id_comicbook_info:
            try:
                from entidades.comicbook_info_model import ComicbookInfo
                comicbook_info = session.query(ComicbookInfo).get(comic.id_comicbook_info)
                if comicbook_info and comicbook_info.portadas:
                    covers = list(comicbook_info.portadas)
            except Exception as e:
                print(f"Error obteniendo covers de ComicbookInfo: {e}")

        # Si no hay covers de ComicbookInfo, usar la cover del comic
        if not covers:
            covers = [None]  # Placeholder para cover principal del comic

        # Crear carrusel solo si hay múltiples covers
        if len(covers) > 1:
            # AdwCarousel para múltiples covers
            carousel = Adw.Carousel()
            carousel.set_size_request(120, 160)
            carousel.set_allow_mouse_drag(True)
            carousel.set_allow_scroll_wheel(True)

            # Agregar cada cover al carrusel
            for i, cover in enumerate(covers):
                cover_image = Gtk.Picture()
                cover_image.set_can_shrink(True)
                cover_image.set_keep_aspect_ratio(True)
                cover_image.set_content_fit(Gtk.ContentFit.CONTAIN)
                cover_image.set_size_request(120, 160)
                cover_image.add_css_class("comic-detail-image")

                # Cargar imagen de la cover
                load_cover_image(cover_image, cover, comic)

                carousel.append(cover_image)

            # Indicador de páginas (dots)
            dots = Adw.CarouselIndicatorDots()
            dots.set_carousel(carousel)

            # Label con cantidad de covers
            cover_count_label = Gtk.Label()
            cover_count_label.set_text(f"{len(covers)} covers")
            cover_count_label.add_css_class("dim-label")
            cover_count_label.add_css_class("caption")
            cover_count_label.set_halign(Gtk.Align.CENTER)

            carousel_container.append(carousel)
            carousel_container.append(dots)
            carousel_container.append(cover_count_label)

        else:
            # Solo una cover: mostrar imagen simple
            single_image = Gtk.Picture()
            single_image.set_can_shrink(True)
            single_image.set_keep_aspect_ratio(True)
            single_image.set_content_fit(Gtk.ContentFit.CONTAIN)
            single_image.set_size_request(120, 160)
            single_image.add_css_class("comic-detail-image")

            # Cargar la única cover disponible
            cover = covers[0] if covers else None
            load_cover_image(single_image, cover, comic)

            carousel_container.append(single_image)

        return carousel_container

    except Exception as e:
        print(f"Error creando carrusel de covers: {e}")
        # Fallback: crear imagen simple
        return create_simple_cover_image(comic)

def create_simple_cover_image(comic):
    """Crear imagen simple como fallback"""
    image_container = Gtk.Box()
    comic_image = Gtk.Picture()
    comic_image.set_can_shrink(True)
    comic_image.set_keep_aspect_ratio(True)
    comic_image.set_content_fit(Gtk.ContentFit.CONTAIN)
    comic_image.set_size_request(120, 160)
    comic_image.add_css_class("comic-detail-image")

    load_comic_image(comic_image, comic)
    image_container.append(comic_image)
    return image_container

def load_cover_image(cover_image, cover, comic):
    """Cargar imagen de cover (de ComicbookInfo o del comic)"""
    try:
        if cover is not None:
            # Es una cover de ComicbookInfo, usar ruta local
            cover_path = cover.obtener_ruta_local()
            if cover_path and os.path.exists(cover_path):
                if not cover_path.endswith("Comic_sin_caratula.png"):
                    cover_image.set_filename(cover_path)
                else:
                    set_comic_placeholder_image(cover_image)
            else:
                set_comic_placeholder_image(cover_image)
        else:
            # Usar cover del comic (fallback)
            load_comic_image(cover_image, comic)

    except Exception as e:
        print(f"Error cargando cover: {e}")
        set_comic_placeholder_image(cover_image)

def load_comic_image(comic_image, comic):
    """Cargar imagen del cómic"""
    try:
        cover_path = comic.obtener_cover()
        if cover_path and os.path.exists(cover_path):
            if not cover_path.endswith("Comic_sin_caratula.png"):
                comic_image.set_filename(cover_path)
            else:
                set_comic_placeholder_image(comic_image)
        else:
            set_comic_placeholder_image(comic_image)
    except Exception as e:
        print(f"Error cargando imagen del cómic: {e}")
        set_comic_placeholder_image(comic_image)


def set_comic_placeholder_image(comic_image):
    """Configurar imagen placeholder para cómic"""
    try:
        pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 100, 140)
        pixbuf.fill(0x3584E4FF)  # Azul para cómics
        texture = Gdk.Texture.new_for_pixbuf(pixbuf)
        comic_image.set_paintable(texture)
    except Exception as e:
        print(f"Error creando placeholder de cómic: {e}")


def load_comic_pages_auto(comic, session, thumbnail_generator, main_window, pages_flow_box):
    """Cargar páginas del cómic automáticamente, extrayendo si es necesario"""
    try:
        # Verificar si ya tenemos páginas en BD
        existing_pages = session.query(Comicbook_Detail).filter(
            Comicbook_Detail.comicbook_id == comic.id_comicbook
        ).order_by(Comicbook_Detail.ordenPagina).all()

        if existing_pages:
            # Ya tenemos páginas: mostrarlas inmediatamente
            print(f"✅ Cargando {len(existing_pages)} páginas existentes del cómic {comic.id_comicbook}")
            load_existing_pages(existing_pages, comic, session, main_window, pages_flow_box)
        else:
            # No tenemos páginas: mostrar placeholders y extraer
            print(f"🔄 Extrayendo páginas del cómic {comic.id_comicbook} por primera vez...")
            extract_and_load_pages(comic, session, thumbnail_generator, main_window, pages_flow_box)

    except Exception as e:
        print(f"Error en carga automática: {e}")
        show_error_message(pages_flow_box, "Error cargando páginas del cómic")

    return False


def load_existing_pages(pages, comic, session, main_window, pages_flow_box):
    """Cargar páginas existentes desde BD"""
    try:
        for page in pages:
            # Crear card para la página
            page_card = create_page_card_with_progressive_loading(page, comic, session, main_window)
            page_card.set_size_request(150, 200)

            # Menú contextual para cambiar tipo de página
            setup_page_context_menu(page_card, page, comic, session, main_window, pages_flow_box)

            pages_flow_box.append(page_card)

    except Exception as e:
        print(f"Error cargando páginas existentes: {e}")


def extract_and_load_pages(comic, session, thumbnail_generator, main_window, pages_flow_box):
    """Extraer páginas por primera vez y mostrar progresivamente"""
    try:
        # Mostrar mensaje de carga
        loading_label = Gtk.Label(label="🔄 Extrayendo páginas del archivo...")
        loading_label.add_css_class("title-3")
        loading_label.set_margin_top(50)
        pages_flow_box.append(loading_label)

        # Función worker para extracción
        def extraction_worker():
            try:
                from helpers.comic_extractor import ComicExtractor

                # Crear extractor
                extractor = ComicExtractor()

                # Verificar si el archivo es válido
                comic_format = extractor.detect_comic_format(comic.path)
                if not comic_format:
                    GLib.idle_add(show_extraction_error, pages_flow_box, "Formato de archivo no soportado")
                    return

                # Extraer páginas temporalmente y poblar BD
                success = extractor.process_comic(comic, session)

                if success:
                    # Obtener páginas recién creadas
                    new_pages = session.query(Comicbook_Detail).filter(
                        Comicbook_Detail.comicbook_id == comic.id_comicbook
                    ).order_by(Comicbook_Detail.ordenPagina).all()

                    # Actualizar UI en hilo principal
                    GLib.idle_add(show_extracted_pages, new_pages, comic, session, main_window, pages_flow_box, loading_label)
                else:
                    GLib.idle_add(show_extraction_error, pages_flow_box, "Error extrayendo páginas")

            except Exception as e:
                print(f"Error en worker de extracción: {e}")
                GLib.idle_add(show_extraction_error, pages_flow_box, f"Error: {e}")

        # Iniciar extracción en hilo separado
        import threading
        extraction_thread = threading.Thread(target=extraction_worker, daemon=True)
        extraction_thread.start()

    except Exception as e:
        print(f"Error iniciando extracción: {e}")
        show_error_message(pages_flow_box, f"Error iniciando extracción: {e}")


def show_extracted_pages(pages, comic, session, main_window, pages_flow_box, loading_label):
    """Mostrar páginas recién extraídas"""
    try:
        # Quitar mensaje de carga
        if loading_label:
            pages_flow_box.remove(loading_label)

        # Mostrar toast de éxito
        if hasattr(main_window, 'toast_overlay'):
            toast = Adw.Toast.new(f"✅ Extraídas {len(pages)} páginas")
            toast.set_timeout(3)
            main_window.toast_overlay.add_toast(toast)

        # Cargar páginas con carga progresiva de thumbnails
        for page in pages:
            page_card = create_page_card_with_progressive_loading(page, comic, session, main_window)
            page_card.set_size_request(150, 200)

            # Menú contextual
            setup_page_context_menu(page_card, page, comic, session, main_window, pages_flow_box)

            pages_flow_box.append(page_card)

    except Exception as e:
        print(f"Error mostrando páginas extraídas: {e}")


def show_extraction_error(pages_flow_box, error_message):
    """Mostrar error de extracción"""
    try:
        # Limpiar contenido
        child = pages_flow_box.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            pages_flow_box.remove(child)
            child = next_child

        # Mostrar error
        error_label = Gtk.Label(label=f"❌ {error_message}")
        error_label.add_css_class("dim-label")
        error_label.set_margin_top(50)
        pages_flow_box.append(error_label)

    except Exception as e:
        print(f"Error mostrando mensaje de error: {e}")


def show_error_message(pages_flow_box, message):
    """Mostrar mensaje de error genérico"""
    error_label = Gtk.Label(label=message)
    error_label.add_css_class("dim-label")
    error_label.set_margin_top(20)
    pages_flow_box.append(error_label)


def create_page_card_with_progressive_loading(page, comic, session, main_window):
    """Crear card para una página con carga progresiva de thumbnails"""

    # Card container
    card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
    card.add_css_class("card")
    card.set_margin_start(5)
    card.set_margin_end(5)
    card.set_margin_top(5)
    card.set_margin_bottom(5)

    # Imagen de la página
    page_image = Gtk.Picture()
    page_image.set_can_shrink(True)
    page_image.set_keep_aspect_ratio(True)
    page_image.set_content_fit(Gtk.ContentFit.CONTAIN)
    page_image.set_size_request(140, 160)

    # Inicialmente mostrar placeholder
    set_page_placeholder_with_loading(page_image, page)

    # Intentar cargar thumbnail progresivamente
    GLib.idle_add(load_page_thumbnail_progressive, page_image, page, comic)

    # Info de la página
    info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
    info_box.set_margin_start(5)
    info_box.set_margin_end(5)
    info_box.set_margin_bottom(5)

    # Número de página
    page_label = Gtk.Label(label=f"Página {page.ordenPagina}")
    page_label.add_css_class("caption")
    page_label.set_halign(Gtk.Align.CENTER)

    # Tipo de página
    page_type = "COVER" if page.tipoPagina == 1 else "INTERNAL"
    type_label = Gtk.Label(label=page_type)
    type_label.add_css_class("caption")
    if page.tipoPagina == 1:  # COVER
        type_label.add_css_class("success")
    else:
        type_label.add_css_class("dim-label")
    type_label.set_halign(Gtk.Align.CENTER)

    # Nombre del archivo
    filename_label = Gtk.Label(label=page.nombre_pagina)
    filename_label.add_css_class("caption")
    filename_label.add_css_class("dim-label")
    filename_label.set_halign(Gtk.Align.CENTER)
    filename_label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
    filename_label.set_max_width_chars(20)

    # Tooltip con nombre completo
    filename_label.set_tooltip_text(f"Archivo: {page.nombre_pagina}")

    info_box.append(page_label)
    info_box.append(type_label)
    info_box.append(filename_label)

    card.append(page_image)
    card.append(info_box)

    return card


def create_page_card(page, comic, session, thumbnail_generator):
    """Crear card para una página del cómic (versión legacy)"""

    # Card container
    card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
    card.add_css_class("card")
    card.set_margin_start(5)
    card.set_margin_end(5)
    card.set_margin_top(5)
    card.set_margin_bottom(5)

    # Imagen de la página
    page_image = Gtk.Picture()
    page_image.set_can_shrink(True)
    page_image.set_keep_aspect_ratio(True)
    page_image.set_content_fit(Gtk.ContentFit.CONTAIN)
    page_image.set_size_request(140, 160)

    # Cargar thumbnail de la página
    load_page_thumbnail(page_image, page)

    # Info de la página
    info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
    info_box.set_margin_start(5)
    info_box.set_margin_end(5)
    info_box.set_margin_bottom(5)

    # Número de página
    page_label = Gtk.Label(label=f"Página {page.ordenPagina}")
    page_label.add_css_class("caption")
    page_label.set_halign(Gtk.Align.CENTER)

    # Tipo de página
    page_type = "COVER" if page.tipoPagina == 1 else "INTERNAL"
    type_label = Gtk.Label(label=page_type)
    type_label.add_css_class("caption")
    if page.tipoPagina == 1:  # COVER
        type_label.add_css_class("success")
    else:
        type_label.add_css_class("dim-label")
    type_label.set_halign(Gtk.Align.CENTER)

    # Nombre del archivo
    filename_label = Gtk.Label(label=page.nombre_pagina)
    filename_label.add_css_class("caption")
    filename_label.add_css_class("dim-label")
    filename_label.set_halign(Gtk.Align.CENTER)
    filename_label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
    filename_label.set_max_width_chars(20)

    # Tooltip con nombre completo
    filename_label.set_tooltip_text(f"Archivo: {page.nombre_pagina}")

    info_box.append(page_label)
    info_box.append(type_label)
    info_box.append(filename_label)

    card.append(page_image)
    card.append(info_box)

    return card


def load_page_thumbnail(page_image, page):
    """Cargar thumbnail de la página"""
    try:
        thumbnail_path = page.obtener_ruta_local()
        if thumbnail_path and os.path.exists(thumbnail_path):
            if not thumbnail_path.endswith("Comic_sin_caratula.png"):
                page_image.set_filename(thumbnail_path)
            else:
                set_page_placeholder_image(page_image)
        else:
            set_page_placeholder_image(page_image)
    except Exception as e:
        print(f"Error cargando thumbnail de página: {e}")
        set_page_placeholder_image(page_image)


def set_page_placeholder_image(page_image):
    """Configurar imagen placeholder para página"""
    try:
        pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 140, 160)
        pixbuf.fill(0xE5A50AFF)  # Amarillo para páginas
        texture = Gdk.Texture.new_for_pixbuf(pixbuf)
        page_image.set_paintable(texture)
    except Exception as e:
        print(f"Error creando placeholder de página: {e}")


def setup_page_context_menu(page_card, page, comic, session, main_window, pages_flow_box):
    """Configurar menú contextual para cambiar tipo de página"""

    # Crear gesture para click derecho
    right_click = Gtk.GestureClick()
    right_click.set_button(3)  # Botón derecho
    right_click.connect("pressed", on_page_right_click, page, comic, session, main_window, pages_flow_box)
    page_card.add_controller(right_click)


def on_page_right_click(gesture, n_press, x, y, page, comic, session, main_window, pages_flow_box):
    """Manejar click derecho en página"""
    try:
        # Crear menú popover
        popover = Gtk.PopoverMenu()

        # Crear acciones del menú
        menu_model = Gio.Menu()

        if page.tipoPagina != 1:  # No es COVER
            menu_model.append("Marcar como COVER", "page.set_cover")

        if page.tipoPagina != 0:  # No es INTERNAL
            menu_model.append("Marcar como INTERNAL", "page.set_internal")

        popover.set_menu_model(menu_model)

        # Configurar acciones
        action_group = Gio.SimpleActionGroup()

        # Acción para marcar como COVER
        set_cover_action = Gio.SimpleAction.new("set_cover", None)
        set_cover_action.connect("activate", lambda action, param: set_page_as_cover(page, comic, session, main_window, pages_flow_box))
        action_group.add_action(set_cover_action)

        # Acción para marcar como INTERNAL
        set_internal_action = Gio.SimpleAction.new("set_internal", None)
        set_internal_action.connect("activate", lambda action, param: set_page_as_internal(page, comic, session, main_window, pages_flow_box))
        action_group.add_action(set_internal_action)

        # Insertar grupo de acciones
        popover.insert_action_group("page", action_group)

        # Obtener widget desde el gesture
        widget = gesture.get_widget()
        popover.set_parent(widget)

        # Mostrar popover
        popover.popup()

    except Exception as e:
        print(f"Error creando menú contextual: {e}")


def set_page_as_cover(page, comic, session, main_window, pages_flow_box):
    """Marcar página como COVER (solo una por cómic)"""
    try:
        # Primero, cambiar todas las páginas de este cómic a INTERNAL
        session.query(Comicbook_Detail).filter(
            Comicbook_Detail.comicbook_id == comic.id_comicbook
        ).update({"tipoPagina": 0})  # 0 = INTERNAL

        # Luego, marcar esta página como COVER
        page.tipoPagina = 1  # 1 = COVER

        session.commit()

        # Refrescar la vista de páginas
        refresh_pages_view(comic, session, main_window, pages_flow_box)

        # Mostrar confirmación
        if hasattr(main_window, 'toast_overlay'):
            toast = Adw.Toast.new(f"Página {page.ordenPagina} marcada como COVER")
            main_window.toast_overlay.add_toast(toast)

        print(f"Página {page.ordenPagina} marcada como COVER")

    except Exception as e:
        print(f"Error marcando página como COVER: {e}")
        session.rollback()


def set_page_as_internal(page, comic, session, main_window, pages_flow_box):
    """Marcar página como INTERNAL"""
    try:
        page.tipoPagina = 0  # 0 = INTERNAL
        session.commit()

        # Refrescar la vista de páginas
        refresh_pages_view(comic, session, main_window, pages_flow_box)

        # Mostrar confirmación
        if hasattr(main_window, 'toast_overlay'):
            toast = Adw.Toast.new(f"Página {page.ordenPagina} marcada como INTERNAL")
            main_window.toast_overlay.add_toast(toast)

        print(f"Página {page.ordenPagina} marcada como INTERNAL")

    except Exception as e:
        print(f"Error marcando página como INTERNAL: {e}")
        session.rollback()


def refresh_pages_view(comic, session, main_window, pages_flow_box):
    """Refrescar la vista de páginas después de cambios"""
    try:
        # Limpiar contenido actual
        child = pages_flow_box.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            pages_flow_box.remove(child)
            child = next_child

        # Recargar páginas
        GLib.idle_add(load_comic_pages_auto, comic, session, main_window.thumbnail_generator, main_window, pages_flow_box)

    except Exception as e:
        print(f"Error refrescando vista de páginas: {e}")


def extract_comic_pages_async(comic, session, main_window, pages_box):
    """Extraer páginas del cómic de forma asíncrona"""
    try:
        # Mostrar progreso
        if hasattr(main_window, 'toast_overlay'):
            toast = Adw.Toast.new("Extrayendo páginas del cómic...")
            toast.set_timeout(2)
            main_window.toast_overlay.add_toast(toast)

        # Función para ejecutar en hilo separado
        def extract_worker():
            try:
                from helpers.comic_extractor import ComicExtractor

                # Crear extractor con callbacks
                def progress_cb(progress):
                    GLib.idle_add(update_extraction_progress, progress * 100)

                def status_cb(message):
                    GLib.idle_add(update_extraction_status, message)

                extractor = ComicExtractor(progress_cb, status_cb)

                # Procesar este cómic específico
                success = extractor.process_comic(comic, session)

                # Actualizar UI en hilo principal
                GLib.idle_add(extraction_complete, success, extractor.pages_extracted)

            except Exception as e:
                print(f"Error en extracción: {e}")
                GLib.idle_add(extraction_error, str(e))

        def update_extraction_progress(percent):
            if hasattr(main_window, 'toast_overlay'):
                toast = Adw.Toast.new(f"Extrayendo: {percent:.0f}%")
                toast.set_timeout(1)
                main_window.toast_overlay.add_toast(toast)

        def update_extraction_status(message):
            if hasattr(main_window, 'toast_overlay'):
                toast = Adw.Toast.new(message)
                toast.set_timeout(2)
                main_window.toast_overlay.add_toast(toast)

        def extraction_complete(success, pages_count):
            if success:
                if hasattr(main_window, 'toast_overlay'):
                    toast = Adw.Toast.new(f"✅ Extraídas {pages_count} páginas")
                    toast.set_timeout(3)
                    main_window.toast_overlay.add_toast(toast)

                # Refrescar vista de páginas
                refresh_pages_view(comic, session, main_window, find_pages_flow_box(pages_box))
            else:
                if hasattr(main_window, 'toast_overlay'):
                    toast = Adw.Toast.new("❌ Error extrayendo páginas")
                    toast.set_timeout(3)
                    main_window.toast_overlay.add_toast(toast)

        def extraction_error(error_msg):
            if hasattr(main_window, 'toast_overlay'):
                toast = Adw.Toast.new(f"❌ Error: {error_msg}")
                toast.set_timeout(4)
                main_window.toast_overlay.add_toast(toast)

        # Iniciar extracción en hilo separado
        import threading
        extraction_thread = threading.Thread(target=extract_worker, daemon=True)
        extraction_thread.start()

    except Exception as e:
        print(f"Error iniciando extracción: {e}")
        if hasattr(main_window, 'toast_overlay'):
            toast = Adw.Toast.new(f"❌ Error iniciando extracción: {e}")
            main_window.toast_overlay.add_toast(toast)


def find_pages_flow_box(pages_box):
    """Encontrar el FlowBox de páginas en la jerarquía"""
    try:
        # Buscar recursivamente el FlowBox
        def find_flowbox(widget):
            if isinstance(widget, Gtk.FlowBox):
                return widget

            # Si tiene hijos, buscar en ellos
            if hasattr(widget, 'get_first_child'):
                child = widget.get_first_child()
                while child:
                    result = find_flowbox(child)
                    if result:
                        return result
                    child = child.get_next_sibling()

            return None

        return find_flowbox(pages_box)

    except Exception as e:
        print(f"Error buscando FlowBox: {e}")
        return None


def set_page_placeholder_with_loading(page_image, page):
    """Configurar placeholder con indicador de carga"""
    try:
        # Color diferente según tipo de página
        if page.tipoPagina == 1:  # COVER
            color = 0x33D17AFF  # Verde para COVER
        else:
            color = 0xE5A50AFF  # Amarillo para INTERNAL

        pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 140, 160)
        pixbuf.fill(color)
        texture = Gdk.Texture.new_for_pixbuf(pixbuf)
        page_image.set_paintable(texture)
    except Exception as e:
        print(f"Error creando placeholder con carga: {e}")


def load_page_thumbnail_progressive(page_image, page, comic):
    """Cargar thumbnail de página progresivamente"""
    try:
        # Intentar cargar desde el thumbnail guardado
        thumbnail_path = page.obtener_ruta_local()

        if thumbnail_path and os.path.exists(thumbnail_path) and not thumbnail_path.endswith("Comic_sin_caratula.png"):
            # Thumbnail existe: cargarlo directamente
            GLib.idle_add(update_page_image, page_image, thumbnail_path)
            return False
        else:
            # Thumbnail no existe: intentar generar desde archivo original
            return generate_thumbnail_from_comic(page_image, page, comic)

    except Exception as e:
        print(f"Error cargando thumbnail progresivo: {e}")
        return False


def generate_thumbnail_from_comic(page_image, page, comic):
    """Generar thumbnail extrayendo desde el archivo del cómic"""
    try:
        # Función worker para generar thumbnail
        def thumbnail_worker():
            try:
                from helpers.comic_extractor import ComicExtractor
                import tempfile

                extractor = ComicExtractor()

                # Crear directorio temporal
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Extraer páginas del archivo
                    extracted_files = extractor.extract_comic_pages(comic.path, temp_dir)

                    if extracted_files and len(extracted_files) >= page.ordenPagina:
                        # Obtener el archivo de esta página específica
                        page_file = extracted_files[page.ordenPagina - 1]  # ordenPagina es 1-based

                        # Generar thumbnail
                        from helpers.thumbnail_path import get_thumbnails_base_path
                        thumbnail_dir = os.path.join(get_thumbnails_base_path(), "comic_pages", str(comic.id_comicbook))
                        thumbnail_filename = f"page_{page.ordenPagina:03d}.jpg"
                        thumbnail_path = os.path.join(thumbnail_dir, thumbnail_filename)

                        success = extractor.generate_page_thumbnail(page_file, thumbnail_path)

                        if success:
                            # Actualizar imagen en UI thread
                            GLib.idle_add(update_page_image, page_image, thumbnail_path)
                        else:
                            print(f"Error generando thumbnail para página {page.ordenPagina}")

            except Exception as e:
                print(f"Error en worker de thumbnail: {e}")

        # Iniciar generación en hilo separado
        import threading
        thumbnail_thread = threading.Thread(target=thumbnail_worker, daemon=True)
        thumbnail_thread.start()

        return False

    except Exception as e:
        print(f"Error iniciando generación de thumbnail: {e}")
        return False


def update_page_image(page_image, image_path):
    """Actualizar imagen de página en UI thread"""
    try:
        if os.path.exists(image_path):
            page_image.set_filename(image_path)
            print(f"✅ Thumbnail cargado: {os.path.basename(image_path)}")
        else:
            print(f"⚠️ Thumbnail no encontrado: {image_path}")
    except Exception as e:
        print(f"Error actualizando imagen de página: {e}")

    return False