#!/usr/bin/env python3
"""
Diálogo "Acerca de" para Babelcomics4
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw
import os
import sys
from datetime import datetime

def create_about_window(parent_window=None):
    """Devuelve una Adw.AboutWindow configurada para Babelcomics4."""
    about = Adw.AboutWindow()

    if parent_window:
        about.set_transient_for(parent_window)
        about.set_modal(True)

    # Configuración básica
    about.set_application_name("Babelcomics4")
    about.set_application_icon("application-x-comic-book")
    about.set_version("1.0.0")
    about.set_comments("Gestor completo de colección de comics digitales")

    # Información del desarrollador
    about.set_developer_name("Pedro")
    about.set_translator_credits("Pedro")

    # Enlaces
    about.set_website("https://github.com/pedro/babelcomics4")
    about.add_link("Documentación", "https://github.com/pedro/babelcomics4/wiki")
    about.add_link("Reportar problemas", "https://github.com/pedro/babelcomics4/issues")

    # Secciones de créditos
    about.add_credit_section("Desarrollo", [
        "Pedro - Desarrollador Principal",
        "Claude - Asistente de Desarrollo IA"
    ])

    about.add_credit_section("Tecnologías", [
        "GTK4 - Toolkit de interfaz gráfica",
        "libadwaita - Componentes modernos de GNOME",
        "Python 3.13 - Lenguaje de programación",
        "SQLAlchemy - ORM para base de datos",
        "Pillow (PIL) - Procesamiento de imágenes",
        "ComicVine API - Base de datos de comics"
    ])

    about.add_credit_section("Formatos Soportados", [
        "CBZ - Comic Book ZIP",
        "CBR - Comic Book RAR",
        "PDF - Documentos PDF",
        "JPG, PNG, WEBP - Imágenes"
    ])

    about.add_credit_section("Características", [
        "🔍 Catalogación automática con ComicVine",
        "🖼️ Generación de thumbnails en tiempo real",
        "⚫ Efectos visuales (escala de grises)",
        "🔄 Actualizaciones concurrentes de metadata",
        "📊 Filtros avanzados y búsqueda inteligente",
        "🗃️ Base de datos SQLite robusta"
    ])

    # Información del sistema
    gtk_version = get_gtk_version()
    about.add_credit_section("Información del Sistema", [
        f"Python: {sys.version.split()[0]}",
        f"GTK: {gtk_version}",
        f"Plataforma: {sys.platform}",
        f"Directorio: {os.getcwd()}"
    ])

    # Licencia y copyright
    about.set_license(
        "Este programa es software libre: puedes redistribuirlo y/o modificarlo "
        "bajo los términos de la Licencia Pública General de GNU tal y como está "
        "publicada por la Free Software Foundation, versión 3 de la Licencia."
    )
    about.set_copyright("© 2024 Pedro")

    return about

def get_gtk_version():
    """Obtener versión de GTK"""
    try:
        return f"{Gtk.get_major_version()}.{Gtk.get_minor_version()}.{Gtk.get_micro_version()}"
    except:
        return "4.0+"


def create_about_dialog(parent_window=None):
    """Función de conveniencia para crear el diálogo"""
    dialog = create_about_window(parent_window)
    return dialog

def show_about_dialog(parent_window=None):
    """Mostrar diálogo Acerca de"""
    dialog = create_about_window(parent_window)
    dialog.present()

if __name__ == "__main__":
    # Test del diálogo
    app = Adw.Application()

    def on_activate(app):
        window = Adw.ApplicationWindow(application=app)
        window.set_title("Test About Dialog")
        window.set_default_size(400, 300)

        # Botón para mostrar About
        button = Gtk.Button(label="Mostrar Acerca de")
        button.connect('clicked', lambda b: show_about_dialog(window))

        window.set_content(button)
        window.present()

    app.connect('activate', on_activate)
    app.run(sys.argv)