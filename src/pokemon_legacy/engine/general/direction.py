from enum import Enum

import pygame as pg


class Direction(Enum):
    down = pg.Vector2(0, 1)
    up = pg.Vector2(0, -1)
    left = pg.Vector2(-1, 0)
    right = pg.Vector2(1, 0)


opposite_direction_mapping = {
    Direction.down : Direction.up,
    Direction.up : Direction.down,
    Direction.left : Direction.right,
    Direction.right : Direction.left,
}