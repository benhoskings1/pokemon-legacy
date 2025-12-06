import importlib.resources as resources

import pygame as pg

import engine.graphics.engine as engine
from engine.graphics.sprite_screen import DisplayContainer
from engine.graphics.selector_display import SelectorDisplay

MODULE_PATH = resources.files(__package__)
ENGINE_PATH = resources.files(engine)

class StorageSystemContainer(SelectorDisplay):
    def __init__(self):
        selector_image = ENGINE_PATH / "assets" / "hand_picker" / "frame_1.png"
        container_image = MODULE_PATH / "assets" / "hand_picker"

        SelectorDisplay.__init__(
            self,
            selector_image,
            container_image,
            options=[True],
            option_positions=[(0, 0)],
            display_posistion=pg.Vector2(0, 0)
        )


class PokemonContainer(DisplayContainer):
    def __init__(self, box_idx):
        ...


class StorageBox(DisplayContainer):

    def __init__(self, box_idx):
        file_name = f"box_{box_idx}_main.png"
        container_path = MODULE_PATH / "assets" / "containers" / "boxes" / file_name

        DisplayContainer.__init__(self, container_path, file_name, pos=pg.Vector2(91, 35))

        self.box_idx = box_idx
        self.pokemon = []


