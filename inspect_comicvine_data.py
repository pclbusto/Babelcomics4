#!/usr/bin/env python3
"""
Script para inspeccionar qué datos de imágenes envía ComicVine para los issues
"""

import sys
import json
sys.path.insert(0, '.')

from helpers.comicvine_cliente import ComicVineClient

def inspect_issue_image_data():
    """Inspeccionar datos de imágenes en issues de ComicVine"""

    print("🔍 INSPECCIONANDO DATOS DE IMÁGENES DE COMICVINE")
    print("=" * 50)

    # Configurar cliente
    api_key = "7e4368b71c5a66d710a62e996a660024f6a868d4"
    client = ComicVineClient(api_key)

    print("1. Obteniendo volumen de ejemplo...")
    volumes = client.get_volumes(query="Batman", publisher_id="4040-10")
    if not volumes:
        print("❌ No se encontraron volúmenes")
        return

    volume = volumes[0]
    print(f"📚 Volumen: {volume['name']} (ID: {volume['id']})")

    print("2. Obteniendo detalles del volumen...")
    volume_details = client.get_volume_details(volume['id'])
    if not volume_details:
        print("❌ No se pudieron obtener detalles")
        return

    print("3. Obteniendo issues del volumen...")
    issues_list = volume_details.get('issues', [])[:3]  # Solo primeros 3 para inspección
    if not issues_list:
        print("❌ No hay issues")
        return

    issue_ids = [issue['id'] for issue in issues_list if 'id' in issue]
    detailed_issues = client.get_issues_by_ids(issue_ids)

    print(f"4. Analizando estructura de imágenes en {len(detailed_issues)} issues...")

    for i, issue in enumerate(detailed_issues):
        print(f"\n--- ISSUE {i+1}: #{issue.get('issue_number', 'N/A')} ---")

        # Verificar campo 'image' (principal)
        if 'image' in issue:
            print("✅ Tiene campo 'image' (principal):")
            image_data = issue['image']
            if image_data:
                print(f"   - icon_url: {image_data.get('icon_url', 'N/A')}")
                print(f"   - medium_url: {image_data.get('medium_url', 'N/A')}")
                print(f"   - screen_url: {image_data.get('screen_url', 'N/A')}")
                print(f"   - screen_large_url: {image_data.get('screen_large_url', 'N/A')}")
                print(f"   - small_url: {image_data.get('small_url', 'N/A')}")
                print(f"   - super_url: {image_data.get('super_url', 'N/A')}")
                print(f"   - thumb_url: {image_data.get('thumb_url', 'N/A')}")
                print(f"   - tiny_url: {image_data.get('tiny_url', 'N/A')}")
                print(f"   - original_url: {image_data.get('original_url', 'N/A')}")
            else:
                print("   (image es null)")
        else:
            print("❌ No tiene campo 'image'")

        # Verificar si hay otros campos de imágenes
        image_fields = [key for key in issue.keys() if 'image' in key.lower() or 'cover' in key.lower()]
        if len(image_fields) > 1:
            print(f"🔍 Otros campos de imagen encontrados: {image_fields}")
            for field in image_fields:
                if field != 'image':
                    print(f"   - {field}: {type(issue[field])}")

        # Mostrar todas las claves para detectar otros campos
        all_keys = list(issue.keys())
        print(f"📋 Todas las claves del issue: {', '.join(all_keys[:10])}{'...' if len(all_keys) > 10 else ''}")

    print(f"\n=" * 50)
    print("📋 RESUMEN:")
    print("- ComicVine provee UNA imagen principal por issue en el campo 'image'")
    print("- Esta imagen tiene múltiples tamaños (icon, medium, screen, super, etc.)")
    print("- Actualmente se descarga solo 'medium_url'")
    print("- NO parece haber múltiples covers/variantes por issue en la API")

if __name__ == "__main__":
    inspect_issue_image_data()