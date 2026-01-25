import os
import re
import importlib.resources as resources
from enum import Enum
from math import floor, ceil

import numpy as np
import pygame as pg

from pokemon_legacy.engine.general.utils import Colours

MODULE_PATH = resources.files(__package__)

class FontType(Enum):
    regular = 0
    level = 1
    clock = 2


class CharacterType(Enum):
    baseline = 0
    descender = 1
    ascender = 2


class Baseline(Enum):
    centre = 0
    lower = 1


FONT_CHARACTER_SIZES = {
    "a": (6, 7),  "b": (6, 10), "c": (6, 7),  "d": (6, 10), "e": (6, 7),
    "f": (4, 10), "g": (6, 9),  "h": (6, 10), "i": (2, 9),  "j": (4, 11),
    "k": (6, 10), "l": (3, 10), "m": (6, 7),  "n": (6, 7),  "o": (6, 7),
    "p": (6, 9),  "q": (6, 9),  "r": (6, 7),  "s": (6, 7),  "t": (5, 8),
    "u": (6, 7),  "v": (6, 7),  "w": (6, 7),  "x": (6, 7),  "y": (6, 9),
    "z": (6, 7),  "0": (6, 10), "1": (4, 10), "2": (6, 10), "3": (6, 10),
    "4": (6, 10), "5": (6, 10), "6": (6, 10), "7": (6, 10), "8": (6, 10),
    "9": (6, 10), "/": (6, 10), "?": (6, 11), "!": (2, 11), "'": (3, 11),
    "-": (6, 10), " ": (4, 10), ".": (4, 10), "é": (6, 10), ",": (6, 10),
    "$": (6, 12)
}

FONT_CHARACTER_SIZES.update({k.upper(): (6, 10) for k in FONT_CHARACTER_SIZES.keys()})


def colour_change(surface, baseColours, shadowColours=None):

    pixels = pg.surfarray.pixels3d(surface)

    for layer in range(3):
        array = np.array(pixels[:, :, layer])
        for row in range(pixels.shape[0]):
            for col in range(pixels.shape[1]):
                value = array[row, col]
                if value == baseColours[0][layer]:
                    pixels[row, col, layer] = baseColours[1][layer]

                if shadowColours:
                    if value == shadowColours[0][layer]:
                        pixels[row, col, layer] = shadowColours[1][layer]

    newImage = pg.surfarray.make_surface(pixels)
    newImage.set_colorkey(pg.Color(0, 0, 0))
    return newImage


class Font:

    custom_image_mapping = {
        "é": "e_accent",
        ",": "comma",
        "$": "dollar"
    }

    baselines = {
        "g": Baseline.lower, "j": Baseline.lower, "p": Baseline.lower,
        "q": Baseline.lower, "y": Baseline.lower, "dollar": Baseline.lower,
    }

    def __init__(self, scale, font_type: FontType = FontType.regular):
        self.scale = scale

        self.space = 1 * scale

        self.letters = {}
        self.sizes = {}

        names = sorted([f for f in os.listdir(os.path.join(MODULE_PATH, font_type.name)) if f.endswith(".png")])

        for name in names:
            if any([re.match(val, name) for val in self.custom_image_mapping.values()]):
                letter = name.split(".")[0]
            elif "Upper" in name:
                letter = str.upper(letter)
            elif "slash" in name:
                letter = "/"
            elif "accent" in name:
                letter = name.split(".")[0]
            else:
                letter = name[0]

            # print(letter)

            image = pg.image.load(os.path.join(MODULE_PATH, f"{font_type.name}/{name}"))
            newImage = pg.transform.scale(image, pg.Vector2(image.get_size()) * scale)
            self.sizes[letter] = newImage.get_size()
            self.letters[letter] = newImage

        self.size = 10

    @staticmethod
    def calculate_text_size(text: str, sep=1, scale=1) -> (list[int], int):
        """ This function takes text in as a string and calculates how much horizontal space is needed."""
        space_count = len(text.split(" ")) - 1
        text = text.replace(".", "")
        word_widths = [(sum([FONT_CHARACTER_SIZES[char][0] for char in word]) + len(word)*sep) * scale for word in text.split(" ")]
        return word_widths, (sum([word_width for word_width in word_widths]) + space_count*3) * scale

    @staticmethod
    def sanitise_characters(text):
        characters = set(text)
        defined_keys = set(FONT_CHARACTER_SIZES.keys())
        replace_dict = {
            unknown: "?" for unknown in characters.difference(defined_keys)
        }

        sanitised = text
        for o_word, n_word in replace_dict.items():
            sanitised = sanitised.replace(o_word, n_word)

        # replace all unknowns
        return sanitised


    def render_text(self, text: str, lineCount=1, colour=None, shadowColour=None) -> pg.Surface:
        words = text.split(" ")
        lines = []
        totalLetters = len("".join(words))
        letters = 0

        for idx, word in enumerate(words):
            lines.append(floor(letters / (totalLetters / lineCount)))
            letters += len(word)

        surfaces = []

        for line in range(lineCount):
            lineWords = []
            for idx, word in enumerate(words):
                if lines[idx] == line:
                    lineWords.append(word)

            lineText = " ".join(lineWords)

            width = 0
            height = 0
            lowerBase = False
            for letter in lineText:
                if letter == " ":
                    width += 3 * self.scale
                else:

                    width += self.sizes[letter][0]
                    letter_baseline = self.baselines.get(letter, Baseline.centre)
                    if self.sizes[letter][1] > height and letter_baseline != Baseline.lower:
                        height = self.sizes[letter][1]

                    if letter_baseline == Baseline.lower:
                        lowerBase = True

            if lowerBase:
                height += 2 * self.scale

            width += self.space * (len(lineText) - 1)

            if width < 0:
                width = 0

            surf = pg.Surface((width, height), pg.SRCALPHA)
            surfSize = pg.Vector2(surf.get_size())

            offset = 0
            for letter in lineText:
                if letter == " ":
                    offset += 3 * self.space
                else:

                    letter = self.custom_image_mapping.get(letter, letter)

                    letter_baseline = self.baselines.get(letter, Baseline.centre)
                    if letter_baseline == Baseline.centre:
                        surf.blit(self.letters[letter], (offset, surfSize.y - self.sizes[letter][1] - 2 * self.scale * lowerBase))
                        offset += self.sizes[letter][0] + self.space
                    else:
                        surf.blit(self.letters[letter], (offset, surfSize.y - self.sizes[letter][1]))
                        offset += self.sizes[letter][0] + self.space

            surfaces.append(surf)

        totalSize = pg.Vector2(0, 0)
        for surface in surfaces:
            size = pg.Vector2(surface.get_size())
            if size.x > totalSize.x:
                totalSize.x = size.x

            totalSize.y += size.y + (lineCount - 1) * self.scale

        textSurf = pg.Surface(totalSize, pg.SRCALPHA)

        heightOffset = 0
        for surface in surfaces:
            textSurf.blit(surface, (0, heightOffset))
            heightOffset += surface.get_size()[1] + 2 * self.scale

        if colour:
            textColours = [pg.Color(16, 24, 32), colour]
            if shadowColour:
                shadowColours = [pg.Color(168, 184, 184), shadowColour]
                textSurf = colour_change(textSurf, textColours, shadowColours=shadowColours)
            else:
                textSurf = colour_change(textSurf, textColours)

        return textSurf

    def render_text_2(self, text: str, text_box: pg.Rect | pg.Vector2 | tuple[int, int],
                      sep=0, vsep=1.5, colour: Colours | pg.Color = None, shadow_colour=None, max_chars=None) -> pg.Surface:
        """
        Renders the given text in the given colour or shadow colour. The max_chars should be used over
        indexing directly into text, since this will maintain the correct line formatting as each
        character for the words is rendered

        :param text: the text to be rendered
        :param text_box: the bounding box of the text to be rendered
        :param sep: the pixels to space each word by
        :param colour: the primary colour of the font
        :param shadow_colour: the secondary colour of the font
        :param max_chars: the maximum number of characters to be rendered.
        :return: pygame surface representing the rendered text
        """
        def blit_word(chars, x, y) -> int:
            for char in chars:
                char = self.custom_image_mapping.get(char, char)

                char_size = self.letters[char].get_size()
                v_offset = base_line - char_size[1]
                if self.baselines.get(char, Baseline.centre) != Baseline.centre:
                    v_offset += 2 * self.scale

                text_surface.blit(self.letters[char], (x, y + v_offset))
                x += char_size[0] + sep * self.scale

                if char == "\n":
                    print("line break")

            return x

        text = self.sanitise_characters(text)

        max_chars = max_chars if max_chars is not None else len(text)

        words = text.split(" ")
        word_widths, total_width = self.calculate_text_size(text, scale=self.scale, sep=sep)

        if isinstance(text_box, pg.Vector2) or len(text_box) == 2:
            # treat two value pairs as x, y coordinates and only render text on one line
            text_box = pg.Rect(text_box, (total_width*self.scale, 11*self.scale))

        lines = ceil(text_box.width / total_width)
        base_line = 11 * self.scale

        # begin creating surface
        text_surface = pg.Surface(text_box.size, pg.SRCALPHA)

        x_pos, y_pos = 0, 0
        char_count = 0
        for word, width in zip(words, word_widths):
            if x_pos + width < text_box.width:
                if char_count + len(word) >= max_chars:
                    blit_word(word[:max_chars-char_count], x_pos, y_pos)
                    break
                else:
                    x_pos = blit_word(word, x_pos, y_pos)
                    char_count += len(word)

                x_pos += self.space * 3

            else:
                y_pos += base_line * vsep
                x_pos = blit_word(word, 0, y_pos)
                x_pos += self.space * 3

        for idx, c in enumerate([colour, shadow_colour]):
            if c is not None:
                if isinstance(c, Colours):
                    c = c.value

                px_array = pg.PixelArray(text_surface)
                px_array.replace(
                    color=pg.Color(16, 24, 32) if idx == 0 else pg.Color(168, 184, 184),
                    repcolor=c
                )

        return text_surface, text_box


class LevelFont:
    def __init__(self, scale):
        self.scale = scale

        self.space = 0

        self.letters = {}
        self.sizes = {}

        names = sorted(os.listdir(os.path.join(MODULE_PATH, "level")))

        for name in names:

            letter = name[0]
            if "slash" in name:
                letter = "/"

            image = pg.image.load(str.format(os.path.join(MODULE_PATH, "level/{}"), name))
            newImage = pg.transform.scale(image, pg.Vector2(image.get_size()) * scale)
            self.sizes[letter] = newImage.get_size()
            self.letters[letter] = newImage

    def render_text(self, text: str, lineCount, colour=None, shadowColour=None):

        width = 0

        for letter in text:
            if letter == " ":
                width += 3 * self.space
            else:

                width += self.sizes[letter][0]

        height = self.sizes["0"][1]
        width += self.space * (len(text) - 1)

        if width < 0:
            width = 0

        surf = pg.Surface((width, height), pg.SRCALPHA)
        surfSize = pg.Vector2(surf.get_size())

        offset = 0
        for letter in text:
            if letter == " ":
                offset += 3 * self.space
            else:
                surf.blit(self.letters[letter], (offset, surfSize.y - self.sizes[letter][1]))
                offset += self.sizes[letter][0] + self.space

        if colour:
            textColours = [pg.Color(16, 24, 32), colour]
            if shadowColour:
                shadowColours = [pg.Color(168, 184, 184), shadowColour]
                textSurf = colour_change(surf, textColours, shadowColours=shadowColours)
            else:
                textSurf = colour_change(surf, textColours)

        return surf


class ClockFont:
    def __init__(self, scale):
        self.scale = scale

        self.space = 1 * scale

        self.letters = {}
        self.sizes = {}

        clock_dir = os.path.join(os.path.dirname(__file__), "Clock")
        names = sorted(os.listdir(clock_dir))

        for name in names:
            letter = name[0]

            if "Colon" in name:
                letter = ":"

            if name.endswith(".png"):
                image = pg.image.load(os.path.join(clock_dir, name))
                newImage = pg.transform.scale(image, pg.Vector2(image.get_size()) * scale)
                self.sizes[letter] = newImage.get_size()
                self.letters[letter] = newImage

    def render_text(self, text: str):
        size = pg.Vector2(0, 0)
        size.y = self.sizes["0"][1]
        for letter in text:
            size.x += self.sizes[letter][0]

        textSurf = pg.Surface(size, pg.SRCALPHA)

        offset = pg.Vector2(0, 0)
        for letter in text:
            textSurf.blit(self.letters[letter], pg.Vector2(0, 0) + offset)
            offset.x += self.sizes[letter][0]

        return textSurf


if __name__ == "__main__":
    test_font = Font(2)