from entidades.setup_model import Setup

class SetupRepository:
    """
    Repositorio para gestionar las operaciones de la base de datos
    para la entidad de configuración (Setup).
    """
    def __init__(self, session):
        """
        Inicializa el repositorio con la sesión de la base de datos.
        
        Args:
            session: La sesión de SQLAlchemy.
        """
        self.session = session

    def obtener_o_crear_configuracion(self):
        """
        Obtiene la configuración única de la base de datos.
        Si no existe ninguna configuración, la crea con valores por defecto.
        
        Returns:
            El objeto Setup de la base de datos.
        """
        # Intenta obtener la primera (y única) fila de configuración
        config = self.session.query(Setup).first()
        
        if not config:
            # Si no hay ninguna configuración en la BD, la creamos
            print("INFO: No se encontró configuración. Creando una nueva con valores por defecto.")
            config = Setup()
            self.session.add(config)
            self.session.commit()
            
        return config

    def guardar_configuracion(self, config_obj):
        """
        Guarda (hace commit) los cambios en un objeto de configuración.
        
        Args:
            config_obj: El objeto Setup con los valores ya modificados.
        """
        # La ventana de configuración ya modifica el objeto,
        # aquí solo nos aseguramos de que los cambios se guarden en la BD.
        self.session.commit()
        print("INFO: Configuración guardada en la base de datos.")