#!/usr/bin/env python3
"""
Ventana de ayuda para mostrar todos los atajos de teclado disponibles en Babelcomics4
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw


class ShortcutsHelpWindow(Gtk.ShortcutsWindow):
    """Ventana de ayuda que muestra todos los shortcuts disponibles usando Gtk.ShortcutsWindow"""

    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window

        self.set_transient_for(parent_window)
        self.set_modal(True)

        self.setup_shortcuts()

    def setup_shortcuts(self):
        """Configurar la ventana de shortcuts usando Gtk.ShortcutsWindow"""

        # Crear sección principal
        section = Gtk.ShortcutsSection()
        section.set_property("section-name", "main")
        section.set_property("title", "Babelcomics4")
        section.set_property("max-height", 10)

        # Grupo: Navegación General
        general_group = Gtk.ShortcutsGroup()
        general_group.set_property("title", "Navegación General")

        general_shortcuts = [
            ("F5", "Actualizar contenido"),
            ("<Control>f", "Enfocar búsqueda"),
            ("F1", "Mostrar esta ayuda"),
            ("<Control>d", "Abrir ComicVine"),
            ("<Control>j", "Abrir Descarga de Editoriales"),
            ("<Shift><Control>f", "Filtros avanzados"),
            ("1", "Vista Comics"),
            ("2", "Vista Volúmenes"),
            ("3", "Vista Editoriales"),
            ("4", "Vista Arcos"),
        ]

        for accelerator, title in general_shortcuts:
            shortcut = Gtk.ShortcutsShortcut()
            shortcut.set_property("accelerator", accelerator)
            shortcut.set_property("title", title)
            general_group.append(shortcut)

        section.append(general_group)

        # Grupo: Multiselección
        multiselect_group = Gtk.ShortcutsGroup()
        multiselect_group.set_property("title", "Modo Multiselección")

        multiselect_shortcuts = [
            ("<Control>m", "Activar/desactivar multiselección"),
            # ("<Control>a", "Seleccionar todos"),  # TEMPORALMENTE DESHABILITADO
            # ("space", "Seleccionar/deseleccionar item actual"),  # TEMPORALMENTE DESHABILITADO
            ("Escape", "Salir del modo multiselección"),
            ("Delete", "Mover a papelera"),
        ]

        for accelerator, title in multiselect_shortcuts:
            shortcut = Gtk.ShortcutsShortcut()
            shortcut.set_property("accelerator", accelerator)
            shortcut.set_property("title", title)
            multiselect_group.append(shortcut)

        section.append(multiselect_group)

        # Grupo: Catalogación
        catalog_group = Gtk.ShortcutsGroup()
        catalog_group.set_property("title", "Catalogación")

        catalog_shortcuts = [
            ("<Shift><Control>c", "Abrir catalogación"),
            ("Delete", "Eliminar de lista (en ventana catalogación)"),
        ]

        for accelerator, title in catalog_shortcuts:
            shortcut = Gtk.ShortcutsShortcut()
            shortcut.set_property("accelerator", accelerator)
            shortcut.set_property("title", title)
            catalog_group.append(shortcut)

        section.append(catalog_group)

        # Grupo: ComicVine
        comicvine_group = Gtk.ShortcutsGroup()
        comicvine_group.set_property("title", "Descargas ComicVine")

        comicvine_shortcuts = [
            ("Escape", "Cerrar ventana"),
            ("<Control>a", "Seleccionar todos"),
            ("<Shift><Control>a", "Deseleccionar todos"),
            ("<Control>Return", "Iniciar descarga"),
            ("<Control>f", "Enfocar búsqueda"),
            ("Return", "Buscar (si campo enfocado)"),
        ]

        for accelerator, title in comicvine_shortcuts:
            shortcut = Gtk.ShortcutsShortcut()
            shortcut.set_property("accelerator", accelerator)
            shortcut.set_property("title", title)
            comicvine_group.append(shortcut)

        section.append(comicvine_group)

        # Grupo: Filtros
        filters_group = Gtk.ShortcutsGroup()
        filters_group.set_property("title", "Filtros Avanzados")

        filters_shortcuts = [
            ("<Control>Return", "Aplicar filtros"),
            ("<Shift><Control>r", "Limpiar filtros"),
            ("Escape", "Cerrar ventana"),
        ]

        for accelerator, title in filters_shortcuts:
            shortcut = Gtk.ShortcutsShortcut()
            shortcut.set_property("accelerator", accelerator)
            shortcut.set_property("title", title)
            filters_group.append(shortcut)

        section.append(filters_group)

        # Grupo: Lector
        reader_group = Gtk.ShortcutsGroup()
        reader_group.set_property("title", "Lector de Comics")

        reader_shortcuts = [
            ("Left Right", "Página anterior/siguiente"),
            ("space", "Página siguiente"),
            ("Page_Up Page_Down", "Página anterior/siguiente"),
            ("Home End", "Primera/última página"),
            ("plus minus", "Zoom in/out"),
            ("0", "Zoom 100%"),
            ("w", "Ajustar al ancho"),
            ("h", "Ajustar a la altura"),
            ("p", "Ajustar a la página"),
            ("F11", "Pantalla completa"),
            ("t", "Mostrar/ocultar barra lateral"),
            ("Escape", "Cerrar lector"),
        ]

        for accelerator, title in reader_shortcuts:
            shortcut = Gtk.ShortcutsShortcut()
            shortcut.set_property("accelerator", accelerator)
            shortcut.set_property("title", title)
            reader_group.append(shortcut)

        section.append(reader_group)

        # Agregar la sección a la ventana
        self.add_section(section)


def create_shortcuts_help_window(parent_window):
    """Factory function para crear la ventana de ayuda"""
    return ShortcutsHelpWindow(parent_window)