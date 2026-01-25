import warnings
import hashlib

import pygame as pg
from pokemon_legacy.engine.general.utils import Colours
from pokemon_legacy.constants import ASSET_PATH
import os


def sha256_hash(data):
    return hashlib.sha256(data).hexdigest()


class GameObject(pg.sprite.Sprite):
    def __init__(
            self,
            rect: pg.Rect,
            obj_id: None | int | str,
            solid: bool = True,
            scale: int | float = 1.0,
            custom_image: bool = False,
            auto_interact: bool = False,
            render_mode=0,
            **kwargs
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
            if render_mode > 0:
                self.image = pg.Surface(self.rect.size, pg.SRCALPHA)
                pg.draw.rect(self.image, Colours.green.value, self.image.get_rect(), 1)

        self.solid = solid
        self.auto_interact = auto_interact

        if self.obj_id is None:
            # raise warning
            warnings.warn(f"No object id provided for {self.__class__.__name__} object")

        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])

    def __repr__(self):
        return f"{self.__class__.__name__} at {self.rect} <id:{self.obj_id}>"

    def interaction(self, *args):
        """ hook function """
        return None


class PokeballTile(GameObject):
    def __init__(self, obj_id: int, rect, item, scale: int | float = 1.0):
        GameObject.__init__(self, rect, obj_id=obj_id, solid=True, scale=scale)

        self.image = pg.image.load(os.path.join(ASSET_PATH, "maps/assets/overworld/objects/pokeball.png"))
        if scale != 1:
            self.image = pg.transform.scale(self.image, pg.Vector2(self.image.get_size()) * scale)

        self.item = item

    def __repr__(self):
        return f"PokeballTile({self.item})"