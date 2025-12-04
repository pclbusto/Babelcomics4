#!/usr/bin/env python3
"""
Script de prueba para descargar imágenes de ComicVine
"""
import time
import os
from helpers.image_downloader import download_image

# Lista de URLs de prueba
test_urls = [
    ("Issue #1", "https://comicvine.gamespot.com/a/uploads/scale_medium/11/110017/2232096-www.jpg"),
    ("Issue #2", "https://comicvine.gamespot.com/a/uploads/scale_medium/11/110017/2275130-www.jpg"),
    ("Issue #3", "https://comicvine.gamespot.com/a/uploads/scale_medium/11/110017/2323326-www.jpg"),
    ("Issue #4", "https://comicvine.gamespot.com/a/uploads/scale_medium/7/71975/2385970-prev_img.jpg"),
    ("Issue #5", "https://comicvine.gamespot.com/a/uploads/scale_medium/7/71975/2444894-prev_img.jpg"),
    ("Issue #6", "https://comicvine.gamespot.com/a/uploads/scale_medium/3/31666/2503063-prv13100_cov.jpg"),
    ("Issue #7", "https://comicvine.gamespot.com/a/uploads/scale_medium/7/71975/2572783-prev_img.jpg"),
    ("Issue #8", "https://comicvine.gamespot.com/a/uploads/scale_medium/6/67663/2627393-995357.jpg"),
    ("Issue #9", "https://comicvine.gamespot.com/a/uploads/scale_medium/7/71975/2690041-__kgrhqn__gsfcywgq_hzbqmhvb6c6g__60_57.jpg"),
    ("Issue #10", "https://comicvine.gamespot.com/a/uploads/scale_medium/6/67663/2747490-10.jpg"),
    ("Issue #11", "https://comicvine.gamespot.com/a/uploads/scale_medium/6/67663/2798007-11.jpg"),
    ("Issue #12", "https://comicvine.gamespot.com/a/uploads/scale_medium/6/67663/2867418-12.jpg"),
    ("Issue #13", "https://comicvine.gamespot.com/a/uploads/scale_medium/6/67663/2909094-13.jpg"),
    ("Issue #14", "https://comicvine.gamespot.com/a/uploads/scale_medium/6/67663/2959092-14a.jpg"),
]

def main():
    """Función principal"""
    destination_folder = "test_imagen_downloads"

    # Crear carpeta si no existe
    os.makedirs(destination_folder, exist_ok=True)

    print("="*80)
    print("INICIANDO PRUEBA DE DESCARGA DE IMÁGENES")
    print("="*80)
    print(f"Carpeta destino: {destination_folder}")
    print(f"Total de imágenes: {len(test_urls)}")
    print("="*80 + "\n")

    successful = 0
    failed = 0

    for idx, (issue_name, url) in enumerate(test_urls, 1):
        print(f"\n[{idx}/{len(test_urls)}] Descargando {issue_name}...")
        print(f"URL: {url}")

        try:
            result = download_image(url, destination_folder)

            if result and os.path.exists(result):
                file_size = os.path.getsize(result)
                print(f"✅ ÉXITO: Descargado {os.path.basename(result)} ({file_size} bytes)")
                successful += 1
            else:
                print(f"❌ FALLO: La descarga no retornó un archivo válido")
                failed += 1

        except Exception as e:
            print(f"❌ ERROR: {e}")
            failed += 1

        # Delay de 1 segundo entre descargas
        if idx < len(test_urls):
            print("Esperando 1 segundo...")
            time.sleep(1.0)

    # Resumen final
    print("\n" + "="*80)
    print("RESUMEN DE DESCARGAS")
    print("="*80)
    print(f"✅ Exitosas: {successful}/{len(test_urls)}")
    print(f"❌ Fallidas:  {failed}/{len(test_urls)}")
    print(f"📁 Carpeta:   {os.path.abspath(destination_folder)}")
    print("="*80)

    # Listar archivos descargados
    if successful > 0:
        print("\nArchivos descargados:")
        files = sorted(os.listdir(destination_folder))
        for f in files:
            file_path = os.path.join(destination_folder, f)
            file_size = os.path.getsize(file_path)
            print(f"  - {f} ({file_size} bytes)")

if __name__ == "__main__":
    main()
