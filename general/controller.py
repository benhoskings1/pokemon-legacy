import pygame as pg
from general.Direction import Direction

class Controller:
    def __init__(self, a=pg.K_x, b=pg.K_z, x=pg.K_s, y=pg.K_a,
                 up=pg.K_UP, down=pg.K_DOWN, left=pg.K_LEFT, right=pg.K_RIGHT):
        self.a = a
        self.b = b
        self.x = x
        self.y = y
        self.up = up
        self.down = down
        self.left = left
        self.right = right

        self.keys = [a, b, x, up, down, left, right]

        self.move_keys = [up, down, left, right]

        self.direction_key_bindings = {
            self.down: Direction.down,
            self.up: Direction.up,
            self.left: Direction.left,
            self.right: Direction.right
        }
