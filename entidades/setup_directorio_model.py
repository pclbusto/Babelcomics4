from entidades import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

class SetupDirectorio(Base):
    __tablename__ = 'setup_directorios'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign key
    setup_id = Column(Integer, ForeignKey('setups.setupkey'), nullable=False)

    # Configuración del directorio
    directorio_path = Column(String, nullable=False)
    activo = Column(Boolean, nullable=False, default=True)

    # Relación con setup
    setup = relationship("Setup", back_populates="directorios")

    def __repr__(self):
        return f"<SetupDirectorio(id={self.id}, path='{self.directorio_path}', activo={self.activo})>"

    def is_valid_path(self):
        """Verificar si el path del directorio existe y es válido"""
        try:
            from pathlib import Path
            path = Path(self.directorio_path)
            return path.exists() and path.is_dir()
        except Exception:
            return False