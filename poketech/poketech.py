import datetime
from enum import Enum

import pygame as pg

from font.font import ClockFont
from graphics.screen_V2 import BlitLocation
from graphics.sprite_screen import SpriteScreen

from team import Team
from pokemon import Pokemon

largeClockFont = ClockFont(1.85)
smallClockFont = ClockFont(0.8)


class PoketechButton(pg.sprite.Sprite):
    def __init__(self, scale=1.0):
        pg.sprite.Sprite.__init__(self)

        self.sprite_type = "PoketechButton"

        self.id = "poketech_button"

        self.image = pg.image.load('poketech/assets/button.png')

        if scale != 1.0:
            self.image = pg.transform.scale(self.image, pg.Vector2(self.image.get_size()) * scale)

        self.rect = self.image.get_rect()
        self.rect = self.rect.move(pg.Vector2(217, 86) * scale)

    @staticmethod
    def click_return(self):
        return None

    def is_clicked(self, pos):
        if self.rect.collidepoint(pos):
            return True
        else:
            return False


class PoketechScreens(Enum):
    clock = 0
    pedometer = 1
    team = 2


class ClockDisplay(SpriteScreen):
    def __init__(self, size, scale=1):
        SpriteScreen.__init__(self, size)
        self.load_image("poketech/assets/clock_background.png", base=True, scale=scale)

        self.set_time = datetime.datetime.now()

        surf = largeClockFont.render_text(self.set_time.strftime("%H:%M"))
        self.add_image(surf, pos=(int(4 * 15 / 8), int(36 * 15 / 8)))

    def update(self):
        ...

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
    def __init__(self, size, scale: float = 1.0):
        SpriteScreen.__init__(self, size)
        self.load_image("poketech/assets/pedometer_background.png", base=True, scale=scale)

        self.reset_button = ...

        self.scale = scale

    def update(self, steps):
        self.refresh()
        surf = smallClockFont.render_text(str(steps))
        self.add_image(surf, pos=pg.Vector2(96, 48)*self.scale, location=BlitLocation.centre)


class TeamDisplay(SpriteScreen):
    PK_POSITIONS = [
        (47, 28), (142, 28), (47, 81), (142, 81), (47, 129), (142, 129)
    ]

    hp_outline = pg.image.load('poketech/assets/hp_outline.png')
    hp_infill = pg.image.load('poketech/assets/hp_infill.png')

    def __init__(self, size, team: Team, scale: float = 1.0):
        SpriteScreen.__init__(self, size)
        self.load_image("poketech/assets/blank_background.png", base=True, scale=scale)

        self.team = team
        self.scale = scale

        if scale != 1.0:
            self.hp_outline = pg.transform.scale(self.hp_outline, pg.Vector2(self.hp_outline.get_size()) * scale)
            self.hp_infill = pg.transform.scale(self.hp_infill, pg.Vector2(self.hp_infill.get_size()) * scale)

        self.outline_offset = pg.Vector2(-33, 26)
        self.infill_offset = self.outline_offset + pg.Vector2(2, 2)

        self.update()


    def scale_hp_rect(self, pk):
        new_size = pg.Vector2(self.hp_infill.get_size())
        new_size.x *= pk.health_ratio
        return pg.transform.scale(self.hp_infill, new_size)

    def update(self):
        self.refresh()
        for idx, pk in enumerate(self.team):
            pk: Pokemon
            grey_image = pg.transform.grayscale(pk.smallImage)
            grey_image = pg.transform.scale_by(grey_image, self.scale)
            grey_image.set_alpha(150)
            self.add_image(self.hp_outline,
                           (pg.Vector2(self.PK_POSITIONS[idx]) + self.outline_offset) * self.scale,
                           location=BlitLocation.topLeft)

            self.add_image(self.scale_hp_rect(pk),
                           (pg.Vector2(self.PK_POSITIONS[idx]) + self.infill_offset) * self.scale,
                           location=BlitLocation.topLeft)
            self.add_image(grey_image,
                           pg.Vector2(self.PK_POSITIONS[idx]) * self.scale,
                           location=BlitLocation.centre)


class Poketech(SpriteScreen):
    def __init__(self, size, time, team, scale=1):
        SpriteScreen.__init__(self, size)
        self.load_image("poketech/assets/poketech_base.png", base=True, scale=scale)

        self._active_display = PoketechScreens.clock

        self.displays: None | dict = None

        self.time = time
        self.scale = scale

        self.button = None

        self.team = team

        self.pedometerSteps = 0
        self.pedometerReset = pg.Rect((int(66 * 15 / 8), int(81 * 15 / 8)), (int(66 * 15 / 8), int(58 * 15 / 8)))
        self.pedometerReset.topleft += pg.Vector2(int(16 * 15 / 8), int(16 * 15 / 8))

        self.buttonRect = pg.Rect((434, 159), (66, 169))

        self.app_offest = pg.Vector2(16, 16) * self.scale
        self.app_rect = pg.Rect(self.app_offest, pg.Vector2(192, 160) * self.scale)

        self._load_surfaces()

    def __getstate__(self):
        self.font, self.fonts = None, None
        self._clear_surfaces()

        return self.__dict__

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._load_surfaces()

    def cycle_screens(self, window, duration=800, frames=50):
        def get_coverage_ratio(frame, frame_count):
            if frame < frame_count / 2:
                return frame / (frame_count / 2)
            else:
                return (frame_count - frame) / (frame_count / 2)

        # delay per frame in milliseconds
        delay = duration / frames

        for frame in range(frames):
            coverage_ratio = get_coverage_ratio(frame, frames)
            rect_height = round((self.size.y / 2) * coverage_ratio)

            top_rect = pg.Rect(self.app_offest, (self.app_rect.w, rect_height))
            bottom_rect = pg.Rect((self.app_rect.left, self.app_rect.bottom - rect_height), (self.app_rect.w, rect_height))

            pg.draw.rect(self.sprite_surface, pg.Color(49, 49, 49), top_rect)
            pg.draw.rect(self.sprite_surface, pg.Color(49, 49, 49), bottom_rect)

            window.blit(self.get_surface(), (0, 0))
            pg.display.flip()
            pg.time.delay(round(delay))
            self.refresh()

            if frame == frames / 2:
                self._active_display = PoketechScreens((self._active_display.value + 1) % len(PoketechScreens))
                self.update_pedometer()


    def get_surface(self, show_sprites: bool = True, offset: None | pg.Vector2 = None):
        if show_sprites:
            self.sprites.draw(self)

        display_surf = self.base_surface.copy()
        display_surf.blit(self.surface, (0, 0))

        display_surf.blit(self.displays[self._active_display].get_surface(), self.app_offest)

        display_surf.blit(self.sprite_surface, (0, 0))

        return display_surf

    def update_pedometer(self):
        if self._active_display != PoketechScreens.pedometer:
            return
        self.displays[PoketechScreens.pedometer].update(self.pedometerSteps)

    def _clear_surfaces(self):
        self.displays = None

        self.button = None

        self.base_surface = None
        self.surface = None
        self.sprite_surface = None
        self.power_off_surface = None

    def _load_surfaces(self):
        # sprite screen init
        self.base_surface = pg.Surface(self.size, pg.SRCALPHA)
        self.surface = pg.Surface(self.size, pg.SRCALPHA)
        self.sprite_surface = pg.Surface(self.size, pg.SRCALPHA)

        self.load_image("poketech/assets/poketech_base.png", base=True, scale=self.scale)

        # poketech init
        self.displays = {
            PoketechScreens.clock: ClockDisplay(self.app_rect.size, self.scale),
            PoketechScreens.pedometer: PedometerDisplay(self.app_rect.size, self.scale),
            PoketechScreens.team: TeamDisplay(self.app_rect.size, self.team, scale=self.scale),
        }

        self.button = PoketechButton(scale=self.scale)
