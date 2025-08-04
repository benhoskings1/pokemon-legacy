from enum import Enum
import pygame as pg
import json

from team import Team


class TrainerTypes(Enum):
    player_male = "player_male"
    player_female = "player_female"
    barry = "barry"
    cheryl = "cheryl"
    riley = "riley"
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

battle_font_mapping = {
    TrainerTypes.player_male: (0, 0),
    TrainerTypes.player_female: (1, 0),
    TrainerTypes.youngster: (3, 0),
    TrainerTypes.lass: (4, 0),
}

battle_back_mapping = {
    TrainerTypes.player_male: (0, 0),
    TrainerTypes.player_female: (1, 0),
    TrainerTypes.barry: (0, 1),
    TrainerTypes.riley: (0, 2),
}

bag_colour_mapping = {
    TrainerTypes.youngster: pg.Color((32, 128, 96, 255)),
    TrainerTypes.lass: pg.Color((32, 128, 96, 255)),
}

npc_parent_surf = pg.image.load('assets/sprites/trainers/all_npcs.png')
trainer_front_parent_surf = pg.image.load('assets/sprites/trainers/trainer_front_images.png')
trainer_back_parent_surf = pg.image.load('assets/sprites/trainers/trainer_front_images.png')


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
    def __init__(self, rect: pg.Rect, properties: dict=None, team: None | Team=None, is_player=False, scale=1):
        pg.sprite.Sprite.__init__(self)

        self.is_player = is_player
        self.scale = scale

        self.trainer_type = TrainerTypes(properties["npc_type"])
        self.name = "" if not properties else properties["npc_name"]
        self.trainer_id = properties["trainer_id"]

        self.sprite_frames = None
        self.image = None

        self.battle_sprite = pg.sprite.Sprite()

        # load team data
        self.team = team if team else Team(data=trainer_data[self.trainer_id])

        # display config
        self.map_location = ...
        self.rect = rect
        self.position = pg.Vector2(self.rect.topleft) / 32

        self.battled = False

        self._load_surfaces()

    def __repr__(self):
        return f"Trainer('{self.trainer_type.name.title()} {self.name.title()}',{self.team})"

    def __getstate__(self):
        self._clear_surfaces()
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._load_surfaces()

    @staticmethod
    def get_battle_front(trainer_type: TrainerTypes, bg_colour=None, scale=1) -> pg.Surface:
        block_size, border_size = pg.Vector2(80, 80), pg.Vector2(1, 18)
        block_location = battle_font_mapping[trainer_type]
        image_rect = pg.Rect(
            pg.Vector2(
                block_location[0] * (block_size.x + border_size.x) + border_size.x,
                block_location[1] * (block_size.y + border_size.y) + border_size.y
            ), block_size)

        image = trainer_front_parent_surf.subsurface(image_rect).copy()
        # print(image.get_at([0, 0]))

        if bg_colour is not None:
            image = image.convert_alpha()
            px_array = pg.PixelArray(image)
            px_array.replace(bg_colour, pg.Color(0, 0, 0, 0), distance=0.05)
            px_array.close()

        return pg.transform.scale(image, pg.Vector2(image.get_size()) * scale) if scale != 1.0 else image

    def _load_surfaces(self):
        self.sprite_frames = TrainerSpriteFrames(self.trainer_type, scale=self.scale)
        self.image = self.sprite_frames.frames[5]  # 6 is the default frame

        self.battle_sprite.image = self.get_battle_front(
            self.trainer_type, scale=self.scale, bg_colour=(147, 187, 236, 255)
        )
        self.battle_sprite.rect = pg.Rect(pg.Vector2(152, 10) * self.scale, self.battle_sprite.image.get_size())

    def _clear_surfaces(self):
        self.sprite_frames = None
        self.image = None
        self.battle_sprite.image = None


class Player2(Trainer):
    def __init__(self, rect: pg.Rect, team: None | Team=None, scale=1):
        properties = {
            "npc_type": "player_male",
            "npc_name": "Benji",
            "trainer_id": "1001",
        }

        Trainer.__init__(self, rect, properties=properties, team=team, is_player=True, scale=scale)

        back_frames = self.get_battle_back(self.trainer_type, scale=scale, bg_colour=(147, 187, 236, 255))

        self.battle_sprite.image = back_frames[0]

    @staticmethod
    def get_battle_back(trainer_type, bg_colour=None, scale=1):
        """
        Loads each back frame for a player in a battle

        :param trainer_type:
        :param bg_colour:
        :param scale: value to scale the surface by
        :return: frames
        """

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