#!/usr/bin/env python3
"""
thumbnail_generator.py - Generador de thumbnails para archivos de comics (Optimizado con Multiprocessing)
"""

import os
import threading
import concurrent.futures
from pathlib import Path
from gi.repository import GLib

# Importar worker
try:
    from thumbnail_worker import generate_thumbnail_task
    WORKER_AVAILABLE = True
except ImportError:
    WORKER_AVAILABLE = False
    print("Error importando thumbnail_worker.py")

class ThumbnailGenerator:
    """
    Generador de thumbnails usando ProcessPoolExecutor para no bloquear la UI.
    """
    
    def __init__(self, cache_dir=None):
        # Configuración de rutas
        if cache_dir is None:
            from helpers.thumbnail_path import get_thumbnails_base_path
            cache_dir = get_thumbnails_base_path()
        self.cache_dir = Path(cache_dir)
        self._create_cache_directories()

        # Executor para multiprocessing
        # Max workers = número de CPUs (o un límite razonable)
        max_workers = min(os.cpu_count() or 4, 8)
        self.executor = concurrent.futures.ProcessPoolExecutor(max_workers=max_workers)
        print(f"ThumbnailGenerator iniciado con {max_workers} procesos")
        
        # Mantener sesión de BD para smart covers
        self.session = None

    def set_session(self, session):
        """Configurar sesión de base de datos para lógica inteligente"""
        self.session = session
        
    def _create_cache_directories(self):
        """Crear directorios de cache"""
        subdirs = ["comics", "volumes", "publishers", "comicbook_info"]
        for subdir in subdirs:
            (self.cache_dir / subdir).mkdir(parents=True, exist_ok=True)
            
    def request_thumbnail(self, item_path, item_id, item_type, callback):
        """
        Solicitar generación de thumbnail
        """
        # Verificar cache existente primero
        thumbnail_path = self.get_cached_thumbnail_path(item_id, item_type)
        if thumbnail_path.exists():
            # print(f"Cache hit: {thumbnail_path}")
            GLib.idle_add(callback, str(thumbnail_path))
            return
            
        if not WORKER_AVAILABLE:
            print("Worker no disponible")
            GLib.idle_add(callback, None)
            return

        # Resolver info de Smart Cover (solo para comics)
        cover_info = None
        if item_type == "comics" and self.session:
            cover_info = self._resolve_smart_cover_metadata(item_id, item_path)
            
        # Enviar tarea al pool
        future = self.executor.submit(
            generate_thumbnail_task, 
            str(item_path), 
            str(thumbnail_path), 
            cover_info
        )
        
        # Configurar callback cuando termine
        future.add_done_callback(
            lambda f: self._on_thumbnail_generated(f, callback, str(thumbnail_path))
        )
        
    def _on_thumbnail_generated(self, future, callback, result_path):
        """Manejar resultado del worker"""
        try:
            success, result = future.result()
            if success:
                # print(f"Thumbnail generado: {result}")
                GLib.idle_add(callback, result)
            else:
                # print(f"Fallo generando thumbnail: {result}")
                GLib.idle_add(callback, None)
        except Exception as e:
            print(f"Excepción en worker: {e}")
            GLib.idle_add(callback, None)
        
    def get_cached_thumbnail_path(self, item_id, item_type):
        """Obtener ruta del thumbnail en caché"""
        return self.cache_dir / item_type / f"{item_id}.jpg"
        
    def has_cached_thumbnail(self, item_id, item_type):
        """Verificar si existe thumbnail en caché"""
        return self.get_cached_thumbnail_path(item_id, item_type).exists()
        
    def clear_cache_for_item(self, item_id, item_type):
        """Limpiar cache para un item específico"""
        thumbnail_path = self.get_cached_thumbnail_path(item_id, item_type)
        if thumbnail_path.exists():
            thumbnail_path.unlink()
            
    def clear_all_cache(self):
        """Limpiar todo el cache"""
        import shutil
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self._create_cache_directories()
            
    def get_stats(self):
        """Obtener estadísticas del cache"""
        stats = {}
        for subdir in ["comics", "volumes", "publishers"]:
            cache_subdir = self.cache_dir / subdir
            if cache_subdir.exists():
                count = len(list(cache_subdir.glob("*.jpg")))
                stats[subdir] = count
            else:
                stats[subdir] = 0
        return stats

    def _resolve_smart_cover_metadata(self, comic_id, comic_path):
        """
        Resolver metadatos de cover inteligente (DB query) en el proceso principal.
        Retorna dict {'page_name': str, 'page_order': int} o None
        """
        if not self.session:
            return None
            
        try:
            # Importar aquí para evitar ciclos
            from entidades.comicbook_detail_model import Comicbook_Detail
            
            # 1. Buscar marcado explícito
            cover_page = self.session.query(Comicbook_Detail).filter(
                Comicbook_Detail.comicbook_id == comic_id,
                Comicbook_Detail.tipoPagina == 1
            ).first()
            
            if cover_page:
                return {'page_name': cover_page.nombre_pagina, 'page_order': cover_page.ordenPagina}
                
            # 2. Buscar por nombre
            cover_by_name = self.session.query(Comicbook_Detail).filter(
                Comicbook_Detail.comicbook_id == comic_id
            ).filter(
                Comicbook_Detail.nombre_pagina.ilike('cover.%') |
                Comicbook_Detail.nombre_pagina.ilike('portada.%') |
                Comicbook_Detail.nombre_pagina.ilike('caratula.%')
            ).first()
            
            if cover_by_name:
                # Actualizar DB
                cover_by_name.tipoPagina = 1
                self.session.commit()
                return {'page_name': cover_by_name.nombre_pagina, 'page_order': cover_by_name.ordenPagina}
                
            # 3. Primera página (si hay detalles)
            first_page = self.session.query(Comicbook_Detail).filter(
                Comicbook_Detail.comicbook_id == comic_id
            ).order_by(Comicbook_Detail.ordenPagina).first()
            
            if first_page:
                first_page.tipoPagina = 1
                self.session.commit()
                return {'page_name': first_page.nombre_pagina, 'page_order': first_page.ordenPagina}
                
        except Exception as e:
            print(f"Error resolviendo smart cover: {e}")
            if self.session:
                self.session.rollback()
                
        return None

    def shutdown(self):
        """Cerrar el pool de procesos"""
        self.executor.shutdown(wait=False)

if __name__ == "__main__":
    print("Probando ThumbnailGenerator con Multiprocessing...")
    gen = ThumbnailGenerator()
    print(f"Stats: {gen.get_stats()}")
    gen.shutdown()