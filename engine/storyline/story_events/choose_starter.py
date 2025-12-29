from enum import Enum

import pygame as pg
from pathlib import Path

from numpy.ma.core import choose
from statemachine import StateMachine, State

from engine.general.direction import Direction
from engine.general.controller import Controller
from engine.general.utils import BlitLocation
from engine.graphics.main_screen import MainScreen
from engine.graphics.selector_display import SelectorDisplay

from engine import pokemon_generator
from engine.graphics.sprite_screen import SpriteScreen
from engine.pokemon.pokemon import Pokemon

MODULE_PATH = Path(__file__).parent


class SelectorOptions(Enum):
    no = 0
    yes = 1


class PokemonContainer(pg.sprite.Sprite, SpriteScreen):
    def __init__(self, pokemon: Pokemon, scale: float | int = 1.0):
        pg.sprite.Sprite.__init__(self)

        base_image = pg.image.load(str(MODULE_PATH / "assets" / "pokemon_spotlight.png"))

        SpriteScreen.__init__(self, pg.Vector2(base_image.get_size()) * scale)
        # load base circle
        self.add_image(base_image, scale=scale)

        # load pokemon
        self.add_image(
            pokemon.image,
            pos=pg.Vector2(48, 48) * scale,
            location=BlitLocation.centre
        )

        self.rect = pg.Rect(pg.Vector2(77, 48) * scale, self.size)

    @property
    def image(self):
        return self.get_surface()


class ChooseStarterDisplay(SelectorDisplay, MainScreen, StateMachine):
    choosing = State("choose", initial=True)
    confirming = State("confirm")
    # confirmed = State("confirmed")

    confirm_starter = choosing.to(confirming, on="confirm_transition")

    go_back = (
        choosing.to(choosing)
        | confirming.to(choosing, on="cancel_selection")
    )

    controller = Controller()

    def __init__(self, size, scale=1.0):

        starters = [pokemon_generator.generate_pokemon(name, level=5) for name in ("Chimchar", "Turtwig", "Piplup")]

        self.starter_containers = {
            pk: PokemonContainer(pk, scale=scale) for pk in starters
        }

        MainScreen.__init__(self, size, scale)

        SelectorDisplay.__init__(
            self,
            display_image_path=str(MODULE_PATH / "assets" / "choose_starter_base.png"),
            selector_image_path=str(MODULE_PATH / "assets" / "finger_selector.png"),
            options=starters,
            option_positions=[(64, 45), (116, 72), (158, 45)],
            display_position=pg.Vector2(0, 0),
            scale=scale
        )

        StateMachine.__init__(self)

        self.link_options(starters[0], starters[1], Direction.right, reverse=True)
        self.link_options(starters[1], starters[2], Direction.right, reverse=True)

        self.confirm_box = SelectorDisplay(
            display_image_path=str(MODULE_PATH / "assets" / "confirm_box.png"),
            selector_image_path="arrow",
            options=SelectorOptions,
            option_positions=[(6, 9), (6, 25)],
            display_position=pg.Vector2(178, 90),
            scale=scale

        )

    # === STATE MACHINE API ===
    def confirm_transition(self):
        selected_pk: Pokemon = self.selected

        self.sprites.add(self.confirm_box)
        self.sprites.add(self.starter_containers[selected_pk])

        self.update_display_text(
            f"{selected_pk.species} {selected_pk.name.upper()}!,"
            f"Will you take this Pokémon?"
        )

    def cancel_selection(self):
        self.sprites.empty()
        self.refresh()

    # === DISPLAY CONFIGURATION ===
    def set_up(self):
            ...

    def loop(
            self,
            window: pg.Surface,
            controller: Controller = Controller()
    ):
        window.blit(self.get_surface(), (0, 0))
        pg.display.flip()

        while True:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    return None

                elif event.type == pg.KEYDOWN:
                    if event.key in controller.move_keys:
                        move_dir = controller.direction_key_bindings[event.key]
                        self.process_interaction(move_dir)
                        self.update()

                    elif event.key == controller.a:
                        self.send("confirm_starter")

                    elif event.key == controller.b:
                        self.send("go_back")

                window.blit(self.get_surface(), (0, 0))
                pg.display.flip()


if __name__ == "__main__":
    pg.init()

    display_scale = 2.0
    screen_size = pg.Vector2(256, 192) * display_scale
    window = pg.display.set_mode(pg.Vector2(screen_size.x, screen_size.y * 2))
    main_display = window.subsurface(pg.Rect((0, 0), screen_size))

    starter_display = ChooseStarterDisplay(screen_size, scale=display_scale)

    starter_display.loop(window)


