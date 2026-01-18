""" A collection of maps, linked with a networkx graph """
import networkx as nx
# import networkx_mermaid as nxm
import pygame as pg

from engine.game_world.tiled_map import TiledMap2, LinkType, MapLinkTile
from engine.characters.player import Player2

from engine.errors import MapError


class MapCollection:
    """ A collection of maps """

    def __init__(
            self,
            player: Player2,
            maps: list[TiledMap2],
            collection_name: str,
            *,
            start_map: str | TiledMap2 = None,
    ):
        self.player = player
        self.maps = maps

        for _map in maps:
            _map.parent_collection = self

        # directional graph for enhanced functionality
        self._graph = nx.DiGraph()
        self._graph.add_nodes_from(self.maps)

        if isinstance(start_map, str):
            start_map = self._get_map_node(start_map)
        elif isinstance(start_map, TiledMap2) and start_map not in self.maps:
            start_map = self.maps[0]
        else:
            start_map = self.maps[0]

        self._active_map = start_map
        self.collection_name = collection_name

    @property
    def map(self):
        return self._active_map

    @map.setter
    def map(
            self,
            new_map: TiledMap2
    ):
        """ Ensure that the map has some link to the new map """
        if self._active_map in self._graph.adj[new_map]:
            self._active_map = new_map
        else:
            raise MapError("Tried to move to a map that is not connected")

    def render(
            self,
            grid_lines: bool = False,
            start_pos: None | pg.Vector2 = None,
            camera_offset: None | pg.Vector2 = None
    ):
        """
        Render all active maps within the collection.
        """
        for _map in self._get_active_maps():
            _map.render(grid_lines=grid_lines, start_pos=start_pos, camera_offset=camera_offset)

    def detect_map_edge(self):
        return self.map.detect_map_edge()

    def get_surface(self, camera_offset: None | pg.Vector2 = None):
        maps = self._get_active_maps()

        # reverse the order of maps
        maps.reverse()
        surface = maps[0].get_surface()
        for _map in maps[1:]:
            surface.blit(_map.get_surface(), (0, 0))

        return surface

    def update_sprites(self):
        for _map in self._get_active_maps():
            self.map.update_sprites()

    def link_maps(
            self,
            map_1: str | TiledMap2,
            map_2: str | TiledMap2,
            link_type: LinkType,
            link_params: dict,
            reverse_link=False,
    ):
        """
        Link two maps (nodes) within the graph.

        :param map_1: first map. pass either the node property or the string of the node name (map_name)
        :param map_2: second map. pass either the node property or the string of the node name (map_name)
        :param link_type: one of LinkType
        :param link_params: dict with link parameters
        """
        node_1 = self._get_map_node(map_1) if isinstance(map_1, str) else map_1
        node_2 = self._get_map_node(map_2) if isinstance(map_2, str) else map_2

        if (not isinstance(node_1, TiledMap2)) or (not isinstance(node_2, TiledMap2)):
            print(f"Cannot find specified maps {map_1, map_2} ({node_1}, {node_2})")
            return

        self._graph.add_edge(
            node_1,
            node_2,
            link_type=link_type,
            link=link_params,
        )

    def _get_active_maps(self) -> list[TiledMap2]:
        """ Return a list of the active maps """
        edges = self.map.detect_map_edge()
        joint_maps = self._get_adjoining_maps(edges)

        maps = [self.map]

        if joint_maps is not None:
            maps += list(joint_maps.keys())

        return maps

    def _get_adjoining_maps(
            self,
            edges: None | list[str]  # left | right | top | bottom
    ):
        map_neighbours = self.get_map_links(self._active_map, link_type=LinkType.adjacency)
        if (map_neighbours is None) or (edges is None):
            return None

        links = {}

        for nbr, link_dict in map_neighbours.items():
            map_link_pos = link_dict["link"][self._active_map.map_name]

            if map_link_pos[0] == 0 and "left" in edges:
                links.update({nbr: link_dict["link"]})
            elif map_link_pos[0] >= self._active_map.width - 1 and "right" in edges:
                links.update({nbr: link_dict["link"]})
            elif map_link_pos[1] == 0 and "top" in edges:
                links.update({nbr: link_dict["link"]})
            elif map_link_pos[1] >= self._active_map.height - 1 and "bottom" in edges:
                links.update({nbr: link_dict["link"]})

        return links if len(links) > 0 else None

    def _get_adjacent_maps(
            self,
            _map: TiledMap2,
    ):
        return self.get_map_links(_map, link_type=LinkType.adjacency)

    def get_map_links(
            self,
            _map: TiledMap2,
            *,
            link_type: None | LinkType = None
    ):
        """ Get all links of specified type between two maps """
        map_neighbours = self._graph.adj[_map]

        links = {
            nbr: link_dict for nbr, link_dict in map_neighbours.items()
            if (link_type is None) or (link_dict.get("link_type", None) == link_type)
        }

        return links if len(links) > 0 else None

    def _get_map_node(self, map_name: str) -> TiledMap2:
        """ Get a map node that matches the map name """
        return next((n for n in self._graph.nodes if n.map_name == map_name), None)

    def _get_sprites(
            self,
            *,
            sprite_type: type
    ) -> None | dict[TiledMap2, list[pg.sprite.Sprite]]:
        sprites = {}
        for _map in self.maps:
            _map: TiledMap2
            sprites[_map] = _map.get_sprite_types(sprite_type=sprite_type)

        return sprites if len(sprites) > 0 else None

    def link_internal_maps(self):
        map_links = {
            _map: _map.get_sprite_types(MapLinkTile) for _map in self.maps
        }

        for _map, link_tiles in map_links.items():
            link_tiles: list[MapLinkTile]
            for link_tile in [t for t in link_tiles if t.map_link_type == LinkType.map_link]:
                link_tile: MapLinkTile
                self.link_maps(
                    _map,
                    link_tile.linked_map_name,
                    link_type=LinkType.map_link,
                    link_params={"location": link_tile.location},
                )

    # === Utils API ===
    def write_to_mermaid(self):
        ...
        # builder = nxm.builders.DiagramBuilder(
        #     orientation=nxm.DiagramOrientation.LEFT_RIGHT,
        #     node_shape=nxm.DiagramNodeShape.ROUND_RECTANGLE,
        # )
        #
        # mermaid_diagram: nxm.typing.MermaidDiagram = builder.build(self.route_graph)
        # markdown_diagram: str = nxm.formatters.markdown(mermaid_diagram)
        # return markdown_diagram

    def write_to_latex(self, filename: str):
        nx.write_latex(self._graph, f"{filename}.tex", caption="A caption")

