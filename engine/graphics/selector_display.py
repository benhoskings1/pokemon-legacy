from enum import Enum
import importlib.resources as resources

import pygame as pg

from engine.graphics.sprite_screen import DisplayContainer
from engine.graphics.engine.option_selector import OptionSelector
from engine.general.direction import Direction


MODULE_PATH = resources.files(__package__)


class SelectorDisplay(DisplayContainer):
    def __init__(
            self,
            display_image_path: str,
            selector_image_path: str,
            options: list | Enum,
            option_positions: list,
            display_position: pg.Vector2 = pg.Vector2(0, 0),
            *,
            scale: int | float | tuple[int, int] | list[int] | pg.Vector2 = 1.0
    ):
        """
        Initialise the selector display.

        :param display_image_path: path to the base image of the display
        :param selector_image_path: path to the selector image
        :param options: list of options within the display
        :param option_positions: positions of each of the options
        
        """
        DisplayContainer.__init__(self, display_image_path, sprite_id=0, pos=display_position, scale=scale)

        self.selector = OptionSelector(
            selector_image_path,
            options,
            positions=option_positions,
            scale=self.scale
        )
        self.sprites.add(self.selector)

    @property
    def selected(self):
        return self.selector.selected

    def process_interaction(
            self,
            direction: Direction,
            selector: None | OptionSelector = None
    ):
        self.refresh()
        selector = selector or self.selector

        selector.process_interaction(direction)

    def link_options(
            self,
            option_1,
            option_2,
            direction: Direction,
            reverse=True
    ):
        self.selector.link_options(option_1, option_2, direction, reverse)

    def reset(self):
        self.refresh()
        self.selector.reset()