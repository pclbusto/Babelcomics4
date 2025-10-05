# API ComicVine

Babelcomics4 integra con la API oficial de ComicVine para obtener metadatos completos de comics, volúmenes, editoriales y personajes, proporcionando catalogación automática y enriquecimiento de información.

## 🌐 Integración con ComicVine

### Cliente API Principal

#### ComicVineClient
```python
import requests
import time
import json
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlencode
from dataclasses import dataclass
import logging

@dataclass
class ComicVineConfig:
    """Configuración del cliente ComicVine"""
    api_key: str
    base_url: str = "https://comicvine.gamespot.com/api/"
    user_agent: str = "Babelcomics4/1.0"
    requests_per_hour: int = 200
    request_delay: float = 0.5
    timeout: int = 30
    retries: int = 3
    cache_enabled: bool = True
    cache_ttl: int = 3600  # 1 hora

class ComicVineClient:
    """Cliente para la API de ComicVine"""

    def __init__(self, config: ComicVineConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.user_agent,
            'Accept': 'application/json'
        })

        # Control de rate limiting
        self.request_timestamps = []
        self.last_request_time = 0

        # Cache simple en memoria
        self.cache = {}

        # Logger
        self.logger = logging.getLogger(__name__)

    def _wait_for_rate_limit(self):
        """Esperar para respetar rate limiting"""
        current_time = time.time()

        # Limpiar timestamps antiguos (más de 1 hora)
        hour_ago = current_time - 3600
        self.request_timestamps = [
            ts for ts in self.request_timestamps if ts > hour_ago
        ]

        # Verificar si hemos excedido el límite
        if len(self.request_timestamps) >= self.config.requests_per_hour:
            sleep_time = 3600 - (current_time - self.request_timestamps[0])
            if sleep_time > 0:
                self.logger.info(f"Rate limit reached, sleeping for {sleep_time:.1f} seconds")
                time.sleep(sleep_time)

        # Esperar delay mínimo entre requests
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.config.request_delay:
            time.sleep(self.config.request_delay - time_since_last)

    def _make_request(
        self,
        endpoint: str,
        params: Dict[str, Any] = None,
        use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Realizar petición a la API con rate limiting y cache"""

        # Preparar parámetros
        params = params or {}
        params.update({
            'api_key': self.config.api_key,
            'format': 'json'
        })

        # Generar clave de cache
        cache_key = f"{endpoint}:{urlencode(sorted(params.items()))}"

        # Verificar cache
        if use_cache and self.config.cache_enabled and cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.config.cache_ttl:
                return cached_data

        # Rate limiting
        self._wait_for_rate_limit()

        # Construir URL
        url = urljoin(self.config.base_url, endpoint)

        # Realizar petición con reintentos
        for attempt in range(self.config.retries):
            try:
                current_time = time.time()
                self.request_timestamps.append(current_time)
                self.last_request_time = current_time

                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.config.timeout
                )

                response.raise_for_status()
                data = response.json()

                # Verificar respuesta de ComicVine
                if data.get('status_code') != 1:
                    error_msg = data.get('error', 'Unknown ComicVine API error')
                    self.logger.error(f"ComicVine API error: {error_msg}")
                    return None

                # Guardar en cache
                if self.config.cache_enabled:
                    self.cache[cache_key] = (data, current_time)

                return data

            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Request attempt {attempt + 1} failed: {e}")
                if attempt < self.config.retries - 1:
                    time.sleep(2 ** attempt)  # Backoff exponencial
                else:
                    self.logger.error(f"All {self.config.retries} attempts failed for {url}")
                    return None

        return None

    def search_volumes(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Buscar volúmenes por nombre"""

        params = {
            'query': query,
            'resources': 'volume',
            'limit': limit,
            'offset': offset,
            'field_list': 'id,name,start_year,publisher,count_of_issues,image,description'
        }

        response = self._make_request('search/', params)
        if response and 'results' in response:
            return response['results']

        return []

    def get_volume_details(self, volume_id: int) -> Optional[Dict[str, Any]]:
        """Obtener detalles completos de un volumen"""

        params = {
            'field_list': 'id,name,start_year,description,count_of_issues,publisher,image,site_detail_url'
        }

        response = self._make_request(f'volume/4000-{volume_id}/', params)
        if response and 'results' in response:
            return response['results']

        return None

    def get_volume_issues(
        self,
        volume_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Obtener issues de un volumen"""

        params = {
            'filter': f'volume:{volume_id}',
            'limit': limit,
            'offset': offset,
            'sort': 'issue_number:asc',
            'field_list': 'id,name,issue_number,cover_date,store_date,description,image,site_detail_url'
        }

        response = self._make_request('issues/', params)
        if response and 'results' in response:
            return response['results']

        return []

    def get_issue_details(self, issue_id: int) -> Optional[Dict[str, Any]]:
        """Obtener detalles completos de un issue"""

        params = {
            'field_list': 'id,name,issue_number,cover_date,store_date,description,volume,character_credits,person_credits,image,site_detail_url'
        }

        response = self._make_request(f'issue/4000-{issue_id}/', params)
        if response and 'results' in response:
            return response['results']

        return None

    def search_issues(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0,
        volume_id: int = None
    ) -> List[Dict[str, Any]]:
        """Buscar issues específicos"""

        params = {
            'query': query,
            'resources': 'issue',
            'limit': limit,
            'offset': offset,
            'field_list': 'id,name,issue_number,cover_date,volume,image,description'
        }

        if volume_id:
            params['filter'] = f'volume:{volume_id}'

        response = self._make_request('search/', params)
        if response and 'results' in response:
            return response['results']

        return []

    def get_publisher_details(self, publisher_id: int) -> Optional[Dict[str, Any]]:
        """Obtener detalles de una editorial"""

        params = {
            'field_list': 'id,name,description,location_address,location_city,location_state'
        }

        response = self._make_request(f'publisher/4010-{publisher_id}/', params)
        if response and 'results' in response:
            return response['results']

        return None

    def search_publishers(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Buscar editoriales"""

        params = {
            'query': query,
            'resources': 'publisher',
            'limit': limit,
            'field_list': 'id,name,description'
        }

        response = self._make_request('search/', params)
        if response and 'results' in response:
            return response['results']

        return []

    def get_character_details(self, character_id: int) -> Optional[Dict[str, Any]]:
        """Obtener detalles de un personaje"""

        params = {
            'field_list': 'id,name,description,real_name,aliases,birth,gender,origin,powers,image'
        }

        response = self._make_request(f'character/4005-{character_id}/', params)
        if response and 'results' in response:
            return response['results']

        return None

    def get_person_details(self, person_id: int) -> Optional[Dict[str, Any]]:
        """Obtener detalles de una persona (creador)"""

        params = {
            'field_list': 'id,name,description,birth,death,hometown,image'
        }

        response = self._make_request(f'person/4040-{person_id}/', params)
        if response and 'results' in response:
            return response['results']

        return None

    def clear_cache(self):
        """Limpiar cache"""
        self.cache.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del cache"""
        current_time = time.time()
        valid_entries = 0
        expired_entries = 0

        for cache_key, (data, timestamp) in self.cache.items():
            if current_time - timestamp < self.config.cache_ttl:
                valid_entries += 1
            else:
                expired_entries += 1

        return {
            'total_entries': len(self.cache),
            'valid_entries': valid_entries,
            'expired_entries': expired_entries,
            'hit_ratio': getattr(self, '_cache_hits', 0) / getattr(self, '_cache_requests', 1)
        }
```

### Servicios de Catalogación

#### ComicVineCatalogService
```python
from models import Comicbook, ComicbookInfo, Volume, Publisher, Person, Character
from repositories import ComicRepository, VolumeRepository, PublisherRepository
from sqlalchemy.orm import Session
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class ComicVineCatalogService:
    """Servicio de catalogación usando ComicVine"""

    def __init__(
        self,
        session: Session,
        comicvine_client: ComicVineClient,
        comic_repo: ComicRepository,
        volume_repo: VolumeRepository,
        publisher_repo: PublisherRepository
    ):
        self.session = session
        self.cv_client = comicvine_client
        self.comic_repo = comic_repo
        self.volume_repo = volume_repo
        self.publisher_repo = publisher_repo
        self.logger = logging.getLogger(__name__)

    def catalog_comic_from_filename(
        self,
        comic: Comicbook,
        confidence_threshold: float = 0.7
    ) -> Optional[ComicbookInfo]:
        """Catalogar comic basándose en el nombre del archivo"""

        # Extraer metadatos del filename
        metadata = self._extract_metadata_from_filename(comic.filename)
        if not metadata.get('series') or not metadata.get('issue_number'):
            return None

        # Buscar volúmenes candidatos
        volume_candidates = self._find_volume_candidates(metadata)
        if not volume_candidates:
            return None

        # Buscar issue específico en cada volumen candidato
        best_match = None
        best_confidence = 0

        for volume in volume_candidates:
            match_result = self._find_issue_in_volume(volume, metadata)
            if match_result and match_result['confidence'] > best_confidence:
                best_match = match_result
                best_confidence = match_result['confidence']

        # Verificar confianza mínima
        if best_confidence < confidence_threshold:
            self.logger.info(
                f"No se encontró coincidencia suficiente para {comic.filename} "
                f"(mejor confianza: {best_confidence:.2f})"
            )
            return None

        # Crear ComicbookInfo
        comic_info = self._create_comicbook_info_from_match(best_match)
        if comic_info:
            # Asociar con el comic físico
            comic.id_comicbook_info = comic_info.id_comicbook_info
            comic_info.owned_comics.append(comic)

            self.session.add(comic_info)
            self.session.flush()

        return comic_info

    def _extract_metadata_from_filename(self, filename: str) -> Dict[str, Any]:
        """Extraer metadatos del nombre de archivo usando regex"""

        # Patrones de regex para diferentes formatos de nombre
        patterns = [
            # Pattern: "Series Name #123 (2018).cbz"
            r'^(?P<series>.+?)\s*#(?P<issue_number>\d+(?:\.\d+)?)\s*\((?P<year>\d{4})\)',

            # Pattern: "Series Name - Issue 123 - Title.cbz"
            r'^(?P<series>.+?)\s*-\s*Issue\s*(?P<issue_number>\d+(?:\.\d+)?)\s*-\s*(?P<title>.+)',

            # Pattern: "Series_Name_123_Title.cbz"
            r'^(?P<series>.+?)_(?P<issue_number>\d+(?:\.\d+)?)_(?P<title>.+)',

            # Pattern: "SeriesName123.cbz"
            r'^(?P<series>[A-Za-z\s]+?)(?P<issue_number>\d+(?:\.\d+)?)$',

            # Pattern: "Series Name v2 #123.cbz"
            r'^(?P<series>.+?)\s*v(?P<volume>\d+)\s*#(?P<issue_number>\d+(?:\.\d+)?)',

            # Pattern: "Series Name 123 (Publisher, Year).cbz"
            r'^(?P<series>.+?)\s*(?P<issue_number>\d+(?:\.\d+)?)\s*\((?P<publisher>.+?),\s*(?P<year>\d{4})\)'
        ]

        # Remover extensión
        basename = re.sub(r'\.[^.]+$', '', filename)

        metadata = {
            'series': None,
            'issue_number': None,
            'year': None,
            'title': None,
            'volume': None,
            'publisher': None
        }

        # Intentar cada patrón
        for pattern in patterns:
            match = re.match(pattern, basename, re.IGNORECASE)
            if match:
                groups = match.groupdict()

                # Limpiar y procesar los grupos capturados
                if 'series' in groups and groups['series']:
                    metadata['series'] = self._clean_series_name(groups['series'])

                if 'issue_number' in groups and groups['issue_number']:
                    metadata['issue_number'] = groups['issue_number']

                if 'year' in groups and groups['year']:
                    metadata['year'] = int(groups['year'])

                if 'title' in groups and groups['title']:
                    metadata['title'] = self._clean_title(groups['title'])

                if 'volume' in groups and groups['volume']:
                    metadata['volume'] = int(groups['volume'])

                if 'publisher' in groups and groups['publisher']:
                    metadata['publisher'] = groups['publisher'].strip()

                break

        return metadata

    def _clean_series_name(self, series: str) -> str:
        """Limpiar nombre de serie"""
        # Reemplazar guiones bajos y puntos con espacios
        cleaned = re.sub(r'[_.]', ' ', series)

        # Remover caracteres especiales extras
        cleaned = re.sub(r'[^\w\s\-&]', '', cleaned)

        # Normalizar espacios
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        # Capitalizar apropiadamente
        words = cleaned.split()
        capitalized_words = []

        for word in words:
            # No capitalizar artículos y preposiciones comunes (excepto si es la primera palabra)
            if word.lower() in ['the', 'a', 'an', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'for'] and len(capitalized_words) > 0:
                capitalized_words.append(word.lower())
            else:
                capitalized_words.append(word.capitalize())

        return ' '.join(capitalized_words)

    def _clean_title(self, title: str) -> str:
        """Limpiar título del issue"""
        # Similar al series name pero más permisivo
        cleaned = re.sub(r'[_.]', ' ', title)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned

    def _find_volume_candidates(
        self,
        metadata: Dict[str, Any],
        max_candidates: int = 5
    ) -> List[Dict[str, Any]]:
        """Encontrar volúmenes candidatos en ComicVine"""

        series_name = metadata.get('series')
        if not series_name:
            return []

        # Buscar en ComicVine
        search_results = self.cv_client.search_volumes(
            query=series_name,
            limit=max_candidates * 2  # Buscar más para filtrar después
        )

        candidates = []

        for result in search_results:
            # Calcular similitud de nombre
            name_similarity = self._calculate_string_similarity(
                series_name.lower(),
                result.get('name', '').lower()
            )

            # Filtrar por similitud mínima
            if name_similarity < 0.5:
                continue

            # Calcular score del candidato
            score = name_similarity

            # Bonus por año coincidente
            if metadata.get('year') and result.get('start_year'):
                year_diff = abs(metadata['year'] - result['start_year'])
                if year_diff <= 2:  # Tolerancia de 2 años
                    score += 0.2 * (1 - year_diff / 2)

            # Bonus por editorial conocida
            publisher = result.get('publisher', {})
            if publisher and publisher.get('name'):
                publisher_name = publisher['name'].lower()
                if any(major in publisher_name for major in ['dc', 'marvel', 'image', 'dark horse']):
                    score += 0.1

            candidates.append({
                'volume_data': result,
                'name_similarity': name_similarity,
                'score': score
            })

        # Ordenar por score y devolver top candidatos
        candidates.sort(key=lambda x: x['score'], reverse=True)
        return candidates[:max_candidates]

    def _find_issue_in_volume(
        self,
        volume_candidate: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Buscar issue específico en un volumen"""

        volume_data = volume_candidate['volume_data']
        volume_id = volume_data.get('id')

        if not volume_id:
            return None

        # Obtener issues del volumen
        issues = self.cv_client.get_volume_issues(volume_id, limit=200)

        target_issue_number = metadata.get('issue_number')
        if not target_issue_number:
            return None

        # Buscar issue coincidente
        for issue in issues:
            issue_number = issue.get('issue_number')
            if not issue_number:
                continue

            # Comparar números de issue
            if self._compare_issue_numbers(target_issue_number, issue_number):
                # Calcular confianza total
                confidence = volume_candidate['score']

                # Bonus por coincidencia exacta de número
                if target_issue_number == issue_number:
                    confidence += 0.2

                # Bonus por fecha cercana si disponible
                if metadata.get('year') and issue.get('cover_date'):
                    issue_year = self._extract_year_from_date(issue['cover_date'])
                    if issue_year and abs(metadata['year'] - issue_year) <= 1:
                        confidence += 0.1

                return {
                    'volume_data': volume_data,
                    'issue_data': issue,
                    'confidence': min(confidence, 1.0),
                    'metadata': metadata
                }

        return None

    def _compare_issue_numbers(self, target: str, candidate: str) -> bool:
        """Comparar números de issue con tolerancia"""
        try:
            target_num = float(target)
            candidate_num = float(candidate)
            return abs(target_num - candidate_num) < 0.1
        except (ValueError, TypeError):
            # Fallback a comparación de string
            return target.lower() == candidate.lower()

    def _extract_year_from_date(self, date_str: str) -> Optional[int]:
        """Extraer año de string de fecha"""
        if not date_str:
            return None

        try:
            # Formato típico: "2018-06-15"
            return int(date_str[:4])
        except (ValueError, IndexError):
            return None

    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """Calcular similitud entre strings usando Levenshtein"""
        import difflib
        return difflib.SequenceMatcher(None, str1, str2).ratio()

    def _create_comicbook_info_from_match(
        self,
        match_result: Dict[str, Any]
    ) -> Optional[ComicbookInfo]:
        """Crear ComicbookInfo desde resultado de coincidencia"""

        volume_data = match_result['volume_data']
        issue_data = match_result['issue_data']

        try:
            # Crear o obtener el volumen
            volume = self._create_or_update_volume(volume_data)

            # Crear ComicbookInfo
            comic_info = ComicbookInfo(
                titulo=issue_data.get('name', ''),
                numero=str(issue_data.get('issue_number', '')),
                fecha_tapa=self._parse_cover_date(issue_data.get('cover_date')),
                resumen=self._clean_description(issue_data.get('description', '')),
                url_api_detalle=issue_data.get('api_detail_url', ''),
                url_sitio_web=issue_data.get('site_detail_url', ''),
                id_comicvine=issue_data.get('id'),
                id_volume=volume.id_volume,
                ultima_sync_comicvine=datetime.utcnow()
            )

            # Añadir imagen de portada si está disponible
            if issue_data.get('image') and issue_data['image'].get('original_url'):
                comic_info.add_cover_image(
                    url=issue_data['image']['original_url'],
                    is_primary=True
                )

            return comic_info

        except Exception as e:
            self.logger.error(f"Error creando ComicbookInfo: {e}")
            return None

    def _create_or_update_volume(self, volume_data: Dict[str, Any]) -> Volume:
        """Crear o actualizar volumen desde datos de ComicVine"""

        comicvine_id = volume_data.get('id')

        # Buscar volumen existente
        volume = None
        if comicvine_id:
            volume = self.volume_repo.get_by_comicvine_id(comicvine_id)

        if not volume:
            # Crear nuevo volumen
            publisher = self._create_or_update_publisher(
                volume_data.get('publisher', {})
            )

            volume = Volume(
                nombre=volume_data.get('name', ''),
                anio_inicio=volume_data.get('start_year'),
                resumen=self._clean_description(volume_data.get('description', '')),
                cantidad_numeros=volume_data.get('count_of_issues', 0),
                url_api_detalle=volume_data.get('api_detail_url', ''),
                url_sitio_web=volume_data.get('site_detail_url', ''),
                id_comicvine=comicvine_id,
                id_publisher=publisher.id_publisher if publisher else None,
                ultima_sync_comicvine=datetime.utcnow()
            )

            self.session.add(volume)
            self.session.flush()

        else:
            # Actualizar volumen existente si es necesario
            volume.update_from_comicvine(volume_data)

        return volume

    def _create_or_update_publisher(
        self,
        publisher_data: Dict[str, Any]
    ) -> Optional[Publisher]:
        """Crear o actualizar editorial desde datos de ComicVine"""

        if not publisher_data or not publisher_data.get('name'):
            return None

        publisher_name = publisher_data['name']
        comicvine_id = publisher_data.get('id')

        # Usar repositorio para obtener o crear
        publisher = self.publisher_repo.get_or_create_publisher(
            name=publisher_name,
            comicvine_id=comicvine_id
        )

        return publisher

    def _parse_cover_date(self, date_str: str) -> Optional[datetime.date]:
        """Parsear fecha de portada"""
        if not date_str:
            return None

        try:
            # Formato típico: "2018-06-15"
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            try:
                # Formato alternativo: "2018-06"
                return datetime.strptime(date_str, '%Y-%m').date()
            except ValueError:
                return None

    def _clean_description(self, description: str) -> str:
        """Limpiar descripción removiendo HTML y normalizando"""
        if not description:
            return ''

        # Remover tags HTML básicos
        import re
        clean_desc = re.sub(r'<[^>]+>', '', description)

        # Decodificar entidades HTML comunes
        html_entities = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'"
        }

        for entity, char in html_entities.items():
            clean_desc = clean_desc.replace(entity, char)

        # Normalizar espacios
        clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()

        return clean_desc

    def update_volume_from_comicvine(
        self,
        volume: Volume,
        update_issues: bool = True
    ) -> bool:
        """Actualizar volumen completo desde ComicVine"""

        if not volume.id_comicvine:
            return False

        try:
            # Obtener datos actualizados del volumen
            volume_data = self.cv_client.get_volume_details(volume.id_comicvine)
            if not volume_data:
                return False

            # Actualizar volumen
            volume.update_from_comicvine(volume_data)

            # Actualizar issues si se solicita
            if update_issues:
                self._sync_volume_issues(volume)

            self.session.commit()
            return True

        except Exception as e:
            self.logger.error(f"Error actualizando volumen {volume.id_volume}: {e}")
            self.session.rollback()
            return False

    def _sync_volume_issues(self, volume: Volume):
        """Sincronizar issues del volumen con ComicVine"""

        # Obtener todos los issues del volumen desde ComicVine
        all_issues = []
        offset = 0
        limit = 100

        while True:
            issues_batch = self.cv_client.get_volume_issues(
                volume.id_comicvine,
                limit=limit,
                offset=offset
            )

            if not issues_batch:
                break

            all_issues.extend(issues_batch)

            if len(issues_batch) < limit:
                break

            offset += limit

        # Actualizar cantidad de issues en el volumen
        volume.cantidad_numeros = len(all_issues)

        # Para cada issue, verificar si existe ComicbookInfo
        for issue_data in all_issues:
            issue_comicvine_id = issue_data.get('id')
            if not issue_comicvine_id:
                continue

            # Buscar ComicbookInfo existente
            existing_info = self.session.query(ComicbookInfo).filter(
                ComicbookInfo.id_comicvine == issue_comicvine_id
            ).first()

            if existing_info:
                # Actualizar información existente
                existing_info.update_from_comicvine(issue_data)
            else:
                # Crear nueva entrada solo si hay comics físicos correspondientes
                # (esto evita crear entradas huérfanas)
                # La creación se hará cuando se catalogue un comic físico
                pass

    def batch_catalog_uncataloged_comics(
        self,
        batch_size: int = 50,
        confidence_threshold: float = 0.7,
        progress_callback=None
    ) -> Dict[str, int]:
        """Catalogar lote de comics sin catalogar"""

        uncataloged_comics = self.comic_repo.get_uncataloged_comics()
        total_comics = len(uncataloged_comics)

        results = {
            'processed': 0,
            'cataloged': 0,
            'failed': 0,
            'skipped': 0
        }

        for i, comic in enumerate(uncataloged_comics):
            try:
                if progress_callback:
                    progress_callback(i + 1, total_comics, comic.filename)

                # Intentar catalogar
                comic_info = self.catalog_comic_from_filename(
                    comic,
                    confidence_threshold
                )

                if comic_info:
                    results['cataloged'] += 1
                else:
                    results['skipped'] += 1

                results['processed'] += 1

                # Commit cada lote
                if results['processed'] % batch_size == 0:
                    self.session.commit()

                # Rate limiting
                time.sleep(0.5)

            except Exception as e:
                self.logger.error(f"Error catalogando {comic.filename}: {e}")
                results['failed'] += 1
                self.session.rollback()

        # Commit final
        try:
            self.session.commit()
        except Exception as e:
            self.logger.error(f"Error en commit final: {e}")
            self.session.rollback()

        return results
```

---

**¿Quieres conocer más sobre la configuración?** 👉 [Configuración](../referencia/configuracion.md)