from enum import Enum

import pygame as pg

from general.utils import Colours, BlitLocation
from engine.graphics.sprite_screen import SpriteScreen, DisplayContainer
from engine.pokemon.pokemon import Pokemon, oldPokedex


NAME_CONTAINER_POSITIONS = [
    (117, 20), (113, 32), (111, 48), (106, 72), (111, 96), (113, 112), (117, 128),
]


class PokedexDisplayStates(Enum):
    home = 0
    info = 1
    area = 2


class NameContainer(DisplayContainer):
    def __init__(self, pk_id, pk_name: str, pos, offset, scale=1):
        img_path = "assets/containers/menu/pokedex/name_container.png"
        DisplayContainer.__init__(self, img_path, "name_container", pos, scale)

        self.add_text_2(pk_name.upper(), text_box=pg.Rect(pg.Vector2(49, 4)*scale, (200, 100)))
        self.add_text_2(f"{pk_id:03}", text_box=pg.Rect(pg.Vector2(22, 4) * scale, (200, 100)))

        self.offset = offset


class NameContainer2(DisplayContainer):
    def __init__(self, pk_id, pk_name: str, species:str, pos, scale=1):
        img_path = "assets/containers/menu/pokedex/name_container_2.png"
        DisplayContainer.__init__(self, img_path, "name_container", pos, scale)

        self.add_text_2(pk_name.upper(), text_box=pg.Rect(pg.Vector2(49, 4)*scale, (300, 100)))
        self.add_text_2(f"{pk_id:03}", text_box=pg.Rect(pg.Vector2(22, 4) * scale, (200, 100)))
        self.add_text_2(species, text_box=pg.Rect(pg.Vector2(30, 24) * scale, (200, 100)))


class PokedexDisplayMain(SpriteScreen):
    def __init__(self, size, scale, pokedex, display):
        SpriteScreen.__init__(self, size)
        self.scale = scale

        self.pokedex = pokedex
        self.pokedex_display = display

        self.load_image("assets/menu/pokedex/pokedex_background_upper.png", scale=scale, base=True)
        self.add_text_2("Seen", pg.Rect(pg.Vector2(8, 155) * scale, (200, 100)), colour=Colours.white, base=True)
        self.add_text_2("Obtained", pg.Rect(pg.Vector2(128, 155) * scale, (200, 100)), colour=Colours.white, base=True)

        self.add_text_2(f"{self.pokedex.data['appearances'].astype(bool).sum():03}", pg.Rect(pg.Vector2(48, 173) * scale, (200, 100)), colour=Colours.white, base=True)
        self.add_text_2(f"{self.pokedex.data['caught'].sum():03}", pg.Rect(pg.Vector2(180, 172) * scale, (200, 100)), colour=Colours.white, base=True)

        self.pokemon_idx = 1
        self.update()

    def update(self):
        images = Pokemon.get_images(self.pokedex_display.pokemon_idx, crop=False)

        self.kill_sprites()

        self.refresh()

        name = oldPokedex.loc[oldPokedex["ID"] == self.pokedex_display.pokemon_idx].index.values[0]
        if self.pokedex.data.loc[name, "appearances"] > 0:
            self.add_image(images["front"], pg.Vector2(16, 40)*self.scale)
        else:
            self.load_image("assets/menu/pokedex/unknown_pk.png", pos=pg.Vector2(24, 48)*self.scale,scale=self.scale,)

        for i in sorted(range(max([-(self.pokedex_display.pokemon_idx-1), -3]), min([4, -(self.pokedex_display.pokemon_idx - 152)])), key=lambda x: abs(x), reverse=True):
            name = oldPokedex.loc[oldPokedex["ID"] == self.pokedex_display.pokemon_idx+i].index.values[0]
            disp_name = "----" if self.pokedex.data.loc[name, "appearances"] < 1 else name

            container = NameContainer(self.pokedex_display.pokemon_idx+i, disp_name, NAME_CONTAINER_POSITIONS[3+i], scale=self.scale, offset=i)
            if self.pokedex.data.loc[name, "caught"]:
                container.load_image("assets/menu/pokedex/pokeball.png", pos=pg.Vector2(2, 2) * self.scale,
                                scale=self.scale, )

            # container.surface.set_alpha(255 - abs(i)*50)

            self.sprites.add(container)


class PokedexDisplayInfo(SpriteScreen):
    def __init__(self, size, scale, pokedex, display):
        SpriteScreen.__init__(self, size)
        self.scale = scale
        self.pokedex = pokedex
        self.pokedex_display = display

        self.load_image("assets/menu/pokedex/info/background.png", scale=scale, base=True)
        self.addText("HT", pg.Vector2(152, 91) * self.scale, base=True)
        self.addText("WT", pg.Vector2(152, 107) * self.scale, base=True)

    def update(self):
        self.refresh()
        images= Pokemon.get_images(self.pokedex_display.pokemon_idx, crop=False)
        self.add_image(images["front"], pg.Vector2(8, 32) * self.scale)

        name = oldPokedex.loc[oldPokedex["ID"] == self.pokedex_display.pokemon_idx].index.values[0]
        data = self.pokedex.data.loc[name]
        caught = data["caught"]

        species = self.pokedex.national_dex.loc[name, "Species"] if caught else "????? Pokemon"
        container = NameContainer2(self.pokedex_display.pokemon_idx, name, species, pg.Vector2(107, 22), scale=self.scale)

        if caught:
            pk_type = data['Type'][0] if isinstance(data['Type'], tuple) else data['Type']
            img_path = f"Images/Type Labels/{pk_type} Label.png"
            self.load_image(img_path, pg.Vector2(146, 64) * self.scale, scale=self.scale)

            container.load_image(
                "assets/menu/pokedex/pokeball.png", pos=pg.Vector2(2, 2) * self.scale, scale=self.scale,
            )

        self.sprites.add(container)

        self.addText("???\'??\'\'", pg.Vector2(225, 101) * self.scale, location=BlitLocation.bottomRight)
        self.addText(f"{'????.?' if not caught else '2.1'} lbs", pg.Vector2(243, 117) * self.scale,
                     location=BlitLocation.bottomRight)


class PokedexDisplay:
    def __init__(self, size, scale, pokedex):
        self.pokedex = pokedex

        self.pokemon_idx = 1

        self.displays = {
            PokedexDisplayStates.home: PokedexDisplayMain(size, scale, pokedex, display=self),
            PokedexDisplayStates.info: PokedexDisplayInfo(size, scale, pokedex, display=self),
        }

        self.display_state = PokedexDisplayStates.home
        self.active_display = self.displays[self.display_state]

    def update(self):
        self.active_display = self.displays[self.display_state]
        self.active_display.update()



