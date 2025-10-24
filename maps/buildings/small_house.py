
import pygame as pg

from general.utils import Colours

from maps.tiled_map import TiledMap2, GameObject


class SmallHouse(TiledMap2, GameObject):

    def __init__(self, rect, player, map_scale=1, obj_scale=1, parent_map_scale=1.0):
        size = pg.Vector2(256, 192) * map_scale

        GameObject.__init__(self, rect, obj_id=0, solid=True, scale=parent_map_scale)

        TiledMap2.__init__(
            self,
            "maps/pokecenter.tmx",
            size,
            player,
            player_position=pg.Vector2(8, 14),
            map_scale=map_scale,
            object_scale=obj_scale,
            player_layer="5_player_layer",
            view_screen_tile_size=pg.Vector2(19, 18)
        )

        self.base_surface.fill(Colours.black.value)
        self.running = False

