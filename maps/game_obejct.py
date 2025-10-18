import pygame as pg
from general.utils import Colours


class GameObject(pg.sprite.Sprite):
    def __init__(
            self,
            rect: pg.Rect,
            obj_id: int,
            solid: bool = True,
            scale: int | float = 1.0,
            custom_image: bool = False,
    ):
        """
        base class for any game object.

        :param rect: the rect of the object on the game map
        :param obj_id: unique id to reference the object
        :param solid: can the object be walked on
        :param scale: the scale of the object within the map
        """
        pg.sprite.Sprite.__init__(self)
        size = pg.Vector2(rect.size) * scale
        pos = pg.Vector2(rect.topleft) * scale

        self.obj_id = obj_id
        self.rect = pg.Rect(pos, size)

        if not custom_image:
            self.image = pg.Surface(self.rect.size, pg.SRCALPHA)
            pg.draw.rect(self.image, Colours.green.value, self.image.get_rect(), 1)

        self.solid = solid

    def __repr__(self):
        return f"{self.__class__.__name__} at {self.rect} <id:{self.obj_id}>"