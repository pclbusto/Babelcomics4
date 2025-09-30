#!/usr/bin/env python3
"""
Cards para mostrar diferentes tipos de items: Comics, Volúmenes, Editoriales
"""

import gi
import os
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GdkPixbuf, Gdk, Pango

try:
    from entidades.comicbook_model import Comicbook
    from entidades.comicbook_info_model import ComicbookInfo
except ImportError:
    # En caso de que no estén disponibles
    Comicbook = None
    ComicbookInfo = None


class BaseCard(Gtk.Box):
    """Clase base para todas las cards"""
    
    def __init__(self, item, item_type, thumbnail_generator):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.item = item
        self.item_type = item_type
        self.thumbnail_generator = thumbnail_generator
        
        # Configurar el widget
        self.set_size_request(280, 480)
        
        # Crear tarjeta principal
        self.card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.card.add_css_class("card")
        self.card.set_margin_top(8)
        self.card.set_margin_bottom(8)
        self.card.set_margin_start(8)
        self.card.set_margin_end(8)
        
        # Contenedor de imagen
        image_container = Gtk.Box()
        image_container.set_size_request(264, 380)
        image_container.set_halign(Gtk.Align.CENTER)
        image_container.set_valign(Gtk.Align.CENTER)
        
        # Imagen
        self.image = Gtk.Picture()
        self.image.set_can_shrink(True)
        self.image.set_keep_aspect_ratio(True)
        self.image.set_content_fit(Gtk.ContentFit.CONTAIN)
        self.image.add_css_class("cover-image")
        
        # Imagen placeholder inicial
        self.set_placeholder_image()
        
        image_container.append(self.image)
        
        # Información
        self.info_box = self.create_info_box()
        
        # Añadir a la tarjeta
        self.card.append(image_container)
        self.card.append(self.info_box)
        self.append(self.card)
        
        # Solicitar thumbnail
        self.request_thumbnail()
        
    def create_info_box(self):
        """Crear caja de información - implementar en subclases"""
        return Gtk.Box()
        
    def set_placeholder_image(self):
        """Configurar imagen placeholder"""
        try:
            colors = {
                "comic": 0x3584E4FF,      # Azul
                "volume": 0x33D17AFF,     # Verde  
                "publisher": 0xF66151FF,  # Rojo
                "arc": 0x9141ACFF         # Púrpura
            }
            color = colors.get(self.item_type, 0x808080FF)
            
            pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 250, 350)
            pixbuf.fill(color)
            texture = Gdk.Texture.new_for_pixbuf(pixbuf)
            self.image.set_paintable(texture)
        except Exception as e:
            print(f"Error creando placeholder: {e}")
            
    def request_thumbnail(self):
        """Solicitar thumbnail - implementar en subclases"""
        pass
        
    def load_thumbnail(self, thumbnail_path):
        """Cargar thumbnail en la imagen"""
        try:
            if thumbnail_path and os.path.exists(thumbnail_path):
                self.image.set_filename(thumbnail_path)
                print(f"✓ Thumbnail cargado: {thumbnail_path}")
            else:
                if not thumbnail_path:
                    print("Thumbnail path is None, usando placeholder")
                else:
                    print(f"Thumbnail no encontrado: {thumbnail_path}")
                # Mantener el placeholder actual
        except Exception as e:
            print(f"Error cargando thumbnail: {e}")


class ComicCard(BaseCard):
    """Card para mostrar un comic"""
    
    def __init__(self, comic, thumbnail_generator):
        super().__init__(comic, "comic", thumbnail_generator)
        
    def create_info_box(self):
        """Crear información del comic"""
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        info_box.set_margin_start(8)
        info_box.set_margin_end(8)
        info_box.set_margin_bottom(8)
        
        # Título
        title = self.item.nombre_archivo if hasattr(self.item, 'nombre_archivo') else os.path.basename(self.item.path)
        self.title_label = Gtk.Label(label=title)
        self.title_label.set_wrap(True)
        self.title_label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.title_label.set_width_chars(35)
        self.title_label.set_max_width_chars(35)
        self.title_label.set_lines(2)
        self.title_label.set_ellipsize(Pango.EllipsizeMode.END)
        self.title_label.set_justify(Gtk.Justification.CENTER)
        self.title_label.add_css_class("heading")
        
        # Información adicional
        extra_info = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        extra_info.set_halign(Gtk.Align.CENTER)
        
        # ID
        id_label = Gtk.Label(label=f"#{self.item.id_comicbook}")
        id_label.add_css_class("dim-label")
        id_label.add_css_class("caption")
        
        # Estado
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        if self.item.is_classified:
            status_icon = Gtk.Image.new_from_icon_name("emblem-ok-symbolic")
            status_text = "Clasificado"
            status_box.add_css_class("success")
        else:
            status_icon = Gtk.Image.new_from_icon_name("dialog-warning-symbolic")
            status_text = "Sin clasificar"
            status_box.add_css_class("warning")
            
        status_icon.set_icon_size(Gtk.IconSize.INHERIT)
        status_label = Gtk.Label(label=status_text)
        status_label.add_css_class("caption")
        
        status_box.append(status_icon)
        status_box.append(status_label)
        
        # Calidad
        if self.item.calidad > 0:
            quality_text = "★" * self.item.calidad + "☆" * (5 - self.item.calidad)
            quality_label = Gtk.Label(label=quality_text)
            quality_label.add_css_class("caption")
            quality_label.add_css_class("accent")
            extra_info.append(quality_label)
        
        extra_info.append(id_label)
        extra_info.append(status_box)
        
        info_box.append(self.title_label)
        info_box.append(extra_info)
        
        return info_box
        
    def request_thumbnail(self):
        """Solicitar thumbnail del comic"""
        thumbnail_path = self.thumbnail_generator.get_cached_thumbnail_path(self.item.id_comicbook, "comics")
        print(f"Solicitando thumbnail para comic: thumbnail_path={thumbnail_path}")
        if thumbnail_path.exists():
            self.load_thumbnail(str(thumbnail_path))
        else:
            self.thumbnail_generator.request_thumbnail(
                self.item.path,
                self.item.id_comicbook,
                "comics",
                self.load_thumbnail
            )


class VolumeCard(BaseCard):
    """Card para mostrar un volumen"""
    
    def __init__(self, volume, thumbnail_generator, session):
        self.session = session
        super().__init__(volume, "volume", thumbnail_generator)
        
    def create_info_box(self):
        """Crear información del volumen"""
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        info_box.set_margin_start(8)
        info_box.set_margin_end(8)
        info_box.set_margin_bottom(8)
        
        # Título
        self.title_label = Gtk.Label(label=self.item.nombre)
        self.title_label.set_wrap(True)
        self.title_label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.title_label.set_width_chars(35)
        self.title_label.set_max_width_chars(35)
        self.title_label.set_lines(2)
        self.title_label.set_ellipsize(Pango.EllipsizeMode.END)
        self.title_label.set_justify(Gtk.Justification.CENTER)
        self.title_label.add_css_class("heading")
        
        # Información básica
        basic_info = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        basic_info.set_halign(Gtk.Align.CENTER)
        
        # ID
        id_label = Gtk.Label(label=f"#{self.item.id_volume}")
        id_label.add_css_class("caption")
        id_label.add_css_class("dim-label")
        basic_info.append(id_label)
        
        # Año
        if self.item.anio_inicio > 0:
            year_label = Gtk.Label(label=str(self.item.anio_inicio))
            year_label.add_css_class("caption")
            year_label.add_css_class("dim-label")
            basic_info.append(year_label)
        
        # Total de números
        total_label = Gtk.Label(label=f"{self.item.cantidad_numeros} nums")
        total_label.add_css_class("caption")
        total_label.add_css_class("dim-label")
        basic_info.append(total_label)
        
        # Completitud
        completion_info = self.create_completion_info()
        
        info_box.append(self.title_label)
        info_box.append(basic_info)
        info_box.append(completion_info)
        
        return info_box
        
    def create_completion_info(self):
        """Crear información de completitud del volumen"""
        completion_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        
        try:
            # Contar comics físicos para este volumen
            owned_count = 0
            
            if Comicbook and ComicbookInfo and self.session:
                # Si tenemos todas las clases necesarias
                owned_count = self.session.query(Comicbook).filter(
                    Comicbook.id_comicbook_info.in_(
                        self.session.query(ComicbookInfo.id_comicbook_info).filter(
                            ComicbookInfo.id_volume == self.item.id_volume
                        )
                    )
                ).count()
            elif Comicbook and self.session:
                # Método alternativo: buscar por coincidencia de nombres o algo similar
                # Por ahora, mostrar 0
                owned_count = 0
            else:
                print("⚠ No se puede calcular completitud - faltan dependencias")
                
            # Calcular porcentaje de completitud
            if self.item.cantidad_numeros > 0:
                completion_percentage = min(owned_count / self.item.cantidad_numeros, 1.0)
            else:
                completion_percentage = 0.0
            
            # Label de completitud
            completion_text = f"{owned_count}/{self.item.cantidad_numeros} comics"
            completion_label = Gtk.Label(label=completion_text)
            completion_label.add_css_class("caption")
            
            if completion_percentage == 1.0:
                completion_label.add_css_class("success")
            elif completion_percentage > 0.5:
                completion_label.add_css_class("accent")
            elif completion_percentage > 0:
                completion_label.add_css_class("warning")
            else:
                completion_label.add_css_class("dim-label")
            
            # Barra de progreso
            progress_bar = Gtk.ProgressBar()
            progress_bar.set_fraction(completion_percentage)
            progress_bar.set_margin_start(8)
            progress_bar.set_margin_end(8)
            progress_bar.add_css_class("completion-bar")
            
            completion_box.append(completion_label)
            completion_box.append(progress_bar)
            
        except Exception as e:
            print(f"Error calculando completitud para volumen {self.item.id_volume}: {e}")
            error_label = Gtk.Label(label="Error calculando")
            error_label.add_css_class("dim-label")
            error_label.add_css_class("caption")
            completion_box.append(error_label)
        
        return completion_box
        
    def request_thumbnail(self):
        """Solicitar thumbnail del volumen"""
        print(f"🖼️ Solicitando thumbnail para volumen: {self.item.nombre} (ID: {self.item.id_volume})")
        
        thumbnail_path = self.thumbnail_generator.get_cached_thumbnail_path(self.item.id_volume, "volumes")
        print(f"📁 Cache path: {thumbnail_path}")
        
        if thumbnail_path.exists():
            print("✅ Thumbnail existe en cache, cargando...")
            self.load_thumbnail(str(thumbnail_path))
        else:
            print("🔄 Thumbnail no existe en cache")
            
            # Intentar obtener imagen real del volumen
            try:
                cover_path = self.item.obtener_cover()
                print(f"🎨 Cover path obtenido del volumen: {cover_path}")
                
                # Verificar si es una imagen real (no la imagen por defecto)
                if cover_path and os.path.exists(cover_path) and not cover_path.endswith("Volumen_sin_caratula.png"):
                    print(f"✅ Imagen real encontrada: {cover_path}")
                    # Solo generar thumbnail si hay imagen real
                    self.thumbnail_generator.request_thumbnail(
                        cover_path,
                        self.item.id_volume,
                        "volumes",
                        self.load_thumbnail
                    )
                else:
                    print(f"⚠️ No hay imagen real disponible")
                    print(f"📊 image_url del volumen: {getattr(self.item, 'image_url', 'No definida')}")
                    
                    # Cargar directamente la imagen por defecto SIN generar thumbnail
                    self.set_placeholder_image()
                
            except Exception as e:
                print(f"❌ Error obteniendo cover: {e}")
                self.set_placeholder_image()


class PublisherCard(BaseCard):
    """Card para mostrar una editorial"""
    
    def __init__(self, publisher, thumbnail_generator, session=None):
        self.session = session
        super().__init__(publisher, "publisher", thumbnail_generator)
        
    def create_info_box(self):
        """Crear información de la editorial"""
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        info_box.set_margin_start(8)
        info_box.set_margin_end(8)
        info_box.set_margin_bottom(8)
        
        # Título
        self.title_label = Gtk.Label(label=self.item.nombre)
        self.title_label.set_wrap(True)
        self.title_label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.title_label.set_width_chars(35)
        self.title_label.set_max_width_chars(35)
        self.title_label.set_lines(2)
        self.title_label.set_ellipsize(Pango.EllipsizeMode.END)
        self.title_label.set_justify(Gtk.Justification.CENTER)
        self.title_label.add_css_class("heading")
        
        # Información básica
        basic_info = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        basic_info.set_halign(Gtk.Align.CENTER)
        
        # ID
        id_label = Gtk.Label(label=f"#{self.item.id_publisher}")
        id_label.add_css_class("caption")
        id_label.add_css_class("dim-label")
        basic_info.append(id_label)
        
        # Deck (descripción corta)
        if hasattr(self.item, 'deck') and self.item.deck:
            deck_label = Gtk.Label(label=self.item.deck[:30] + "..." if len(self.item.deck) > 30 else self.item.deck)
            deck_label.add_css_class("caption")
            deck_label.add_css_class("dim-label")
            deck_label.set_wrap(True)
            deck_label.set_max_width_chars(35)
            info_box.append(deck_label)
        
        # Estadísticas de la editorial
        stats_info = self.create_publisher_stats()
        
        info_box.append(self.title_label)
        info_box.append(basic_info)
        info_box.append(stats_info)
        
        return info_box
        
    def create_publisher_stats(self):
        """Crear estadísticas de la editorial"""
        stats_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        
        try:
            if self.session:
                # Contar volúmenes de esta editorial
                from entidades.volume_model import Volume
                volume_count = self.session.query(Volume).filter(
                    Volume.id_publisher == self.item.id_publisher
                ).count()
                
                # Mostrar estadísticas
                if volume_count > 0:
                    volume_label = Gtk.Label(label=f"{volume_count} volúmenes")
                    volume_label.add_css_class("caption")
                    volume_label.add_css_class("accent")
                    stats_box.append(volume_label)
                else:
                    no_volumes_label = Gtk.Label(label="Sin volúmenes")
                    no_volumes_label.add_css_class("caption")
                    no_volumes_label.add_css_class("dim-label")
                    stats_box.append(no_volumes_label)
                
        except Exception as e:
            print(f"Error calculando estadísticas de editorial {self.item.id_publisher}: {e}")
            
        return stats_box
        
    def request_thumbnail(self):
        """Solicitar thumbnail de la editorial"""
        print(f"🏢 Solicitando thumbnail para editorial: {self.item.nombre} (ID: {self.item.id_publisher})")
        
        thumbnail_path = self.thumbnail_generator.get_cached_thumbnail_path(self.item.id_publisher, "publishers")
        print(f"📁 Cache path: {thumbnail_path}")
        
        if thumbnail_path.exists():
            print("✅ Thumbnail existe en cache, cargando...")
            self.load_thumbnail(str(thumbnail_path))
        else:
            print("🔄 Thumbnail no existe en cache")
            
            # Intentar obtener logo real de la editorial
            try:
                logo_path = self.item.obtener_nombre_logo()
                print(f"🏷️ Logo path obtenido de la editorial: {logo_path}")
                
                # Verificar si es un logo real (no la imagen por defecto)
                if logo_path and os.path.exists(logo_path) and not logo_path.endswith("publisher_sin_logo.png"):
                    print(f"✅ Logo real encontrado: {logo_path}")
                    # Solo generar thumbnail si hay logo real
                    self.thumbnail_generator.request_thumbnail(
                        logo_path,
                        self.item.id_publisher,
                        "publishers",
                        self.load_thumbnail
                    )
                else:
                    print(f"⚠️ No hay logo real disponible")
                    print(f"📊 url_logo de la editorial: {getattr(self.item, 'url_logo', 'No definida')}")
                    
                    # Cargar directamente la imagen por defecto SIN generar thumbnail
                    self.set_placeholder_image()
                
            except Exception as e:
                print(f"❌ Error obteniendo logo: {e}")
                self.set_placeholder_image()


class ArcCard(BaseCard):
    """Card para mostrar un arco argumental (placeholder para futuro)"""
    
    def __init__(self, arc, thumbnail_generator, session=None):
        self.session = session
        super().__init__(arc, "arc", thumbnail_generator)
        
    def create_info_box(self):
        """Crear información del arco argumental"""
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        info_box.set_margin_start(8)
        info_box.set_margin_end(8)
        info_box.set_margin_bottom(8)
        
        # Título placeholder
        title = getattr(self.item, 'nombre', getattr(self.item, 'name', 'Arco Argumental'))
        self.title_label = Gtk.Label(label=title)
        self.title_label.set_wrap(True)
        self.title_label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.title_label.set_width_chars(35)
        self.title_label.set_max_width_chars(35)
        self.title_label.set_lines(2)
        self.title_label.set_ellipsize(Pango.EllipsizeMode.END)
        self.title_label.set_justify(Gtk.Justification.CENTER)
        self.title_label.add_css_class("heading")
        
        # Información básica
        basic_info = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        basic_info.set_halign(Gtk.Align.CENTER)
        
        # ID placeholder
        arc_id = getattr(self.item, 'id', getattr(self.item, 'id_arc', 0))
        id_label = Gtk.Label(label=f"#{arc_id}")
        id_label.add_css_class("caption")
        id_label.add_css_class("dim-label")
        basic_info.append(id_label)
        
        # Estado
        status_label = Gtk.Label(label="En desarrollo")
        status_label.add_css_class("caption")
        status_label.add_css_class("warning")
        basic_info.append(status_label)
        
        info_box.append(self.title_label)
        info_box.append(basic_info)
        
        return info_box
        
    def request_thumbnail(self):
        """Placeholder para thumbnail de arcos"""
        # Por ahora usar imagen por defecto
        pass