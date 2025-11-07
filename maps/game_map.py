import os.path

import time
import pygame as pg
from random import randint

from graphics.screen_V2 import Screen
from maps.tiled_map import TiledMap2, GameObject
from maps.buildings.pokecenter import PokeCenter
from maps.buildings.small_house import SmallHouse

from general.utils import BlitLocation


class TallGrass(GameObject):
    def __init__(self, rect, scale: int | float = 1.0, route=None):
        GameObject.__init__(self, rect, obj_id=0, solid=False, scale=scale, auto_interact=True)

        self.route = route
        self.encounterNum = randint(15, 25)


class RoutePopup(Screen, pg.sprite.Sprite):
    def __init__(self, location, scale=1.0):
        size = pg.Vector2(118, 24) * scale
        Screen.__init__(self, size)
        pg.sprite.Sprite.__init__(self)
        self.load_image("maps/assets/route_popup.png", scale=scale)


        rect_box = pg.Rect(pg.Vector2(8, 2) * scale, pg.Vector2(101, 17) * scale)
        # self.add_text_2(location.replace("_", " ").title(), rect_box, )
        self.addText(location.replace("_", " ").title(), rect_box.center, location=BlitLocation.centre)

        self.rect = pg.Rect((0, 0), size)
        self.image = self.get_surface()

        self.created_time = time.monotonic()

    def update(self):
        if time.monotonic() - self.created_time > 2:
            self.kill()


class GameMap(TiledMap2):

    start_positions = {
        "Sinnoh Map.tmx": pg.Vector2(31, 14),
        "Twinleaf Town.tmx": pg.Vector2(21, 32)
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
                rect = pg.Rect(obj.x, obj.y, obj.width, obj.height)
                if obj.type == "tall_grass":
                    grass = TallGrass(rect, route=obj.Location, scale=self.map_scale)
                    sprite_group.add(grass)

                elif obj.name == "pokecenter":
                    pokecenter = PokeCenter(rect, player=self.player, map_scale=2, obj_scale=2,
                                            parent_map_scale=self.map_scale)
                    sprite_group.add(pokecenter)

                elif obj.type == "entry_tile":
                    if obj.name == "player_house":
                        game_object = SmallHouse(
                            rect, player=self.player, map_scale=2, obj_scale=2,
                            parent_map_scale=self.map_scale
                        )
                        sprite_group.add(game_object)

    def object_interaction(self, sprite: pg.sprite.Sprite, *args):
        if isinstance(sprite, TiledMap2):
            return sprite, True

        return None, False


if __name__ == '__main__':
    pg.init()
    native_size = pg.Vector2(256, 192)
    graphics_scale = 2
    displaySize = native_size * graphics_scale
    window = pg.display.set_mode(displaySize)

    # load all attributes which utilise any pygame surfaces!
    pg.display.set_caption('Map Files')
    pg.event.pump()

    # player = Player("Sprites/Player Sprites", position=pg.Vector2(14, 13))
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
