import os

import numpy as np
import pandas as pd
from PIL import Image

from Image_Processing.ImageEditor import ImageEditor

from pokemon_module.pokemon import Pokemon


attributes = pd.read_csv("game_data/pokedex/AttributeDex.tsv", delimiter='\t', index_col=1)
editor = ImageEditor()


def create_animation(name):
    attributeData = attributes.loc[name]

    folderPath = os.path.join("Sprites/Pokemon/Gen IV", name.title())
    if os.path.isdir(folderPath):
        if not attributeData.Female_Form:
            frontPath = os.path.join(folderPath, "Front.gif")
            frontShinyPath = os.path.join(folderPath, "Front_Shiny.gif")
        else:
            frontPath = os.path.join(folderPath, "Front_Male.gif")
            frontShinyPath = os.path.join(folderPath, "Front_Shiny_Male.gif")

        small_path = os.path.join(folderPath, "Small.gif")

        front_animation = getImageAnimation(frontPath)

        small_animation = getImageAnimation(small_path)

        return Animations(front=front_animation, small=small_animation)

    return None


def getImageAnimation(path):
    imageAnimation = Image.open(path)
    animation = []
    for frame in range(imageAnimation.n_frames):
        imageAnimation.seek(frame)
        imageData = np.asarray(imageAnimation.convert("RGBA"))
        editor.loadData(imageData)
        editor.crop_transparent_borders(overwrite=True)
        editor.scaleImage((2, 2), overwrite=True)
        surf = editor.createSurface(bgr=False)
        animation.append(surf)

    return animation


class Animations:
    def __init__(self, front=None, frontShiny=None, small=None):
        self.front = front
        self.frontShiny = frontShiny
        self.small = small


class PokemonGenerator:
    def __init__(self):
        self._animations: dict[str, Animations] = {}

    def generate_pokemon(self, pokemon_name):
        if pokemon_name not in self._animations:
            self._animations[pokemon_name] = create_animation(pokemon_name)

        return Pokemon(pokemon_name, 10, animations=self._animations[pokemon_name])