import os
from enum import Enum
import importlib.resources as resources

import pygame as pg

from graphics.sprite_screen import DisplayContainer
from graphics.engine.option_selector import OptionSelector
from general.direction import Direction


MODULE_PATH = resources.files(__package__)


class SelectorDisplay(DisplayContainer):
    def __init__(
            self,
            display_image,
            selector_image,
            options: list | Enum,
            positions: list,
            pos: pg.Vector2,
            scale=1.0
    ):
        DisplayContainer.__init__(self, display_image, sprite_id=0, pos=pos, scale=scale)

        self.selector = OptionSelector(
            selector_image,
            options,
            positions=positions,
            scale=self.scale
        )
        self.sprites.add(self.selector)

    @property
    def selected(self):
        return self.selector.selected

    def process_interaction(self, direction: Direction):
        self.refresh()
        self.selector.process_interaction(direction)

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