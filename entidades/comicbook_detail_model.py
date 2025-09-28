from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from entidades import Base
import os

class Comicbook_Detail(Base):
    __tablename__ = 'comicbooks_detail'
    __table_args__ = (
        UniqueConstraint('comicbook_id', 'indicePagina', name='uq_comic_page_idx'),
    )

    id_detail    = Column(Integer, primary_key=True, autoincrement=True)
    comicbook_id = Column(Integer, ForeignKey('comicbooks.id_comicbook'), nullable=False)
    indicePagina = Column(Integer, nullable=False, default=0)
    ordenPagina  = Column(Integer, nullable=False, default=0)
    tipoPagina   = Column(Integer, nullable=False, default=0)
    nombre_pagina = Column(String, nullable=True)

    comicbook = relationship("Comicbook", back_populates="detalles")

    def __repr__(self):
        return (f"<Comicbook_Detail(comicbook_id={self.comicbook_id}, "
                f"indicePagina={self.indicePagina}, orden={self.ordenPagina}, "
                f"tipo={self.tipoPagina}, nombre='{self.nombre_pagina}')>")

    def obtener_ruta_local(self) -> str:
        """
        Devuelve la ruta local a un thumbnail/cache de esta página si existe.
        No genera nada: solo resuelve path. Si no existe, retorna placeholder.
        Estructura propuesta:
          data/thumbnails/comic_pages/{comicbook_id}/page_{indice}.jpg
        """
        # carpeta destino “estándar”, similar al de ComicbookInfoCover
        base_dir = os.path.join("data", "thumbnails", "comic_pages", str(self.comicbook_id))
        filename = f"page_{self.indicePagina}.jpg"
        ruta = os.path.join(base_dir, filename)

        if os.path.exists(ruta):
            return ruta

        # Podés intentar un nombre basado en nombre_pagina (sanitizado), por si ya lo tenés guardado así
        if self.nombre_pagina:
            limpio = "".join([c if c.isalnum() else " " for c in self.nombre_pagina]).split()
            alt = "_".join(limpio)[:80] or f"page_{self.indicePagina}"
            ruta_alt = os.path.join(base_dir, f"{alt}.jpg")
            if os.path.exists(ruta_alt):
                return ruta_alt

        # fallback a placeholder común
        return "images/Comic_sin_caratula.png"
