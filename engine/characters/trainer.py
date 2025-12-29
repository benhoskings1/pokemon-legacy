import os
import pygame as pg
import json

from engine.pokemon.team import Team

from engine.general.direction import Direction

from engine.storyline.game_state import GameState
from engine.storyline.game_action import *
from engine.characters.character import Character, CharacterTypes

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'game_data')
ASSET_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'assets')


class Trainer(Character):
    """
    Returns a Trainer Object. 
    """

    battle_font_mapping = {
        CharacterTypes.player_male: (0, 0),
        CharacterTypes.dawn: (1, 0),
        CharacterTypes.barry: (2, 0),
        CharacterTypes.youngster: (3, 0),
        CharacterTypes.lass: (4, 0),
    }

    battle_back_mapping = {
        CharacterTypes.player_male: (0, 0),
        CharacterTypes.dawn: (1, 0),
        CharacterTypes.barry: (0, 1),
        CharacterTypes.riley: (0, 2),
    }

    trainer_front_parent_surf = pg.image.load(os.path.join(ASSET_PATH, 'sprites/trainers/trainer_front_images.png'))
    trainer_back_parent_surf = pg.image.load(os.path.join(ASSET_PATH, 'sprites/trainers/trainer_front_images.png'))

    with open(os.path.join(DATA_PATH, "game_config/trainer_teams.json")) as f:
        trainer_data = json.load(f)

    def __init__(
            self,
            properties: dict = None,
            team: None | Team = None,
            is_player = False,
            scale: float = 1.0
    ):
        """
        Trainer Class
        """

        Character.__init__(self, properties, scale)

        self.trainer_id = properties["trainer_id"]

        self.is_player = is_player

        self.battle_sprite = pg.sprite.Sprite()

        # load team data
        team_data = self.trainer_data.get(self.trainer_id, None)
        self.team: Team = team if team else (Team(data=self.trainer_data[self.trainer_id]) if team_data else Team())

        # dict to hold trainer position and blit rect on each map

        self.battled = False

        self._load_surfaces()

    def __repr__(self):
        return f"Trainer('{self.character_type.name.title()} {self.name.title()}',{self.team})"

    def __getstate__(self):
        self._clear_surfaces()
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._load_surfaces()

    def get_vision_rect(self, _map):
        return self._get_vision_rect(self.map_rects[_map], self.facing_direction)

    @staticmethod
    def _get_vision_rect(sprite_rect: pg.Rect, facing_direction: Direction, view_dist: int = 4) -> pg.Rect:
        """
        Return a rect representing the view distance of a trainer.

        :param sprite_rect: rect of the trainer
        :param facing_direction: facing direction
        :param view_dist: view distance in grid squares
        :return: rect of vision field
        """
        w, h = sprite_rect.size
        if facing_direction == Direction.up:
            size = (w, h * view_dist)
            topleft = (sprite_rect.left, sprite_rect.top - size[1])
        elif facing_direction == Direction.down:
            size = (w, h * view_dist)
            topleft = (sprite_rect.left, sprite_rect.bottom)
        elif facing_direction == Direction.left:
            size = (w * view_dist, h)
            topleft = (sprite_rect.left - size[0], sprite_rect.top)
        else:  # Direction.right
            size = (w * view_dist, h)
            topleft = (sprite_rect.right, sprite_rect.top)

        return pg.Rect(topleft, size)

    @classmethod
    def get_battle_front(cls, trainer_type: CharacterTypes, bg_colour=None, scale=1) -> pg.Surface:
        block_size, border_size = pg.Vector2(80, 80), pg.Vector2(1, 18)
        block_location = cls.battle_font_mapping[trainer_type]
        image_rect = pg.Rect(
            pg.Vector2(
                block_location[0] * (block_size.x + border_size.x) + border_size.x,
                block_location[1] * (block_size.y + border_size.y) + border_size.y
            ), block_size)

        image = cls.trainer_front_parent_surf.subsurface(image_rect).copy()
        # print(image.get_at([0, 0]))

        if bg_colour is not None:
            image = image.convert_alpha()
            px_array = pg.PixelArray(image)
            px_array.replace(bg_colour, pg.Color(0, 0, 0, 0), distance=0.05)
            px_array.close()

        return pg.transform.scale(image, pg.Vector2(image.get_size()) * scale) if scale != 1.0 else image

    def _load_surfaces(self):
        super()._load_surfaces()
        self.battle_sprite = pg.sprite.Sprite()
        self.battle_sprite.image = self.get_battle_front(
            self.character_type, scale=self.scale, bg_colour=(147, 187, 236, 255)
        )
        self.battle_sprite.rect = pg.Rect(pg.Vector2(152, 10) * self.scale, self.battle_sprite.image.get_size())

    def _clear_surfaces(self):
        super()._clear_surfaces()
        self._sprite_sets = None
        self.battle_sprite.image = None

    def interaction(self, *args, **kwargs) -> None | list[GameAction]:
        return [
            TrainerBattle(self)
        ]


class Rival(Trainer):
    def __init__(
            self,
            team: None | Team = None,
            scale: float = 1.0
    ):
        """
        Trainer Class
        """
        properties = {"character_type": "barry", "trainer_id": None, "npc_name": "Damion"}
        Trainer.__init__(self, properties, team, scale=scale)
        self.visible = False

        obj_rect = pg.Rect(176, 192, 16, 16)

        size = pg.Vector2(obj_rect.size) * scale
        pos = pg.Vector2(obj_rect.topleft) * scale

        self.vision_rect = pg.Rect(pos, size)

    def interaction(self, game_state, game_map=None, player=None, auto=False) -> None | list[GameAction]:
        if not auto:
            return super().interaction()

        elif game_state == GameState.meeting_rival:
            assert player is not None, "Player must be provided for auto-interaction"

            self.visible = True

            # set to new vision rect
            rect = pg.Rect(48, 52, 16, 13)

            size = pg.Vector2(rect.size) * self.scale
            pos = pg.Vector2(rect.topleft) * self.scale

            self.vision_rect = pg.Rect(pos, size)

            return [
                MoveAction(self, direction=Direction.down, steps=1, ignore_solid_objects=True, duration=50),
                MoveAction(player, direction=Direction.down, steps=1),
                TalkAction(self, texts=["THUD!!!"]),
                AttentionAction(self),
                TalkAction(self, texts=[
                    "Damion: What was that about?",
                    f"Oh, hey, {player.name}!",
                    "Hey! I'm going to the lake!\nYou come too! And be quick about it!",
                    f"Ok, {player.name}? I'm fining you $1 million if you're late!",
                ]),
                MoveAction(self, direction=Direction.right, steps=4, duration=125),
                AttentionAction(self),
                MoveAction(self, direction=Direction.left, steps=4, duration=125),
                TalkAction(self, texts=["Damion: Oh, jeez!\nForgot something!"]),
                MoveAction(self, direction=Direction.up, steps=1, ignore_solid_objects=True),
                SetCharacterVisibility(self, visible=False),
                MoveAction(self, direction=Direction.up, steps=1, ignore_solid_objects=True, duration=10),
                SetGameState(GameState.following_rival)
            ]

        elif game_state == GameState.following_rival:
            vision_rect = pg.Rect(224, 336, 64, 16)
            size = pg.Vector2(vision_rect.size) * self.scale
            pos = pg.Vector2(vision_rect.topleft) * self.scale

            self.vision_rect = pg.Rect(pos, size)

            return [
                TalkAction(self, texts=[
                    "Damion: ...I'd better take\nmy Bag and Journal, too..."
                ]),
                AttentionAction(self),
                TalkAction(self, texts=[
                    f"Oh, hey, {player.name}!",
                    "We're going to the lake!\nI'll be waiting on the road!",
                    "It's a $10 million fine of you're late!",
                ]),
                MoveAction(self, direction=Direction.left, steps=4),
                MoveAction(self, direction=Direction.up, steps=1),
                MoveAction(self, direction=Direction.left, steps=1),
                MoveAction(player, direction=Direction.down, steps=1),
                MoveAction(self, direction=Direction.left, steps=1),
                SetGameState(GameState.going_to_lake_verity),
                MoveAction(self, direction=Direction.left, steps=2),
                SetCharacterVisibility(self, visible=False),
            ]

        elif game_state == GameState.going_to_lake_verity:
            return [
                TalkAction(self, texts=[
                    "Damion: Hey, you saw that news report that was on TV, right?",
                    'You know, "Search for the Red GYARADOS! The mysterious appearance"',
                    'of the furious Pokémon in a lake!"',
                    'That show got me to thinking.',
                    "I'll bet our local lake has a Pokémon like that in it too!"
                    "So, that's what we're gonna do.\nWe'll go find a Pokémon like that!"
                ])
            ]

        return None

    def get_vision_rect(self, *args):
        return self.vision_rect


class Dawn(Trainer):
    def __init__(
            self,
            team: None | Team = None,
            scale: float = 1.0
    ):
        """
        Trainer Class
        """
        properties = {"character_type": "dawn", "trainer_id": "dawn", "npc_name": "Dawn", "facing_direction": "up"}
        Trainer.__init__(self, properties, team, scale=scale)

        obj_rect = pg.Rect(176, 192, 16, 16)

        size = pg.Vector2(obj_rect.size) * scale
        pos = pg.Vector2(obj_rect.topleft) * scale

        self.vision_rect = pg.Rect(pos, size)

    def interaction(self, game_state, game_map=None, player=None, auto=False) -> None | list[GameAction]:
        if not auto:
            return super().interaction()

        elif game_state == GameState.meeting_rival:
            assert player is not None, "Player must be provided for auto-interaction"

            self.visible = True

            # set to new vision rect
            rect = pg.Rect(48, 52, 16, 13)

            size = pg.Vector2(rect.size) * self.scale
            pos = pg.Vector2(rect.topleft) * self.scale

            self.vision_rect = pg.Rect(pos, size)

            return [
                MoveAction(self, direction=Direction.down, steps=1, ignore_solid_objects=True, duration=50),
                MoveAction(player, direction=Direction.down, steps=1),
                TalkAction(self, texts=["THUD!!!"]),
                AttentionAction(self),
                TalkAction(self, texts=[
                    "Damion: What was that about?",
                    f"Oh, hey, {player.name}!",
                    "Hey! I'm going to the lake!\nYou come too! And be quick about it!",
                    f"Ok, {player.name}? I'm fining you $1 million if you're late!",
                ]),
                MoveAction(self, direction=Direction.right, steps=4, duration=125),
                AttentionAction(self),
                MoveAction(self, direction=Direction.left, steps=4, duration=125),
                TalkAction(self, texts=["Damion: Oh, jeez!\nForgot something!"]),
                MoveAction(self, direction=Direction.up, steps=1, ignore_solid_objects=True),
                SetCharacterVisibility(self, visible=False),
                MoveAction(self, direction=Direction.up, steps=1, ignore_solid_objects=True, duration=10),
                SetGameState(GameState.following_rival)
            ]

        elif game_state == GameState.following_rival:
            vision_rect = pg.Rect(224, 336, 64, 16)
            size = pg.Vector2(vision_rect.size) * self.scale
            pos = pg.Vector2(vision_rect.topleft) * self.scale

            self.vision_rect = pg.Rect(pos, size)

            return [
                TalkAction(self, texts=[
                    "Damion: ...I'd better take\nmy Bag and Journal, too..."
                ]),
                AttentionAction(self),
                TalkAction(self, texts=[
                    f"Oh, hey, {player.name}!",
                    "We're going to the lake!\nI'll be waiting on the road!",
                    "It's a $10 million fine of you're late!",
                ]),
                MoveAction(self, direction=Direction.left, steps=4),
                MoveAction(self, direction=Direction.up, steps=1),
                MoveAction(self, direction=Direction.left, steps=1),
                MoveAction(player, direction=Direction.down, steps=1),
                MoveAction(self, direction=Direction.left, steps=1),
                SetGameState(GameState.going_to_lake_verity),
                MoveAction(self, direction=Direction.left, steps=2),
                SetCharacterVisibility(self, visible=False),
            ]

        elif game_state == GameState.going_to_lake_verity:
            return [
                TalkAction(self, texts=[
                    "Damion: Hey, you saw that news report that was on TV, right?",
                    'You know, "Search for the Red GYARADOS! The mysterious appearance"',
                    'of the furious Pokémon in a lake!"',
                    'That show got me to thinking.',
                    "I'll bet our local lake has a Pokémon like that in it too!"
                    "So, that's what we're gonna do.\nWe'll go find a Pokémon like that!"
                ])
            ]

        return None

    def get_vision_rect(self, *args):
        return self.vision_rect
