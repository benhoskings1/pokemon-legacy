from engine.game_world.tiled_building import TiledBuilding

from engine.characters.player import Player2

import importlib.resources as resources

MODULE_PATH = resources.files(__package__)


class RivalHouse(TiledBuilding):
    def __init__(self, rect, obj_id, player: Player2, parent_map, map_scale=1, obj_scale=1):
        start_positions = [(6,  10), (3, 4)]

        TiledBuilding.__init__(
            self,
            rect,
            obj_id,
            player,
            map_dir="maps/buildings/rival_house",
            map_name="rival_house",
            map_scale=map_scale,
            parent_map=parent_map,
            start_floor=0,
            module_dir=MODULE_PATH,
            start_positions=start_positions
        )