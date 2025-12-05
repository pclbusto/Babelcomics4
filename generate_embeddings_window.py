"""
Ventana para generar embeddings de covers con progreso visual
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, GdkPixbuf, Gio, Gdk
import threading
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from entidades.comicbook_info_cover_model import ComicbookInfoCover
from helpers.embedding_generator import get_embedding_generator


class GenerateEmbeddingsWindow(Adw.Window):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_default_size(800, 600)
        self.set_title("Generar Embeddings de Covers")

        self.processing = False
        self.cancelled = False

        # Layout principal
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_content(main_box)

        # Header bar
        header = Adw.HeaderBar()
        main_box.append(header)

        # Botón cancelar
        self.cancel_button = Gtk.Button(label="Cancelar")
        self.cancel_button.add_css_class("destructive-action")
        self.cancel_button.connect("clicked", self.on_cancel_clicked)
        header.pack_end(self.cancel_button)

        # Contenido principal
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content_box.set_margin_top(12)
        content_box.set_margin_bottom(12)
        content_box.set_margin_start(12)
        content_box.set_margin_end(12)
        main_box.append(content_box)

        # Stats box
        stats_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        stats_box.set_homogeneous(True)
        content_box.append(stats_box)

        # Stat cards
        self.total_label = self._create_stat_card("Total", "0")
        self.processed_label = self._create_stat_card("Procesadas", "0")
        self.skipped_label = self._create_stat_card("Omitidas", "0")
        self.errors_label = self._create_stat_card("Errores", "0")

        stats_box.append(self.total_label)
        stats_box.append(self.processed_label)
        stats_box.append(self.skipped_label)
        stats_box.append(self.errors_label)

        # Progress bar
        progress_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        content_box.append(progress_box)

        self.progress_label = Gtk.Label(label="Preparando...")
        self.progress_label.set_xalign(0)
        progress_box.append(self.progress_label)

        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        progress_box.append(self.progress_bar)

        # Imagen actual preview
        preview_frame = Gtk.Frame()
        preview_frame.set_margin_top(12)
        content_box.append(preview_frame)

        preview_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        preview_box.set_margin_top(6)
        preview_box.set_margin_bottom(6)
        preview_box.set_margin_start(6)
        preview_box.set_margin_end(6)
        preview_frame.set_child(preview_box)

        preview_label = Gtk.Label(label="<b>Procesando:</b>")
        preview_label.set_use_markup(True)
        preview_label.set_xalign(0)
        preview_box.append(preview_label)

        self.current_image = Gtk.Picture()
        self.current_image.set_size_request(200, 300)
        self.current_image.set_can_shrink(True)
        preview_box.append(self.current_image)

        self.current_name_label = Gtk.Label(label="")
        self.current_name_label.set_xalign(0)
        self.current_name_label.set_wrap(True)
        preview_box.append(self.current_name_label)

        # Log scrolled window
        log_frame = Gtk.Frame()
        log_frame.set_vexpand(True)
        content_box.append(log_frame)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        log_frame.set_child(scrolled)

        self.log_view = Gtk.TextView()
        self.log_view.set_editable(False)
        self.log_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.log_view.set_monospace(True)
        self.log_view.set_margin_top(6)
        self.log_view.set_margin_bottom(6)
        self.log_view.set_margin_start(6)
        self.log_view.set_margin_end(6)
        scrolled.set_child(self.log_view)

        self.log_buffer = self.log_view.get_buffer()

        # Iniciar automáticamente
        GLib.idle_add(self.start_processing)

    def _create_stat_card(self, title, value):
        """Crea una tarjeta de estadística"""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.add_css_class("card")
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        box.set_margin_start(6)
        box.set_margin_end(6)

        title_label = Gtk.Label(label=title)
        title_label.add_css_class("dim-label")
        box.append(title_label)

        value_label = Gtk.Label(label=value)
        value_label.add_css_class("title-1")
        box.append(value_label)

        return box

    def log(self, message):
        """Agrega mensaje al log"""
        GLib.idle_add(self._append_log, message)

    def _append_log(self, message):
        """Agrega mensaje al buffer (thread-safe)"""
        end_iter = self.log_buffer.get_end_iter()
        self.log_buffer.insert(end_iter, message + "\n")

        # Auto-scroll al final
        mark = self.log_buffer.create_mark(None, end_iter, False)
        self.log_view.scroll_to_mark(mark, 0.0, True, 0.0, 1.0)

        return False

    def update_progress(self, current, total, cover_path=None):
        """Actualiza barra de progreso"""
        def _update():
            fraction = current / total if total > 0 else 0
            self.progress_bar.set_fraction(fraction)
            self.progress_bar.set_text(f"{current}/{total}")
            self.progress_label.set_text(f"Procesando cover {current} de {total}...")

            if cover_path and os.path.exists(cover_path):
                try:
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                        cover_path, 200, 300, True
                    )
                    texture = Gdk.Texture.new_for_pixbuf(pixbuf)
                    self.current_image.set_paintable(texture)
                    self.current_name_label.set_text(os.path.basename(cover_path))
                except Exception as e:
                    self.log(f"Error cargando preview: {e}")

            return False

        GLib.idle_add(_update)

    def update_stats(self, total, processed, skipped, errors):
        """Actualiza estadísticas"""
        def _update():
            # Obtener los value labels (segundo hijo de cada card)
            self.total_label.get_last_child().set_text(str(total))
            self.processed_label.get_last_child().set_text(str(processed))
            self.skipped_label.get_last_child().set_text(str(skipped))
            self.errors_label.get_last_child().set_text(str(errors))
            return False

        GLib.idle_add(_update)

    def on_cancel_clicked(self, button):
        """Cancelar proceso"""
        self.cancelled = True
        self.log("⚠️ Cancelando...")
        button.set_sensitive(False)

    def start_processing(self):
        """Inicia el procesamiento en background"""
        if self.processing:
            return

        self.processing = True
        thread = threading.Thread(target=self.process_embeddings)
        thread.daemon = True
        thread.start()

    def process_embeddings(self):
        """Procesa embeddings (corre en thread separado)"""
        try:
            # Conectar a BD
            db_path = os.path.join('data', 'babelcomics.db')
            engine = create_engine(f'sqlite:///{db_path}')
            Session = sessionmaker(bind=engine)
            session = Session()

            self.log("🚀 Iniciando generación de embeddings...")
            self.log("📊 Cargando modelo CLIP...")

            # Cargar generador
            emb_gen = get_embedding_generator()

            self.log("✅ Modelo cargado")
            self.log("")

            # Obtener covers sin embedding
            covers_sin_embedding = session.query(ComicbookInfoCover).filter(
                (ComicbookInfoCover.embedding == None) | (ComicbookInfoCover.embedding == '')
            ).all()

            total = len(covers_sin_embedding)
            self.log(f"📦 Total de covers sin embedding: {total}")
            self.log("")

            if total == 0:
                self.log("✅ Todas las covers ya tienen embeddings!")
                GLib.idle_add(self.on_complete)
                return

            processed = 0
            skipped = 0
            errors = 0
            batch_size = 50

            for i, cover in enumerate(covers_sin_embedding, 1):
                if self.cancelled:
                    self.log("❌ Proceso cancelado por el usuario")
                    break

                try:
                    # Obtener ruta
                    imagen_path = cover.obtener_ruta_local()

                    # Verificar si existe
                    if "Comic_sin_caratula" in imagen_path or not os.path.exists(imagen_path):
                        skipped += 1
                        self.update_stats(total, processed, skipped, errors)
                        self.update_progress(i, total)
                        continue

                    # Generar embedding
                    self.log(f"[{i}/{total}] {os.path.basename(imagen_path)}")
                    self.update_progress(i, total, imagen_path)

                    embedding = emb_gen.generate_embedding(imagen_path)

                    if embedding is not None:
                        cover.embedding = emb_gen.embedding_to_json(embedding)
                        processed += 1

                        # Commit por batches
                        if processed % batch_size == 0:
                            session.commit()
                            self.log(f"  ✓ Guardadas {processed} covers")
                    else:
                        errors += 1
                        self.log(f"  ✗ Error generando embedding")

                    self.update_stats(total, processed, skipped, errors)

                except Exception as e:
                    errors += 1
                    self.log(f"  ✗ Error: {e}")
                    self.update_stats(total, processed, skipped, errors)

            # Commit final
            session.commit()
            session.close()

            self.log("")
            self.log("="*60)
            self.log("✅ PROCESO COMPLETADO")
            self.log(f"   Procesadas: {processed}")
            self.log(f"   Omitidas: {skipped}")
            self.log(f"   Errores: {errors}")
            self.log("="*60)

            GLib.idle_add(self.on_complete)

        except Exception as e:
            self.log(f"❌ ERROR FATAL: {e}")
            import traceback
            self.log(traceback.format_exc())
            GLib.idle_add(self.on_complete)

    def on_complete(self):
        """Proceso completado"""
        self.processing = False
        self.progress_label.set_text("Completado")
        self.cancel_button.set_label("Cerrar")
        self.cancel_button.set_sensitive(True)
        self.cancel_button.remove_css_class("destructive-action")
        self.cancel_button.connect("clicked", lambda b: self.close())
        return False
