from enum import Enum
import pygame as pg

from sprite_screen import SpriteScreen
from Map_Files.TiledMap import TiledMap2
from displays.battle.battle_display_main import TextBox
from displays.menu.menu_display_popup import MenuDisplayPopup


class GameDisplayStates(Enum):
    pokedex = 0
    team = 1
    bag = 2
    player = 3
    save = 4
    options = 5
    exit = 6


class GameDisplay(SpriteScreen):
    def __init__(self, size, player, scale: int | float = 1):
        # ==== INIT ====
        SpriteScreen.__init__(self, size)

        self.player = player
        self.map = TiledMap2("Map_Files/Sinnoh Map.tmx", size, player=player)

        self.scale = scale

        self.text_box = TextBox(sprite_id="text_box", scale=scale, static=True)
        self.text_box.rect.topleft += pg.Vector2(3, 0) * scale
        self.player.blit_rect.center = self.surface.get_rect().center
        self.sprites.add(self.player)

    def get_surface(self, show_sprites: bool = True, offset: None | pg.Vector2 = None) -> pg.Surface:
        if self.power_off:
            return self.power_off_surface

        if show_sprites:
            self.sprites.draw(self)

        blit_pos = pg.Vector2(-64, -64) if offset is None else pg.Vector2(-64, -64) - offset
        self.add_image(self.map.get_surface(), blit_pos)

        display_surf = self.base_surface.copy()
        display_surf.blit(self.surface, (0, 0))
        display_surf.blit(self.sprite_surface, (0, 0))

        return display_surf

    def move_animation(self, window, direction, frames=20, duration=500):
        self.refresh()

        start_pos = self.player.position
        for frame in range(frames):
            window.blit(self.get_surface(offset=(direction.value * self.map.tilewidth) / frames * frame), (0, 0))
            pg.display.flip()
            pg.time.delay(int(duration / frames))

        self.player.position = start_pos + direction.value
        self.player.rect.topleft = self.player.position * self.map.tilewidth

        self.map.render(self.player.position)

    def update_display_text(self, text, max_chars=None):
        if self.text_box not in self.sprites:
            self.sprites.add(self.text_box)

        self.text_box.refresh()

        text_rect = pg.Rect(pg.Vector2(10, 4) * self.scale, pg.Vector2(201, 40) * self.scale)
        self.text_box.add_text_2(text, text_rect.inflate(-10, -18), max_chars=max_chars)
        self.text_box.update_image()

    def menu_loop(self, game):
        """
        Loop to return an action based on the menu selection
        :return:
        """
        action = None
        popup = MenuDisplayPopup(scale=game.graphics_scale)
        self.sprites.add(popup)
        game.update_display()

        while not action:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    game.running = False
                elif event.type == pg.KEYDOWN:
                    if event.key in (game.controller.y, game.controller.b):
                        popup.kill()
                        return None
                    elif event.key == game.controller.a and GameDisplayStates(popup.selector.position_idx) in game.menu_objects:
                        popup.kill()
                        return GameDisplayStates(popup.selector.position_idx)

                    else:
                        popup.process_input(event.key, controller=game.controller)
                        # game.menu_active = not game.menu_active
                        game.update_display()

    def refresh(self, sprite_only=False):
        if not sprite_only:
            self.surface = pg.Surface(self.size, pg.SRCALPHA)
        self.sprite_surface = pg.Surface(self.size, pg.SRCALPHA)

        # self.map.refresh()
