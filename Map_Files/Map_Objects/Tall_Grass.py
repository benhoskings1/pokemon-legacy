from random import randint

import pygame as pg

White = pg.Color(255, 255, 255)


class TallGrass(pg.sprite.Sprite):
    def __init__(self, rect, scale, route=None):
        pg.sprite.Sprite.__init__(self)
        size = pg.Vector2(rect.size) * scale
        pos = pg.Vector2(rect.topleft) * scale
        self.rect = pg.Rect(pos, size)
        self.surf = pg.Surface(self.rect.size)
        self.surf.fill(White)
        self.route = route
        self.encounterNum = randint(15, 25)

    def __repr__(self):
        return f"Tall Grass at {self.rect}"


class Obstacle(pg.sprite.Sprite):
    def __init__(self, rect, scale):
        pg.sprite.Sprite.__init__(self)
        size = pg.Vector2(rect.size) * scale
        pos = pg.Vector2(rect.topleft) * scale
        self.rect = pg.Rect(pos, size)
        self.surf = pg.Surface(self.rect.size, pg.SRCALPHA)

    def __repr__(self):
        return f"Obstacle at {self.rect}"
