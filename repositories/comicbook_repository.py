# repositories/comicbook_repository.py

from entidades.comicbook_model import Comicbook
from .base_repository import BaseRepository

class ComicbookRepository(BaseRepository):
    """
    Repositorio para gestionar las operaciones de la base de datos
    para la entidad Comicbook.
    """
    def __init__(self, session):
        super().__init__(session)

    def obtener_total(self, modelo=None):
        """
        Obtiene el número total de cómics, aplicando los filtros actuales.
        """
        return super().obtener_total(Comicbook)

    def obtener_pagina(self, pagina, tamanio, orden=None, direccion='asc', columnas=None):
        """
        Sobrescribe el método base para manejar filtros específicos de Comicbook.
        """
        query = self.session.query(Comicbook)

        # --- LÓGICA DE FILTRADO CORREGIDA ---
        if self.filtros:
            for campo, valor in self.filtros.items():
                if campo == 'is_classified':
                    # TRADUCCIÓN CORRECTA: Basado en tu @property is_classified.
                    # Un cómic está clasificado si su 'id_comicbook_info' NO es una cadena vacía.
                    if valor is True:
                        query = query.filter(Comicbook.id_comicbook_info != '')
                    else:
                        # No está clasificado si 'id_comicbook_info' ES una cadena vacía.
                        query = query.filter(Comicbook.id_comicbook_info == '')

                elif campo == 'path' and isinstance(valor, str):
                    # Para el resto de los filtros (como path), usamos ilike
                    query = query.filter(getattr(Comicbook, campo).ilike(f"%{valor}%"))
                
        # --- Lógica de orden y paginación (sin cambios) ---
        if orden:
            columna_orden = getattr(Comicbook, orden)
            if direccion == 'desc':
                columna_orden = columna_orden.desc()
            query = query.order_by(columna_orden)

        self._total_filtrado = query.count()
        return query.offset(pagina * tamanio).limit(tamanio).all()

    def pagina_siguiente(self, pagina_actual, tamanio):
        """
        Calcula el número de la página siguiente para la paginación de cómics.
        """
        return super().pagina_siguiente(pagina_actual, tamanio, Comicbook)
        def pagina_anterior(self, pagina_actual, tamanio):
            """
            Calcula el número de la página anterior para la paginación de cómics.
            """
            return super().pagina_anterior(pagina_actual, tamanio, Comicbook)