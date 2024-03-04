import requests
from pymongo import MongoClient
from urllib.parse import urlparse
import re

# Obter dados JSON remotos
url = 'https://raw.githubusercontent.com/joshhighet/ransomwatch/main/groups.json'
data = requests.get(url).json()

# Conectar ao MongoDB
client = MongoClient("mongodb://localhost:27017/")  # Substitua pela sua URI do MongoDB
db = client.crawler
http_collection = db.http
onion_collection = db.onion

# Expressão regular para identificar URLs Onion
onion_regex = re.compile(r'\.onion(/|$)')

# Função para remover o caminho da URL
def remove_path_from_url(url):
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}"

# Processar e inserir os dados
for group in data:
    if "locations" in group:
        for location in group["locations"]:
            original_url = location["slug"]
            url = remove_path_from_url(original_url)
            if onion_regex.search(url):
                # URL do tipo Onion
                onion_collection.update_one({"url": url}, {"$setOnInsert": {"url": url}}, upsert=True)
            else:
                # URL do tipo HTTP
                http_collection.update_one({"url": url}, {"$setOnInsert": {"url": url}}, upsert=True)

# Opcional: Listar URLs existentes
print("HTTP URLs:")
for url in http_collection.find({}, {"_id": 0, "url": 1}):
    print(url['url'])

print("\nOnion URLs:")
for url in onion_collection.find({}, {"_id": 0, "url": 1}):
    print(url['url'])

print("\nDados processados com sucesso.")
