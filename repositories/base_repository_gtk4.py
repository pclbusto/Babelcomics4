class BaseRepository:
    def __init__(self, session):
        self.session = session
        self.filtros = {}

    def obtener_total(self, modelo):
        """Obtiene el número total de ítems aplicando los filtros actuales."""
        query = self.session.query(modelo)
        for campo, valor in self.filtros.items():
            if hasattr(getattr(modelo, campo), 'ilike'):
                query = query.filter(getattr(modelo, campo).ilike(f"%{valor}%"))
            else:
                query = query.filter(getattr(modelo, campo) == valor)
        return query.count()

    def limpiar_filtros(self):
        """Limpia los filtros de la sesión."""
        self.filtros = {}

    def filtrar(self, **kwargs):
        """Actualiza los filtros para la próxima consulta (mantiene filtros existentes)."""
        nuevos_filtros = {k: v for k, v in kwargs.items() if v is not None}
        self.filtros.update(nuevos_filtros)