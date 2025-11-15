import os

import pygame as pg

from engine.characters.character import Movement
from engine.characters.trainer import Trainer

from graphics.engine.sprite_set import SpriteSet2

from battle_animation import BattleAnimation
from team import Team
from bag.bag import BagV2


class Player2(Trainer):
    def __init__(
            self,
            position: tuple[int, int] | list[int] | pg.Vector2,
            team: Team,
            scale: float = 1.0,
            bag: BagV2 | None = None
    ):
        """
        Player object (inherits from trainer)

        :param position: grid position of the player
        :param team: team for the player
        :param scale: scale of the sprites
        """
        properties = {
            "npc_type": "player_male",
            "npc_name": "Benji",
            "trainer_id": "1001",
            "facing_direction": "down"
        }

        if not isinstance(position, pg.Vector2):
            position = pg.Vector2(position)

        # player_rect = pg.Rect(position * 32 * scale, pg.Vector2(32, 32) * scale)

        self.sprite_path = "Sprites/Player Sprites"
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

            frame = cls.character_back_parent_surf.subsurface(frame_rect).copy()
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
        self._sprite_sets = {
            Movement.walking: SpriteSet2(
                os.path.join(self.sprite_path, "Walking Sprites.png"), 12, pg.Vector2(34, 50), pg.Vector2(0, 0)
            ),
            Movement.running: SpriteSet2(
                os.path.join(self.sprite_path, "Running Sprites.png"), 12, pg.Vector2(40, 50), pg.Vector2(0, 0)
            )
        }

        battle_animation_dir = "assets/sprites/trainers/battle_start"
        frame_durations = [1000, 200, 200, 200, 200]
        self.battle_animation = BattleAnimation(battle_animation_dir, durations=frame_durations, scale=2)

    def _clear_surfaces(self):
        self._sprite_sets = None
        self.battle_sprite.image = None

        self.battle_animation = None
