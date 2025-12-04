#!/usr/bin/env python3
"""
Script para probar diferentes configuraciones de headers
"""
import requests
import time

# URL que sabemos que falla
failing_url = "https://comicvine.gamespot.com/a/uploads/scale_medium/11/110017/2232096-www.jpg"
# URL que sabemos que funciona
working_url = "https://comicvine.gamespot.com/a/uploads/scale_medium/6/67663/2867418-12.jpg"

def test_headers_config(name, headers):
    """Probar una configuración de headers"""
    print(f"\n{'='*80}")
    print(f"Probando: {name}")
    print(f"{'='*80}")

    for test_name, url in [("URL que falla", failing_url), ("URL que funciona", working_url)]:
        print(f"\n{test_name}: {url}")
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            print(f"✅ ÉXITO: Status {response.status_code}, Size: {len(response.content)} bytes")
        except requests.exceptions.RequestException as e:
            print(f"❌ ERROR: {e}")
        time.sleep(0.5)

# Configuración 1: Headers actuales
headers_v1 = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://comicvine.gamespot.com/'
}

# Configuración 2: Headers más completos (como navegador Chrome real)
headers_v2 = {
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

# Configuración 3: Headers como si viniéramos de la página del volumen
headers_v3 = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,es;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://comicvine.gamespot.com/the-amazing-spider-man/4050-18/issues/',
    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'image',
    'sec-fetch-mode': 'no-cors',
    'sec-fetch-site': 'same-origin',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
}

# Configuración 4: Firefox
headers_v4 = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Accept': 'image/avif,image/webp,*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://comicvine.gamespot.com/',
    'DNT': '1',
    'Connection': 'keep-alive',
}

def main():
    print("PROBANDO DIFERENTES CONFIGURACIONES DE HEADERS")

    test_headers_config("Config 1: Headers actuales", headers_v1)
    test_headers_config("Config 2: Chrome completo", headers_v2)
    test_headers_config("Config 3: Chrome con Referer específico", headers_v3)
    test_headers_config("Config 4: Firefox", headers_v4)

    print(f"\n{'='*80}")
    print("FIN DE PRUEBAS")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
