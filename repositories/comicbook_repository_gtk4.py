from entidades.comicbook_model import Comicbook
from .base_repository_gtk4 import BaseRepository

class ComicbookRepository(BaseRepository):
    """
    Repositorio para gestionar las operaciones de la base de datos
    para la entidad Comicbook.
    """
    def __init__(self, session):
        super().__init__(session)

    def obtener_todos_los_comics(self, orden=None, direccion='asc'):
        """
        Obtiene todos los cómics, aplicando los filtros y el orden
        desde el repositorio.
        """
        query = self.session.query(Comicbook)

        # --- Aplicación de filtros ---
        if self.filtros:
            print(f"🗄️ ComicRepository aplicando filtros: {self.filtros}")
            for campo, valor in self.filtros.items():
                if campo == 'is_classified':
                    if valor is True:
                        print(f"🟢 Filtrando: Solo cómics CLASIFICADOS (id_comicbook_info != '')")
                        query = query.filter(Comicbook.id_comicbook_info != '')
                    else:
                        print(f"🔴 Filtrando: Solo cómics SIN CLASIFICAR (id_comicbook_info == '')")
                        query = query.filter(Comicbook.id_comicbook_info == '')
                elif campo == 'en_papelera':
                    # Campo booleano: comparación directa
                    print(f"🗑️ Filtrando por en_papelera = {valor}")
                    query = query.filter(Comicbook.en_papelera == valor)
                elif hasattr(getattr(Comicbook, campo), 'ilike'):
                    print(f"🔍 Filtrando por {campo} LIKE '%{valor}%'")
                    query = query.filter(getattr(Comicbook, campo).ilike(f"%{valor}%"))
                else:
                    print(f"📝 Filtrando por {campo} = {valor}")
                    query = query.filter(getattr(Comicbook, campo) == valor)
        
        # --- Lógica de orden ---
        if orden:
            columna_orden = getattr(Comicbook, orden)
            if direccion == 'desc':
                columna_orden = columna_orden.desc()
            query = query.order_by(columna_orden)

        return query.all()
    
    def obtener_total(self):
        """Obtiene el número total de cómics, aplicando los filtros actuales."""
        return super().obtener_total(Comicbook)