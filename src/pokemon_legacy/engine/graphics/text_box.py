import pygame as pg
from pokemon_legacy.engine.graphics.screen_V2 import Screen

from pokemon_legacy.engine.general.image_editor import ImageEditor
from PIL import Image
import numpy as np
import time


class TextBox(pg.sprite.Sprite, Screen):

    editor = ImageEditor()

    def __init__(self, sprite_id, scale, static=False):
        pg.sprite.Sprite.__init__(self)
        self.sprite_type = "text_box"
        self.id = sprite_id
        self.scale = scale

        if static:
            self.frames = [pg.image.load("assets/battle/main_display/text_box_main.png")]
            self.frames = [pg.transform.scale(frame, pg.Vector2(frame.get_size()) * scale) for frame in self.frames]
            self.frame_count = 1
        else:
            imageAnimation = Image.open("assets/battle/main_display/text_box.gif")
            self.frames = []
            self.frame_count = imageAnimation.n_frames
            for frame in range(self.frame_count):
                imageAnimation.seek(frame)
                imageData = np.asarray(imageAnimation.convert("RGBA"))
                self.editor.loadData(imageData)
                surf = self.editor.createSurface(bgr=False)
                surf = pg.transform.scale(surf, pg.Vector2(surf.get_size())*scale)
                self.frames.append(surf)

        Screen.__init__(self, size=self.frames[0].get_size())
        self.image = self.frames[0]

        self.rect = self.image.get_rect()
        self.rect.topleft = pg.Vector2(0, 144) * scale

        self.frame_idx = 0
        self.frame_update = time.monotonic()

    def update_image(self):
        now = time.monotonic()
        if now - self.frame_update > 0.8:
            self.frame_update = now
            self.frame_idx = (self.frame_idx + 1) % self.frame_count

        self.image = self.frames[self.frame_idx].copy()
        self.image.blit(self.get_surface(), (0, 0))