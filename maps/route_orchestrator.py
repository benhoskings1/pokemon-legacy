import os

import pygame as pg
from pytmx import TiledMap

from maps.tiled_map import TiledMap2
from engine.characters.player import Player2
# from trainer import Player2
import networkx as nx

from team import Team

from maps.game_map import GameMap


class RouteOrchestrator:

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
            map_scale: int | float = 1.0,
            obj_scale: int | float = 1.0,
            render_mode: int = 0
    ):
        route_files = [f for f in os.listdir("maps/routes") if f.endswith(".tmx")]
        self.routes = [
            GameMap(
                os.path.join("maps/routes/", f),
                size,
                player,
                window,
                map_scale=map_scale,
                obj_scale=obj_scale,
                render_mode=render_mode
            ) for f in route_files
        ]

        self.route_graph = nx.Graph()
        self.route_graph.add_nodes_from(self.routes)

        for m1, m2, p1, p2 in self.sinnoh_links:
            self.link_routes(m1, m2, pg.Vector2(p1), pg.Vector2(p2))

        # for each pair of portals in the entire map, link the map and the output position
        self.portal_mapping = {
        }

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
            edges: list[str]  # left | right | top | bottom
    ):
        if edges is None or _map not in self.route_graph.nodes:
            return None

        map_neighbours = self.route_graph.adj[_map]

        links = {}

        for nbr, link_dict in map_neighbours.items():
            map_link_pos = link_dict["link"][_map.map_name]

            if map_link_pos[0] == 0 and "left" in edges:
                links.update({nbr: link_dict["link"]})
            elif map_link_pos[0] >= _map.width - 1 and "right" in edges:
                links.update({nbr: link_dict["link"]})
            elif map_link_pos[1] == 0 and "top" in edges:
                links.update({nbr: link_dict["link"]})
            elif map_link_pos[1] >= _map.height - 1 and "bottom" in edges:
                links.update({nbr: link_dict["link"]})

        return links if len(links) > 0 else None


if "__main__" == __name__:
    os.chdir("../")
    print(os.getcwd())
    player = Player2((10, 10), Team(["hi"]))
    orchestrator = RouteOrchestrator((600, 500), player=player, window=pg.display.set_mode((600, 500)))
    orchestrator.get_map_node("twinleaf_town")