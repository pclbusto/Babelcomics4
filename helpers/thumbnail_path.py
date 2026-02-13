#!/usr/bin/env python3
"""
Módulo centralizado para la gestión de la ruta base de thumbnails.
Mantiene un cache en memoria para evitar queries repetitivas a la BD.
"""

import os

# Cache en memoria de la ruta base
_thumbnails_base_path = "data/thumbnails"

# Subdirectorios estándar de thumbnails
THUMBNAIL_SUBDIRS = [
    "comics",
    "volumes",
    "publishers",
    "comicbook_info",
    "editoriales",
    "comic_pages",
    "comicinfo",
]


def initialize(path=None):
    """
    Inicializa el cache con la ruta de la BD.
    Se llama al arrancar la app con el valor de carpeta_thumbnails.
    """
    global _thumbnails_base_path
    if path and path.strip():
        _thumbnails_base_path = path.strip()
    else:
        _thumbnails_base_path = "data/thumbnails"


def get_thumbnails_base_path():
    """Devuelve la ruta base configurada para thumbnails."""
    return _thumbnails_base_path


def set_thumbnails_base_path(path):
    """Actualiza el cache en memoria (cuando el usuario cambia la ruta)."""
    global _thumbnails_base_path
    _thumbnails_base_path = path.strip()


def ensure_directories_exist(base_path=None):
    """
    Crea la estructura de subdirectorios de thumbnails.
    Si no se pasa base_path, usa la ruta cacheada.
    """
    if base_path is None:
        base_path = _thumbnails_base_path

    os.makedirs(base_path, exist_ok=True)
    for subdir in THUMBNAIL_SUBDIRS:
        os.makedirs(os.path.join(base_path, subdir), exist_ok=True)
