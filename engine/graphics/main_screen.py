import pygame as pg

from engine.graphics.sprite_screen import SpriteScreen
from engine.graphics.text_box import TextBox


class MainScreen(SpriteScreen):
    def __init__(
            self,
            size: tuple[int, int] | list[int] | pg.Vector2,
            scale = 1.0
    ):
        SpriteScreen.__init__(self, size)

        self.text_box = TextBox(sprite_id="text_box", scale=scale, static=True)
        self.text_box.rect.topleft += pg.Vector2(3, 0) * scale

    def update_display_text(self, text, max_chars=None):
        if self.text_box not in self.sprites:
            self.sprites.add(self.text_box)

        self.text_box.refresh()

        text_rect = pg.Rect(pg.Vector2(12, 8) * self.text_box.scale, pg.Vector2(221, 34) * self.text_box.scale)
        self.text_box.add_text_2(text, text_rect, max_chars=max_chars)
        self.text_box.update_image()

    def display_message(
            self,
            text,
            window,
            *,
            speed: int | float = 1.0,
            keep_textbox: bool =False,
            offset: None = None,
    ):
        for char_idx in range(1, len(text) + 1):
            self.update_display_text(text, max_chars=char_idx)
            window.blit(self.get_surface(offset=offset), (0, 0))
            pg.display.flip()
            # 20 ms per character
            pg.time.delay(int(40 / speed))

        if not keep_textbox:
            self.sprites.remove(self.text_box)