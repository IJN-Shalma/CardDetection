import math
import os

from PIL import Image
from tqdm import tqdm
from dotenv import load_dotenv
import numpy as np
import cv2
import shutil
import requests
import imagehash
import json

load_dotenv()
headers = {'X-API-Key': os.getenv("POKEMON_TCG_API_KEY")}


def build_sets_hashes():
    """
    Service setup function.
    For each legal set in the current Pokémon TCG Format, calls the build_set_data function

    TODO: Approach will probably be changed using a Database instead of local JSON files.
    """
    response = requests.get("https://api.pokemontcg.io/v2/sets?q=legalities.standard:legal", headers=headers)
    if response.status_code == 200:
        data = response.json().get('data', [])
        for card_set in data:
            if card_set.get('id') == "sv4pt5":  # Testing, build only Paldean Fates set
                build_set_data(card_set.get('id'), card_set.get('name'))
    else:
        print("Failed to retrieve data. Status code:", response.status_code)


def build_set_data(set_id, set_name):
    """
    Wrapper function, calls download_card_set_images and compile_card_set_hashes downloading and building all
    necessary data for a specified set

    Args:
        set_id (str): Card set id (from API)
        set_name (str): Official card set name (from API)
    """
    download_card_set_images(set_id, set_name)
    compile_card_set_hashes(set_id)


def compile_card_set_hashes(set_id):
    """
    Generates a JSON file with a hash for each card image in the set.
    download_card_set_images function must be called before (card images must be present in set folder)

    Args: set_id (str): Card set id (from API), used to read the card images in the right folder and save the JSON
    file in that same folder
    """
    images_data = []
    for card_image in os.listdir(os.path.join("card_sets", set_id)):
        image = Image.open(os.path.join("card_sets", set_id, card_image))
        image_hash = imagehash.phash(image)
        images_data.append({
            'card_id': card_image.rsplit('.', 1)[0],
            'hash': str(image_hash)
        })
    with open(os.path.join("card_sets", set_id, set_id + ".json"), 'w') as json_file:
        json.dump(images_data, json_file, indent=4)


def download_card_set_images(set_id, set_name):
    """
    Requests from the API all cards in the specified set (with set_id) and downloads all the high resolution png files.

    Args:
        set_id (str): Card set id (from API), used to request cards in a set from API.
        set_name (str): Official card set name (from API), used as tqdm description
    """
    response = requests.get("https://api.pokemontcg.io/v2/cards?q=set.id:" + set_id, headers=headers)
    if response.status_code == 200:
        if not os.path.exists(os.path.join("card_sets", set_id)):
            os.makedirs(os.path.join("card_sets", set_id))
        data = response.json().get('data', [])
        for i, card in enumerate(tqdm(data, desc=set_name)):
            download_card_image(set_id, card.get('images').get('large'), card.get('id'))

    else:
        print("Failed to retrieve data. Status code:", response.status_code)


def download_card_image(set_id, url, card_id):
    """
    Helper function, downloads the specified and saves the specified card.

    Args:
        set_id (str): Card set id (from API), used to determine download folder
        url (str): Image URL (from API)
        card_id (str): Card ID (from API), used as file name.
    """
    response = requests.get(url, stream=True)
    with open(os.path.join("card_sets", set_id, card_id + ".png"), 'wb') as out_file:
        shutil.copyfileobj(response.raw, out_file)


def find_cards_in_image(image):
    """
    Main operating function.
    From a camera image, returns all the cards identified in the image

    Args:
        image: Camera image
    """
    image = cv2.resize(image, (1270, 720), interpolation=cv2.INTER_AREA)
    contours = find_contours(image)
    images = extract_card_images_from_image(contours, image)
    for image in images:
        cv2.imshow("Image", image)
        identify_card(image)
        cv2.waitKey(0)


def identify_card(image):
    """
    Hash the identified card from the camera and compare it with the hashes previously generated

    TODO: Completely update logic, process more images at once, use database
    """
    pil_image = Image.fromarray(image)
    pil_image_hash = imagehash.phash(pil_image)
    min_dist = -1
    matched_card = ''
    with open('card_sets/sv4pt5/sv4pt5.json') as f:
        card_data = json.load(f)

    for card in card_data:
        card_hash = imagehash.hex_to_hash(card['hash'])  # Convert the hash string back to ImageHash
        dist = pil_image_hash - card_hash  # Calculate Hamming distance
        if min_dist == -1 or dist < min_dist:
            min_dist = dist
            matched_card = card['card_id']

    print(min_dist, matched_card)
    response = requests.get("https://api.pokemontcg.io/v2/cards/" + matched_card, headers=headers)
    print(response.json())


# https://docs.opencv.org/4.9.0/d4/d73/tutorial_py_contours_begin.html
def find_contours(image):
    """
    Using CV2 package, finds the contours in the image and returns the card contours calling the
    get_rectangular_contours function

    Args:
        image: Camera image

    Returns:
        contours: Array of contours containing the card images
    """
    image_grayscale = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    ret, thresh = cv2.threshold(image_grayscale, 127, 255, 0)
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    image_copy = image.copy()
    cv2.drawContours(image_copy, contours, -1, (0, 255, 0), 3)
    cv2.imshow("Image", image_copy)
    cv2.waitKey(0)

    contours = get_rectangular_contours(contours
                                        )
    image_copy = image.copy()
    cv2.drawContours(image_copy, contours, -1, (0, 255, 0), 3)
    cv2.imshow("Image", image_copy)
    cv2.waitKey(0)
    return contours


# https://stackoverflow.com/questions/62274412/cv2-approxpolydp-cv2-arclength-how-these-works
def get_rectangular_contours(contours):
    """
    Tries to find all rectangular contours, supposedly containing Pokémon Cards.

    Args:
        contours: Contours from cv2.findContours function

    Returns:
        rectangular_contours: Array of contours containing the card images
    """
    rectangular_contours = []
    for i in contours:
        area = cv2.contourArea(i)
        if area > 4000:  # Test  value for minimum threshold
            peri = cv2.arcLength(i, True)  # Get perimeter of contour
            approx = cv2.approxPolyDP(i, 0.05 * peri, True)  # Gets number of sides of contour
            if len(approx) == 4:
                rectangular_contours.append(approx)
    return rectangular_contours


def extract_card_images_from_image(contours, image):
    """
    Args:
        contours: Rectangular contours containing playing cards from get_rectangular_contours function
        image: Original image

    Returns:
        images: Array of card images
    """
    images = []
    for contour in contours:
        extracted_image = perspective_transform_card(contour, image)
        images.append(extracted_image)
    return images


# https://docs.opencv.org/3.4/da/d6e/tutorial_py_geometric_transformations.html
# https://stackoverflow.com/questions/7263621/how-to-find-corners-on-a-image-using-opencv
# https://docs.opencv.org/3.1.0/dd/d49/tutorial_py_contour_features.html !
def perspective_transform_card(contour, image):
    """
    Transforms the perspective of the rectangular contour containing a playing card returning a "full screen" scan of
    the card

    Args:
        contour: Rectangular contours containing a playing card
        image: Original image

    Returns:
        res: Perspective transformed image
    """
    card_width = 733
    card_height = 1024
    contour = fix_contour(contour)
    pts1 = np.float32([contour[0], contour[1], contour[3], contour[2]])
    pts2 = np.float32([[0, 0], [card_width, 0], [0, card_height], [card_width, card_height]])
    m = cv2.getPerspectiveTransform(pts1, pts2)
    res = cv2.warpPerspective(image, m, (733, 1024))

    return res


def fix_contour(contour):
    """
    Rotates the contour array putting in position 0 the top left corner of the card

    Args:
        contour: Rectangular contours containing a playing card

    Returns:
        contour: Contour array with fixed corner order
    """
    dist1 = np.linalg.norm(contour[0] - contour[1])
    dist2 = np.linalg.norm(contour[1] - contour[2])

    if dist1 < dist2:  # Card is tilted to the right, position 0 is top-left:
        pass
    else:  # Card is tilted to the left, position 0 is top-right, needs to be rotated
        contour = np.roll(contour, 2)
    return contour
