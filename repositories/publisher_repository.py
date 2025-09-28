from entidades.publisher_model import Publisher
from .base_repository import BaseRepository

class PublisherRepository(BaseRepository):
    def __init__(self, session):
        super().__init__(session)

    def obtener_total(self):
        return super().obtener_total(Publisher)

    def obtener_pagina(self, pagina, tamanio, orden="nombre", direccion="asc"):
        return super().obtener_pagina(Publisher, pagina, tamanio, orden, direccion)
    
    def pagina_siguiente(self, pagina_actual, tamanio):
        return super().pagina_siguiente(pagina_actual, tamanio, Publisher)
