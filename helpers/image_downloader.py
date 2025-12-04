# helpers/image_downloader.py
import os
import requests
from urllib.parse import urlparse
from PIL import Image # <--- 1. Importamos la librería de imágenes


def _build_api_image_url(image_url: str) -> str | None:
    """Convierte una URL de /a/uploads/ al endpoint /api/image/ de ComicVine."""
    try:
        parsed = urlparse(image_url)
    except ValueError:
        return None

    path_parts = [part for part in parsed.path.split('/') if part]

    # Esperamos un path del tipo a/uploads/<scale>/<folders...>/<filename>
    if len(path_parts) < 4:
        return None

    if path_parts[0] != 'a' or path_parts[1] != 'uploads':
        return None

    scale_segment = path_parts[2]  # scale_medium, scale_large, etc.
    filename = path_parts[-1]

    return f"https://comicvine.gamespot.com/api/image/{scale_segment}/{filename}"

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
    # Headers completos de Chrome para evitar bloqueos 403 Forbidden de Cloudflare
    # ComicVine/GameSpot requiere headers sec-ch-ua y sec-fetch-* para verificar navegador real
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,es;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://comicvine.gamespot.com/',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'image',
        'sec-fetch-mode': 'no-cors',
        'sec-fetch-site': 'same-origin',
        'DNT': '1',
        'Connection': 'keep-alive',
    }

    response = None
    last_error = None
    urls_to_try = [image_url]

    fallback_url = _build_api_image_url(image_url)
    if fallback_url and fallback_url not in urls_to_try:
        urls_to_try.append(fallback_url)

    for candidate_url in urls_to_try:
        try:
            response = requests.get(candidate_url, stream=True, headers=headers, timeout=30)
            response.raise_for_status()
            if candidate_url != image_url:
                print(f"INFO: Descargando {filename} a través de la API de ComicVine")
            break
        except requests.exceptions.HTTPError as http_exc:
            last_error = http_exc
            status = http_exc.response.status_code if http_exc.response else 'unknown'
            if status in (403, 404) and candidate_url == image_url and fallback_url:
                # Intentaremos con la URL de la API en el siguiente ciclo
                continue
            print(f"Error al descargar la imagen de {candidate_url}: {http_exc}")
            return None
        except requests.exceptions.RequestException as req_exc:
            last_error = req_exc
            print(f"Error al descargar la imagen de {candidate_url}: {req_exc}")
            return None

    if response is None:
        if last_error:
            print(f"Error al descargar la imagen de {image_url}: {last_error}")
        return None

    try:
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
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
