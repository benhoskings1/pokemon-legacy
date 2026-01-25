from math import floor

import pygame as pg


class Selector:
    def __init__(self, level, value, prevValue, image, size, pos):
        self.level = level
        self.value = value
        self.prevValue = prevValue
        self.image = image
        self.size = size
        self.pos = pos


class Selector2:
    def __init__(self, image, cancelImage=None, size=None, value=0, prevValue=1, optionCount=4, positions=None,
                 sizes=None):

        self.optionImage = image

        self.cancelImage = cancelImage

        self.options = optionCount

        if size:
            self.size = size
        else:
            if image:
                self.size = pg.Vector2(self.optionImage.get_size())
            else:
                self.size = pg.Vector2(0, 0)

        if sizes:
            self.sizes = sizes
        else:
            sizes = []
            for idx in range(optionCount + 1):
                sizes.append(self.size)
            self.sizes = sizes

        if positions:
            self.positions = positions
        else:
            positions = []
            for option in range(optionCount):
                if option % 2 == 0:
                    position = pg.Vector2(0, floor(option / 2) * self.size.y)
                else:
                    position = pg.Vector2(self.size.x, floor(option / 2) * self.size.y)

                positions.append(position)

            self.positions = positions

        self.value = value
        self.prevValue = prevValue
        self.cancelValue = optionCount

    def getValues(self):
        if self.value != self.options:
            image = pg.transform.scale(self.optionImage, self.sizes[self.value])
        else:
            if self.cancelImage:
                image = pg.transform.scale(self.cancelImage, self.sizes[self.value])
            else:
                image = pg.transform.scale(self.optionImage, self.sizes[self.value])

        return [image, self.positions[self.value]]


class Selector3:
    def __init__(self, shape, blitPositions=None, sizes=None, images=None, imageType=None):
        self.shape = shape
        self.level = 0

        self.positions = []

        self.options = 0
        for vec in shape:
            self.positions.append(pg.Vector2(0, 0))
            self.options += vec.x * vec.y

        self.position = pg.Vector2(0, 0)

        self.blitPositions = blitPositions
        self.sizes = sizes
        self.images = images
        if not imageType:
            self.imageIndices = [0 for _ in range(len(blitPositions))]
        else:
            self.imageIndices = imageType

    def moveLeft(self):
        if self.positions[self.level].x > 0:
            self.positions[self.level].x -= 1
            self.position = self.positions[self.level]

    def moveRight(self):
        if self.positions[self.level].x < self.shape[self.level].x - 1:
            self.positions[self.level].x += 1
            self.position = self.positions[self.level]

    def moveUp(self):
        # check within level first
        if self.positions[self.level].y > 0:
            self.positions[self.level].y -= 1
            self.position = self.positions[self.level]

        elif self.level > 0:

            if self.shape[self.level].x == self.shape[self.level - 1].x:
                xPos = self.position.x
            else:
                xPos = None

            self.level -= 1
            self.position = self.positions[self.level]

            if xPos is not None:
                self.position.x = xPos

    def moveDown(self):
        # check within level first
        if self.positions[self.level].y < self.shape[self.level].y - 1:
            self.positions[self.level].y += 1
            self.position = self.positions[self.level]

        elif self.level < len(self.shape) - 1:

            if self.shape[self.level].x == self.shape[self.level + 1].x:
                xPos = self.position.x
            else:
                xPos = None

            self.level += 1
            self.position = self.positions[self.level]

            if xPos is not None:
                self.position.x = xPos

    def reset(self):
        for i in range(len(self.shape)):
            self.positions[i] = pg.Vector2(0, 0)

        self.position = pg.Vector2(0, 0)
        self.level = 0

    def getValues(self):
        idx = 0
        for level in range(self.level):
            idx += self.shape[level].x * self.shape[level].y

        # now get idx within the level
        for row in range(int(self.position.y)):
            idx += self.shape[self.level].x

        idx += self.position.x

        idx = int(idx)

        if self.images:
            imageIdx = self.imageIndices[idx]
            baseImage = self.images[imageIdx]
            image = pg.transform.scale(baseImage, self.sizes[idx])
            pos = self.blitPositions[idx]
        else:
            image = None
            pos = None

        return image, pos, idx
