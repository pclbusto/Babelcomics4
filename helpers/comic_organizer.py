#!/usr/bin/env python3
"""
Helper para organizar y renombrar cómics físicos
Maneja la generación de nombres normalizados, detección de duplicados,
y movimiento de archivos con actualización de la base de datos
"""

import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ComicOrganizationPlan:
    """Plan de reorganización para un cómic"""
    comicbook_id: int
    current_path: str  # Path actual (absoluto)
    new_path_relative: str  # Path nuevo relativo a carpeta base
    new_path_absolute: str  # Path nuevo absoluto
    filename_normalized: str  # Nombre de archivo normalizado
    status: str  # 'OK', 'DUPLICATE', 'ALREADY_IN_PLACE', 'NO_INFO', 'ERROR'
    message: str  # Mensaje descriptivo
    version: int  # Número de versión si es duplicado (0 = original, 1+ = versiones)
    volume_id: int = 0  # ID del volumen al que pertenece (para agrupación)
    volume_name: str = ""  # Nombre del volumen (para display)


class ComicOrganizer:
    """
    Organiza cómics físicos en estructura:
    {base_folder}/{Publisher}/{Volume}/{normalized_name}.ext
    """

    def __init__(self, base_folder: str, session):
        """
        Args:
            base_folder: Carpeta base donde organizar los cómics
            session: Sesión de SQLAlchemy para acceso a BD
        """
        self.base_folder = Path(base_folder)
        self.session = session

    def sanitize_filename(self, name: str) -> str:
        """
        Limpia un nombre de archivo de caracteres inválidos.
        Mantiene solo letras, números, espacios, guiones y paréntesis.
        """
        # Reemplazar caracteres problemáticos
        replacements = {
            '/': '-',
            '\\': '-',
            ':': '-',
            '*': '',
            '?': '',
            '"': '',
            '<': '',
            '>': '',
            '|': '',
            '\n': ' ',
            '\r': ' ',
            '\t': ' ',
        }

        for old, new in replacements.items():
            name = name.replace(old, new)

        # Eliminar múltiples espacios
        name = re.sub(r'\s+', ' ', name)

        # Eliminar espacios al inicio y final
        name = name.strip()

        return name

    def generate_normalized_filename(
        self,
        volume_name: str,
        issue_number: str,
        extension: str,
        version: int = 0
    ) -> str:
        """
        Genera un nombre de archivo normalizado.

        Formato: {Volume} {Number}[_ver{XX}].ext
        Ejemplo: Batman 001.cbz
        Ejemplo duplicado: Batman 001_ver01.cbz

        Args:
            volume_name: Nombre del volumen
            issue_number: Número del issue
            extension: Extensión del archivo (incluye el punto)
            version: Número de versión (0 = original, 1+ = versión)

        Returns:
            Nombre de archivo normalizado
        """
        # Limpiar nombre del volumen
        clean_volume = self.sanitize_filename(volume_name)

        # Formatear número con padding (ej: 1 -> 001, 12 -> 012)
        # Intentar extraer el número si viene con texto
        number_match = re.search(r'(\d+)', str(issue_number))
        if number_match:
            number = int(number_match.group(1))
            formatted_number = f"{number:03d}"
        else:
            # Si no hay número, usar el issue_number tal cual
            formatted_number = self.sanitize_filename(str(issue_number))

        # Construir nombre base
        base_name = f"{clean_volume} {formatted_number}"

        # Agregar versión si es duplicado
        if version > 0:
            base_name += f"_ver{version:02d}"

        return f"{base_name}{extension}"

    def _detect_and_fix_extension(self, file_path: str, original_extension: str) -> str:
        """
        Detecta el tipo real del archivo y corrige la extensión si es necesario.

        Args:
            file_path: Path completo al archivo
            original_extension: Extensión original (ej: '.cbz')

        Returns:
            Extensión correcta basada en el tipo real del archivo
        """
        import subprocess

        try:
            # Usar 'file' command para detectar el tipo real
            result = subprocess.run(
                ['file', '-b', '--mime-type', file_path],
                capture_output=True,
                text=True,
                timeout=5
            )

            mime_type = result.stdout.strip()

            # Mapeo de MIME types a extensiones
            if 'zip' in mime_type.lower() or 'application/zip' == mime_type:
                correct_ext = '.cbz'
            elif 'rar' in mime_type.lower() or 'application/x-rar' == mime_type:
                correct_ext = '.cbr'
            elif '7z' in mime_type.lower() or 'application/x-7z' in mime_type:
                correct_ext = '.cb7'
            elif 'pdf' in mime_type.lower():
                correct_ext = '.pdf'
            else:
                # Si no podemos detectar, usar la original
                return original_extension

            # Si la extensión es diferente, reportar
            if correct_ext != original_extension.lower():
                print(f"  ⚠️  Extensión incorrecta detectada:")
                print(f"      Archivo: {os.path.basename(file_path)}")
                print(f"      Extensión original: {original_extension}")
                print(f"      Tipo real: {mime_type}")
                print(f"      Extensión correcta: {correct_ext}")
                return correct_ext

            return original_extension

        except Exception as e:
            print(f"  ⚠️  No se pudo detectar tipo de archivo, usando extensión original: {e}")
            return original_extension

    def get_comic_metadata(self, comicbook_id: int) -> Optional[Dict]:
        """
        Obtiene metadata completa de un cómic (Publisher, Volume, ComicbookInfo)

        Returns:
            Dict con 'publisher', 'volume', 'info', 'comicbook' o None si no tiene info
        """
        from entidades.comicbook_model import Comicbook
        from entidades.comicbook_info_model import ComicbookInfo
        from entidades.volume_model import Volume
        from entidades.publisher_model import Publisher

        # Obtener el comicbook
        comicbook = self.session.query(Comicbook).filter_by(
            id_comicbook=comicbook_id
        ).first()

        if not comicbook:
            return None

        # Verificar que tenga info asociada
        if not comicbook.id_comicbook_info or comicbook.id_comicbook_info.strip() == '':
            return None

        # Obtener ComicbookInfo
        comic_info = self.session.query(ComicbookInfo).filter_by(
            id_comicbook_info=comicbook.id_comicbook_info
        ).first()

        if not comic_info:
            return None

        # Obtener Volume
        volume = self.session.query(Volume).filter_by(
            id_volume=comic_info.id_volume
        ).first()

        if not volume:
            return None

        # Obtener Publisher
        publisher = self.session.query(Publisher).filter_by(
            id_publisher=volume.id_publisher
        ).first()

        # Publisher puede ser None, no es obligatorio

        return {
            'comicbook': comicbook,
            'info': comic_info,
            'volume': volume,
            'publisher': publisher
        }

    def generate_target_path(
        self,
        publisher_name: Optional[str],
        volume_name: str,
        volume_year: int,
        filename: str
    ) -> Tuple[str, str]:
        """
        Genera el path de destino relativo y absoluto.

        Estructura: {Publisher}/{Volume-Year}/{filename}
        Ejemplo: DC Comics/The Flash-2011/The Flash 001.cbz
        Si no hay publisher: Sin Editorial/{Volume-Year}/{filename}

        Returns:
            Tupla (path_relativo, path_absoluto)
        """
        # Sanitizar nombres de carpetas
        publisher_folder = self.sanitize_filename(publisher_name) if publisher_name else "Sin Editorial"

        # Generar nombre de carpeta del volumen con año
        if volume_year and volume_year > 0:
            volume_folder = self.sanitize_filename(f"{volume_name}-{volume_year}")
        else:
            volume_folder = self.sanitize_filename(volume_name)

        # Construir path relativo
        relative_path = os.path.join(publisher_folder, volume_folder, filename)

        # Construir path absoluto
        absolute_path = self.base_folder / relative_path

        return (relative_path, str(absolute_path))

    def find_existing_versions(
        self,
        target_dir: Path,
        base_filename: str
    ) -> List[int]:
        """
        Encuentra versiones existentes de un archivo.

        Args:
            target_dir: Directorio donde buscar
            base_filename: Nombre base del archivo (con extensión, sin _verXX)

        Returns:
            Lista de números de versión encontrados [0, 1, 2, ...] ordenados
        """
        if not target_dir.exists():
            return []

        # Separar nombre y extensión
        name, ext = os.path.splitext(base_filename)

        versions = []

        # Buscar archivo original (sin versión)
        original_file = target_dir / base_filename
        if original_file.exists():
            versions.append(0)

        # Buscar versiones (_ver01, _ver02, etc.)
        pattern = re.compile(rf"^{re.escape(name)}_ver(\d{{2}}){re.escape(ext)}$")

        for file in target_dir.iterdir():
            if file.is_file():
                match = pattern.match(file.name)
                if match:
                    version_num = int(match.group(1))
                    versions.append(version_num)

        return sorted(versions)

    def create_organization_plan(
        self,
        volume_id: Optional[int] = None,
        volume_ids: Optional[List[int]] = None,
        comicbook_ids: Optional[List[int]] = None
    ) -> List[ComicOrganizationPlan]:
        """
        Crea un plan de reorganización para los cómics especificados.

        Args:
            volume_id: ID de un volumen. Si se proporciona, solo procesa cómics de ese volumen.
            volume_ids: Lista de IDs de volúmenes. Si se proporciona, procesa cómics de esos volúmenes.
            comicbook_ids: IDs de cómics a organizar. Si es None, procesa todos de los volúmenes.

        Returns:
            Lista de planes de organización
        """
        from entidades.comicbook_model import Comicbook
        from entidades.comicbook_info_model import ComicbookInfo

        plans = []

        # Obtener cómics a procesar
        query = self.session.query(Comicbook).filter_by(en_papelera=False)

        # Filtrar por volumen(es) si se especifica
        if volume_id or volume_ids:
            # Construir lista de IDs de volúmenes
            target_volume_ids = []
            if volume_id:
                target_volume_ids.append(volume_id)
            if volume_ids:
                target_volume_ids.extend(volume_ids)

            # Obtener solo cómics catalogados de esos volúmenes
            query = query.join(
                ComicbookInfo,
                Comicbook.id_comicbook_info == ComicbookInfo.id_comicbook_info
            ).filter(
                ComicbookInfo.id_volume.in_(target_volume_ids)
            )

        if comicbook_ids:
            query = query.filter(Comicbook.id_comicbook.in_(comicbook_ids))

        comicbooks = query.all()

        for comicbook in comicbooks:
            try:
                plan = self._create_plan_for_comic(comicbook)
                plans.append(plan)
            except Exception as e:
                # Si falla al crear un plan, crear un plan de ERROR
                print(f"ERROR creando plan para cómic ID {comicbook.id_comicbook}: {e}")
                import traceback
                traceback.print_exc()

                error_plan = ComicOrganizationPlan(
                    comicbook_id=comicbook.id_comicbook,
                    current_path=comicbook.path,
                    new_path_relative='',
                    new_path_absolute='',
                    filename_normalized='',
                    status='ERROR',
                    message=f'Error al generar plan: {str(e)}',
                    version=0,
                    volume_id=0,
                    volume_name=""
                )
                plans.append(error_plan)

        # Segundo pase: detectar y resolver duplicados entre los planes
        plans = self._resolve_duplicate_plans(plans)

        return plans

    def _resolve_duplicate_plans(
        self,
        plans: List[ComicOrganizationPlan]
    ) -> List[ComicOrganizationPlan]:
        """
        Detecta y resuelve duplicados entre los planes generados.

        Si múltiples planes tienen el mismo path de destino (mismo nombre de archivo),
        les asigna versiones incrementales.

        Args:
            plans: Lista de planes generados

        Returns:
            Lista de planes con duplicados resueltos
        """
        from collections import defaultdict

        # Agrupar planes por path de destino (sin considerar planes que no se pueden ejecutar)
        path_groups = defaultdict(list)

        for plan in plans:
            # Solo considerar planes que se van a mover
            if plan.status in ['OK', 'DUPLICATE']:
                path_groups[plan.new_path_absolute].append(plan)

        # Procesar grupos con duplicados
        for target_path, duplicate_plans in path_groups.items():
            if len(duplicate_plans) <= 1:
                # No hay duplicados
                continue

            # Hay duplicados, necesitamos versionarlos
            # Verificar qué versiones ya existen en el sistema de archivos
            target_dir = Path(target_path).parent
            base_filename = Path(target_path).name
            existing_versions = self.find_existing_versions(target_dir, base_filename)

            # Determinar desde qué versión empezar
            # Si ya existen archivos, empezamos desde max(existing) + 1
            # Si no existen archivos, el primero es sin versión (0), los demás desde 1
            if existing_versions:
                start_version = max(existing_versions) + 1
                first_needs_version = True
            else:
                start_version = 1
                first_needs_version = False

            # Asignar versiones a cada plan duplicado
            for idx, plan in enumerate(duplicate_plans):
                # Determinar versión para este plan
                if idx == 0 and not first_needs_version:
                    # El primero sin versión (ya está bien como está)
                    continue
                else:
                    # Necesita versión
                    version = start_version + idx if first_needs_version else start_version + idx - 1

                # Regenerar nombre de archivo con versión
                metadata = self.get_comic_metadata(plan.comicbook_id)
                if not metadata:
                    continue

                volume_name = metadata['volume'].nombre
                volume_year = metadata['volume'].anio_inicio
                issue_number = metadata['info'].numero
                publisher_name = metadata['publisher'].nombre if metadata['publisher'] else None

                # Obtener extensión
                _, extension = os.path.splitext(plan.current_path)

                # Generar nombre con versión
                versioned_filename = self.generate_normalized_filename(
                    volume_name=volume_name,
                    issue_number=issue_number,
                    extension=extension,
                    version=version
                )

                # Recalcular paths
                relative_path, absolute_path = self.generate_target_path(
                    publisher_name=publisher_name,
                    volume_name=volume_name,
                    volume_year=volume_year,
                    filename=versioned_filename
                )

                # Actualizar plan
                plan.new_path_relative = relative_path
                plan.new_path_absolute = absolute_path
                plan.filename_normalized = versioned_filename
                plan.status = 'DUPLICATE'
                plan.message = f'Duplicado en el volumen, se creará versión {version:02d}'
                plan.version = version

        return plans

    def _create_plan_for_comic(self, comicbook) -> ComicOrganizationPlan:
        """Crea plan de organización para un cómic específico"""

        # Construir path absoluto actual
        # Si el path es relativo, añadir base_folder
        current_path = comicbook.path
        if not os.path.isabs(current_path):
            current_path = os.path.join(str(self.base_folder), current_path)

        # Obtener metadata
        metadata = self.get_comic_metadata(comicbook.id_comicbook)

        if not metadata:
            # Sin información de catalogación
            return ComicOrganizationPlan(
                comicbook_id=comicbook.id_comicbook,
                current_path=current_path,
                new_path_relative='',
                new_path_absolute='',
                filename_normalized='',
                status='NO_INFO',
                message='Cómic sin catalogar (no tiene ComicbookInfo asociado)',
                version=0,
                volume_id=0,
                volume_name=""
            )

        # Extraer datos
        publisher_name = metadata['publisher'].nombre if metadata['publisher'] else None
        volume_name = metadata['volume'].nombre
        volume_year = metadata['volume'].anio_inicio
        issue_number = metadata['info'].numero

        # Obtener extensión del archivo actual
        # Pero verificar el tipo real del archivo para corregir extensión si es necesario
        _, original_extension = os.path.splitext(comicbook.path)
        extension = self._detect_and_fix_extension(current_path, original_extension)

        # Generar nombre normalizado base (sin versión)
        base_filename = self.generate_normalized_filename(
            volume_name=volume_name,
            issue_number=issue_number,
            extension=extension,
            version=0
        )

        # Generar path de destino base
        relative_path, absolute_path = self.generate_target_path(
            publisher_name=publisher_name,
            volume_name=volume_name,
            volume_year=volume_year,
            filename=base_filename
        )

        # Verificar si ya está en la ubicación correcta
        current_absolute = str(Path(current_path).absolute())
        target_absolute = str(Path(absolute_path).absolute())

        if current_absolute == target_absolute:
            return ComicOrganizationPlan(
                comicbook_id=comicbook.id_comicbook,
                current_path=current_path,
                new_path_relative=relative_path,
                new_path_absolute=absolute_path,
                filename_normalized=base_filename,
                status='ALREADY_IN_PLACE',
                message='Ya está en la ubicación correcta',
                version=0,
                volume_id=metadata['volume'].id_volume,
                volume_name=volume_name
            )

        # Verificar duplicados
        target_dir = Path(absolute_path).parent
        existing_versions = self.find_existing_versions(target_dir, base_filename)

        # Determinar versión y status
        if existing_versions:
            # Hay duplicados, necesitamos versionar
            next_version = max(existing_versions) + 1

            # Generar filename con versión
            versioned_filename = self.generate_normalized_filename(
                volume_name=volume_name,
                issue_number=issue_number,
                extension=extension,
                version=next_version
            )

            # Recalcular paths con versión
            relative_path, absolute_path = self.generate_target_path(
                publisher_name=publisher_name,
                volume_name=volume_name,
                volume_year=volume_year,
                filename=versioned_filename
            )

            return ComicOrganizationPlan(
                comicbook_id=comicbook.id_comicbook,
                current_path=current_path,
                new_path_relative=relative_path,
                new_path_absolute=absolute_path,
                filename_normalized=versioned_filename,
                status='DUPLICATE',
                message=f'Duplicado detectado, se creará versión {next_version:02d}',
                version=next_version,
                volume_id=metadata['volume'].id_volume,
                volume_name=volume_name
            )
        else:
            # No hay duplicados
            return ComicOrganizationPlan(
                comicbook_id=comicbook.id_comicbook,
                current_path=current_path,
                new_path_relative=relative_path,
                new_path_absolute=absolute_path,
                filename_normalized=base_filename,
                status='OK',
                message='Listo para mover',
                version=0,
                volume_id=metadata['volume'].id_volume,
                volume_name=volume_name
            )

    def execute_plan(
        self,
        plan: ComicOrganizationPlan,
        dry_run: bool = False
    ) -> Tuple[bool, str]:
        """
        Ejecuta un plan de reorganización individual.

        Args:
            plan: Plan a ejecutar
            dry_run: Si es True, solo simula sin mover archivos

        Returns:
            Tupla (éxito, mensaje)
        """
        from entidades.comicbook_model import Comicbook

        print(f"\n🔧 DEBUG execute_plan:")
        print(f"  current_path: {plan.current_path}")
        print(f"  new_path_absolute: {plan.new_path_absolute}")
        print(f"  new_path_relative: {plan.new_path_relative}")
        print(f"  status: {plan.status}")

        # Validar estado del plan
        if plan.status in ['NO_INFO', 'ALREADY_IN_PLACE']:
            print(f"  ❌ No se puede ejecutar: {plan.message}")
            return (False, f"No se puede ejecutar: {plan.message}")

        if plan.status == 'ERROR':
            print(f"  ❌ Plan con error: {plan.message}")
            return (False, f"Plan con error: {plan.message}")

        try:
            # Verificar que el archivo actual existe
            current_exists = os.path.exists(plan.current_path)
            print(f"  ¿Existe current_path? {current_exists}")

            if not current_exists:
                print(f"  ❌ Archivo origen no existe: {plan.current_path}")
                return (False, f"Archivo origen no existe: {plan.current_path}")

            if dry_run:
                # Modo simulación
                return (True, f"[DRY RUN] Movería: {plan.current_path} → {plan.new_path_absolute}")

            # Crear directorio de destino si no existe
            target_dir = Path(plan.new_path_absolute).parent
            print(f"  Creando directorio destino: {target_dir}")
            target_dir.mkdir(parents=True, exist_ok=True)

            # Mover archivo
            print(f"  Moviendo archivo...")
            shutil.move(plan.current_path, plan.new_path_absolute)
            print(f"  ✅ Archivo movido exitosamente")

            # Actualizar BD con path ABSOLUTO
            comicbook = self.session.query(Comicbook).filter_by(
                id_comicbook=plan.comicbook_id
            ).first()

            if comicbook:
                print(f"  Actualizando BD con path absoluto: {plan.new_path_absolute}")
                comicbook.path = plan.new_path_absolute
                self.session.commit()
                print(f"  ✅ BD actualizada")

            return (True, f"Movido exitosamente: {plan.filename_normalized}")

        except Exception as e:
            # Revertir transacción en caso de error
            print(f"  ❌ EXCEPCIÓN: {e}")
            import traceback
            traceback.print_exc()
            self.session.rollback()
            return (False, f"Error moviendo archivo: {str(e)}")

    def execute_plans(
        self,
        plans: List[ComicOrganizationPlan],
        dry_run: bool = False,
        progress_callback=None
    ) -> Dict[str, int]:
        """
        Ejecuta múltiples planes de reorganización.

        Args:
            plans: Lista de planes a ejecutar
            dry_run: Si es True, solo simula
            progress_callback: Función a llamar con progreso (plan_index, total, plan, success, message)

        Returns:
            Dict con estadísticas: {'success': N, 'failed': N, 'skipped': N}
        """
        stats = {
            'success': 0,
            'failed': 0,
            'skipped': 0
        }

        total = len(plans)

        for index, plan in enumerate(plans):
            # Saltar planes que no se deben ejecutar
            if plan.status in ['NO_INFO', 'ALREADY_IN_PLACE', 'ERROR']:
                stats['skipped'] += 1
                if progress_callback:
                    progress_callback(index, total, plan, False, plan.message)
                continue

            # Ejecutar plan
            success, message = self.execute_plan(plan, dry_run=dry_run)

            if success:
                stats['success'] += 1
            else:
                stats['failed'] += 1

            # Callback de progreso
            if progress_callback:
                progress_callback(index, total, plan, success, message)

        return stats
