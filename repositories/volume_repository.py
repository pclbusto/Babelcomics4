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

    def create_volume(self, volume_data, force_update=False):
        """
        Crear un nuevo volumen desde datos de ComicVine o actualizar uno existente

        Args:
            volume_data: Datos del volumen desde ComicVine
            force_update: Si True, actualiza el volumen existente con los nuevos datos
        """
        # Verificar si ya existe
        comicvine_id = volume_data.get('id')
        existing = self.get_by_comicvine_id(comicvine_id)

        if existing and not force_update:
            print(f"INFO: El volumen con ComicVine ID {comicvine_id} ya existe. Use force_update=True para actualizar.")
            return existing
        elif existing and force_update:
            print(f"INFO: Actualizando volumen existente con ComicVine ID {comicvine_id}")
            return self.update_volume_from_comicvine(existing, volume_data)

        # Limpiar año
        year_str = str(volume_data.get('start_year') or '0')
        cleaned_year_str = "".join(filter(str.isdigit, year_str))
        year = int(cleaned_year_str) if cleaned_year_str else 0

        # Crear nuevo volumen con manejo seguro de valores None
        # Manejar image_url de forma segura
        image_data = volume_data.get('image', {})
        image_url = ''
        if image_data and isinstance(image_data, dict):
            image_url = image_data.get('medium_url') or ''

        # Manejar publisher ID de forma segura
        publisher_data = volume_data.get('publisher', {})
        publisher_id = 0
        if publisher_data and isinstance(publisher_data, dict):
            publisher_id = publisher_data.get('id') or 0

        nuevo_volumen = Volume(
            nombre=volume_data.get('name') or 'N/A',
            deck=volume_data.get('deck') or '',
            descripcion=volume_data.get('description') or '',
            url=volume_data.get('site_detail_url') or '',
            image_url=image_url,
            id_publisher=publisher_id,
            anio_inicio=year,
            cantidad_numeros=volume_data.get('count_of_issues', 0) or 0,
            id_comicvine=comicvine_id
        )

        # Guardar en base de datos
        self.session.add(nuevo_volumen)
        self.session.commit()
        print(f"INFO: Volumen '{nuevo_volumen.nombre}' creado con ComicVine ID {comicvine_id}")

        return nuevo_volumen

    def update_volume_from_comicvine(self, volume, volume_data):
        """
        Actualizar un volumen existente con datos completos de ComicVine

        Args:
            volume: Objeto Volume existente
            volume_data: Datos actualizados desde ComicVine
        """
        try:
            # Guardar valores anteriores para logging
            old_count = volume.cantidad_numeros
            old_name = volume.nombre

            # Limpiar año
            year_str = str(volume_data.get('start_year') or '0')
            cleaned_year_str = "".join(filter(str.isdigit, year_str))
            year = int(cleaned_year_str) if cleaned_year_str else volume.anio_inicio

            # Actualizar todos los campos con datos de ComicVine
            # Asegurar que los campos NOT NULL tengan valores por defecto
            volume.nombre = volume_data.get('name', volume.nombre) or volume.nombre
            volume.deck = volume_data.get('deck') or ''  # Convertir None a string vacío
            volume.descripcion = volume_data.get('description') or ''  # Convertir None a string vacío
            volume.url = volume_data.get('site_detail_url') or volume.url or ''

            # Manejar image_url de forma segura
            image_data = volume_data.get('image', {})
            if image_data and isinstance(image_data, dict):
                new_image_url = image_data.get('medium_url')
                volume.image_url = new_image_url or volume.image_url or ''
            else:
                volume.image_url = volume.image_url or ''

            # Manejar publisher ID de forma segura
            publisher_data = volume_data.get('publisher', {})
            if publisher_data and isinstance(publisher_data, dict):
                new_publisher_id = publisher_data.get('id')
                volume.id_publisher = new_publisher_id or volume.id_publisher or 0
            else:
                volume.id_publisher = volume.id_publisher or 0

            volume.anio_inicio = year
            volume.cantidad_numeros = volume_data.get('count_of_issues', 0) or 0

            # Guardar cambios
            self.session.commit()

            # Log de cambios importantes
            if old_count != volume.cantidad_numeros:
                print(f"📊 Cantidad actualizada para '{volume.nombre}': {old_count} → {volume.cantidad_numeros} números")
            if old_name != volume.nombre:
                print(f"📝 Nombre actualizado: '{old_name}' → '{volume.nombre}'")

            print(f"✅ Volumen '{volume.nombre}' actualizado exitosamente desde ComicVine")
            return volume

        except Exception as e:
            print(f"❌ Error actualizando volumen {volume.id_volume}: {e}")
            self.session.rollback()
            raise e

    def download_complete_volume_data(self, volume_data, comicvine_client, download_covers=True, progress_callback=None):
        """
        Descarga COMPLETA de un volumen desde ComicVine incluyendo:
        - Información del volumen
        - Todos los issues
        - Covers del volumen e issues

        Args:
            volume_data: Datos básicos del volumen desde búsqueda de ComicVine
            comicvine_client: Cliente de ComicVine ya inicializado
            download_covers: Si descargar covers o no
            progress_callback: Función para reportar progreso (mensaje)

        Returns:
            Volume: Objeto volumen creado/actualizado
        """
        try:
            def report_progress(message):
                if progress_callback:
                    progress_callback(message)
                print(f"📥 {message}")

            comicvine_id = volume_data.get('id')
            if not comicvine_id:
                raise ValueError("El volumen no tiene ID de ComicVine válido")

            report_progress("Obteniendo información completa del volumen...")

            # 1. Obtener detalles completos del volumen
            volume_details = comicvine_client.get_volume_details(comicvine_id)
            if not volume_details:
                raise Exception("No se pudieron obtener detalles del volumen")

            # 2. Crear/actualizar el volumen base
            report_progress("Creando/actualizando información del volumen...")
            volume = self.create_volume(volume_details, force_update=True)

            # 3. Obtener y procesar issues
            issues_list = volume_details.get('issues', [])
            if issues_list:
                issue_ids = [issue['id'] for issue in issues_list if 'id' in issue]

                if issue_ids:
                    report_progress(f"Descargando información de {len(issue_ids)} issues...")
                    detailed_issues = comicvine_client.get_issues_by_ids(issue_ids)

                    if detailed_issues:
                        new_issues_count, updated_issues_count = self._process_volume_issues(
                            volume, detailed_issues, report_progress
                        )

                        report_progress(f"Issues procesados: {new_issues_count} nuevos, {updated_issues_count} actualizados")

                        # 4. Descargar covers si está habilitado
                        if download_covers:
                            self._download_volume_and_issues_covers(
                                volume, volume_details, detailed_issues, report_progress
                            )
                    else:
                        report_progress("No se pudieron obtener detalles de los issues")
                else:
                    report_progress("El volumen no tiene issues")
            else:
                report_progress("El volumen no tiene issues listados")

            # 5. Commit final
            self.session.commit()
            report_progress(f"✅ Descarga completa finalizada: {volume.nombre}")

            return volume

        except Exception as e:
            print(f"❌ Error en descarga completa: {e}")
            self.session.rollback()
            raise e

    def _process_volume_issues(self, volume, detailed_issues, progress_callback=None):
        """Procesar issues del volumen - crear nuevos y actualizar existentes"""
        from entidades.comicbook_info_model import ComicbookInfo

        new_issues_count = 0
        updated_issues_count = 0

        for i, issue_data in enumerate(detailed_issues):
            try:
                if progress_callback and i % 10 == 0:  # Reportar cada 10 issues
                    progress_callback(f"Procesando issues... {i+1}/{len(detailed_issues)}")

                issue_number = issue_data.get('issue_number')
                if not issue_number:
                    continue

                # Buscar si ya existe este issue
                existing_issue = self.session.query(ComicbookInfo).filter(
                    ComicbookInfo.id_volume == volume.id_volume,
                    ComicbookInfo.numero == str(issue_number)
                ).first()

                if existing_issue:
                    # Actualizar issue existente
                    self._update_existing_issue(existing_issue, issue_data)
                    updated_issues_count += 1
                else:
                    # Crear nuevo issue
                    self._create_new_issue(volume, issue_data)
                    new_issues_count += 1

            except Exception as e:
                print(f"Error procesando issue {issue_data.get('issue_number', 'N/A')}: {e}")

        return new_issues_count, updated_issues_count

    def _update_existing_issue(self, existing_issue, issue_data):
        """Actualizar un issue existente con datos de ComicVine"""
        # Actualizar campos si vienen datos nuevos
        if issue_data.get('name') and not existing_issue.titulo:
            existing_issue.titulo = issue_data['name']

        if issue_data.get('description') and not existing_issue.resumen:
            existing_issue.resumen = self._clean_html_text(issue_data['description'])

        if issue_data.get('cover_date'):
            try:
                fecha_str = issue_data['cover_date']
                if fecha_str and len(fecha_str) >= 4:
                    existing_issue.fecha_tapa = int(fecha_str[:4])
            except (ValueError, TypeError):
                pass

        # Actualizar ID de ComicVine si no lo tiene
        if issue_data.get('id') and not existing_issue.id_comicvine:
            existing_issue.id_comicvine = issue_data['id']

    def _create_new_issue(self, volume, issue_data):
        """Crear un nuevo issue desde datos de ComicVine"""
        from entidades.comicbook_info_model import ComicbookInfo

        # Procesar fecha de tapa
        fecha_tapa = None
        if issue_data.get('cover_date'):
            try:
                fecha_str = issue_data['cover_date']
                if fecha_str and len(fecha_str) >= 4:
                    fecha_tapa = int(fecha_str[:4])
            except (ValueError, TypeError):
                pass

        new_issue = ComicbookInfo(
            numero=str(issue_data.get('issue_number', '')),
            titulo=issue_data.get('name', ''),
            resumen=self._clean_html_text(issue_data.get('description', '')),
            fecha_tapa=fecha_tapa,
            id_volume=volume.id_volume,
            id_comicvine=issue_data.get('id')
        )

        self.session.add(new_issue)

    def _download_volume_and_issues_covers(self, volume, volume_details, detailed_issues, progress_callback=None):
        """Descargar covers del volumen y de los issues"""
        from helpers.image_downloader import download_image

        covers_downloaded = 0

        # Descargar cover del volumen
        if volume_details.get('image') and volume_details['image'].get('medium_url'):
            try:
                if progress_callback:
                    progress_callback("Descargando cover del volumen...")

                cover_url = volume_details['image']['medium_url']
                cover_path = download_image(cover_url, "data/thumbnails/volumes", f"{volume.id_volume}.jpg")

                if cover_path:
                    volume.image_url = cover_url
                    covers_downloaded += 1
                    print(f"✅ Cover del volumen descargado: {cover_path}")
            except Exception as e:
                print(f"❌ Error descargando cover del volumen: {e}")

        # Descargar covers de issues en background (sin bloquear)
        if detailed_issues:
            if progress_callback:
                progress_callback(f"Iniciando descarga de covers de {len(detailed_issues)} issues...")

            import threading
            cover_thread = threading.Thread(
                target=self._download_issues_covers_background,
                args=(volume, detailed_issues, progress_callback),
                daemon=True
            )
            cover_thread.start()

        return covers_downloaded

    def _download_issues_covers_background(self, volume, detailed_issues, progress_callback=None):
        """Descargar covers de issues en background thread"""
        from helpers.image_downloader import download_image

        covers_downloaded = 0
        total_issues = len(detailed_issues)

        for i, issue_data in enumerate(detailed_issues):
            try:
                if issue_data.get('image') and issue_data['image'].get('medium_url'):
                    issue_number = issue_data.get('issue_number', 'unknown')
                    cover_url = issue_data['image']['medium_url']

                    # Crear nombre de archivo basado en volumen e issue
                    filename = f"{volume.id_volume}_{issue_number}.jpg"
                    cover_path = download_image(cover_url, "data/thumbnails/issues", filename)

                    if cover_path:
                        covers_downloaded += 1

                    # Reportar progreso cada 5 covers
                    if progress_callback and i % 5 == 0:
                        progress_callback(f"Covers descargados: {covers_downloaded}/{i+1} issues procesados")

            except Exception as e:
                print(f"Error descargando cover del issue {issue_data.get('issue_number', 'N/A')}: {e}")

        if progress_callback:
            progress_callback(f"✅ Descarga de covers completada: {covers_downloaded} covers de issues")

    def _clean_html_text(self, html_text):
        """Limpiar texto HTML para almacenar en base de datos"""
        if not html_text:
            return ''

        import re
        # Remover tags HTML básicos
        clean_text = re.sub(r'<[^>]+>', '', html_text)
        # Decodificar entidades HTML comunes
        clean_text = clean_text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        clean_text = clean_text.replace('&quot;', '"').replace('&#39;', "'")

        return clean_text.strip()
