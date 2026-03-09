#!/usr/bin/env python3
"""
volume_detail_page.py - Página de detalle de volumen para Navigation View
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
    from comic_cards import ComicCard, BaseCard
    from sqlalchemy import Integer
except ImportError as e:
    print(f"Error importando entidades: {e}")


# Definición de IssueCard a nivel de módulo para evitar crear GTypes dinámicamente
class IssueCard(BaseCard):
    """Card para mostrar issues de un volumen con contador de físicos"""

    def __init__(self, comic_info, physical_count, thumbnail_generator, session, volume, main_window):
        self.physical_count = physical_count
        self.session = session
        self.volume = volume
        self.main_window = main_window
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
            print(f"DEBUG - Issue {self.item.numero}: cover_path = {cover_path}")
            print(f"DEBUG - Issue {self.item.numero}: exists = {os.path.exists(cover_path) if cover_path else False}")
            if cover_path and os.path.exists(cover_path) and not cover_path.endswith("Comic_sin_caratula.png"):
                self.thumbnail_generator.request_thumbnail(
                    cover_path,
                    f"issue_{self.item.id_comicbook_info}",
                    "comicinfo",
                    self.load_issue_thumbnail
                )
            else:
                self.set_issue_placeholder()
        except Exception as e:
            print(f"Error cargando thumbnail de issue: {e}")
            self.set_issue_placeholder()

    def load_issue_thumbnail(self, texture_or_path):
        """Cargar thumbnail del issue con efecto B&N si no tiene físicos"""
        try:
            from gi.repository import Gdk

            if self.physical_count == 0:
                # Sin físicos: convertir a escala de grises con Pillow
                print(f"🎨 Convirtiendo a escala de grises para issue sin físicos: {self.item.numero}")
                texture = self.convert_to_grayscale(texture_or_path)
            else:
                # Con físicos: cargar imagen normalmente
                print(f"🌈 Cargando imagen en color para issue con físicos: {self.item.numero}")
                if isinstance(texture_or_path, str):
                    texture = Gdk.Texture.new_from_filename(texture_or_path)
                else:
                    texture = texture_or_path

            # Cargar la imagen (ya procesada si es necesario)
            if texture:
                self.image.set_paintable(texture)
            else:
                self.set_issue_placeholder()

        except Exception as e:
            print(f"Error aplicando efecto B&N: {e}")
            import traceback
            traceback.print_exc()
            # Fallback: cargar imagen original si es posible
            try:
                if isinstance(texture_or_path, str):
                    texture = Gdk.Texture.new_from_filename(texture_or_path)
                    self.image.set_paintable(texture)
                else:
                    self.image.set_paintable(texture_or_path)
            except Exception as fallback_error:
                print(f"Error en fallback: {fallback_error}")
                self.set_issue_placeholder()

    def convert_to_grayscale(self, texture_or_path):
        """Convertir imagen a escala de grises usando Pillow directamente desde archivo"""
        try:
            from PIL import Image
            from gi.repository import Gdk, GLib
            import io

            # Si recibimos una texture, necesitamos la ruta original
            if hasattr(self, 'cover_path') and self.cover_path:
                image_path = self.cover_path
            elif isinstance(texture_or_path, str):
                image_path = texture_or_path
            else:
                # Fallback: usar la texture original
                print("No se pudo obtener ruta de imagen, usando texture original")
                return texture_or_path

            # Cargar imagen directamente con PIL desde archivo
            with Image.open(image_path) as pil_image:
                # Convertir a RGB si es necesario
                if pil_image.mode in ('RGBA', 'LA'):
                    # Crear fondo blanco para imágenes con transparencia
                    background = Image.new('RGB', pil_image.size, (255, 255, 255))
                    if pil_image.mode == 'RGBA':
                        background.paste(pil_image, mask=pil_image.split()[3])
                    else:
                        background.paste(pil_image, mask=pil_image.split()[1])
                    rgb_image = background
                elif pil_image.mode == 'P':
                    rgb_image = pil_image.convert('RGB')
                else:
                    rgb_image = pil_image.convert('RGB')

                # Convertir a escala de grises
                gray_image = rgb_image.convert('L')

                # Convertir de vuelta a RGB para compatibilidad
                final_image = gray_image.convert('RGB')

                # Guardar en memoria como PNG
                buffer = io.BytesIO()
                final_image.save(buffer, format='PNG')
                buffer.seek(0)

                # Crear nuevo texture desde los bytes
                gbytes = GLib.Bytes.new(buffer.getvalue())
                gray_texture = Gdk.Texture.new_from_bytes(gbytes)

                print(f"✓ Imagen convertida a escala de grises desde archivo: {image_path}")
                return gray_texture

        except Exception as e:
            print(f"Error convirtiendo a escala de grises desde archivo: {e}")
            import traceback
            traceback.print_exc()
            # En caso de error, devolver la textura original
            if isinstance(texture_or_path, str):
                try:
                    return Gdk.Texture.new_from_filename(texture_or_path)
                except:
                    return None
            return texture_or_path

    def set_issue_placeholder(self):
        """Placeholder específico para issues"""
        try:
            self.image.set_paintable(texture)
        except Exception as e:
            print(f"Error creando placeholder de issue: {e}")


class IssueFilterDialog(Adw.Window):
    """Diálogo para filtrar issues"""
    
    __gsignals__ = {
        'filters-applied': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
    }
    
    def __init__(self, parent_window, current_filters):
        super().__init__()
        self.set_transient_for(parent_window)
        self.set_modal(True)
        self.set_title("Filtrar Issues")
        self.set_default_size(350, 400)
        
        # Filtros actuales
        self.current_filters = current_filters.copy() if current_filters else {"status": "all", "min_quantity": 0}
        
        self.create_content()
        self.load_filters()
        
    def create_content(self):
        """Crear contenido del diálogo"""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Header
        header = Adw.HeaderBar()
        header.set_show_end_title_buttons(False) # Usaremos nuestros botones
        header.set_title_widget(Gtk.Label(label="Filtros"))
        
        cancel_btn = Gtk.Button(label="Cancelar")
        cancel_btn.connect("clicked", lambda x: self.close())
        header.pack_start(cancel_btn)
        
        apply_btn = Gtk.Button(label="Aplicar")
        apply_btn.add_css_class("suggested-action")
        apply_btn.connect("clicked", self.on_apply)
        header.pack_end(apply_btn)
        
        main_box.append(header)
        
        # Contenido
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        content_box.set_margin_top(20)
        content_box.set_margin_bottom(20)
        content_box.set_margin_start(20)
        content_box.set_margin_end(20)
        
        # Grupo 1: Estado (Mostrar)
        status_group = Adw.PreferencesGroup()
        status_group.set_title("Mostrar")
        
        # Usamos ActionRows con RadioButtons para el estado
        self.status_all = Adw.ActionRow()
        self.status_all.set_title("Todos")
        self.radio_all = Gtk.CheckButton()
        self.radio_all.set_active(True)
        self.status_all.add_prefix(self.radio_all)
        self.status_all.set_activatable_widget(self.radio_all)
        status_group.add(self.status_all)
        
        self.status_with = Adw.ActionRow()
        self.status_with.set_title("Con físicos")
        self.status_with.set_subtitle("Muestra issues que tienes en tu colección")
        self.radio_with = Gtk.CheckButton()
        self.radio_with.set_group(self.radio_all)
        self.status_with.add_prefix(self.radio_with)
        self.status_with.set_activatable_widget(self.radio_with)
        status_group.add(self.status_with)
        
        self.status_without = Adw.ActionRow()
        self.status_without.set_title("Sin físicos")
        self.status_without.set_subtitle("Muestra issues que faltan en tu colección")
        self.radio_without = Gtk.CheckButton()
        self.radio_without.set_group(self.radio_all)
        self.status_without.add_prefix(self.radio_without)
        self.status_without.set_activatable_widget(self.radio_without)
        status_group.add(self.status_without)
        
        content_box.append(status_group)
        
        # Grupo 2: Cantidad
        qty_group = Adw.PreferencesGroup()
        qty_group.set_title("Inventario")
        
        # Crear adjustment explícito para evitar problemas
        adjustment = Gtk.Adjustment(value=0, lower=0, upper=100, step_increment=1, page_increment=10, page_size=0)
        
        self.min_qty_row = Adw.SpinRow()
        self.min_qty_row.set_adjustment(adjustment)
        self.min_qty_row.set_title("Cantidad mínima")
        self.min_qty_row.set_subtitle("Filtrar por cantidad de copias físicas")
        # set_range ya no es necesario si usamos adjustment configurado, pero no hace daño
        self.min_qty_row.set_climb_rate(1)
        qty_group.add(self.min_qty_row)
        
        content_box.append(qty_group)
        
        main_box.append(content_box)
        self.set_content(main_box)
        
    def load_filters(self):
        """Cargar estado actual"""
        status = self.current_filters.get("status", "all")
        if status == "all":
            self.radio_all.set_active(True)
        elif status == "with":
            self.radio_with.set_active(True)
        elif status == "without":
            self.radio_without.set_active(True)
            
        min_qty = self.current_filters.get("min_quantity", 0)
        self.min_qty_row.set_value(float(min_qty))
        
    def on_apply(self, btn):
        """Emitir señal con nuevos filtros"""
        new_filters = {}
        
        # Estado
        if self.radio_with.get_active():
            new_filters["status"] = "with"
        elif self.radio_without.get_active():
            new_filters["status"] = "without"
        else:
            new_filters["status"] = "all"
            
        # Cantidad
        new_filters["min_quantity"] = int(self.min_qty_row.get_value())
        
        self.emit("filters-applied", new_filters)
        self.close()


def create_volume_detail_content(volume, session, thumbnail_generator, main_window):
    """Crear contenido de detalle del volumen para NavigationPage"""

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
    create_info_tab(tab_view, volume, session, thumbnail_generator)
    create_issues_tab(tab_view, volume, session, thumbnail_generator, main_window)

    scrolled.set_child(tab_container)
    return scrolled, tab_view


def create_volume_detail_page_with_header(volume, session, thumbnail_generator, main_window):
    """Crear NavigationPage completa con ToolbarView y HeaderBar"""

    # Crear la página de navegación
    page = Adw.NavigationPage()
    year_text = f" ({volume.anio_inicio})" if volume.anio_inicio and volume.anio_inicio > 0 else ""
    page.set_title(f"{volume.nombre}{year_text}")

    # Crear ToolbarView para manejo correcto de cabeceras
    toolbar_view = Adw.ToolbarView()

    # Crear HeaderBar estándar
    header_bar = Adw.HeaderBar()
    
    # Botón de actualización
    update_button = Gtk.Button()
    update_button.set_icon_name("view-refresh-symbolic")
    update_button.set_tooltip_text("Actualizar desde ComicVine")
    update_button.add_css_class("suggested-action")
    
    header_bar.pack_end(update_button)
    
    # Agregar HeaderBar al ToolbarView
    toolbar_view.add_top_bar(header_bar)

    # Crear contenido principal
    content, tab_view = create_volume_detail_content(volume, session, thumbnail_generator, main_window)
    
    # Conectar el botón de actualización
    update_button.connect("clicked", lambda btn: update_volume_from_comicvine(volume, session, main_window, tab_view))

    # Establecer contenido en el ToolbarView
    toolbar_view.set_content(content)
    
    # Establecer ToolbarView como hijo de la página
    page.set_child(toolbar_view)

    return page


# Función create_content_with_update_button eliminada ya que se integró en la función principal



def clean_html_text(text):
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


def create_info_tab(tab_view, volume, session, thumbnail_generator):
    """Crear pestaña de información del volumen"""
    # Similar a volume_detail_window.py pero adaptado para NavigationPage
    info_scroll = Gtk.ScrolledWindow()
    info_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

    info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
    info_box.set_margin_start(20)
    info_box.set_margin_end(20)
    info_box.set_margin_top(20)
    info_box.set_margin_bottom(20)

    # Header section con imagen y datos básicos
    create_header_section(info_box, volume, session, thumbnail_generator)

    # Información detallada
    create_info_section(info_box, volume)

    # Editorial
    create_publisher_section(info_box, volume, session)

    info_scroll.set_child(info_box)

    # Crear pestaña
    info_page = tab_view.append(info_scroll)
    info_page.set_title("Información")
    info_page.set_icon(Gio.ThemedIcon.new("info-outline-symbolic"))


def update_card_cover(card, file_path, thumbnail_generator):
    """
    Actualizar el cover de un card cuando se descarga una nueva imagen

    Args:
        card: IssueCard a actualizar
        file_path: Ruta del archivo descargado
        thumbnail_generator: Generador de thumbnails
    """
    try:
        import os
        import time

        # Prevenir bucles infinitos - verificar si ya estamos actualizando este card recientemente
        current_time = time.time()
        if hasattr(card, '_last_update_time'):
            time_since_last_update = current_time - card._last_update_time
            if time_since_last_update < 5.0:  # No actualizar si fue hace menos de 5 segundos
                print(f"⏭️ DEBUG: Card actualizado recientemente (hace {time_since_last_update:.1f}s), saltando...")
                return False

        # Marcar timestamp de actualización
        card._last_update_time = current_time

        print(f"🖼️ DEBUG: Actualizando cover del card con archivo: {file_path}")

        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            print(f"⚠️ DEBUG: Archivo no existe: {file_path}")
            return False

        # Borrar cache del thumbnail si existe
        try:
            from helpers.thumbnail_path import get_thumbnails_base_path
            cache_path = os.path.join(get_thumbnails_base_path(), "comicinfo", f"issue_{card.item.id_comicbook_info}.jpg")
            if os.path.exists(cache_path):
                os.remove(cache_path)
                print(f"🗑️ DEBUG: Cache borrado: {cache_path}")
        except Exception as e:
            print(f"⚠️ Error borrando cache: {e}")

        # Solicitar nuevo thumbnail
        thumbnail_generator.request_thumbnail(
            file_path,
            f"issue_{card.item.id_comicbook_info}",
            "comicinfo",
            card.load_issue_thumbnail
        )

        print(f"✅ DEBUG: Thumbnail solicitado para {file_path}")
        return True

    except Exception as e:
        print(f"❌ Error actualizando cover del card: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_issues_tab(tab_view, volume, session, thumbnail_generator, main_window):
    """Crear pestaña de issues del volumen"""
    comics_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    comics_box.set_margin_start(20)
    comics_box.set_margin_end(20)
    comics_box.set_margin_top(20)
    comics_box.set_margin_bottom(20)
    comics_box.set_vexpand(True)

    # Header: título + barra de búsqueda y filtros
    header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
    header_box.set_margin_bottom(10)

    # Título de la sección
    comics_title = Gtk.Label(label=f"Issues de {volume.nombre}")
    comics_title.add_css_class("title-2")
    comics_title.set_halign(Gtk.Align.START)
    header_box.append(comics_title)

    # Controles de Ordenamiento y Búsqueda
    search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    search_box.set_hexpand(True)
    search_box.set_halign(Gtk.Align.END)
    
    # Dropdown de campos (Número, Título)
    sort_model = Gtk.StringList.new(["Número", "Título"])
    sort_dropdown = Gtk.DropDown.new(sort_model, None)
    sort_dropdown.set_selected(0)  # Por defecto: Número
    sort_dropdown.set_tooltip_text("Campo por el cual buscar y ordenar")
    search_box.append(sort_dropdown)

    # Campo de búsqueda
    search_entry = Gtk.SearchEntry()
    search_entry.set_placeholder_text("Buscar...")
    search_entry.set_width_chars(25)
    search_entry.set_hexpand(True)
    search_box.append(search_entry)

    # Filtro con Botón y Dialogo
    filter_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    
    # Estado actual de los filtros
    filter_state = {
        "status": "all",  # all, with, without
        "min_quantity": 0,
        "search_text": "",
        "sort_field": "Número"
    }
    
    # Label de estado del filtro
    filter_info_label = Gtk.Label(label="Todos")
    filter_info_label.add_css_class("dim-label")
    filter_box.append(filter_info_label)
    
    # Botón de filtro
    filter_button = Gtk.Button.new_from_icon_name("view-filter-symbolic")
    filter_button.set_tooltip_text("Filtrar issues")
    filter_box.append(filter_button)
    
    search_box.append(filter_box)
    header_box.append(search_box)

    comics_box.append(header_box)

    # FlowBox para los issues
    comics_flow_box = Gtk.FlowBox()
    comics_flow_box.set_valign(Gtk.Align.START)
    comics_flow_box.set_max_children_per_line(5)
    comics_flow_box.set_selection_mode(Gtk.SelectionMode.NONE)
    comics_flow_box.set_homogeneous(True)
    comics_flow_box.set_column_spacing(15)
    comics_flow_box.set_row_spacing(15)
    comics_flow_box.set_vexpand(True)

    # Scroll para los issues
    comics_scroll = Gtk.ScrolledWindow()
    comics_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    comics_scroll.set_vexpand(True)
    comics_scroll.set_child(comics_flow_box)

    comics_box.append(comics_scroll)

    # Obtener configuración de batch_size para scroll infinito
    from repositories.setup_repository import SetupRepository
    setup_repo = SetupRepository(session)
    config = setup_repo.obtener_o_crear_configuracion()
    batch_size = config.items_per_batch if config else 20

    # Inicializar variables de paginado
    comics_flow_box.loaded_count = 0
    comics_flow_box.batch_size = batch_size
    comics_flow_box.is_loading = False

    # Conectar evento de scroll para cargar más
    vadj = comics_scroll.get_vadjustment()
    vadj.connect("value-changed", on_issues_scroll, comics_flow_box, volume, session, thumbnail_generator, main_window)

    def update_filter_label():
        """Actualizar etiqueta de estado del filtro"""
        text_parts = []
        
        # Estado
        status = filter_state["status"]
        if status == "all":
            text_parts.append("Todos")
        elif status == "with":
            text_parts.append("Con físicos")
        elif status == "without":
            text_parts.append("Sin físicos")
            
        # Cantidad
        min_qty = filter_state["min_quantity"]
        if min_qty > 0:
            text_parts.append(f"(Min: {min_qty})")
            
        filter_info_label.set_text(" ".join(text_parts))
        
        # Cambiar estilo del botón si hay filtros activos
        if status != "all" or min_qty > 0:
            filter_button.add_css_class("suggested-action")
        else:
            filter_button.remove_css_class("suggested-action")

    def apply_current_filters():
        """Aplicar filtros actuales a los issues (recargando desde BD)"""
        print(f"🔄 DEBUG: Recargando lista con filtros: {filter_state}")
        
        # 1. Actualizar UI
        update_filter_label()
        
        # 2. Guardar filtros en el flowbox para que load_comics_batch los vea
        comics_flow_box.current_filters = filter_state.copy()
        
        # 3. Limpiar FlowBox
        child = comics_flow_box.get_first_child()
        while child:
            comics_flow_box.remove(child)
            child = comics_flow_box.get_first_child()
            
        # 4. Resetear contadores de paginación
        comics_flow_box.loaded_count = 0
        comics_flow_box.issue_cards_map = {}
        comics_flow_box.processed_covers = set()
        comics_flow_box.is_loading = False
        
        # Forzar recalculación de total_issues
        if hasattr(comics_flow_box, 'total_issues'):
            del comics_flow_box.total_issues
        
        # 5. Cargar primer lote
        GLib.idle_add(load_comics_batch, volume, session, thumbnail_generator, main_window, comics_flow_box)

    search_timeout_id = 0

    def process_search():
        """Procesa la búsqueda y aplica los filtros"""
        nonlocal search_timeout_id
        search_timeout_id = 0
        search_text = search_entry.get_text().strip()
        sort_field = sort_dropdown.get_selected_item().get_string()
        
        filter_state["search_text"] = search_text
        filter_state["sort_field"] = sort_field
        apply_current_filters()
        return False

    def on_search_changed(entry):
        """Maneja los cambios en la entrada de búsqueda con debounce"""
        nonlocal search_timeout_id
        if search_timeout_id != 0:
            GLib.source_remove(search_timeout_id)
        # Esperar 500ms antes de ejecutar la búsqueda
        search_timeout_id = GLib.timeout_add(500, process_search)

    def on_sort_changed(dropdown, param):
        """Maneja el cambio de campo de ordenamiento/búsqueda"""
        # Limpia el campo de búsqueda cuando cambia el criterio de ordenamiento/búsqueda
        search_entry.set_text("")
        sort_field = dropdown.get_selected_item().get_string()
        filter_state["sort_field"] = sort_field
        filter_state["search_text"] = ""
        apply_current_filters()

    search_entry.connect("search-changed", on_search_changed)
    sort_dropdown.connect("notify::selected", on_sort_changed)

    def on_filter_clicked(btn):
        """Abrir diálogo de filtros"""
        print("🔘 Botón de filtro clickeado")
        dialog = IssueFilterDialog(main_window, filter_state)
        dialog.connect("filters-applied", lambda d, new_filters: on_filters_applied(new_filters))
        dialog.present()
        
    def on_filters_applied(new_filters):
        """Callback cuando se aplican nuevos filtros desde el diálogo"""
        print(f"📥 Filtros recibidos del diálogo: {new_filters}")
        filter_state.update(new_filters)
        apply_current_filters()

    filter_button.connect("clicked", on_filter_clicked)

    # Crear pestaña
    comics_page = tab_view.append(comics_box)

    comics_page.set_title("Issues")
    comics_page.set_icon(Gio.ThemedIcon.new("view-list-symbolic"))

    # Diccionario para mapear issue numbers a sus cards (para actualización rápida)
    issue_cards_map = {}
    comics_flow_box.issue_cards_map = issue_cards_map

    # Set para rastrear qué covers ya fueron procesados (prevenir duplicados)
    processed_covers = set()
    comics_flow_box.processed_covers = processed_covers

    # Conectar al notificador de descargas para actualizar covers en tiempo real
    from helpers.cover_download_notifier import get_notifier
    notifier = get_notifier()

    def on_cover_downloaded(notifier, id_volume, numero_issue, file_path):
        """Handler cuando se descarga un cover"""
        # Solo procesar si es del volumen actual
        if id_volume != volume.id_volume:
            return

        # Crear clave única para este cover
        cover_key = f"{id_volume}_{numero_issue}_{file_path}"

        # Verificar si ya procesamos este cover
        if cover_key in processed_covers:
            print(f"⏭️ DEBUG: Cover ya procesado anteriormente, saltando - Issue: #{numero_issue}")
            return

        # Marcar como procesado
        processed_covers.add(cover_key)

        print(f"🔔 DEBUG: Señal recibida - Volumen: {id_volume}, Issue: #{numero_issue}")

        # Buscar el card correspondiente
        if numero_issue in issue_cards_map:
            card = issue_cards_map[numero_issue]
            print(f"🔄 DEBUG: Actualizando card del issue #{numero_issue}")
            # Actualizar la imagen del card (idle_add retorna False para que solo se ejecute una vez)
            def do_update():
                update_card_cover(card, file_path, thumbnail_generator)
                return False  # Importante: False para que no se repita
            GLib.idle_add(do_update)
        else:
            print(f"⚠️ DEBUG: No se encontró card para issue #{numero_issue} en el mapa")

    # Conectar señal
    signal_id = notifier.connect('cover-downloaded', on_cover_downloaded)

    # Guardar signal_id para poder desconectar después si es necesario
    comics_flow_box.cover_download_signal_id = signal_id
    comics_flow_box.cover_notifier = notifier

    # Desconectar señal cuando se destruya el widget
    def on_flowbox_destroy(widget):
        """Desconectar señal al destruir el widget"""
        try:
            if hasattr(widget, 'cover_notifier') and hasattr(widget, 'cover_download_signal_id'):
                widget.cover_notifier.disconnect(widget.cover_download_signal_id)
                print("🔌 DEBUG: Señal de cover downloads desconectada")
        except Exception as e:
            print(f"Error desconectando señal: {e}")

    comics_flow_box.connect('destroy', on_flowbox_destroy)

    # Cargar primer lote de issues
    GLib.idle_add(load_comics_batch, volume, session, thumbnail_generator, main_window, comics_flow_box)


def create_header_section(parent, volume, session, thumbnail_generator):
    """Crear sección de cabecera con imagen y datos básicos"""
    header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
    header_box.set_margin_bottom(20)
    header_box.set_halign(Gtk.Align.FILL)
    header_box.set_hexpand(True)

    # Contenedor de imagen
    image_container = Gtk.Box()
    image_container.set_size_request(250, 350)

    # Imagen del volumen
    volume_image = Gtk.Picture()
    volume_image.set_can_shrink(True)
    volume_image.set_keep_aspect_ratio(True)
    volume_image.set_content_fit(Gtk.ContentFit.CONTAIN)
    volume_image.add_css_class("volume-detail-image")

    # Cargar imagen del volumen
    load_volume_image(volume_image, volume)

    image_container.append(volume_image)

    # Información básica
    info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
    info_box.set_hexpand(True)
    info_box.set_vexpand(True)
    info_box.set_valign(Gtk.Align.START)

    # Título
    title_label = Gtk.Label(label=volume.nombre)
    title_label.set_halign(Gtk.Align.START)
    title_label.add_css_class("title-1")
    title_label.set_wrap(True)
    title_label.set_selectable(True)

    # Información básica en grid
    info_grid = create_info_grid(volume, session)

    # Deck (descripción corta)
    if volume.deck:
        clean_deck = clean_html_text(volume.deck)
        deck_frame = create_info_frame("Resumen", clean_deck)
        info_box.append(deck_frame)

    info_box.append(title_label)
    info_box.append(info_grid)

    header_box.append(image_container)
    header_box.append(info_box)

    parent.append(header_box)


# Continúo implementando las funciones auxiliares...
def create_info_grid(volume, session):
    """Crear grid con información básica del volumen"""
    grid = Gtk.Grid()
    grid.set_row_spacing(8)
    grid.set_column_spacing(20)

    row = 0

    # ID
    add_info_row(grid, row, "ID", f"#{volume.id_volume}")
    row += 1

    # Año de inicio
    if volume.anio_inicio > 0:
        add_info_row(grid, row, "Año de inicio", str(volume.anio_inicio))
        row += 1

    # Total de números
    add_info_row(grid, row, "Total de números", str(volume.cantidad_numeros))
    row += 1

    # Completitud
    completion_text = calculate_completion(volume, session)
    add_info_row(grid, row, "Completitud", completion_text)
    row += 1

    # URL si existe
    if volume.url:
        url_label = Gtk.Label()
        url_label.set_markup(f"<a href='{volume.url}'>{volume.url}</a>")
        url_label.set_halign(Gtk.Align.START)
        url_label.set_ellipsize(Pango.EllipsizeMode.END)
        url_label.set_max_width_chars(50)
        url_label.add_css_class("link")
        url_label.set_selectable(True)
        # Importante: para que los links funcionen
        url_label.set_property("use-markup", True)
        
        add_info_row(grid, row, "URL", "")
        grid.attach(url_label, 1, row, 1, 1)
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


def calculate_completion(volume, session):
    """Calcular completitud del volumen"""
    try:
        owned_count = 0
        if Comicbook and ComicbookInfo:
            # Contar números únicos de issues que tenemos físicamente
            from sqlalchemy import func, distinct

            owned_count = session.query(func.count(distinct(ComicbookInfo.numero))).join(
                Comicbook, ComicbookInfo.id_comicbook_info == Comicbook.id_comicbook_info
            ).filter(
                ComicbookInfo.id_volume == volume.id_volume
            ).scalar() or 0

        if volume.cantidad_numeros > 0:
            percentage = (owned_count / volume.cantidad_numeros) * 100
            return f"{owned_count}/{volume.cantidad_numeros} ({percentage:.1f}%)"
        else:
            return f"{owned_count}/? cómics"

    except Exception as e:
        print(f"Error calculando completitud: {e}")
        return "Error calculando"


def create_info_section(parent, volume):
    """Crear sección de descripción detallada"""
    if volume.descripcion:
        clean_desc = clean_html_text(volume.descripcion)
        desc_frame = create_info_frame("Descripción", clean_desc)
        parent.append(desc_frame)


def create_publisher_section(parent, volume, session):
    """Crear sección de editorial"""
    try:
        if volume.id_publisher > 0:
            publisher = session.query(Publisher).filter(
                Publisher.id_publisher == volume.id_publisher
            ).first()

            if publisher:
                publisher_frame = Adw.PreferencesGroup()
                publisher_frame.set_title("Editorial")
                publisher_frame.set_margin_top(20)

                publisher_row = Adw.ActionRow()
                publisher_row.set_title(publisher.nombre)
                if hasattr(publisher, 'deck') and publisher.deck:
                    publisher_row.set_subtitle(publisher.deck)

                publisher_icon = Gtk.Image.new_from_icon_name("folder-symbolic")
                publisher_row.add_prefix(publisher_icon)

                publisher_frame.add(publisher_row)
                parent.append(publisher_frame)

    except Exception as e:
        print(f"Error cargando editorial: {e}")


def create_info_frame(title, content):
    """Crear un frame de información con título y contenido"""
    frame = Adw.PreferencesGroup()
    frame.set_title(title)
    frame.set_margin_top(20)

    # Para contenido largo, usar scroll con altura limitada
    if len(content) > 200:
        desc_scroll = Gtk.ScrolledWindow()
        desc_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        desc_scroll.set_max_content_height(150)
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
        content_row = Adw.ActionRow()
        content_row.set_title(content)
        frame.add(content_row)

    return frame


def load_volume_image(volume_image, volume):
    """Cargar imagen del volumen"""
    try:
        cover_path = volume.obtener_cover()
        if cover_path and os.path.exists(cover_path):
            if not cover_path.endswith("Volumen_sin_caratula.png"):
                volume_image.set_filename(cover_path)
            else:
                set_placeholder_image(volume_image)
        else:
            set_placeholder_image(volume_image)
    except Exception as e:
        print(f"Error cargando imagen del volumen: {e}")
        set_placeholder_image(volume_image)


def set_placeholder_image(volume_image):
    """Configurar imagen placeholder"""
    try:
        pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 250, 350)
        pixbuf.fill(0x33D17AFF)  # Verde para volúmenes
        texture = Gdk.Texture.new_for_pixbuf(pixbuf)
        volume_image.set_paintable(texture)
    except Exception as e:
        print(f"Error creando placeholder: {e}")


def on_issues_scroll(adjustment, flow_box, volume, session, thumbnail_generator, main_window):
    """Manejar scroll para cargar más issues"""
    if flow_box.is_loading:
        return

    # Verificar si estamos cerca del final
    value = adjustment.get_value()
    upper = adjustment.get_upper()
    page_size = adjustment.get_page_size()

    # Cargar más cuando estamos al 80% del scroll
    if value + page_size >= upper * 0.8:
        # Verificar si hay más issues por cargar
        total = getattr(flow_box, 'total_issues', 0)
        if total == 0 or flow_box.loaded_count < total:
            flow_box.is_loading = True
            GLib.idle_add(load_comics_batch, volume, session, thumbnail_generator, main_window, flow_box)

def load_comics_batch(volume, session, thumbnail_generator, main_window, comics_flow_box):
    """Cargar un lote de issues"""
    try:
        if not ComicbookInfo:
            print("No se pueden cargar issues - faltan dependencias")
            return False

        # Si es la primera carga, obtener el total de issues (sin cargar los datos)
        if not hasattr(comics_flow_box, 'current_filters'):
             comics_flow_box.current_filters = {
                 "status": "all", 
                 "min_quantity": 0,
                 "search_text": "",
                 "sort_field": "Número"
             }

        filters = comics_flow_box.current_filters
        print(f"📥 DEBUG: Cargando batch con filtros: {filters}")

        # Construir consulta base con filtros
        from sqlalchemy import func, or_, and_
        from sqlalchemy.orm import aliased
        
        # Subquery para contar físicos
        # Contamos cuántos comics físicos hay para cada comicbook_info
        if Comicbook:
            stmt = session.query(
                Comicbook.id_comicbook_info,
                func.count('*').label('count')
            ).group_by(Comicbook.id_comicbook_info).subquery()
            
            physical_counts = aliased(stmt)
        
        # Query base
        query = session.query(ComicbookInfo)
        
        # Join con conteos si es necesario filtrar por cantidad/estado
        # O si simplemente queremos ordenar/mostrar info (aunque el count lo hacemos en el loop por ahora)
        # Para filtrar, necesitamos el join
        if filters["status"] != "all" or filters["min_quantity"] > 0:
             if Comicbook:
                query = query.outerjoin(physical_counts, ComicbookInfo.id_comicbook_info == physical_counts.c.id_comicbook_info)
                
                # Aplicar filtros
                if filters["status"] == "with":
                    query = query.filter(physical_counts.c.count > 0)
                elif filters["status"] == "without":
                    query = query.filter(or_(physical_counts.c.count == 0, physical_counts.c.count.is_(None)))
                    
                if filters.get("min_quantity", 0) > 0:
                    # Nota: si min_quantity > 0, implícitamente es "with" physicals
                    query = query.filter(physical_counts.c.count >= filters["min_quantity"])

        # Aplicar filtro de búsqueda de texto si no está vacío
        search_text = filters.get("search_text", "")
        sort_field = filters.get("sort_field", "Número")
        if search_text:
            if sort_field == "Título":
                # Usar case insensitive LIKE o match
                query = query.filter(ComicbookInfo.titulo.ilike(f"%{search_text}%"))
            else: # Número
                query = query.filter(ComicbookInfo.numero.ilike(f"%{search_text}%"))

        # Filtro de volumen siempre aplica
        query = query.filter(ComicbookInfo.id_volume == volume.id_volume)

        # Si es la primera carga (o recarga por filtro), obtener el total de issues filtrados
        if not hasattr(comics_flow_box, 'total_issues') or comics_flow_box.loaded_count == 0:
            comics_flow_box.total_issues = query.count()
            print(f"Total de issues (filtrados): {comics_flow_box.total_issues}")

        # Verificar si ya cargamos todo
        if comics_flow_box.loaded_count > 0 and comics_flow_box.loaded_count >= comics_flow_box.total_issues:
            print("Todos los issues ya están cargados")
            comics_flow_box.is_loading = False
            return False

        # Obtener el mapa de cards si existe
        if not hasattr(comics_flow_box, 'issue_cards_map'):
            comics_flow_box.issue_cards_map = {}

        # Calcular offset y limit para la consulta SQL
        offset = comics_flow_box.loaded_count
        limit = comics_flow_box.batch_size

        print(f"Cargando lote: offset={offset}, limit={limit}")

        # Configurar orden
        sort_field = filters.get("sort_field", "Número")
        if sort_field == "Título":
            order_criteria = [ComicbookInfo.titulo]
        else: # Número
            order_criteria = [ComicbookInfo.numero.cast(Integer), ComicbookInfo.numero]

        # Cargar solo el lote actual desde la base de datos
        from sqlalchemy.orm import joinedload
        batch_issues = query.options(
            joinedload(ComicbookInfo.portadas)
        ).order_by(
            *order_criteria
        ).offset(offset).limit(limit).all()

        print(f"Lote obtenido: {len(batch_issues)} issues")

        # Cargar el lote actual
        for comic_info in batch_issues:
            try:
                # Contar cómics físicos asociados a este metadata
                physical_count = 0
                if Comicbook:
                    physical_count = session.query(Comicbook).filter(
                        Comicbook.id_comicbook_info == comic_info.id_comicbook_info
                    ).count()

                # Crear card para metadata con contador
                comic_card = create_issue_card(comic_info, physical_count, thumbnail_generator, session, volume, main_window)

                # Tamaños más grandes ahora que tienen toda la pestaña
                comic_card.set_size_request(220, 350)

                # Registrar el card en el mapa para actualizaciones futuras
                comics_flow_box.issue_cards_map[comic_info.numero] = comic_card

                # Hacer que sea clickeable para ver físicos de este issue
                click_gesture = Gtk.GestureClick()
                click_gesture.connect("pressed", on_issue_clicked, comic_info, physical_count, main_window)
                comic_card.add_controller(click_gesture)

                # Agregar menú contextual para clic derecho
                right_click_gesture = Gtk.GestureClick()
                right_click_gesture.set_button(3)  # Botón derecho
                right_click_gesture.connect("pressed", on_issue_right_click, comic_card, comic_info, volume, session, main_window)
                comic_card.add_controller(right_click_gesture)

                comics_flow_box.append(comic_card)

            except Exception as e:
                print(f"Error creando card para comic_info {comic_info.id_comicbook_info}: {e}")

        # Actualizar contador
        comics_flow_box.loaded_count += len(batch_issues)
        comics_flow_box.is_loading = False

        print(f"✓ Lote cargado: {comics_flow_box.loaded_count}/{comics_flow_box.total_issues} issues")

        return False

    except Exception as e:
        print(f"Error cargando lote de issues: {e}")
        import traceback
        traceback.print_exc()
        comics_flow_box.is_loading = False
        return False

def load_comics(volume, session, thumbnail_generator, main_window, comics_flow_box):
    """Cargar issues del volumen"""
    try:
        if not ComicbookInfo:
            print("No se pueden cargar issues - faltan dependencias")
            return False

        # Obtener todos los ComicbookInfo para este volumen con sus portadas
        from sqlalchemy.orm import joinedload
        comic_infos = session.query(ComicbookInfo).options(
            joinedload(ComicbookInfo.portadas)
        ).filter(
            ComicbookInfo.id_volume == volume.id_volume
        ).order_by(ComicbookInfo.numero.cast(Integer), ComicbookInfo.numero).all()

        print(f"Encontrados {len(comic_infos)} issues para el volumen {volume.nombre}")

        # Obtener el mapa de cards si existe
        issue_cards_map = getattr(comics_flow_box, 'issue_cards_map', {})

        # Agregar cada comic_info como card con contador de físicos
        for comic_info in comic_infos:
            try:
                # Contar cómics físicos asociados a este metadata
                physical_count = 0
                if Comicbook:
                    physical_count = session.query(Comicbook).filter(
                        Comicbook.id_comicbook_info == comic_info.id_comicbook_info
                    ).count()

                # Crear card para metadata con contador
                comic_card = create_issue_card(comic_info, physical_count, thumbnail_generator, session, volume, main_window)

                # Tamaños más grandes ahora que tienen toda la pestaña
                comic_card.set_size_request(220, 350)

                # Registrar el card en el mapa para actualizaciones futuras
                issue_cards_map[comic_info.numero] = comic_card
                print(f"📋 DEBUG: Card registrado para issue #{comic_info.numero}")

                # Hacer que sea clickeable para ver físicos de este issue
                click_gesture = Gtk.GestureClick()
                click_gesture.connect("pressed", on_issue_clicked, comic_info, physical_count, main_window)
                comic_card.add_controller(click_gesture)

                # Agregar menú contextual para clic derecho
                right_click_gesture = Gtk.GestureClick()
                right_click_gesture.set_button(3)  # Botón derecho
                right_click_gesture.connect("pressed", on_issue_right_click, comic_card, comic_info, volume, session, main_window)
                comic_card.add_controller(right_click_gesture)

                comics_flow_box.append(comic_card)

            except Exception as e:
                print(f"Error creando card para comic_info {comic_info.id_comicbook_info}: {e}")

    except Exception as e:
        print(f"Error cargando issues: {e}")
        error_label = Gtk.Label(label="No se pudieron cargar los issues de este volumen")
        error_label.add_css_class("dim-label")
        error_label.set_margin_top(20)
        comics_flow_box.append(error_label)

    return False


def create_issue_card(comic_info, physical_count, thumbnail_generator, session, volume, main_window):
    """
    Crear card para issue con contador de cómics físicos.
    Ahora simplemente retorna una instancia de IssueCard definida a nivel de módulo.
    """
    return IssueCard(comic_info, physical_count, thumbnail_generator, session, volume, main_window)


def on_issue_clicked(gesture, n_press, x, y, comic_info, physical_count, main_window):
    """Manejar click en un issue (ComicbookInfo)"""
    if n_press == 2:  # Doble click
        print(f"Doble click en issue: {comic_info.titulo} #{comic_info.numero} ({physical_count} físicos)")

        # Siempre mostrar detalle de ComicbookInfo (con covers de ComicVine)
        show_comicbook_info_detail(comic_info, physical_count, main_window)

        # Opcional: Si hay físicos, también permitir navegar a ellos
        # if physical_count > 0:
        #     main_window.navigate_to_physical_comics(comic_info)


def on_issue_right_click(gesture, n_press, x, y, card_widget, comic_info, volume, session, main_window):
    """Manejar clic derecho en un issue para mostrar menú contextual"""
    try:
        # Crear menú popover
        popover = Gtk.PopoverMenu()
        popover.set_parent(card_widget)

        # Crear modelo del menú
        menu_model = Gio.Menu()
        menu_model.append("🔄 Redescargar portada", "issue.redownload_cover")

        # Configurar menú
        popover.set_menu_model(menu_model)

        # Crear acción para redescargar
        action_group = Gio.SimpleActionGroup()
        redownload_action = Gio.SimpleAction.new("redownload_cover", None)
        redownload_action.connect("activate", lambda a, p: redownload_issue_cover(comic_info, volume, session, main_window))
        action_group.add_action(redownload_action)

        # Insertar el grupo de acciones
        card_widget.insert_action_group("issue", action_group)

        # Mostrar popover en la posición del clic
        rect = Gdk.Rectangle()
        rect.x = x
        rect.y = y
        rect.width = 1
        rect.height = 1
        popover.set_pointing_to(rect)
        popover.popup()

    except Exception as e:
        print(f"Error mostrando menú contextual: {e}")
        import traceback
        traceback.print_exc()


def redownload_issue_cover(comic_info, volume, session, main_window):
    """Redescargar la portada de un issue específico desde ComicVine"""
    try:
        import threading
        import os
        from helpers.comicvine_cliente import ComicVineClient

        print(f"\n{'='*80}")
        print(f"REDESCARGANDO PORTADA PARA ISSUE #{comic_info.numero}")
        print(f"Volume: {volume.nombre}")
        print(f"ComicVine ID: {comic_info.comicvine_id}")
        print(f"{'='*80}\n")

        # Mostrar toast de inicio
        toast = Adw.Toast.new("Redescargando portada...")
        toast.set_timeout(2)
        main_window.toast_overlay.add_toast(toast)

        def download_in_thread():
            """Descargar en hilo separado"""
            try:
                # Si no tenemos ComicVine ID, no podemos redescargar
                if not comic_info.comicvine_id or comic_info.comicvine_id == 0:
                    GLib.idle_add(show_error, "Este issue no tiene ComicVine ID")
                    return

                # Obtener datos del issue desde ComicVine API (para URL actualizada)
                # TODO: Obtener API key de configuración
                api_key = "7e4368b71c5a66d710a62e996a660024f6a868d4"
                client = ComicVineClient(api_key)

                print(f"Consultando ComicVine API para issue ID: {comic_info.comicvine_id}")
                # get_issues_by_ids espera una lista y devuelve una lista
                issues_list = client.get_issues_by_ids([comic_info.comicvine_id])

                if not issues_list or len(issues_list) == 0:
                    GLib.idle_add(show_error, "No se pudieron obtener datos del issue")
                    return

                # Tomar el primer (y único) issue de la lista
                issue_data = issues_list[0]

                # Verificar que tenga imagen
                if not issue_data.get('image') or not issue_data['image'].get('medium_url'):
                    GLib.idle_add(show_error, "El issue no tiene imagen disponible en ComicVine")
                    return

                image_url = issue_data['image']['medium_url']
                print(f"URL de imagen obtenida de ComicVine: {image_url}")

                # Descargar la portada con la URL actualizada desde ComicVine
                # force_redownload=True para reescribir el archivo aunque ya exista
                success = download_issue_cover(issue_data, volume, session, force_redownload=True)

                if success:
                    session.commit()

                    # Borrar cache del thumbnail para forzar regeneración
                    try:
                        from helpers.thumbnail_path import get_thumbnails_base_path
                        cache_path = os.path.join(get_thumbnails_base_path(), "comicinfo", f"issue_{comic_info.id_comicbook_info}.jpg")
                        if os.path.exists(cache_path):
                            os.remove(cache_path)
                            print(f"DEBUG: Cache borrado: {cache_path}")
                    except Exception as e:
                        print(f"Error borrando cache: {e}")

                    GLib.idle_add(show_success, "Portada redescargada exitosamente")
                    # Ya no es necesario recargar la vista - el cover se actualiza automáticamente vía señales
                else:
                    GLib.idle_add(show_error, "Error descargando la portada")

            except Exception as e:
                print(f"Error en hilo de descarga: {e}")
                import traceback
                traceback.print_exc()
                GLib.idle_add(show_error, f"Error: {str(e)}")

        def show_error(message):
            toast = Adw.Toast.new(message)
            toast.set_timeout(3)
            main_window.toast_overlay.add_toast(toast)

        def show_success(message):
            toast = Adw.Toast.new(message)
            toast.set_timeout(2)
            main_window.toast_overlay.add_toast(toast)

        def refresh_volume_view():
            """Refrescar la vista del volumen"""
            if hasattr(main_window, 'navigate_to_volume_detail'):
                main_window.navigate_to_volume_detail(volume)

        # Iniciar descarga en hilo separado
        thread = threading.Thread(target=download_in_thread, daemon=True)
        thread.start()

    except Exception as e:
        print(f"Error redescargando portada: {e}")
        import traceback
        traceback.print_exc()


def show_comicbook_info_detail(comic_info, physical_count, main_window):
    """Mostrar página de detalle de ComicbookInfo con carrusel de covers"""
    try:
        # Crear página de detalle
        detail_page = create_comicbook_info_detail_page(comic_info, physical_count, main_window.session, main_window)

        # Agregar a la pila de navegación
        if hasattr(main_window, 'navigation_view') and main_window.navigation_view:
            main_window.navigation_view.push(detail_page)
        else:
            print("Error: No se encontró navigation_view en main_window")

    except Exception as e:
        print(f"Error mostrando detalle de ComicbookInfo: {e}")
        import traceback
        traceback.print_exc()


def create_comicbook_info_detail_page(comic_info, physical_count, session, main_window):
    """Crear página de detalle para ComicbookInfo"""
    # Crear la página de navegación
    page = Adw.NavigationPage()
    page.set_title(f"{comic_info.titulo} #{comic_info.numero}")

    # Crear ToolbarView
    toolbar_view = Adw.ToolbarView()

    # Crear HeaderBar estándar (el botón 'Back' se maneja automáticamente)
    header_bar = Adw.HeaderBar()
    toolbar_view.add_top_bar(header_bar)

    # Contenedor principal para el contenido scrolling
    # (Ya no usamos el HeaderBar manual ni el botón Back manual)


    # Contenedor principal con scroll
    scrolled = Gtk.ScrolledWindow()
    scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scrolled.set_vexpand(True)

    main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
    main_box.set_margin_start(20)
    main_box.set_margin_end(20)
    main_box.set_margin_top(20)
    main_box.set_margin_bottom(20)

    # Header con covers carousel
    header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
    header_box.set_margin_bottom(20)

    # Carrusel de covers
    covers_carousel = create_comicbook_info_covers_carousel(comic_info)
    header_box.append(covers_carousel)

    # Información del comic
    info_box = create_comicbook_info_content(comic_info, physical_count, session, main_window)
    header_box.append(info_box)

    main_box.append(header_box)
    scrolled.set_child(main_box)
    
    # Establecer el contenido escroleable como contenido del ToolbarView
    toolbar_view.set_content(scrolled)

    # Agregar controlador de eventos de teclado para manejar ESC
    key_controller = Gtk.EventControllerKey()

    def on_key_pressed(controller, keyval, keycode, state):
        """Manejar eventos de teclado"""
        if keyval == Gdk.KEY_Escape:
            # ESC presionado: ir hacia atrás en la navegación
            # Solo si no es la primera página
            if hasattr(main_window, 'navigation_view') and main_window.navigation_view:
                if main_window.navigation_view.get_navigation_stack().get_n_items() > 1:
                    main_window.navigation_view.pop()
                    return True
        return False

    key_controller.connect('key-pressed', on_key_pressed)
    page.add_controller(key_controller)

    # Hacer la página capaz de recibir el foco para eventos de teclado
    page.set_can_focus(True)
    page.set_focusable(True)

    # Enfocar la página cuando se muestre
    def on_page_shown(widget):
        widget.grab_focus()

    page.connect('show', on_page_shown)

    # Usar el ToolbarView como hijo de la página
    page.set_child(toolbar_view)

    return page


def create_comicbook_info_covers_carousel(comic_info):
    """Crear carrusel de covers para ComicbookInfo"""
    try:
        # Contenedor del carrusel
        carousel_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        # Obtener covers
        covers = list(comic_info.portadas) if comic_info.portadas else []

        if len(covers) > 1:
            # Carrusel para múltiples covers
            carousel = Adw.Carousel()
            carousel.set_size_request(200, 280)
            carousel.set_allow_mouse_drag(True)
            carousel.set_allow_scroll_wheel(True)

            # Agregar cada cover
            for i, cover in enumerate(covers):
                cover_image = Gtk.Picture()
                cover_image.set_can_shrink(True)
                cover_image.set_keep_aspect_ratio(True)
                cover_image.set_content_fit(Gtk.ContentFit.CONTAIN)
                cover_image.set_size_request(200, 280)

                # Cargar imagen de la cover
                load_comicbook_cover_image(cover_image, cover)
                carousel.append(cover_image)

            # Indicador de páginas
            dots = Adw.CarouselIndicatorDots()
            dots.set_carousel(carousel)

            # Label con cantidad
            cover_count_label = Gtk.Label()
            cover_count_label.set_markup(f"<b>{len(covers)} covers</b>")
            cover_count_label.add_css_class("title-4")
            cover_count_label.set_halign(Gtk.Align.CENTER)

            carousel_container.append(carousel)
            carousel_container.append(dots)
            carousel_container.append(cover_count_label)

        elif len(covers) == 1:
            # Una sola cover
            single_image = Gtk.Picture()
            single_image.set_can_shrink(True)
            single_image.set_keep_aspect_ratio(True)
            single_image.set_content_fit(Gtk.ContentFit.CONTAIN)
            single_image.set_size_request(200, 280)

            load_comicbook_cover_image(single_image, covers[0])
            carousel_container.append(single_image)

        else:
            # Sin covers - placeholder
            placeholder = Gtk.Label()
            placeholder.set_markup("<i>Sin covers disponibles</i>")
            placeholder.add_css_class("dim-label")
            placeholder.set_size_request(200, 280)
            placeholder.set_valign(Gtk.Align.CENTER)
            carousel_container.append(placeholder)

        return carousel_container

    except Exception as e:
        print(f"Error creando carrusel de ComicbookInfo: {e}")
        return Gtk.Box()


def load_comicbook_cover_image(image_widget, cover):
    """Cargar imagen de cover de ComicbookInfo"""
    try:
        print(f"🖼️ DEBUG: Intentando cargar cover ID {cover.id_cover}")
        print(f"🖼️ DEBUG: URL imagen: {cover.url_imagen}")

        # Primero, intentar búsqueda manual antes de usar obtener_ruta_local()
        found_path = None

        if cover.url_imagen:
            # Intentar generar ruta desde URL
            filename = cover.url_imagen.split('/')[-1]
            base_name = filename.rsplit('.', 1)[0]  # Sin extensión
            extension = filename.rsplit('.', 1)[1] if '.' in filename else 'jpg'

            # Buscar archivo principal y variantes
            from helpers.thumbnail_path import get_thumbnails_base_path
            _ci_base = os.path.join(get_thumbnails_base_path(), "comicbook_info")
            possible_patterns = [
                f"{_ci_base}/*/{filename}",  # Nombre exacto
                f"{_ci_base}/*/{base_name}_variant_*.{extension}",  # Variantes
                f"{_ci_base}/*/{base_name}.{extension}",  # Sin variant
            ]

            print(f"🖼️ DEBUG: Buscando variantes de: {filename}")

            # Buscar archivo en directorios de covers
            import glob
            for pattern in possible_patterns:
                found_files = glob.glob(pattern)
                if found_files:
                    found_path = found_files[0]  # Tomar el primero encontrado
                    print(f"🖼️ DEBUG: ✅ Encontrado variante: {found_path}")
                    break

        # Si no encontramos variante, usar método del modelo
        if not found_path:
            cover_path = cover.obtener_ruta_local()
            print(f"🖼️ DEBUG: Ruta local del modelo: {cover_path}")

            # Solo usar si no es el placeholder
            if cover_path and not cover_path.endswith("Comic_sin_caratula.png"):
                found_path = cover_path

        # Cargar imagen si encontramos alguna
        if found_path and os.path.exists(found_path):
            print(f"🖼️ DEBUG: ✅ Cargando: {found_path}")
            image_widget.set_filename(found_path)
        else:
            # Placeholder si no se encuentra la imagen
            print(f"🖼️ DEBUG: ❌ No se encontró archivo, usando placeholder")
            placeholder_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 200, 280)
            placeholder_pixbuf.fill(0x3584E4FF)  # Azul
            image_widget.set_pixbuf(placeholder_pixbuf)

    except Exception as e:
        print(f"❌ Error cargando cover: {e}")
        import traceback
        traceback.print_exc()


def create_comicbook_info_content(comic_info, physical_count, session, main_window):
    """Crear contenido de información de ComicbookInfo"""
    info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
    info_box.set_hexpand(True)

    # Título
    title_label = Gtk.Label()
    title_label.set_markup(f"<span size='xx-large' weight='bold'>{comic_info.titulo or 'Sin título'}</span>")
    title_label.set_halign(Gtk.Align.START)
    title_label.set_wrap(True)
    info_box.append(title_label)

    # Número
    if comic_info.numero:
        number_label = Gtk.Label()
        number_label.set_markup(f"<span size='large'>Número: <b>#{comic_info.numero}</b></span>")
        number_label.set_halign(Gtk.Align.START)
        info_box.append(number_label)

    # Fecha
    if comic_info.fecha_tapa:
        date_label = Gtk.Label()
        date_label.set_markup(f"<span size='large'>Año: <b>{comic_info.fecha_tapa}</b></span>")
        date_label.set_halign(Gtk.Align.START)
        info_box.append(date_label)

    # Comics físicos
    physical_label = Gtk.Label()
    if physical_count > 0:
        physical_label.set_markup(f"<span size='large'>Comics físicos: <b>{physical_count}</b></span>")
        physical_label.add_css_class("success")
    else:
        physical_label.set_markup(f"<span size='large'>Comics físicos: <b>0</b></span>")
        physical_label.add_css_class("warning")
    physical_label.set_halign(Gtk.Align.START)
    info_box.append(physical_label)

    # ComicVine ID si existe
    if hasattr(comic_info, 'comicvine_id') and comic_info.comicvine_id:
        cv_label = Gtk.Label()
        cv_label.set_markup(f"<span size='small'>ComicVine ID: {comic_info.comicvine_id}</span>")
        cv_label.add_css_class("dim-label")
        cv_label.set_halign(Gtk.Align.START)
        info_box.append(cv_label)

    # URLs de ComicVine si existen
    if hasattr(comic_info, 'url_sitio_web') and comic_info.url_sitio_web:
        url_label = Gtk.Label()
        url_label.set_markup(f"<span size='small'><a href='{comic_info.url_sitio_web}'>Ver en ComicVine</a></span>")
        url_label.set_halign(Gtk.Align.START)
        info_box.append(url_label)

    # Resumen si existe
    if comic_info.resumen:
        summary_frame = Adw.PreferencesGroup()
        summary_frame.set_title("Resumen")

        summary_label = Gtk.Label()
        summary_label.set_text(comic_info.resumen[:500] + "..." if len(comic_info.resumen) > 500 else comic_info.resumen)
        summary_label.set_wrap(True)
        summary_label.set_halign(Gtk.Align.START)
        summary_label.set_valign(Gtk.Align.START)

        summary_frame.add(summary_label)
        info_box.append(summary_frame)

    # Botón para ver físicos si los hay
    if physical_count > 0:
        view_physicals_button = Gtk.Button.new_with_label(f"Ver {physical_count} comic(s) físico(s)")
        view_physicals_button.add_css_class("suggested-action")
        view_physicals_button.set_halign(Gtk.Align.START)

        # Conectar botón para navegar a físicos
        view_physicals_button.connect("clicked", lambda btn: main_window.navigate_to_physical_comics(comic_info))

        info_box.append(view_physicals_button)

    return info_box


def update_volume_from_comicvine(volume, session, main_window, tab_view):
    """Actualizar volumen desde ComicVine API"""
    try:
        from helpers.comicvine_cliente import ComicVineClient
        from helpers.image_downloader import download_image
    except ImportError as e:
        print(f"Error importando helpers: {e}")
        show_update_error(main_window, "No se pudieron cargar los helpers de ComicVine")
        return

    # Verificar que el volumen tenga ID de ComicVine
    if not volume.id_comicvine:
        show_update_error(main_window, "Este volumen no tiene ID de ComicVine asociado. Necesitas catalogarlo desde ComicVine primero.")
        return

    # Crear toast de progreso
    show_update_progress(main_window, "Conectando con ComicVine...")

    # Realizar actualización en segundo plano
    GLib.idle_add(perform_comicvine_update, volume, session, main_window, tab_view)


def perform_comicvine_update(volume, session, main_window, tab_view):
    """Realizar la actualización desde ComicVine en segundo plano"""
    try:
        from helpers.comicvine_cliente import ComicVineClient
        from helpers.image_downloader import download_image
        from repositories.volume_repository import VolumeRepository

        # Crear cliente con API key (debería venir de configuración)
        api_key = "7e4368b71c5a66d710a62e996a660024f6a868d4"  # TODO: Mover a configuración
        client = ComicVineClient(api_key)

        show_update_progress(main_window, "Obteniendo información del volumen...")

        # Obtener detalles del volumen desde ComicVine
        volume_details = client.get_volume_details(volume.id_comicvine)
        if not volume_details:
            show_update_error(main_window, "No se pudo obtener información del volumen")
            return False

        # NUEVA FUNCIONALIDAD: Actualizar información básica del volumen primero
        show_update_progress(main_window, "Actualizando información del volumen...")
        volume_repo = VolumeRepository(session)

        try:
            # Usar la nueva función para actualizar toda la información del volumen
            updated_volume = volume_repo.update_volume_from_comicvine(volume, volume_details)
            print(f"✅ Información del volumen actualizada: {updated_volume.nombre}")
        except Exception as e:
            print(f"❌ Error actualizando información del volumen: {e}")
            # Hacer rollback de la sesión para poder continuar
            try:
                session.rollback()
                print("🔄 Rollback de sesión realizado, continuando con issues...")
            except Exception as rollback_error:
                print(f"❌ Error en rollback: {rollback_error}")
            # Continuar con la actualización de issues aunque falle la actualización del volumen

        show_update_progress(main_window, "Obteniendo lista de issues...")

        # Obtener todos los issues del volumen
        issues_list = volume_details.get('issues', [])
        if not issues_list:
            show_update_success(main_window, f"Volumen actualizado exitosamente. No hay issues nuevos.")
            return True

        # Extraer IDs de issues
        issue_ids = [issue['id'] for issue in issues_list if 'id' in issue]

        show_update_progress(main_window, f"Procesando {len(issue_ids)} issues...")

        # Obtener detalles completos de todos los issues
        detailed_issues = client.get_issues_by_ids(issue_ids)

        if not detailed_issues:
            show_update_error(main_window, "No se pudieron obtener los detalles de los issues")
            return False

        # Procesar cada issue
        new_issues_count = 0
        updated_issues_count = 0

        for issue_data in detailed_issues:
            try:
                issue_number = issue_data.get('issue_number')
                if not issue_number:
                    continue

                # Buscar si ya existe este issue
                existing_issue = session.query(ComicbookInfo).filter(
                    ComicbookInfo.id_volume == volume.id_volume,
                    ComicbookInfo.numero == str(issue_number)
                ).first()

                if existing_issue:
                    # Actualizar issue existente
                    update_existing_issue(existing_issue, issue_data, session)
                    updated_issues_count += 1
                else:
                    # Crear nuevo issue
                    create_new_issue(volume, issue_data, session)
                    new_issues_count += 1

                # Las portadas se descargarán en el hilo separado

            except Exception as e:
                print(f"Error procesando issue {issue_data.get('issue_number', 'N/A')}: {e}")

        # Actualizar cover del volumen si está disponible
        volume_cover_updated = False
        if volume_details.get('image') and volume_details['image'].get('medium_url'):
            try:
                show_update_progress(main_window, "Descargando cover del volumen...")
                cover_url = volume_details['image']['medium_url']
                from helpers.thumbnail_path import get_thumbnails_base_path
                cover_path = download_image(cover_url, os.path.join(get_thumbnails_base_path(), "volumes"), f"{volume.id_volume}.jpg")
                if cover_path:
                    # Actualizar image_url para mantener consistencia con el modelo
                    volume.image_url = cover_url
                    volume_cover_updated = True
                    print(f"DEBUG: Cover del volumen descargado: {cover_path}")
                    print(f"DEBUG: image_url actualizada: {cover_url}")
            except Exception as e:
                print(f"Error descargando cover del volumen: {e}")

        # Confirmar cambios de metadata primero
        session.commit()

        # Mostrar resultado de metadata
        cover_msg = " + cover actualizado" if volume_cover_updated else ""
        message = f"Metadata actualizada: {new_issues_count} nuevos, {updated_issues_count} actualizados{cover_msg}"
        show_update_success(main_window, message)

        # Refrescar la pestaña de issues (si existe tab_view)
        if tab_view:
            GLib.idle_add(refresh_issues_tab, tab_view, volume, session, main_window.thumbnail_generator, main_window)

        # Descargar portadas en hilo separado para no bloquear UI
        print(f"DEBUG: Iniciando hilo de descarga para {len(detailed_issues)} issues")
        
        def progress_callback(msg):
            GLib.idle_add(show_update_progress, main_window, msg)
            
        def save_cover_result(result):
            """
            Callback ejecutado por el worker de descarga.
            Recibe un diccionario con resultados y los guarda en DB usando GLib.idle_add
            para asegurar ejecución en el hilo principal.
            """
            def _update_db_in_main_thread():
                try:
                    # Este código corre en el Main Thread
                    # Usamos la sesión de la ventana principal
                    from entidades.comicbook_info_model import ComicbookInfo
                    from entidades.comicbook_info_cover_model import ComicbookInfoCover
                    
                    issue_num = result.get('issue_number')
                    results_list = result.get('results', [])
                    
                    if not results_list:
                        return False
                        
                    # Buscar ComicbookInfo
                    comic_info = session.query(ComicbookInfo).filter(
                        ComicbookInfo.id_volume == volume.id_volume,
                        ComicbookInfo.numero == str(issue_num)
                    ).first()
                    
                    if not comic_info:
                        print(f"⚠️ No se encontró ComicbookInfo para issue #{issue_num}")
                        return False
                        
                    changes_made = False
                    for item in results_list:
                        url = item.get('url')
                        embedding_json = item.get('embedding')
                        # item.get('path') -> ruta local, no la guardamos en DB, solo verificamos
                        
                        # Buscar si ya existe la portada
                        cover_record = next((c for c in comic_info.portadas if c.url_imagen == url), None)
                        
                        if not cover_record:
                            # Crear nueva
                            cover_record = ComicbookInfoCover(
                                id_comicbook_info=comic_info.id_comicbook_info,
                                url_imagen=url
                            )
                            session.add(cover_record)
                            comic_info.portadas.append(cover_record)
                            changes_made = True
                        
                        # Actualizar embedding si existe y es nuevo
                        if embedding_json:
                            if cover_record.embedding != embedding_json:
                                cover_record.embedding = embedding_json
                                changes_made = True
                                
                    if changes_made:
                        session.commit()
                        # print(f"💾 Guardado en DB issue #{issue_num}")
                        
                    return False # Retornar False para que GLib no lo vuelva a llamar
                    
                except Exception as e:
                    print(f"❌ Error guardando cover result en DB thread principal: {e}")
                    session.rollback()
                    return False

            # Programar ejecución en main thread
            GLib.idle_add(_update_db_in_main_thread)

        # Usar el nuevo método unificado del repositorio
        volume_repo.download_covers_concurrently(
            volume, 
            detailed_issues, 
            progress_callback=progress_callback,
            background=True,
            result_callback=save_cover_result
        )
        print("DEBUG: Hilo de descarga iniciado (Repository)")

    except Exception as e:
        print(f"Error en actualización ComicVine: {e}")
        show_update_error(main_window, f"Error durante la actualización: {str(e)}")
        session.rollback()

    return False


def update_existing_issue(existing_issue, issue_data, session):
    """Actualizar un issue existente con datos de ComicVine"""
    # Actualizar campos si vienen datos nuevos
    if issue_data.get('name') and not existing_issue.titulo:
        existing_issue.titulo = issue_data['name']

    if issue_data.get('description') and not existing_issue.resumen:
        existing_issue.resumen = clean_html_text(issue_data['description'])

    if issue_data.get('cover_date'):
        try:
            fecha_str = issue_data['cover_date']
            if fecha_str and len(fecha_str) >= 4:
                existing_issue.fecha_tapa = int(fecha_str[:4])
        except (ValueError, TypeError):
            pass

    # Actualizar ComicVine ID y URLs siempre (para corregir datos desactualizados)
    if issue_data.get('id'):
        existing_issue.comicvine_id = issue_data['id']
        print(f"🔄 DEBUG: Actualizando ComicVine ID para issue #{existing_issue.numero}: {issue_data['id']}")

    if issue_data.get('api_detail_url'):
        existing_issue.url_api_detalle = issue_data['api_detail_url']
        print(f"🔄 DEBUG: Actualizando API URL para issue #{existing_issue.numero}")

    if issue_data.get('site_detail_url'):
        existing_issue.url_sitio_web = issue_data['site_detail_url']
        print(f"🔄 DEBUG: Actualizando site URL para issue #{existing_issue.numero}")


def create_new_issue(volume, issue_data, session):
    """Crear un nuevo issue desde datos de ComicVine"""
    try:
        new_issue = ComicbookInfo()
        new_issue.id_volume = volume.id_volume
        new_issue.numero = str(issue_data.get('issue_number', ''))
        new_issue.titulo = issue_data.get('name', '')
        new_issue.resumen = clean_html_text(issue_data.get('description', ''))

        # Fecha de portada
        if issue_data.get('cover_date'):
            try:
                fecha_str = issue_data['cover_date']
                if fecha_str and len(fecha_str) >= 4:
                    new_issue.fecha_tapa = int(fecha_str[:4])
            except (ValueError, TypeError):
                pass

        # Guardar ComicVine ID y URLs
        new_issue.comicvine_id = issue_data.get('id', 0)
        new_issue.url_api_detalle = issue_data.get('api_detail_url', '')
        new_issue.url_sitio_web = issue_data.get('site_detail_url', '')

        print(f"➕ DEBUG: Nuevo issue #{new_issue.numero} con ComicVine ID: {new_issue.comicvine_id}")

        session.add(new_issue)

    except Exception as e:
        print(f"Error creando nuevo issue: {e}")


def download_issue_cover(issue_data, volume, session, force_redownload=False):
    """Descargar portadas del issue (principal y variantes). 
    Retorna True si descarga al menos una imagen nueva.
    
    Args:
        issue_data: Datos del issue desde ComicVine
        volume: Objeto Volume
        session: Sesión de base de datos
        force_redownload: Si es True, reescribe los archivos aunque ya existan
    """
    try:
        from helpers.image_downloader import download_image
        from helpers.cover_download_notifier import get_notifier
        import os

        issue_number = str(issue_data.get('issue_number', 'N/A'))
        print(f"DEBUG: Iniciando descarga de portadas para issue {issue_number}")
        
        if force_redownload:
            print(f"DEBUG: Modo FORCE_REDOWNLOAD activado")

        # Recopilar todas las URLs de imágenes disponibles
        image_urls = []
        
        # 1. Imagen principal
        if issue_data.get('image') and issue_data['image'].get('medium_url'):
            image_urls.append(issue_data['image']['medium_url'])
            
        # 2. Imágenes asociadas (variantes, etc.)
        if issue_data.get('associated_images'):
            for img in issue_data['associated_images']:
                if img.get('medium_url'):
                    image_urls.append(img['medium_url'])
                elif img.get('original_url'):
                    image_urls.append(img['original_url'])
                    
        # 3. Lista de imágenes genérica (por si acaso)
        if issue_data.get('images'):
            for img in issue_data['images']:
                if img.get('medium_url'):
                    image_urls.append(img['medium_url'])

        # Eliminar duplicados manteniendo orden
        unique_urls = []
        seen = set()
        for url in image_urls:
            if url not in seen:
                unique_urls.append(url)
                seen.add(url)
                
        if not unique_urls:
            print(f"No hay imágenes disponibles para issue {issue_number}")
            return False

        print(f"DEBUG: Encontradas {len(unique_urls)} imágenes para descargar")

        # Preparar carpeta de destino
        clean_volume_name = "".join([c if c.isalnum() or c.isspace() else "" for c in volume.nombre]).strip()
        from helpers.thumbnail_path import get_thumbnails_base_path
        carpeta_destino = os.path.join(
            get_thumbnails_base_path(), "comicbook_info",
            f"{clean_volume_name}_{volume.id_volume}"
        )

        try:
            os.makedirs(carpeta_destino, exist_ok=True)
        except Exception as e:
            print(f"ERROR: No se pudo crear carpeta {carpeta_destino}: {e}")
            return False

        # Buscar el ComicbookInfo correspondiente
        comic_info = session.query(ComicbookInfo).filter(
            ComicbookInfo.id_volume == volume.id_volume,
            ComicbookInfo.numero == str(issue_data.get('issue_number', ''))
        ).first()

        any_downloaded_new = False

        # Procesar cada URL
        for image_url in unique_urls:
            try:
                nombre_archivo = image_url.split('/')[-1]
                ruta_archivo = os.path.join(carpeta_destino, nombre_archivo)
                
                downloaded_this = False
                
                # Si force_redownload, borrar archivo existente
                if force_redownload and os.path.exists(ruta_archivo):
                    try:
                        os.remove(ruta_archivo)
                        print(f"DEBUG: Archivo borrado para redescarga: {nombre_archivo}")
                    except Exception as e:
                        print(f"ERROR: No se pudo borrar {nombre_archivo}: {e}")

                # Descargar si no existe
                if not os.path.exists(ruta_archivo):
                    print(f"Descargando: {nombre_archivo}")
                    # NOTA: Usar resize_height=400 para consistencia con el nuevo proceso
                    resultado = download_image(image_url, carpeta_destino, nombre_archivo, resize_height=400)
                    if resultado:
                        downloaded_this = True
                        any_downloaded_new = True
                        print(f"DEBUG: Descargado exitosamente: {nombre_archivo}")
                    else:
                        print(f"ERROR: Falló descarga de {nombre_archivo}")
                else:
                    print(f"DEBUG: Ya existe: {nombre_archivo}")

                # Registrar en base de datos si tenemos el comic_info y el archivo existe
                if comic_info and os.path.exists(ruta_archivo):
                    from entidades.comicbook_info_cover_model import ComicbookInfoCover
                    
                    # Verificar si existe el registro
                    existing_cover = session.query(ComicbookInfoCover).filter(
                        ComicbookInfoCover.id_comicbook_info == comic_info.id_comicbook_info,
                        ComicbookInfoCover.url_imagen == image_url
                    ).first()

                    if not existing_cover:
                        new_cover = ComicbookInfoCover()
                        new_cover.id_comicbook_info = comic_info.id_comicbook_info
                        new_cover.url_imagen = image_url
                        session.add(new_cover)
                        print(f"Agregado registro de portada: {nombre_archivo}")
                        try:
                            session.commit()
                        except:
                            session.rollback()
                        
                        # Si ya existe y se redescargó (downloaded_this), invalidar embedding
                        # para que se regenere
                        if existing_cover and downloaded_this:
                            try:
                                existing_cover.embedding = None
                                session.commit()
                                print(f"DEBUG: Embedding invalidado para: {nombre_archivo}")
                            except Exception as e:
                                print(f"Error invalidando embedding: {e}")

                # Notificar si se descargó algo nuevo
                if downloaded_this:
                    try:
                        notifier = get_notifier()
                        GLib.idle_add(notifier.notify_cover_downloaded, volume.id_volume, issue_number, ruta_archivo)
                    except Exception as e:
                        print(f"Error notificando: {e}")

            except Exception as e:
                print(f"Error procesando imagen {image_url}: {e}")

        return any_downloaded_new

    except Exception as e:
        print(f"Error general descargando portadas: {e}")
        return False


def check_and_download_missing_covers(volume, session, comicvine_client):
    """Verificar y descargar portadas faltantes para issues existentes"""
    # Mantenemos esta función por compatibilidad si es llamada desde otros lugares,
    # pero internamente podría delegar o simplificarse.
    # Por ahora la dejamos funcional como fallback.
    try:
        import os
        downloaded_count = 0

        # Obtener todos los issues del volumen que no tienen portadas o cuyas portadas no existen físicamente
        from entidades.comicbook_info_cover_model import ComicbookInfoCover

        # Issues sin portadas en base de datos
        issues_without_covers = session.query(ComicbookInfo).outerjoin(ComicbookInfoCover).filter(
            ComicbookInfo.id_volume == volume.id_volume,
            ComicbookInfoCover.id_cover.is_(None)
        ).all()

        print(f"Encontrados {len(issues_without_covers)} issues sin portadas en base de datos")

        # Issues con portadas en base de datos pero archivos faltantes
        issues_with_covers = session.query(ComicbookInfo).join(ComicbookInfoCover).filter(
            ComicbookInfo.id_volume == volume.id_volume
        ).all()

        issues_missing_files = []
        for issue in issues_with_covers:
            try:
                cover_path = issue.obtener_portada_principal()
                if cover_path == "images/Comic_sin_caratula.png" or not os.path.exists(cover_path):
                    issues_missing_files.append(issue)
            except:
                issues_missing_files.append(issue)

        print(f"Encontrados {len(issues_missing_files)} issues con archivos de portada faltantes")

        # Combinar ambas listas sin duplicados
        all_issues_missing = list(set(issues_without_covers + issues_missing_files))

        if not all_issues_missing:
            print("No se encontraron portadas faltantes")
            return 0

        # Si el volumen tiene ID de ComicVine, obtener todos los issues de CV para hacer match
        comicvine_issues = {}
        if volume.id_comicvine:
            try:
                cv_issues = comicvine_client.get_volume_issues(volume.id_comicvine)
                if cv_issues:
                    # Crear diccionario por número de issue para match rápido
                    comicvine_issues = {str(issue.get('issue_number', '')): issue for issue in cv_issues}
            except Exception as e:
                print(f"Error obteniendo issues de ComicVine: {e}")

        # Para cada issue faltante, buscar en ComicVine por número
        for issue in all_issues_missing:
            try:
                if volume.id_comicvine and issue.numero in comicvine_issues:
                    # Obtener detalles del issue desde ComicVine usando el número
                    cv_issue = comicvine_issues[issue.numero]
                    if cv_issue and download_issue_cover(cv_issue, volume, session):
                        downloaded_count += 1
                        print(f"Portada descargada para issue #{issue.numero}")
                else:
                    print(f"Issue #{issue.numero} no encontrado en ComicVine o volumen sin ID CV, saltando...")

            except Exception as e:
                print(f"Error procesando portada para issue #{issue.numero}: {e}")

        print(f"Descargadas {downloaded_count} portadas faltantes")
        return downloaded_count

    except Exception as e:
        print(f"Error verificando portadas faltantes: {e}")
        return 0

# NOTE: download_covers_in_background, collect_missing_covers, download_single_cover 
# were removed/replaced by VolumeRepository.download_covers_concurrently logic



# FUNCIÓN OBSOLETA - Ya no es necesaria gracias al sistema de actualización en tiempo real
# def refresh_issues_tab_delayed(volume, main_window):
#     """Refrescar la pestaña de issues con un pequeño delay"""
#     import time
#     time.sleep(1)  # Pequeño delay para asegurar que las imágenes estén escritas
#
#     # Refrescar vista sin borrar cache
#     if hasattr(main_window, 'navigation_view'):
#         try:
#             # Solo re-navegar para refrescar la vista, SIN borrar cache
#             print(f"DEBUG: Refrescando vista del volumen {volume.nombre} sin borrar cache")
#             main_window.navigate_to_volume_detail(volume)
#         except Exception as e:
#             print(f"Error refrescando vista: {e}")


def refresh_issues_tab(tab_view, volume, session, thumbnail_generator, main_window):
    """Refrescar la pestaña de issues después de la actualización"""
    try:
        # Buscar la pestaña de issues (segunda pestaña, índice 1)
        issues_page = tab_view.get_nth_page(1)
        if issues_page:
            # Recrear el contenido de la pestaña
            new_content = create_issues_tab_content(volume, session, thumbnail_generator, main_window)
            # Usar el método correcto para TabPage
            if hasattr(issues_page, 'set_child'):
                issues_page.set_child(new_content)
            elif hasattr(issues_page, 'get_child') and hasattr(issues_page.get_child(), 'set_child'):
                issues_page.get_child().set_child(new_content)
            else:
                print("DEBUG: No se pudo actualizar la pestaña, método no encontrado")

    except Exception as e:
        print(f"Error refrescando pestaña de issues: {e}")


def show_update_progress(main_window, message):
    """Mostrar progreso de actualización"""
    try:
        toast = Adw.Toast.new(message)
        toast.set_timeout(2)
        main_window.toast_overlay.add_toast(toast)
    except Exception as e:
        print(f"Progress: {message}")


def show_update_success(main_window, message):
    """Mostrar mensaje de éxito"""
    try:
        toast = Adw.Toast.new(message)
        toast.set_timeout(4)
        main_window.toast_overlay.add_toast(toast)
    except Exception as e:
        print(f"Success: {message}")


def show_update_error(main_window, message):
    """Mostrar mensaje de error"""
    try:
        toast = Adw.Toast.new(f"Error: {message}")
        toast.set_timeout(5)
        main_window.toast_overlay.add_toast(toast)
    except Exception as e:
        print(f"Error: {message}")


def create_issues_tab_content(volume, session, thumbnail_generator, main_window):
    """Crear contenido de la pestaña de issues (para refresh)"""
    # Esta función duplica parte de create_issues_tab pero solo el contenido
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
    box.set_margin_start(20)
    box.set_margin_end(20)
    box.set_margin_top(20)
    box.set_margin_bottom(20)

    # Scroll para los issues
    scrolled = Gtk.ScrolledWindow()
    scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scrolled.set_vexpand(True)

    # FlowBox para las cards de issues
    flow_box = Gtk.FlowBox()
    flow_box.set_valign(Gtk.Align.START)
    flow_box.set_max_children_per_line(4)
    flow_box.set_selection_mode(Gtk.SelectionMode.NONE)
    flow_box.set_homogeneous(True)
    flow_box.set_column_spacing(15)
    flow_box.set_row_spacing(15)

    scrolled.set_child(flow_box)
    box.append(scrolled)

    # Obtener configuración de batch_size
    from repositories.setup_repository import SetupRepository
    setup_repo = SetupRepository(session)
    config = setup_repo.obtener_o_crear_configuracion()
    batch_size = config.items_per_batch if config else 20

    # Inicializar variables de paginado
    flow_box.loaded_count = 0
    flow_box.batch_size = batch_size
    flow_box.is_loading = False

    # Conectar evento de scroll para cargar más
    vadj = scrolled.get_vadjustment()
    vadj.connect("value-changed", on_issues_scroll, flow_box, volume, session, thumbnail_generator, main_window)

    # Cargar primer lote
    GLib.idle_add(load_comics_batch, volume, session, thumbnail_generator, main_window, flow_box)

    return box