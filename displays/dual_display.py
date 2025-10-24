from graphics.sprite_screen import SpriteScreen


class DualDisplay:
    def __init__(self, size):
        self.main_display = SpriteScreen(size)
        self.touch_display = SpriteScreen(size)

