#!/usr/bin/env python3
"""
thumbnail_generator.py - Generador de thumbnails para archivos de comics
"""

import os
import threading
import queue
from pathlib import Path
from gi.repository import GdkPixbuf, GLib


class ThumbnailGenerator:
    """
    Generador de thumbnails para archivos CBZ/CBR y otros formatos de imagen.
    
    Características:
    - Soporte para CBZ (ZIP) y CBR (RAR)
    - Cache de thumbnails reales (no placeholders)
    - Worker thread para no bloquear UI
    - Extracción de primera página de comics
    """
    
    def __init__(self, cache_dir="data/thumbnails"):
        # Configuración de rutas
        self.cache_dir = Path(cache_dir)
        self._create_cache_directories()
        
        # Queue y worker thread
        self.thumbnail_queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        
        # Verificar dependencias
        self._check_dependencies()
        
        # Iniciar worker
        self.worker_thread.start()
        print("ThumbnailGenerator iniciado")
        
    def _create_cache_directories(self):
        """Crear directorios de cache"""
        subdirs = ["comics", "volumes", "publishers", "arcs"]
        for subdir in subdirs:
            (self.cache_dir / subdir).mkdir(parents=True, exist_ok=True)
            
    def _check_dependencies(self):
        """Verificar dependencias opcionales"""
        # Verificar rarfile para CBR
        self.has_rarfile = True
        try:
            import rarfile
            self.rarfile = rarfile
            print("rarfile disponible - soporte CBR activado")
        except ImportError:
            self.has_rarfile = False
            print("rarfile no disponible - solo soporte CBZ")
            print("Instalar con: pip install rarfile")
            
        # Verificar zipfile (debería estar siempre)
        try:
            import zipfile
            self.zipfile = zipfile
            print("zipfile disponible - soporte CBZ activado")
        except ImportError:
            print("ERROR: zipfile no disponible")
            
    def request_thumbnail(self, item_path, item_id, item_type, callback):
        """
        Solicitar generación de thumbnail
        
        Args:
            item_path: Ruta al archivo fuente
            item_id: ID único del item
            item_type: Tipo de item ("comics", "volumes", "publishers")
            callback: Función a llamar con el resultado
        """
        request = {
            'item_path': item_path,
            'item_id': item_id,
            'item_type': item_type,
            'callback': callback
        }
        self.thumbnail_queue.put(request)
        
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
            print(f"Cache limpiado para {item_type} {item_id}")
            
    def clear_all_cache(self):
        """Limpiar todo el cache"""
        import shutil
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self._create_cache_directories()
            print("Cache completo limpiado")
            
    def _worker(self):
        """Worker thread para procesar solicitudes"""
        while True:
            try:
                request = self.thumbnail_queue.get(timeout=1)
                self._process_thumbnail_request(request)
                self.thumbnail_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error en worker de thumbnails: {e}")
                import traceback
                traceback.print_exc()
                
    def _process_thumbnail_request(self, request):
        """Procesar una solicitud de thumbnail"""
        item_path = request['item_path']
        item_id = request['item_id']
        item_type = request['item_type']
        callback = request['callback']
        
        print(f"Procesando thumbnail: {item_type} ID:{item_id}")
        
        # Verificar cache existente
        thumbnail_path = self.get_cached_thumbnail_path(item_id, item_type)
        if thumbnail_path.exists():
            print(f"Cache hit: {thumbnail_path}")
            GLib.idle_add(callback, str(thumbnail_path))
            return
            
        # Intentar generar thumbnail
        success = self._generate_thumbnail(item_path, thumbnail_path, item_type)
        
        if success:
            print(f"Thumbnail generado: {thumbnail_path}")
            GLib.idle_add(callback, str(thumbnail_path))
        else:
            # No se pudo generar - dejar que el modelo maneje placeholder
            print(f"No se pudo generar thumbnail para {item_type} {item_id}")
            GLib.idle_add(callback, None)
            
    def _generate_thumbnail(self, source_path, target_path, item_type):
        """Generar thumbnail según el tipo de archivo"""
        if not source_path or not os.path.exists(source_path):
            return False
            
        try:
            if item_type == "comics":
                return self._generate_comic_thumbnail(source_path, target_path)
            else:
                return self._generate_image_thumbnail(source_path, target_path)
        except Exception as e:
            print(f"Error generando thumbnail: {e}")
            return False
            
    def _generate_comic_thumbnail(self, comic_path, thumbnail_path):
        """Generar thumbnail desde archivo de comic"""
        extension = comic_path.lower()
        
        if extension.endswith('.cbz'):
            return self._extract_from_cbz(comic_path, thumbnail_path)
        elif extension.endswith('.cbr'):
            if self.has_rarfile:
                return self._extract_from_cbr(comic_path, thumbnail_path)
            else:
                print("CBR no soportado - falta rarfile")
                return False
        elif extension.endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp')):
            return self._generate_image_thumbnail(comic_path, thumbnail_path)
        else:
            print(f"Formato no soportado: {comic_path}")
            return False
            
    def _extract_from_cbz(self, cbz_path, thumbnail_path):
        """Extraer primera imagen de archivo CBZ (ZIP)"""
        try:
            with self.zipfile.ZipFile(cbz_path, 'r') as zip_file:
                # Encontrar archivos de imagen
                image_files = [
                    f for f in zip_file.namelist()
                    if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp'))
                    and not f.startswith('__MACOSX')
                    and '/' not in f.split('/')[-1][:1]  # Evitar archivos ocultos
                ]
                
                if not image_files:
                    print(f"No se encontraron imágenes en {cbz_path}")
                    return False
                    
                # Ordenar y tomar la primera
                image_files.sort()
                first_image = image_files[0]
                print(f"Extrayendo: {first_image}")
                
                # Leer imagen a memoria
                with zip_file.open(first_image) as img_file:
                    image_data = img_file.read()
                    
                # Crear pixbuf desde datos en memoria
                loader = GdkPixbuf.PixbufLoader()
                loader.write(image_data)
                loader.close()
                
                pixbuf = loader.get_pixbuf()
                if pixbuf:
                    return self._save_resized_thumbnail(pixbuf, thumbnail_path)
                else:
                    print("No se pudo crear pixbuf desde imagen")
                    return False
                    
        except Exception as e:
            print(f"Error extrayendo CBZ {cbz_path}: {e}")
            return False
            
    def _extract_from_cbr(self, cbr_path, thumbnail_path):
        """Extraer primera imagen de archivo CBR (RAR)"""
        try:
            if not self.rarfile.is_rarfile(cbr_path):
                print(f"Archivo no es RAR válido: {cbr_path}")
                return False
                
            with self.rarfile.RarFile(cbr_path, 'r') as rar_file:
                # Encontrar archivos de imagen
                image_files = [
                    f for f in rar_file.namelist()
                    if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp'))
                ]
                
                if not image_files:
                    print(f"No se encontraron imágenes en {cbr_path}")
                    return False
                    
                # Ordenar y tomar la primera
                image_files.sort()
                first_image = image_files[0]
                print(f"Extrayendo: {first_image}")
                
                # Leer imagen a memoria
                image_data = rar_file.read(first_image)
                    
                # Crear pixbuf desde datos
                loader = GdkPixbuf.PixbufLoader()
                loader.write(image_data)
                loader.close()
                
                pixbuf = loader.get_pixbuf()
                if pixbuf:
                    return self._save_resized_thumbnail(pixbuf, thumbnail_path)
                else:
                    print("No se pudo crear pixbuf desde imagen")
                    return False
                    
        except Exception as e:
            print(f"Error extrayendo CBR {cbr_path}: {e}")
            return False
            
    def _generate_image_thumbnail(self, image_path, thumbnail_path):
        """Generar thumbnail desde imagen directa"""
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(image_path)
            return self._save_resized_thumbnail(pixbuf, thumbnail_path)
        except Exception as e:
            print(f"Error cargando imagen {image_path}: {e}")
            return False
            
    def _save_resized_thumbnail(self, pixbuf, thumbnail_path):
        """Redimensionar y guardar pixbuf como thumbnail"""
        try:
            # Obtener dimensiones originales
            original_width = pixbuf.get_width()
            original_height = pixbuf.get_height()
            
            # Calcular nuevas dimensiones manteniendo proporción
            target_width = 280
            if original_width > target_width:
                scale_factor = target_width / original_width
                new_height = int(original_height * scale_factor)
                
                # Redimensionar
                pixbuf = pixbuf.scale_simple(
                    target_width, 
                    new_height, 
                    GdkPixbuf.InterpType.BILINEAR
                )
                print(f"Redimensionado a: {target_width}x{new_height}")
            
            # Asegurar que el directorio existe
            thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Guardar como JPEG
            pixbuf.savev(str(thumbnail_path), "jpeg", ["quality"], ["85"])
            print(f"Thumbnail guardado: {thumbnail_path}")
            
            return True
            
        except Exception as e:
            print(f"Error guardando thumbnail: {e}")
            return False
            
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
        
    def debug_comic_file(self, comic_path):
        """Debug de un archivo de comic específico"""
        print(f"\n=== DEBUG COMIC FILE ===")
        print(f"Archivo: {comic_path}")
        print(f"Existe: {os.path.exists(comic_path)}")
        
        if not os.path.exists(comic_path):
            return
            
        print(f"Tamaño: {os.path.getsize(comic_path):,} bytes")
        
        if comic_path.lower().endswith('.cbz'):
            self._debug_cbz(comic_path)
        elif comic_path.lower().endswith('.cbr'):
            self._debug_cbr(comic_path)
        else:
            print(f"Tipo: Imagen directa")
            
    def _debug_cbz(self, cbz_path):
        """Debug específico para CBZ"""
        try:
            with self.zipfile.ZipFile(cbz_path, 'r') as zf:
                all_files = zf.namelist()
                image_files = [
                    f for f in all_files 
                    if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp'))
                ]
                
                print(f"Archivos totales en CBZ: {len(all_files)}")
                print(f"Archivos de imagen: {len(image_files)}")
                
                if image_files:
                    sorted_images = sorted(image_files)
                    print(f"Primera imagen: {sorted_images[0]}")
                    print(f"Última imagen: {sorted_images[-1]}")
                    
                    # Mostrar algunas imágenes
                    print("Primeras 5 imágenes:")
                    for img in sorted_images[:5]:
                        print(f"  - {img}")
                        
        except Exception as e:
            print(f"Error analizando CBZ: {e}")
            
    def _debug_cbr(self, cbr_path):
        """Debug específico para CBR"""
        if not self.has_rarfile:
            print("rarfile no disponible - no se puede analizar CBR")
            return
            
        try:
            with self.rarfile.RarFile(cbr_path, 'r') as rf:
                all_files = rf.namelist()
                image_files = [
                    f for f in all_files 
                    if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp'))
                ]
                
                print(f"Archivos totales en CBR: {len(all_files)}")
                print(f"Archivos de imagen: {len(image_files)}")
                
                if image_files:
                    sorted_images = sorted(image_files)
                    print(f"Primera imagen: {sorted_images[0]}")
                    print(f"Última imagen: {sorted_images[-1]}")
                    
        except Exception as e:
            print(f"Error analizando CBR: {e}")


# Función de utilidad para instalar dependencias
def install_rarfile_instructions():
    """Mostrar instrucciones para instalar rarfile"""
    print("\n=== INSTALAR SOPORTE CBR ===")
    print("Para soporte completo de archivos CBR:")
    print("1. pip install rarfile")
    print("2. Instalar unrar:")
    print("   - Ubuntu/Debian: sudo apt install unrar")
    print("   - Fedora: sudo dnf install unrar")
    print("   - macOS: brew install unrar")
    print("   - Windows: descargar desde rarlab.com")


if __name__ == "__main__":
    # Test básico del módulo
    print("Probando ThumbnailGenerator...")
    
    generator = ThumbnailGenerator()
    stats = generator.get_stats()
    print(f"Estadísticas del cache: {stats}")
    
    # Mostrar instrucciones si falta rarfile
    if not generator.has_rarfile:
        install_rarfile_instructions()