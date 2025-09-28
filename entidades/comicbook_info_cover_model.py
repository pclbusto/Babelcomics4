# modelos/comicbook_info_cover_model.py

import os
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from entidades import Base # Importa la Base compartida

class ComicbookInfoCover(Base):
    __tablename__ = 'comicbooks_info_covers'

    id_cover = Column(Integer, primary_key=True, autoincrement=True)
    id_comicbook_info = Column(Integer, ForeignKey('comicbooks_info.id_comicbook_info'), nullable=False)
    url_imagen = Column(String, nullable=False)
    

    comic_info = relationship("ComicbookInfo", back_populates="portadas")

    def __repr__(self):
        return f"<ComicbookInfoCover(id_cover='{self.id_cover}', url_imagen='{self.url_imagen}')>"

    def obtener_ruta_local(self):
        """Obtiene la ruta local de la portada o una imagen por defecto."""
        if self.url_imagen:
            nombre_archivo = self.url_imagen.split('/')[-1]

            # Limpiar el nombre del volumen pero conservando espacios
            clean_volume_name = "".join([c if c.isalnum() or c.isspace() else "" for c in self.comic_info.volume.nombre]).strip()

            print(f"Nombre limpio del volumen: {clean_volume_name}")
            print(f"Nombre del archivo de la portada: {nombre_archivo}")
            print(f"nombre del volumen: {self.comic_info.volume.nombre}")

            covers_destination_folder = os.path.join(
                "data",
                "thumbnails",
                "comicbookinfo_issues",
                f"{clean_volume_name}_{self.comic_info.volume.id_volume}" # Combinar nombre limpio y ID
            )
            ruta = os.path.join(covers_destination_folder, nombre_archivo)
            print(f"Ruta de destino de las portadas: {ruta}")
            if os.path.exists(ruta):
                return ruta
        return "images/Comic_sin_caratula.png"