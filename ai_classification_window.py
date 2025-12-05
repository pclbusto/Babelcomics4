"""
Ventana de auto-clasificación por IA usando embeddings visuales.
Muestra comics sin clasificar y sugiere los mejores matches globalmente.
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, GdkPixbuf, Gdk
import os
import threading
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from entidades.comicbook_model import Comicbook
from entidades.comicbook_info_cover_model import ComicbookInfoCover
from entidades.comicbook_info_model import ComicbookInfo
from helpers.embedding_generator import get_embedding_generator


class AIClassificationWindow(Adw.Window):
    def __init__(self, parent, session, comic_ids):
        super().__init__()
        self.parent = parent
        self.session = session
        self.comic_ids = comic_ids  # IDs de comics pre-seleccionados
        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_default_size(950, 1275)  # 25% más alta (700 -> 875)
        self.set_title("Auto-Clasificación por IA")

        self.threshold = 0.75
        self.current_index = 0
        self.comics_to_classify = []
        self.classified_count = 0
        self.skipped_count = 0
        self.emb_gen = None
        self.candidate_embeddings = []
        self.cover_to_info = {}
        self.current_matches = []

        # Layout principal
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_content(main_box)

        # Header bar
        header = Adw.HeaderBar()
        main_box.append(header)

        # Botón configuración umbral
        threshold_button = Gtk.Button()
        threshold_button.set_icon_name("preferences-other-symbolic")
        threshold_button.set_tooltip_text("Configurar umbral de similaridad")
        threshold_button.connect("clicked", self.on_configure_threshold)
        header.pack_end(threshold_button)

        # Contenido principal con scroll
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        main_box.append(scrolled)

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content_box.set_margin_top(12)
        content_box.set_margin_bottom(12)
        content_box.set_margin_start(12)
        content_box.set_margin_end(12)
        scrolled.set_child(content_box)

        # Stats bar
        stats_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        stats_box.set_homogeneous(True)
        content_box.append(stats_box)

        self.total_label = self._create_stat_card("Total", "0")
        self.classified_label = self._create_stat_card("Clasificados", "0", "success")
        self.skipped_label = self._create_stat_card("Omitidos", "0", "warning")
        self.remaining_label = self._create_stat_card("Restantes", "0")

        stats_box.append(self.total_label)
        stats_box.append(self.classified_label)
        stats_box.append(self.skipped_label)
        stats_box.append(self.remaining_label)

        # Comic actual
        current_frame = Gtk.Frame()
        current_frame.set_label("Comic Actual")
        content_box.append(current_frame)

        current_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        current_box.set_margin_top(12)
        current_box.set_margin_bottom(12)
        current_box.set_margin_start(12)
        current_box.set_margin_end(12)
        current_frame.set_child(current_box)

        self.current_comic_label = Gtk.Label(label="Cargando...")
        self.current_comic_label.add_css_class("title-2")
        self.current_comic_label.set_wrap(True)
        current_box.append(self.current_comic_label)

        self.current_comic_image = Gtk.Picture()
        self.current_comic_image.set_size_request(200, 300)
        self.current_comic_image.set_can_shrink(True)
        current_box.append(self.current_comic_image)

        # Status label
        self.status_label = Gtk.Label(label="")
        self.status_label.add_css_class("dim-label")
        self.status_label.set_wrap(True)
        current_box.append(self.status_label)

        # Matches carousel
        matches_frame = Gtk.Frame()
        matches_frame.set_label("Top 3 Matches (navega con ← → o desliza)")
        content_box.append(matches_frame)

        carousel_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        carousel_box.set_margin_top(12)
        carousel_box.set_margin_bottom(12)
        carousel_box.set_margin_start(12)
        carousel_box.set_margin_end(12)
        matches_frame.set_child(carousel_box)

        # Carousel para mostrar matches de a uno
        self.carousel = Adw.Carousel()
        self.carousel.set_allow_mouse_drag(True)
        self.carousel.set_allow_scroll_wheel(True)
        self.carousel.set_vexpand(True)
        # Reducir altura para que los botones sean visibles
        self.carousel.set_size_request(-1, 420)
        carousel_box.append(self.carousel)

        # Indicador de páginas
        self.carousel_indicator = Adw.CarouselIndicatorDots()
        self.carousel_indicator.set_carousel(self.carousel)
        carousel_box.append(self.carousel_indicator)

        # Botones de navegación
        nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        nav_box.set_halign(Gtk.Align.CENTER)
        carousel_box.append(nav_box)

        prev_button = Gtk.Button(label="← Anterior")
        prev_button.connect("clicked", lambda b: self.carousel.scroll_to(
            self.carousel.get_nth_page(max(0, int(self.carousel.get_position()) - 1)), True
        ))
        nav_box.append(prev_button)

        self.match_label = Gtk.Label(label="Match 1 de 3")
        self.match_label.add_css_class("title-3")
        nav_box.append(self.match_label)

        next_button = Gtk.Button(label="Siguiente →")
        next_button.connect("clicked", lambda b: self.carousel.scroll_to(
            self.carousel.get_nth_page(min(self.carousel.get_n_pages() - 1, int(self.carousel.get_position()) + 1)), True
        ))
        nav_box.append(next_button)

        # Conectar señal de cambio de página
        self.carousel.connect("page-changed", self.on_carousel_page_changed)

        # Botones de acción
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        action_box.set_halign(Gtk.Align.CENTER)
        action_box.set_margin_top(12)
        content_box.append(action_box)

        self.skip_button = Gtk.Button(label="⏭️ Omitir Este Comic")
        self.skip_button.set_size_request(180, 50)
        self.skip_button.add_css_class("pill")
        self.skip_button.connect("clicked", self.on_skip_clicked)
        action_box.append(self.skip_button)

        self.apply_button = Gtk.Button(label="✅ Aplicar Este Match")
        self.apply_button.set_size_request(220, 50)
        self.apply_button.add_css_class("suggested-action")
        self.apply_button.add_css_class("pill")
        self.apply_button.connect("clicked", self.on_apply_clicked)
        action_box.append(self.apply_button)

        # Inicializar
        GLib.idle_add(self.initialize)

    def _create_stat_card(self, title, value, style=None):
        """Crea tarjeta de estadística"""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.add_css_class("card")
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        box.set_margin_start(6)
        box.set_margin_end(6)

        if style:
            box.add_css_class(style)

        title_label = Gtk.Label(label=title)
        title_label.add_css_class("dim-label")
        box.append(title_label)

        value_label = Gtk.Label(label=value)
        value_label.add_css_class("title-1")
        box.append(value_label)

        return box

    def update_stats(self):
        """Actualiza estadísticas"""
        total = len(self.comics_to_classify)
        remaining = total - self.current_index

        self.total_label.get_last_child().set_text(str(total))
        self.classified_label.get_last_child().set_text(str(self.classified_count))
        self.skipped_label.get_last_child().set_text(str(self.skipped_count))
        self.remaining_label.get_last_child().set_text(str(remaining))

    def initialize(self):
        """Inicializa datos en background"""
        thread = threading.Thread(target=self._load_data)
        thread.daemon = True
        thread.start()

    def _load_data(self):
        """Carga datos (thread)"""
        try:
            GLib.idle_add(self.status_label.set_text, "🔄 Cargando modelo CLIP...")

            # Cargar generador de embeddings
            self.emb_gen = get_embedding_generator()

            GLib.idle_add(self.status_label.set_text, "📊 Cargando embeddings de covers...")

            # Cargar todos los embeddings de covers
            covers_con_embedding = self.session.query(ComicbookInfoCover).filter(
                ComicbookInfoCover.embedding != None,
                ComicbookInfoCover.embedding != ''
            ).all()

            if len(covers_con_embedding) == 0:
                GLib.idle_add(self._show_error, "No hay covers con embeddings. Ejecuta 'Generar Embeddings' primero.")
                return

            # Crear índice
            self.cover_to_info = {cover.id_cover: cover.id_comicbook_info for cover in covers_con_embedding}
            self.candidate_embeddings = [
                (cover.id_cover, self.emb_gen.json_to_embedding(cover.embedding))
                for cover in covers_con_embedding
            ]

            GLib.idle_add(self.status_label.set_text, f"✅ {len(covers_con_embedding)} covers cargadas")

            # Obtener los comics pre-seleccionados por el usuario
            self.comics_to_classify = self.session.query(Comicbook).filter(
                Comicbook.id_comicbook.in_(self.comic_ids)
            ).filter(
                Comicbook.en_papelera == False
            ).all()

            if len(self.comics_to_classify) == 0:
                GLib.idle_add(self._show_error, "No hay comics seleccionados para clasificar!")
                return

            GLib.idle_add(self.status_label.set_text, f"📚 {len(self.comics_to_classify)} comics para clasificar")
            GLib.idle_add(self.update_stats)
            GLib.idle_add(self.show_current_comic)

        except Exception as e:
            GLib.idle_add(self._show_error, f"Error inicializando: {e}")
            import traceback
            traceback.print_exc()

    def _show_error(self, message):
        """Muestra error"""
        self.status_label.set_text(f"❌ {message}")
        self.apply_button.set_sensitive(False)
        self.skip_button.set_sensitive(False)

    def show_current_comic(self):
        """Muestra el comic actual y busca matches"""
        if self.current_index >= len(self.comics_to_classify):
            self._show_completed()
            return

        comic = self.comics_to_classify[self.current_index]

        # Actualizar UI
        self.current_comic_label.set_text(f"[{self.current_index + 1}/{len(self.comics_to_classify)}] {comic.nombre_archivo}")

        # Cargar preview
        cover_path = comic.obtener_cover()
        if os.path.exists(cover_path) and "Comic_sin_caratula" not in cover_path:
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(cover_path, 200, 300, True)
                texture = Gdk.Texture.new_for_pixbuf(pixbuf)
                self.current_comic_image.set_paintable(texture)
            except:
                pass

        # Buscar matches en background
        self.status_label.set_text("🔍 Buscando mejores matches...")
        thread = threading.Thread(target=self._find_matches, args=(comic,))
        thread.daemon = True
        thread.start()

    def _find_matches(self, comic):
        """Busca los mejores matches (thread)"""
        try:
            # Obtener embedding del comic
            cover_path = comic.obtener_cover()

            if not os.path.exists(cover_path) or "Comic_sin_caratula" in cover_path:
                GLib.idle_add(self._show_no_thumbnail)
                return

            # Generar o usar embedding existente
            if comic.embedding:
                embedding = self.emb_gen.json_to_embedding(comic.embedding)
            else:
                embedding = self.emb_gen.generate_embedding(cover_path)
                if embedding:
                    comic.embedding = self.emb_gen.embedding_to_json(embedding)
                    self.session.commit()

            if embedding is None:
                GLib.idle_add(self._show_error, "Error generando embedding del comic")
                return

            # Buscar todos los matches y ordenar por similaridad
            matches = []
            for cover_id, candidate_emb in self.candidate_embeddings:
                similarity = self.emb_gen.calculate_similarity(embedding, candidate_emb)
                comicbook_info_id = self.cover_to_info[cover_id]
                matches.append((comicbook_info_id, similarity, cover_id))

            # Ordenar por similaridad (mayor primero)
            matches.sort(key=lambda x: x[1], reverse=True)

            # Tomar top 3
            top_matches = matches[:3]

            GLib.idle_add(self._display_matches, top_matches)

        except Exception as e:
            GLib.idle_add(self._show_error, f"Error buscando matches: {e}")
            import traceback
            traceback.print_exc()

    def _show_no_thumbnail(self):
        """No hay thumbnail para este comic"""
        self.status_label.set_text("⚠️ Este comic no tiene thumbnail. Generalo primero desde la app.")
        self.apply_button.set_sensitive(False)

        # Limpiar carousel
        while self.carousel.get_n_pages() > 0:
            self.carousel.remove(self.carousel.get_nth_page(0))

    def _display_matches(self, matches):
        """Muestra los matches en el carousel"""
        # Limpiar carousel
        while self.carousel.get_n_pages() > 0:
            self.carousel.remove(self.carousel.get_nth_page(0))

        self.current_matches = []

        if not matches:
            self.status_label.set_text("❌ No se encontraron matches")
            self.apply_button.set_sensitive(False)
            return

        for i, (info_id, similarity, cover_id) in enumerate(matches, 1):
            # Obtener ComicbookInfo
            info = self.session.query(ComicbookInfo).get(info_id)
            if not info:
                continue

            # Crear página del carousel para el match
            page = self._create_match_page(i, info, similarity, cover_id)
            self.carousel.append(page)

            # Guardar referencia (ya no necesitamos el widget card)
            self.current_matches.append((info_id, similarity))

        # Scroll al primer match
        if self.carousel.get_n_pages() > 0:
            self.carousel.scroll_to(self.carousel.get_nth_page(0), False)

        # Actualizar label
        self.match_label.set_text(f"Match 1 de {len(matches)}")

        # Actualizar status
        best_similarity = matches[0][1]
        if best_similarity >= self.threshold:
            self.status_label.set_text(f"✅ Mejor match: {best_similarity:.1%} (sobre umbral {self.threshold:.0%})")
            self.apply_button.set_sensitive(True)
        else:
            self.status_label.set_text(f"⚠️ Mejor match: {best_similarity:.1%} (bajo umbral {self.threshold:.0%})")
            self.apply_button.set_sensitive(True)

    def _create_match_page(self, rank, info, similarity, cover_id):
        """Crea página del carousel para un match"""
        # Box principal con borde para destacar
        main_frame = Gtk.Frame()
        main_frame.add_css_class("card")
        main_frame.set_margin_top(6)
        main_frame.set_margin_bottom(6)
        main_frame.set_margin_start(6)
        main_frame.set_margin_end(6)

        page_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        page_box.set_margin_top(12)
        page_box.set_margin_bottom(12)
        page_box.set_margin_start(24)
        page_box.set_margin_end(24)
        main_frame.set_child(page_box)

        # Badge "SELECCIONADO" prominente
        selected_badge = Gtk.Label(label="⭐ ESTE MATCH SE APLICARÁ ⭐")
        selected_badge.add_css_class("title-2")
        selected_badge.add_css_class("success")
        selected_badge.set_margin_bottom(6)
        page_box.append(selected_badge)

        # Header con ranking y similaridad
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        header_box.set_halign(Gtk.Align.CENTER)
        page_box.append(header_box)

        rank_label = Gtk.Label(label=f"Match #{rank}")
        rank_label.add_css_class("title-1")
        header_box.append(rank_label)

        similarity_label = Gtk.Label(label=f"{similarity:.1%}")
        if similarity >= self.threshold:
            similarity_label.add_css_class("success")
        else:
            similarity_label.add_css_class("warning")
        similarity_label.add_css_class("title-1")
        header_box.append(similarity_label)

        # Cover reducido 25% (de 300x450 a 225x338)
        cover = self.session.query(ComicbookInfoCover).get(cover_id)
        if cover:
            cover_path = cover.obtener_ruta_local()
            if os.path.exists(cover_path):
                try:
                    picture = Gtk.Picture()
                    picture.set_can_shrink(True)
                    picture.set_halign(Gtk.Align.CENTER)
                    # Cover 25% más pequeño
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(cover_path, 225, 338, True)
                    texture = Gdk.Texture.new_for_pixbuf(pixbuf)
                    picture.set_paintable(texture)
                    page_box.append(picture)
                except Exception as e:
                    error_label = Gtk.Label(label=f"Error cargando cover: {e}")
                    error_label.add_css_class("dim-label")
                    page_box.append(error_label)

        # Info del comic
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        info_box.set_halign(Gtk.Align.CENTER)
        info_box.set_margin_top(12)
        page_box.append(info_box)

        title_label = Gtk.Label(label=info.titulo)
        title_label.add_css_class("title-2")
        title_label.set_wrap(True)
        title_label.set_max_width_chars(50)
        info_box.append(title_label)

        number_label = Gtk.Label(label=f"Número: #{info.numero}")
        number_label.add_css_class("title-3")
        info_box.append(number_label)

        if info.volume:
            volume_label = Gtk.Label(label=f"Serie: {info.volume.nombre}")
            volume_label.add_css_class("dim-label")
            volume_label.set_wrap(True)
            volume_label.set_max_width_chars(50)
            info_box.append(volume_label)

        if info.fecha_tapa:
            date_label = Gtk.Label(label=f"Fecha: {info.fecha_tapa}")
            date_label.add_css_class("dim-label")
            info_box.append(date_label)

        return main_frame

    def on_carousel_page_changed(self, carousel, index):
        """Actualiza el label cuando cambia la página del carousel"""
        n_pages = carousel.get_n_pages()
        if n_pages > 0:
            current_page = int(carousel.get_position()) + 1
            self.match_label.set_text(f"Match {current_page} de {n_pages}")

    def on_configure_threshold(self, button):
        """Configurar umbral"""
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading("Configurar Umbral")
        dialog.set_body(f"Umbral actual: {self.threshold:.0%}")
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("apply", "Aplicar")
        dialog.set_response_appearance("apply", Adw.ResponseAppearance.SUGGESTED)

        # Entry para nuevo valor
        entry = Gtk.Entry()
        entry.set_text(str(int(self.threshold * 100)))
        entry.set_placeholder_text("Ejemplo: 75 (para 75%)")

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        content.set_margin_start(12)
        content.set_margin_end(12)

        label = Gtk.Label(label="Nuevo umbral (0-100):")
        label.set_xalign(0)
        content.append(label)
        content.append(entry)

        dialog.set_extra_child(content)

        def on_response(dialog, response):
            if response == "apply":
                try:
                    value = int(entry.get_text())
                    if 0 <= value <= 100:
                        self.threshold = value / 100
                        # Re-evaluar matches actuales
                        if self.current_matches:
                            best = self.current_matches[0][1]
                            if best >= self.threshold:
                                self.status_label.set_text(f"✅ Mejor match: {best:.1%} (sobre umbral {self.threshold:.0%})")
                            else:
                                self.status_label.set_text(f"⚠️ Mejor match: {best:.1%} (bajo umbral {self.threshold:.0%})")
                except:
                    pass

        dialog.connect("response", on_response)
        dialog.present()

    def on_skip_clicked(self, button):
        """Omitir comic actual"""
        self.skipped_count += 1
        self.current_index += 1
        self.update_stats()
        self.show_current_comic()

    def on_apply_clicked(self, button):
        """Aplicar clasificación seleccionada (del match visible en el carousel)"""
        if not self.current_matches:
            dialog = Adw.MessageDialog.new(self)
            dialog.set_heading("Sin matches")
            dialog.set_body("No hay matches disponibles")
            dialog.add_response("ok", "OK")
            dialog.present()
            return

        # Obtener el match actualmente visible en el carousel
        current_page = int(self.carousel.get_position())
        if current_page >= len(self.current_matches):
            current_page = 0

        selected_info_id, similarity = self.current_matches[current_page]

        # Aplicar clasificación
        comic = self.comics_to_classify[self.current_index]
        comic.id_comicbook_info = str(selected_info_id)
        self.session.commit()

        self.classified_count += 1
        self.current_index += 1
        self.update_stats()
        self.show_current_comic()

    def _show_completed(self):
        """Proceso completado"""
        self.current_comic_label.set_text("✅ Clasificación Completada!")
        self.status_label.set_text(
            f"Clasificados: {self.classified_count} | Omitidos: {self.skipped_count}"
        )
        self.current_comic_image.set_paintable(None)

        # Limpiar carousel
        while self.carousel.get_n_pages() > 0:
            self.carousel.remove(self.carousel.get_nth_page(0))

        self.apply_button.set_sensitive(False)
        self.skip_button.set_label("Cerrar")
        self.skip_button.disconnect_by_func(self.on_skip_clicked)
        self.skip_button.connect("clicked", lambda b: self.close())
