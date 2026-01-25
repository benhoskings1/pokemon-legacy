import pygame as pg
from pokemon_legacy.engine.general.direction import Direction

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

        self.save_keys = {
            pg.K_1: 1, pg.K_2: 2, pg.K_3: 3, pg.K_4: 4, pg.K_5: 5,
            pg.K_6: 6, pg.K_7: 7, pg.K_8: 8, pg.K_9: 9, pg.K_0: 10
        }
