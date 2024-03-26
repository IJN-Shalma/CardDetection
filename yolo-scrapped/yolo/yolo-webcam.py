from ultralytics import YOLO
import cv2
import cvzone
import math

cap = cv2.VideoCapture(0) # Webcam ID, only one webcam connected so id = 0
cap.set(3, 1280)  # Set width
cap.set(4, 720)  # Set height

model = YOLO("../runs/detect/sv4pt53/weights/best.pt")

while True:
    success, img = cap.read()
    results = model(img, stream=True)  # replace show=True
    for r in results:  # For each bounding box
        boxes = r.boxes
        for box in boxes:  # Bounding box
            x1, y1, x2, y2 = box.xyxy[0]  # 4 coordinates format
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)  # Convert to integer to be used with cv2
            # cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0))
            w, h = x2 - x1, y2 - y1
            cvzone.cornerRect(img, (x1, y1, w, h))

            conf = math.ceil(box.conf[0] * 100) / 100  # Get and transform confidence value to two decimal places

            cls = int(box.cls[0])  # Class id number given by YOLO, needs to be converted using classNames

            cvzone.putTextRect(img, f'{cls} {conf}', (max(0, x1), max(35, y1)), scale=1.5,
                               thickness=2)  # max used to keep value inside screen

    cv2.imshow("Image", img)
    cv2.waitKey(1)
