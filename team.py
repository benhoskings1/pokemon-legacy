import time
import pygame as pg
from pokemon import Pokemon


class Team:
    def __init__(self, data: list[dict] | list[Pokemon]):
        if isinstance(data[0], dict):
            self.pokemon: list[Pokemon] = [Pokemon(**pkData) for pkData in data]
        else:
            self.pokemon = data

        self.display_running = False

        self.active_index = 0

    def __len__(self):
        return len(self.pokemon)

    def __iter__(self):
        for pokemon in self.pokemon:
            yield pokemon

    def __setitem__(self, idx, data: Pokemon):
        if not isinstance(data, Pokemon):
            raise TypeError("Team member must be a Pokemon")

        self.pokemon[idx] = data

    def __getitem__(self, idx):
        return self.pokemon[idx]

    def __repr__(self):
        return f"Team({self.pokemon})"

    @property
    def all_koed(self) -> bool:
        """Returns True if the team is all Ko'ed"""
        return all([pk.health <= 0 for pk in self.pokemon])

    @property
    def alive_pokemon(self) -> list[Pokemon]:
        return [pk for pk in self if pk.health > 0]

    def get_active_pokemon(self):
        return self[self.active_index]

    def get_index(self, pokemon):
        return self.pokemon.index(pokemon) if pokemon in self.pokemon else None

    def get_pk_up(self, start_index):
        idx = (start_index - 1) % len(self.pokemon)
        return self[idx], idx

    def get_pk_down(self, start_index):
        idx = (start_index + 1) % len(self.pokemon)
        return self[idx], idx

    def swap_pokemon(self, pk_1, pk_2):
        idx_1, idx_2 = self.get_index(pk_1), self.get_index(pk_2)
        if idx_1 is not None and idx_2 is not None:
            self[idx_1], self[idx_2] = pk_2, pk_1

