#!/usr/bin/env python3

import gi
import sys
import os

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Importar tus entidades y repositorios
try:
    from entidades import Base
    from entidades.comicbook_model import Comicbook
    from repositories.comicbook_repository_gtk4 import ComicbookRepository
except ImportError as e:
    print(f"Error importando: {e}")
    print("Asegúrate de que los archivos estén en las carpetas correctas")
    sys.exit(1)


class ComicCard(Gtk.Box):
    """Widget simple para mostrar un comic"""
    
    def __init__(self, comic):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.comic = comic
        
        # Configurar el widget
        self.set_size_request(180, 250)
        self.set_margin_top(8)
        self.set_margin_bottom(8)
        self.set_margin_start(8)
        self.set_margin_end(8)
        
        # Crear tarjeta
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        card.add_css_class("card")
        card.set_margin_top(12)
        card.set_margin_bottom(12)
        card.set_margin_start(12)
        card.set_margin_end(12)
        
        # Imagen placeholder
        image = Gtk.Image()
        image.set_from_icon_name("text-x-generic")
        image.set_icon_size(Gtk.IconSize.LARGE)
        image.set_size_request(120, 160)
        
        # Información del comic
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        
        # Título (nombre del archivo)
        title = comic.nombre_archivo if hasattr(comic, 'nombre_archivo') else os.path.basename(comic.path)
        title_label = Gtk.Label(label=title)
        title_label.set_wrap(True)
        title_label.set_max_width_chars(20)
        title_label.set_justify(Gtk.Justification.CENTER)
        title_label.add_css_class("heading")
        
        # ID del comic
        id_label = Gtk.Label(label=f"ID: {comic.id_comicbook}")
        id_label.add_css_class("dim-label")
        id_label.add_css_class("caption")
        
        # Estado de clasificación
        status_text = "Clasificado" if comic.is_classified else "Sin clasificar"
        status_label = Gtk.Label(label=status_text)
        status_label.add_css_class("caption")
        if comic.is_classified:
            status_label.add_css_class("success")
        else:
            status_label.add_css_class("warning")
        
        # Calidad
        if comic.calidad > 0:
            quality_text = "★" * comic.calidad + "☆" * (5 - comic.calidad)
            quality_label = Gtk.Label(label=quality_text)
            quality_label.add_css_class("caption")
            info_box.append(quality_label)
        
        # Añadir elementos al info_box
        info_box.append(title_label)
        info_box.append(id_label)
        info_box.append(status_label)
        
        # Añadir elementos a la tarjeta
        card.append(image)
        card.append(info_box)
        
        # Añadir tarjeta al contenedor principal
        self.append(card)
        
        # Intentar cargar imagen real
        self.load_cover_image(image)
        
    def load_cover_image(self, image_widget):
        """Intentar cargar la portada real del comic"""
        try:
            cover_path = self.comic.obtener_cover()
            if cover_path and os.path.exists(cover_path):
                image_widget.set_from_file(cover_path)
                print(f"Imagen cargada: {cover_path}")
            else:
                print(f"No se encontró imagen para: {self.comic.path}")
        except Exception as e:
            print(f"Error cargando imagen: {e}")


class ComicManagerWindow(Adw.ApplicationWindow):
    """Ventana principal de la aplicación"""
    
    def __init__(self, app):
        super().__init__(application=app)
        
        # Configurar ventana
        self.set_title("Comic Manager")
        self.set_default_size(1000, 700)
        
        # Inicializar base de datos
        self.init_database()
        
        # Crear interfaz
        self.setup_ui()
        
        # Cargar comics
        self.load_comics()
        
    def init_database(self):
        """Inicializar conexión a base de datos"""
        try:
            # Cambiar la ruta por tu base de datos
            db_path = "data/babelcomics.db"
            if not os.path.exists(db_path):
                print(f"⚠ Base de datos no encontrada en: {db_path}")
                print("Creando base de datos nueva...")
                
            engine = create_engine(f'sqlite:///{db_path}', echo=False)
            Base.metadata.create_all(engine)
            Session = sessionmaker(bind=engine)
            self.session = Session()
            
            self.comic_repository = ComicbookRepository(self.session)
            print("✓ Base de datos inicializada correctamente")
            
        except Exception as e:
            print(f"✗ Error inicializando base de datos: {e}")
            self.session = None
            self.comic_repository = None
            
    def setup_ui(self):
        """Configurar interfaz de usuario"""
        # Box principal
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Header Bar
        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label="Comic Manager"))
        
        # Botón actualizar
        refresh_button = Gtk.Button()
        refresh_button.set_icon_name("view-refresh-symbolic")
        refresh_button.set_tooltip_text("Actualizar lista")
        refresh_button.connect("clicked", self.on_refresh_clicked)
        header.pack_end(refresh_button)
        
        # Botón información
        info_button = Gtk.Button()
        info_button.set_icon_name("dialog-information-symbolic")
        info_button.set_tooltip_text("Información")
        info_button.connect("clicked", self.on_info_clicked)
        header.pack_end(info_button)
        
        main_box.append(header)
        
        # Barra de estado
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        status_box.set_margin_start(12)
        status_box.set_margin_end(12)
        status_box.set_margin_top(8)
        status_box.set_margin_bottom(8)
        
        self.status_label = Gtk.Label(label="Cargando...")
        self.status_label.set_hexpand(True)
        self.status_label.set_halign(Gtk.Align.START)
        
        self.count_label = Gtk.Label(label="0 comics")
        self.count_label.add_css_class("dim-label")
        
        status_box.append(self.status_label)
        status_box.append(self.count_label)
        main_box.append(status_box)
        
        # Separador
        separator = Gtk.Separator()
        main_box.append(separator)
        
        # Área de scroll para los comics
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        
        # FlowBox para mostrar los comics en cuadrícula
        self.flow_box = Gtk.FlowBox()
        self.flow_box.set_valign(Gtk.Align.START)
        self.flow_box.set_max_children_per_line(8)
        self.flow_box.set_min_children_per_line(2)
        self.flow_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.flow_box.set_margin_top(12)
        self.flow_box.set_margin_bottom(12)
        self.flow_box.set_margin_start(12)
        self.flow_box.set_margin_end(12)
        
        scrolled.set_child(self.flow_box)
        main_box.append(scrolled)
        
        # Configurar como contenido principal
        self.set_content(main_box)
        
    def load_comics(self):
        """Cargar comics desde la base de datos"""
        if not self.comic_repository or not self.session:
            self.status_label.set_text("Error: No hay conexión a la base de datos")
            self.count_label.set_text("0 comics")
            return
            
        try:
            # Limpiar comics existentes
            while True:
                child = self.flow_box.get_first_child()
                if child:
                    self.flow_box.remove(child)
                else:
                    break
            
            # Obtener comics del repositorio
            comics = self.comic_repository.obtener_todos_los_comics()
            
            print(f"Encontrados {len(comics)} comics en la base de datos")
            
            if not comics:
                # Mostrar mensaje cuando no hay comics
                no_comics_label = Gtk.Label(label="No hay comics en la base de datos")
                no_comics_label.add_css_class("title-2")
                no_comics_label.add_css_class("dim-label")
                no_comics_label.set_margin_top(50)
                self.flow_box.append(no_comics_label)
                
                self.status_label.set_text("Base de datos vacía")
                self.count_label.set_text("0 comics")
                return
            
            # Crear widgets para cada comic
            for comic in comics[:50]:  # Limitar a 50 para prueba
                try:
                    comic_card = ComicCard(comic)
                    self.flow_box.append(comic_card)
                except Exception as e:
                    print(f"Error creando card para comic {comic.id_comicbook}: {e}")
            
            # Actualizar estado
            self.status_label.set_text("Comics cargados correctamente")
            self.count_label.set_text(f"{len(comics)} comics")
            
        except Exception as e:
            print(f"Error cargando comics: {e}")
            self.status_label.set_text(f"Error cargando comics: {e}")
            self.count_label.set_text("0 comics")
            
    def on_refresh_clicked(self, button):
        """Actualizar lista de comics"""
        print("Actualizando lista de comics...")
        self.status_label.set_text("Actualizando...")
        GLib.idle_add(self.load_comics)
        
    def on_info_clicked(self, button):
        """Mostrar información de la aplicación"""
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading("Comic Manager")
        dialog.set_body("Gestor simple de comics\nDesarrollado con GTK4 y Libadwaita")
        dialog.add_response("ok", "OK")
        dialog.set_default_response("ok")
        dialog.set_close_response("ok")
        dialog.present()


class ComicManagerApp(Adw.Application):
    """Aplicación principal"""
    
    def __init__(self):
        super().__init__(application_id="com.example.comicmanager")
        
    def do_activate(self):
        """Activar aplicación"""
        window = ComicManagerWindow(self)
        window.present()


def main():
    """Función principal"""
    print("🚀 Iniciando Comic Manager...")
    
    # Verificar que los módulos necesarios existan
    required_files = [
        "entidades/__init__.py",
        "entidades/comicbook_model.py", 
        "repositories/__init__.py",
        "repositories/comicbook_repository_gtk4.py"
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"✗ Archivo requerido no encontrado: {file_path}")
            return 1
            
    print("✓ Archivos requeridos encontrados")
    
    # Crear aplicación
    app = ComicManagerApp()
    return app.run(sys.argv)


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)