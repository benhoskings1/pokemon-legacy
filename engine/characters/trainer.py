import pygame as pg
import json

from team import Team

from general.direction import Direction

from engine.characters.character import Character, CharacterTypes, AttentionBubble, Movement


class Trainer(Character):
    """
    Returns a Trainer Object. 
    """

    battle_font_mapping = {
        CharacterTypes.player_male: (0, 0),
        CharacterTypes.player_female: (1, 0),
        CharacterTypes.youngster: (3, 0),
        CharacterTypes.lass: (4, 0),
    }

    battle_back_mapping = {
        CharacterTypes.player_male: (0, 0),
        CharacterTypes.player_female: (1, 0),
        CharacterTypes.barry: (0, 1),
        CharacterTypes.riley: (0, 2),
    }

    with open("game_data/game_config/trainer_teams.json") as f:
        trainer_data = json.load(f)

    def __init__(self, properties: dict=None, team: None | Team=None, is_player=False, scale: float = 1.0):
        """
        Trainer Class
        """

        Character.__init__(self, properties, scale)

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
    def get_battle_front(cls, trainer_type: CharacterTypes, bg_colour=None, scale=1) -> pg.Surface:
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
