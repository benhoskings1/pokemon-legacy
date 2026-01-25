import os

import pygame as pg

from pokemon_legacy.constants import ASSET_PATH

from pokemon_legacy.engine.characters.trainer import Trainer

from pokemon_legacy.engine.battle.battle_animation import BattleAnimation
from pokemon_legacy.engine.pokemon.team import Team
from pokemon_legacy.engine.bag.bag import BagV2


class Player2(Trainer):
    def __init__(
            self,
            team: Team,
            scale: float = 1.0,
            bag: BagV2 | None = None
    ):
        """
        Player object (inherits from trainer)

        :param team: team for the player
        :param scale: scale of the sprites
        """
        properties = {
            "character_type": "player_male",
            "character_id": -1,
            "npc_name": "Benji",
            "trainer_id": "1001",
            "facing_direction": "up"
        }

        self.sprite_path = os.path.join(ASSET_PATH, "sprites/Player Sprites")
        Trainer.__init__(self, properties=properties, team=team, is_player=True, scale=scale)

        back_frames = self.get_battle_back(self.character_type, scale=scale, bg_colour=(147, 187, 236, 255))

        self.battle_sprite.image = back_frames[0]
        self.blit_rect = self.image.get_rect()

        self.reset_battle_sprite()

        self.steps = 0
        self.money = 3000
        self.bag = bag

    def __repr__(self):
        return f"Player {self.character_type.name} at {self.map_rects}"

    def __getstate__(self):
        self._clear_surfaces()
        print(dir(self))
        return self.__dict__

    @classmethod
    def get_battle_back(cls, character_type, bg_colour=None, scale: float = 1.0):
        """
        Loads each back frame for a player in a battle

        :param character_type:
        :param bg_colour:
        :param scale: value to scale the surface by
        :return: frames
        """

        frame_size, border_size = pg.Vector2(80, 80), pg.Vector2(1, 18)
        trainer_block_size = pg.Vector2((frame_size.x + border_size.x) * 5, frame_size.y)

        block_location = cls.battle_back_mapping[character_type]
        block_rect = pg.Rect((trainer_block_size.x * block_location[0],
                              trainer_block_size.y * block_location[1]),
                             trainer_block_size)

        frames: list[pg.Surface] = []
        for frame_idx in range(5):
            frame_rect = pg.Rect((frame_idx * (frame_size.x * border_size.x), frame_size.y + border_size.y), frame_size)
            frame_rect.topleft += pg.Vector2(block_rect.topleft)

            frame = cls.trainer_back_parent_surf.subsurface(frame_rect).copy()
            if bg_colour is not None:
                frame = frame.convert_alpha()
                px_array = pg.PixelArray(frame)
                px_array.replace(bg_colour, pg.Color(0, 0, 0, 0), distance=0.05)
                px_array.close()

            if scale != 1.0:
                frame = pg.transform.scale(frame, frame_size * scale)

            frames.append(frame)
        return frames

    def reset_battle_sprite(self):
        self.battle_sprite.image = self.battle_animation[0]
        self.battle_sprite.rect = pg.Rect(pg.Vector2(152, 10) * self.scale, self.battle_sprite.image.get_size())
        self.battle_sprite.rect.midbottom = pg.Vector2(63, 144) * self.scale

    def _load_surfaces(self):
        super()._load_surfaces()

        battle_animation_dir = "assets/sprites/trainers/battle_start"
        frame_durations = [1000, 200, 200, 200, 200]
        self.battle_animation = BattleAnimation(battle_animation_dir, durations=frame_durations, scale=2)

    def _clear_surfaces(self):
        super()._clear_surfaces()
        self._sprite_sets = None
        self.battle_sprite.kill()
        self.battle_sprite = None

        self.battle_animation = None

    def get_json_data(self):
        return {
            "steps": self.steps,
            "money": self.money,
            "bag": self.bag.get_json_data(),
            "team": self.team.get_json_data(),
            "positions": [
                (_map.map_name, _map.parent_collection.collection_name, pos[0:2]) for _map, pos in self.map_positions.items()
            ]
        }

    def load_from_state(self, player_state: dict):
        self.steps = player_state.get("steps", self.steps)
        self.money = player_state.get("money", self.money)

        self.bag = BagV2(player_state.get("bag", None))
        self.team = Team(player_state.get("team", None))

    # === Follower Management ===
    @property
    def has_follower(self) -> bool:
        """Check if the player has an active follower."""
        return self.follower is not None

    def set_follower(self, character) -> None:
        """
        Attach a follower to the player.
        
        :param character: The character to follow the player
        """
        self.follower = character
        self.clear_position_history()

    def clear_follower(self) -> None:
        """Remove the current follower."""
        self.follower = None
        self.clear_position_history()
