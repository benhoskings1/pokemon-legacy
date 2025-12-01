"""
Tiled Building Object. Supports Multiple Floors.
"""
import os
import re
import importlib.resources as resources

import pygame as pg

from engine.characters.character import Character
from engine.game_world.map_collection import MapCollection

from engine.game_world.tiled_map import TiledMap2, MapLinkTile, LinkType
from general.direction import Direction
from general.utils import Colours

MODULE_PATH = resources.files(__package__)


class TiledBuilding(MapLinkTile, MapCollection):
    def __init__(
            self,
            rect,
            obj_id,
            player,
            map_dir,
            parent_map: TiledMap2,
            map_name: str,
            module_dir: str,
            map_scale=1,
            obj_scale=1,
            start_floor: int = 0,
            start_positions: None | tuple = None
    ):
        screen_size = pg.Vector2(256, 192) * map_scale
        MapLinkTile.__init__(self, rect, obj_id, linked_map_name=map_name, scale=2, map_link_type=LinkType.child)

        floor_files = sorted([f for f in os.listdir(map_dir) if re.match(r"floor_\d.tmx", f)])
        if start_positions is None:
            start_positions = [None] * len(floor_files)

        floors: list[TiledMap2] = [
            TiledMap2(
                os.path.join(map_dir, map_file),
                screen_size,
                player,
                player_position=pg.Vector2(start_positions[idx]),
                map_scale=map_scale,
                object_scale=obj_scale,
                view_screen_tile_size=pg.Vector2(19, 18),
                map_directory=module_dir,
                base_colour=Colours.black,
            ) for idx, map_file in enumerate(floor_files)
        ]

        MapCollection.__init__(self, player, floors, collection_name=map_name, start_map=f"floor_{start_floor}")

        self.player = player
        self.map_name = map_name

    def move_player(self, direction: Direction, window, check_facing_direction=True):
        """ Moves the player by a given direction """
        collision, moved = self.map.move_trainer(
            self.player, direction, window, check_facing_direction=check_facing_direction
        )
        edge = self.detect_map_edge()

        return collision, moved, edge

    def check_trainer_collision(self):
        trainers = self.map.get_sprite_types(Character)
        trainers = [c for c in trainers if hasattr(c, "vision_rect")]
        trainer = self.player.map_rects[self.map].collideobjects(trainers, key=lambda o: o.get_vision_rect(self.map))
        return trainer

    def get_sprite_types(self, sprite_type) -> dict[TiledMap2, list[pg.sprite.Sprite]]:
        return {floor: floor.get_sprite_types(sprite_type) for floor in self.maps}