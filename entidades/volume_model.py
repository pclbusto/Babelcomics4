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
        if self.image_url:
            nombre_archivo = self.image_url.rsplit("/", 1)[-1]
            print(f"INFO: Obteniendo carátula para el volumen: {self.nombre} ({self.id_volume})")
            print(f"INFO: Nombre del archivo de la imagen: {nombre_archivo}")
            ruta = os.path.join("data", "thumbnails", "volumenes", nombre_archivo)
            print(f"INFO: Ruta de la imagen: {ruta}")
            if os.path.exists(ruta):
                return ruta
        return "images/Volumen_sin_caratula.png"

