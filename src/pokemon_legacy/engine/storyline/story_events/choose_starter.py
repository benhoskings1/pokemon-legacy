from enum import Enum

import pygame as pg
from pathlib import Path

from numpy.ma.core import choose
from statemachine import StateMachine, State

from pokemon_legacy.engine.general.direction import Direction
from pokemon_legacy.engine.general.controller import Controller
from pokemon_legacy.engine.general.utils import BlitLocation
from pokemon_legacy.engine.graphics.main_screen import MainScreen
from pokemon_legacy.engine.graphics.selector_display import SelectorDisplay

from pokemon_legacy.engine import pokemon_generator
from pokemon_legacy.engine.graphics.sprite_screen import SpriteScreen
from pokemon_legacy.engine.pokemon.pokemon import Pokemon

MODULE_PATH = Path(__file__).parent


class ConfirmOption(Enum):
    yes = 1
    no = 0


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
    confirmed = State("confirmed", final=True)

    confirm_starter = choosing.to(confirming, on="confirm_transition")
    complete_starter = confirming.to(confirmed, on="complete_transition")

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

        self.main_selector = self.selector

        StateMachine.__init__(self)

        self.link_options(starters[0], starters[1], Direction.right, reverse=True)
        self.link_options(starters[1], starters[2], Direction.right, reverse=True)

        self.confirm_box = SelectorDisplay(
            display_image_path=str(MODULE_PATH / "assets" / "confirm_box.png"),
            selector_image_path="arrow",
            options=ConfirmOption,
            option_positions=[(6, 9), (6, 25)],
            display_position=pg.Vector2(178, 90),
            scale=scale

        )

        self.confirm_box.link_options(ConfirmOption.yes, ConfirmOption.no, direction=Direction.down, reverse=True)

        self.selector_map = {
            self.choosing: self.selector,
            self.confirming: self.confirm_box.selector,
        }

    # === STATE MACHINE API ===
    def confirm_transition(self):
        selected_pk: Pokemon = self.selected

        self.sprites.add(self.confirm_box)
        self.sprites.add(self.starter_containers[selected_pk])

        self.update_display_text(
            f"{selected_pk.species} {selected_pk.name.upper()}!"
            f"Will you take this Pokémon?"
        )

    def complete_transition(self):
        ...

    def cancel_selection(self):
        self.sprites.empty()
        self.sprites.add(self.selector)
        self.refresh()

    # === DISPLAY CONFIGURATION ===
    def set_up(self):
            ...

    def loop(
            self,
            window: pg.Surface,
            controller: Controller = Controller()
    ) -> None | bool:
        window.blit(self.get_surface(), (0, 0))
        pg.display.flip()

        while True:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    return None

                elif event.type == pg.KEYDOWN:
                    if event.key in controller.move_keys:
                        move_dir = controller.direction_key_bindings[event.key]
                        self.confirm_box.refresh()
                        self.process_interaction(move_dir, self.selector_map[self.current_state])

                        self.update()

                    elif event.key == controller.b or self.selector_map[self.current_state].selected == ConfirmOption.no:
                        self.send("go_back")

                    elif event.key == controller.a:
                        if self.current_state == self.choosing:
                            self.send("confirm_starter")
                        elif self.current_state == self.confirming:
                            self.send("complete_starter")
                            return True



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


