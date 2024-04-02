import utils
import cv2

#utils.build_sets_hashes()
#utils.compile_card_set_hashes("sv4pt5")
#print(help(utils.build_sets_hashes))
image = cv2.imread("test/2.jpg")
utils.find_cards_in_image(image)
