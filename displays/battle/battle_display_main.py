import time
from math import floor

from PIL import Image
import pygame as pg
import numpy as np
from Image_Processing.ImageEditor import ImageEditor

from engine.general.Environment import Environment
from engine.general.utils import Colours, create_display_bar, BlitLocation
from engine.graphics.screen_V2 import Screen, FontOption
from engine.graphics.sprite_screen import SpriteScreen, PokeballCatchAnimation
from engine.pokemon.pokemon import Pokemon

editor = ImageEditor()
STAT_NAMES = ["Max. HP", "Attack", "Defence", "Sp. Atk", "Sp. Def", "Speed"]


class StatContainer(pg.sprite.Sprite, Screen):
    def __init__(self, sprite_id, pokemon: Pokemon, scale=2):
        pg.sprite.Sprite.__init__(self)
        # convention across game to be able to retrieve sprites
        self.id = sprite_id
        self.sprite_type = "stat_container"

        self.pokemon = pokemon
        self.friendly = pokemon.friendly
        self.scale = scale

        image_path = f"assets/battle/main_display/stat_container_{'friendly' if pokemon.friendly else 'foe'}.png"
        self.image = pg.image.load(image_path)

        if scale:
            self.image = pg.transform.scale(self.image, pg.Vector2(self.image.get_size()) * scale)

        self.rect = self.image.get_rect()
        if pokemon.friendly:
            self.rect.topright = pg.Vector2(256, 97) * scale
        else:
            self.rect.topleft = pg.Vector2(0, 21) * scale

        Screen.__init__(self, self.image.get_size())
        self.load_image(image_path, base=True, scale=scale)

        # ======= Add base features =========
        self.add_text_2(self.pokemon.name, pg.Vector2((16, 5) if self.friendly else (5, 5)) * self.scale, base=True)

        self.update()

        self.pos_update = time.monotonic()
        self.pos_offset = 0

    def update(self):
        """ Refresh the information shown on the container """
        self.refresh()

        # pokemon level
        self.addText(f"Lv{self.pokemon.level}", pg.Vector2(70, 8) * self.scale, fontOption=FontOption.level)

        # pokemon health
        hp_bar = create_display_bar(self.pokemon.health, self.pokemon.stats.health, "HP")
        self.add_image(hp_bar, pg.Vector2(62 if self.pokemon.friendly else 50, 20) * self.scale, scale=self.scale)

        if self.pokemon.friendly:
            current_exp = self.pokemon.exp - self.pokemon.level_exp
            max_exp = self.pokemon.level_up_exp - self.pokemon.level_exp

            exp_bar = create_display_bar(current_exp, max_exp, "XP")
            self.add_image(exp_bar, pg.Vector2(30, 38) * self.scale, scale=self.scale)

            self.addText(
                text=f"{floor(self.pokemon.health)}/{self.pokemon.stats.health}",
                pos=pg.Vector2(115, 36) * self.scale,
                location=BlitLocation.bottomRight,
                fontOption=FontOption.level
            )

        self.image = self.get_surface()

    def update_pos(self):
        now = time.monotonic()
        if now - self.pos_update > 0.1:
            self.pos_update = now
            self.pos_offset = (self.pos_offset + 1) % 7
            self.rect.top += self.pos_offset - 3


class TextBox(pg.sprite.Sprite, Screen):
    def __init__(self, sprite_id, scale, static=False):
        pg.sprite.Sprite.__init__(self)
        self.sprite_type = "text_box"
        self.id = sprite_id

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
                editor.loadData(imageData)
                surf = editor.createSurface(bgr=False)
                surf = pg.transform.scale(surf, pg.Vector2(surf.get_size())*scale)
                self.frames.append(surf)

        Screen.__init__(self, size=self.frames[0].get_size())
        # self.base_surface.fill(Colours.black.value)
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


class LevelUpBox(pg.sprite.Sprite, Screen):
    def __init__(self, sprite_id, scale, new_stats, old_stats=None):
        pg.sprite.Sprite.__init__(self)
        self.sprite_type = "text_box"
        self.id = sprite_id

        img = pg.image.load("assets/battle/main_display/level_up.png")
        img = pg.transform.scale(img, pg.Vector2(img.get_size())*scale)

        Screen.__init__(self, size=img.get_size())
        self.add_image(img, (0, 0), base=True)
        self.rect = img.get_rect()
        self.rect.topleft = pg.Vector2(130, 50) * scale

        values = (new_stats - old_stats).get_values() if old_stats else new_stats.get_values()

        for idx, h in enumerate([(9 + idx * 16) * scale for idx in range(6)]):
            self.addText(f"{STAT_NAMES[idx]}", pos=(6 * scale, h))
            if old_stats:
                self.addText(f"+ {values[idx]}", pos=(96 * scale, h))
            else:
                self.addText(f"{values[idx]}", pos=(100 * scale, h))

        self.image = self.get_surface()


class BattleDisplayMain(SpriteScreen):
    def __init__(self, window, size, time, environment: Environment, scale=2):
        """
        This is the menu battle display. The native screen size is 256x192 px
        :param window: The pygame surface to blit the display onto
        :param size: the size of the display
        :param time: the time of day, used to configure the battle background option
        :param environment:
        """
        super().__init__(size, colour=Colours.black)
        self.scale = scale

        self.layer_names = ["background", "stats", "animations", "text"]

        self.screens = {
            name: SpriteScreen(size) for name in self.layer_names
        }

        self.text_box = TextBox(sprite_id="text_box", scale=2)

        self.window = window

        # self.image_scale = pg.Vector2(15 / 8, 15 / 8)

        self.friendly: None | Pokemon = None
        self.foe: None | Pokemon = None

        self.text: None| str = None

        # configure base surfaces for each screen level
        self.screens["background"].load_image(
            f"assets/battle/main_display/backgrounds/{environment.value}_{time.value}.png",
            base=True, scale=pg.Vector2(self.scale, self.scale)
        )

        self.screens["text"].sprites.add(self.text_box)

        self.bounce_friendly_stat = False
        self.friendly_stat_bounce_val = 0

    def add_text(self, text, pos, lines=1, location=BlitLocation.topLeft, base=False, colour=None):
        self.text_box.addText(text, pos, lines, location, base, colour)

        words = text.split()

        for word in words:
            # self.screens["text"].add
            ...

    def update_display_text(self, text, max_chars=None):
        self.text_box.refresh()

        text_rect = pg.Rect(pg.Vector2(10, 4)*self.scale, pg.Vector2(201, 40) * self.scale)
        self.text_box.add_text_2(text, text_rect.inflate(-10, -18), max_chars=max_chars)

    def add_pokemon_sprites(self, pokemon):
        for pk in pokemon:
            self.screens["stats"].sprites.add(pk)

        self.friendly = pokemon[0]
        self.foe = pokemon[1]

        self.screens["stats"].sprites.add([
            StatContainer(sprite_id="friendly_stats", pokemon=self.friendly, scale=self.scale),
            StatContainer(sprite_id="foe_stats", pokemon=self.foe, scale=self.scale)
        ])

    def render_pokemon_details(self, opacity=None, friendly=False, lines=None):
        self.refresh()

        offset = 120 * (1 - (opacity / 255)) if opacity else 0

        # Display options for the wild Pokémon
        if self.foe.visible:
            # add the name of the Pokémon
            self.screens["stats"].get_object("foe_stats").update()

            # if the Pokémon has any status conditions, add display them
            if self.foe.status:
                self.load_image(str.format("Images/Status Labels/{}.png", self.foe.status.name),
                                pg.Vector2(int((10 - offset * (not friendly)) * 15 / 8), int(62 * 15 / 8)),
                                scale=pg.Vector2(2, 2))

        # Display options for the friendly Pokémon
        if self.friendly.visible:
            # draw the health onto the screen
            self.screens["stats"].get_object("friendly_stats").update()

    def intro_animations(self, window: pg.Surface, duration):
        self.render_pokemon_details()
        if self.foe.animation:
            frames = len(self.foe.animation)
            for frame in self.foe.animation:
                self.foe.image = frame
                window.blit(self.get_surface(), (0, 0))
                pg.display.flip()
                pg.time.delay(int(0.75 * duration / frames))
                self.refresh()

            pg.time.delay(int(0.25 * duration))
        else:
            pg.time.delay(duration)

        self.foe.image = self.foe.displayImage
        window.blit(self.get_surface(), (0, 0))
        pg.display.flip()

    def catch_animation(self, duration, checks):
        frames = 100
        timePerFrame = duration / frames
        images = 22

        # the proportion of frames for each of the 21 images!
        frameWeight = [1, 1, 1, 1, 1, 1, 1, 1, 1, 3, 1,
                       1, 1, 1, 1, 3, 1, 1.5, 1, 2, 2, 2]

        imageFrames = []
        for [idx, weight] in enumerate(frameWeight):
            if idx == 0:
                imageFrames.append(frames * (weight / sum(frameWeight)))
            else:
                imageFrames.append(imageFrames[idx - 1] + (frames * (weight / sum(frameWeight))))

        for idx, frameCount in enumerate(imageFrames):
            imageFrames[idx] = floor(frameCount)

        throwFrames = imageFrames[15]
        shakeFrames = imageFrames[19]

        animation = PokeballCatchAnimation(sprite_id="pokeball")
        self.sprites.add(animation)

        for frame in range(throwFrames):
            animation.image_idx = images
            for idx in range(images - 1, -1, -1):
                if frame <= imageFrames[idx]:
                    animation.image_idx = idx

            animation.update(frame)

            if animation.image_idx == 10:
                self.foe.image.set_alpha(0)

            self.refresh()
            # self.render_pokemon_details()
            self.window.blit(self.get_surface(), (0, 0))
            pg.display.flip()
            pg.time.delay(int(timePerFrame))

        for check in range(checks):
            for frame in range(throwFrames, shakeFrames):
                animation.image_idx = images
                for idx in range(images - 1, -1, -1):
                    if frame <= imageFrames[idx]:
                        animation.image_idx = idx

                animation.update(frame)

                self.refresh()
                # self.render_pokemon_details()
                self.window.blit(self.get_surface(), (0, 0))
                pg.display.flip()
                pg.time.delay(int(timePerFrame))
            pg.time.delay(500)

        if checks != 3:
            # break free!
            pass
        else:
            for frame in range(shakeFrames, frames):
                animation.image_idx = images
                for idx in range(images - 1, -1, -1):
                    if frame <= imageFrames[idx]:
                        animation.image_idx = idx

                animation.update(frame)

                self.refresh()
                # self.render_pokemon_details()
                self.window.blit(self.get_surface(), (0, 0))
                pg.display.flip()
                pg.time.delay(int(timePerFrame))

        self.sprites.remove(animation)

    def switch_active_pokemon(self, new_pokemon):
        self.screens["stats"].refresh()
        friendly_container = self.screens["stats"].get_object("friendly_stats")
        self.screens["stats"].sprites.remove(self.friendly)
        self.screens["stats"].sprites.remove(friendly_container)

        self.screens["stats"].sprites.add([
            StatContainer(sprite_id="friendly_stats", pokemon=new_pokemon, scale=self.scale),
            new_pokemon
        ])
        self.friendly = new_pokemon

        self.render_pokemon_details()

    def render_pokemon_animation(self, window, target: Pokemon, animation_type: str, duration=2000):
        self.render_pokemon_details()
        if target.sprite.animations[animation_type]:
            frames = len(target.sprite.animations[animation_type])
            for frame in target.sprite.animations[animation_type]:
                target.image = frame
                window.blit(self.get_surface(), (0, 0))
                pg.display.flip()
                pg.time.delay(int(0.75 * duration / frames))
                self.refresh()

            target.image = target.displayImage

        window.blit(self.get_surface(), (0, 0))
        pg.display.flip()

    def refresh(self, text=True):
        self.surface = pg.Surface(self.size, pg.SRCALPHA)
        self.screens["stats"].refresh()
        if text:
            self.screens["text"].refresh()

        self.sprite_surface = pg.Surface(self.size, pg.SRCALPHA)

    def get_surface(self, show_sprites=True):
        self.screens["text"].refresh()
        self.text_box.update_image()

        if self.power_off:
            return self.power_off_surface

        if show_sprites:
            self.sprites.draw(self)

        display_surf = self.base_surface.copy()
        display_surf.blit(self.surface, (0, 0))

        for name in self.layer_names:
            display_surf.blit(self.screens[name].get_surface(show_sprites=True), (0, 0))

        display_surf.blit(self.sprite_surface, (0, 0))

        if self.bounce_friendly_stat:
            self.screens["stats"].refresh()
            self.screens["stats"].get_object("friendly_stats").update_pos()

        return display_surf


if __name__ == "__main__":
    import time

    pg.init()
    window = pg.display.set_mode(pg.Vector2(240, 180) * 2)

    bd = BattleDisplayMain(size=window.get_size())

    window.blit(bd.get_surface(), (0, 0))

    pg.event.pump()

    while True:
        time.sleep(1)
