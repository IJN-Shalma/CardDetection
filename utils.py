import os
import requests
from dotenv import load_dotenv

load_dotenv()
headers = {'X-API-Key': os.getenv("POKEMON_TCG_API_KEY")}
print(headers)

def build_models():
    response = requests.get("https://api.pokemontcg.io/v2/sets?q=legalities.standard:legal", headers=headers)
    if response.status_code == 200:
        data = response.json().get('data', [])  # Extract 'data' attribute from JSON response
        for set in data:
            build_model(set.get('id'))
    else:
        print("Failed to retrieve data. Status code:", response.status_code)

def build_model(set_id):
    if(set_id == "sv4pt5"): #Testing
        print(set_id)

def download_set_cards_images(set):
    print("c")