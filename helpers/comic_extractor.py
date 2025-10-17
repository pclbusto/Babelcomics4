#!/usr/bin/env python3
"""
comic_extractor.py - Extractor de páginas de archivos de cómics
Soporta CBZ (ZIP), CBR (RAR), y otros formatos comprimidos
"""

import os
import sys
import tempfile
import zipfile
import shutil
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional

# Agregar directorio padre al path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import sessionmaker
from entidades import engine
from entidades.comicbook_model import Comicbook
from entidades.comicbook_detail_model import Comicbook_Detail

# Intentar importar dependencias opcionales
try:
    import rarfile
    RAR_SUPPORT = True
    print("✅ Soporte RAR (CBR) disponible")
except ImportError:
    RAR_SUPPORT = False
    print("⚠️ Soporte RAR (CBR) no disponible - instalar: pip install rarfile")

try:
    import py7zr
    SEVEN_ZIP_SUPPORT = True
    print("✅ Soporte 7z (CB7) disponible")
except ImportError:
    SEVEN_ZIP_SUPPORT = False
    print("⚠️ Soporte 7z (CB7) no disponible - instalar: pip install py7zr")

try:
    from PIL import Image
    PIL_SUPPORT = True
    print("✅ Soporte PIL (thumbnails) disponible")
except ImportError:
    PIL_SUPPORT = False
    print("⚠️ Soporte PIL (thumbnails) no disponible - instalar: pip install Pillow")


class ComicExtractor:
    """Extractor de páginas de archivos de cómics"""

    # Extensiones de archivo soportadas
    COMIC_EXTENSIONS = {'.cbz', '.cbr', '.cb7', '.cbt', '.zip', '.rar', '.7z'}

    # Extensiones de imagen válidas (en orden de prioridad)
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif', '.tiff'}

    def __init__(self, progress_callback=None, status_callback=None):
        """
        Inicializar extractor

        Args:
            progress_callback: function(progress_percent) - Progreso 0.0-1.0
            status_callback: function(message) - Mensaje de estado actual
        """
        self.progress_callback = progress_callback
        self.status_callback = status_callback

        # Estadísticas
        self.comics_processed = 0
        self.pages_extracted = 0
        self.errors = 0

    def detect_comic_format(self, file_path: str) -> Optional[str]:
        """Detectar formato del archivo de cómic"""
        try:
            path = Path(file_path)
            extension = path.suffix.lower()

            # Mapeo de extensiones a formatos
            format_map = {
                '.cbz': 'zip',
                '.zip': 'zip',
                '.cbr': 'rar',
                '.rar': 'rar',
                '.cb7': '7z',
                '.7z': '7z',
                '.cbt': 'tar'
            }

            detected_format = format_map.get(extension)

            # Verificar si tenemos soporte para el formato
            if detected_format == 'rar' and not RAR_SUPPORT:
                print(f"❌ Archivo RAR detectado pero sin soporte: {file_path}")
                return None

            if detected_format == '7z' and not SEVEN_ZIP_SUPPORT:
                print(f"❌ Archivo 7z detectado pero sin soporte: {file_path}")
                return None

            return detected_format

        except Exception as e:
            print(f"Error detectando formato de {file_path}: {e}")
            return None

    def extract_comic_pages(self, comic_file: str, temp_dir: str) -> List[str]:
        """Extraer páginas de un archivo de cómic a directorio temporal"""
        try:
            comic_format = self.detect_comic_format(comic_file)
            if not comic_format:
                return []

            extracted_files = []

            if comic_format == 'zip':
                extracted_files = self._extract_zip(comic_file, temp_dir)
            elif comic_format == 'rar':
                extracted_files = self._extract_rar(comic_file, temp_dir)
            elif comic_format == '7z':
                extracted_files = self._extract_7z(comic_file, temp_dir)
            else:
                print(f"Formato no soportado: {comic_format}")
                return []

            # Filtrar solo archivos de imagen
            image_files = self._filter_image_files(extracted_files)

            # Ordenar por nombre (orden de lectura)
            image_files.sort(key=lambda x: self._natural_sort_key(Path(x).name))

            return image_files

        except Exception as e:
            print(f"Error extrayendo páginas de {comic_file}: {e}")
            return []

    def _extract_zip(self, zip_file: str, temp_dir: str) -> List[str]:
        """Extraer archivo ZIP/CBZ"""
        extracted = []
        try:
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                for file_info in zip_ref.filelist:
                    if not file_info.is_dir():
                        # Extraer archivo
                        zip_ref.extract(file_info, temp_dir)
                        extracted_path = os.path.join(temp_dir, file_info.filename)
                        extracted.append(extracted_path)
            return extracted
        except Exception as e:
            print(f"Error extrayendo ZIP {zip_file}: {e}")
            return []

    def _extract_rar(self, rar_file: str, temp_dir: str) -> List[str]:
        """Extraer archivo RAR/CBR"""
        if not RAR_SUPPORT:
            return self._extract_rar_system_command(rar_file, temp_dir)

        extracted = []
        try:
            with rarfile.RarFile(rar_file, 'r') as rar_ref:
                for file_info in rar_ref.infolist():
                    if not file_info.is_dir():
                        # Extraer archivo
                        rar_ref.extract(file_info, temp_dir)
                        extracted_path = os.path.join(temp_dir, file_info.filename)
                        extracted.append(extracted_path)
            return extracted
        except Exception as e:
            print(f"Error extrayendo RAR con rarfile {rar_file}: {e}")
            print("🔄 Intentando extracción con comando del sistema...")
            return self._extract_rar_system_command(rar_file, temp_dir)

    def _extract_rar_system_command(self, rar_file: str, temp_dir: str) -> List[str]:
        """Extraer archivo RAR usando comandos del sistema"""
        extracted = []

        # Lista de comandos RAR a intentar
        rar_commands = ['unrar', 'rar', '7z']

        for cmd in rar_commands:
            try:
                # Verificar si el comando existe
                subprocess.run([cmd, '--help'], capture_output=True, check=False, timeout=5)

                print(f"🔧 Intentando extracción RAR con: {cmd}")

                if cmd == '7z':
                    # Comando 7z - solo extraer archivos de imagen
                    result = subprocess.run([
                        '7z', 'x', '-y', f'-o{temp_dir}', rar_file,
                        '*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp', '*.webp'
                    ], capture_output=True, text=True, timeout=300)
                else:
                    # Comandos unrar/rar - solo extraer archivos de imagen
                    result = subprocess.run([
                        cmd, 'x', '-y', '-o+', rar_file, temp_dir + '/',
                        '*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp', '*.webp'
                    ], capture_output=True, text=True, timeout=300)

                if result.returncode == 0:
                    print(f"✅ Extracción RAR exitosa con {cmd}")

                    # Buscar archivos extraídos
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            if not file.startswith('.'):  # Ignorar archivos ocultos
                                extracted.append(file_path)

                    return extracted
                else:
                    print(f"❌ Error con {cmd}: {result.stderr}")

            except subprocess.TimeoutExpired:
                print(f"⏰ Timeout con comando {cmd}")
            except FileNotFoundError:
                print(f"⚠️ Comando {cmd} no encontrado")
            except Exception as e:
                print(f"❌ Error con comando {cmd}: {e}")

        print("❌ No se pudo extraer el archivo RAR con ningún método")
        return []

    def _extract_7z(self, seven_z_file: str, temp_dir: str) -> List[str]:
        """Extraer archivo 7z/CB7"""
        if not SEVEN_ZIP_SUPPORT:
            return []

        extracted = []
        try:
            with py7zr.SevenZipFile(seven_z_file, 'r') as seven_z_ref:
                seven_z_ref.extractall(path=temp_dir)
                # Buscar archivos extraídos recursivamente
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        extracted.append(os.path.join(root, file))
            return extracted
        except Exception as e:
            print(f"Error extrayendo 7z {seven_z_file}: {e}")
            return []

    def _filter_image_files(self, file_list: List[str]) -> List[str]:
        """Filtrar solo archivos de imagen válidos"""
        image_files = []
        for file_path in file_list:
            try:
                # Verificar extensión
                extension = Path(file_path).suffix.lower()
                if extension in self.IMAGE_EXTENSIONS:
                    # Verificar que el archivo existe
                    if os.path.exists(file_path) and os.path.isfile(file_path):
                        image_files.append(file_path)
            except Exception:
                continue
        return image_files

    def _natural_sort_key(self, text: str):
        """Clave de ordenamiento natural para nombres de archivo"""
        import re
        def atoi(text):
            return int(text) if text.isdigit() else text.lower()
        return [atoi(c) for c in re.split(r'(\d+)', text)]

    def generate_page_thumbnail(self, image_path: str, thumbnail_path: str, size=(150, 200)) -> bool:
        """Generar thumbnail de una página"""
        if not PIL_SUPPORT:
            return False

        try:
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)

            # Abrir y redimensionar imagen
            with Image.open(image_path) as img:
                # Convertir a RGB si es necesario
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')

                # Redimensionar manteniendo aspecto
                img.thumbnail(size, Image.Resampling.LANCZOS)

                # Guardar thumbnail
                img.save(thumbnail_path, 'JPEG', quality=85, optimize=True)

            return True

        except Exception as e:
            print(f"Error generando thumbnail {thumbnail_path}: {e}")
            return False

    def process_comic(self, comic: Comicbook, session) -> bool:
        """Procesar un cómic completo: extraer páginas y popular BD"""
        try:
            self._update_status(f"Procesando: {Path(comic.path).name}")

            # Verificar que el archivo existe
            if not os.path.exists(comic.path):
                print(f"❌ Archivo no existe: {comic.path}")
                return False

            # Verificar si ya tiene páginas en BD
            existing_pages = session.query(Comicbook_Detail).filter(
                Comicbook_Detail.comicbook_id == comic.id_comicbook
            ).count()

            if existing_pages > 0:
                print(f"✅ Cómic {comic.id_comicbook} ya tiene {existing_pages} páginas")
                return True

            # Crear directorio temporal
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extraer páginas del archivo
                page_files = self.extract_comic_pages(comic.path, temp_dir)

                if not page_files:
                    print(f"❌ No se pudieron extraer páginas de: {comic.path}")
                    return False

                print(f"📄 Extraídas {len(page_files)} páginas de {Path(comic.path).name}")

                # Crear directorio de thumbnails
                thumbnail_dir = os.path.join("data", "thumbnails", "comic_pages", str(comic.id_comicbook))
                os.makedirs(thumbnail_dir, exist_ok=True)

                # Procesar cada página
                for page_order, page_file in enumerate(page_files, 1):
                    try:
                        # Generar thumbnail
                        thumbnail_filename = f"page_{page_order:03d}.jpg"
                        thumbnail_path = os.path.join(thumbnail_dir, thumbnail_filename)

                        thumbnail_success = self.generate_page_thumbnail(page_file, thumbnail_path)

                        # Crear registro en BD
                        page_detail = Comicbook_Detail()
                        page_detail.comicbook_id = comic.id_comicbook
                        page_detail.indicePagina = page_order - 1  # 0-based
                        page_detail.ordenPagina = page_order      # 1-based
                        page_detail.tipoPagina = 1 if page_order == 1 else 0  # Primera página = COVER
                        page_detail.nombre_pagina = Path(page_file).name

                        session.add(page_detail)

                        if thumbnail_success:
                            self.pages_extracted += 1

                    except Exception as e:
                        print(f"Error procesando página {page_order}: {e}")
                        self.errors += 1

                # Commit páginas de este cómic
                session.commit()
                self.comics_processed += 1

                print(f"✅ Procesado cómic {comic.id_comicbook}: {len(page_files)} páginas")
                return True

        except Exception as e:
            print(f"Error procesando cómic {comic.id_comicbook}: {e}")
            session.rollback()
            self.errors += 1
            return False

    def process_comics_batch(self, comic_ids: List[int] = None, limit: int = None) -> dict:
        """Procesar lote de cómics"""
        try:
            Session = sessionmaker(bind=engine)
            session = Session()

            # Construir query
            query = session.query(Comicbook)

            if comic_ids:
                query = query.filter(Comicbook.id_comicbook.in_(comic_ids))

            if limit:
                query = query.limit(limit)

            comics = query.all()
            total_comics = len(comics)

            self._update_status(f"Procesando {total_comics} cómics...")

            for i, comic in enumerate(comics):
                if self.progress_callback:
                    progress = i / total_comics
                    self.progress_callback(progress)

                self.process_comic(comic, session)

            session.close()

            # Estadísticas finales
            stats = {
                'comics_processed': self.comics_processed,
                'pages_extracted': self.pages_extracted,
                'errors': self.errors,
                'total_comics': total_comics
            }

            self._update_status(f"✅ Completado: {self.comics_processed}/{total_comics} cómics")

            return stats

        except Exception as e:
            print(f"Error en proceso batch: {e}")
            return {'error': str(e)}

    def _update_status(self, message: str):
        """Actualizar mensaje de estado"""
        print(f"ComicExtractor: {message}")
        if self.status_callback:
            self.status_callback(message)


# Función de conveniencia
def extract_comic_pages(comic_id: int) -> bool:
    """Extraer páginas de un cómic específico"""
    extractor = ComicExtractor()
    return extractor.process_comics_batch([comic_id])


if __name__ == "__main__":
    # Test del extractor
    print("🧪 Testing ComicExtractor...")

    extractor = ComicExtractor()

    # Procesar primeros 3 cómics como test
    stats = extractor.process_comics_batch(limit=3)

    print("\n📊 Estadísticas:")
    print(f"   - Cómics procesados: {stats.get('comics_processed', 0)}")
    print(f"   - Páginas extraídas: {stats.get('pages_extracted', 0)}")
    print(f"   - Errores: {stats.get('errors', 0)}")