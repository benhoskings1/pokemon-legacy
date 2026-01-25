from enum import Enum

import pygame as pg
from pokemon_legacy.engine.graphics.font.font import Font, FontType

from pokemon_legacy.engine.general.utils import BlitLocation, Colours


# class Colours(Enum):
#     clear = pg.SRCALPHA
#     white = pg.Color(255, 255, 255)
#     black = pg.Color(1, 1, 1)
#     darkGrey = pg.Color(60, 60, 60)
#     midGrey = pg.Color(150, 150, 150)
#     lightGrey = pg.Color(200, 200, 200)
#     green = pg.Color(69, 181, 67)
#     red = pg.Color(181, 67, 67)
#     shadow = pg.Color(180, 180, 180)
#     blue = pg.Color(67, 113, 181)
#     yellow = pg.Color(252, 198, 3)
#     hero_blue = pg.Color("#274251")
#     light_blue = pg.Color("#4f86a5")


class BlitPosition(Enum):
    topLeft = 0
    midTop = 1
    topRight = 2
    bottomLeft = 3
    midBottom = 4
    bottomRight = 5
    midLeft = 6
    midRight = 7
    centre = 8


fonts = {
    "regular": Font(2, font_type=FontType.regular),
    "level": Font(2, font_type=FontType.level)
}


class FontOption(Enum):
    main = fonts["regular"]
    level = fonts["level"]


class Screen:
    def __init__(self, size, font=None, colour=None):
        self.size = pg.Vector2(size)
        self.base_surface = pg.Surface(size, pg.SRCALPHA)
        self.surface = pg.Surface(size, pg.SRCALPHA)
        self.sprite_surface = pg.Surface(size, pg.SRCALPHA)

        self.fonts = FontOption
        self.font: pg.font.Font = font if font else self.fonts.main

        if colour:
            colour = colour.value if not isinstance(colour, pg.Color) else colour
            self.base_surface.fill(colour)

        self.colour = colour

        self.power_off = False

        self.power_off_surface = pg.Surface((self.size.x, self.size.y), pg.SRCALPHA)
        self.power_off_surface.fill(Colours.white.value)

    def __getstate__(self):
        # self.font, self.fonts = None, None
        print("[__getstate__] Cleaning surfaces before pickling...")
        # return clean_surfaces(self)
        return None

    def add_surf(self, surf: pg.Surface, pos=(0, 0), base=False, location=BlitLocation.topLeft, sprite=False):
        surf_rect = pg.Rect(pos, surf.get_size())

        if location == BlitLocation.centre:
            surf_rect.topleft -= pg.Vector2(surf_rect.size) / 2
        elif location == BlitLocation.topRight:
            surf_rect.x -= surf_rect.width
        elif location == BlitLocation.bottomLeft:
            surf_rect.y -= surf_rect.height
        elif location == BlitLocation.midBottom:
            surf_rect.y -= surf_rect.height
            surf_rect.x -= surf_rect.width / 2

        if sprite:
            self.sprite_surface.blit(surf, surf_rect.topleft)
        elif base:
            self.base_surface.blit(surf, surf_rect.topleft)
        else:
            self.surface.blit(surf, surf_rect.topleft)

    def load_image(self, path, pos=(0, 0), fill=False, base=False, size=None,
                   scale: float | int | list[int] | tuple[int, int] | pg.Vector2 = None,
                   location=BlitLocation.topLeft):

        if isinstance(scale, float) or isinstance(scale, int):
            scale = (scale, scale)

        image = pg.image.load(path)

        if size:
            image = pg.transform.scale(image, size)
        elif scale:
            image = pg.transform.scale(image, (image.get_size()[0] * scale[0], image.get_size()[1] * scale[1]))
        elif fill:
            image = pg.transform.scale(image, self.size)

        imageRect = pg.Rect(pos, image.get_size())

        if location == BlitLocation.centre:
            imageRect.topleft = pg.Vector2(imageRect.topleft) - pg.Vector2(imageRect.size) / 2
        elif location == BlitLocation.topRight:
            imageRect.x -= imageRect.width
        elif location == BlitLocation.midBottom:
            imageRect.topleft -= pg.Vector2(imageRect.width / 2, imageRect.height)

        if base:
            self.base_surface.blit(image, imageRect.topleft)
        else:
            self.surface.blit(image, imageRect.topleft)

        return imageRect

    def add_image(self, image, pos=pg.Vector2(0, 0), fill=False, scale=None, size=None, location=BlitLocation.topLeft,
                  base=False):
        if isinstance(scale, float) or isinstance(scale, int):
            scale = (scale, scale)

        if base:
            surf = self.base_surface
        else:
            surf = self.surface

        if size:
            image = pg.transform.scale(image, size)
        elif scale:
            image = pg.transform.scale(image, (image.get_size()[0] * scale[0], image.get_size()[1] * scale[0]))
        elif fill:
            image = pg.transform.scale(image, self.size)

        size = pg.Vector2(image.get_size())
        if location == BlitLocation.centre:
            surf.blit(image, pos - size / 2)
        elif location == BlitLocation.midBottom:
            newPos = pg.Vector2(pos.x - (size.x / 2), pos.y - size.y)
            surf.blit(image, newPos)
        elif location == BlitLocation.midTop:
            new_pos = pg.Vector2(pos.x - (size.x / 2), pos.y)
            surf.blit(image, new_pos)
        else:
            surf.blit(image, pos)

    def add_text_2(self, text: str, text_box: pg.Rect, font_option: FontOption = FontOption.main,
                   colour: Colours | pg.Color = None, shadow_colour: Colours | pg.Color = None,
                   max_chars=None, sep=1, vsep=1.5, base=False) -> None | bool:

        if len(text) == 0:
            return False

        self.font = font_option.value
        text_surf, text_box = self.font.render_text_2(
            text, text_box, colour=colour, shadow_colour=shadow_colour, max_chars=max_chars, sep=sep, vsep=vsep
        )

        blit_surf = self.base_surface if base else self.surface
        blit_surf.blit(text_surf, text_box.topleft)

    def addText(self, text, pos, lines=1, location=BlitLocation.topLeft, base=False, colour=None,
                shadowColour=None, fontOption: FontOption = FontOption.main, surface=None,):

        if len(text) == 0:
            return False

        self.font = fontOption.value

        if colour:
            if shadowColour:
                textSurf = self.font.render_text(text, lineCount=lines, colour=colour, shadowColour=shadowColour)
            else:
                textSurf = self.font.render_text(text, lineCount=lines, colour=colour)
        else:
            textSurf = self.font.render_text(text, lineCount=lines,)
        blitPos = pos
        size = pg.Vector2(textSurf.get_size())
        if location == BlitLocation.centre:
            blitPos -= size / 2
        elif location == BlitLocation.topRight:
            blitPos -= pg.Vector2(size.x, 0)
        elif location == BlitLocation.midTop:
            blitPos -= pg.Vector2(size.x / 2, 0)
        elif location == BlitLocation.bottomRight:
            blitPos -= pg.Vector2(size)

        if base:
            self.base_surface.blit(textSurf, blitPos)
        elif surface:
            surface.blit(textSurf, blitPos)
        else:
            self.surface.blit(textSurf, blitPos)

    def update_pixels(self, pos, colour=Colours.black.value, base=False, width=3):
        pad = (width - 1) / 2
        for x_pos in range(int(pos[0] - pad), int(pos[0] + 1 + pad)):
            for y_pos in range(int(pos[1] - pad), int(pos[1] + 1 + pad)):
                if base:
                    self.base_surface.set_at((x_pos, y_pos), colour)
                else:
                    self.surface.set_at((x_pos, y_pos), colour)

    def refresh(self):
        self.surface = pg.Surface(self.size, pg.SRCALPHA)
        self.sprite_surface = pg.Surface(self.size, pg.SRCALPHA)

    def clear_surfaces(self):
        self.surface = None
        self.base_surface = None
        self.font = None

    def get_surface(self):
        display_surf = self.base_surface.copy()
        display_surf.blit(self.surface, (0, 0))
        display_surf.blit(self.sprite_surface, (0, 0))

        return display_surf


class GameButton(pg.sprite.Sprite):
    def __init__(self, position, size, id, text=None, label=None, colour=None):
        super().__init__()
        self.object_type = "button"
        self.rect = pg.Rect(position, size)
        self.id = id
        if colour:
            self.colour = colour.value
        else:
            self.colour = Colours.hero_blue.value
        self.text = text
        self.label = label

    def is_clicked(self, pos):
        if self.rect.collidepoint(pos):
            return True
        else:
            return False

    def click_return(self):
        return self.object_type, self.id


if __name__ == "__main__":
    pg.init()
