import os

import cv2
import requests
from dotenv import load_dotenv

load_dotenv()
headers = {'X-API-Key': os.getenv("POKEMON_TCG_API_KEY")}

'''
    SETUP FUNCTIONS
'''


def build_sets_hashes():
    response = requests.get("https://api.pokemontcg.io/v2/sets?q=legalities.standard:legal", headers=headers)
    if response.status_code == 200:
        data = response.json().get('data', [])  # Extract 'data' attribute from JSON response
        for card_set in data:
            build_set_hashes(card_set.get('id'))
    else:
        print("Failed to retrieve data. Status code:", response.status_code)


def build_set_hashes(card_set):
    pass


'''
    OPERATING FUNCTIONS
'''


# https://docs.opencv.org/4.9.0/d4/d73/tutorial_py_contours_begin.html
def find_contours(image):
    image_resized = cv2.resize(image, (1280, 720), interpolation=cv2.INTER_AREA)
    image_grayscale = cv2.cvtColor(image_resized, cv2.COLOR_RGB2GRAY)

    ret, thresh = cv2.threshold(image_grayscale, 127, 255, 0)
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    contours = get_biggest_contours(contours)
    cv2.drawContours(image_resized, contours, -1, (0, 255, 0), 3)

    cv2.imshow("Image", image_resized)
    cv2.waitKey(0)


# https://stackoverflow.com/questions/62274412/cv2-approxpolydp-cv2-arclength-how-these-works
def get_biggest_contours(contours):
    biggest = []
    for i in contours:
        area = cv2.contourArea(i)
        if area > 2500:  # Test  value for minimum threshold
            peri = cv2.arcLength(i, True)  # Get perimeter of contour
            approx = cv2.approxPolyDP(i, 0.02 * peri, True)  # Gets number of sides of contour
            if len(approx) == 4:
                biggest.append(approx)
    return biggest


def find_cards_in_image(image):
    find_contours(image)
