import os
import os.path as path

import pygame as pg

from general.utils import Colours
from general.controller import Controller

from maps.tiled_map import TiledMap2, GameObject, Obstacle

move_directions = {pg.K_UP: (0, 1), pg.K_DOWN: (0, -1), pg.K_LEFT: (1, 0), pg.K_RIGHT: (-1, 0)}


class ExitTile(GameObject):
    def __init__(self, rect: pg.Rect, obj_id: int, scale=1):
        GameObject.__init__(self, rect, obj_id, solid=True, scale=scale)


class DeskTile(Obstacle):
    def __init__(self, rect: pg.Rect, obj_id: int, scale=1):
        Obstacle.__init__(self, rect, obj_id, scale)


class ComputerTile(Obstacle):
    def __init__(self, rect: pg.Rect, obj_id: int, scale=1):
        Obstacle.__init__(self, rect, obj_id, scale)


tile_object_mapping = {
    "exit" : ExitTile,
    "desk" : DeskTile,
    "computer": ComputerTile,
}


class PokeCenter(TiledMap2, GameObject):
    def __init__(self, rect, player, map_scale=1, obj_scale=1, parent_map_scale=1.0):
        size = pg.Vector2(256, 192) * map_scale

        # TODO: work out why the
        TiledMap2.__init__(self, "maps/pokecenter.tmx", size, player,
                           player_position=pg.Vector2(8, 14), map_scale=map_scale, object_scale=obj_scale,
                           player_layer="5_player_layer",
                           view_screen_tile_size=pg.Vector2(19, 18))

        GameObject.__init__(self, rect, obj_id=0, solid=False, scale=parent_map_scale)
        self.base_surface.fill(Colours.black.value)
        self.base_image = pg.image.load(path.join("maps/assets/pokecenter_floor_0.png"))
        self.base_image = pg.transform.scale(self.base_image, size)
        self.player = player

        self.tile_size = pg.Vector2(16, 13) * map_scale

        self.running = True

    def __repr__(self):
        return f"PokeCenter(rect:, {self.map_scale})"

    def load_objects(self):
        # load default objects
        super().load_objects()

        # TODO: Update to use scaled version of the objects!
        for obj in self.objects:
            rect = pg.Rect(obj.x, obj.y, obj.width, obj.height)

            if obj.type in tile_object_mapping:
                obj_tile = tile_object_mapping[obj.type](rect, obj.id, scale=self.map_scale)
                self.obstacles.add(obj_tile)

    def object_interaction(self, sprite: pg.sprite.Sprite):
        """ hook for automatic object interactions """
        if isinstance(sprite, ExitTile):
            self.running = False
            return sprite

        return None

    def intentional_interaction(self, sprite: pg.sprite.Sprite, render_surface: pg.Surface):
        """ hook for player triggered interactions """
        if isinstance(sprite, DeskTile):
            self.display_message("Hello and welcome to the pokecenter.",
                                 window=render_surface, )
            self.display_message("We restore your tired pokemon to full health.",
                                 window=render_surface, )
            self.display_message("Would you like to rest your pokemon?",
                                 window=render_surface)
            print("Healing all pokemon")
            self.player.team.restore()

        elif isinstance(sprite, ComputerTile):
            print("Computer!")

    def loop(self, render_surface, controller=Controller()):
        self.render()
        render_surface.blit(self.get_surface(), (0, 0))
        pg.display.flip()
        print("starting pokecenter loop")
        self.running = True
        while self.running:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.running = False

                elif event.type == pg.KEYDOWN:
                    if event.key in controller.move_keys:
                        player_moving = True

                        while player_moving:
                            collision = self.move_player(
                                controller.direction_key_bindings[event.key],
                                window=render_surface
                            )

                            # if collision:
                            #     self.object_interaction(collision)
                            #     if not self.running:
                            #         break

                            pg.display.flip()

                            for event_2 in pg.event.get():
                                if event_2.type == pg.KEYUP:
                                    player_moving = False

                    elif event.key == controller.a:
                        obj_collision = self.check_collision(self.player, self.player.facing_direction)

                        if obj_collision:
                            self.intentional_interaction(obj_collision, render_surface)

    # def move_trainer(self, trainer, direction, window, move_duration=2000):
    #     super().move_trainer(trainer, direction, window, move_duration=move_duration)


if __name__ == '__main__':
    from player import Player

    pg.init()

    player = Player("Sprites/Player Sprites")
    center = PokeCenter(pg.Rect(100, 100, 100, 100), player, 2)

    pg.init()
    display = pg.display.set_mode((512, 384))

    while True:
        for event in pg.event.get():
            if event.type == pg.KEYDOWN:
                if event.key in move_directions:
                    player.position += move_directions[event.key]

                display.fill((0, 0, 0))
                center.render(player.position)
                display.blit(center.get_surface(), (0, 0))
                pg.display.flip()
