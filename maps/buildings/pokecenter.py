import os
import os.path as path

import pygame as pg

from trainer import Trainer
from general.direction import Direction
from general.utils import Colours, wait_for_key
# from general.controller import Controller

from maps.tiled_map import TiledMap2, GameObject, Obstacle, EntryTile

import importlib.resources as resources
MODULE_PATH = resources.files(__package__)


class DeskTile(GameObject):
    def __init__(self, rect: pg.Rect, obj_id: int, scale=1, render_mode=0):
        GameObject.__init__(self, rect, obj_id, solid=True, scale=scale)
        if render_mode > 0:
            self.image = pg.Surface(self.rect.size, pg.SRCALPHA)
            pg.draw.rect(self.image, Colours.blue.value, self.image.get_rect(), 1)


class ComputerTile(Obstacle):
    def __init__(self, rect: pg.Rect, obj_id: int, scale=1):
        Obstacle.__init__(self, rect, obj_id, scale=scale)


tile_object_mapping = {
    "desk": DeskTile,
    "computer": ComputerTile,
}


class PokeCenter(TiledMap2, EntryTile):
    def __init__(self, rect, player, map_scale=1, obj_scale=1, parent_map_scale=1.0):
        size = pg.Vector2(256, 192) * map_scale

        EntryTile.__init__(self, rect, obj_id=0, scale=parent_map_scale)

        TiledMap2.__init__(
            self,
            "maps/buildings/pokecenter.tmx",
            size,
            player,
            player_position=pg.Vector2(8, 14),
            map_scale=map_scale,
            object_scale=obj_scale,
            player_layer="5_player_layer",
            view_screen_tile_size=pg.Vector2(19, 18),
            map_directory=MODULE_PATH,
        )

        self.base_surface.fill(Colours.black.value)
        self.running = False

    def __repr__(self):
        return f"PokeCenter({self.rect})"

    def load_objects(self):
        # load default objects
        super().load_objects()

        for layer in self.object_layers:
            sprite_group = self.object_layer_sprites[layer.id]
            for obj in layer:
                rect = pg.Rect(obj.x, obj.y, obj.width, obj.height)

                if obj.type in tile_object_mapping:
                    obj_tile = tile_object_mapping[obj.type](rect, obj.id, scale=self.map_scale)
                    sprite_group.add(obj_tile)

    def object_interaction(self, sprite: pg.sprite.Sprite, render_surface: pg.Surface):
        map_obj, action_complete = super().object_interaction(sprite)
        if map_obj and action_complete:
            return map_obj, True

        elif isinstance(sprite, DeskTile):
            self.display_message(
                "Hello and welcome to the pokecenter.",
                window=render_surface,
            )
            wait_for_key()

            self.display_message(
                "We restore your tired pokemon to full health.",
                    window=render_surface,
            )
            wait_for_key()
            self.display_message(
                "Would you like to rest your pokemon?",
                window=render_surface
            )
            wait_for_key()

            print("Healing all pokemon")
            self.player.team.restore()
            self.render()

        elif isinstance(sprite, ComputerTile):
            print("Computer!")

        return None, True


if __name__ == '__main__':
    ...
