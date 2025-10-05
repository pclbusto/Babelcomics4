from entidades import Base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from entidades.comicbook_info_model import ComicbookInfo

class Volume(Base):
    __tablename__ = 'volumens'
    id_volume = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False, default='')
    deck = Column(String, nullable=False, default='')
    descripcion = Column(String, nullable=False, default='')
    url = Column(String, nullable=False, default='')
    image_url = Column(String, nullable=False, default='')
    id_publisher = Column(Integer, nullable=False, default=0)  # Mantiene la relación con Publisher
    anio_inicio = Column(Integer, nullable=False, default=0)
    cantidad_numeros = Column(Integer, nullable=False, default=0)
    id_comicvine = Column(Integer, nullable=True, default=None)  # ID de ComicVine para actualizaciones

    comicbookinfos = relationship("ComicbookInfo", back_populates="volume", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<volumens(id_volume={self.id_volume}, nombre='{self.nombre}', deck='{self.deck}', descripcion='{self.descripcion}', url='{self.url}', image_url='{self.image_url}', id_publisher='{self.id_publisher}', anio_inicio={self.anio_inicio}, cantidad_numeros={self.cantidad_numeros})>"
    
    def obtener_cover(self):
        import os
        # Primero intentar con la ruta local basada en ID (formato esperado)
        ruta_local = os.path.join("data", "thumbnails", "volumes", f"{self.id_volume}.jpg")
        print(f"INFO: Obteniendo carátula para el volumen: {self.nombre} ({self.id_volume})")
        print(f"INFO: Ruta local esperada: {ruta_local}")
        if os.path.exists(ruta_local):
            print(f"INFO: Encontrada imagen local: {ruta_local}")
            return ruta_local

        # Si no existe la local, intentar con image_url (formato antiguo)
        if self.image_url:
            nombre_archivo = self.image_url.rsplit("/", 1)[-1]
            ruta_antigua = os.path.join("data", "thumbnails", "volumes", nombre_archivo)
            print(f"INFO: Ruta antigua: {ruta_antigua}")
            if os.path.exists(ruta_antigua):
                print(f"INFO: Encontrada imagen antigua: {ruta_antigua}")
                return ruta_antigua

        print(f"INFO: No se encontró imagen para volumen {self.id_volume}, usando placeholder")
        return "images/Volumen_sin_caratula.png"

