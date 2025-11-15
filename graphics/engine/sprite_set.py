import cv2
import pygame as pg

from Image_Processing.ImageEditor import ImageEditor

clear = pg.SRCALPHA


class SpriteSet:
    def __init__(self, path, number, size, space):
        self.spriteSheet = pg.image.load(path)
        self.sprites = []

        for num in range(number):
            image = pg.Surface(size, clear)
            rect = pg.Rect(pg.Vector2((size.x + space.x) * num, 0), size)
            image.blit(self.spriteSheet, (0, 0), rect)

            self.sprites.append(image)

    def scaleSprites(self, tileSize, mapsScale, newSize=None):
        for (idx, surf) in enumerate(self.sprites):
            ratio = surf.get_size()[1] / surf.get_size()[0]
            if not newSize:
                newSize = pg.Vector2(tileSize, tileSize * ratio) * mapsScale

            scaledImage = pg.transform.scale(surf, newSize)
            self.sprites[idx] = scaledImage


class SpriteSet2:
    def __init__(self, path, number, size, space):
        self.spriteSheet = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        self.sprites = []

        for num in range(number):
            rect = pg.Rect(pg.Vector2((size.x + space.x) * num, 0), size)
            imageData = self.spriteSheet[rect.top:rect.bottom, rect.left:rect.right, :]
            editor = ImageEditor(pixelData=imageData)
            cropped = editor.crop_transparent_borders()
            formattedImage = cv2.cvtColor(cropped, cv2.COLOR_BGRA2RGBA)
            surf = pg.Surface((formattedImage.shape[1], formattedImage.shape[0]), pg.SRCALPHA)
            pixArray = pg.PixelArray(surf)
            for row in range(formattedImage.shape[0]):
                for col in range(formattedImage.shape[1]):
                    colour = pg.Color(int(formattedImage[row, col, 0]), int(formattedImage[row, col, 1]),
                                      int(formattedImage[row, col, 2]), int(formattedImage[row, col, 3]))
                    pixArray[col, row] = colour
            pixArray.close()

            self.sprites.append(surf)

    def __getitem__(self, idx):
        return self.sprites[idx]

    def scaleSprites(self, scale):
        for (idx, surf) in enumerate(self.sprites):
            scaledImage = pg.transform.scale(surf, pg.Vector2(surf.get_size()) * scale)
            self.sprites[idx] = scaledImage
