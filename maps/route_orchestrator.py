import os

import pygame as pg
from pytmx import TiledMap

from maps.tiled_map import TiledMap2
from trainer import Player2
import networkx as nx

from team import Team

from maps.game_map import GameMap


class RouteOrchestrator:
    def __init__(self, size, player, window, map_scale = 1.0, obj_scale = 1.0):
        route_files = [f for f in os.listdir("maps/routes") if f.endswith(".tmx")]
        self.routes = [
            GameMap(
                os.path.join("maps/routes/", f),
                size,
                player,
                window,
                map_scale=map_scale,
                obj_scale=obj_scale
            ) for f in route_files
        ]

        self.route_graph = nx.Graph()
        self.route_graph.add_nodes_from(self.routes)

        # TODO convert this to a static config set
        self.link_routes(
            "twinleaf_town.tmx", "route_201.tmx",
            pg.Vector2(16, 0), pg.Vector2(14, 32)
        )

    def load_player_positions(self):
        ...

    def get_map_node(self, map_name) -> GameMap:
        """ Get a map node that matches the map name """
        return next((n for n in self.route_graph.nodes if n.map_name == map_name), None)

    def link_routes(self, route_1, route_2, pos_1, pos_2):
        node_1 = self.get_map_node(route_1)
        node_2 = self.get_map_node(route_2)

        try:
            for n in [node_1, node_2]:
                assert n is not None, (
                    f"{route_1 if n is node_1 else route_2} is not a valid option. "
                    f"Please make sure to link one of these values: "
                    f"{[node.map_name for node in self.route_graph.nodes]}"
                )
        except AssertionError as e:
            raise e

        self.route_graph.add_edge(node_1, node_2, link={route_1: pos_1, route_2: pos_2})  # unpack edge tuple*

    def get_adjoining_map(
            self,
            _map: TiledMap,
            edge: str  # left | right | top | bottom
    ):
        map_neighbours = self.route_graph.adj[_map]

        for nbr, link_dict in map_neighbours.items():
            map_link_pos = link_dict["link"][_map.map_name]

            if map_link_pos[0] == 0 and edge == "left":
                return {nbr: link_dict["link"]}
            elif map_link_pos[0] >= _map.width - 1 and edge == "right":
                return {nbr: link_dict["link"]}
            elif map_link_pos[1] == 0 and edge == "top":
                return {nbr: link_dict["link"]}
            elif map_link_pos[1] >= _map.height - 1 and edge == "bottom":
                return {nbr: link_dict["link"]}

        return None


if "__main__" == __name__:
    os.chdir("../")
    print(os.getcwd())
    player = Player2((10, 10), Team(["hi"]))
    orchestrator = RouteOrchestrator((600, 500), player=player, window=pg.display.set_mode((600, 500)))
    orchestrator.get_map_node("twinleaf_town")