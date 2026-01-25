import os.path

import time
import pygame as pg
from random import randint

from pokemon_legacy.engine.graphics.screen_V2 import Screen

from pokemon_legacy.engine.game_world.tiled_map import TiledMap2
from pokemon_legacy.engine.game_world.tiled_building import TiledBuilding

from pokemon_legacy.engine.game_world.game_obejct import GameObject, PokeballTile
from pokemon_legacy.maps.buildings import *

from pokemon_legacy.engine.general.utils import BlitLocation


class TallGrass(GameObject):
    def __init__(self, rect, scale: int | float = 1.0, route=None):
        GameObject.__init__(self, rect, obj_id=0, solid=False, scale=scale, auto_interact=True)

        self.route = route
        self.encounterNum = randint(15, 25)


class WaterTile(GameObject):
    def __init__(self, rect, properties, scale: int | float = 1.0):
        GameObject.__init__(self, rect, obj_id=0, solid=True, scale=scale, auto_interact=True)
        self.surfable = properties.get("surfable", False)


class PortalTile(GameObject):
    def __init__(self, rect, obj_id, map_name, scale: int | float = 1.0):
        GameObject.__init__(self, rect, obj_id=obj_id, solid=True, scale=scale, auto_interact=True)
        self.map_name = map_name


class RoutePopup(Screen, pg.sprite.Sprite):
    def __init__(self, location, scale=1.0):
        size = pg.Vector2(118, 24) * scale
        Screen.__init__(self, size)
        pg.sprite.Sprite.__init__(self)
        self.load_image("assets/maps/assets/route_popup.png", scale=scale)


        rect_box = pg.Rect(pg.Vector2(8, 2) * scale, pg.Vector2(101, 17) * scale)
        # self.add_text_2(location.replace("_", " ").title(), rect_box, )
        self.addText(location.replace("_", " ").title(), rect_box.center, location=BlitLocation.centre)

        self.rect = pg.Rect((0, 0), size)
        self.image = self.get_surface()

        self.created_time = time.monotonic()

    def update(self):
        if time.monotonic() - self.created_time > 2:
            self.kill()


class BuildingTile(GameObject):
    def __init__(
            self,
            rect: pg.Rect,
            obj_id: int,
            linked_map_name: str,
            building_link: bool = False,
            location: None | str = None
    ):
        if location:
            vals = [int(char) for char in location.split(",")]
            location = (vals[0], vals[1])

        GameObject.__init__(
            self,
            rect,
            obj_id,
            solid=True,
            auto_interact=True
        )
        self.linked_map_name = linked_map_name
        self.building_link = building_link
        self.location = location


class GameMap(TiledMap2):

    start_positions = {
        "twinleaf_town.tmx": pg.Vector2(22, 22),
        "route_219.tmx": pg.Vector2(16, 6),
        "verity_lakefront.tmx": pg.Vector2(10, 45),
    }

    building_mappings = {
        "player_house": PlayerHouse,
        "rival_house": RivalHouse,
        "pokecenter": PokeCenter,
        "pokemart": PokeMart,
    }

    def __init__(
            self,
            file_path,
            size,
            player,
            window,
            map_scale=1,
            obj_scale=1,
            render_mode=0,
    ):
        if os.path.basename(file_path) in self.start_positions:
            player_position = self.start_positions[os.path.basename(file_path)]
        else:
            player_position = pg.Vector2(31, 14)
            
        TiledMap2.__init__(
            self,
            file_path,
            size,
            player,
            player_position=player_position,
            map_scale=map_scale,
            object_scale=obj_scale,
            player_layer="4_NPCs",
            render_mode=render_mode,
        )

        self.render()

        self.window = window

    def load_objects(self):
        # load all default objects
        super().load_objects()

        for layer in self.object_layers:
            sprite_group = self.object_layer_sprites[layer.id]
            for obj in layer:
                tile = None

                rect = pg.Rect(obj.x, obj.y, obj.width, obj.height)
                if obj.type == "tall_grass":
                    tile = TallGrass(rect, route=obj.Location, scale=self.map_scale)

                elif obj.type == "building":
                    if obj.name in self.building_mappings:
                        tile = self.building_mappings[obj.name](
                            rect,
                            obj_id=obj.id,
                            player=self.player,
                            map_scale=2,
                            obj_scale=2,
                            parent_map=self
                        )

                elif obj.type == "water":
                    tile = WaterTile(rect, properties=obj.properties, scale=self.map_scale)

                elif obj.type == "pokeball":
                    item = obj.properties.get("item", None)
                    tile = PokeballTile(obj.id, rect, item=item, scale=self.map_scale)

                elif obj.type == "portal":
                    tile = PortalTile(rect, obj.id, self.map_name, scale=self.map_scale)

                if tile is not None:
                    sprite_group.add(tile)

    def object_interaction(self, sprite: pg.sprite.Sprite, *args):
        if isinstance(sprite, TiledMap2) or isinstance(sprite, TiledBuilding):
            print(f"{sprite}: Building")
            return sprite, True

        return sprite, False


if __name__ == '__main__':
    pg.init()
    native_size = pg.Vector2(256, 192)
    graphics_scale = 2
    displaySize = native_size * graphics_scale
    window = pg.display.set_mode(displaySize)

    # load all attributes which utilise any pygame surfaces!
    pg.display.set_caption('Map Files')
    pg.event.pump()

    # player = Player("assets/sprites/Player Sprites", position=pg.Vector2(14, 13))
    #
    # sinnoh_map = GameMap('pokecenter.tmx', displaySize, player=player)
    # sinnoh_map.render(player.position)
    # while True:
    #     for event in pg.event.get():
    #         if event.type == pg.QUIT:
    #             pg.quit()
    #         elif event.type == pg.KEYDOWN:
    #             ...
    #
    #     window.blit(sinnoh_map.get_surface(), (32, 32))
    #     pg.display.flip()
