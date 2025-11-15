import os

from enum import Enum
import pygame as pg

from Sprites.SpriteSet import SpriteSet2
from maps.game_obejct import GameObject

from general.direction import Direction
from Image_Processing.ImageEditor import ImageEditor

import cv2


class CharacterTypes(Enum):
    player_male = "player_male"
    player_female = "player_female"
    pokecenter_lady = "pokecenter_lady"
    barry = "barry"
    cheryl = "cheryl"
    riley = "riley"
    youngster = "youngster"
    lass = "lass"
    farmer = "farmer"
    player_mum = 9
    professor_rowan = 10
    twinleaf_guard = 11


class Movement(Enum):
    walking = 0
    running = 1


class AttentionBubble(pg.sprite.Sprite):
    def __init__(self, character, scale=1.0):
        pg.sprite.Sprite.__init__(self)
        self.character = character
        self.scale = scale

        self.image = pg.image.load("assets/sprites/trainers/attention_bubble.png").convert_alpha()

        if scale != 1.0:
            self.image = pg.transform.scale(self.image, pg.Vector2(self.image.get_size()) * scale)

        self.rect = self.image.get_rect()

        self.position = pg.Vector2(0, 100)


class Character(GameObject):
    # load in the sprite surfaces
    npc_parent_surf_cv2 = cv2.imread('assets/sprites/trainers/all_npcs_2.png', cv2.IMREAD_UNCHANGED)

    character_front_parent_surf = pg.image.load('assets/sprites/trainers/trainer_front_images.png')
    character_back_parent_surf = pg.image.load('assets/sprites/trainers/trainer_front_images.png')

    character_sprite_mapping = {
        CharacterTypes.player_male: (0, 0),
        CharacterTypes.youngster: (1, 1),
        CharacterTypes.lass: (9, 2),
        CharacterTypes.pokecenter_lady: (6, 7),
        CharacterTypes.farmer: (10, 0),
        CharacterTypes.player_mum: (9, 3),
        CharacterTypes.professor_rowan: (10, 1),
        CharacterTypes.twinleaf_guard: (5, 1),

    }

    # colours given in BGR for opencv
    bag_colour_mapping = {
        CharacterTypes.youngster: [96, 128, 32],
        CharacterTypes.farmer: [96, 128, 32],
        CharacterTypes.pokecenter_lady: [80, 128, 64],
        CharacterTypes.lass: [96, 128, 32],
        CharacterTypes.player_mum: [64, 104, 120],
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
        elif properties["npc_type"] not in [t.name for t in CharacterTypes]:
            print("falling back to youngster npc")
            npc_type = "youngster"
        else:
            npc_type = properties["npc_type"]

        self.character_type: CharacterTypes = CharacterTypes(npc_type)
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
            character_type: CharacterTypes,
            bg_colour: None | pg.Color = None,
            order_frames: bool = True,
            scale: int | float = 1.0
    ):
        """
        Loads each frame for an NPC walking

        :param character_type:
        :param bg_colour:
        :param order_frames:
        :param scale: value to scale the surface by
        :return: frames
        """
        character_block_size = pg.Vector2(96, 128)
        frame_size = pg.Vector2(32, 32)
        block_location = cls.character_sprite_mapping[character_type]
        block_rect = pg.Rect((character_block_size.x * block_location[0],
                              character_block_size.y * block_location[1]),
                             character_block_size)

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
                    print(f"consider mapping {character_type}: pg.Color({frame[0, 0, :]}),")

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
        if self.character_type in self.bag_colour_mapping:
            bg_colour = self.bag_colour_mapping[self.character_type]
        else:
            bg_colour = None

        self._sprite_sets = {Movement.walking: self.get_npc_frames(
            self.character_type, bg_colour=bg_colour, scale=self.scale
        )}

    def _clear_surfaces(self):
        self._sprite_sets = None

    def __repr__(self):
        return f"NPC('{self.character_type.name.title()} {self.name.title()}. {self.map_positions} {self.map_rects}')"
