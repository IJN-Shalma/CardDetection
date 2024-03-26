import os
import shutil
import random
from tqdm import tqdm
from ultralytics import YOLO

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
    if set_id == "sv4pt5":  # Testing
        labels = download_set_cards_images(set_id)
        split_data(set_id, labels)
        yolo_train(set_id)


'''
    API Requests, data fetch and download
'''


def download_set_cards_images(set_id):
    response = requests.get("https://api.pokemontcg.io/v2/cards?q=set.id:" + set_id, headers=headers)
    if response.status_code == 200:
        if not os.path.exists(os.path.join("card_sets", set_id)):
            os.makedirs(os.path.join("card_sets", set_id))
        data = response.json().get('data', [])
        labels = []
        for i, card in enumerate(tqdm(data)):
            download_file(set_id, card.get('images').get('large'), card.get('id'))
            labels.append(card.get('id'))
            create_image_label_file(set_id, card.get('id'), i)
        generate_data_yaml(set_id, labels)
        return labels

    else:
        print("Failed to retrieve data. Status code:", response.status_code)


def download_file(set, url, card_id):
    response = requests.get(url, stream=True)
    with open(os.path.join("card_sets", set, card_id + ".png"), 'wb') as out_file:
        shutil.copyfileobj(response.raw, out_file)


'''
    AI Training functions
'''


def yolo_train(set_id):
    model = YOLO('yolo/models/yolov8l.pt')

    results = model.train(
        data=os.path.join("card_sets", set_id, "data.yaml"),
        imgsz=[733, 1024],
        epochs=10,
        batch=8,
        name=set_id,
        rect=True)


def split_data(set_id, labels):
    random.shuffle(labels)

    num_images = len(labels)
    num_train = int(0.7 * num_images)
    num_val = int(0.15 * num_images)
    num_test = num_images - num_train - num_val

    create_training_dirs(set_id)

    for i in range(0, num_train):
        card_id = labels[i]
        shutil.move(os.path.join("card_sets", set_id, card_id + ".png"),
                    os.path.join("card_sets", set_id, "train", "images", card_id + ".png"))

        shutil.move(os.path.join("card_sets", set_id, card_id + ".txt"),
                    os.path.join("card_sets", set_id, "train", "labels", card_id + ".txt"))

    for i in range(num_train, num_train + num_val):
        card_id = labels[i]
        shutil.move(os.path.join("card_sets", set_id, card_id + ".png"),
                    os.path.join("card_sets", set_id, "valid", "images", card_id + ".png"))

        shutil.move(os.path.join("card_sets", set_id, card_id + ".txt"),
                    os.path.join("card_sets", set_id, "valid", "labels", card_id + ".txt"))

    for i in range(num_train + num_val, num_train + num_val + num_test):
        card_id = labels[i]
        shutil.move(os.path.join("card_sets", set_id, card_id + ".png"),
                    os.path.join("card_sets", set_id, "test", "images", card_id + ".png"))

        shutil.move(os.path.join("card_sets", set_id, card_id + ".txt"),
                    os.path.join("card_sets", set_id, "test", "labels", card_id + ".txt"))


def create_image_label_file(set_id, file_name, label):
    with open(os.path.join("card_sets", set_id, file_name + ".txt"), 'w') as f:
        f.write(str(label) + " 0.000000 0.000000 1.000000 1.000000")
        f.close()


def generate_data_yaml(set_id, labels):
    with open(os.path.join("card_sets", set_id, "data.yaml"), 'w') as f:
        f.write("path: " + set_id + "/\n")  # Fix output path with current CWD
        f.write("train: train/images\n")
        f.write("val: valid/images\n")
        f.write("test: test/images\n")
        f.write("\n")
        f.write("nc: " + str(len(labels)) + "\n")
        f.write("names: " + str(labels))


def create_training_dirs(set_id):
    os.makedirs(os.path.join("card_sets", set_id, "train"), exist_ok=True)
    os.makedirs(os.path.join("card_sets", set_id, "train", "labels"), exist_ok=True)
    os.makedirs(os.path.join("card_sets", set_id, "train", "images"), exist_ok=True)
    os.makedirs(os.path.join("card_sets", set_id, "valid"), exist_ok=True)
    os.makedirs(os.path.join("card_sets", set_id, "valid", "labels"), exist_ok=True)
    os.makedirs(os.path.join("card_sets", set_id, "valid", "images"), exist_ok=True)
    os.makedirs(os.path.join("card_sets", set_id, "test"), exist_ok=True)
    os.makedirs(os.path.join("card_sets", set_id, "test", "labels"), exist_ok=True)
    os.makedirs(os.path.join("card_sets", set_id, "test", "images"), exist_ok=True)
