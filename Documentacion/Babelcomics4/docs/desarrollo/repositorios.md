# Repositorios de Datos

Los repositorios en Babelcomics4 implementan el patrón Repository para abstraer el acceso a datos, proporcionando una interfaz limpia y consistente entre la lógica de negocio y la capa de persistencia.

## 🏗️ Arquitectura de Repositorios

### Patrón Repository

#### Clase Base AbstractRepository
```python
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, TypeVar, Generic
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

T = TypeVar('T')

class AbstractRepository(Generic[T], ABC):
    """Repositorio base abstracto"""

    def __init__(self, session: Session, model_class: type):
        self.session = session
        self.model_class = model_class

    @abstractmethod
    def get_by_id(self, entity_id: str) -> Optional[T]:
        """Obtener entidad por ID"""
        pass

    @abstractmethod
    def get_all(self, **filters) -> List[T]:
        """Obtener todas las entidades"""
        pass

    @abstractmethod
    def create(self, entity_data: Dict[str, Any]) -> T:
        """Crear nueva entidad"""
        pass

    @abstractmethod
    def update(self, entity_id: str, updates: Dict[str, Any]) -> Optional[T]:
        """Actualizar entidad existente"""
        pass

    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """Eliminar entidad"""
        pass

    def save(self, entity: T) -> T:
        """Guardar entidad en la sesión"""
        self.session.add(entity)
        return entity

    def flush(self):
        """Flush de la sesión"""
        self.session.flush()

    def commit(self):
        """Commit de la sesión"""
        self.session.commit()

    def rollback(self):
        """Rollback de la sesión"""
        self.session.rollback()

    def refresh(self, entity: T) -> T:
        """Refrescar entidad desde la base de datos"""
        self.session.refresh(entity)
        return entity

class BaseRepository(AbstractRepository[T]):
    """Implementación base del repositorio con funcionalidad común"""

    def get_by_id(self, entity_id: str) -> Optional[T]:
        """Obtener entidad por ID"""
        return self.session.query(self.model_class).filter(
            self.model_class.id == entity_id
        ).first()

    def get_all(self, **filters) -> List[T]:
        """Obtener todas las entidades con filtros opcionales"""
        query = self.session.query(self.model_class)

        for field, value in filters.items():
            if hasattr(self.model_class, field):
                query = query.filter(getattr(self.model_class, field) == value)

        return query.all()

    def create(self, entity_data: Dict[str, Any]) -> T:
        """Crear nueva entidad"""
        entity = self.model_class(**entity_data)
        return self.save(entity)

    def update(self, entity_id: str, updates: Dict[str, Any]) -> Optional[T]:
        """Actualizar entidad existente"""
        entity = self.get_by_id(entity_id)
        if entity:
            for key, value in updates.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
            return entity
        return None

    def delete(self, entity_id: str) -> bool:
        """Eliminar entidad"""
        entity = self.get_by_id(entity_id)
        if entity:
            self.session.delete(entity)
            return True
        return False

    def exists(self, entity_id: str) -> bool:
        """Verificar si existe una entidad"""
        return self.session.query(
            self.session.query(self.model_class).filter(
                self.model_class.id == entity_id
            ).exists()
        ).scalar()

    def count(self, **filters) -> int:
        """Contar entidades con filtros opcionales"""
        query = self.session.query(func.count(self.model_class.id))

        for field, value in filters.items():
            if hasattr(self.model_class, field):
                query = query.filter(getattr(self.model_class, field) == value)

        return query.scalar()

    def paginate(self, page: int = 1, per_page: int = 50, **filters) -> Dict[str, Any]:
        """Paginación de resultados"""
        query = self.session.query(self.model_class)

        # Aplicar filtros
        for field, value in filters.items():
            if hasattr(self.model_class, field):
                query = query.filter(getattr(self.model_class, field) == value)

        # Calcular offset
        offset = (page - 1) * per_page

        # Obtener resultados paginados
        items = query.offset(offset).limit(per_page).all()
        total = query.count()

        return {
            'items': items,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page,
            'has_prev': page > 1,
            'has_next': page * per_page < total
        }
```

## 📚 ComicRepository

### Repositorio Principal de Comics

```python
from models import Comicbook, ComicbookInfo, Volume, Publisher
from sqlalchemy import func, and_, or_, desc, asc
from typing import List, Optional, Dict, Any
import os

class ComicRepository(BaseRepository[Comicbook]):
    """Repositorio para gestión de comics"""

    def __init__(self, session: Session):
        super().__init__(session, Comicbook)

    def get_by_id(self, comic_id: str) -> Optional[Comicbook]:
        """Obtener comic por ID con relaciones cargadas"""
        return self.session.query(Comicbook).filter(
            Comicbook.id_comicbook == comic_id
        ).first()

    def get_by_path(self, path: str) -> Optional[Comicbook]:
        """Obtener comic por ruta de archivo"""
        return self.session.query(Comicbook).filter(
            Comicbook.path == path
        ).first()

    def get_by_filename(self, filename: str) -> List[Comicbook]:
        """Obtener comics por nombre de archivo"""
        return self.session.query(Comicbook).filter(
            Comicbook.filename.ilike(f'%{filename}%')
        ).all()

    def search_comics(
        self,
        search_term: str = None,
        filters: Dict[str, Any] = None,
        sort_by: str = 'filename',
        sort_order: str = 'asc',
        page: int = 1,
        per_page: int = 50
    ) -> Dict[str, Any]:
        """Búsqueda avanzada de comics con filtros y paginación"""

        query = self.session.query(Comicbook).outerjoin(ComicbookInfo).outerjoin(Volume).outerjoin(Publisher)

        # Aplicar búsqueda por texto
        if search_term:
            search_filters = []

            # Búsqueda en campos del comic
            search_filters.extend([
                Comicbook.filename.ilike(f'%{search_term}%'),
                Comicbook.path.ilike(f'%{search_term}%')
            ])

            # Búsqueda en información catalogada
            search_filters.extend([
                ComicbookInfo.titulo.ilike(f'%{search_term}%'),
                Volume.nombre.ilike(f'%{search_term}%'),
                Publisher.nombre.ilike(f'%{search_term}%')
            ])

            query = query.filter(or_(*search_filters))

        # Aplicar filtros específicos
        if filters:
            query = self._apply_filters(query, filters)

        # Aplicar ordenamiento
        query = self._apply_sorting(query, sort_by, sort_order)

        # Calcular paginación
        total = query.count()
        offset = (page - 1) * per_page
        items = query.offset(offset).limit(per_page).all()

        return {
            'items': items,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page,
            'has_prev': page > 1,
            'has_next': page * per_page < total
        }

    def _apply_filters(self, query, filters: Dict[str, Any]):
        """Aplicar filtros específicos a la consulta"""

        # Filtro de clasificación
        if 'classification' in filters:
            if filters['classification'] == 'cataloged':
                query = query.filter(
                    and_(
                        Comicbook.id_comicbook_info.isnot(None),
                        Comicbook.id_comicbook_info != ''
                    )
                )
            elif filters['classification'] == 'uncataloged':
                query = query.filter(
                    or_(
                        Comicbook.id_comicbook_info.is_(None),
                        Comicbook.id_comicbook_info == ''
                    )
                )

        # Filtro de calidad
        if 'quality_range' in filters:
            min_quality, max_quality = filters['quality_range']
            query = query.filter(
                and_(
                    Comicbook.calidad >= min_quality,
                    Comicbook.calidad <= max_quality
                )
            )

        # Filtro de papelera
        if 'include_trash' not in filters or not filters['include_trash']:
            query = query.filter(Comicbook.en_papelera == False)

        # Filtro de tamaño de archivo
        if 'size_range' in filters:
            min_size_mb, max_size_mb = filters['size_range']
            min_bytes = min_size_mb * 1024 * 1024
            max_bytes = max_size_mb * 1024 * 1024
            query = query.filter(
                and_(
                    Comicbook.tamaño >= min_bytes,
                    Comicbook.tamaño <= max_bytes
                )
            )

        # Filtro por editorial
        if 'publishers' in filters and filters['publishers']:
            query = query.filter(Publisher.nombre.in_(filters['publishers']))

        # Filtro por año
        if 'year_range' in filters:
            start_year, end_year = filters['year_range']
            query = query.filter(
                and_(
                    ComicbookInfo.fecha_tapa >= f'{start_year}-01-01',
                    ComicbookInfo.fecha_tapa <= f'{end_year}-12-31'
                )
            )

        # Filtro por formato de archivo
        if 'file_formats' in filters and filters['file_formats']:
            format_filters = []
            for fmt in filters['file_formats']:
                format_filters.append(Comicbook.filename.ilike(f'%.{fmt}'))
            query = query.filter(or_(*format_filters))

        # Filtro por copias físicas
        if 'has_physical_copies' in filters:
            if filters['has_physical_copies']:
                query = query.filter(Comicbook.cantidad_adquirida > 0)
            else:
                query = query.filter(Comicbook.cantidad_adquirida == 0)

        return query

    def _apply_sorting(self, query, sort_by: str, sort_order: str):
        """Aplicar ordenamiento a la consulta"""

        sort_column = None

        # Mapeo de campos de ordenamiento
        if sort_by == 'filename':
            sort_column = Comicbook.filename
        elif sort_by == 'size':
            sort_column = Comicbook.tamaño
        elif sort_by == 'quality':
            sort_column = Comicbook.calidad
        elif sort_by == 'date_added':
            sort_column = Comicbook.fecha_agregado
        elif sort_by == 'title':
            sort_column = ComicbookInfo.titulo
        elif sort_by == 'cover_date':
            sort_column = ComicbookInfo.fecha_tapa
        elif sort_by == 'publisher':
            sort_column = Publisher.nombre
        elif sort_by == 'volume':
            sort_column = Volume.nombre

        if sort_column is not None:
            if sort_order.lower() == 'desc':
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))

        return query

    def get_uncataloged_comics(self) -> List[Comicbook]:
        """Obtener comics sin catalogar"""
        return self.session.query(Comicbook).filter(
            or_(
                Comicbook.id_comicbook_info.is_(None),
                Comicbook.id_comicbook_info == ''
            ),
            Comicbook.en_papelera == False
        ).all()

    def get_comics_by_volume(self, volume_id: str) -> List[Comicbook]:
        """Obtener comics de un volumen específico"""
        return self.session.query(Comicbook).join(ComicbookInfo).filter(
            ComicbookInfo.id_volume == volume_id
        ).all()

    def get_comics_by_publisher(self, publisher_id: str) -> List[Comicbook]:
        """Obtener comics de una editorial específica"""
        return self.session.query(Comicbook).join(ComicbookInfo).join(Volume).filter(
            Volume.id_publisher == publisher_id
        ).all()

    def get_recently_added(self, days: int = 7, limit: int = 50) -> List[Comicbook]:
        """Obtener comics agregados recientemente"""
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        return self.session.query(Comicbook).filter(
            Comicbook.fecha_agregado >= cutoff_date,
            Comicbook.en_papelera == False
        ).order_by(desc(Comicbook.fecha_agregado)).limit(limit).all()

    def get_high_quality_comics(self, min_quality: int = 4) -> List[Comicbook]:
        """Obtener comics de alta calidad"""
        return self.session.query(Comicbook).filter(
            Comicbook.calidad >= min_quality,
            Comicbook.en_papelera == False
        ).order_by(desc(Comicbook.calidad)).all()

    def get_collection_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas completas de la colección"""

        # Conteos básicos
        total_comics = self.session.query(func.count(Comicbook.id_comicbook)).scalar()

        cataloged_comics = self.session.query(func.count(Comicbook.id_comicbook)).filter(
            and_(
                Comicbook.id_comicbook_info.isnot(None),
                Comicbook.id_comicbook_info != ''
            )
        ).scalar()

        trash_comics = self.session.query(func.count(Comicbook.id_comicbook)).filter(
            Comicbook.en_papelera == True
        ).scalar()

        # Distribución por calidad
        quality_distribution = dict(
            self.session.query(
                Comicbook.calidad,
                func.count(Comicbook.id_comicbook)
            ).group_by(Comicbook.calidad).all()
        )

        # Distribución por formato
        format_distribution = dict(
            self.session.query(
                func.substr(Comicbook.filename, func.instr(Comicbook.filename, '.') + 1),
                func.count(Comicbook.id_comicbook)
            ).group_by(
                func.substr(Comicbook.filename, func.instr(Comicbook.filename, '.') + 1)
            ).all()
        )

        # Tamaño total
        total_size = self.session.query(func.sum(Comicbook.tamaño)).scalar() or 0

        # Distribución por editorial
        publisher_distribution = dict(
            self.session.query(
                Publisher.nombre,
                func.count(Comicbook.id_comicbook)
            ).join(ComicbookInfo).join(Volume).join(Publisher).group_by(
                Publisher.nombre
            ).all()
        )

        return {
            'total_comics': total_comics,
            'cataloged_comics': cataloged_comics,
            'uncataloged_comics': total_comics - cataloged_comics,
            'trash_comics': trash_comics,
            'active_comics': total_comics - trash_comics,
            'catalog_percentage': round((cataloged_comics / total_comics) * 100, 1) if total_comics > 0 else 0,
            'quality_distribution': quality_distribution,
            'format_distribution': format_distribution,
            'publisher_distribution': publisher_distribution,
            'total_size_bytes': total_size,
            'total_size_gb': round(total_size / (1024**3), 2),
            'average_file_size_mb': round((total_size / total_comics) / (1024**2), 2) if total_comics > 0 else 0
        }

    def find_duplicates(self) -> List[Dict[str, Any]]:
        """Encontrar comics duplicados por checksum o nombre"""

        duplicates = []

        # Duplicados por checksum
        checksum_duplicates = self.session.query(
            Comicbook.checksum,
            func.count(Comicbook.id_comicbook).label('count')
        ).filter(
            Comicbook.checksum.isnot(None),
            Comicbook.en_papelera == False
        ).group_by(Comicbook.checksum).having(
            func.count(Comicbook.id_comicbook) > 1
        ).all()

        for checksum, count in checksum_duplicates:
            comics = self.session.query(Comicbook).filter(
                Comicbook.checksum == checksum
            ).all()

            duplicates.append({
                'type': 'checksum',
                'identifier': checksum,
                'count': count,
                'comics': comics
            })

        # Duplicados por nombre de archivo
        filename_duplicates = self.session.query(
            Comicbook.filename,
            func.count(Comicbook.id_comicbook).label('count')
        ).filter(
            Comicbook.en_papelera == False
        ).group_by(Comicbook.filename).having(
            func.count(Comicbook.id_comicbook) > 1
        ).all()

        for filename, count in filename_duplicates:
            comics = self.session.query(Comicbook).filter(
                Comicbook.filename == filename
            ).all()

            # Verificar que no sean el mismo archivo (diferentes rutas)
            paths = set(comic.path for comic in comics)
            if len(paths) > 1:
                duplicates.append({
                    'type': 'filename',
                    'identifier': filename,
                    'count': count,
                    'comics': comics
                })

        return duplicates

    def verify_file_integrity(self) -> Dict[str, List[Comicbook]]:
        """Verificar integridad de archivos"""

        results = {
            'missing_files': [],
            'corrupted_files': [],
            'checksum_mismatches': [],
            'valid_files': []
        }

        comics = self.get_all(en_papelera=False)

        for comic in comics:
            if not comic.file_exists:
                results['missing_files'].append(comic)
                continue

            validation = comic.validate_file()

            if not validation['exists']:
                results['missing_files'].append(comic)
            elif not validation['readable']:
                results['corrupted_files'].append(comic)
            elif not validation['checksum_valid']:
                results['checksum_mismatches'].append(comic)
            else:
                results['valid_files'].append(comic)

        return results

    def bulk_update_quality(self, comic_ids: List[str], quality: int) -> int:
        """Actualización masiva de calidad"""
        updated = self.session.query(Comicbook).filter(
            Comicbook.id_comicbook.in_(comic_ids)
        ).update(
            {Comicbook.calidad: quality},
            synchronize_session=False
        )
        return updated

    def bulk_move_to_trash(self, comic_ids: List[str]) -> int:
        """Mover múltiples comics a papelera"""
        updated = self.session.query(Comicbook).filter(
            Comicbook.id_comicbook.in_(comic_ids)
        ).update(
            {Comicbook.en_papelera: True},
            synchronize_session=False
        )
        return updated

    def bulk_restore_from_trash(self, comic_ids: List[str]) -> int:
        """Restaurar múltiples comics de papelera"""
        updated = self.session.query(Comicbook).filter(
            Comicbook.id_comicbook.in_(comic_ids)
        ).update(
            {Comicbook.en_papelera: False},
            synchronize_session=False
        )
        return updated

    def create_from_file_scan(self, file_path: str) -> Optional[Comicbook]:
        """Crear comic desde escaneo de archivo"""
        import os

        if not os.path.exists(file_path):
            return None

        # Verificar si ya existe
        existing = self.get_by_path(file_path)
        if existing:
            return existing

        # Crear nuevo comic
        comic_data = {
            'path': file_path,
            'filename': os.path.basename(file_path),
            'tamaño': os.path.getsize(file_path)
        }

        comic = self.create(comic_data)

        # Calcular checksum en background
        comic.calculate_checksum()

        return comic
```

## 📖 VolumeRepository

### Repositorio de Volúmenes

```python
class VolumeRepository(BaseRepository[Volume]):
    """Repositorio para gestión de volúmenes"""

    def __init__(self, session: Session):
        super().__init__(session, Volume)

    def get_by_id(self, volume_id: str) -> Optional[Volume]:
        """Obtener volumen por ID"""
        return self.session.query(Volume).filter(
            Volume.id_volume == volume_id
        ).first()

    def get_by_comicvine_id(self, comicvine_id: int) -> Optional[Volume]:
        """Obtener volumen por ID de ComicVine"""
        return self.session.query(Volume).filter(
            Volume.id_comicvine == comicvine_id
        ).first()

    def search_volumes(
        self,
        search_term: str = None,
        publisher_id: str = None,
        year_range: tuple = None,
        completion_filter: str = None,
        sort_by: str = 'nombre',
        sort_order: str = 'asc'
    ) -> List[Volume]:
        """Búsqueda avanzada de volúmenes"""

        query = self.session.query(Volume).outerjoin(Publisher)

        # Búsqueda por texto
        if search_term:
            query = query.filter(
                or_(
                    Volume.nombre.ilike(f'%{search_term}%'),
                    Publisher.nombre.ilike(f'%{search_term}%')
                )
            )

        # Filtro por editorial
        if publisher_id:
            query = query.filter(Volume.id_publisher == publisher_id)

        # Filtro por rango de años
        if year_range:
            start_year, end_year = year_range
            query = query.filter(
                and_(
                    Volume.anio_inicio >= start_year,
                    Volume.anio_inicio <= end_year
                )
            )

        # Aplicar ordenamiento
        if sort_by == 'nombre':
            sort_column = Volume.nombre
        elif sort_by == 'year':
            sort_column = Volume.anio_inicio
        elif sort_by == 'publisher':
            sort_column = Publisher.nombre
        elif sort_by == 'completion':
            # Ordenar por porcentaje de completitud requiere cálculo
            sort_column = Volume.nombre  # Fallback
        else:
            sort_column = Volume.nombre

        if sort_order.lower() == 'desc':
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        volumes = query.all()

        # Filtrar por completitud después de cargar (si es necesario)
        if completion_filter:
            filtered_volumes = []
            for volume in volumes:
                completion = volume.completion_percentage

                if completion_filter == 'complete' and completion >= 100:
                    filtered_volumes.append(volume)
                elif completion_filter == 'nearly_complete' and 80 <= completion < 100:
                    filtered_volumes.append(volume)
                elif completion_filter == 'in_progress' and 20 <= completion < 80:
                    filtered_volumes.append(volume)
                elif completion_filter == 'started' and 1 <= completion < 20:
                    filtered_volumes.append(volume)
                elif completion_filter == 'empty' and completion == 0:
                    filtered_volumes.append(volume)

            volumes = filtered_volumes

        return volumes

    def get_volumes_by_publisher(self, publisher_id: str) -> List[Volume]:
        """Obtener volúmenes de una editorial"""
        return self.session.query(Volume).filter(
            Volume.id_publisher == publisher_id
        ).order_by(Volume.nombre).all()

    def get_complete_volumes(self) -> List[Volume]:
        """Obtener volúmenes completos en la colección"""
        volumes = self.get_all()
        return [vol for vol in volumes if vol.is_complete]

    def get_ongoing_volumes(self) -> List[Volume]:
        """Obtener volúmenes en curso"""
        return self.session.query(Volume).filter(
            Volume.estado == 'ongoing'
        ).all()

    def get_volume_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas de volúmenes"""

        total_volumes = self.count()

        # Conteo por estado
        status_counts = dict(
            self.session.query(
                Volume.estado,
                func.count(Volume.id_volume)
            ).group_by(Volume.estado).all()
        )

        # Conteo por tipo
        type_counts = dict(
            self.session.query(
                Volume.tipo,
                func.count(Volume.id_volume)
            ).group_by(Volume.tipo).all()
        )

        # Distribución por década
        decade_counts = dict(
            self.session.query(
                func.floor(Volume.anio_inicio / 10) * 10,
                func.count(Volume.id_volume)
            ).filter(
                Volume.anio_inicio.isnot(None)
            ).group_by(
                func.floor(Volume.anio_inicio / 10) * 10
            ).all()
        )

        # Estadísticas de completitud
        volumes = self.get_all()
        completion_stats = {
            'complete': 0,
            'nearly_complete': 0,
            'in_progress': 0,
            'started': 0,
            'empty': 0
        }

        total_completion = 0
        for volume in volumes:
            completion = volume.completion_percentage
            total_completion += completion

            if completion >= 100:
                completion_stats['complete'] += 1
            elif completion >= 80:
                completion_stats['nearly_complete'] += 1
            elif completion >= 20:
                completion_stats['in_progress'] += 1
            elif completion > 0:
                completion_stats['started'] += 1
            else:
                completion_stats['empty'] += 1

        average_completion = total_completion / total_volumes if total_volumes > 0 else 0

        return {
            'total_volumes': total_volumes,
            'status_distribution': status_counts,
            'type_distribution': type_counts,
            'decade_distribution': decade_counts,
            'completion_distribution': completion_stats,
            'average_completion': round(average_completion, 1)
        }

    def find_volumes_needing_update(self, days_threshold: int = 30) -> List[Volume]:
        """Encontrar volúmenes que necesitan actualización"""
        from datetime import datetime, timedelta

        threshold_date = datetime.utcnow() - timedelta(days=days_threshold)

        return self.session.query(Volume).filter(
            or_(
                Volume.ultima_sync_comicvine.is_(None),
                Volume.ultima_sync_comicvine < threshold_date
            ),
            Volume.id_comicvine.isnot(None)
        ).all()

    def get_volumes_with_gaps(self) -> List[Dict[str, Any]]:
        """Obtener volúmenes con gaps en la colección"""
        volumes_with_gaps = []

        volumes = self.session.query(Volume).filter(
            Volume.cantidad_numeros > 0
        ).all()

        for volume in volumes:
            gaps = volume.find_gaps_in_collection()
            if gaps:
                volumes_with_gaps.append({
                    'volume': volume,
                    'gaps': gaps,
                    'total_missing': sum(gap['size'] for gap in gaps)
                })

        return volumes_with_gaps

    def update_volume_statistics(self, volume_id: str = None):
        """Actualizar estadísticas de volúmenes"""
        if volume_id:
            volumes = [self.get_by_id(volume_id)]
        else:
            volumes = self.get_all()

        for volume in volumes:
            if volume:
                # Recalcular cantidad de issues
                issue_count = self.session.query(func.count(ComicbookInfo.id_comicbook_info)).filter(
                    ComicbookInfo.id_volume == volume.id_volume
                ).scalar()

                volume.cantidad_numeros = issue_count
                volume.updated_at = datetime.utcnow()
```

## 🏢 PublisherRepository

### Repositorio de Editoriales

```python
class PublisherRepository(BaseRepository[Publisher]):
    """Repositorio para gestión de editoriales"""

    def __init__(self, session: Session):
        super().__init__(session, Publisher)

    def get_by_id(self, publisher_id: str) -> Optional[Publisher]:
        """Obtener editorial por ID"""
        return self.session.query(Publisher).filter(
            Publisher.id_publisher == publisher_id
        ).first()

    def get_by_name(self, name: str) -> Optional[Publisher]:
        """Obtener editorial por nombre"""
        return self.session.query(Publisher).filter(
            Publisher.nombre.ilike(name)
        ).first()

    def get_by_comicvine_id(self, comicvine_id: int) -> Optional[Publisher]:
        """Obtener editorial por ID de ComicVine"""
        return self.session.query(Publisher).filter(
            Publisher.id_comicvine == comicvine_id
        ).first()

    def get_all_with_stats(self) -> List[Dict[str, Any]]:
        """Obtener todas las editoriales con estadísticas"""
        publishers = self.get_all()

        publishers_with_stats = []
        for publisher in publishers:
            volume_count = len(publisher.volumes)
            comic_count = sum(
                len(volume.issues) for volume in publisher.volumes
            )

            publishers_with_stats.append({
                'publisher': publisher,
                'volume_count': volume_count,
                'comic_count': comic_count,
                'completion_percentage': self._calculate_publisher_completion(publisher)
            })

        return publishers_with_stats

    def _calculate_publisher_completion(self, publisher: Publisher) -> float:
        """Calcular porcentaje de completitud de una editorial"""
        if not publisher.volumes:
            return 0.0

        total_completion = sum(
            volume.completion_percentage for volume in publisher.volumes
        )
        return round(total_completion / len(publisher.volumes), 1)

    def get_top_publishers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtener top editoriales por número de comics"""
        results = self.session.query(
            Publisher,
            func.count(Comicbook.id_comicbook).label('comic_count')
        ).join(Volume).join(ComicbookInfo).join(Comicbook).filter(
            Comicbook.en_papelera == False
        ).group_by(Publisher.id_publisher).order_by(
            desc('comic_count')
        ).limit(limit).all()

        return [
            {
                'publisher': publisher,
                'comic_count': comic_count
            }
            for publisher, comic_count in results
        ]

    def search_publishers(self, search_term: str) -> List[Publisher]:
        """Buscar editoriales por nombre"""
        return self.session.query(Publisher).filter(
            Publisher.nombre.ilike(f'%{search_term}%')
        ).order_by(Publisher.nombre).all()

    def get_or_create_publisher(self, name: str, comicvine_id: int = None) -> Publisher:
        """Obtener o crear editorial"""
        # Buscar por ComicVine ID primero
        if comicvine_id:
            publisher = self.get_by_comicvine_id(comicvine_id)
            if publisher:
                return publisher

        # Buscar por nombre
        publisher = self.get_by_name(name)
        if publisher:
            # Actualizar ComicVine ID si no lo tiene
            if comicvine_id and not publisher.id_comicvine:
                publisher.id_comicvine = comicvine_id
            return publisher

        # Crear nueva editorial
        publisher_data = {
            'nombre': name,
            'id_comicvine': comicvine_id
        }

        return self.create(publisher_data)
```

---

**¿Quieres conocer más sobre la API de ComicVine?** 👉 [API ComicVine](api-comicvine.md)