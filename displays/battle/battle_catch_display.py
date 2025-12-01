import pygame as pg
from engine.pokemon.pokemon import Pokemon
from engine.graphics.sprite_screen import SpriteScreen, DisplayContainer


class NameContainer2(DisplayContainer):
    def __init__(self, pk_id, pk_name: str, species:str, pos, scale=1):
        img_path = "assets/containers/menu/pokedex/name_container_2.png"
        DisplayContainer.__init__(self, img_path, "name_container", pos, scale)

        self.add_text_2(pk_name.upper(), text_box=pg.Rect(pg.Vector2(49, 4)*scale, (200, 100)))
        self.add_text_2(f"{pk_id:03}", text_box=pg.Rect(pg.Vector2(22, 4) * scale, (200, 100)))
        self.add_text_2(species, text_box=pg.Rect(pg.Vector2(30, 24) * scale, (200, 100)))


class BattleCatchDisplay(SpriteScreen):
    def __init__(self, size, pokemon, scale=1):
        SpriteScreen.__init__(self,  size)
        self.scale = scale

        self.load_image("assets/menu/pokedex/info/background.png", scale=scale, base=True)

        # self.add_image(pokemon.image, pg.Vector2(48, 72), location=BlitLocation.centre)

        self.addText("HT", pg.Vector2(152, 91) * scale)
        self.addText("WT", pg.Vector2(152, 107) * scale)

        images = Pokemon.get_images(pokemon.ID, crop=False)
        self.add_image(images["front"], pg.Vector2(8, 32) * self.scale)

        container = NameContainer2(pokemon.ID, pokemon.name, pokemon.species, pg.Vector2(107, 22), scale=self.scale)
        container.load_image("assets/menu/pokedex/pokeball.png", pos=pg.Vector2(2, 2) * self.scale,
                             scale=self.scale, )

        img_path = f"Images/Type Labels/{pokemon.type1} Label.png"
        self.load_image(img_path, pg.Vector2(146, 64) * self.scale, scale=self.scale)

        self.sprites.add(container)