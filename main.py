import utils
import cv2

image = cv2.imread("test/R.jpg")
utils.find_cards_in_image(image)
