# en entidades/volume_search_model.py

from sqlalchemy import Column, Integer, String
from entidades import Base

class VolumeSearch(Base):
    """
    Representa un resultado de búsqueda de volumen de Comic Vine, guardado
    temporalmente en la base de datos para facilitar el filtrado y la ordenación.
    """
    __tablename__ = 'volume_searches'

    # Usamos el ID de Comic Vine como clave primaria. 
    # No es autoincremental, lo asignamos nosotros.
    id_volume = Column(Integer, primary_key=True, autoincrement=False)
    
    nombre = Column(String)
    editorial = Column(String)
    anio_inicio = Column(Integer)
    cantidad_numeros = Column(Integer)
    image_url = Column(String)
    site_detail_url = Column(String)

    def __repr__(self):
        return f"<VolumeSearch(id={self.id_volume}, nombre='{self.nombre}')>"