# repositories/comicbook_info_repository.py

from typing import Iterable, List, Optional, Sequence, Tuple
from sqlalchemy.orm import joinedload
from entidades.comicbook_info_model import ComicbookInfo
from entidades.comicbook_info_cover_model import ComicbookInfoCover
from entidades.comicbook_model import Comicbook
from entidades.volume_model import Volume
from .base_repository import BaseRepository

class ComicbookInfoRepository(BaseRepository):
    """
    Repositorio para gestionar metadata de issues (ComicbookInfo).
    - Filtros soportados (keys en self.filtros):
        * id_volume: int                -> issues de un volumen
        * numero: str (ilike)           -> filtra por número (texto)
        * titulo: str (ilike)           -> filtra por título
        * fue_actualizado_api: bool     -> flag booleano
        * min_fecha_tapa / max_fecha_tapa: int -> rango de fecha_tapa (YYYYMM)
        * con_propietarios: bool        -> si True, solo issues con Comicbook asociado
    - Orden por: 'numero', 'titulo', 'orden_clasificacion', 'fecha_tapa' (o cualquier columna válida)
    """

    def __init__(self, session):
        super().__init__(session)
        self._total_filtrado = 0

    # ------- Conteo total con filtros (corrige uso de filtros) -------
    def obtener_total(self, modelo=None):
        query = self.session.query(ComicbookInfo)

        # Filtros
        for campo, valor in (self.filtros or {}).items():
            if campo == "id_volume" and valor is not None:
                query = query.filter(ComicbookInfo.id_volume == int(valor))
            elif campo == "numero" and isinstance(valor, str):
                query = query.filter(ComicbookInfo.numero.ilike(f"%{valor}%"))
            elif campo == "titulo" and isinstance(valor, str):
                query = query.filter(ComicbookInfo.titulo.ilike(f"%{valor}%"))
            elif campo == "fue_actualizado_api" and isinstance(valor, bool):
                query = query.filter(ComicbookInfo.fue_actualizado_api.is_(valor))
            elif campo == "min_fecha_tapa" and isinstance(valor, int):
                query = query.filter(ComicbookInfo.fecha_tapa >= valor)
            elif campo == "max_fecha_tapa" and isinstance(valor, int):
                query = query.filter(ComicbookInfo.fecha_tapa <= valor)
            elif campo == "con_propietarios" and isinstance(valor, bool):
                if valor:
                    query = query.join(
                        Comicbook, ComicbookInfo.id_comicbook_info == Comicbook.id_comicbook_info
                    )

        return query.count()

    # ------- Página con filtros/orden y carga opcional de relaciones -------
    def obtener_pagina(
        self,
        pagina: int,
        tamanio: int,
        orden: Optional[str] = "orden_clasificacion",
        direccion: str = "asc",
        columnas: Optional[Sequence[str]] = None,
        with_covers: bool = True,
        with_volume: bool = False,
        with_owned_count: bool = False,  # si usás cantidad_adquirida (column_property)
    ):
        # Base query (columnas o modelo completo)
        if columnas:
            query = self.session.query(*[getattr(ComicbookInfo, col) for col in columnas])
        else:
            query = self.session.query(ComicbookInfo)

        # Filtros
        for campo, valor in (self.filtros or {}).items():
            if campo == "id_volume" and valor is not None:
                query = query.filter(ComicbookInfo.id_volume == int(valor))
            elif campo == "numero" and isinstance(valor, str):
                query = query.filter(ComicbookInfo.numero.ilike(f"%{valor}%"))
            elif campo == "titulo" and isinstance(valor, str):
                query = query.filter(ComicbookInfo.titulo.ilike(f"%{valor}%"))
            elif campo == "fue_actualizado_api" and isinstance(valor, bool):
                query = query.filter(ComicbookInfo.fue_actualizado_api.is_(valor))
            elif campo == "min_fecha_tapa" and isinstance(valor, int):
                query = query.filter(ComicbookInfo.fecha_tapa >= valor)
            elif campo == "max_fecha_tapa" and isinstance(valor, int):
                query = query.filter(ComicbookInfo.fecha_tapa <= valor)
            elif campo == "con_propietarios" and isinstance(valor, bool) and valor:
                query = query.join(
                    Comicbook, ComicbookInfo.id_comicbook_info == Comicbook.id_comicbook_info
                )

        # Eager loading (opcional)
        if not columnas:
            if with_covers:
                query = query.options(joinedload(ComicbookInfo.portadas))
            if with_volume:
                query = query.options(joinedload(ComicbookInfo.volume))
            # cantidad_adquirida ya es column_property; no requiere eager loading
            # with_owned_count se deja por compatibilidad semántica

        # Orden
        if orden and hasattr(ComicbookInfo, orden):
            campo_orden = getattr(ComicbookInfo, orden)
            if direccion == "desc":
                campo_orden = campo_orden.desc()
            else:
                campo_orden = campo_orden.asc()
            query = query.order_by(campo_orden)

        # Paginación
        self._total_filtrado = query.count()
        return query.offset(pagina * tamanio).limit(tamanio).all()

    def pagina_siguiente(self, pagina_actual, tamanio):
        return super().pagina_siguiente(pagina_actual, tamanio, ComicbookInfo)

    # ------- Utilidades específicas -------
    def listar_por_volume(self, id_volume: int) -> List[ComicbookInfo]:
        return (
            self.session.query(ComicbookInfo)
            .filter(ComicbookInfo.id_volume == int(id_volume))
            .order_by(ComicbookInfo.orden_clasificacion.asc())
            .all()
        )

    def obtener_por_ids(self, ids: Iterable[int]) -> List[ComicbookInfo]:
        ids = list({int(x) for x in ids})
        if not ids:
            return []
        return (
            self.session.query(ComicbookInfo)
            .filter(ComicbookInfo.id_comicbook_info.in_(ids))
            .all()
        )


class ComicbookInfoCoverRepository(BaseRepository):
    """
    Repositorio simple para portadas de ComicbookInfo (ComicbookInfoCover).
    Útil si querés operar covers aparte.
    """
    def __init__(self, session):
        super().__init__(session)

    def obtener_total(self, modelo=None):
        query = self.session.query(ComicbookInfoCover)
        # Si necesitás filtros (por id_comicbook_info), podés aprovechar self.filtros
        if self.filtros:
            iid = self.filtros.get("id_comicbook_info")
            if iid:
                query = query.filter(ComicbookInfoCover.id_comicbook_info == int(iid))
        return query.count()

    def obtener_pagina(self, pagina, tamanio, orden=None, direccion="asc", columnas=None):
        if columnas:
            query = self.session.query(*[getattr(ComicbookInfoCover, c) for c in columnas])
        else:
            query = self.session.query(ComicbookInfoCover)
        if self.filtros:
            iid = self.filtros.get("id_comicbook_info")
            if iid:
                query = query.filter(ComicbookInfoCover.id_comicbook_info == int(iid))
        if orden and hasattr(ComicbookInfoCover, orden):
            campo = getattr(ComicbookInfoCover, orden)
            query = query.order_by(campo.desc() if direccion == "desc" else campo.asc())
        return query.offset(pagina * tamanio).limit(tamanio).all()
