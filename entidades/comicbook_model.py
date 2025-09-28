import os
from entidades import Base
from sqlalchemy import Column, Integer, String, Boolean, Sequence, ForeignKey
from sqlalchemy.orm import relationship
from entidades.comicbook_detail_model import Comicbook_Detail

class Comicbook(Base):
    """
    Esta entidad representa un archivo de cómic físico en el disco.
    La clase se llama 'Comicbook' (singular) y mapea a la tabla 'comicbooks' (plural).
    """
    __tablename__ = 'comicbooks'
    __table_args__ = {'sqlite_autoincrement': True}

    # --- Definición de Columnas ---

    id_comicbook = Column(Integer, Sequence('comicbook_id_seq'), primary_key=True)
    path = Column(String, unique=True, nullable=False)
    id_comicbook_info = Column(String, nullable=False, default='')
    calidad = Column(Integer, nullable=False, default=0)
    en_papelera = Column(Boolean, nullable=False, default=False)

    detalles = relationship("Comicbook_Detail", back_populates="comicbook", cascade="all, delete-orphan")

    def obtener_cover(self):
        """
        Busca una carátula de miniatura pre-generada para este cómic.
        Si la encuentra, devuelve su ruta. De lo contrario, devuelve una
        imagen predeterminada.
        """
        # 1. Obtiene el nombre del archivo del cómic (ej: "Batman 01.cbr")
        nombre_archivo = os.path.basename(str(self.id_comicbook))

        # 2. Le cambia la extensión a .png (asumiendo que las miniaturas son png)
        nombre_base, _ = os.path.splitext(nombre_archivo)
        nombre_thumbnail = nombre_base + ".jpg"

        # 3. Construye la ruta donde debería estar la miniatura del cómic
        ruta = os.path.join("data", "thumbnails", "comics", nombre_thumbnail)
        # 4. Si el archivo de miniatura existe, devuelve su ruta
        if os.path.exists(ruta):
            return ruta
        
        # 5. Si no, devuelve la imagen predeterminada para cómics
        return "images/Comic_sin_caratula289328139.png"

     # --- AÑADE ESTA PROPIEDAD ACTUALIZADA ---
    @property
    def is_classified(self):
        """
        Devuelve True si el cómic tiene información asociada (está clasificado).
        """
        # La condición ahora comprueba si 'id_comicbook_info' no es una cadena vacía.
        return bool(self.id_comicbook_info and self.id_comicbook_info.strip())

    @property
    def nombre_archivo(self) -> str:
        """
        Devuelve solo el nombre del archivo (sin path) desde el atributo `path`.
        """
        return os.path.basename(self.path)


    def __repr__(self):
        return (f"<Comicbook(id={self.id_comicbook}, "
                f"path='{self.path}', "
                f"info_id='{self.id_comicbook_info}')>")