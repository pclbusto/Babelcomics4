from entidades import Base
from sqlalchemy import Column, Integer, String, Boolean, Float
from sqlalchemy.orm import relationship
import base64

class Setup(Base):
    __tablename__ = 'setups'

    # Primary key
    setupkey = Column(Integer, primary_key=True)

    # Configuración general
    ultimo_volume_id_utilizado = Column(String, default='')
    expresion_regular_numero = Column(String, nullable=False, default=r'.* (\d*) \(')
    modo_oscuro = Column(Boolean, nullable=False, default=False)
    actualizar_metadata = Column(Boolean, nullable=False, default=False)

    # Configuración API
    api_key_encrypted = Column(String, nullable=False, default='')
    rate_limit_interval = Column(Float, nullable=False, default=0.5)

    # Configuración interfaz
    thumbnail_size = Column(Integer, nullable=False, default=200)
    items_per_batch = Column(Integer, nullable=False, default=20)

    # Configuración rendimiento
    workers_concurrentes = Column(Integer, nullable=False, default=5)
    cache_thumbnails = Column(Boolean, nullable=False, default=True)
    limpieza_automatica = Column(Boolean, nullable=False, default=True)

    # Relación con directorios
    directorios = relationship("SetupDirectorio", back_populates="setup", cascade="all, delete-orphan")

    def get_api_key(self):
        """Desencriptar y obtener API key"""
        if not self.api_key_encrypted:
            return ""
        try:
            return base64.b64decode(self.api_key_encrypted.encode()).decode()
        except Exception:
            return ""

    def set_api_key(self, api_key):
        """Encriptar y guardar API key"""
        if api_key:
            self.api_key_encrypted = base64.b64encode(api_key.encode()).decode()
        else:
            self.api_key_encrypted = ""