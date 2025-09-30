from entidades import Base
from sqlalchemy import Column, String, Integer
import os

class Publisher(Base):
    __tablename__ = 'publishers'
    id_publisher = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False, default='')
    deck = Column(String, default='')  # Nuevo campo agregado
    descripcion = Column(String, default='')
    url_logo = Column(String, default='')  # Renombrado de 'url' a 'url_logo'
    sitio_web = Column(String, default='')
    id_comicvine = Column(Integer, default=None)  # ID de ComicVine para filtros

    def __repr__(self):
        return f"<Publisher(id_publisher='{self.id_publisher}', nombre='{self.nombre}', deck='{self.deck}', descripcion='{self.descripcion}')>"

    def obtener_nombre_logo(self):
        """Obtiene la ruta completa del logo o una imagen por defecto."""
        if self.url_logo:
            nombre_archivo = self.url_logo.split('/')[-1]  # Extraer el nombre del archivo
            ruta = os.path.join("data", "thumbnails", "editoriales", nombre_archivo)  # Construir la ruta completa
            if os.path.exists(ruta):  # Verificar si el archivo existe
                return ruta
        # Si no se encuentra el archivo, retornar la imagen por defecto
        return "images/publisher_sin_logo.png"

