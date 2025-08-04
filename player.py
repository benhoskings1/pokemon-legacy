import os
from enum import Enum

import pygame as pg

from general.Direction import Direction
from Sprites.SpriteSet import SpriteSet2
from general.utils import get_image_frame
from trainer import TrainerTypes

from battle_animation import BattleAnimation


battle_back_mapping = {
    TrainerTypes.player_male: (0, 0),
    TrainerTypes.player_female: (1, 0),
    TrainerTypes.barry: (0, 1),
    TrainerTypes.riley: (0, 2),
}

trainer_back_parent_surf = pg.image.load('assets/sprites/trainers/trainer_front_images.png')


class Movement(Enum):
    walking = 0
    running = 1


class Player(pg.sprite.Sprite):
    def __init__(self, sprite_path: os.PathLike | str, position=pg.Vector2(0, 0), tile_size=32, scale=1):
        """
        
        :param sprite_path:
        :param position:
        """
        # ======== INITIALISATION =======
        pg.sprite.Sprite.__init__(self)
        self.sprite_type = "player"
        self.id = "benji"
        self.scale = scale

        self.spriteIdx = 3
        self.facingDirection = Direction.down

        self._leg = True
        self._sprite_sets: dict | None = None
        self._moving = False
        self.battle_animation = None

        self.movement = Movement.walking
        self.battle_sprite = pg.sprite.Sprite()

        self.sprite_path = sprite_path
        self._load_surfaces(sprite_path)

        self.position = position
        self.blit_rect = self.image.get_rect()
        self.rect = pg.Rect(self.position * tile_size, (tile_size, tile_size))

        self.steps = 0

    def __getstate__(self):
        self._clear_surfaces()
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._load_surfaces(self.sprite_path)

    @property
    def sprites(self):
        return self._sprite_sets[self.movement].sprites

    @property
    def image(self) -> pg.Surface | None:
        return self.sprites[
            self.spriteIdx + (0 if not self._moving else (1 if self._leg else 2))
        ] if self.sprites is not None else None

    @staticmethod
    def get_battle_back(trainer_type, bg_colour=None, scale=1):
        frame_size, border_size = pg.Vector2(80, 80), pg.Vector2(1, 18)
        trainer_block_size = pg.Vector2((frame_size.x + border_size.x) * 5, frame_size.y)

        block_location = battle_back_mapping[trainer_type]
        block_rect = pg.Rect((trainer_block_size.x * block_location[0],
                              trainer_block_size.y * block_location[1]),
                             trainer_block_size)

        frames: list[pg.Surface] = []
        for frame_idx in range(5):
            frame_rect = pg.Rect((frame_idx * (frame_size.x * border_size.x), frame_size.y + border_size.y), frame_size)
            frame_rect.topleft += pg.Vector2(block_rect.topleft)

            frame = trainer_back_parent_surf.subsurface(frame_rect).copy()
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

    def _load_surfaces(self, sprite_path: str | os.PathLike):
        self._sprite_sets = {
            Movement.walking: SpriteSet2(
                os.path.join(sprite_path, "Walking Sprites.png"), 12, pg.Vector2(34, 50), pg.Vector2(0, 0)
            ),
            Movement.running: SpriteSet2(
                os.path.join(sprite_path, "Running Sprites.png"), 12, pg.Vector2(40, 50), pg.Vector2(0, 0)
            )
        }

        battle_animation_dir = "assets/sprites/trainers/battle_start"
        frame_durations = [1000, 200, 200, 200, 200]
        self.battle_animation = BattleAnimation(battle_animation_dir, durations=frame_durations, scale=2)
        self.reset_battle_sprite()

    def _clear_surfaces(self):
        self._sprite_sets = None
        self.battle_animation = None
        self.battle_sprite.image = None
