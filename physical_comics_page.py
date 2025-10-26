#!/usr/bin/env python3
"""
physical_comics_page.py - Página de cómics físicos para Navigation View
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


def create_physical_comics_content(comic_info, session, thumbnail_generator):
    """Crear contenido de cómics físicos para NavigationPage"""

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
    create_header_section(main_box, comic_info)
    physical_flow_box = create_physical_comics_section(main_box)

    # Cargar físicos
    GLib.idle_add(load_physical_comics, comic_info, session, thumbnail_generator, physical_flow_box)

    scrolled.set_child(main_box)
    return scrolled


def create_header_section(parent, comic_info):
    """Crear sección de información del ComicbookInfo"""
    # Frame de información
    info_frame = Adw.PreferencesGroup()
    info_frame.set_title("Información del Issue")

    # Título
    if comic_info.titulo:
        title_row = Adw.ActionRow()
        title_row.set_title("Título")
        title_row.set_subtitle(comic_info.titulo)
        info_frame.add(title_row)

    # Número
    number_row = Adw.ActionRow()
    number_row.set_title("Número")
    number_row.set_subtitle(f"#{comic_info.numero}")
    info_frame.add(number_row)

    # Fecha de portada
    if comic_info.fecha_tapa > 0:
        date_row = Adw.ActionRow()
        date_row.set_title("Fecha de portada")
        date_row.set_subtitle(str(comic_info.fecha_tapa))
        info_frame.add(date_row)

    # Calificación
    if comic_info.calificacion > 0:
        rating_row = Adw.ActionRow()
        rating_row.set_title("Calificación")
        stars = "★" * int(comic_info.calificacion) + "☆" * (5 - int(comic_info.calificacion))
        rating_row.set_subtitle(f"{stars} ({comic_info.calificacion}/5)")
        info_frame.add(rating_row)

    # Resumen si existe
    if comic_info.resumen:
        summary_row = Adw.ExpanderRow()
        summary_row.set_title("Resumen")
        summary_row.set_subtitle("Click para expandir")

        # Contenido del resumen
        summary_label = Gtk.Label(label=comic_info.resumen)
        summary_label.set_wrap(True)
        summary_label.set_selectable(True)
        summary_label.set_margin_start(12)
        summary_label.set_margin_end(12)
        summary_label.set_margin_top(12)
        summary_label.set_margin_bottom(12)
        summary_row.add_row(summary_label)

        info_frame.add(summary_row)

    parent.append(info_frame)


def create_physical_comics_section(parent):
    """Crear sección de cómics físicos"""
    # Frame de físicos
    physical_frame = Adw.PreferencesGroup()
    physical_frame.set_title("Archivos Físicos")
    physical_frame.set_vexpand(True)

    # Contenedor para las cards
    physical_flow_box = Gtk.FlowBox()
    physical_flow_box.set_valign(Gtk.Align.START)
    physical_flow_box.set_max_children_per_line(4)
    physical_flow_box.set_selection_mode(Gtk.SelectionMode.NONE)
    physical_flow_box.set_homogeneous(True)
    physical_flow_box.set_column_spacing(15)
    physical_flow_box.set_row_spacing(15)
    physical_flow_box.set_margin_top(10)
    physical_flow_box.set_margin_start(10)
    physical_flow_box.set_margin_end(10)
    physical_flow_box.set_margin_bottom(10)

    # Scroll para los físicos
    physical_scroll = Gtk.ScrolledWindow()
    physical_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    physical_scroll.set_vexpand(True)
    physical_scroll.set_min_content_height(300)
    physical_scroll.set_child(physical_flow_box)

    physical_frame.add(physical_scroll)
    parent.append(physical_frame)

    return physical_flow_box


def load_physical_comics(comic_info, session, thumbnail_generator, physical_flow_box):
    """Cargar cómics físicos del ComicbookInfo"""
    try:
        if not Comicbook:
            print("No se pueden cargar físicos - falta Comicbook")
            return False

        # Obtener todos los físicos para este ComicbookInfo
        physical_comics = session.query(Comicbook).filter(
            Comicbook.id_comicbook_info == comic_info.id_comicbook_info
        ).all()

        print(f"Encontrados {len(physical_comics)} físicos para {comic_info.titulo} #{comic_info.numero}")

        if not physical_comics:
            # Mostrar mensaje de que no hay físicos
            no_physical_label = Gtk.Label(label="No hay archivos físicos para este issue")
            no_physical_label.add_css_class("dim-label")
            no_physical_label.set_margin_top(50)
            physical_flow_box.append(no_physical_label)
            return False

        # Agregar cada físico como card
        for physical_comic in physical_comics:
            try:
                # Crear card más grande para mejor visualización
                comic_card = ComicCard(physical_comic, thumbnail_generator)
                comic_card.set_size_request(250, 400)

                # Hacer clickeable para acciones futuras
                click_gesture = Gtk.GestureClick()
                click_gesture.connect("pressed", on_physical_comic_clicked, physical_comic)
                comic_card.add_controller(click_gesture)

                physical_flow_box.append(comic_card)

            except Exception as e:
                print(f"Error creando card para físico {physical_comic.id_comicbook}: {e}")

    except Exception as e:
        print(f"Error cargando físicos: {e}")

    return False


def on_physical_comic_clicked(gesture, n_press, x, y, physical_comic):
    """Manejar click en un cómic físico"""
    if n_press == 2:  # Doble click
        print(f"Doble click en físico: {physical_comic.nombre_archivo}")
        # Abrir con el lector interno de Babelcomics4
        try:
            from comic_reader import open_comic_with_reader

            # Verificar que el archivo existe
            if os.path.exists(physical_comic.path):
                comic_title = physical_comic.nombre_archivo or f"Comic #{physical_comic.id_comicbook}"
                reader = open_comic_with_reader(
                    comic_path=physical_comic.path,
                    comic_title=comic_title,
                    parent_window=None  # Permitir que el lector sea independiente
                )
                if reader:
                    print(f"✅ Lector abierto para: {comic_title}")
                else:
                    print(f"❌ Error abriendo lector para: {comic_title}")
            else:
                print(f"❌ Archivo no encontrado: {physical_comic.path}")

        except ImportError as e:
            print(f"❌ Error importando comic_reader: {e}")
            # Fallback al lector del sistema si no se puede usar el interno
            try:
                import subprocess
                subprocess.run(['xdg-open', physical_comic.path], check=True)
                print("📖 Fallback: usando lector del sistema")
            except Exception as fallback_e:
                print(f"❌ Error con fallback del sistema: {fallback_e}")
        except Exception as e:
            print(f"❌ Error abriendo con lector interno: {e}")

    elif n_press == 1:  # Click simple
        print(f"Click en: {physical_comic.nombre_archivo} (Calidad: {physical_comic.calidad})")