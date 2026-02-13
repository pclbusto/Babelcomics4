import requests
import json

API_KEY = "7e4368b71c5a66d710a62e996a660024f6a868d4"
ISSUE_ID = "4000-6" # Using a low ID, hopefully it exists (Issue #6 of something)

url = f"https://comicvine.gamespot.com/api/issue/{ISSUE_ID}/?api_key={API_KEY}&format=json"
headers = {'User-Agent': "ComicVineClient/1.0 (Python)"}

print(f"Requesting {url}")
response = requests.get(url, headers=headers)
data = response.json()

if data['status_code'] == 1:
    results = data['results']
    print("Keys in results:")
    print(results.keys())
    
    if 'image' in results:
        print("\n'image' field:")
        print(json.dumps(results['image'], indent=2))
        
    if 'associated_images' in results:
        print("\n'associated_images' field:")
        print(json.dumps(results['associated_images'], indent=2))
        
    if 'images' in results:
        print("\n'images' field:")
        print(json.dumps(results['images'], indent=2))
else:
    print(f"Error: {data['error']}")
