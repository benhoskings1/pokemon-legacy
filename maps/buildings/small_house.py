import pygame as pg

from general.utils import Colours

from maps.tiled_map import TiledMap2, EntryTile
import importlib.resources as resources

MODULE_PATH = resources.files(__package__)


class SmallHouse(TiledMap2, EntryTile):
    def __init__(self, rect, player, map_scale=1, obj_scale=1, parent_map_scale=1.0):
        size = pg.Vector2(256, 192) * map_scale

        EntryTile.__init__(self, rect, obj_id=0, scale=parent_map_scale)

        TiledMap2.__init__(
            self,
            "maps/buildings/player_house.tmx",
            size,
            player,
            player_position=pg.Vector2(6, 8),
            map_scale=map_scale,
            object_scale=obj_scale,
            player_layer="5_player_layer",
            view_screen_tile_size=pg.Vector2(19, 18),
            map_directory=MODULE_PATH,
        )

        self.base_surface.fill(Colours.black.value)
        self.running = False

    # def load_objects(self):
    #     super().load_objects()

    # def object_interaction(self, sprite: pg.sprite.Sprite, *args):
    #     super().object_interaction(sprite, *args)

