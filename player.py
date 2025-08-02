import os
from enum import Enum

import pygame as pg

from general.Direction import Direction
from Sprites.SpriteSet import SpriteSet2
from general.utils import get_image_frame

from battle_animation import BattleAnimation


class Movement(Enum):
    walking = 0
    running = 1


class Player(pg.sprite.Sprite):
    def __init__(self, sprite_path: os.PathLike | str, position=pg.Vector2(0, 0), tile_size=32):
        """
        
        :param sprite_path:
        :param position:
        """
        # ======== INITIALISATION =======
        pg.sprite.Sprite.__init__(self)
        self.sprite_type = "player"
        self.id = "benji"

        self.spriteIdx = 3
        self.facingDirection = Direction.down

        self._leg = True
        self._sprite_sets: dict | None = None
        self._moving = False

        self.movement = Movement.walking

        battle_animation_dir = "assets/sprites/trainers/battle_start"
        frame_durations = [1000, 200, 200, 200, 200]
        self.battle_animation = BattleAnimation(battle_animation_dir, durations=frame_durations, scale=2)

        self.load_surfaces(sprite_path)
        self.position = position
        self.blit_rect = self.image.get_rect()
        self.rect = pg.Rect(self.position * tile_size, (tile_size, tile_size))

        self.steps = 0

    def __getstate__(self):
        self._sprite_sets = None
        self.battle_animation = None

    @property
    def sprites(self):
        return self._sprite_sets[self.movement].sprites

    @property
    def image(self) -> pg.Surface | None:
        return self.sprites[
            self.spriteIdx + (0 if not self._moving else (1 if self._leg else 2))
        ] if self.sprites is not None else None

    def clear_surfaces(self):
        self._sprite_sets = None
        self.battle_animation = None

    def load_surfaces(self, sprite_path: str | os.PathLike):
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

        self.update()
