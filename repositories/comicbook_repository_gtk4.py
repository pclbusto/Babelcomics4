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
                elif campo == 'path_año_numero':
                    # Filtro especial para búsquedas con años/números
                    for numero in valor:
                        print(f"📅 Filtrando por año/número en path: {numero}")
                        query = query.filter(Comicbook.path.ilike(f"%{numero}%"))
                elif campo == 'path_multiple_terms':
                    # Filtro especial para múltiples términos (AND)
                    for term in valor:
                        print(f"🔗 Filtrando por término (AND): {term}")
                        query = query.filter(Comicbook.path.ilike(f"%{term}%"))
                elif campo == 'path_exclude_terms':
                    # Filtro especial para exclusión de términos (NOT)
                    for term in valor:
                        print(f"🚫 Excluyendo término: {term}")
                        query = query.filter(~Comicbook.path.ilike(f"%{term}%"))
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

    def filtrar_año_o_numero(self, valor):
        """
        Filtrar comics por año o número en el path del archivo.
        Busca el valor numérico en el nombre del archivo.
        """
        if 'path_año_numero' not in self.filtros:
            self.filtros['path_año_numero'] = []
        self.filtros['path_año_numero'].append(str(valor))

    def filtrar_multiple_path_terms(self, terms):
        """
        Filtrar comics que contengan TODOS los términos en el path (AND).
        """
        if terms:
            self.filtros['path_multiple_terms'] = terms

    def filtrar_path_exclude_terms(self, exclude_terms):
        """
        Filtrar comics que NO contengan ninguno de los términos (NOT).
        """
        if exclude_terms:
            self.filtros['path_exclude_terms'] = exclude_terms