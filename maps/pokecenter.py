import os.path as path
import importlib.resources as resources

import pygame as pg

from sprite_screen import SpriteScreen


# MODULE_PATH = resources.files(__package__)

move_directions = {pg.K_UP: (0, 1), pg.K_DOWN: (0, -1), pg.K_LEFT: (1, 0), pg.K_RIGHT: (-1, 0)}


class PokeCenter(SpriteScreen):
    def __init__(self, player=None, scale=1):
        size = pg.Vector2(256, 192) * scale
        SpriteScreen.__init__(self, size)
        self.base_image = pg.image.load(path.join("maps/assets/pokecenter_floor_0.png"))
        self.base_image = pg.transform.scale(self.base_image, size)
        self.player = player

        if player:
            self.player.blit_rect.center = self.surface.get_rect().center
            self.sprites.add(player)

        self.tile_size = 16*scale

    def render(self, player_pos):
        self.refresh()

        self.add_image(self.base_image, player_pos*self.tile_size)


if __name__ == '__main__':
    from player import Player

    player = Player("Sprites/Player Sprites")
    center = PokeCenter(player, 2)

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
