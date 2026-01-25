from dataclasses import dataclass

import pygame as pg

from pokemon_legacy.engine.storyline.game_action import *
from pokemon_legacy.engine.storyline.game_state import GameState

from pokemon_legacy.engine.characters.character import Character
from pokemon_legacy.engine.characters.npc import ProfessorRowan
from pokemon_legacy.engine.characters.player import Player2
from pokemon_legacy.engine.characters.trainer import Rival, Dawn

from pokemon_legacy.engine.general.direction import Direction

__all__ = ["SelectStarterPokemon", "MapInteraction",]


@dataclass
class MapInteraction:
    character_name: str
    map_name: str
    collection_name: str
    rect: pg.Rect
    game_state: GameState | None = None


class StorylineEvent:

    def __init__(
            self,
            event_name: str,
            trigger_criteria: MapInteraction,
            *args,
            **kwargs
    ):
        self.event_name = event_name
        self.trigger_criteria = trigger_criteria

    def run_event(self, *args, **kwargs) -> None | list[GameAction]:
        return None


class SelectStarterPokemon(StorylineEvent):
    def __init__(self):
        trigger = MapInteraction(
            "player", "verity_lakefront", "route_orchestrator", rect=pg.Rect(128, 336, 32, 16),
            game_state=GameState.going_to_lake_verity
        )

        StorylineEvent.__init__(self, "select_starter", trigger_criteria=trigger)

    def run_event(self, characters: list[Character], **kwargs):
        player = next((c for c in characters if isinstance(c, Player2)), None)
        rival = next((c for c in characters if isinstance(c, Rival)), None)
        professor_rowan = next((c for c in characters if isinstance(c, ProfessorRowan)), None)
        dawn = next((c for c in characters if isinstance(c, Dawn)), None)

        return [
            MoveAction(player, Direction.up, steps=1),
            MoveAction(rival, Direction.up, steps=1),
            TalkAction(player, texts=[
                "Damion: What's going on...?",
            ]),
            # pan ahead...
            MoveCameraPosition(direction=Direction.up, tiles=9),
            TalkAction(dawn, texts=[
                "Professor, there isn't anything out of the ordinary on the other side,"
                "either!",
                "Professor: Hmm...\nI may have been mistaken...",
                "Something appears to be different than it was before, but...",
                "Fine! It's enough that we have seen the lake."
            ]),
            SetFacingDirection(professor_rowan, direction=Direction.right),
            TalkAction(professor_rowan, texts=["Dawn, we're leaving."]),
            SetFacingDirection(professor_rowan, direction=Direction.down),
            SetFacingDirection(dawn, direction=Direction.left),
            SetFacingDirection(professor_rowan, direction=Direction.right),
            TalkAction(professor_rowan, texts=[
                "Dawn: Professor, how are you enjoying being back in Sinnoh?",
                "After being away for four years, it must be exciting again?",
                "Professor: ...Hm.\nThere is one thing I can say.",
                "There are many rare kinds of Pokémon in Sinnoh.",
                "The region should serve us very well in regards to our studies.",
            ]),

            MoveAction(professor_rowan, direction=Direction.down, steps=1),
            MoveAction(dawn, direction=Direction.left, steps=1),
            MoveCameraPosition(direction=Direction.down, tiles=1),

            MoveAction(professor_rowan, direction=Direction.down, steps=1),
            MoveAction(dawn, direction=Direction.down, steps=1),
            MoveCameraPosition(direction=Direction.down, tiles=1),

            MoveAction(professor_rowan, direction=Direction.down, steps=1),
            MoveAction(dawn, direction=Direction.down, steps=1),
            MoveCameraPosition(direction=Direction.down, tiles=1),

            MoveAction(professor_rowan, direction=Direction.down, steps=1),
            MoveAction(dawn, direction=Direction.down, steps=1),
            MoveCameraPosition(direction=Direction.down, tiles=1),

            MoveAction(professor_rowan, direction=Direction.left, steps=1),
            MoveAction(professor_rowan, direction=Direction.down, steps=5),
            MoveAction(dawn, direction=Direction.left, steps=1),
            MoveAction(dawn, direction=Direction.down, steps=5),
            MoveAction(dawn, direction=Direction.left, steps=1),
            MoveAction(dawn, direction=Direction.down, steps=5),
            MoveAction(rival, direction=Direction.right, steps=1),
            SetFacingDirection(rival, direction=Direction.left),
            TalkAction(rival, texts=["Professor: Excuse me.\nLet us pass, please."]),
            MoveAction(professor_rowan, direction=Direction.down, steps=4),
            SetFacingDirection(dawn, direction=Direction.left),
            SetFacingDirection(dawn, direction=Direction.right),
            SetFacingDirection(dawn, direction=Direction.left),
            SetFacingDirection(dawn, direction=Direction.down),
            TalkAction(dawn, texts=["Dawn: I beg your pardon... We'll be on our way."]),
            MoveAction(dawn, direction=Direction.down, steps=4),
            SetGameState(GameState.going_to_sandgem_town)
        ]


if __name__ == "__main__":
    select_starter_pokemon = SelectStarterPokemon()
    print(select_starter_pokemon.events)
