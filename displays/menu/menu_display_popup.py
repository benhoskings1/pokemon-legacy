import pygame as pg

from general.controller import Controller
from graphics.sprite_screen import DisplayContainer


MENU_SELECTOR_POSITIONS = [(4, y) for y in [5 + idx * 24 for idx in range(7)]]


class MenuDisplaySelector(pg.sprite.Sprite):
    def __init__(self, scale=1):
        pg.sprite.Sprite.__init__(self)
        self.sprite_type = "menu_selector"
        self.id = None

        img_path = "assets/containers/menu/popup_selector.png"
        self.image = pg.image.load(img_path)
        if scale != 1:
            size = self.image.get_size()
            self.image = pg.transform.scale(self.image, pg.Vector2(size[0], size[1])*scale)

        self.rect = self.image.get_rect()

        scaled_positions = [pg.Vector2(pos)*scale for pos in MENU_SELECTOR_POSITIONS]
        self.rect.topleft = scaled_positions[0]

        self.positions = scaled_positions
        self.position_idx = 0

    def update_position(self, key, controller: Controller):
        self.position_idx = (self.position_idx + (1 if key == controller.down else -1)) % len(self.positions)
        self.rect.topleft = self.positions[self.position_idx]


class MenuDisplayPopup(DisplayContainer):
    def __init__(self, scale: int | float | None = None):
        img_path = 'assets/containers/menu/popup.png'
        DisplayContainer.__init__(self, img_path, "menu", (154, 2), scale=scale)
        self.sprite_type = "menu_popup"
        self.id = "menu_popup"

        self.selector = MenuDisplaySelector(scale=scale)

        self.sprites.add(self.selector)

        self.image = self.get_surface()

    def process_input(self, key, controller: Controller):
        if key in (controller.up, controller.down):
            self.selector.update_position(key, controller)
            self.refresh()
            self.image = self.get_surface()
