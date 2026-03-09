"""
Download Manager to handle queueing and processing of volume downloads centrally.
Emits GObject signals so the UI can update decoupling logic from presentation.
"""
import gi
import threading
import queue

gi.require_version('Gtk', '4.0')
from gi.repository import GObject, GLib

class DownloadManager(GObject.GObject):
    """Gestor central de descargas"""
    
    __gsignals__ = {
        'download-added': (GObject.SignalFlags.RUN_FIRST, None, (str,)), # volume_cv_id
        'download-progress': (GObject.SignalFlags.RUN_FIRST, None, (str, float, str)), # volume_cv_id, fraction, message
        'download-completed': (GObject.SignalFlags.RUN_FIRST, None, (str,)), # volume_cv_id
        'download-error': (GObject.SignalFlags.RUN_FIRST, None, (str, str)), # volume_cv_id, error_msg
        'download-removed': (GObject.SignalFlags.RUN_FIRST, None, (str,)), # volume_cv_id
    }

    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = DownloadManager()
        return cls._instance

    def __init__(self):
        super().__init__()
        self.download_queue = queue.Queue()
        self.active_downloads = {} # volume_cv_id -> metadata { title, total_issues, current_progress }
        self.is_running = False
        self.worker_thread = None
        self.main_session = None  # Sesión para el main thread
        self.engine = None        # Engine para sesiones en background

    def set_main_session(self, session):
        self.main_session = session

    def set_engine(self, engine):
        self.engine = engine

    def add_download(self, volume_data, comicvine_client, download_covers):
        """Añade un volumen a la cola de descargas"""
        volume_cv_id = str(volume_data.get('id', ''))
        if not volume_cv_id:
            return

        if volume_cv_id in self.active_downloads:
            return  # Ya está en proceso

        # Inicializamos en estado queued
        self.active_downloads[volume_cv_id] = {
            'volume_data': volume_data,
            'title': volume_data.get('name', 'Desconocido'),
            'total_issues': volume_data.get('count_of_issues', 0),
            'progress': 0.0,
            'message': 'En cola...',
            'comicvine_client': comicvine_client,
            'download_covers': download_covers,
            'status': 'queued' # queued, downloading, completed, error
        }
        
        # Emitir al UI
        GLib.idle_add(lambda: self.emit('download-added', volume_cv_id))
        
        self.download_queue.put(volume_cv_id)
        self._start_worker_if_needed()

    def remove_download(self, volume_cv_id):
        """Elimina una descarga completada o con error de la cola activa."""
        if volume_cv_id in self.active_downloads:
            dl_info = self.active_downloads[volume_cv_id]
            if dl_info['status'] in ['completed', 'error']:
                del self.active_downloads[volume_cv_id]
                GLib.idle_add(lambda: self.emit('download-removed', volume_cv_id))
                return True
        return False

    def retry_download(self, volume_cv_id):
        """Vuelve a encolar una descarga que falló."""
        if volume_cv_id in self.active_downloads:
            dl_info = self.active_downloads[volume_cv_id]
            if dl_info['status'] == 'error':
                print(f"Reintentando descarga para {volume_cv_id}...")
                dl_info['status'] = 'queued'
                dl_info['message'] = 'Reintentando...'
                dl_info['progress'] = 0.0
                
                # Emitir al UI
                GLib.idle_add(lambda: self.emit('download-progress', volume_cv_id, 0.0, 'Reintentando...'))
                
                self.download_queue.put(volume_cv_id)
                self._start_worker_if_needed()
                return True
        return False

    def _start_worker_if_needed(self):
        if not self.is_running:
            self.is_running = True
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()

    def _worker_loop(self):
        while self.is_running:
            try:
                # Esperar nueva descarga con un timeout para poder evaluar is_running
                volume_cv_id = self.download_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            dl_info = self.active_downloads.get(volume_cv_id)
            if not dl_info:
                self.download_queue.task_done()
                continue
                
            dl_info['status'] = 'downloading'
            dl_info['message'] = 'Iniciando descarga...'
            GLib.idle_add(lambda cv=volume_cv_id: self.emit('download-progress', cv, 0.0, 'Iniciando descarga...'))

            try:
                self._process_download(volume_cv_id, dl_info)
                dl_info['status'] = 'completed'
                dl_info['progress'] = 1.0
                dl_info['message'] = '¡Completado!'
                GLib.idle_add(lambda cv=volume_cv_id: self.emit('download-completed', cv))
            except Exception as e:
                print(f"Error procesando descarga para {volume_cv_id}: {e}")
                dl_info['status'] = 'error'
                dl_info['message'] = f'Error: {e}'
                GLib.idle_add(lambda cv=volume_cv_id, err=str(e): self.emit('download-error', cv, err))
            finally:
                self.download_queue.task_done()

        self.is_running = False

    def _process_download(self, volume_cv_id, dl_info):
        """Delega a VolumeRepository, pasándole el callback de progreso"""
        from repositories.volume_repository import VolumeRepository
        from sqlalchemy.orm import sessionmaker
        
        if not self.engine:
            raise ValueError("No database engine set for DownloadManager")

        # Crear sesión específica para este worker thread
        Session = sessionmaker(bind=self.engine)
        bg_session = Session()

        try:
            volume_repo = VolumeRepository(bg_session)
            
            def progress_callback(message, fraction=None):
                if fraction is not None:
                    dl_info['progress'] = fraction
                dl_info['message'] = message
                
                # Emitir para la UI (en el hilo principal)
                GLib.idle_add(lambda cv=volume_cv_id, frac=dl_info['progress'], msg=message: 
                        self.emit('download-progress', cv, frac, msg))

            def result_callback(result):
                # Callback seguro para guardado en DB desde hilo secundario de covers
                from entidades.comicbook_info_model import ComicbookInfo
                from entidades.comicbook_info_cover_model import ComicbookInfoCover
                def _update_db_in_main_thread():
                    if not self.main_session: return False
                    try:
                        issue_num = result.get('issue_number')
                        results_list = result.get('results', [])
                        if not results_list: return False
                        
                        from entidades.volume_model import Volume
                        vol = self.main_session.query(Volume).filter_by(id_comicvine=volume_cv_id).first()
                        if not vol: return False
                        
                        comic_info = self.main_session.query(ComicbookInfo).filter(
                            ComicbookInfo.id_volume == vol.id_volume,
                            ComicbookInfo.numero == str(issue_num)
                        ).first()
                        
                        if not comic_info: return False

                        changes_made = False
                        for item in results_list:
                            url = item.get('url')
                            embedding_json = item.get('embedding')
                            
                            cover_record = next((c for c in comic_info.portadas if c.url_imagen == url), None)
                            if not cover_record:
                                cover_record = ComicbookInfoCover(
                                    id_comicbook_info=comic_info.id_comicbook_info,
                                    url_imagen=url
                                )
                                self.main_session.add(cover_record)
                                comic_info.portadas.append(cover_record)
                                changes_made = True
                            
                            if embedding_json and cover_record.embedding != embedding_json:
                                cover_record.embedding = embedding_json
                                changes_made = True
                                    
                        if changes_made:
                            self.main_session.commit()
                    except Exception as e:
                        print(f"Error guardando cover en DM callback: {e}")
                        self.main_session.rollback()
                    return False
                GLib.idle_add(_update_db_in_main_thread)

            volume_repo.download_complete_volume_data(
                volume_data=dl_info['volume_data'],
                comicvine_client=dl_info['comicvine_client'],
                download_covers=dl_info['download_covers'],
                progress_callback=progress_callback,
                result_callback=result_callback
            )
            # Aseguramos commit final por si acaso
            bg_session.commit()
            
        except Exception as e:
            bg_session.rollback()
            raise e
        finally:
            bg_session.close()
