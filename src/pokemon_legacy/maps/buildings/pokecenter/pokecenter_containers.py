import os
import importlib.resources as resources
from enum import Enum
import time

import pygame as pg

from pokemon_legacy.engine.general.direction import Direction
from pokemon_legacy.engine.graphics.sprite_screen import DisplayContainer
from pokemon_legacy.engine.graphics.selector_display import SelectorDisplay

MODULE_PATH = resources.files(__package__)

class ConfirmOption(Enum):
    yes = 1
    no = 0


class ConfirmContainer(SelectorDisplay):
    def __init__(self, scale=1.0):
        container_img_path = os.path.join(MODULE_PATH, "assets/containers/confirm_container.png")
        selector_img_path = os.path.join(MODULE_PATH, "assets/selector_arrow.png")

        SelectorDisplay.__init__(
            self,
            container_img_path,
            selector_img_path,
            scale=scale,
            options=[ConfirmOption.yes, ConfirmOption.no],
            option_positions=[(6, 9), (6, 25)],
            display_posistion=pg.Vector2(178, 98),
        )

        self.link_options(ConfirmOption.yes, ConfirmOption.no, direction=Direction.down, reverse=True)


class PokeballIcon(pg.sprite.Sprite):
    def __init__(self, pos: None | pg.Vector2 = None, scale=1.0):
        pg.sprite.Sprite.__init__(self)
        image = pg.image.load(os.path.join(MODULE_PATH, "assets/pokeball_icon.png"))

        if scale != 1.0:
            image = pg.transform.scale(image, pg.Vector2(image.get_size())*scale)

        self.image = image
        self.rect = self.image.get_rect()
        if pos is not None:
            self.rect.topleft = pos

        self.created = time.monotonic()

    def update(self):
        # TODO add yellow glow over lifetime
        ...


class PokeballIncubator(DisplayContainer):

    pokeball_locations = [
        (6, 10), (15, 10),
        (6, 14), (15, 14),
        (6, 18), (15, 18),

    ]

    def __init__(self, scale=1.0):
        image_path = os.path.join(MODULE_PATH, "assets/incubator.png")
        DisplayContainer.__init__(self, image_path, "incubator", pg.Vector2(92, 35), scale)

        self.pokeball_count = 0

    def add_pokeball(self):
        icon = PokeballIcon(pos=pg.Vector2(self.pokeball_locations[self.pokeball_count])*self.scale, scale=self.scale)
        self.sprites.add(icon)
        self.pokeball_count += 1

    def reset(self):
        self.pokeball_count = 0
        self.sprites.empty()
        self.refresh()


class ComputerSelectOption(Enum):
    someones = 0
    players = 1
    rowans = 2
    switch_off = 3


class ComputerSelector(SelectorDisplay):
    def __init__(self, scale=1.0):
        container_img_path = os.path.join(MODULE_PATH, "assets/containers/computer_select.png")
        selector_img_path = os.path.join(MODULE_PATH, "assets/selector_arrow.png")
        options = list(ComputerSelectOption)
        SelectorDisplay.__init__(
            self,
            container_img_path,
            selector_img_path,
            scale=scale,
            options=options,
            option_positions=[(6, 9), (6, 25), (6, 41), (6, 57)],
            display_posistion=pg.Vector2(2, 2),
        )

        # define node links here
        for idx in range(len(options) - 1):
            self.link_options(options[idx], options[idx + 1], direction=Direction.down, reverse=True)


class ComputerAction(Enum):
    deposit = 0
    withdraw = 1
    move_pokemon = 2
    move_items = 3
    see_ya = 4


class ComputerActionSelector(SelectorDisplay):
    def __init__(self, scale=1.0):
        selector_img_path = os.path.join(MODULE_PATH, "assets/selector_arrow.png")
        container_img_path = os.path.join(MODULE_PATH, "assets/containers/computer_action_selector.png")

        options = list(ComputerAction)
        SelectorDisplay.__init__(
            self,
            container_img_path,
            selector_img_path,
            scale=scale,
            options=options,
            option_positions=[(8, 10), (8, 26), (8, 42), (8, 58), (8, 74)],
            display_posistion=pg.Vector2(2, 2),
        )

        # define node links here
        for idx in range(len(options) - 1):
            self.link_options(options[idx], options[idx + 1], direction=Direction.down, reverse=True)