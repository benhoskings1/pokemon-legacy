import datetime
from enum import Enum

import pygame as pg

from font.font import ClockFont
from pokemon import smallSprites
from screen_V2 import Screen, BlitLocation
from sprite_screen import SpriteScreen

from general.utils import clean_surfaces

largeClockFont = ClockFont(1.85)
smallClockFont = ClockFont(0.8)


class PoketechScreens(Enum):
    clock = 0
    pedometer = 1


class ClockDisplay(SpriteScreen):
    def __init__(self, size, scale=1):
        SpriteScreen.__init__(self, size)
        self.load_image("poketech/assets/clock_background.png", base=True, scale=scale)

        self.set_time = datetime.datetime.now()

        surf = largeClockFont.render_text(self.set_time.strftime("%H:%M"))
        self.add_image(surf, pos=(int(4 * 15 / 8), int(36 * 15 / 8)))

    def get_surface(self, show_sprites: bool = True, offset: None | pg.Vector2 = None):
        current_time = datetime.datetime.now()
        if current_time.minute != self.set_time.minute:
            self.refresh()
            surf = largeClockFont.render_text(current_time.strftime("%H:%M"))
            self.add_image(surf, pos=(int(4 * 15 / 8), int(36 * 15 / 8)))

        if show_sprites:
            self.sprites.draw(self)

        display_surf = self.base_surface.copy()
        display_surf.blit(self.surface, (0, 0))
        display_surf.blit(self.sprite_surface, (0, 0))

        return display_surf


class PedometerDisplay(SpriteScreen):
    def __init__(self, size, scale=1):
        SpriteScreen.__init__(self, size)
        self.load_image("poketech/assets/pedometer_background.png", base=True, scale=scale)

        self.reset_button = ...

    def update(self, steps):
        self.refresh()
        surf = smallClockFont.render_text(str(steps))
        self.add_image(surf, pos=(int(96 * 15 / 8), int(48 * 15 / 8)), location=BlitLocation.centre)


class Poketech(SpriteScreen):
    def __init__(self, size, time, scale=1):
        SpriteScreen.__init__(self, size)
        self.load_image("poketech/assets/Poketech Base.png", base=True, scale=scale)

        self.active_display = PoketechScreens.clock

        self.displays = {
            PoketechScreens.clock: ClockDisplay(size, scale),
            PoketechScreens.pedometer: PedometerDisplay(size, scale),
        }

        self.time = time

        self.pedometerSteps = 0
        self.pedometerReset = pg.Rect((int(66 * 15 / 8), int(81 * 15 / 8)), (int(66 * 15 / 8), int(58 * 15 / 8)))
        self.pedometerReset.topleft += pg.Vector2(int(16 * 15 / 8), int(16 * 15 / 8))

        self.buttonRect = pg.Rect((434, 159), (66, 169))

        self.scale = scale

    def __getstate__(self):
        self.font, self.fonts = None, None
        print("[__getstate__] Cleaning surfaces before pickling...")
        self.displays = None

        self.base_surface = None
        self.surface = None
        self.sprite_surface = None
        self.power_off_surface = None

        return self.__dict__

    def __setstate__(self, state):
        self.__dict__.update(state)

        self.base_surface = pg.Surface(self.size, pg.SRCALPHA)
        self.surface = pg.Surface(self.size, pg.SRCALPHA)
        self.sprite_surface = pg.Surface(self.size, pg.SRCALPHA)

        self.load_image("poketech/assets/Poketech Base.png", base=True, scale=self.scale)

    def get_surface(self, show_sprites: bool = True, offset: None | pg.Vector2 = None):
        if show_sprites:
            self.sprites.draw(self)

        display_surf = self.base_surface.copy()
        display_surf.blit(self.surface, (0, 0))
        display_surf.blit(self.sprite_surface, (0, 0))

        display_surf.blit(self.displays[self.active_display].get_surface(), pg.Vector2(16, 16)*self.scale)

        return display_surf

    def update_pedometer(self):
        ...


    def clear_surfaces(self):
        print("surfaced cleared")
        self.displays = None

        self.base_surface = None
        self.surface = None
        self.sprite_surface = None
        self.power_off_surface = None

    def load_surfaces(self):
        self.displays = {
            PoketechScreens.clock: ClockDisplay(self.size, self.scale),
            PoketechScreens.pedometer: PedometerDisplay(self.size, self.scale),
        }


