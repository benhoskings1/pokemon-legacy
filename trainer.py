import os
from enum import Enum

import cv2
import pygame as pg
import json

from team import Team

from general.Direction import Direction
from Sprites.SpriteSet import SpriteSet2


class TrainerTypes(Enum):
    player_male = "player_male"
    player_female = "player_female"
    youngster = "youngster"
    lass = "lass"


class Movement(Enum):
    walking = 0
    running = 1

trainer_sprite_mapping = {
    TrainerTypes.player_male: (0, 0),
    TrainerTypes.youngster: (1, 1),
    TrainerTypes.lass: (9, 2),
}

bag_colour_mapping = {
    TrainerTypes.youngster: pg.Color((32, 128, 96, 255)),
    TrainerTypes.lass: pg.Color((32, 128, 96, 255)),
}

npc_parent_surf = pg.image.load('assets/sprites/trainers/all_npcs.png')


with open("game_data/trainer_teams.json") as f:
    trainer_data = json.load(f)

def get_npc_frames(trainer_type: TrainerTypes, bg_colour: None | pg.Color=None, scale: int | float=1.0):
    """
    Loads each frame for an NPC walking

    :param trainer_type:
    :param bg_colour:
    :param scale: value to scale the surface by
    :return: frames
    """
    trainer_block_size = pg.Vector2(96, 128)
    frame_size = pg.Vector2(32, 32)
    block_location = trainer_sprite_mapping[trainer_type]
    block_rect = pg.Rect((trainer_block_size.x * block_location[0],
                          trainer_block_size.y * block_location[1]),
                         trainer_block_size)

    frames: list[pg.Surface] = []
    for frame in range(12):
        y, x = divmod(frame, 3)
        frame_rect = pg.Rect((x * frame_size.x, y * frame_size.y), frame_size)
        frame_rect.topleft += pg.Vector2(block_rect.topleft)
        frame = npc_parent_surf.subsurface(frame_rect).copy()
        # print(frame.get_at([0, 0]))
        if bg_colour is not None:
            frame = frame.convert_alpha()
            px_array = pg.PixelArray(frame)
            px_array.replace(bg_colour, pg.Color(0, 0, 0, 0), distance=0.05)
            px_array.close()

        if scale != 1.0:
            frame = pg.transform.scale(frame, frame_size*scale)

        frames.append(frame)


    return frames


class TrainerSpriteFrames:
    def __init__(self, trainer_type: TrainerTypes, scale=1):
        self.frames: list[pg.Surface] = get_npc_frames(trainer_type, bag_colour_mapping[trainer_type], scale=scale)


class Trainer(pg.sprite.Sprite):
    def __init__(self, rect: pg.Rect, properties: dict=None, team: None | Team=None):
        pg.sprite.Sprite.__init__(self)

        self.trainer_type = TrainerTypes(properties["npc_type"])
        self.name = "" if not properties else properties["npc_name"]
        self.trainer_id = properties["trainer_id"]

        self.sprite_frames = TrainerSpriteFrames(self.trainer_type, scale=2)
        # 6 is the default frame
        self.image = self.sprite_frames.frames[5]

        # load team data
        self.team = team if team else Team(data=trainer_data[self.trainer_id])

        # display config
        self.map_location = ...
        self.rect = rect
        self.position = pg.Vector2(self.rect.topleft) / 32

        self.battled = False

    def __repr__(self):
        return f"Trainer('{self.trainer_type.name.title()} {self.name.title()}',{self.team})"


class Player2(Trainer):
    def __init__(self, rect: pg.Rect, team: None | Team=None):
        properties = {
            "npc_type": "player_male",
            "npc_name": "Benji",
            "trainer_id": "1001",
        }

        Trainer.__init__(self, rect, properties=properties, team=team)