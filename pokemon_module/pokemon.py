import datetime
import pickle
from enum import Enum
from typing import Any

from math import floor
import random

import cv2
import pandas as pd
import pygame as pg
from pandas import DataFrame

from general.utils import load_gif
from general.Move import Move2
from general.Animations import Animations, createAnimation
from general.Move import getMove
from general.ability import Ability
from Image_Processing.ImageEditor import ImageEditor


with open("game_data/pokedex/LocalDex/LocalDex.pickle", 'rb') as file:
    pokedex: pd.DataFrame = pickle.load(file)

oldPokedex = pd.read_csv("game_data/pokedex/Local Dex.tsv", delimiter='\t', index_col=1)
national_dex = pd.read_csv("game_data/pokedex/NationalDex/NationalDex.tsv", delimiter='\t', index_col=0)

editor = ImageEditor()


class StatusEffect(Enum):
    Burned = 0
    Frozen = 1
    Paralysed = 2
    Poisoned = 3
    Sleeping = 4
    Confusion = 5


class Stats:
    def __init__(self, health=0, attack=0, defence=0, spAttack=0, spDefence=0, speed=0, exp=0):
        self.health = health
        self.attack = attack
        self.defence = defence
        self.spAttack = spAttack
        self.spDefence = spDefence
        self.speed = speed
        self.exp = exp

    @staticmethod
    def _calc_stat(base, ev, level, is_hp=False):
        ev_part = ev + ev // 4
        if is_hp:
            return floor(((2 * base + ev_part) * level) / 100 + level + 10)
        return floor(((2 * base + ev_part) * level) / 100 + 5)

    @classmethod
    def from_base_and_evs(cls, base_stats, evs, level, exp=0):
        """
        Factory for Stats from base stats + EVs.

        :param base_stats: iterable [HP, Atk, Def, SpAtk, SpDef, Speed]
        :param evs: iterable [HP EV, Atk EV, ...]
        :param level: Pokémon level
        :param exp: current exp
        :return: Stats instance
        """
        health = cls._calc_stat(base_stats[0], evs[0], level, is_hp=True)
        others = [cls._calc_stat(b, e, level) for b, e in zip(base_stats[1:], evs[1:])]
        return cls(health, *others, exp)

    def __sub__(self, other):
        new_dict = {k: v1 - other.__dict__[k] for k, v1 in self.__dict__.items()}
        return Stats(**new_dict)

    def __str__(self):
        return f"{[(k, v) for k, v in self.__dict__.items()]}"

    def __iter__(self):
        for val in self.get_values():
            yield val

    def __getitem__(self, key):
        return self.get_values()[key]

    def get_values(self):
        return [self.health, self.attack, self.defence, self.spAttack, self.spDefence, self.speed]


class StatStages:
    def __init__(self, attack=0, defence=0, spAttack=0, spDefence=0, speed=0, accuracy=0, evasion=0):
        self.attack = attack
        self.defence = defence
        self.spAttack = spAttack
        self.spDefence = spDefence
        self.speed = speed
        self.accuracy = accuracy
        self.evasion = evasion

    def __str__(self):
        return (f"{self.attack}, {self.defence}, {self.spAttack}, {self.spDefence}, "
                f"{self.speed}, {self.accuracy}, {self.evasion}")

    def __repr__(self):
        return (f"{self.attack}, {self.defence}, {self.spAttack}, {self.spDefence}, "
                f"{self.speed}, {self.accuracy}, {self.evasion}")


class PokemonSpriteSmall(pg.sprite.Sprite):
    def __init__(self, frames, pos=pg.Vector2(0, 0)):
        pg.sprite.Sprite.__init__(self)
        self.frames = frames
        self.frame_idx = 0
        self.image = self.frames[0]
        self.rect = self.image.get_rect()
        self.rect.center = pos
        self.sprite_type = "pokemon_small"
        self.id = "small"

    def update(self):
        self.toggle_image()

    def toggle_image(self):
        self.frame_idx = (self.frame_idx + 1) % len(self.frames)
        self.image = self.frames[self.frame_idx]

    @staticmethod
    def is_clicked():
        return None


class PokemonSprite(pg.sprite.Sprite):
    def __init__(self, pk_id, shiny, friendly=True, visible=False):
        pg.sprite.Sprite.__init__(self)

        self.images = Pokemon.get_images(pk_id, shiny=shiny)
        self.friendly = friendly

        self.image = self.images["back"] if friendly else self.images["front"]
        self.rect = self.image.get_rect()

        # numpy and pygame use different x-y coordinate systems
        self.mask = pg.surfarray.pixels_alpha(self.image).transpose()

        self.intro_animation = None

        self.animations: dict[str, None | list[pg.Surface]] = {
            "intro": None,
            "stat_raise": None,
            "stat_lower": None,
        }

        self.load_stat_stage_animations()

        self.visible = visible

    def load_stat_stage_animations(self):
        for direction in ["raise", "lower"]:
            frames = load_gif(f"assets/battle/main_display/stat_{direction}.gif",
                              bit_mask=self.mask, opacity=150, scale=2)
            self.animations[f"stat_{direction}"] = [self.image.copy() for _ in range(len(frames))]
            for frame_idx in range(len(frames)):
                self.animations[f"stat_{direction}"][frame_idx].blit(frames[frame_idx], (0, 0))


class Pokemon(pg.sprite.Sprite):
    # battle maps
    crit_chance = {0: 1 / 16, 1: 1 / 8, 2: 1 / 4, 3: 1 / 3, 4: 1 / 2}
    stage_multipliers = {idx: (idx + 2 if idx > 0 else 2) / (abs(idx) + 2 if idx < 0 else 2) for idx in range(-6, 7)}

    # pokemon sprites
    all_sprites = cv2.imread("Sprites/Pokemon/Gen_IV_Sprites.png", cv2.IMREAD_UNCHANGED)
    small_sprites = cv2.imread("Sprites/Pokemon/Gen_IV_Small_Sprites.png", cv2.IMREAD_UNCHANGED)

    # pokemon data
    natures = pd.read_csv("game_data/natures.tsv", delimiter='\t', index_col=0)
    level_up_values: DataFrame = pd.read_csv("game_data/level_up_exp.tsv", delimiter='\t', index_col=6)
    effectiveness = pd.read_csv("game_data/effectiveness.csv", index_col=0)

    def __init__(self, name, level=None, exp=None, moves=None, health=None, status=None,
                 EVs=None, IVs=None, gender=None, nature=None, ability_name=None, stat_stages=None,
                 friendly=False, shiny=None, visible=False, catch_location=None, catch_level=None,
                 catch_date=None, animations=None):
        # ===== Load Default Data ======
        data = pokedex.loc[name]
        oldData = oldPokedex.loc[name]

        self.name = name
        self.ID = data.Local_Num
        self.species = national_dex.loc[name, "Species"]
        self.growthRate = data.Growth_Rate
        self.catchRate = data.Catch_Rate
        self.EVYield = data.EV_Yield
        self.moveData = data.Learnset

        if isinstance(data.Type, str):
            self.type1 = data.Type
            self.type2 = None
        else:
            # will be in as a tuple
            self.type1 = data.Type[0]
            self.type2 = data.Type[1]

        exp: int = int(self.level_up_values.loc[level, self.growthRate]) if exp is None else exp
        level: int = random.randint(1, 10) if level is None else level

        self.level, self.exp = level, exp
        self.level_exp: int = int(self.level_up_values.loc[level, self.growthRate])
        self.level_up_exp: int = int(self.level_up_values.loc[level+1, self.growthRate])
        self.evolveLevel: int = oldData.Evolve_Level

        if moves is None:
            possible_moves = [name for name, level in self.moveData if level <= self.level]
            move_names = random.choices(possible_moves, k=min([4, len(possible_moves)]))
            move_pps = [None] * len(move_names)
        else:
            move_names = [move["name"] for move in moves]
            move_pps = [move["pp"] if "pp" in move else None for move in moves]

        self.moves = [getMove(name, move_pp) for name, move_pp in zip(move_names, move_pps)]

        self.EVs = EVs if EVs is not None else [0] * 6
        self.IVs = IVs if IVs is not None else [random.randint(0, 31) for _ in range(6)]

        self.stats = Stats(exp=data.Base_Exp)
        self.update_stats()

        self.health = health if health else self.stats.health
        self.friendly = friendly

        if gender:
            self.gender = gender.lower()
        else:
            genders = data.Gender
            self.gender = ("male" if random.random() * 100 < genders[0] else "female") if genders else None

        ability_name = ability_name if ability_name else random.choice(data.Abilities[:len(data.Abilities)])
        self.ability = Ability(name=ability_name)

        self.nature = nature if nature else self.natures.loc[random.randint(0, 24)].Name
        self.shiny = shiny if shiny else (True if random.randint(0, 4095) == 0 else False)

        self.sprite: None | PokemonSprite = None

        self._clear_surfaces = False
        self.images: None | dict[str, pg.Surface] = None

        self.smallImage: None | pg.Surface = None
        self.animation = None
        self.small_animation = None

        self.load_images(animations=animations)

        self.displayImage = self.image.copy()
        self.sprite_mask = pg.mask.from_surface(self.image)

        self.statStages = StatStages(**stat_stages) if stat_stages else StatStages()
        self.status = StatusEffect(status) if status else None

        self.item = None

        self.catchLocation = catch_location
        self.catchLevel = catch_level
        if catch_date:
            year, month, day = catch_date.split("-")
            self.catchDate = datetime.date(int(year), int(month), int(day))
        else:
            self.catchDate = None

        # loading for the first time from the start team
        if self.friendly and (not catch_date and not catch_location and not catch_level):
            self.catchLocation = None
            self.catchLevel = self.level
            self.catchDate = datetime.datetime.now()

        # =========== SPRITE INITIALISATION =======
        pg.sprite.Sprite.__init__(self)
        self.sprite_type = "pokemon"
        self.id = name
        self.visible = visible

    def __str__(self):
        return f"Lv.{self.level} {self.name} caught on {self.catchDate}.\nIt likes playing \n{self.stats}"

    def __repr__(self):
        return f"Pokemon({self.name},Lv{self.level},Type:{self.type1}, IVs:{self.IVs})"

    def __getstate__(self):
        self._clear_images()
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.load_images()

    @classmethod
    def get_images(cls, local_id, crop=False, shiny=False) -> dict[str, pg.Surface]:
        """ Return the font, back and small images for the Pokémon """
        grid_width, per_row = 5, 32

        image_size = pg.Vector2(80, 80)

        y, x = divmod(local_id - 1, int(per_row / 2))

        images = {}

        pk_block = pg.Rect((x * (80 + grid_width) * 2 + grid_width, y * (80 + grid_width) * 2 + grid_width),
                           image_size * 2 + pg.Vector2(grid_width, grid_width))

        front_rect = pg.Rect(pk_block.topleft, image_size)
        back_rect = pg.Rect(pk_block.topleft + pg.Vector2(image_size.x + grid_width, 0), image_size)

        if shiny:
            front_rect = front_rect.move(pg.Vector2(0, grid_width + image_size.y))
            back_rect = back_rect.move(pg.Vector2(0, grid_width + image_size.y))

        small_rect = pg.Rect(pg.Vector2(x * (32 + grid_width) + grid_width, y * (32 + grid_width) + grid_width),
                             (32, 32))

        images["front"] = cls.all_sprites[front_rect.top:front_rect.bottom, front_rect.left:front_rect.right, :]
        images["back"] = cls.all_sprites[back_rect.top:back_rect.bottom, back_rect.left:back_rect.right, :]
        images["small"] = cls.small_sprites[small_rect.top:small_rect.bottom, small_rect.left:small_rect.right, :]

        for k, v in images.items():
            editor.loadData(v)
            if crop and k != "small":
                editor.crop_transparent_borders(overwrite=True)
            editor.scaleImage((2, 2), overwrite=True)
            images[k] = editor.createSurface()

        return images

    @property
    def rect(self) -> pg.Rect:
        img_rect = self.image.get_rect()
        img_rect.midbottom = pg.Vector2(64, 153) * 2 if self.friendly else pg.Vector2(192, 90) * 2
        return img_rect

    @property
    def is_koed(self) -> bool:
        """ Return True if the Pokémon has no health left """
        return self.health <= 0

    @property
    def image(self) -> None | pg.Surface:
        if self._clear_surfaces:
            return None
        return self.images["back"] if self.friendly else self.images["front"]

    @image.setter
    def image(self, img: pg.Surface) -> None:
        self.images["front"] = img

    def _get_move_damage(self, move: Move2, target, ignore_modifiers=False) -> float:
        """ Return the damage that the move will do to the target"""

        if not move.power:
            return 0

        attack_stat = self.stats.attack if move.category == "Physical" else self.stats.spAttack
        defence_stat = self.stats.defence if move.category == "Physical" else self.stats.spDefence

        attack_stage = self.statStages.attack
        defence_stage = target.statStages.defence

        if ignore_modifiers:
            if defence_stage < 0:
                # no modification for positive defence stat
                defence_stat *= self.stage_multipliers[target.statStages.defence]
            if attack_stage > 0:
                # no modification for negative attack stat
                attack_stat *= self.stage_multipliers[self.statStages.attack]
        else:
            defence_stat *= self.stage_multipliers[target.statStages.defence]
            attack_stat *= self.stage_multipliers[self.statStages.attack]

        return floor(floor(floor(2 * self.level / 5) + 2) * move.power *
                               floor(attack_stat / defence_stat)) / 50

    def use_move(self, move: Move2, target):
        crit_stage = 0

        if move.effect:
            inflict_condition, modify, hits, heal = move.effect.getEffect()

        else:
            inflict_condition = None
            modify = None
            hits = 1
            heal = 0

        num = random.randint(0, 99) / 100
        crit, critical = (True, 2) if num < self.crit_chance[crit_stage] else (False, 1)

        base_damage: float = self._get_move_damage(move, target, crit)

        burn = 0.5 if self.status == StatusEffect.Burned and move.type == "Physical" else 1

        screen, targets, weather, FF = 1, 1, 1, 1

        damage = base_damage * burn * screen * targets * weather * FF + 2

        item, first = 1, 1

        rand = random.randint(85, 100) / 100

        stab = 1.5 if (move.type == self.type1 or move.type == self.type2) else 1

        type1 = self.effectiveness.loc[str.upper(move.type), target.type1]
        type2 = self.effectiveness.loc[str.upper(move.type), target.type2] if target.type2 else 1

        SRF, EB, TL, Berry = 1, 1, 1, 1

        damage: float = damage * critical * item * first * rand * stab * type1 * type2 * SRF * EB * TL * Berry

        move.PP -= 1

        damage = floor(damage)

        if move.category == "Status":
            damage = 0

        return damage, type1 * type2, inflict_condition, heal, modify, hits, crit

    def updateEVs(self, name) -> None:
        data = pokedex.loc[name]
        EVYield = data.EV_Yield
        for [idx, value] in enumerate(EVYield):
            self.EVs[idx] += value

    def get_faint_xp(self) -> float:
        """ Return the exp yield of the pokemon on ko """
        a, e, f, L, Lp, p, s, t, v = 1, 1, 1, 1, 1, 1, 1, 1, 1

        b = self.stats.exp
        L = self.level

        exp = (a * t * b * e * L * p * f * v) / (7 * s)
        return exp

    def update_stats(self):
        data = pokedex.loc[self.name]
        base_stats = data.Stats  # [HP, Atk, Def, SpAtk, SpDef, Speed]
        self.stats = Stats.from_base_and_evs(base_stats, self.EVs, self.level, self.stats.exp)

    def level_up(self):
        self.level += 1
        self.level_exp = int(self.level_up_values.loc[self.level, self.growthRate])
        self.level_up_exp = int(self.level_up_values.loc[self.level + 1, self.growthRate])
        self.update_stats()

    def get_new_moves(self) -> list[Move2]:
        """ Return a list of new moves for this level """
        return [getMove(move_name) for move_name, level in self.moveData if level == self.level]

    def get_evolution(self):
        return oldPokedex[oldPokedex["ID"] == self.ID + 1].index[0]

    def _clear_images(self) -> None:
        self.animation = None

        self.displayImage = None

        self.smallImage = None
        self.small_animation = None
        self.sprite.kill()
        self.sprite = None
        self.sprite_mask = None

        self.images = None

    def load_images(self, animations: None | Animations = None):
        """ Load images """
        self.images = self.get_images(self.ID, crop=True, shiny=self.shiny)

        self.smallImage = self.images["small"]
        if not animations:
            animations = createAnimation(self.name)

        self.small_animation = animations.small
        self.animation = animations.front

        self.sprite = PokemonSprite(self.ID, self.shiny, friendly=self.friendly)

    def reset_stat_stages(self) -> None:
        self.statStages = StatStages()

    def restore(self) -> None:
        self.health = self.stats.health
        self.status = None

        for move in self.moves:
            move.PP = move.maxPP

    # ========== PICKLE DATA  =============
    def get_json_data(self) -> dict[str, Any]:
        status = self.status.value if self.status else None

        data = {
            "name": self.name, "level": self.level, "exp": self.exp,
            "moves": [move.get_json() for move in self.moves], "health": self.health,
            "status": status, "EVs": self.EVs, "IVs": self.IVs,
            "gender": self.gender, "nature": self.nature, "ability_name": self.ability.name,
            "stat_stages": self.statStages.__dict__,
            "friendly": self.friendly, "shiny": self.shiny, "visible": self.visible,
            "catch_date": self.catchDate.strftime("%Y-%m-%d"),
            "catch_location": self.catchLocation,
            "catch_level": self.catchLevel
        }

        return data
