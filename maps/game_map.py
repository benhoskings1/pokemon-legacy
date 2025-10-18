import pytmx
import pygame as pg
from random import randint

from general.utils import Colours
from player import Player
from trainer import Trainer, TrainerTypes, AttentionBubble

from maps.tiled_map import TiledMap2, GameObject
from maps.pokecenter import PokeCenter


class EntryTile(GameObject):
    def __init__(self, rect: pg.Rect, obj_id: int, scale=1.0):
        GameObject.__init__(self, rect, obj_id, solid=False, scale=scale)


class TallGrass(GameObject):
    def __init__(self, rect, scale: int | float = 1.0, route=None):
        GameObject.__init__(self, rect, obj_id=0, solid=False, scale=scale)

        self.route = route
        self.encounterNum = randint(15, 25)


class GameMap(TiledMap2):
    def __init__(self, file_path, size, player, window, map_scale=1, obj_scale=1):
        TiledMap2.__init__(
            self,
            file_path,
            size,
            player,
            player_position=pg.Vector2(10, 9),
            map_scale=map_scale,
            object_scale=obj_scale,
            player_layer="4_NPCs"
        )

        # self.load_objects()
        self.render()

        self.window = window

    def load_custom_object_layers(self):
        """ loads the default object layers """
        for layer in self.object_layers:
            sprite_group = self.object_layer_sprites[layer.id]
            for obj in layer:
                rect = pg.Rect(obj.x, obj.y, obj.width, obj.height)
                if obj.type == "entry_tile":
                    pokecenter = PokeCenter(rect, player=self.player, map_scale=2, obj_scale=2)
                    sprite_group.add(pokecenter)

            self.object_layer_sprites[layer.id] = sprite_group

    def load_objects(self):
        # load all default objects
        super().load_objects()

        for layer in self.object_layers:
            sprite_group = self.object_layer_sprites[layer.id]
            for obj in layer:
                rect = pg.Rect(obj.x, obj.y, obj.width, obj.height)
                if obj.name == "Grass":
                    grass = TallGrass(rect, route=obj.Location, scale=self.map_scale)
                    sprite_group.add(grass)

                elif obj.name == "pokecenter":
                    pokecenter = PokeCenter(rect, player=self.player, map_scale=2, obj_scale=2)
                    sprite_group.add(pokecenter)

    def object_interaction(self, sprite: pg.sprite.Sprite):
        if isinstance(sprite, PokeCenter):
            sprite: PokeCenter
            sprite.loop(self.window)

        return None

    def detect_collision(self) -> pg.sprite.Sprite:
        """
        Detects collisions between the player and the grass objects.
        """
        player_rect = self.player.map_rects[self]
        collisions = player_rect.collideobjects(self.grassObjects.sprites(), key=lambda o: o.rect)
        return collisions


if __name__ == '__main__':
    pg.init()
    native_size = pg.Vector2(256, 192)
    graphics_scale = 2
    displaySize = native_size * graphics_scale
    window = pg.display.set_mode(displaySize)

    # load all attributes which utilise any pygame surfaces!
    pg.display.set_caption('Map Files')
    pg.event.pump()

    player = Player("Sprites/Player Sprites", position=pg.Vector2(14, 13))

    sinnoh_map = GameMap('pokecenter.tmx', displaySize, player=player)
    sinnoh_map.render(player.position)
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
            elif event.type == pg.KEYDOWN:
                ...

        window.blit(sinnoh_map.get_surface(), (32, 32))
        pg.display.flip()
