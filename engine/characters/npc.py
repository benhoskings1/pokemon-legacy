import os
import json
from random import choice

import pygame as pg

from engine.general.direction import Direction
from engine.characters.character import Character
from engine.storyline.game_action import *
from engine.storyline.game_state import GameState


__all__ = ["NPC", "TwinleafGuard", "ProfessorRowan", "PlayerMum"]


DATA_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'game_data')


class NPC(Character):
    """
    Returns a NPC Object.
    """

    with open(os.path.join(DATA_PATH, "game_config/npc_texts.json"), "r") as file:
        response_texts = json.load(file)


    def __init__(self, properties: dict = None, scale: float = 1.0):
        """
        NPC Class
        """

        Character.__init__(
            self,
            properties,
            scale
        )

        self.allow_rotate = properties.get("allow_rotate", False)
        self.response_text: None | list[str] = None
        if self.character_id is not None:
            self.response_text = self.response_texts.get(str(self.character_id), None)

    def update(self, *args, **kwargs):
        if self.allow_rotate:
            self.facing_direction = choice(list(Direction))

    def interaction(self, *args, **kwargs) -> None | list[GameAction]:
        if self.response_text is not None:
            return [TalkAction(self, texts=self.response_text)]
        else:
            return None


class PlayerMum(NPC):
    def __init__(self, properties: dict = None, scale: float = 1.0):
        properties["npc_type"] = "player_mum"
        NPC.__init__(
            self,
            properties,
            scale
        )

        obj_rect = pg.Rect(160, 32, 16, 16)

        size = pg.Vector2(obj_rect.size) * scale
        pos = pg.Vector2(obj_rect.topleft) * scale

        self.vision_rect = pg.Rect(pos, size)
        self.display_name = "Mom"

        print(self.vision_rect)

    def interaction(self, game_state, game_map=None, player=None, auto=False) -> None | list[GameAction]:
        if not auto:
            return super().interaction()

        elif game_state == GameState.meeting_mum:
            events = [
                AttentionAction(self),
                MoveAction(self, direction=Direction.up, steps=1),
                MoveAction(self, direction=Direction.right, steps=3),
                MoveAction(self, direction=Direction.up, steps=3),
                TalkAction(self, texts=[
                    f"Mom: {player.name}!",
                    "Damion came calling for you a little while ago.",
                    "I don't know what it was about, but he said it was an emergency.",
                ]),
                MoveAction(self, direction=Direction.down, steps=2),
                MoveAction(self, direction=Direction.left, steps=3),
                MoveAction(self, direction=Direction.down, steps=1),
                SetGameState(GameState.mum_warning)
            ]

            # update to new vision rect
            obj_rect = pg.Rect(96, 128, 16, 16)

            size = pg.Vector2(obj_rect.size) * self.scale
            pos = pg.Vector2(obj_rect.topleft) * self.scale

            self.vision_rect = pg.Rect(pos, size)

            return events

        elif game_state == GameState.mum_warning:
            self.facing_direction = Direction.down
            events = [
                TalkAction(self, texts=[
                    f"Mom: Oh, yes!\n{player.name}!",
                    "Don't go into the tall grass.\nWild Pokémon might attack you.",
                    "It would be OK if you had your own Pokémon, but you don't, so..."
                ]),
                SetGameState(GameState.meeting_rival)
            ]
            return events

        return None

    def get_vision_rect(self, *args):
        return self.vision_rect


class TwinleafGuard(NPC):
    def __init__(self, properties: dict = None, scale: float = 1.0):
        properties["npc_type"] = "twinleaf_guard"
        NPC.__init__(
            self,
            properties,
            scale
        )

        vision_obj: None | dict = properties.get("custom_vision_rect", None)
        self.vision_rect: None | pg.Rect = None

        if vision_obj is not None:
            # obj_rect: None | pg.Rect = vision_obj.get("rect", None)
            obj_rect = pg.Rect(224, 48, 128, 16)

            size = pg.Vector2(obj_rect.size) * scale
            pos = pg.Vector2(obj_rect.topleft) * scale

            self.vision_rect = pg.Rect(pos, size)

    def get_vision_rect(self, *args):
        return self.vision_rect

    def interaction(self, game_state, game_map=None, player=None, auto=False) -> None | list[GameAction]:
        if not auto:
            return super().interaction()

        elif game_state.value < GameState.going_to_lake_verity.value:
            x_diff = int(player.map_positions[game_map].x - self.map_positions[game_map].x)
            assert player is not None, "Player must be provided for auto-interaction"

            self.facing_direction = Direction.up
            return [
                MoveAction(self, direction=Direction.up, steps=3),
                MoveAction(self, direction=Direction.right, steps=x_diff),
                MoveAction(player, direction=Direction.down, steps=1),
                MoveAction(self, direction=Direction.down, steps=1),
                TalkAction(self, texts=[
                    f"Hiya, {player.name}. Damion was looking for you",
                    "I think he's home now. Why don't you go and check it out?"
                ]),
                MoveAction(self, direction=Direction.left, steps=x_diff),
                MoveAction(self, direction=Direction.down, steps=2),
            ]

        return None


class ProfessorRowan(NPC):
    def __init__(self, scale: float = 1.0):
        properties = {
            "character_type": "professor_rowan",
            "trainer_id": None,
            "npc_name": "Rowan",
            "facing_direction": "up",
        }
        NPC.__init__(
            self,
            properties,
            scale
        )

