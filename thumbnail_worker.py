#!/usr/bin/env python3
"""
thumbnail_worker.py - Worker independiente para generación de thumbnails
Diseñado para ejecutarse en procesos separados (multiprocessing) sin dependencias de GTK/GObject.
"""

import os
import io
import traceback
import zipfile
import sys

# Dependencias opcionales
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("PIL no disponible en worker")

try:
    import rarfile
    RAR_AVAILABLE = True
except ImportError:
    RAR_AVAILABLE = False
    print("rarfile no disponible en worker")

try:
    import py7zr
    SEVEN_ZIP_AVAILABLE = True
except ImportError:
    SEVEN_ZIP_AVAILABLE = False
    print("py7zr no disponible en worker")


def generate_thumbnail_task(source_path, target_path, cover_info=None, size=(280, 400)):
    """
    Función worker para generar thumbnail.
    
    Args:
        source_path (str): Ruta al archivo fuente (comic o imagen)
        target_path (str): Ruta donde guardar el thumbnail
        cover_info (dict, optional): Info de portada inteligente {'page_name': str, 'page_order': int}
        size (tuple): Tamaño máximo (ancho, alto)
        
    Returns:
        tuple: (bool success, str path_or_error)
    """
    if not PIL_AVAILABLE:
        return False, "PIL no instalado"
        
    if not os.path.exists(source_path):
        return False, "Archivo no existe"
        
    try:
        # Asegurar directorio destino
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        # 1. Extraer imagen (binaria)
        image_data = _extract_image_data(source_path, cover_info)
        
        if not image_data:
            return False, "No se pudo extraer imagen"
            
        # 2. Procesar con PIL
        success = _process_image_data(image_data, target_path, size)
        if success:
            return True, target_path
        else:
            return False, "Error procesando imagen"
        
    except Exception as e:
        traceback.print_exc()
        return False, str(e)


def _extract_image_data(source_path, cover_info):
    """Extraer bytes de imagen del archivo fuente"""
    ext = os.path.splitext(source_path)[1].lower()
    
    # Caso 1: Imagen directa
    if ext in ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif'):
        try:
            with open(source_path, 'rb') as f:
                return f.read()
        except:
            return None
            
    # Caso 2: Archivos comprimidos
    if ext in ('.cbz', '.zip'):
        return _extract_from_zip(source_path, cover_info)
    elif ext in ('.cbr', '.rar'):
        return _extract_from_rar(source_path, cover_info)
    elif ext in ('.cb7', '.7z'):
        return _extract_from_7z(source_path, cover_info)
        
    return None


def _get_target_image_name(file_list, cover_info):
    """
    Determinar qué archivo extraer.
    file_list: lista de nombres de archivo en el archivo comprimido
    """
    # Filtrar solo imágenes
    images = [
        f for f in file_list 
        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp'))
        and not f.startswith('__MACOSX')
        and '/.' not in f  # Evitar ocultos en subcarpetas
    ]
    
    if not images:
        return None
        
    # Ordenar naturalmente
    images.sort()
    
    # Estrategia 1: Cover Info específico
    if cover_info:
        # Por nombre
        if 'page_name' in cover_info and cover_info['page_name']:
            name = cover_info['page_name']
            for img in images:
                if os.path.basename(img) == name:
                    return img
                    
        # Por orden (1-based)
        if 'page_order' in cover_info and cover_info['page_order']:
            idx = cover_info['page_order'] - 1 
            if 0 <= idx < len(images):
                return images[idx]
                
    # Estrategia 2: Primera imagen (fallback)
    return images[0]


def _extract_from_zip(path, cover_info):
    try:
        with zipfile.ZipFile(path, 'r') as zf:
            target_file = _get_target_image_name(zf.namelist(), cover_info)
            if target_file:
                return zf.read(target_file)
    except Exception as e:
        print(f"Error ZIP {path}: {e}")
    return None


def _extract_from_rar(path, cover_info):
    if not RAR_AVAILABLE:
        return None
    try:
        with rarfile.RarFile(path, 'r') as rf:
            target_file = _get_target_image_name(rf.namelist(), cover_info)
            if target_file and target_file in rf.namelist():
                return rf.read(target_file)
    except Exception as e:
        print(f"Error RAR {path}: {e}")
    return None


def _extract_from_7z(path, cover_info):
    if not SEVEN_ZIP_AVAILABLE:
        return None
    try:
        with py7zr.SevenZipFile(path, 'r') as zf:
            all_files = zf.getnames()
            target_file = _get_target_image_name(all_files, cover_info)
            
            if target_file:
                result = zf.read(targets=[target_file])
                if target_file in result:
                    return result[target_file].read()
    except Exception as e:
        print(f"Error 7z {path}: {e}")
    return None


def _process_image_data(image_data, target_path, size):
    """Redimensionar y guardar imagen usando PIL"""
    try:
        # Cargar desde bytes
        img = Image.open(io.BytesIO(image_data))
        
        # Convertir modos no compatibles con JPEG
        if img.mode in ('RGBA', 'P', 'LA'):
            img = img.convert('RGB')
            
        # Calcular thumbnail para "cover"
        # Usamos .thumbnail() que mantiene aspecto
        img.thumbnail(size, Image.Resampling.LANCZOS)
        
        # Guardar
        img.save(target_path, 'JPEG', quality=85, optimize=True)
        return True
    except Exception as e:
        print(f"Error procesando imagen PIL: {e}")
        return False
