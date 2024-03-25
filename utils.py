import os
import shutil
import random

import requests
from dotenv import load_dotenv

load_dotenv()
headers = {'X-API-Key': os.getenv("POKEMON_TCG_API_KEY")}


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
        # download_set_cards_images(set_id)
        train_model(set_id)


'''
    API Requests, data fetch and download
'''
def download_set_cards_images(set_id):
    response = requests.get("https://api.pokemontcg.io/v2/cards?q=set.id:sv4pt5", headers=headers)
    if response.status_code == 200:
        if not os.path.exists(os.path.join("card_sets", set_id)):
            os.makedirs(os.path.join("card_sets", set_id))
        data = response.json().get('data', [])
        for i, card in enumerate(data):
            download_file(set_id, card.get('images').get('large'), i)

    else:
        print("Failed to retrieve data. Status code:", response.status_code)


def download_file(set, url, i):
    response = requests.get(url, stream=True)
    with open(os.path.join("card_sets", set, str(i) + ".png"), 'wb') as out_file:
        shutil.copyfileobj(response.raw, out_file)


'''
    AI Training functions
'''
def train_model(set_id):
    split_data(set_id)


def split_data(set_id):
    card_images = os.listdir(os.path.join("card_sets", set_id))
    card_ids = list(range(len(card_images)))
    random.shuffle(card_ids)

    # Determine the sizes of each set
    num_images = len(card_images)
    num_train = int(0.7 * num_images)
    num_val = int(0.15 * num_images)
    num_test = num_images - num_train - num_val

    os.makedirs(os.path.join("card_sets", set_id, "train"), exist_ok=True)
    os.makedirs(os.path.join("card_sets", set_id, "valid"), exist_ok=True)
    os.makedirs(os.path.join("card_sets", set_id, "test"), exist_ok=True)

    for i in range(0, num_train):
        image_name = card_images[card_ids[i]]
        shutil.move(os.path.join("card_sets", set_id, image_name),
                    os.path.join("card_sets", set_id, "train", image_name))

    for i in range(num_train, num_train+num_val):
        image_name = card_images[card_ids[i]]
        shutil.move(os.path.join("card_sets", set_id, image_name),
                    os.path.join("card_sets", set_id, "valid", image_name))

    for i in range(num_train + num_val, num_train+num_val+num_test):
        image_name = card_images[card_ids[i]]
        shutil.move(os.path.join("card_sets", set_id, image_name),
                    os.path.join("card_sets", set_id, "test", image_name))
