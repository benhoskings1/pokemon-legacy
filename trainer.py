import os

from enum import Enum
import pygame as pg
import json

from team import Team
from Sprites.SpriteSet import SpriteSet2
from maps.game_obejct import GameObject

from Image_Processing.ImageEditor import ImageEditor

from battle_animation import BattleAnimation

import cv2


class CharacterTypes(Enum):
    player = 0
    npc = 1
    trainer = 2


class TrainerTypes(Enum):
    player_male = "player_male"
    player_female = "player_female"
    pokecenter_lady = "pokecenter_lady"
    barry = "barry"
    cheryl = "cheryl"
    riley = "riley"
    youngster = "youngster"
    lass = "lass"
    farmer = "farmer"


class Movement(Enum):
    walking = 0
    running = 1


class Direction(Enum):
    down = pg.Vector2(0, 1)
    up = pg.Vector2(0, -1)
    left = pg.Vector2(-1, 0)
    right = pg.Vector2(1, 0)


class AttentionBubble(pg.sprite.Sprite):
    def __init__(self, trainer, scale=1.0):
        pg.sprite.Sprite.__init__(self)
        self.trainer = trainer
        self.scale = scale

        self.image = pg.image.load("assets/sprites/trainers/attention_bubble.png").convert_alpha()

        if scale != 1.0:
            self.image = pg.transform.scale(self.image, pg.Vector2(self.image.get_size()) * scale)

        self.rect = self.image.get_rect()

        self.position = pg.Vector2(0, 100)


class NPC(GameObject):
    # load in the sprite surfaces
    # npc_parent_surf = pg.image.load('assets/sprites/trainers/all_npcs.png')
    npc_parent_surf_cv2 = cv2.imread('assets/sprites/trainers/all_npcs_2.png', cv2.IMREAD_UNCHANGED)

    trainer_front_parent_surf = pg.image.load('assets/sprites/trainers/trainer_front_images.png')
    trainer_back_parent_surf = pg.image.load('assets/sprites/trainers/trainer_front_images.png')

    trainer_sprite_mapping = {
        TrainerTypes.player_male: (0, 0),
        TrainerTypes.youngster: (1, 1),
        TrainerTypes.lass: (9, 2),
        TrainerTypes.pokecenter_lady: (6, 7),
        TrainerTypes.farmer: (10, 0)
    }

    # colours given in BGR for opencv
    bag_colour_mapping = {
        TrainerTypes.youngster: [96, 128, 32],
        TrainerTypes.farmer: [96, 128, 32],
        TrainerTypes.pokecenter_lady: pg.Color((80, 128, 64, 255)),
        TrainerTypes.lass: pg.Color((96, 128, 32, 255)),
    }

    direction_dict = {
        Direction.up: 0,
        Direction.down: 3,
        Direction.left: 6,
        Direction.right: 9,
    }

    editor = ImageEditor()

    def __init__(self, properties: dict = None, scale: float = 1.0, map_scale: int | float = 1.0):
        GameObject.__init__(self, pg.Rect(0, 0, 800, 800), obj_id=0, solid=True, scale=scale, custom_image=True)

        self.scale = scale
        self.map_scale = map_scale

        if "npc_type" not in properties.keys():
            npc_type = "youngster"
        elif properties["npc_type"] not in TrainerTypes:
            npc_type = "youngster"
        else:
            npc_type = properties["npc_type"]

        self.trainer_type: TrainerTypes = TrainerTypes[npc_type]
        self.name: str = "" if not properties else properties.get("npc_name")

        self._sprite_sets: dict[Movement, list[pg.Surface]]
        self._leg: bool = True
        self._moving: bool = False

        if properties and "facing_direction" in properties:
            self.facing_direction = Direction[properties["facing_direction"]]
        else:
            self.facing_direction = Direction.down

        self.movement: Movement = Movement.walking

        self.map_positions = {}

    @property
    def _sprite_idx(self):
        return self.direction_dict[self.facing_direction]

    @property
    def sprites(self):
        sprites = self._sprite_sets[self.movement]
        return sprites.sprites if isinstance(sprites, SpriteSet2) else sprites

    @property
    def image(self) -> pg.Surface | None:
        return self.sprites[
            self._sprite_idx + (0 if not self._moving else (1 if self._leg else 2))
        ] if self.sprites is not None else None

    @property
    def map_rects(self):
        return {map_: pg.Rect(
            pg.Vector2(pos.x * map_.tilewidth, pos.y * map_.tileheight),
            map_.tile_size) for map_, pos in self.map_positions.items()
        }

    @classmethod
    def get_npc_frames(
            cls,
            trainer_type: TrainerTypes,
            bg_colour: None | pg.Color = None,
            order_frames: bool = True,
            scale: int | float = 1.0
    ):
        """
        Loads each frame for an NPC walking

        :param trainer_type:
        :param bg_colour:
        :param order_frames:
        :param scale: value to scale the surface by
        :return: frames
        """
        trainer_block_size = pg.Vector2(96, 128)
        frame_size = pg.Vector2(32, 32)
        block_location = cls.trainer_sprite_mapping[trainer_type]
        block_rect = pg.Rect((trainer_block_size.x * block_location[0],
                              trainer_block_size.y * block_location[1]),
                             trainer_block_size)

        frames: list[pg.Surface] = []
        for frame_idx in range(12):
            y, x = divmod(frame_idx, 3)
            frame_rect = pg.Rect((x * frame_size.x, y * frame_size.y), frame_size)
            frame_rect.topleft += pg.Vector2(block_rect.topleft)
            frame = cls.npc_parent_surf_cv2[frame_rect.top:frame_rect.bottom, frame_rect.left:frame_rect.right, :]

            if bg_colour is not None:
                cls.editor.loadData(frame)
                cls.editor.transparent_where_color(bg_colour[:3], overwrite=True)
                cls.editor.crop_transparent_borders(overwrite=True)

                frame = cls.editor.createSurface()

            else:

                if frame_idx == 0:
                    # frame = frame.convert_alpha()
                    print(f"consider mapping {trainer_type}: pg.Color({frame[0, 0, :]}),")

                cls.editor.loadData(frame)
                frame = cls.editor.createSurface()

            if scale != 1.0:
                frame = pg.transform.scale(frame, pg.Vector2(frame.get_size()) * scale)

            frames.append(frame)

        if order_frames:
            new_order = [0, 2, 10, 5, 11, 8, 6, 3, 9, 1, 4, 7]
            return [frames[i] for i in new_order]

        return frames

    def _load_surfaces(self):
        if self.trainer_type in self.bag_colour_mapping:
            bg_colour = self.bag_colour_mapping[self.trainer_type]
        else:
            bg_colour = None

        self._sprite_sets = {Movement.walking: self.get_npc_frames(
            self.trainer_type, bg_colour=bg_colour, scale=self.scale
        )}

    def _clear_surfaces(self):
        self._sprite_sets = None

    def __repr__(self):
        return f"NPC('{self.trainer_type.name.title()} {self.name.title()}. {self.map_positions} {self.map_rects}')"


class Trainer(NPC):
    """
    Returns a Trainer Object. 
    """

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

    with open("game_data/trainer_teams.json") as f:
        trainer_data = json.load(f)

    def __init__(self, properties: dict=None, team: None | Team=None, is_player=False, scale: float = 1.0):
        """
        Trainer Class
        """

        NPC.__init__(self, properties, scale)

        self.trainer_id = properties["trainer_id"]

        self.is_player = is_player

        self.battle_sprite = pg.sprite.Sprite()

        # load team data
        self.team: Team = team if team else Team(data=self.trainer_data[self.trainer_id])

        # display config
        self.map_location = ...

        # dict to hold trainer position and blit rect on each map

        self.battled = False
        self.attention_bubble = None

        self._load_surfaces()

    def __repr__(self):
        return f"Trainer('{self.trainer_type.name.title()} {self.name.title()}',{self.team})"

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
    def get_battle_front(cls, trainer_type: TrainerTypes, bg_colour=None, scale=1) -> pg.Surface:
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
        if self.trainer_type in self.bag_colour_mapping:
            bg_colour = self.bag_colour_mapping[self.trainer_type]
        else:
            bg_colour = None

        self._sprite_sets = {Movement.walking: self.get_npc_frames(
            self.trainer_type, bg_colour=bg_colour, scale=self.scale
        )}

        self.battle_sprite.image = self.get_battle_front(
            self.trainer_type, scale=self.scale, bg_colour=(147, 187, 236, 255)
        )
        self.battle_sprite.rect = pg.Rect(pg.Vector2(152, 10) * self.scale, self.battle_sprite.image.get_size())

        self.blit_rect = self.rect.copy().move(4, 0)

        self.attention_bubble = AttentionBubble(self, scale=self.scale)
        self.attention_bubble.rect.midbottom = self.rect.midtop

    def _clear_surfaces(self):
        self._sprite_sets = None
        self.battle_sprite.image = None


class Player2(Trainer):
    def __init__(
            self,
            position: tuple[int, int] | list[int] | pg.Vector2,
            team: Team,
            scale: float = 1.0
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

        back_frames = self.get_battle_back(self.trainer_type, scale=scale, bg_colour=(147, 187, 236, 255))

        self.battle_sprite.image = back_frames[0]
        self.blit_rect = self.image.get_rect()

        self.reset_battle_sprite()

        self.steps = 0

    def __repr__(self):
        return f"Player {self.trainer_type.name} at {self.map_rects}"

    @classmethod
    def get_battle_back(cls, trainer_type, bg_colour=None, scale: float = 1.0):
        """
        Loads each back frame for a player in a battle

        :param trainer_type:
        :param bg_colour:
        :param scale: value to scale the surface by
        :return: frames
        """

        frame_size, border_size = pg.Vector2(80, 80), pg.Vector2(1, 18)
        trainer_block_size = pg.Vector2((frame_size.x + border_size.x) * 5, frame_size.y)

        block_location = cls.battle_back_mapping[trainer_type]
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
