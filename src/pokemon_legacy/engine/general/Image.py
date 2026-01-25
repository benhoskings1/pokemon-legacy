import numpy as np
import pygame as pg


class Image:
    def __init__(self, image: pg.Surface):
        self.baseSurface = image
        self.size = pg.Vector2(image.get_size())
        self.surface = self.baseSurface.copy()

    def scale(self, scale: pg.Vector2):
        size = pg.Vector2(self.baseSurface.get_size())
        self.size = pg.Vector2(size.x * scale.x, size.y * scale.y)
        self.surface = pg.transform.scale(self.baseSurface, self.size)

        return self.surface

    def replaceWithWhite(self):

        pixels = pg.surfarray.pixels3d(self.surface)

        for layer in range(3):
            array = np.array(pixels[:, :, layer])
            for row in range(pixels.shape[0]):
                for col in range(pixels.shape[1]):
                    value = array[row, col]

                    if all(value != [0, 0, 0]):
                        pixels[row, col, :] = [255, 255, 255]

        newImage = pg.surfarray.make_surface(pixels)
        newImage.set_colorkey(pg.Color(0, 0, 0))
        self.surface = newImage
        return self.surface


# image = Image(pg.image.load(
#     "/Users/benhoskings/Documents/Coding/Pokemon/Sprites/Pokemon/Gen IV/chimchar_front.png"))
#
# image.replaceWithWhite()
