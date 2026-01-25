import os

import pygame as pg
from pokemon_legacy.constants import ASSET_PATH

from pokemon_legacy.engine.game_world.tiled_map import LinkType
from pokemon_legacy.engine.game_world.tiled_building import TiledBuilding

from pokemon_legacy.engine.characters.player import Player2

from pokemon_legacy.engine.pokemon.team import Team

from pokemon_legacy.engine.game_world.game_map import GameMap
from pokemon_legacy.engine.game_world.map_collection import MapCollection


class RouteOrchestrator(MapCollection):

    sinnoh_links = {
        ("twinleaf_town", "route_201", (16, 0), (14, 28)),
        ("route_201", "sandgem_town", (64, 12), (0, 16)),
        ("verity_lakefront", "route_201", (24, 38), (0, 9)),
        ("sandgem_town", "route_219", (20, 32), (20, 0)),
    }

    def __init__(
            self,
            size,
            player: Player2,
            window,
            *,
            start_map="twinleaf_town",
            map_scale: int | float = 1.0,
            obj_scale: int | float = 1.0,
            render_mode: int = 0
    ):
        map_dir = os.path.join(ASSET_PATH, "maps/routes")
        route_files = [f for f in os.listdir(map_dir) if f.endswith(".tmx")]
        routes = [
            GameMap(
                os.path.join(map_dir, f),
                size,
                player,
                window,
                map_scale=map_scale,
                obj_scale=obj_scale,
                render_mode=render_mode
            ) for f in route_files
        ]

        MapCollection.__init__(self, player, routes, collection_name="route_orchestrator", start_map=start_map)

        for m1, m2, p1, p2 in self.sinnoh_links:
            self.link_routes(m1, m2, pg.Vector2(p1), pg.Vector2(p2))

        self.link_buildings()

        # for each pair of portals in the entire map, link the map and the output position
        self.portal_mapping = {
        }


        self.link_internal_maps()

    def link_routes(self, route_1, route_2, pos_1, pos_2):
        node_1 = self._get_map_node(route_1)
        node_2 = self._get_map_node(route_2)

        self.link_maps(
            node_1,
            node_2,
            link_type=LinkType.adjacency,
            link_params={route_1: pos_1, route_2: pos_2}
        )
        self.link_maps(
            node_2,
            node_1,
            link_type=LinkType.adjacency,
            link_params={route_1: pos_1, route_2: pos_2}
        )

    def link_buildings(self):
        building_links = self._get_sprites(sprite_type=TiledBuilding)

        if building_links is None:
            return None

        for game_map, buildings in building_links.items():
            for building in buildings:
                building: TiledBuilding
                self._graph.add_edge(
                    game_map, building.map, link_type=LinkType.child, link={}
                )
                building._graph.add_edge(
                    building._get_map_node("floor_0"), game_map, link_type=LinkType.parent, link={}
                )

                building.link_internal_maps()

        return None


if __name__ == "__main__":

    # os.chdir("../")
    # print(os.getcwd())
    pg.init()
    pg.display.set_mode((400, 400))
    player = Player2((10, 10), Team(["hi"]))
    orchestrator = RouteOrchestrator((600, 500), player=player, window=pg.display.set_mode((600, 500)))
    print(orchestrator._get_map_node("player_house"))

    diagram = orchestrator.write_to_mermaid()

    with open('route_graph.md', 'w') as f:
        f.write(diagram)

    print(diagram)