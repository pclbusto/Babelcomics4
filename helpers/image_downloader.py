# helpers/image_downloader.py
import requests
import os
from PIL import Image # <--- 1. Importamos la librería de imágenes

def download_image(image_url, destination_folder, filename=None, resize_height=None): # <--- 2. Añadimos el nuevo parámetro
    """
    Descarga una imagen y opcionalmente la redimensiona a una altura específica.

    :param resize_height: Si se proporciona un valor (ej: 254), la imagen se redimensiona a esa altura.
    """
    if not image_url:
        return None

    os.makedirs(destination_folder, exist_ok=True)

    if filename is None:
        filename = image_url.split('/')[-1]

    file_path = os.path.join(destination_folder, filename)

    # Descargamos la imagen como antes
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()

        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    except requests.exceptions.RequestException as e:
        print(f"Error al descargar la imagen de {image_url}: {e}")
        return None
    except IOError as e:
        print(f"Error al guardar la imagen en {file_path}: {e}")
        return None

    # --- 3. LÓGICA DE REDIMENSIONAMIENTO ---
    # Si se especificó una altura y el archivo se descargó correctamente...
    if resize_height and os.path.exists(file_path):
        try:
            with Image.open(file_path) as img:
                # Solo redimensionamos si la imagen es más alta que el límite
                if img.height > resize_height:
                    # Calculamos el nuevo ancho para mantener la proporción
                    aspect_ratio = img.width / img.height
                    new_width = int(resize_height * aspect_ratio)

                    # Redimensionamos con un filtro de alta calidad (LANCZOS)
                    resized_img = img.resize((new_width, resize_height), Image.Resampling.LANCZOS)

                    # Convertimos a RGB para evitar problemas con formatos como GIF o PNG con paletas
                    if resized_img.mode in ('RGBA', 'P'):
                        resized_img = resized_img.convert('RGB')
                    
                    # Guardamos la imagen redimensionada, sobreescribiendo la original
                    resized_img.save(file_path, 'JPEG', quality=90)
                    print(f"DEBUG: Imagen redimensionada a {new_width}x{resize_height} y guardada en {file_path}")

        except Exception as e:
            print(f"ERROR: No se pudo redimensionar la imagen {file_path}: {e}")
            # Si falla el redimensionamiento, no hacemos nada y dejamos el archivo original
    
    return file_path