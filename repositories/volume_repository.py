from entidades.volume_model import Volume
from .base_repository import BaseRepository

class VolumeRepository(BaseRepository):
    def __init__(self, session):
        super().__init__(session)

    def _generate_cover_embedding(self, cover_record, image_path):
        """
        Genera embedding para una cover recién descargada.
        Se llama automáticamente después de descargar una cover.
        """
        try:
            import os
            if not os.path.exists(image_path):
                print(f"⚠️ No se puede generar embedding: imagen no existe en {image_path}")
                return False

            # Evitar cargar el modelo si la imagen no existe o si ya tiene embedding
            if cover_record.embedding:
                print(f"✓ Cover ya tiene embedding, omitiendo...")
                return True

            from helpers.embedding_generator import get_embedding_generator

            emb_gen = get_embedding_generator()
            embedding = emb_gen.generate_embedding(image_path)

            if embedding is not None:
                cover_record.embedding = emb_gen.embedding_to_json(embedding)
                self.session.flush()  # Usar flush en vez de commit para no cerrar la transacción padre
                print(f"✓ Embedding generado para cover {cover_record.id_cover}")
                return True
            else:
                print(f"⚠️ No se pudo generar embedding para {image_path}")
                return False

        except Exception as e:
            print(f"❌ Error generando embedding: {e}")
            return False

    def obtener_total(self, modelo=None):
        return super().obtener_total(modelo or Volume)

    def obtener_pagina(self, pagina, tamanio, orden="nombre", direccion="asc", columnas=None):
        """Obtener página de volúmenes con filtros avanzados"""
        # Usar columnas si están definidas, sino el modelo completo
        if columnas:
            query = self.session.query(*[getattr(Volume, col) for col in columnas])
        else:
            query = self.session.query(Volume)

        # Aplicar filtros avanzados
        for campo, valor in self.filtros.items():
            if campo == 'name_multiple_terms':
                # Filtro especial para múltiples términos (AND)
                for term in valor:
                    print(f"🔗 Filtrando volumen por término (AND): {term}")
                    query = query.filter(Volume.nombre.ilike(f"%{term}%"))
            elif campo == 'name_exclude_terms':
                # Filtro especial para exclusión de términos (NOT)
                for term in valor:
                    print(f"🚫 Excluyendo término en volumen: {term}")
                    query = query.filter(~Volume.nombre.ilike(f"%{term}%"))
            elif campo == 'name_año_numero':
                # Filtro especial para búsquedas con años/números
                for numero in valor:
                    print(f"📅 Filtrando volumen por año/número: {numero}")
                    query = query.filter(Volume.nombre.ilike(f"%{numero}%"))
            elif campo == 'year_range':
                # Filtro de rango de años
                min_year, max_year = valor
                print(f"📅 Filtrando volumen por rango de años: {min_year}-{max_year}")
                query = query.filter(Volume.anio_inicio.between(min_year, max_year))
            elif campo == 'count_range':
                # Filtro de rango de cantidad de números
                min_count, max_count = valor
                print(f"📊 Filtrando volumen por rango de números: {min_count}-{max_count}")
                query = query.filter(Volume.cantidad_numeros.between(min_count, max_count))
            elif campo == 'publisher_name':
                # Filtro por nombre de editorial (requiere join)
                from entidades.publisher_model import Publisher
                print(f"🏢 Filtrando volumen por editorial: {valor}")
                query = query.join(Publisher, Volume.id_publisher == Publisher.id_publisher).filter(
                    Publisher.nombre.ilike(f"%{valor}%")
                )
            elif hasattr(Volume, campo):
                # Filtro normal
                query = query.filter(getattr(Volume, campo).ilike(f"%{valor}%"))

        # Aplicar orden
        if hasattr(Volume, orden):
            campo_orden = getattr(Volume, orden)
            campo_orden = campo_orden.desc() if direccion == "desc" else campo_orden.asc()
            query = query.order_by(campo_orden)

        return query.offset(pagina * tamanio).limit(tamanio).all()

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

        print(f"🔍 DEBUG: Iniciando _process_volume_issues para volumen {volume.nombre}")
        print(f"🔍 DEBUG: Volume ID: {volume.id_volume}")
        print(f"🔍 DEBUG: Issues recibidos: {len(detailed_issues)}")

        new_issues_count = 0
        updated_issues_count = 0

        for i, issue_data in enumerate(detailed_issues):
            try:
                if progress_callback and i % 10 == 0:  # Reportar cada 10 issues
                    progress_callback(f"Procesando issues... {i+1}/{len(detailed_issues)}")

                issue_number = issue_data.get('issue_number')
                issue_id = issue_data.get('id')
                issue_name = issue_data.get('name', 'Sin título')

                print(f"🔍 DEBUG Issue {i+1}: #{issue_number} - {issue_name} (CV ID: {issue_id})")

                if not issue_number:
                    print(f"⚠️ Issue sin número, saltando: {issue_data}")
                    continue

                # Buscar si ya existe este issue
                existing_issue = self.session.query(ComicbookInfo).filter(
                    ComicbookInfo.id_volume == volume.id_volume,
                    ComicbookInfo.numero == str(issue_number)
                ).first()

                if existing_issue:
                    print(f"✏️ Actualizando issue existente: #{issue_number}")
                    # Actualizar issue existente
                    self._update_existing_issue(existing_issue, issue_data)
                    updated_issues_count += 1
                else:
                    print(f"➕ Creando nuevo issue: #{issue_number}")
                    # Crear nuevo issue
                    self._create_new_issue(volume, issue_data)
                    new_issues_count += 1

            except Exception as e:
                print(f"❌ Error procesando issue {issue_data.get('issue_number', 'N/A')}: {e}")
                import traceback
                traceback.print_exc()

        print(f"✅ Proceso completado: {new_issues_count} nuevos, {updated_issues_count} actualizados")
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

        # Actualizar ComicVine ID y URLs siempre (para corregir datos desactualizados)
        if issue_data.get('id'):
            existing_issue.comicvine_id = issue_data['id']
            print(f"🔄 DEBUG: Actualizando ComicVine ID para issue #{existing_issue.numero}: {issue_data['id']}")

        if issue_data.get('api_detail_url'):
            existing_issue.url_api_detalle = issue_data['api_detail_url']
            print(f"🔄 DEBUG: Actualizando API URL para issue #{existing_issue.numero}")

        if issue_data.get('site_detail_url'):
            existing_issue.url_sitio_web = issue_data['site_detail_url']
            print(f"🔄 DEBUG: Actualizando site URL para issue #{existing_issue.numero}")

        # Actualizar covers - siempre verificar si hay nuevas associated_images
        print(f"📸 DEBUG: Issue #{existing_issue.numero} tiene {len(existing_issue.portadas)} covers existentes")

        # Verificar si hay associated_images que no tengamos
        associated_images = issue_data.get('associated_images', [])
        if associated_images:
            print(f"📸 Issue #{existing_issue.numero} tiene {len(associated_images)} associated_images disponibles, agregando si no existen...")
            self._create_issue_cover_records(existing_issue, issue_data)
        elif not existing_issue.portadas:
            print(f"📸 Issue #{existing_issue.numero} sin covers, agregando cover principal desde ComicVine...")
            self._create_issue_cover_records(existing_issue, issue_data)

    def _create_new_issue(self, volume, issue_data):
        """Crear un nuevo issue desde datos de ComicVine"""
        from entidades.comicbook_info_model import ComicbookInfo

        print(f"🆕 DEBUG: Creando issue para volumen ID {volume.id_volume}")
        print(f"🆕 DEBUG: Issue data: {issue_data.get('issue_number', 'N/A')} - {issue_data.get('name', 'N/A')}")

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
            comicvine_id=issue_data.get('id', 0),
            url_api_detalle=issue_data.get('api_detail_url', ''),
            url_sitio_web=issue_data.get('site_detail_url', '')
        )

        print(f"🆕 DEBUG: Issue creado - Numero: {new_issue.numero}, Titulo: {new_issue.titulo}, Volume ID: {new_issue.id_volume}")
        print(f"🆕 DEBUG: ComicVine ID: {new_issue.comicvine_id}")

        self.session.add(new_issue)
        self.session.flush()  # Para obtener el ID del issue recién creado

        print(f"🆕 DEBUG: Issue ID después de flush: {new_issue.id_comicbook_info}")

        # Crear registros de portadas si hay imágenes disponibles
        self._create_issue_cover_records(new_issue, issue_data)

        print(f"🆕 DEBUG: Issue agregado a la sesión")

    def _create_issue_cover_records(self, issue, issue_data):
        """Crear registros de portadas para un issue (principal + associated_images)"""
        from entidades.comicbook_info_cover_model import ComicbookInfoCover

        print(f"📸 DEBUG: Iniciando _create_issue_cover_records para issue #{issue.numero}")
        print(f"📸 DEBUG: Issue ID: {issue.id_comicbook_info}")
        print(f"📸 DEBUG: issue_data keys: {list(issue_data.keys())}")

        covers_created = 0

        # Obtener URLs de covers existentes para evitar duplicados
        existing_cover_urls = {cover.url_imagen for cover in issue.portadas}
        print(f"📸 DEBUG: URLs de covers existentes: {existing_cover_urls}")

        # 1. Crear cover principal si existe y no está ya guardada
        print(f"📸 DEBUG: Revisando image principal: {issue_data.get('image', {})}")
        if issue_data.get('image') and issue_data['image'].get('medium_url'):
            main_cover_url = issue_data['image']['medium_url']
            print(f"📸 DEBUG: Image principal encontrada: {main_cover_url}")

            if main_cover_url not in existing_cover_urls:
                try:
                    cover_record = ComicbookInfoCover(
                        id_comicbook_info=issue.id_comicbook_info,
                        url_imagen=main_cover_url
                    )
                    self.session.add(cover_record)
                    covers_created += 1
                    print(f"📸 Cover principal creada para issue #{issue.numero}: {main_cover_url}")
                except Exception as e:
                    print(f"❌ Error creando cover principal para issue #{issue.numero}: {e}")
            else:
                print(f"📸 Cover principal ya existe para issue #{issue.numero}: {main_cover_url}")

        # 2. Crear covers adicionales de associated_images
        associated_images = issue_data.get('associated_images', [])
        print(f"📸 DEBUG: Associated images encontradas: {len(associated_images)}")
        if associated_images:
            print(f"📸 DEBUG: Associated images data: {associated_images}")
            print(f"📸 Procesando {len(associated_images)} associated_images para issue #{issue.numero}")

            for i, img_data in enumerate(associated_images):
                try:
                    # Usar original_url si está disponible, sino buscar otras URLs
                    img_url = img_data.get('original_url')
                    if not img_url:
                        # Buscar otras posibles URLs en associated_images
                        for url_key in ['medium_url', 'super_url', 'screen_url']:
                            if img_data.get(url_key):
                                img_url = img_data[url_key]
                                break

                    if img_url:
                        if img_url not in existing_cover_urls:
                            cover_record = ComicbookInfoCover(
                                id_comicbook_info=issue.id_comicbook_info,
                                url_imagen=img_url
                            )
                            self.session.add(cover_record)
                            existing_cover_urls.add(img_url)  # Agregar a la lista para evitar duplicados en esta sesión
                            covers_created += 1
                            print(f"📸 Associated image {i+1} creada para issue #{issue.numero}: {img_url}")
                        else:
                            print(f"📸 Associated image {i+1} ya existe para issue #{issue.numero}: {img_url}")
                    else:
                        print(f"⚠️ Associated image {i+1} sin URL válida para issue #{issue.numero}")

                except Exception as e:
                    print(f"❌ Error creando associated image {i+1} para issue #{issue.numero}: {e}")

        print(f"📸 Total covers creadas para issue #{issue.numero}: {covers_created}")

    def _create_issue_cover_record(self, issue, cover_url):
        """Crear registro de portada para un issue (método legacy)"""
        from entidades.comicbook_info_cover_model import ComicbookInfoCover

        try:
            cover_record = ComicbookInfoCover(
                id_comicbook_info=issue.id_comicbook_info,
                url_imagen=cover_url
            )
            self.session.add(cover_record)
            print(f"📸 Cover record creado para issue #{issue.numero}: {cover_url}")
        except Exception as e:
            print(f"❌ Error creando cover record para issue #{issue.numero}: {e}")

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
        from entidades.comicbook_info_cover_model import ComicbookInfoCover
        import os

        covers_downloaded = 0
        embeddings_generated = 0
        total_issues = len(detailed_issues)

        for i, issue_data in enumerate(detailed_issues):
            try:
                issue_number = issue_data.get('issue_number', 'unknown')

                # Crear carpeta específica para este volumen según ComicbookInfoCover
                clean_volume_name = "".join([c if c.isalnum() or c.isspace() else "" for c in volume.nombre]).strip()
                covers_folder = os.path.join(
                    "data", "thumbnails", "comicbook_info",
                    f"{clean_volume_name}_{volume.id_volume}"
                )

                issue_covers_downloaded = 0

                # 1. Descargar cover principal
                if issue_data.get('image') and issue_data['image'].get('medium_url'):
                    cover_url = issue_data['image']['medium_url']

                    # Usar el nombre de archivo original de la URL
                    filename = cover_url.split('/')[-1]
                    if not filename.endswith(('.jpg', '.jpeg', '.png')):
                        filename = f"issue_{issue_number}.jpg"

                    cover_path = download_image(cover_url, covers_folder, filename)
                    if cover_path:
                        issue_covers_downloaded += 1

                        # Generar embedding automáticamente
                        cover_record = self.session.query(ComicbookInfoCover).filter_by(url_imagen=cover_url).first()
                        if cover_record:
                            if self._generate_cover_embedding(cover_record, cover_path):
                                embeddings_generated += 1

                # 2. Descargar associated_images
                associated_images = issue_data.get('associated_images', [])
                if associated_images:
                    print(f"📸 Descargando {len(associated_images)} associated_images para issue #{issue_number}")

                    for j, img_data in enumerate(associated_images):
                        img_url = img_data.get('original_url')
                        if not img_url:
                            # Buscar otras URLs disponibles
                            for url_key in ['medium_url', 'super_url', 'screen_url']:
                                if img_data.get(url_key):
                                    img_url = img_data[url_key]
                                    break

                        if img_url:
                            # Generar nombre único para associated image
                            filename = img_url.split('/')[-1]
                            if not filename.endswith(('.jpg', '.jpeg', '.png')):
                                filename = f"issue_{issue_number}_variant_{j+1}.jpg"
                            else:
                                # Agregar sufijo para diferenciarlo de la cover principal
                                name, ext = filename.rsplit('.', 1)
                                filename = f"{name}_variant_{j+1}.{ext}"

                            variant_path = download_image(img_url, covers_folder, filename)
                            if variant_path:
                                issue_covers_downloaded += 1
                                print(f"📸 Associated image {j+1} descargada: {filename}")

                                # Generar embedding automáticamente
                                cover_record = self.session.query(ComicbookInfoCover).filter_by(url_imagen=img_url).first()
                                if cover_record:
                                    if self._generate_cover_embedding(cover_record, variant_path):
                                        embeddings_generated += 1

                covers_downloaded += issue_covers_downloaded

                # Reportar progreso cada 5 covers
                if progress_callback and i % 5 == 0:
                    progress_callback(f"Covers descargados: {covers_downloaded}/{i+1} issues procesados")

            except Exception as e:
                print(f"Error descargando cover del issue {issue_data.get('issue_number', 'N/A')}: {e}")

        if progress_callback:
            progress_callback(f"✅ Descarga completada: {covers_downloaded} covers, {embeddings_generated} embeddings generados")

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

    def filtrar_multiple_name_terms(self, terms):
        """
        Filtrar volúmenes que contengan TODOS los términos en el nombre (AND).
        """
        if terms:
            self.filtros['name_multiple_terms'] = terms

    def filtrar_name_exclude_terms(self, exclude_terms):
        """
        Filtrar volúmenes que NO contengan ninguno de los términos en el nombre (NOT).
        """
        if exclude_terms:
            self.filtros['name_exclude_terms'] = exclude_terms

    def filtrar_año_o_numero(self, valor):
        """
        Filtrar volúmenes por año en el nombre.
        """
        if 'name_año_numero' not in self.filtros:
            self.filtros['name_año_numero'] = []
        self.filtros['name_año_numero'].append(str(valor))
