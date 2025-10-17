# modelos/comicbook_info_model.py

from entidades import Base
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, select, func
from sqlalchemy.orm import relationship, column_property
from entidades.comicbook_info_cover_model import ComicbookInfoCover 
from entidades.comicbook_model import Comicbook
class ComicbookInfo(Base):
    __tablename__ = 'comicbooks_info'

    id_comicbook_info = Column(Integer, primary_key=True)
    titulo = Column(String, nullable=False, default='')
    id_volume = Column(Integer, ForeignKey("volumens.id_volume"), nullable=False)
    numero = Column(String, nullable=False, default='0')
    fecha_tapa = Column(Integer, nullable=False, default=0)
    resumen = Column(String, default='')
    notas = Column(String, default='')
    calificacion = Column(Float, nullable=False, default=0.0)
    url_api_detalle = Column(String, default='')
    url_sitio_web = Column(String, default='')
    orden_clasificacion = Column(Float, nullable=False, default=0)
    fue_actualizado_api = Column(Boolean, nullable=False, default=False)
    comicvine_id = Column(Integer, nullable=False, default=0)

    volume = relationship("Volume", back_populates="comicbookinfos") 

    portadas = relationship("ComicbookInfoCover", back_populates="comic_info", cascade="all, delete-orphan", lazy="select")

    owned_comics = relationship(
        "Comicbook",
        foreign_keys=[Comicbook.id_comicbook_info],
        primaryjoin="ComicbookInfo.id_comicbook_info == Comicbook.id_comicbook_info",
        backref="info"
    )
    cantidad_adquirida = column_property(
        select(func.count(Comicbook.id_comicbook))
        .where(Comicbook.id_comicbook_info == id_comicbook_info)
        .correlate_except(Comicbook)
        .scalar_subquery(),
        deferred=True
    )

    def __repr__(self):
        return f"<ComicbookInfo(id='{self.id_comicbook_info}', titulo='{self.titulo}', numero='{self.numero}')>"

    def obtener_portada_principal(self):
        """
        Devuelve la ruta local de la portada principal.
        Ahora comprueba también que el elemento de la portada no sea None.
        """
        # --- VERIFICACIÓN MÁS ROBUSTA ---
        # 1. Comprobamos si la lista tiene elementos.
        # 2. Y ADEMÁS, si el primer elemento no es el valor None.
        print(f"Obteniendo portada principal para ComicbookInfo ID: {self.id_comicbook_info}")

        # Forzar la carga de las portadas si no están cargadas
        if hasattr(self, '_sa_instance_state'):
            from sqlalchemy.orm import session as orm_session
            session = orm_session.object_session(self)
            if session:
                # Refrescar las portadas desde la base de datos
                session.refresh(self)

        print(f"Portadas disponibles: {self.portadas}")
        print(f"Número de portadas: {len(self.portadas) if self.portadas else 0}")

        if self.portadas and len(self.portadas) > 0 and self.portadas[0] is not None:
            # Si ambas condiciones son ciertas, procedemos.
            ruta = self.portadas[0].obtener_ruta_local()
            print(f"Ruta obtenida: {ruta}")
            return ruta
        else:
            # Si la lista está vacía O su primer elemento es None,
            # devolvemos la imagen predeterminada para evitar el crash.
            print("No se encontraron portadas, usando imagen por defecto")
            return "images/Comic_sin_caratula.png"
