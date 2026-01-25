import imageio as iio

from ImageEditor import ImageEditor2
images = []

import pygame as pg
pg.display.set_mode((640, 480))

pg.init()

FILENAMES = [f"frames/frame_{idx}.png" for idx in range(5)]
# images = [pg.image.load(file) for file in FILENAMES]

editor = ImageEditor2()
for idx, file in enumerate(FILENAMES):
    editor.load_image(file)
    editor.erase_colour(pg.Color("white"), overwrite=True)
    pg.image.save(editor.image, f"frames/frame_{idx}.png")
#
images = [iio.v3.imread(filename) for filename in FILENAMES]

editor = ImageEditor2()

iio.mimsave('test.gif', images)