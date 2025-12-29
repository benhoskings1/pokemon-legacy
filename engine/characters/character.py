import os
import json
from enum import Enum
import importlib.resources as resources

import cv2
import pygame as pg

from engine.storyline.game_action import GameAction
from engine.game_world.game_obejct import GameObject
from engine.general.direction import Direction

from Sprites.SpriteSet import SpriteSet2
from Image_Processing.ImageEditor import ImageEditor


MODULE_PATH = resources.files(__package__)
ASSET_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'assets')


class CharacterTypes(Enum):
    # players
    player_male = "player_male"
    player_female = "player_female"

    # rival
    rival = 3

    # other
    pokecenter_lady = "pokecenter_lady"
    barry = "barry"
    cheryl = "cheryl"
    riley = "riley"
    youngster = "youngster"
    lass = "lass"
    farmer_male = 8
    player_mum = 9
    rival_mum = 10
    professor_rowan = 11
    twinleaf_guard = 12
    dawn = "dawn"

    lady_1 = 13


class Movement(Enum):
    walking = 0
    running = 1


class AttentionBubble(pg.sprite.Sprite):
    def __init__(self, character, scale=1.0):
        pg.sprite.Sprite.__init__(self)
        self.character = character
        self.scale = scale

        self.image = pg.image.load(os.path.join(ASSET_PATH, "sprites/trainers/attention_bubble.png")).convert_alpha()

        if scale != 1.0:
            self.image = pg.transform.scale(self.image, pg.Vector2(self.image.get_size()) * scale)

        self.rect = self.image.get_rect()

        self.position = pg.Vector2(0, 100)


class Character(GameObject):
    # load in the sprite surfaces
    npc_parent_surf_cv2 = cv2.imread(os.path.join(ASSET_PATH, 'sprites/trainers/all_npcs_2.png'), cv2.IMREAD_UNCHANGED)

    character_sprite_mapping = {
        CharacterTypes.player_male: (0, 0),
        CharacterTypes.player_female: (0, 0),
        CharacterTypes.barry: (8, 7),

        CharacterTypes.youngster: (1, 1),
        CharacterTypes.lass: (9, 2),
        CharacterTypes.pokecenter_lady: (6, 7),
        CharacterTypes.farmer_male: (10, 0),
        CharacterTypes.player_mum: (9, 3),
        CharacterTypes.rival_mum: (6, 4),
        CharacterTypes.professor_rowan: (10, 1),
        CharacterTypes.twinleaf_guard: (1, 4),
        CharacterTypes.lady_1: (8, 6),
        CharacterTypes.dawn: (9, 7),
    }

    direction_dict = {
        Direction.up: 0,
        Direction.down: 3,
        Direction.left: 6,
        Direction.right: 9,
    }

    editor = ImageEditor()

    bg_colour_file = MODULE_PATH / "character_bg_mappings.json"

    with bg_colour_file.open('r', encoding='utf-8') as f:
        character_bg_mapping: dict[str, list[int]] = json.load(f)

    @classmethod
    def get_npc_frames(
            cls,
            character_type: CharacterTypes,
            bg_colour: None | pg.Color = None,
            order_frames: bool = True,
            scale: int | float = 1.0,
            auto_map_bg: bool = True,
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
                    if auto_map_bg:
                        cls.character_bg_mapping[character_type.name] = frame[0, 0, :].tolist()
                        # write back to json file
                        with cls.bg_colour_file.open("w") as f:
                            json.dump(cls.character_bg_mapping, f, indent=4)

                cls.editor.loadData(frame)
                frame = cls.editor.createSurface()

            if scale != 1.0:
                frame = pg.transform.scale(frame, pg.Vector2(frame.get_size()) * scale)

            frames.append(frame)

        if order_frames:
            new_order = [0, 2, 10, 5, 11, 8, 6, 3, 9, 1, 4, 7]
            return [frames[i] for i in new_order]

        return frames

    def __init__(self, properties: dict = None, scale: float = 1.0, map_scale: int | float = 1.0):
        self.character_id = properties.get("character_id", None)

        GameObject.__init__(self, pg.Rect(0, 0, 800, 800), obj_id=self.character_id, solid=True, scale=scale, custom_image=True)

        self.scale = scale
        self.map_scale = map_scale

        # if "character_type" not in properties.keys():
        #     character_type = "youngster"
        if properties["character_type"] not in [t.name for t in CharacterTypes]:
            print(f"character_type {properties['character_type']} not supported. Choose one of {[t.name for t in CharacterTypes]}")
            print("falling back to youngster npc")
            character_type = "youngster"
        else:
            character_type = properties["character_type"]

        self.character_type: CharacterTypes = CharacterTypes[character_type]
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

        self.attention_bubble = None
        self.display_name = None

        self.visible = True

        # load on instance creation
        self._load_surfaces()

    def __repr__(self):
        return f"{self.__class__.__name__}('{self.character_type.name}')"

    # === SERIALISATION ===
    def _load_surfaces(self):
        bg_colour = self.char_bg_mappings.get(self.character_type, None)

        self._sprite_sets = {Movement.walking: self.get_npc_frames(
            self.character_type, bg_colour=bg_colour, scale=self.scale
        )}

        self.attention_bubble = AttentionBubble(self, scale=self.scale)

    def _clear_surfaces(self):
        self.map_positions = {}
        self._sprite_sets = None
        self.attention_bubble = None

        self.kill()

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._load_surfaces()

    def __getstate__(self):
        self._clear_surfaces()
        return self.__dict__

    # === DYNAMIC ATTRIBUTES ====
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

    @property
    def char_bg_mappings(self):
        return {CharacterTypes[c_type]: vals for c_type, vals in self.character_bg_mapping.items()}

    def interaction(self, *args, **kwargs) -> None | list[GameAction]:
        """ hook function """
        return None


class GameActionType(Enum):
    move = 0
    talk = 2
