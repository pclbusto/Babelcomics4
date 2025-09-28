from sqlalchemy import asc, desc
from entidades.volume_search_model import VolumeSearch

class VolumeSearchRepository:
    def __init__(self, session):
        """
        Inicializa el repositorio con la sesión de la base de datos.
        :param session: La sesión de SQLAlchemy.
        """
        self.session = session

    def get_filtered_and_sorted(self, filters={}, sort_by='nombre', sort_direction='asc'):
        """
        Obtiene los resultados de la búsqueda aplicando filtros y ordenación.

        :param filters: Un diccionario con los filtros. Ej: {'editorial': 'marvel', 'anio_inicio': 2022}
        :param sort_by: El nombre de la columna por la que se quiere ordenar.
        :param sort_direction: 'asc' o 'desc'.
        :return: Una lista de objetos VolumeSearch.
        """
        query = self.session.query(VolumeSearch)

        # --- Aplicar Filtros ---
        if filters:
            for key, value in filters.items():
                if not value:  # Ignorar filtros con valores vacíos
                    continue
                
                # Búsqueda de texto flexible para nombre y editorial
                if key in ['nombre', 'editorial']:
                    query = query.filter(getattr(VolumeSearch, key).ilike(f"%{value}%"))
                
                # Búsqueda exacta para campos numéricos
                elif key in ['anio_inicio', 'cantidad_numeros']:
                    try:
                        # Asegurarse de que el valor del filtro sea un número
                        query = query.filter(getattr(VolumeSearch, key) == int(value))
                    except (ValueError, TypeError):
                        print(f"Advertencia: El valor de filtro para '{key}' no es un número válido: '{value}'")

        # --- Aplicar Ordenación ---
        if hasattr(VolumeSearch, sort_by):
            columna_orden = getattr(VolumeSearch, sort_by)
            if sort_direction == 'desc':
                query = query.order_by(desc(columna_orden))
            else:
                query = query.order_by(asc(columna_orden))

        return query.all()