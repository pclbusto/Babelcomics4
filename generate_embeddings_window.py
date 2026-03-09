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
from concurrent.futures import ThreadPoolExecutor, as_completed


import json

class GenerateEmbeddingsWindow(Adw.Window):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.set_transient_for(parent)
        self.set_modal(True)
        
        # Restore window size
        default_width, default_height = 800, 600
        try:
            if hasattr(self.parent, 'config') and self.parent.config and self.parent.config.window_state:
                states = json.loads(self.parent.config.window_state)
                if 'embeddings_window' in states:
                    w, h = states['embeddings_window']
                    default_width, default_height = w, h
        except Exception as e:
            print(f"Error restaurando tamaño ventana: {e}")
            
        self.set_default_size(default_width, default_height)
        self.set_title("Generar Embeddings de Covers")
        
        # Conectar señal de cierre para guardar tamaño
        self.connect("close-request", self.on_close_request)

        self.processing = False
        self.cancelled = False

        # Layout principal
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_content(main_box)

        # Header bar con ViewSwitcherTitle
        header = Adw.HeaderBar()
        self.view_switcher_title = Adw.ViewSwitcherTitle()
        header.set_title_widget(self.view_switcher_title)
        main_box.append(header)

        # Botón Reparar (inicialmente oculto)
        self.repair_button = Gtk.Button(label="Reparar Errores")
        self.repair_button.add_css_class("suggested-action")
        self.repair_button.set_visible(False)
        self.repair_button.connect("clicked", self.on_repair_clicked)
        header.pack_end(self.repair_button)

        # Botón cancelar
        self.cancel_button = Gtk.Button(label="Cancelar")
        self.cancel_button.add_css_class("destructive-action")
        self.cancel_button.connect("clicked", self.on_cancel_clicked)
        header.pack_end(self.cancel_button)

        # Variables de estado
        self.processing = False
        self.failed_covers = [] # Lista de covers fallidas para reintentar

        # View Stack
        self.view_stack = Adw.ViewStack()
        self.view_switcher_title.set_stack(self.view_stack)
        main_box.append(self.view_stack)

        # --- PAGINA 1: PROGRESO ---
        progress_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        progress_page.set_margin_top(12)
        progress_page.set_margin_bottom(12)
        progress_page.set_margin_start(12)
        progress_page.set_margin_end(12)
        
        progress_scroll = Gtk.ScrolledWindow()
        progress_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        progress_scroll.set_child(progress_page)
        
        self.view_stack.add_titled(progress_scroll, "progress", "Progreso")

        # Stats box
        stats_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        stats_box.set_homogeneous(True)
        progress_page.append(stats_box)

        # Stat cards
        self.total_label = self._create_stat_card("Total", "0")
        self.processed_label = self._create_stat_card("Procesadas", "0")
        self.skipped_label = self._create_stat_card("Omitidas", "0")
        self.errors_label = self._create_stat_card("Errores", "0")

        stats_box.append(self.total_label)
        stats_box.append(self.processed_label)
        stats_box.append(self.skipped_label)
        stats_box.append(self.errors_label)

        # Status label (feedback inmediato en tab de progreso)
        self.status_label = Gtk.Label(label="")
        self.status_label.add_css_class("dim-label")
        self.status_label.set_ellipsize(3) # Ellipsize END
        progress_page.append(self.status_label)

        # Progress bar
        progress_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        progress_page.append(progress_box)

        self.progress_label = Gtk.Label(label="Preparando...")
        self.progress_label.set_xalign(0)
        progress_box.append(self.progress_label)

        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        progress_box.append(self.progress_bar)

        # Imagen actual preview
        preview_frame = Gtk.Frame()
        preview_frame.set_margin_top(12)
        preview_frame.set_vexpand(True) # Expandir para llenar espacio
        progress_page.append(preview_frame)

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
        self.current_image.set_size_request(300, 450) # Más grande
        self.current_image.set_can_shrink(True)
        self.current_image.set_content_fit(3) # COVER
        preview_box.append(self.current_image)

        self.current_name_label = Gtk.Label(label="")
        self.current_name_label.set_xalign(0.5)
        self.current_name_label.set_wrap(True)
        self.current_name_label.set_justify(Gtk.Justification.CENTER)
        preview_box.append(self.current_name_label)
        
        # --- PAGINA 2: REGISTRO (LOG) ---
        log_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.view_stack.add_titled(log_page, "log", "Registro")

        # Log scrolled window (full size)
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        log_page.append(scrolled)

        self.log_view = Gtk.TextView()
        self.log_view.set_editable(False)
        self.log_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.log_view.set_monospace(True)
        self.log_view.set_top_margin(12)
        self.log_view.set_bottom_margin(12)
        self.log_view.set_left_margin(12)
        self.log_view.set_right_margin(12)
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
                        cover_path, 300, 450, True
                    )
                    texture = Gdk.Texture.new_for_pixbuf(pixbuf)
                    self.current_image.set_paintable(texture)
                    self.current_name_label.set_text(os.path.basename(cover_path))
                except Exception as e:
                    self.log(f"Error cargando preview: {e}")
                    self.status_label.set_text(f"Error preview: {str(e)[:50]}...")

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
        """Cancelar proceso o cerrar ventana"""
        if not self.processing:
            self.close()
            return

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
                    
                    # Info para logs
                    issue_info = ""
                    if cover.comic_info and cover.comic_info.volume:
                        issue_info = f"[{cover.comic_info.volume.nombre} #{cover.comic_info.numero}]"

                    # Verificar si existe
                    if "Comic_sin_caratula" in imagen_path:
                        self.log(f"⚠️ Omitido: Sin carátula {issue_info} (ID {cover.id_cover})")
                        skipped += 1
                        self.failed_covers.append(cover) # Agregar a fallidos para posible reparación
                        self.update_stats(total, processed, skipped, errors)
                        self.update_progress(i, total)
                        continue

                    if not os.path.exists(imagen_path):
                        self.log(f"⚠️ Omitido: Archivo no encontrado {issue_info}: {imagen_path}")
                        skipped += 1
                        self.failed_covers.append(cover)
                        self.update_stats(total, processed, skipped, errors)
                        self.update_progress(i, total)
                        continue

                    # Generar embedding
                    self.log(f"[{i}/{total}] {os.path.basename(imagen_path)}")
                    self.update_progress(i, total, imagen_path)

                    embedding = None
                    try:
                        embedding = emb_gen.generate_embedding(imagen_path)
                    except Exception as e:
                        self.log(f"  ⚠️ Error generando embedding {issue_info}: {e}")
                        
                        # Intentar recuperar la cover si falla
                        if self.recover_cover(cover, session):
                            self.log("  🔄 Reintentando generación...")
                            try:
                                # Recalcular ruta por si cambió
                                imagen_path = cover.obtener_ruta_local()
                                embedding = emb_gen.generate_embedding(imagen_path)
                            except Exception as e2:
                                self.log(f"  ❌ Falló reintento: {e2}")
                                embedding = None
                        else:
                            embedding = None

                    if embedding is not None:
                        cover.embedding = emb_gen.embedding_to_json(embedding)
                        processed += 1

                        # Commit por batches
                        if processed % batch_size == 0:
                            session.commit()
                            self.log(f"  ✓ Guardadas {processed} covers")
                    else:
                        errors += 1
                        self.log(f"  ❌ Error (irrecuperable) {issue_info}")
                        self.failed_covers.append(cover) # Agregar a fallidos

                    self.update_stats(total, processed, skipped, errors)

                except Exception as e:
                    errors += 1
                    self.log(f"  ❌ Error procesando item: {e}")
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

    def recover_cover(self, cover, session):
        """Intenta recuperar una cover dañada o faltante"""
        try:
            self.log(f"🚑 Intentando recuperar cover ID {cover.id_cover}...")
            
            # Verificar info asociada
            if not cover.comic_info:
                self.log("  ❌ No hay información de comic asociada")
                return False
                
            issue = cover.comic_info
            
            # Obtener API Key
            api_key = ""
            if hasattr(self.parent, 'config') and self.parent.config:
                api_key = self.parent.config.get_api_key()
                
            if not api_key:
                self.log("  ❌ No hay API Key configurada para redescargar")
                return False
                
            from helpers.comicvine_cliente import ComicVineClient
            from helpers.image_downloader import download_image
            from helpers.thumbnail_path import get_thumbnails_base_path
            
            client = ComicVineClient(api_key)
            image_url = None
            
            # Estrategia 1: Consultar ComicVine si hay ID
            if issue.comicvine_id:
                self.log(f"  🔄 Consultando ComicVine (Issue ID {issue.comicvine_id})...")
                try:
                    details = client.get_issue_details(issue.comicvine_id)
                    if details and 'image' in details:
                        image_url = details['image'].get('medium_url')
                except Exception as e:
                    self.log(f"  ⚠️ Error consultando API: {e}")
            
            # Estrategia 2: Usar URL existente si parece válida
            if not image_url and cover.url_imagen and cover.url_imagen.startswith('http'):
                image_url = cover.url_imagen
                self.log(f"  🔄 Usando URL existente: {image_url}")
                
            if not image_url:
                self.log("  ❌ No se pudo obtener una URL válida")
                return False
                
            # Preparar destino
            clean_vol_name = "".join([c if c.isalnum() or c.isspace() else "" for c in issue.volume.nombre]).strip()
            dest_folder = os.path.join(
                get_thumbnails_base_path(),
                "comicbook_info",
                f"{clean_vol_name}_{issue.volume.id_volume}"
            )
            
            # Determinar nombre de archivo
            filename = os.path.basename(cover.obtener_ruta_local())
            if "Comic_sin_caratula" in filename:
                filename = image_url.split('/')[-1]
                
            self.log(f"  ⬇️ Redescargando a: {filename}")
            
            # Descargar (forzando re-descarga al sobrescribir)
            path = download_image(image_url, dest_folder, filename, resize_height=400)
            
            if path and os.path.exists(path):
                self.log("  ✅ Recuperación exitosa")
                # Actualizar URL si cambió
                if cover.url_imagen != image_url:
                    cover.url_imagen = image_url
                    session.commit()
                return True
            else:
                self.log("  ❌ Falló la descarga de la imagen")
                return False
                
        except Exception as e:
            self.log(f"  ❌ Error en recuperación: {e}")
            return False

    def on_complete(self):
        """Proceso completado"""
        self.processing = False
        self.cancel_button.set_label("Cerrar")
        self.cancel_button.remove_css_class("destructive-action")
        self.cancel_button.set_sensitive(True)
        self.progress_label.set_text("Completado")
        self.progress_bar.set_fraction(1.0)
        
        # Mostrar botón de reparar si hubo fallos
        if self.failed_covers:
            self.log(f"\n⚠️ Se detectaron {len(self.failed_covers)} covers con problemas.")
            self.log("ℹ️ Puede intentar repararlas pulsando el botón 'Reparar Errores'.")
            self.repair_button.set_visible(True)

    def on_repair_clicked(self, button):
        """Maneja el clic en el botón de reparar"""
        if not self.failed_covers:
            return
            
        # Deshabilitar botones
        button.set_sensitive(False)
        self.cancel_button.set_sensitive(False)
        self.log("\n🔧 INICIANDO REPARACIÓN DE COVERS...")
        
        # Iniciar thread de reparación
        thread = threading.Thread(target=self.process_repairs)
        thread.daemon = True
        thread.start()

    @staticmethod
    def _repair_worker(task_data):
        """
        Worker estático para reparar una cover en background.
        Args:
            task_data (dict): Datos necesarios para la reparación (sin objetos SA)
        Returns:
            dict: Resultado de la operación
        """
        result = {
            'cover_id': task_data.get('cover_id'),
            'success': False,
            'new_url': None,
            'embedding_json': None,
            'log_messages': []
        }
        
        def log(msg):
            result['log_messages'].append(msg)

        try:
            cover_id = task_data.get('cover_id')
            comicvine_id = task_data.get('comicvine_id')
            current_url = task_data.get('current_url')
            volume_name = task_data.get('volume_name')
            volume_id = task_data.get('volume_id')
            current_path = task_data.get('current_path')
            api_key = task_data.get('api_key')
            
            # Imports locales para el worker
            from helpers.comicvine_cliente import ComicVineClient
            from helpers.image_downloader import download_image
            from helpers.thumbnail_path import get_thumbnails_base_path
            from helpers.embedding_generator import get_embedding_generator
            
            image_url = None
            
            # 1. Intentar obtener mejor URL desde ComicVine
            if comicvine_id and api_key:
                # log(f"  🔄 [ID {cover_id}] Consultando ComicVine...")
                try:
                    client = ComicVineClient(api_key)
                    details = client.get_issue_details(comicvine_id)
                    if details and 'image' in details:
                        image_url = details['image'].get('medium_url')
                except Exception as e:
                    log(f"  ⚠️ [ID {cover_id}] Error API: {e}")
            
            # 2. Fallback a URL existente
            if not image_url and current_url and current_url.startswith('http'):
                image_url = current_url
                
            if not image_url:
                log(f"  ❌ [ID {cover_id}] No se pudo obtener URL válida")
                return result
                
            # 3. Preparar destino
            clean_vol_name = "".join([c if c.isalnum() or c.isspace() else "" for c in volume_name]).strip()
            dest_folder = os.path.join(
                get_thumbnails_base_path(),
                "comicbook_info",
                f"{clean_vol_name}_{volume_id}"
            )
            
            # Determinar nombre de archivo
            filename = os.path.basename(current_path) if current_path else ""
            if not filename or "Comic_sin_caratula" in filename:
                filename = image_url.split('/')[-1]
                
            # 4. Descargar
            path = download_image(image_url, dest_folder, filename, resize_height=400)
            
            if path and os.path.exists(path):
                # 5. Generar embedding
                try:
                    emb_gen = get_embedding_generator()
                    embedding = emb_gen.generate_embedding(path)
                    
                    if embedding is not None:
                        result['embedding_json'] = emb_gen.embedding_to_json(embedding)
                        result['success'] = True
                        result['new_url'] = image_url
                        log(f"  ✅ [ID {cover_id}] Reparación exitosa")
                    else:
                        log(f"  ⚠️ [ID {cover_id}] Falló generación embedding")
                except Exception as e:
                    log(f"  ❌ [ID {cover_id}] Error generando embedding: {e}")
            else:
                log(f"  ❌ [ID {cover_id}] Falló descarga imagen")
                
        except Exception as e:
            log(f"  ❌ [ID {task_data.get('cover_id')}] Error worker: {e}")
            import traceback
            traceback.print_exc()
            
        return result

    def process_repairs(self):
        """Lógica de reparación en background (Paralelizada)"""
        try:
            # Conectar a BD (para lectura inicial y escritura final)
            db_path = os.path.join('data', 'babelcomics.db')
            engine = create_engine(f'sqlite:///{db_path}')
            Session = sessionmaker(bind=engine)
            session = Session()
            
            # Obtener API Key
            api_key = ""
            if hasattr(self.parent, 'config') and self.parent.config:
                api_key = self.parent.config.get_api_key()

            # Preparar tareas
            tasks = []
            
            # Reattach covers to session y extraer datos para workers
            active_covers_map = {} # {cover_id: cover_object}
            
            for fc in self.failed_covers:
                try:
                    c = session.merge(fc)
                    if c.comic_info and c.comic_info.volume:
                        active_covers_map[c.id_cover] = c
                        
                        # Datos para el worker (picklable)
                        task_data = {
                            'cover_id': c.id_cover,
                            'comicvine_id': c.comic_info.comicvine_id,
                            'current_url': c.url_imagen,
                            'volume_name': c.comic_info.volume.nombre,
                            'volume_id': c.comic_info.volume.id_volume,
                            'current_path': c.obtener_ruta_local(),
                            'api_key': api_key
                        }
                        tasks.append(task_data)
                except Exception as e:
                    print(f"Error preparando tarea reparacion: {e}")
            
            total = len(tasks)
            self.log(f"🔧 Iniciando reparación paralela de {total} covers (3 workers)...")
            
            repaired_count = 0
            processed_count = 0
            
            # Ejecutar con ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=3) as executor:
                future_to_cover = {executor.submit(self._repair_worker, task): task for task in tasks}
                
                for future in as_completed(future_to_cover):
                    if self.cancelled:
                        self.log("⚠️ Reparación cancelada por usuario.")
                        executor.shutdown(wait=False)
                        break
                        
                    task = future_to_cover[future]
                    cover_id = task['cover_id']
                    processed_count += 1
                    
                    try:
                        result = future.result()
                        
                        # Logging de logs del worker
                        for msg in result['log_messages']:
                            self.log(msg)
                            
                        # Actualizar en BD si fue exitoso
                        if result['success']:
                            cover = active_covers_map.get(cover_id)
                            if cover:
                                if result['new_url'] and cover.url_imagen != result['new_url']:
                                    cover.url_imagen = result['new_url']
                                
                                cover.embedding = result['embedding_json']
                                session.commit() # Commit parcial para ir guardando
                                repaired_count += 1
                                
                    except Exception as e:
                        self.log(f"❌ Error obteniendo resultado tarea {cover_id}: {e}")

            session.close()
            
            self.log("")
            self.log("="*60)
            self.log("✅ FIN DE REPARACIÓN")
            self.log(f"   Recuperadas: {repaired_count}/{total}")
            self.log("="*60)
            
            if repaired_count == total:
                self.failed_covers = []
            
        except Exception as e:
            self.log(f"❌ ERROR GENERAL EN REPARACIÓN: {e}")
            import traceback
            self.log(traceback.format_exc())
        
        finally:
            GLib.idle_add(self.on_repair_complete)

    def on_repair_complete(self):
        """Fin de reparación"""
        self.cancel_button.set_sensitive(True)
        self.repair_button.set_sensitive(True) 
        if not self.failed_covers: # Si vaciamos la lista
             self.repair_button.set_visible(False)
        return False

    def on_close_request(self, *args):
        """Guardar tamaño al cerrar"""
        try:
            if hasattr(self.parent, 'config') and self.parent.config:
                width = self.get_width()
                height = self.get_height()
                
                # Obtener estado actual
                current_state = {}
                if self.parent.config.window_state:
                    try:
                        current_state = json.loads(self.parent.config.window_state)
                    except:
                        pass
                
                # Actualizar
                current_state['embeddings_window'] = [width, height]
                self.parent.config.window_state = json.dumps(current_state)
                
                # Guardar en BD
                if hasattr(self.parent, 'session') and self.parent.session:
                    self.parent.session.commit()
                    print(f"Tamaño ventana embeddings guardado: {width}x{height}")
        except Exception as e:
            print(f"Error guardando tamaño ventana: {e}")
            
        return False # Propagar evento de cierre
