from dataclasses import dataclass
from pathlib import Path

from enum import Enum
import pygame as pg
import networkx as nx
from typing import Any

from pokemon_legacy.engine.general.direction import Direction, opposite_direction_mapping

MODULE_PATH = Path(__file__).parent


@dataclass(frozen=True)
class SelectorNode:
    """ Properties to store on the selector node"""
    value: Enum | Any
    pos: tuple
    scale: int | float = 1.0


# ==== Sprites =======
class OptionSelector(pg.sprite.Sprite):
    preset_paths = {
        "arrow": str(MODULE_PATH / "assets" / "selector_arrow.png"),
    }

    def __init__(
            self,
            selector: str,  # arrow |
            options,
            positions,
            start_option=None,
            scale=1
    ):
        """

        :param selector:
        """
        super().__init__()

        selector_path = self.preset_paths[selector] if selector in self.preset_paths else selector

        self.image = pg.image.load(selector_path)
        self.image = pg.transform.scale(
            self.image, pg.Vector2(self.image.get_size()) * scale
        )

        self.sprite_type = "selector"

        self.selected = list(options)[0] if start_option is None else start_option

        self.scale = scale

        self.option_graph = nx.DiGraph()

        for idx, option in enumerate(options):
            graph_node = SelectorNode(option, tuple(positions[idx][0:2]), scale=scale)
            self.option_graph.add_node(graph_node)

    @property
    def rect(self):
        selected_node = self.get_map_node(self.selected)
        return pg.Rect(pg.Vector2(selected_node.pos)*selected_node.scale, self.image.get_size())

    def get_map_node(self, option_value) -> SelectorNode:
        """ Get a map node that matches the map name """
        return next((n for n in self.option_graph.nodes if n.value == option_value), None)

    def link_options(
            self,
            option_1,
            option_2,
            direction: Direction,
            reverse=True
    ):
        node_1 = self.get_map_node(option_1)
        node_2 = self.get_map_node(option_2)

        try:
            for n in [node_1, node_2]:
                assert n is not None, (
                    f"{option_1 if n is node_1 else option_2} is not a valid option. "
                    f"Please make sure to link one of these values: "
                    f"{[node.map_name for node in self.option_graph.nodes]}"
                )
        except AssertionError as e:
            raise e

        self.option_graph.add_edge(node_1, node_2, link=direction)  # unpack edge tuple*

        if reverse:
            self.option_graph.add_edge(node_2, node_1, link=opposite_direction_mapping[direction])


    def process_interaction(self, direction: Direction):
        node_neighbors = self.option_graph.adj[self.get_map_node(self.selected)]

        match = next((nbr for nbr, link_dict in node_neighbors.items() if link_dict["link"] == direction), None)
        if match:
            self.selected = match.value

        return match

    def reset(self):
        self.selected = list(self.option_graph.nodes)[0].value