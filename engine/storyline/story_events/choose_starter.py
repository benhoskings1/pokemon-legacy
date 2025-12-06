import importlib.resources as resources

import pygame as pg

from engine.graphics.main_screen import MainScreen
from engine.graphics.selector_display import SelectorDisplay

from engine import pokemon_generator


MODULE_PATH = resources.files(__package__)

class ChooseStarterDisplay(SelectorDisplay, MainScreen):
    def __init__(self, size, scale=1.0):

        starters = [pokemon_generator.generate_pokemon(name, level=5) for name in ("Chimchar", "Turtwig", "Piplup")]

        MainScreen.__init__(self, size)

        SelectorDisplay.__init__(
            self,
            display_image_path=str(MODULE_PATH / "assets" / "choose_starter_base.png"),
            selector_image_path=str(MODULE_PATH / "assets" / "finger_selector.png"),
            options=starters,
            option_positions=[(64, 45), (116, 72), (158, 45)],
            display_position=pg.Vector2(0, 0),
            scale=scale
        )


if __name__ == "__main__":
    pg.init()
    screen_size = pg.Vector2(256, 192) * 2
    pg.display.set_mode(screen_size)

    starter_display = ChooseStarterDisplay(screen_size)
