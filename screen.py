from enum import Enum

import pygame as pg

from font.font import Font, LevelFont
from general.utils import *


class BlitLocation(Enum):
    topLeft = 0
    midTop = 1
    topRight = 2
    bottomLeft = 3
    midBottom = 4
    bottomRight = 5
    midLeft = 6
    midRight = 7
    centre = 8


fonts = {"Main": Font(2), "level": LevelFont(2)}


class FontOption(Enum):
    main = fonts["Main"]
    level = fonts["level"]


class Screen:
    def __init__(self, size, colour=None):
        self.size = pg.Vector2(size)
        self.baseSurface = pg.Surface(size, pg.SRCALPHA)
        self.surface = pg.Surface(size, pg.SRCALPHA)
        self.font = FontOption.main.value
        self.colour = colour
        if colour:
            self.baseSurface.fill(colour)

    def addText2(self, text, pos, lines=1, location=BlitLocation.topLeft, base=False, colour=None,
                 shadowColour=None, fontOption: FontOption = FontOption.main):

        self.font = fontOption.value

        if colour:
            if shadowColour:
                textSurf = self.font.render_text(text, lineCount=lines, colour=colour, shadowColour=shadowColour)
            else:
                textSurf = self.font.render_text(text, lineCount=lines, colour=colour)
        else:
            textSurf = self.font.render_text(text, lineCount=lines)
        blitPos = pos
        size = pg.Vector2(textSurf.get_size())
        if location == BlitLocation.centre:
            blitPos -=  size / 2
        elif location == BlitLocation.topRight:
            blitPos -= pg.Vector2(size.x, 0)
        elif location == BlitLocation.midTop:
            blitPos -= pg.Vector2(size.x / 2, 0)

        if base:
            self.baseSurface.blit(textSurf, blitPos)
        else:
            self.surface.blit(textSurf, blitPos)

    def loadImage(self, path, pos=(0, 0), fill=False, base=False, size=None, scale=None, location=BlitLocation.topLeft):
        image = pg.image.load(path)

        if size:
            image = pg.transform.scale(image, size)
        elif scale:
            image = pg.transform.scale(image, (image.get_size()[0] * scale.x, image.get_size()[1] * scale.y))
        elif fill:
            image = pg.transform.scale(image, self.size)

        imageRect = pg.Rect(pos, image.get_size())

        if location == BlitLocation.centre:
            imageRect.topleft = pg.Vector2(imageRect.topleft) - pg.Vector2(imageRect.size) / 2
        elif location == BlitLocation.topRight:
            imageRect.x -= imageRect.width

        if base:
            self.baseSurface.blit(image, imageRect.topleft)
        else:
            self.surface.blit(image, imageRect.topleft)

    def addImage(self, image, pos=pg.Vector2(0, 0), fill=False, scale=None, location=BlitLocation.topLeft, base=False):

        if base:
            surf = self.baseSurface
        else:
            surf = self.surface

        if scale:
            image = pg.transform.scale(image, (image.get_size()[0] * scale.x, image.get_size()[1] * scale.y))
        elif fill:
            image = pg.transform.scale(image, self.size)

        size = pg.Vector2(image.get_size())
        if location == BlitLocation.centre:

            surf.blit(image, pos - size / 2)
        elif location == BlitLocation.midBottom:
            newPos = pg.Vector2(pos.x - (size.x / 2), pos.y - size.y)
            surf.blit(image, newPos)
        else:
            surf.blit(image, pos)

    def createLayeredShape(self, pos, shape, size, number, colours, offsets,
                           radii, offsetWidth=False, offsetHeight=False, base=False):
        # create surfaces
        surf = pg.Surface(size, pg.SRCALPHA)
        center = size / 2

        for layer in range(number):
            currentOffset = (0, 0)
            if type(offsets[0]) == pg.Vector2:
                currentOffset = pg.Vector2(0, 0)
            elif type(offsets[0]) == pg.Rect:
                currentOffset = pg.Rect(0, 0, 0, 0)

            for offset in offsets[0:layer + 1]:
                if type(offset) == pg.Vector2:
                    currentOffset += offset
                elif type(offset) == pg.Rect:
                    currentOffset = pg.Rect(pg.Vector2(currentOffset.topleft) + pg.Vector2(offset.topleft),
                                            pg.Vector2(currentOffset.size) + pg.Vector2(offset.size))

            rect = pg.Rect(0, 0, 0, 0)
            if type(currentOffset) == pg.Vector2:
                rect = pg.Rect((0, 0), size - 2 * currentOffset)
                rect.center = center
            elif type(currentOffset) == pg.Rect:
                rect = pg.Rect((currentOffset.x, currentOffset.w), (size.x - currentOffset.x - currentOffset.y,
                                                                    size.y - currentOffset.w - currentOffset.h))

            if shape == "rectangle":
                if type(colours[layer]) == Colours:
                    pg.draw.rect(surf, colours[layer].value, rect, border_radius=radii[layer])
                else:
                    pg.draw.rect(surf, colours[layer], rect, border_radius=radii[layer])
            else:
                pg.draw.ellipse(surf, colours[layer].value, rect)

        offset = pg.Vector2(size)
        offset.x *= offsetWidth
        offset.y *= offsetHeight

        if base:
            self.baseSurface.blit(surf, pos - offset)
        else:
            self.surface.blit(surf, pos - offset)

    def refresh(self):
        self.size = pg.Vector2(self.baseSurface.get_size())
        self.surface = self.baseSurface.copy()

    def clearSurfaces(self):
        self.surface = None
        self.baseSurface = None
        self.font = None

    def getSurface(self, image, pos=(0, 0), location=BlitLocation.topLeft):
        imageRect = pg.Rect(pos, image.get_size())

        if location == BlitLocation.centre:
            imageRect.topleft = pg.Vector2(imageRect.topleft) - pg.Vector2(imageRect.size) / 2
        elif location == BlitLocation.topRight:
            imageRect.x -= imageRect.width

        surf = pg.Surface(self.size, pg.SRCALPHA)
        surf.blit(image, imageRect.topleft)

        surfaceCopy = self.surface.copy()
        surfaceCopy.blit(surf, (0, 0))

        return surfaceCopy

    def scaleSurface(self, scale, base=False):
        self.size = pg.Vector2(self.baseSurface.get_size()) * scale
        self.surface = pg.transform.scale(self.surface, pg.Vector2(self.surface.get_size()) * scale)
        if base:
            self.baseSurface = pg.transform.scale(self.baseSurface, pg.Vector2(self.baseSurface.get_size()) * scale)
