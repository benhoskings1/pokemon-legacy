import os

import cv2
from pygame import Vector2 as vec


def createSheet(directory):
    images = []
    maxSize = vec(0, 0)
    files = os.listdir(directory)
    files.sort()
    for file in files:
        if file.endswith(".png"):
            if file != "Sprite Sheet.png":
                image = cv2.imread(os.path.join(directory, file), cv2.IMREAD_UNCHANGED)
                if image.shape[1] > maxSize.x:
                    maxSize.x = image.shape[1]
                if image.shape[0] > maxSize.y:
                    maxSize.y = image.shape[0]

                images.append(image)

    paddedImages = []

    for image in images:
        size = vec(image.shape[1], image.shape[0])
        topPad = int((maxSize.y - size.y) / 2)
        bottomPad = int((maxSize.y - size.y) / 2)
        leftPad = int((maxSize.x - size.x) / 2)
        rightPad = int((maxSize.x - size.x) / 2)
        paddedImage = cv2.copyMakeBorder(image, topPad, bottomPad, leftPad, rightPad,
                                         borderType=cv2.BORDER_CONSTANT, value=[255, 255, 255, 0])
        paddedImages.append(paddedImage)

    sheet = paddedImages[0]

    for image in paddedImages[1:]:
        sheet = cv2.hconcat([sheet, image])

    cv2.imshow("H", sheet)
    cv2.waitKey()

    cv2.imwrite("Sprite Sheet.png", sheet)


createSheet("Edited Images")
