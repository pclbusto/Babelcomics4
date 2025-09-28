#!/usr/bin/env python3
"""
Schema Manager - Herramienta para gestionar esquemas SQLAlchemy con GTK4 + libadwaita
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Optional, Set
from datetime import datetime

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GObject, Gio, GLib
from sqlalchemy import create_engine, inspect, text, MetaData, Table
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# SOLUCIÓN SIMPLE: Registrar modelos manualmente
try:
    # Importar los modelos
    from entidades.comicbook_detail_model import Comicbook_Detail
    from entidades.comicbook_info_cover_model import ComicbookInfoCover
    from entidades.comicbook_info_model import ComicbookInfo
    from entidades.comicbook_model import Comicbook
    from entidades.publisher_model import Publisher
    from entidades.setup_model import Setup
    from entidades.volume_model import Volume
    from entidades.volume_search_model import VolumeSearch
    
    # Crear una Base nueva
    Base = declarative_base()
    
    # Lista de todos los modelos importados
    all_models = [
        Comicbook_Detail, ComicbookInfoCover, ComicbookInfo,
        Comicbook, Publisher, Setup, Volume, VolumeSearch
    ]
    
    # Registrar cada tabla en nuestra Base manualmente
    for model in all_models:
        if hasattr(model, '__table__'):
            # Copiar la tabla al metadata de nuestra Base
            original_table = model.__table__
            table_copy = original_table.tometadata(Base.metadata, schema=original_table.schema)
            print(f"Registrada tabla: {original_table.name}")
    
    print(f"Modelos registrados correctamente. Tablas: {list(Base.metadata.tables.keys())}")
    
except ImportError as e:
    print(f"Error al importar modelos: {e}")
    Base = declarative_base()
except Exception as e:
    print(f"Error al registrar modelos: {e}")
    Base = declarative_base()

class TableStatus:
    """Estados de las tablas"""
    MISSING = "Falta"
    OK = "OK" 
    EXISTS_UNDECLARED = "Existe (no declarada)"

class TableInfo(GObject.Object):
    """Información de una tabla para el modelo de datos"""
    
    __gtype_name__ = 'TableInfo'
    
    def __init__(self, name: str, status: str, selectable: bool = True):
        super().__init__()
        self.name = name
        self.status = status
        self.selectable = selectable
        self.selected = False

class SchemaManagerWindow(Adw.ApplicationWindow):
    """Ventana principal de Schema Manager"""
    
    def __init__(self, app, db_path: str):
        super().__init__(application=app)
        self.db_path = db_path
        self.engine = None
        self.tables_info: List[TableInfo] = []
        
        # Configurar ventana
        self.set_title("Schema Manager")
        self.set_default_size(900, 700)
        
        # Crear UI
        self._build_ui()
        
        # Conectar a la base de datos automáticamente
        self._connect_database()
    
    def _build_ui(self):
        """Construir la interfaz de usuario"""
        
        # ToolbarView principal
        self.toolbar_view = Adw.ToolbarView()
        self.set_content(self.toolbar_view)
        
        # HeaderBar con botones
        self._build_headerbar()
        
        # Contenido principal con Paned
        self.paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        self.paned.set_position(400)
        self.paned.set_margin_start(12)
        self.paned.set_margin_end(12)
        self.paned.set_margin_bottom(12)
        
        # Lista de tablas (parte superior)
        self._build_tables_list()
        
        # Log (parte inferior)
        self._build_log_area()
        
        self.toolbar_view.set_content(self.paned)
    
    def _build_headerbar(self):
        """Construir HeaderBar con botones"""
        
        headerbar = Adw.HeaderBar()
        self.toolbar_view.add_top_bar(headerbar)
        
        # Botón Conectar
        self.connect_btn = Gtk.Button(label="Conectar")
        self.connect_btn.add_css_class("suggested-action")
        self.connect_btn.connect("clicked", self._on_connect_clicked)
        headerbar.pack_start(self.connect_btn)
        
        # Botón Refrescar
        self.refresh_btn = Gtk.Button(label="Refrescar")
        self.refresh_btn.connect("clicked", self._on_refresh_clicked)
        headerbar.pack_start(self.refresh_btn)
        
        # Botones de acción (lado derecho)
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        # Botón Crear seleccionadas
        self.create_btn = Gtk.Button(label="Crear seleccionadas")
        self.create_btn.add_css_class("success")
        self.create_btn.set_sensitive(False)
        self.create_btn.connect("clicked", self._on_create_selected_clicked)
        action_box.append(self.create_btn)
        
        # Botón Recrear seleccionadas
        self.recreate_btn = Gtk.Button(label="Recrear seleccionadas")
        self.recreate_btn.add_css_class("destructive-action")
        self.recreate_btn.set_sensitive(False)
        self.recreate_btn.connect("clicked", self._on_recreate_selected_clicked)
        action_box.append(self.recreate_btn)
        
        headerbar.pack_end(action_box)
    
    def _build_tables_list(self):
        """Construir lista de tablas"""
        
        # Contenedor con título
        list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        # Título
        title_label = Gtk.Label(label="Tablas de la Base de Datos")
        title_label.add_css_class("title-4")
        title_label.set_halign(Gtk.Align.START)
        title_label.set_margin_bottom(6)
        list_box.append(title_label)
        
        # ScrolledWindow para la lista
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        
        # ListView
        self.tables_model = Gio.ListStore(item_type=TableInfo)
        self.tables_selection = Gtk.NoSelection(model=self.tables_model)
        
        self.tables_listview = Gtk.ListView(model=self.tables_selection)
        
        # Factory para crear filas
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._on_listitem_setup)
        factory.connect("bind", self._on_listitem_bind)
        self.tables_listview.set_factory(factory)
        
        scrolled.set_child(self.tables_listview)
        list_box.append(scrolled)
        
        self.paned.set_start_child(list_box)
    
    def _build_log_area(self):
        """Construir área de log"""
        
        log_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        # Título del log
        log_title = Gtk.Label(label="Registro de Actividad")
        log_title.add_css_class("title-4")
        log_title.set_halign(Gtk.Align.START)
        log_title.set_margin_bottom(6)
        log_box.append(log_title)
        
        # ScrolledWindow para el TextView
        log_scrolled = Gtk.ScrolledWindow()
        log_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        log_scrolled.set_vexpand(True)
        log_scrolled.set_min_content_height(150)
        
        # TextView para el log
        self.log_textview = Gtk.TextView()
        self.log_textview.set_editable(False)
        self.log_textview.set_monospace(True)
        self.log_textview.add_css_class("card")
        
        self.log_buffer = self.log_textview.get_buffer()
        
        log_scrolled.set_child(self.log_textview)
        log_box.append(log_scrolled)
        
        self.paned.set_end_child(log_box)
        
        # Mensaje inicial
        self._log_message("Schema Manager iniciado")
    
    def _on_listitem_setup(self, factory, list_item):
        """Configurar elementos de la lista"""
        
        # Crear contenedor principal
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(8)
        box.set_margin_bottom(8)
        
        # Checkbox
        checkbox = Gtk.CheckButton()
        checkbox.set_name("checkbox")
        box.append(checkbox)
        
        # Información de la tabla
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        info_box.set_hexpand(True)
        
        # Nombre de la tabla
        name_label = Gtk.Label()
        name_label.set_name("name_label")
        name_label.add_css_class("title-4")
        name_label.set_halign(Gtk.Align.START)
        info_box.append(name_label)
        
        # Estado
        status_label = Gtk.Label()
        status_label.set_name("status_label")
        status_label.add_css_class("caption")
        status_label.set_halign(Gtk.Align.START)
        info_box.append(status_label)
        
        box.append(info_box)
        
        list_item.set_child(box)
    
    def _on_listitem_bind(self, factory, list_item):
        """Vincular datos a elementos de la lista"""
        
        table_info = list_item.get_item()
        box = list_item.get_child()
        
        # Obtener widgets
        checkbox = None
        name_label = None
        status_label = None
        
        for child in box:
            if child.get_name() == "checkbox":
                checkbox = child
            elif isinstance(child, Gtk.Box):
                for subchild in child:
                    if subchild.get_name() == "name_label":
                        name_label = subchild
                    elif subchild.get_name() == "status_label":
                        status_label = subchild
        
        if checkbox and name_label and status_label:
            # Configurar checkbox
            checkbox.set_sensitive(table_info.selectable)
            checkbox.set_active(table_info.selected)
            checkbox.connect("toggled", self._on_table_toggled, table_info)
            
            # Configurar labels
            name_label.set_text(table_info.name)
            status_label.set_text(table_info.status)
            
            # Aplicar estilos según el estado
            if table_info.status == TableStatus.MISSING:
                status_label.add_css_class("error")
            elif table_info.status == TableStatus.OK:
                status_label.add_css_class("success")
            else:  # EXISTS_UNDECLARED
                status_label.add_css_class("warning")
    
    def _on_table_toggled(self, checkbox, table_info):
        """Manejar cambio en checkbox de tabla"""
        table_info.selected = checkbox.get_active()
        self._update_action_buttons()
    
    def _update_action_buttons(self):
        """Actualizar estado de botones de acción"""
        has_selection = any(t.selected for t in self.tables_info)
        self.create_btn.set_sensitive(has_selection)
        self.recreate_btn.set_sensitive(has_selection)
    
    def _connect_database(self):
        """Conectar a la base de datos"""
        try:
            # Crear directorio si no existe
            db_path = Path(self.db_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Crear engine con foreign keys habilitadas
            self.engine = create_engine(
                f"sqlite:///{self.db_path}",
                echo=False,
                connect_args={"check_same_thread": False}
            )
            
            # Habilitar foreign keys
            with self.engine.connect() as conn:
                conn.execute(text("PRAGMA foreign_keys=ON"))
                conn.commit()
            
            self._log_message(f"Conectado a base de datos: {self.db_path}")
            self._refresh_tables()
            
        except Exception as e:
            self._log_error(f"Error al conectar a la base de datos: {e}")
    
    def _refresh_tables(self):
        """Refrescar lista de tablas comparando metadata vs DB"""
        if not self.engine:
            self._log_error("No hay conexión a la base de datos")
            return
        
        try:
            # Diagnóstico: Mostrar información de debugging
            self._log_message("=== DIAGNÓSTICO ===")
            self._log_message(f"Base.metadata.tables registradas: {list(Base.metadata.tables.keys())}")
            
            # Obtener tablas existentes en la DB
            inspector = inspect(self.engine)
            existing_tables = set(inspector.get_table_names())
            self._log_message(f"Tablas existentes en DB: {list(existing_tables)}")
            
            # Obtener tablas declaradas en metadata
            declared_tables = set(Base.metadata.tables.keys())
            self._log_message(f"Tablas declaradas en metadata: {list(declared_tables)}")
            
            # Mostrar información detallada de cada tabla en metadata
            for table_name, table in Base.metadata.tables.items():
                self._log_message(f"Tabla '{table_name}': {table.__class__.__name__} - Columnas: {len(table.columns)}")
            
            self._log_message("=== FIN DIAGNÓSTICO ===")
            
            # Limpiar lista actual
            self.tables_info.clear()
            self.tables_model.remove_all()
            
            # Tablas declaradas pero faltantes
            missing_tables = declared_tables - existing_tables
            for table_name in sorted(missing_tables):
                table_info = TableInfo(table_name, TableStatus.MISSING, True)
                self.tables_info.append(table_info)
                self.tables_model.append(table_info)
            
            # Tablas que existen y están declaradas
            ok_tables = declared_tables & existing_tables
            for table_name in sorted(ok_tables):
                table_info = TableInfo(table_name, TableStatus.OK, True)
                self.tables_info.append(table_info)
                self.tables_model.append(table_info)
            
            # Tablas que existen pero no están declaradas
            undeclared_tables = existing_tables - declared_tables
            for table_name in sorted(undeclared_tables):
                table_info = TableInfo(table_name, TableStatus.EXISTS_UNDECLARED, False)
                self.tables_info.append(table_info)
                self.tables_model.append(table_info)
            
            self._log_message(f"Tablas analizadas: {len(missing_tables)} faltantes, "
                            f"{len(ok_tables)} OK, {len(undeclared_tables)} no declaradas")
            
            self._update_action_buttons()
            
        except Exception as e:
            self._log_error(f"Error al refrescar tablas: {e}")
    
    def _get_selected_tables(self) -> List[TableInfo]:
        """Obtener tablas seleccionadas"""
        return [t for t in self.tables_info if t.selected and t.selectable]
    
    def _create_selected_tables(self):
        """Crear tablas seleccionadas"""
        selected = self._get_selected_tables()
        if not selected:
            return
        
        try:
            # Obtener tablas en orden de dependencias
            sorted_tables = Base.metadata.sorted_tables
            tables_to_create = []
            
            # Filtrar solo las seleccionadas manteniendo orden
            selected_names = {t.name for t in selected}
            for table in sorted_tables:
                if table.name in selected_names:
                    tables_to_create.append(table)
            
            # Crear tablas
            success_count = 0
            for table in tables_to_create:
                try:
                    table.create(self.engine, checkfirst=True)
                    self._log_message(f"Tabla creada: {table.name}")
                    success_count += 1
                except Exception as e:
                    self._log_error(f"Error al crear tabla {table.name}: {e}")
            
            self._log_message(f"Proceso completado: {success_count}/{len(tables_to_create)} tablas creadas")
            
            # Refrescar lista
            self._refresh_tables()
            
        except Exception as e:
            self._log_error(f"Error en creación de tablas: {e}")
    
    def _recreate_selected_tables(self):
        """Recrear tablas seleccionadas (con confirmación)"""
        selected = self._get_selected_tables()
        if not selected:
            return
        
        # Crear diálogo de confirmación
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading="⚠️ Confirmar Recreación",
            body=f"¿Estás seguro de que quieres recrear {len(selected)} tabla(s)?\n\n"
                 "ADVERTENCIA: Esto eliminará todos los datos existentes en estas tablas.",
            body_use_markup=True
        )
        
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("recreate", "Recrear")
        dialog.set_response_appearance("recreate", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        
        dialog.connect("response", self._on_recreate_dialog_response, selected)
        dialog.present()
    
    def _on_recreate_dialog_response(self, dialog, response_id, selected_tables):
        """Manejar respuesta del diálogo de recreación"""
        if response_id == "recreate":
            self._perform_recreate(selected_tables)
    
    def _perform_recreate(self, selected_tables: List[TableInfo]):
        """Realizar recreación de tablas"""
        try:
            # Obtener tablas en orden inverso para drop (por dependencias)
            sorted_tables = list(reversed(Base.metadata.sorted_tables))
            tables_to_recreate = []
            
            # Filtrar solo las seleccionadas
            selected_names = {t.name for t in selected_tables}
            for table in sorted_tables:
                if table.name in selected_names:
                    tables_to_recreate.append(table)
            
            # Primero drop en orden inverso
            dropped_count = 0
            for table in tables_to_recreate:
                try:
                    table.drop(self.engine, checkfirst=True)
                    self._log_message(f"Tabla eliminada: {table.name}")
                    dropped_count += 1
                except Exception as e:
                    self._log_error(f"Error al eliminar tabla {table.name}: {e}")
            
            # Luego crear en orden normal
            created_count = 0
            tables_to_recreate.reverse()  # Volver al orden normal
            for table in tables_to_recreate:
                try:
                    table.create(self.engine, checkfirst=True)
                    self._log_message(f"Tabla recreada: {table.name}")
                    created_count += 1
                except Exception as e:
                    self._log_error(f"Error al recrear tabla {table.name}: {e}")
            
            self._log_message(f"Recreación completada: {created_count}/{len(tables_to_recreate)} tablas")
            
            # Refrescar lista
            self._refresh_tables()
            
        except Exception as e:
            self._log_error(f"Error en recreación de tablas: {e}")
    
    def _on_connect_clicked(self, button):
        """Manejar clic en botón Conectar"""
        self._connect_database()
    
    def _on_refresh_clicked(self, button):
        """Manejar clic en botón Refrescar"""
        self._refresh_tables()
    
    def _on_create_selected_clicked(self, button):
        """Manejar clic en botón Crear seleccionadas"""
        self._create_selected_tables()
    
    def _on_recreate_selected_clicked(self, button):
        """Manejar clic en botón Recrear seleccionadas"""
        self._recreate_selected_tables()
    
    def _log_message(self, message: str):
        """Agregar mensaje al log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # Agregar al buffer
        end_iter = self.log_buffer.get_end_iter()
        self.log_buffer.insert(end_iter, log_entry)
        
        # Scroll al final
        mark = self.log_buffer.get_insert()
        self.log_textview.scroll_mark_onscreen(mark)
        
        # También log a consola
        logger.info(message)
    
    def _log_error(self, message: str):
        """Agregar error al log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] ERROR: {message}\n"
        
        # Agregar al buffer
        end_iter = self.log_buffer.get_end_iter()
        self.log_buffer.insert(end_iter, log_entry)
        
        # Scroll al final
        mark = self.log_buffer.get_insert()
        self.log_textview.scroll_mark_onscreen(mark)
        
        # También log a consola
        logger.error(message)

class SchemaManagerApp(Adw.Application):
    """Aplicación principal de Schema Manager"""
    
    def __init__(self, db_path: str):
        super().__init__(application_id="com.example.SchemaManager")
        self.db_path = db_path
    
    def do_activate(self):
        """Activar aplicación"""
        window = SchemaManagerWindow(self, self.db_path)
        window.present()

def get_database_path() -> str:
    """Obtener ruta de la base de datos desde argumentos o variable de entorno"""
    
    # Parsear argumentos
    parser = argparse.ArgumentParser(description="Schema Manager - Gestión de esquemas SQLAlchemy")
    parser.add_argument(
        "--db-path", 
        type=str, 
        help="Ruta a la base de datos SQLite"
    )
    
    args, unknown = parser.parse_known_args()
    
    # Prioridad: argumento > variable de entorno > por defecto
    if args.db_path:
        return args.db_path
    
    env_path = os.environ.get("SCHEMA_MANAGER_DB_PATH")
    if env_path:
        return env_path
    
    return "data/babelcomics.db"

def main():
    """Función principal"""
    
    # Obtener ruta de la base de datos
    db_path = get_database_path()
    
    print(f"Schema Manager iniciando con base de datos: {db_path}")
    
    # IMPORTANTE: Aquí debes importar todos tus modelos
    # Ejemplo:
    # try:
    #     from your_app.models import comicbook_model, comicbook_detail_model, comicbook_info_cover_model
    #     print("Modelos importados correctamente")
    # except ImportError as e:
    #     print(f"Error al importar modelos: {e}")
    #     print("Asegúrate de que tus modelos estén en el PYTHONPATH")
    
    # Crear y ejecutar aplicación
    app = SchemaManagerApp(db_path)
    return app.run(sys.argv)

if __name__ == "__main__":
    sys.exit(main())