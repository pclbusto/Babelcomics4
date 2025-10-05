#!/usr/bin/env python3
"""
ComicScanner moderno - Escanea directorios configurados y carga cómics en la BD
Compatible con la nueva estructura de configuración usando setup_directorios
"""

import os
import sys
import time
import threading
from pathlib import Path
from sqlalchemy.orm import sessionmaker

# Agregar directorio padre al path
sys.path.append(str(Path(__file__).parent.parent))

from entidades import engine
from entidades.comicbook_model import Comicbook
from helpers.config_helper import ConfigHelper

class ComicScanner:
    """Scanner moderno de cómics que usa la configuración de BD"""

    # Formatos soportados para cómics
    COMIC_EXTENSIONS = {'.cbr', '.cbz', '.pdf', '.zip', '.rar', '.7z', '.cb7', '.cbt'}

    def __init__(self, progress_callback=None, status_callback=None):
        """
        Inicializar scanner

        Args:
            progress_callback: function(progress_percent) - Progreso 0.0-1.0
            status_callback: function(message) - Mensaje de estado actual
        """
        self.progress_callback = progress_callback
        self.status_callback = status_callback
        self.is_cancelled = False
        self.start_time = None

        # Estadísticas
        self.total_files_found = 0
        self.files_processed = 0
        self.comics_added = 0
        self.comics_skipped = 0
        self.errors = 0

    def is_comic_file(self, file_path):
        """Verificar si un archivo es un cómic válido"""
        try:
            path = Path(file_path)

            # Verificar extensión
            if path.suffix.lower() not in self.COMIC_EXTENSIONS:
                return False

            # Verificar que existe y es archivo
            if not path.exists() or not path.is_file():
                return False

            # Verificar tamaño mínimo (evitar archivos corruptos)
            if path.stat().st_size < 1024:  # 1KB mínimo
                return False

            return True

        except Exception:
            return False

    def scan_directory_for_comics(self, directory_path):
        """Escanear directorio recursivamente buscando cómics"""
        comics_found = []
        directory = Path(directory_path)

        if not directory.exists() or not directory.is_dir():
            return comics_found

        try:
            # Escaneo recursivo
            for file_path in directory.rglob("*"):
                if self.is_cancelled:
                    break

                if self.is_comic_file(file_path):
                    comics_found.append(str(file_path.absolute()))

        except PermissionError:
            print(f"Sin permisos para acceder a: {directory}")
        except Exception as e:
            print(f"Error escaneando {directory}: {e}")

        return comics_found

    def estimate_scan_time(self, directories):
        """Estimar tiempo total de escaneo"""
        if not directories:
            return 0, 0

        print("🔍 Estimando tiempo de escaneo...")

        # Estimación rápida: contar archivos en muestra pequeña
        sample_files = 0
        total_dirs = 0

        for directory in directories:
            try:
                dir_path = Path(directory)
                if dir_path.exists():
                    # Contar solo primeros 100 archivos para estimación
                    files_in_dir = 0
                    for item in dir_path.rglob("*"):
                        if item.is_file():
                            files_in_dir += 1
                            if files_in_dir >= 100:  # Muestra limitada
                                break

                    sample_files += files_in_dir
                    total_dirs += 1

            except Exception:
                continue

        if sample_files == 0:
            return 0, 0

        # Estimación: promedio 10-50 archivos por directorio
        # Velocidad estimada: 100-500 archivos/segundo dependiendo del disco
        estimated_total_files = sample_files * max(1, total_dirs) * 10  # Factor conservador
        estimated_comics = estimated_total_files * 0.1  # ~10% suelen ser cómics

        # Tiempo estimado: ~200 archivos/segundo en SSD, ~50 en HDD
        estimated_seconds = estimated_total_files / 150  # Valor intermedio

        return int(estimated_comics), int(estimated_seconds)

    def get_existing_comic_paths(self, session):
        """Obtener paths de cómics ya existentes en BD"""
        try:
            existing_paths = session.query(Comicbook.path).all()
            return {path[0] for path in existing_paths if path[0]}
        except Exception as e:
            print(f"Error obteniendo cómics existentes: {e}")
            return set()

    def scan_directories(self, skip_existing=True):
        """
        Escanear todos los directorios configurados

        Args:
            skip_existing: Si True, omitir cómics ya existentes en BD

        Returns:
            dict: Estadísticas del escaneo
        """
        self.start_time = time.time()
        self.is_cancelled = False

        # Resetear estadísticas
        self.total_files_found = 0
        self.files_processed = 0
        self.comics_added = 0
        self.comics_skipped = 0
        self.errors = 0

        try:
            # Obtener directorios configurados
            scan_directories = ConfigHelper.get_scan_directories()

            if not scan_directories:
                self._update_status("❌ No hay directorios configurados para escanear")
                return self._get_stats()

            self._update_status(f"🔍 Escaneando {len(scan_directories)} directorios configurados...")

            # Estimación inicial
            estimated_comics, estimated_time = self.estimate_scan_time(scan_directories)
            if estimated_comics > 0:
                self._update_status(f"📊 Estimación: ~{estimated_comics} cómics, ~{estimated_time}s")

            # Conectar a BD
            Session = sessionmaker(bind=engine)
            session = Session()

            try:
                # Obtener cómics existentes si se van a omitir
                existing_paths = set()
                if skip_existing:
                    self._update_status("📋 Obteniendo cómics existentes...")
                    existing_paths = self.get_existing_comic_paths(session)
                    self._update_status(f"📋 {len(existing_paths)} cómics ya catalogados")

                # Paso 1: Encontrar todos los archivos
                self._update_status("🔍 Buscando archivos de cómics...")
                all_comic_files = []

                for i, directory in enumerate(scan_directories):
                    if self.is_cancelled:
                        break

                    dir_progress = i / len(scan_directories) * 0.3  # 30% para escaneo
                    self._update_progress(dir_progress)
                    self._update_status(f"🔍 Escaneando: {Path(directory).name}...")

                    comics_in_dir = self.scan_directory_for_comics(directory)
                    all_comic_files.extend(comics_in_dir)

                if self.is_cancelled:
                    self._update_status("❌ Escaneo cancelado por el usuario")
                    return self._get_stats()

                self.total_files_found = len(all_comic_files)
                self._update_status(f"✅ Encontrados {self.total_files_found} archivos de cómics")

                if self.total_files_found == 0:
                    self._update_status("ℹ️ No se encontraron archivos de cómics")
                    return self._get_stats()

                # Paso 2: Procesar archivos
                self._update_status("📦 Procesando archivos...")

                for i, file_path in enumerate(all_comic_files):
                    if self.is_cancelled:
                        break

                    # Progreso: 30% escaneo + 70% procesamiento
                    process_progress = 0.3 + (i / self.total_files_found) * 0.7
                    self._update_progress(process_progress)

                    self.files_processed += 1
                    file_name = Path(file_path).name

                    # Verificar si ya existe
                    if skip_existing and file_path in existing_paths:
                        self.comics_skipped += 1
                        continue

                    try:
                        # Crear nuevo cómic
                        comic = Comicbook(
                            path=file_path,
                            id_comicbook_info='',  # Sin catalogar
                            calidad=0,  # Calidad por defecto
                            en_papelera=False  # Recién agregado
                        )

                        session.add(comic)
                        self.comics_added += 1

                        # Commit cada 100 elementos para rendimiento
                        if self.comics_added % 100 == 0:
                            session.commit()
                            self._update_status(f"💾 Guardados {self.comics_added} cómics...")

                    except Exception as e:
                        self.errors += 1
                        print(f"Error procesando {file_name}: {e}")

                # Commit final
                if not self.is_cancelled and self.comics_added > 0:
                    session.commit()
                    self._update_status("💾 Guardando cambios finales...")

            finally:
                session.close()

            # Resultado final
            if self.is_cancelled:
                self._update_status("❌ Proceso cancelado")
            else:
                elapsed = time.time() - self.start_time
                self._update_status(f"✅ Completado en {elapsed:.1f}s")

            self._update_progress(1.0)

        except Exception as e:
            self.errors += 1
            self._update_status(f"❌ Error durante el escaneo: {e}")
            print(f"Error en scan_directories: {e}")
            import traceback
            traceback.print_exc()

        return self._get_stats()

    def cancel_scan(self):
        """Cancelar escaneo en progreso"""
        self.is_cancelled = True
        self._update_status("⏹️ Cancelando escaneo...")

    def _update_progress(self, progress):
        """Actualizar progreso (0.0-1.0)"""
        if self.progress_callback:
            self.progress_callback(progress)

    def _update_status(self, message):
        """Actualizar mensaje de estado"""
        print(f"ComicScanner: {message}")
        if self.status_callback:
            self.status_callback(message)

    def _get_stats(self):
        """Obtener estadísticas del escaneo"""
        elapsed = (time.time() - self.start_time) if self.start_time else 0

        return {
            'total_files_found': self.total_files_found,
            'files_processed': self.files_processed,
            'comics_added': self.comics_added,
            'comics_skipped': self.comics_skipped,
            'errors': self.errors,
            'elapsed_time': elapsed,
            'cancelled': self.is_cancelled
        }

# Función de conveniencia para usar el scanner
def scan_comic_directories(progress_callback=None, status_callback=None, skip_existing=True):
    """
    Función simple para escanear directorios configurados

    Returns:
        dict: Estadísticas del escaneo
    """
    scanner = ComicScanner(progress_callback, status_callback)
    return scanner.scan_directories(skip_existing)

if __name__ == "__main__":
    # Test del scanner
    print("🚀 Testing ComicScanner...")

    def progress_cb(progress):
        print(f"Progreso: {progress*100:.1f}%")

    def status_cb(message):
        print(f"Estado: {message}")

    stats = scan_comic_directories(progress_cb, status_cb)

    print("\n📊 Estadísticas finales:")
    print(f"   - Archivos encontrados: {stats['total_files_found']}")
    print(f"   - Cómics agregados: {stats['comics_added']}")
    print(f"   - Cómics omitidos: {stats['comics_skipped']}")
    print(f"   - Errores: {stats['errors']}")
    print(f"   - Tiempo transcurrido: {stats['elapsed_time']:.1f}s")
    print(f"   - Cancelado: {stats['cancelled']}")