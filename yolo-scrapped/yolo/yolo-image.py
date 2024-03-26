import cv2
from ultralytics import YOLO

# Testing correct Python environment setup and YOLO
model = YOLO("../runs/detect/sv4pt5/weights/best.pt")
image = cv2.imread("../../test/20240326_195843.jpg")
image = cv2.resize(image, (720, 1280), interpolation=cv2.INTER_AREA)
results = model(image, show=True)
cv2.waitKey(0)
