import os
import re

from enum import Enum
from PIL import Image

import pickle
import pandas as pd
import numpy as np
import pygame as pg
from enum import Enum

# from pokemon import pokedex
from Image_Processing.ImageEditor import ImageEditor


def clean_surfaces(obj, _path='root'):
    if isinstance(obj, pg.Surface):
        print(f"[clean_surfaces] Replacing Surface at: {_path}")
        return None
    elif isinstance(obj, Enum):
        return obj  # ✅ Skip Enums
    elif isinstance(obj, dict):
        return {
            k: clean_surfaces(v, f"{_path}.{k}")
            for k, v in obj.items()
        }
    elif isinstance(obj, list):
        return [
            clean_surfaces(v, f"{_path}[{i}]")
            for i, v in enumerate(obj)
        ]
    elif hasattr(obj, '__dict__'):
        cls = obj.__class__
        try:
            new_obj = cls.__new__(cls)
        except TypeError:
            print(f"[clean_surfaces] WARNING: Could not create instance of {cls} at {_path}. Leaving as-is.")
            return obj
        for attr, val in vars(obj).items():
            cleaned_val = clean_surfaces(val, f"{_path}.{attr}")
            setattr(new_obj, attr, cleaned_val)
        return new_obj
    else:
        return obj


# with open("game_data/pokedex/LocalDex/LocalDex.pickle", 'rb') as file:
#     pokedex: pd.DataFrame = pickle.load(file)

editor = ImageEditor()


def create_display_bar(val: float, max_val: float, bar_type: str) -> pg.Surface:
    """
    This function creates the display bar used for health and exp displays within the game screen.

    :param val: current value of health/exp
    :param max_val: maximum value of health/exp
    :param bar_type: health or exp
    :return: pygame surface that is coloured and truncated relative to the maximum value
    """
    ratio = val / max_val

    if bar_type == "HP":
        if ratio > 0.5:
            colour = "high"
        elif ratio > 0.25:
            colour = "medium"
        else:
            colour = "low"
        bar_surf = pg.image.load(f"assets/battle/main_display/health_bar/health_{colour}.png")
    else:
        bar_surf = pg.image.load("assets/battle/touch_display/pokemon/exp_bar.png")
        bar_surf.set_alpha(100)

    bar_size = pg.Vector2(bar_surf.get_size())

    return pg.transform.scale(bar_surf, pg.Vector2((48 if bar_type == "HP" else 64) * ratio, bar_size.y))


def load_gif(gif_path: str, bit_mask=None, opacity=255, scale=1) -> list[pg.Surface]:
    """
    This function loads a gif and returns a list of pygame surfaces.
    :param gif_path: path of the gif file
    :return: animation representing the frames of the gif
    """
    frames = []
    gif_image = Image.open(gif_path)
    for frame in range(gif_image.n_frames):
        gif_image.seek(frame)
        img = gif_image.copy()
        if scale != 1:
            img = img.resize((int(img.size[0] * scale), int(img.size[1] * scale)))

        image_data = np.asarray(img.convert("RGBA")).copy()
        if bit_mask is not None:
            image_data = image_data[:bit_mask.shape[0], :bit_mask.shape[1]]
            image_data[:, :, 3] = bit_mask

        editor.loadData(image_data)
        surf = editor.createSurface(bgr=False)
        if opacity != 255:
            surf.set_alpha(opacity)

        frames.append(surf)

    return frames


def get_image_frame(file_name):
    """ Extracts the number of the frame string using regex """
    match = re.search(r".*_(\d+).png", file_name)
    if match:
        return int(match.group(1))
    else:
        return None


class Colours(Enum):
    clear = pg.SRCALPHA
    white = pg.Color(255, 255, 255)
    black = pg.Color(1, 1, 1)
    darkGrey = pg.Color(60, 60, 60)
    midGrey = pg.Color(150, 150, 150)
    lightGrey = pg.Color(200, 200, 200)
    green = pg.Color(69, 181, 67)
    red = pg.Color(181, 67, 67)
    shadow = pg.Color(180, 180, 180)
    blue = pg.Color(67, 113, 181)
    yellow = pg.Color(252, 198, 3)
    hero_blue = pg.Color("#274251")
    light_blue = pg.Color("#4f86a5")


class BlitLocation(Enum):
    topLeft = pg.Vector2(0, 0)
    midTop = pg.Vector2(-0.5, 0)
    topRight = pg.Vector2(-1, 0)
    bottomLeft = pg.Vector2(0, -1)
    midBottom = pg.Vector2(-0.5, 1)
    bottomRight = pg.Vector2(-1, -1)
    midLeft = pg.Vector2(0, -0.5)
    midRight = pg.Vector2(-1, -0.5)
    centre = pg.Vector2(-0.5, -0.5)
