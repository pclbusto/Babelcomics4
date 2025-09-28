class BaseRepository:
    def __init__(self, session):
        self.session = session
        self.filtros = {}

    def obtener_total(self, modelo):
        # Verificar y crear si no existe antes de usarlo
        if not hasattr(self, 'filtros_activos'):
            self.filtros_activos = {} # Inicialización perezosa
        
        query = self.session.query(modelo)
        for campo, valor in self.filtros_activos.items(): # Aquí fallaría sin la verificación
            if campo == 'is_classified':
                if valor is True:
                    query = query.filter(modelo.comic_book_info_id.isnot(None))
                else:
                    query = query.filter(modelo.comic_book_info_id.is_(None))
            elif hasattr(getattr(modelo, campo), 'ilike'):
                query = query.filter(getattr(modelo, campo).ilike(f"%{valor}%"))
            else:
                query = query.filter(getattr(modelo, campo) == valor)
        return query.count()

    def obtener_pagina(self, modelo, pagina, tamanio, orden="nombre", direccion="asc", columnas=None):
        # Usa columnas si están definidas, sino el modelo completo
        if columnas:
            query = self.session.query(*[getattr(modelo, col) for col in columnas])
        else:
            query = self.session.query(modelo)

        for campo, valor in self.filtros.items():
            if hasattr(modelo, campo):
                query = query.filter(getattr(modelo, campo).ilike(f"%{valor}%"))

        if hasattr(modelo, orden):
            campo_orden = getattr(modelo, orden)
            campo_orden = campo_orden.desc() if direccion == "desc" else campo_orden.asc()
            query = query.order_by(campo_orden)

        return query.offset(pagina * tamanio).limit(tamanio).all()


    def limpiar_filtros(self):
        self.filtros = {}

    def filtrar(self, **kwargs):
        self.filtros = {k: v for k, v in kwargs.items() if v is not None}

    def pagina_siguiente(self, pagina_actual, tamanio, modelo):
        total = self.obtener_total(modelo)
        max_pagina = (total - 1) // tamanio
        return min(pagina_actual + 1, max_pagina)
