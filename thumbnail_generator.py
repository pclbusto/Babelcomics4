#!/usr/bin/env python3
"""
thumbnail_generator.py - Generador de thumbnails para archivos de comics
"""

import os
import threading
import queue
from pathlib import Path
from gi.repository import GdkPixbuf, GLib
from helpers.comic_extractor import ComicExtractor


class ThumbnailGenerator:
    """
    Generador de thumbnails para archivos CBZ/CBR y otros formatos de imagen.
    
    Características:
    - Soporte para CBZ (ZIP) y CBR (RAR)
    - Cache de thumbnails reales (no placeholders)
    - Worker thread para no bloquear UI
    - Extracción de primera página de comics
    """
    
    def __init__(self, cache_dir=None):
        # Configuración de rutas
        if cache_dir is None:
            from helpers.thumbnail_path import get_thumbnails_base_path
            cache_dir = get_thumbnails_base_path()
        self.cache_dir = Path(cache_dir)
        self._create_cache_directories()

        # Queue y worker thread
        self.thumbnail_queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)

        # Extractor de comics compartido (usa la lógica unificada)
        self.comic_extractor = ComicExtractor()

        # Verificar dependencias
        self._check_dependencies()

        # Iniciar worker
        self.worker_thread.start()
        print("ThumbnailGenerator iniciado")
        
    def _create_cache_directories(self):
        """Crear directorios de cache"""
        subdirs = ["comics", "volumes", "publishers", "comicbook_info"]
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
        success = self._generate_thumbnail(item_path, thumbnail_path, item_type, item_id)
        
        if success:
            print(f"Thumbnail generado: {thumbnail_path}")
            GLib.idle_add(callback, str(thumbnail_path))
        else:
            # No se pudo generar - dejar que el modelo maneje placeholder
            print(f"No se pudo generar thumbnail para {item_type} {item_id}")
            GLib.idle_add(callback, None)
            
    def _generate_thumbnail(self, source_path, target_path, item_type, item_id=None):
        """Generar thumbnail según el tipo de archivo"""
        if not source_path or not os.path.exists(source_path):
            return False

        try:
            if item_type == "comics":
                return self._generate_comic_thumbnail(source_path, target_path, item_id)
            else:
                return self._generate_image_thumbnail(source_path, target_path)
        except Exception as e:
            print(f"Error generando thumbnail: {e}")
            return False
            
    def _generate_comic_thumbnail(self, comic_path, thumbnail_path, comic_id=None):
        """Generar thumbnail desde archivo de comic con lógica inteligente de cover"""
        # Si tenemos comic_id, intentar usar la lógica inteligente de cover
        if comic_id and hasattr(self, 'session') and self.session:
            try:
                cover_image_path = self._find_smart_cover_image(comic_id, comic_path)
                if cover_image_path and cover_image_path != comic_path:
                    # Usar imagen específica de cover
                    success = self._generate_image_thumbnail(cover_image_path, thumbnail_path)
                    # Limpiar archivo temporal si fue extraído
                    self._cleanup_temp_file(cover_image_path)
                    return success
            except Exception as e:
                print(f"Error con lógica inteligente de cover, usando método normal: {e}")

        # Usar ComicExtractor para detectar formato real (por magic bytes)
        comic_format = self.comic_extractor.detect_comic_format(comic_path)

        if not comic_format:
            # Si no es un comic, verificar si es imagen directa
            extension = comic_path.lower()
            if extension.endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp')):
                return self._generate_image_thumbnail(comic_path, thumbnail_path)
            print(f"Formato no soportado: {comic_path}")
            return False

        # Extraer según el formato REAL detectado
        if comic_format == 'zip':
            return self._extract_from_cbz(comic_path, thumbnail_path)
        elif comic_format == 'rar':
            if self.has_rarfile:
                return self._extract_from_cbr(comic_path, thumbnail_path)
            else:
                print("CBR no soportado - falta rarfile")
                return False
        elif comic_format == '7z':
            print("Formato 7z detectado - extracción no implementada en ThumbnailGenerator")
            return False
        else:
            print(f"Formato no soportado: {comic_format}")
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

    def _find_smart_cover_image(self, comic_id, comic_path):
        """
        Encontrar imagen de cover inteligentemente:
        1. PRIORIDAD MÁXIMA: Página marcada manualmente (tipoPagina=1)
        2. Si no hay marcada: Buscar por nombre (cover/portada/caratula) y marcarla
        3. Último recurso: Primera imagen en orden y marcarla
        """
        try:
            print(f"\n🔍 SMART COVER SEARCH para comic {comic_id}")
            print(f"Archivo: {comic_path}")

            if not hasattr(self, 'session') or not self.session:
                print("❌ No hay sesión de BD, usando extracción directa")
                return self._extract_first_page_from_comic_file(comic_path)

            # Importar dentro del método para evitar dependencias circulares
            from entidades.comicbook_detail_model import Comicbook_Detail

            # Contar total de páginas para este comic
            total_pages = self.session.query(Comicbook_Detail).filter(
                Comicbook_Detail.comicbook_id == comic_id
            ).count()
            print(f"📄 Total páginas en BD: {total_pages}")

            # PRIORIDAD 1: Buscar página marcada como cover (tipoPagina=1)
            cover_page = self.session.query(Comicbook_Detail).filter(
                Comicbook_Detail.comicbook_id == comic_id,
                Comicbook_Detail.tipoPagina == 1  # COVER
            ).first()

            if cover_page:
                print(f"✅ COVER MARCADO encontrado: {cover_page.nombre_pagina} (tipoPagina={cover_page.tipoPagina})")
                print(f"📄 Orden de página: {cover_page.ordenPagina}")

                # Extraer esa página específica del archivo original (por nombre primero)
                extracted_cover = self._extract_specific_page_from_comic(
                    comic_path,
                    cover_page.ordenPagina,
                    page_name=cover_page.nombre_pagina
                )
                if extracted_cover:
                    print(f"🎯 USANDO COVER MARCADO: {extracted_cover}")
                    return extracted_cover
                else:
                    print(f"⚠️ Error extrayendo cover marcado, continuando con fallbacks...")

            # PRIORIDAD 2: Buscar por nombre (cover, portada, caratula) y marcar
            print(f"❌ No hay página marcada como COVER, buscando por nombre...")
            cover_by_name = self.session.query(Comicbook_Detail).filter(
                Comicbook_Detail.comicbook_id == comic_id
            ).filter(
                Comicbook_Detail.nombre_pagina.ilike('cover.%') |
                Comicbook_Detail.nombre_pagina.ilike('portada.%') |
                Comicbook_Detail.nombre_pagina.ilike('caratula.%')
            ).first()

            if cover_by_name:
                print(f"🎯 COVER ENCONTRADO POR NOMBRE: {cover_by_name.nombre_pagina}")
                print(f"📄 Orden de página: {cover_by_name.ordenPagina}")

                # Marcar como cover automáticamente
                print(f"📌 Marcando automáticamente como cover...")
                cover_by_name.tipoPagina = 1
                self.session.commit()
                print(f"✅ Página marcada como cover en BD")

                # Extraer esa página específica del archivo original (por nombre primero)
                extracted_cover = self._extract_specific_page_from_comic(
                    comic_path,
                    cover_by_name.ordenPagina,
                    page_name=cover_by_name.nombre_pagina
                )
                if extracted_cover:
                    print(f"✅ USANDO COVER POR NOMBRE: {extracted_cover}")
                    return extracted_cover
                else:
                    print(f"⚠️ Error extrayendo cover por nombre, usando primera página...")

            # PRIORIDAD 3: Primera página en orden lexicográfico y marcar
            print(f"📦 Usando primera página en orden lexicográfico...")
            first_page = self.session.query(Comicbook_Detail).filter(
                Comicbook_Detail.comicbook_id == comic_id
            ).order_by(Comicbook_Detail.ordenPagina).first()

            if first_page:
                print(f"🎯 PRIMERA PÁGINA: {first_page.nombre_pagina}")
                print(f"📄 Orden: {first_page.ordenPagina}")

                # Marcar como cover automáticamente
                print(f"📌 Marcando primera página como cover...")
                first_page.tipoPagina = 1
                self.session.commit()
                print(f"✅ Página marcada como cover en BD")

                # Extraer esa página específica (por nombre primero)
                extracted_cover = self._extract_specific_page_from_comic(
                    comic_path,
                    first_page.ordenPagina,
                    page_name=first_page.nombre_pagina
                )
                if extracted_cover:
                    print(f"✅ USANDO PRIMERA PÁGINA: {extracted_cover}")
                    return extracted_cover

            # FALLBACK FINAL: extracción directa sin BD
            print(f"⚠️ Fallback: extracción directa del archivo...")
            extracted = self._extract_first_page_from_comic_file(comic_path)
            print(f"🎯 USANDO EXTRACCIÓN DIRECTA: {extracted}")
            return extracted

        except Exception as e:
            print(f"💥 Error en lógica inteligente de cover: {e}")
            import traceback
            traceback.print_exc()
            return self._extract_first_page_from_comic_file(comic_path)

    def _extract_specific_page_from_comic(self, comic_path, page_order, page_name=None):
        """Extraer una página específica por nombre o por orden del archivo de comic"""
        import tempfile

        try:
            if page_name:
                print(f"🎯 Extrayendo página '{page_name}' de {os.path.basename(comic_path)}")
            else:
                print(f"🎯 Extrayendo página #{page_order} de {os.path.basename(comic_path)}")

            if comic_path.lower().endswith('.cbz'):
                with self.zipfile.ZipFile(comic_path, 'r') as zip_file:
                    # Encontrar archivos de imagen
                    image_files = [
                        f for f in zip_file.namelist()
                        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp'))
                        and not f.startswith('__MACOSX')
                        and '/' not in f.split('/')[-1][:1]  # Evitar archivos ocultos
                    ]

                    if image_files:
                        # Ordenar para mantener consistencia
                        image_files.sort()
                        print(f"📄 Total imágenes encontradas: {len(image_files)}")

                        target_image = None

                        # PRIORIDAD 1: Buscar por nombre exacto si se proporcionó
                        if page_name:
                            for img_path in image_files:
                                if os.path.basename(img_path) == page_name or img_path.endswith('/' + page_name):
                                    target_image = img_path
                                    print(f"✅ Encontrada por nombre: {target_image}")
                                    break

                        # PRIORIDAD 2: Buscar por orden si no se encontró por nombre
                        if not target_image and 1 <= page_order <= len(image_files):
                            target_image = image_files[page_order - 1]
                            print(f"📖 Página #{page_order}: {target_image}")

                        if target_image:
                            # Extraer a temporal
                            temp_dir = tempfile.mkdtemp(dir='/tmp')
                            temp_path = os.path.join(temp_dir, os.path.basename(target_image))

                            with zip_file.open(target_image) as source:
                                with open(temp_path, 'wb') as target:
                                    target.write(source.read())

                            print(f"✅ Página extraída: {temp_path}")
                            return temp_path
                        else:
                            if page_name:
                                print(f"❌ No se encontró página con nombre '{page_name}'")
                            else:
                                print(f"❌ Orden {page_order} fuera de rango (1-{len(image_files)})")

            elif comic_path.lower().endswith('.cbr') and self.has_rarfile:
                with self.rarfile.RarFile(comic_path, 'r') as rar_file:
                    image_files = [
                        f for f in rar_file.namelist()
                        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp'))
                    ]

                    if image_files:
                        image_files.sort()
                        print(f"📄 Total imágenes encontradas: {len(image_files)}")

                        target_image = None

                        # PRIORIDAD 1: Buscar por nombre exacto si se proporcionó
                        if page_name:
                            for img_path in image_files:
                                if os.path.basename(img_path) == page_name or img_path.endswith('/' + page_name) or img_path.endswith('\\' + page_name):
                                    target_image = img_path
                                    print(f"✅ Encontrada por nombre: {target_image}")
                                    break

                        # PRIORIDAD 2: Buscar por orden si no se encontró por nombre
                        if not target_image and 1 <= page_order <= len(image_files):
                            target_image = image_files[page_order - 1]
                            print(f"📖 Página #{page_order}: {target_image}")

                        if target_image:
                            temp_dir = tempfile.mkdtemp(dir='/tmp')
                            temp_path = os.path.join(temp_dir, os.path.basename(target_image))

                            image_data = rar_file.read(target_image)
                            with open(temp_path, 'wb') as f:
                                f.write(image_data)

                            print(f"✅ Página extraída: {temp_path}")
                            return temp_path
                        else:
                            if page_name:
                                print(f"❌ No se encontró página con nombre '{page_name}'")
                            else:
                                print(f"❌ Orden {page_order} fuera de rango (1-{len(image_files)})")

            return None

        except Exception as e:
            print(f"💥 Error extrayendo página #{page_order}: {e}")
            return None

    def _extract_first_page_from_comic_file(self, comic_path):
        """Extraer primera página de un archivo de comic a archivo temporal"""
        import tempfile

        try:
            # Usar ComicExtractor para detectar formato real
            comic_format = self.comic_extractor.detect_comic_format(comic_path)

            if comic_format == 'zip':
                with self.zipfile.ZipFile(comic_path, 'r') as zip_file:
                    # Encontrar archivos de imagen
                    image_files = [
                        f for f in zip_file.namelist()
                        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp'))
                        and not f.startswith('__MACOSX')
                        and '/' not in f.split('/')[-1][:1]  # Evitar archivos ocultos
                    ]

                    if image_files:
                        # Ordenar y tomar primera
                        image_files.sort()
                        first_image = image_files[0]

                        # Extraer a temporal
                        temp_dir = tempfile.mkdtemp(dir='/tmp')
                        temp_path = os.path.join(temp_dir, os.path.basename(first_image))

                        with zip_file.open(first_image) as source:
                            with open(temp_path, 'wb') as target:
                                target.write(source.read())

                        return temp_path

            elif comic_format == 'rar' and self.has_rarfile:
                with self.rarfile.RarFile(comic_path, 'r') as rar_file:
                    image_files = [
                        f for f in rar_file.namelist()
                        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp'))
                    ]

                    if image_files:
                        image_files.sort()
                        first_image = image_files[0]

                        temp_dir = tempfile.mkdtemp(dir='/tmp')
                        temp_path = os.path.join(temp_dir, os.path.basename(first_image))

                        image_data = rar_file.read(first_image)
                        with open(temp_path, 'wb') as f:
                            f.write(image_data)

                        return temp_path

            return None

        except Exception as e:
            print(f"Error extrayendo primera página: {e}")
            return None

    def _cleanup_temp_file(self, file_path):
        """Limpiar archivo temporal"""
        try:
            import tempfile
            if file_path and file_path.startswith(tempfile.gettempdir()):
                if os.path.exists(file_path):
                    os.unlink(file_path)
                # Intentar limpiar directorio si está vacío
                parent_dir = os.path.dirname(file_path)
                try:
                    if not os.listdir(parent_dir):
                        os.rmdir(parent_dir)
                except:
                    pass
        except Exception as e:
            print(f"Error limpiando temporal: {e}")

    def set_session(self, session):
        """Configurar sesión de base de datos para lógica inteligente"""
        self.session = session


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