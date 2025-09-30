from entidades.volume_model import Volume
from .base_repository import BaseRepository

class VolumeRepository(BaseRepository):
    def __init__(self, session):
        super().__init__(session)

    def obtener_total(self, modelo=None):
        return super().obtener_total(modelo or Volume)

    def obtener_pagina(self, pagina, tamanio, orden="nombre", direccion="asc", columnas=None):
        return super().obtener_pagina(Volume, pagina, tamanio, orden, direccion, columnas)

    def pagina_siguiente(self, pagina_actual, tamanio):
        print("Llamando a pagina_siguiente en VolumeRepository")
        return super().pagina_siguiente(pagina_actual, tamanio, Volume)

    def volume_exists(self, volume_api_id):
        return self.session.query(Volume).filter_by(id_volume=volume_api_id).first() is not None

    def create_from_api_data(self, volume_data):
        """
        Crea un nuevo objeto Volume a partir de un diccionario de datos de la API,
        lo añade a la sesión y lo guarda en la base de datos.
        Devuelve el objeto Volume recién creado.
        """
        # 1. Comprueba si el volumen ya existe para evitar duplicados
        volume_id = volume_data.get('id')
        if self.volume_exists(volume_id):
            print(f"INFO: El volumen con ID {volume_id} ya existe. No se creará uno nuevo.")
            return self.find_by_id(volume_id)

        # 2. Extrae y limpia los datos del diccionario
        year_str = str(volume_data.get('start_year') or '0')
        cleaned_year_str = "".join(filter(str.isdigit, year_str))
        year = int(cleaned_year_str) if cleaned_year_str else 0

        # 3. Crea la nueva instancia del modelo Volume
        nuevo_volumen = Volume(
            id_volume=volume_id,
            nombre=volume_data.get('name', 'N/A'),
            deck=volume_data.get('deck', ''),
            descripcion=volume_data.get('description', ''),
            url=volume_data.get('site_detail_url', ''),
            image_url=volume_data.get('image', {}).get('medium_url', ''),
            id_publisher=volume_data.get('publisher', {}).get('id', ''),
            anio_inicio=year,
            cantidad_numeros=volume_data.get('count_of_issues', 0)
        )

        # 4. Lo añade y guarda en la base de datos
        self.session.add(nuevo_volumen)
        self.session.commit()
        print(f"INFO: Volumen '{nuevo_volumen.nombre}' creado y guardado en la base de datos.")

        # 5. Devuelve el objeto recién creado
        return nuevo_volumen

    def get_by_comicvine_id(self, comicvine_id):
        """
        Busca un volumen por su ID de ComicVine
        """
        return self.session.query(Volume).filter_by(id_comicvine=comicvine_id).first()

    def create_volume(self, volume_data):
        """
        Crear un nuevo volumen desde datos de ComicVine
        """
        # Verificar si ya existe
        comicvine_id = volume_data.get('id')
        existing = self.get_by_comicvine_id(comicvine_id)
        if existing:
            print(f"INFO: El volumen con ComicVine ID {comicvine_id} ya existe.")
            return existing

        # Limpiar año
        year_str = str(volume_data.get('start_year') or '0')
        cleaned_year_str = "".join(filter(str.isdigit, year_str))
        year = int(cleaned_year_str) if cleaned_year_str else 0

        # Crear nuevo volumen
        nuevo_volumen = Volume(
            nombre=volume_data.get('name', 'N/A'),
            deck=volume_data.get('deck', ''),
            descripcion=volume_data.get('description', ''),
            url=volume_data.get('site_detail_url', ''),
            image_url=volume_data.get('image', {}).get('medium_url', ''),
            id_publisher=volume_data.get('publisher', {}).get('id', 0),
            anio_inicio=year,
            cantidad_numeros=volume_data.get('count_of_issues', 0),
            id_comicvine=comicvine_id
        )

        # Guardar en base de datos
        self.session.add(nuevo_volumen)
        self.session.commit()
        print(f"INFO: Volumen '{nuevo_volumen.nombre}' creado con ComicVine ID {comicvine_id}")

        return nuevo_volumen
