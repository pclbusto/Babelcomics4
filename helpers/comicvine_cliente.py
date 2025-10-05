# helpers/comicvine_cliente.py

import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed # ¡Nuevas importaciones!

class ComicVineClient:
    """
    Cliente para interactuar con la API de Comic Vine.
    Encapsula la lógica para realizar solicitudes y parsear respuestas.
    """
    
    BASE_URL = 'https://comicvine.gamespot.com/api/'
    API_RESULTS_LIMIT = 100 # Límite máximo de resultados por solicitud de la API
    MAX_WORKERS = 5 # Número máximo de solicitudes concurrentes (ajustar según necesidad y límites de la API)
    
    RESOURCE_PREFIXES = {
        "volume": "4050-",
        "publisher": "4040-", 
        "character": "4005-",
        "issue": "4000-" 
    }
    
    def __init__(self, api_key, user_agent="ComicVineClient/1.0 (Python)"):
        if not api_key or api_key == 'TU_API_KEY':
            raise ValueError("La API Key no puede estar vacía o ser la predeterminada. "
                             "Por favor, reemplaza 'TU_API_KEY' con tu clave real.")
        self.api_key = api_key
        self.headers = {'User-Agent': user_agent}
        self.last_request_time = 0 
        self.request_interval = 0.5 

    def _wait_for_rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_interval:
            time.sleep(self.request_interval - elapsed)
        self.last_request_time = time.time()

    def _make_api_request(self, endpoint, params=None):
        self._wait_for_rate_limit() 

        if params is None:
            params = {}
        
        params['api_key'] = self.api_key
        params['format'] = 'json'

        full_url = f"{self.BASE_URL}{endpoint}"
        
        try:
            print(f"DEBUG: Solicitando URL: {full_url} con params: {params}") 
            response = requests.get(full_url, params=params, headers=self.headers)
            response.raise_for_status() 
            
            data = response.json()
            if data['status_code'] == 1:
                return data
            else:
                print(f"Error de la API en el endpoint '{endpoint}': {data['error']} (Código: {data['status_code']})")
                return None
        except requests.exceptions.HTTPError as http_err:
            print(f"Error HTTP al realizar la solicitud a {full_url}: {http_err}")
            print(f"Respuesta del servidor: {response.text}")
            return None
        except requests.exceptions.ConnectionError as conn_err:
            print(f"Error de conexión al realizar la solicitud a {full_url}: {conn_err}")
            return None
        except requests.exceptions.Timeout as timeout_err:
            print(f"Tiempo de espera agotado al realizar la solicitud a {full_url}: {timeout_err}")
            return None
        except requests.exceptions.RequestException as req_err:
            print(f"Error desconocido al realizar la solicitud a {full_url}: {req_err}")
            return None
        except json.JSONDecodeError as json_err:
            print(f"Error al decodificar la respuesta JSON de {full_url}: {json_err}")
            print(f"Contenido de la respuesta: {response.text}")
            return None

    def _format_resource_id_for_detail_url(self, resource_id, resource_type):
        """
        Asegura que el ID tenga el prefijo de Comic Vine si es necesario, para URLs de detalle.
        """
        resource_id = str(resource_id) 
        prefix = self.RESOURCE_PREFIXES.get(resource_type)
        
        if prefix and not resource_id.startswith(prefix):
            return f"{prefix}{resource_id}"
        return resource_id

    def get_publishers(self, limit=10, offset=0, name_filter=None):
        params = {'limit': limit, 'offset': offset}
        if name_filter:
            params['filter'] = f'name:{name_filter}'
        data = self._make_api_request('publishers/', params)
        if data and 'results' in data:
            return data['results']
        return []

    def get_publisher_details(self, publisher_id):
        data = self._make_api_request(f'publisher/{publisher_id}/') 
        if data and 'results' in data:
            return data['results']
        return None

    def get_volumes(self, query=None, publisher_id=None):
        """
        Obtiene una lista completa de volúmenes, manejando la paginación y concurrencia.
        
        :param query: Texto para buscar volúmenes por nombre.
        :param publisher_id: Filtra volúmenes por ID de editorial.
        :return: Una lista de diccionarios de volúmenes, o una lista vacía si hay un error.
        """
        all_volumes = []
        current_offset = 0
        total_results = None # Se actualizará con la primera llamada

        print("\n--- Consultando Volúmenes (paginación concurrente) ---")

        # Primera llamada para obtener el total de resultados y la primera página
        initial_params = {'limit': self.API_RESULTS_LIMIT, 'offset': current_offset}

        # Construir filtros correctamente
        filters = []
        if query:
            filters.append(f'name:{query}')
        if publisher_id:
            filters.append(f'publisher:{publisher_id}')

        if filters:
            initial_params['filter'] = ','.join(filters) 
        
        first_data = self._make_api_request('volumes/', initial_params)
        
        if first_data and 'results' in first_data:
            all_volumes.extend(first_data['results'])
            total_results = first_data.get('number_of_total_results', len(first_data['results']))
            
            print(f"DEBUG: Primera página de volúmenes obtenida. Total aprox: {total_results}")

            if total_results > len(all_volumes): # Si hay más resultados para paginar
                num_pages = (total_results + self.API_RESULTS_LIMIT - 1) // self.API_RESULTS_LIMIT
                
                print(f"DEBUG: Se necesitan {num_pages} páginas en total.")
                
                # Prepara las tareas para las páginas restantes
                pages_to_fetch = []
                for page_num in range(1, num_pages): # Empezamos desde la segunda página (índice 1)
                    offset = page_num * self.API_RESULTS_LIMIT
                    if offset < total_results: # Asegurarse de no ir más allá del total
                        page_params = {'limit': self.API_RESULTS_LIMIT, 'offset': offset}

                        # Construir filtros correctamente para cada página
                        page_filters = []
                        if query:
                            page_filters.append(f'name:{query}')
                        if publisher_id:
                            page_filters.append(f'publisher:{publisher_id}')

                        if page_filters:
                            page_params['filter'] = ','.join(page_filters)

                        pages_to_fetch.append(page_params)

                # Ejecutar las llamadas en paralelo
                with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
                    future_to_page = {}
                    for page_index, params in enumerate(pages_to_fetch):
                        future = executor.submit(self._make_api_request, 'volumes/', params)
                        future_to_page[future] = f"page_{page_index + 2}" # Etiqueta para depuración

                    for future in as_completed(future_to_page):
                        page_label = future_to_page[future]
                        try:
                            data = future.result()
                            if data and 'results' in data:
                                all_volumes.extend(data['results'])
                                print(f"DEBUG: {page_label} completada. Resultados en esta página: {len(data['results'])}")
                            else:
                                print(f"DEBUG: {page_label} completada sin resultados o con error.")
                        except Exception as exc:
                            print(f"DEBUG: {page_label} generó una excepción: {exc}")
        elif not first_data:
            print("Error al obtener la primera página de volúmenes.")
            return []

        print(f"--- Consulta de volúmenes completada. Se obtuvieron {len(all_volumes)} volúmenes. ---")
        return all_volumes

    def get_volume_details(self, volume_id):
        formatted_volume_id = self._format_resource_id_for_detail_url(volume_id, "volume")
        data = self._make_api_request(f'volume/{formatted_volume_id}/')
        if data and 'results' in data:
            return data['results']
        return None

    def get_issues(self, limit=10, offset=0, query=None, volume_id=None, publisher_id=None):
        print(f"\n--- Consultando Issues (limit={limit}, offset={offset}) ---")
        params = {'limit': limit, 'offset': offset}
        
        filters = []
        if query:
            filters.append(f'name:{query}') 
        if volume_id:
            filters.append(f'volume:{volume_id}')
        if publisher_id:
            filters.append(f'publisher:{publisher_id}') 

        if filters:
            params['filter'] = ','.join(filters)
        
        data = self._make_api_request('issues/', params)
        
        if data and 'results' in data:
            print(f"Total de issues encontrados (aprox.): {data.get('number_of_total_results', 'N/A')}")
            return data['results']
        return []

    def get_issue_details(self, issue_id):
        print(f"\n--- Obteniendo detalles del Issue ID: {issue_id} ---")
        formatted_issue_id = self._format_resource_id_for_detail_url(issue_id, "issue")
        
        data = self._make_api_request(f'issue/{formatted_issue_id}/')
        
        if data and 'results' in data:
            issue = data['results']
            print(f"Título: {issue.get('name', issue.get('title', 'N/A'))}")
            print(f"Volumen: {issue['volume']['name'] if issue.get('volume') else 'N/A'}")
            print(f"Número del Issue: {issue.get('issue_number', 'N/A')}")
            print(f"Fecha de publicación: {issue.get('cover_date', 'N/A')}")
            return issue
        return None

    def get_issues_by_ids(self, ids_list):
        """
        Obtiene una lista de números (issues) de cómics a partir de una lista de IDs.
        Maneja automáticamente el particionado en grupos de 100 IDs y realiza solicitudes en paralelo.
        
        :param ids_list: Una lista de IDs numéricos (sin prefijo) de los issues a buscar.
        :return: Una lista de diccionarios de issues que coinciden con los IDs, o una lista vacía.
        """
        if not ids_list:
            print("La lista de IDs está vacía. No se realizará ninguna consulta.")
            return []

        all_found_issues = []
        total_ids_to_fetch = len(ids_list)
        
        print(f"\n--- Consultando {total_ids_to_fetch} Issues por IDs específicos (paralelo, en grupos de {self.API_RESULTS_LIMIT})... ---")

        # Usar ThreadPoolExecutor para ejecutar las solicitudes en paralelo
        with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
            future_to_chunk = {}
            for i in range(0, total_ids_to_fetch, self.API_RESULTS_LIMIT):
                chunk_ids = ids_list[i : i + self.API_RESULTS_LIMIT]
                
                # Convertir los IDs a strings (sin prefijo) para el filtro 'id:'
                id_strings = [str(issue_id) for issue_id in chunk_ids]
                id_filter_string = '|'.join(id_strings)
                
                params = {
                    'limit': self.API_RESULTS_LIMIT, 
                    'offset': 0, # El offset aquí es 0 porque ya estamos particionando la lista
                    'filter': f'id:{id_filter_string}'
                }
                
                # Enviar la tarea al pool de hilos
                # Usamos lambda para capturar los valores de params para cada llamada
                future = executor.submit(self._make_api_request, 'issues/', params)
                future_to_chunk[future] = f"chunk_{i//self.API_RESULTS_LIMIT + 1}"

            # Recolectar los resultados a medida que se completan
            for future in as_completed(future_to_chunk):
                chunk_label = future_to_chunk[future]
                try:
                    data = future.result() # Obtener el resultado del hilo
                    if data and 'results' in data:
                        all_found_issues.extend(data['results'])
                        print(f"DEBUG: {chunk_label} completado. Resultados: {len(data['results'])}")
                    else:
                        print(f"DEBUG: {chunk_label} completado sin resultados o con error.")
                except Exception as exc:
                    print(f"DEBUG: {chunk_label} generó una excepción: {exc}")
                
        print(f"--- Completada la consulta. Se encontraron {len(all_found_issues)} issues únicos. ---")
        return all_found_issues

    def get_volume_issues(self, volume_id):
        """
        Obtener todos los issues de un volumen específico
        """
        print(f"\n--- Obteniendo issues del volumen {volume_id} ---")
        all_issues = []
        current_offset = 0

        while True:
            params = {
                'limit': self.API_RESULTS_LIMIT,
                'offset': current_offset,
                'filter': f'volume:{volume_id}'
            }

            data = self._make_api_request('issues/', params)

            if not data or 'results' not in data:
                break

            issues_batch = data['results']
            if not issues_batch:
                break

            all_issues.extend(issues_batch)

            # Verificar si hay más páginas
            total_results = data.get('number_of_total_results', 0)
            if len(all_issues) >= total_results:
                break

            current_offset += self.API_RESULTS_LIMIT

        print(f"--- Issues obtenidos: {len(all_issues)} ---")
        return all_issues

    def search(self, query, resource_type=None, limit=10, offset=0):
        params = {
            'query': query,
            'limit': limit,
            'offset': offset
        }
        if resource_type:
            params['resources'] = resource_type

        data = self._make_api_request('search/', params)

        if data and 'results' in data:
            return data['results']
        return []
    

# --- EJEMPLO DE USO DE LA CLASE ---
if __name__ == "__main__":
    # --- CONFIGURACIÓN (REEMPLAZA ESTO) ---
    # ¡IMPORTANTE! Reemplaza 'TU_API_KEY' con tu clave API real de Comic Vine
    # Puedes obtener una clave API registrándote en Comic Vine (o GameSpot).
    MY_API_KEY = '7e4368b71c5a66d710a62e996a660024f6a868d4'

    if MY_API_KEY == 'TU_API_KEY':
        print("¡ADVERTENCIA! Por favor, reemplaza 'TU_API_KEY' en el script con tu clave API real de Comic Vine.")
        print("Este script no funcionará correctamente sin ella.")
        exit()

    try:
        # Instanciar el cliente
        comic_client = ComicVineClient(MY_API_KEY)

        print("\n--- EJEMPLOS DE USO ---")

        # Ejemplo 1: Obtener las volumenes de batman de DC Comics
        print("\nObteniendo lista de volumenes Batman de DC Comics...")
        batman_volumes = comic_client.get_volumes(query="Superman", publisher_id="4040-10")
        if batman_volumes:
            for vol in batman_volumes:
                publisher_name = vol['publisher']['name'] if vol.get('publisher') else 'N/A'
                print(f"- ID: {vol['id']}, Nombre: {vol['name']}, Editor: {publisher_name}")
        # # Ejemplo 2: Obtener los numerops de batman 796
        # batman_volume = comic_client.get_volume_details(volume_id=796)
        # if batman_volume:
        #     lista_issues = [issue['id'] for issue in batman_volume.get('issues', []) if 'id' in issue]
        #     lista = comic_client.get_issues_by_ids(lista_issues)
        #     if lista:
        #         print(f"\nTotal de issues encontrados para el volumen Batman 796: {len(lista)}")
        #         for issue in lista:
        #             print(f"- ID: {issue['id']}, Título: {issue.get('name', issue.get('title', 'N/A'))}, "
        #                   f"Número: {issue.get('issue_number', 'N/A')}, Fecha: {issue.get('cover_date', 'N/A')}")
            

        #     # Obtener detalles del primer volumen de Batman encontrado
        #     print(f"\nObteniendo detalles del primer volumen de Batman (ID: {batman_volumes[0]['id']})...")
        #     first_batman_volume_details = comic_client.get_volume_details(batman_volumes[0]['id'])
        #     if first_batman_volume_details:
        #         print(f"Nombre: {first_batman_volume_details.get('name')}, Issues: {first_batman_volume_details.get('issues', 'N/A')}")
        # else:
        #     print("No se encontraron volúmenes de 'Batman'.")

        # # Ejemplo 4: Usar la función de búsqueda general para buscar personajes de "Superman"
        # print("\nBuscando personajes relacionados con 'Superman'...")
        # superman_characters = comic_client.search(query="Superman", resource_type="character", limit=3)
        # if superman_characters:
        #     for char in superman_characters:
        #         print(f"- Tipo: {char.get('resource_type')}, Nombre: {char.get('name')}, ID: {char.get('id')}")
        # else:
        #     print("No se encontraron personajes de 'Superman'.")

    except ValueError as ve:
        print(f"Error de configuración: {ve}")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")

    print("\n--- EJEMPLOS DE USO FINALIZADOS ---")