from entidades import Base
from sqlalchemy import Column, Integer, String, Boolean

class Setup(Base):
    __tablename__ = 'setups'
    setupkey = Column(Integer, primary_key=True)
    directorio_base = Column(String, default='')
    cantidad_comics_por_pagina = Column(Integer, nullable=False, default=18)
    ultimo_volume_id_utilizado = Column(String, default='')
    ancho_arbol = Column(Integer, default=100)
    expresion_regular_numero = Column(String, default=r'.* (\d*) \(', nullable=False)
    ancho_thumbnail = Column(Integer, nullable=False, default=120)
    modo_oscuro = Column(Boolean, nullable=False, default=False)
    actualizar_metadata = Column(Boolean, nullable=False, default=False)
    api_key = Column(String, nullable=False, default='')