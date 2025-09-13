import pandas as pd
import pygame as pg

from pokemon import pokedex
from displays.pokedex.pokedex_display import PokedexDisplay, PokedexDisplayStates


class Pokedex:
    def __init__(self, game):
        self.game = game
        self.controller = game.controller

        self.national_dex = pd.read_csv("game_data/pokedex/NationalDex/NationalDex.tsv", delimiter='\t', index_col=0)

        self.data: pd.DataFrame = pokedex
        if "appearances" not in self.data.columns:
            self.data["appearances"] = 0
        if "caught" not in self.data.columns:
            self.data["caught"] = False

            # print(self.data.head())

        self.main_display = None
        self.touch_display = None

        self.load_surfaces()

    def get_next_seen_index(self, descending=True):
        direction_mask = (self.data["Local_Num"] > self.main_display.pokemon_idx) if descending else \
                            (self.data["Local_Num"] < self.main_display.pokemon_idx)

        seen_pks = self.data.loc[direction_mask & (self.data["appearances"] > 0)]

        if not descending:
            seen_pks = seen_pks.sort_values("Local_Num", ascending=False)

        return seen_pks["Local_Num"].iloc[0] if len(seen_pks) > 0 else None

    def update_display(self, flip=True):
        self.game.topSurf.blit(self.main_display.active_display.get_surface(), (0, 0))

        # self.game.bottomSurf.blit(self.poketech.getSurface(), (0, 0))
        if flip:
            pg.display.flip()

    def loop(self):
        self.update_display()

        action = None

        while not action:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.game.save_and_exit()
                    return None

                elif event.type == pg.KEYDOWN:
                    if event.key == self.controller.a and self.main_display.display_state == PokedexDisplayStates.home:
                        if self.data.loc[self.data["Local_Num"] == self.main_display.pokemon_idx, "appearances"].iloc[0] > 0:
                            self.main_display.display_state = PokedexDisplayStates.info
                            self.main_display.update()
                            self.update_display()

                    elif event.key == self.controller.b:
                        if self.main_display.display_state == PokedexDisplayStates.home:
                            return None
                        else:
                            self.main_display.display_state = PokedexDisplayStates.home
                            self.main_display.update()
                            self.update_display()

                    elif event.key == self.controller.up:
                        if self.main_display.pokemon_idx != 1:
                            if self.main_display.display_state == PokedexDisplayStates.home:
                                self.main_display.pokemon_idx -= 1
                            else:
                                next_idx = self.get_next_seen_index(descending=False)
                                if next_idx is not None:
                                    self.main_display.pokemon_idx = next_idx

                            self.main_display.update()
                            self.update_display()

                    if event.key == self.controller.down:
                        if self.main_display.pokemon_idx != 151:
                            if self.main_display.display_state == PokedexDisplayStates.home:
                                self.main_display.pokemon_idx += 1
                            else:
                                next_idx = self.get_next_seen_index()
                                if next_idx is not None:
                                    self.main_display.pokemon_idx = next_idx

                            self.main_display.update()
                            self.update_display()

    def clear_surfaces(self):
        self.main_display = None
        self.touch_display = None

    def load_surfaces(self):
        self.main_display = PokedexDisplay(self.game.displaySize, self.game.graphics_scale, pokedex=self)
        self.touch_display = None