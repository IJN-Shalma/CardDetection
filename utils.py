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
    if (set_id == "sv4pt5"):  # Testing
        download_set_cards_images(set_id)


def download_set_cards_images(set_id):
    response = requests.get("https://api.pokemontcg.io/v2/cards?q=set.id:sv4pt5", headers=headers)
    if response.status_code == 200:
        if not os.path.exists(os.path.join("card_sets", set_id)):
            os.makedirs(os.path.join("card_sets", set_id))
        data = response.json().get('data', [])
        for card in data:
            print(card.get('images').get('large'))
    else:
        print("Failed to retrieve data. Status code:", response.status_code)
