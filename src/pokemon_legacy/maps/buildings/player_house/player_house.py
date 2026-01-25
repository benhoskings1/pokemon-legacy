from pokemon_legacy.engine.game_world.tiled_building import TiledBuilding
import importlib.resources as resources

import importlib.resources as resources
from pokemon_legacy.constants import ASSET_PATH
import os

# MODULE_PATH = resources.files(__package__)


class PlayerHouse(TiledBuilding):
    def __init__(self, rect, obj_id, player, parent_map, map_scale=1, obj_scale=1):
        start_positions = [(10,  3), (4, 6)]

        TiledBuilding.__init__(
            self,
            rect,
            obj_id,
            player,
            map_dir=os.path.join(ASSET_PATH, "maps/buildings/player_house"),
            map_name="player_house",
            map_scale=map_scale,
            parent_map=parent_map,
            start_floor=1,
            module_dir=None,
            start_positions=start_positions
        )
