import os

import numpy as np
import pandas as pd
from PIL import Image

from Image_Processing.ImageEditor import ImageEditor

pokedex = pd.read_csv("game_data/pokedex/Local Dex.tsv", delimiter='\t', index_col=1)
attributes = pd.read_csv("game_data/pokedex/AttributeDex.tsv", delimiter='\t', index_col=1)
editor = ImageEditor()


def createAnimation(name):
    attributeData = attributes.loc[name]

    folderPath = os.path.join("Sprites/Pokemon/Gen IV", name.title())
    if os.path.isdir(folderPath):
        if not attributeData.Female_Form:
            frontPath = os.path.join(folderPath, "Front.gif")
            frontShinyPath = os.path.join(folderPath, "Front_Shiny.gif")
        else:
            frontPath = os.path.join(folderPath, "Front_Male.gif")
            frontShinyPath = os.path.join(folderPath, "Front_Shiny_Male.gif")

        smallPath = os.path.join(folderPath, "Small.gif")

        frontAnimation = getImageAnimation(frontPath)

        smallAnimation = getImageAnimation(smallPath)

        return Animations(front=frontAnimation, small=smallAnimation)

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


class PokemonAnimations:
    def __init__(self, limit):
        self.animations = {}

        for idx, name in enumerate(pokedex.index):
            if idx < limit:
                pkAnimations = createAnimation(name)
                self.animations[name] = pkAnimations
                print(name)

