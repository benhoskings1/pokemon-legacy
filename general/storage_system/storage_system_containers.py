import os
import importlib.resources as resources
from enum import Enum
import time

import pygame as pg
import pandas as pd

import graphics.engine as engine
from general.Selector import Selector
from general.direction import Direction
from graphics.screen_V2 import BlitLocation
from graphics.sprite_screen import DisplayContainer
from graphics.selector_display import SelectorDisplay

from trainer import Player2

MODULE_PATH = resources.files(__package__)
ENGINE_PATH = resources.files(engine)

class StorageSystemContainer(SelectorDisplay):
    def __init__(self):
        selector_image = ENGINE_PATH / "assets" / "hand_picker" / "frame_1.png"
        container_image = MODULE_PATH / "assets" / "hand_picker"

        SelectorDisplay.__init__(
            self,
            selector_image,
            container_image
        )