import os
import importlib.resources as resources

import datetime
import pickle
from enum import Enum
from math import floor
import random

import cv2
import pandas as pd
import pygame as pg

from general.utils import load_gif
from general.Animations import Animations, createAnimation
from general.Move import getMove
from general.ability import Ability
from Image_Processing.ImageEditor import ImageEditor


with open("game_data/pokedex/LocalDex/LocalDex.pickle", 'rb') as file:
    pokedex: pd.DataFrame = pickle.load(file)

oldPokedex = pd.read_csv("game_data/pokedex/Local Dex.tsv", delimiter='\t', index_col=1)
attributes = pd.read_csv("game_data/pokedex/AttributeDex.tsv", delimiter='\t', index_col=1)
effectiveness = pd.read_csv("game_data/Effectiveness.csv", index_col=0)
level_up_values = pd.read_csv("game_data/level_up_exp.tsv", delimiter='\t', index_col=6)
natures = pd.read_csv("game_data/Natures.tsv", delimiter='\t', index_col=0)
national_dex = pd.read_csv("game_data/pokedex/NationalDex/NationalDex.tsv", delimiter='\t', index_col=0)

capWildMoves = True

stageMultipliers = {-6: 2 / 8, -5: 2 / 7, -4: 2 / 6, -3: 2 / 5, -2: 2 / 4, -1: 2 / 3,
                    0: 1, 1: 3 / 2, 2: 4 / 2, 3: 5 / 2, 4: 6 / 2, 5: 7 / 2, 6: 8 / 2}
otherMultipliers = {-6: 33 / 100, -5: 36 / 100, -4: 43 / 100, -3: 50 / 100, -2: 60 / 100, -1: 75 / 100,
                    1: 133 / 100, 2: 166 / 100, 3: 200 / 100, 4: 250 / 100, 5: 266 / 100, 6: 300 / 100}
critChance = {0: 1 / 16, 1: 1 / 8, 2: 1 / 4, 3: 1 / 3, 4: 1 / 2}

allSprites = cv2.imread("Sprites/Pokemon/Gen_IV_Sprites.png", cv2.IMREAD_UNCHANGED)
smallSprites = cv2.imread("Sprites/Pokemon/Gen_IV_Small_Sprites.png", cv2.IMREAD_UNCHANGED)
editor = ImageEditor()


def getImages(ID, shiny=False, crop=True):
    gridWidth, perRow = 5, 32
    pos = pg.Vector2((ID - 1) % (perRow / 2), floor((ID - 1) / (perRow / 2)))

    topleft = pg.Vector2(pos.x * (80 + gridWidth) * 2 + gridWidth, pos.y * (80 + gridWidth) * 2 + gridWidth)
    frontRect = pg.Rect(topleft, (80, 80))
    backRect = frontRect.copy()
    backRect.topleft += pg.Vector2(80 + gridWidth, 0)
    frontShinyRect = frontRect.copy()
    frontShinyRect.topleft += pg.Vector2(0, 80 + gridWidth)
    backShinyRect = frontRect.copy()
    backShinyRect.topleft += pg.Vector2(85, 80 + gridWidth)

    perRow = 16
    pos = pg.Vector2((ID - 1) % perRow, floor((ID - 1) / perRow))
    topLeftSmall = pg.Vector2(pos.x * (32 + gridWidth) + gridWidth, pos.y * (32 + gridWidth) + gridWidth)
    smallRect = pg.Rect(topLeftSmall, (32, 32))

    if not shiny:
        frontData = allSprites[frontRect.top:frontRect.bottom, frontRect.left:frontRect.right, :]
        backData = allSprites[backRect.top:backRect.bottom, backRect.left:backRect.right, :]
    else:
        frontData = allSprites[frontShinyRect.top:frontShinyRect.bottom,
                               frontShinyRect.left:frontShinyRect.right, :]
        backData = allSprites[backShinyRect.top:backShinyRect.bottom,
                              backShinyRect.left:backShinyRect.right, :]

    smallData = smallSprites[smallRect.top:smallRect.bottom,
                             smallRect.left:smallRect.right, :]

    editor.loadData(frontData)
    if crop:
        editor.cropImage(overwrite=True)
    editor.scaleImage((2, 2), overwrite=True)
    frontImage = editor.createSurface()

    editor.loadData(backData)
    if crop:
        editor.cropImage(overwrite=True)
    editor.scaleImage((2, 2), overwrite=True)
    backImage = editor.createSurface()

    editor.loadData(smallData)
    smallScale = 2
    editor.scaleImage((smallScale, smallScale), overwrite=True)
    smallImage = editor.createSurface()

    return frontImage, backImage, smallImage


class StatusEffect(Enum):
    Burned = "Burned"
    Frozen = "Frozen"
    Paralysed = "Paralysed"
    Poisoned = "Poisoned"
    Sleeping = "Sleeping"
    Confusion = "Confusion"


class Stats:
    def __init__(self, health=0, attack=0, defence=0, spAttack=0, spDefence=0, speed=0, exp=0):
        self.health = health
        self.attack = attack
        self.defence = defence
        self.spAttack = spAttack
        self.spDefence = spDefence
        self.speed = speed
        self.exp = exp

    def __sub__(self, other):
        return Stats(
            health=self.health-other.health, attack=self.attack-other.attack, defence=self.defence-other.defence,
            spAttack=self.spAttack - other.spAttack, spDefence=self.spDefence - other.spDefence,
            speed=self.speed - other.speed, exp=self.exp - other.exp
        )

    def __str__(self):
        return f"HP: {self.health}, Atk: {self.attack}, Def: {self.defence}, Sp. Atk: {self.spAttack}, Speed: {self.speed}, Exp: {self.exp}"

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
    def is_clicked(self):
        return None


class PokemonSprite(pg.sprite.Sprite):
    def __init__(self, pk_id, shiny, friendly=True, visible=False):
        pg.sprite.Sprite.__init__(self)

        self.front, self.back, self.small = getImages(pk_id, shiny=shiny)
        self.friendly = friendly

        self.image = self.back if friendly else self.front
        self.rect = self.image.get_rect()

        # numpy and pygame use different x-y coordinate systems
        self.mask = pg.surfarray.pixels_alpha(self.image).transpose()

        self.intro_animation = None

        self.animations = {
            "intro": None,
            "stat_raise": None,
            "stat_lower": None,
        }

        self.load_stat_stage_animations()

        self.visible = visible

    def load_stat_stage_animations(self):
        for direction in ["raise", "lower"]:
            frames = load_gif(f"assets/battle/main_display/stat_{direction}.gif", bit_mask=self.mask, opacity=150, scale=2)
            base_image = self.back if self.friendly else self.front
            self.animations[f"stat_{direction}"] = [base_image.copy() for _ in range(len(frames))]
            for frame_idx in range(len(frames)):
                self.animations[f"stat_{direction}"][frame_idx].blit(frames[frame_idx], (0, 0))


class Pokemon(pg.sprite.Sprite):
    def __init__(self, name, level=None, exp=None, moves=None, health=None, status=None,
                 EVs=None, IVs=None, gender=None, nature=None, ability_name=None, stat_stages=None,
                 friendly=False, shiny=None, visible=False, catch_location=None, catch_level=None,
                 catch_date=None):
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

        exp: int = int(level_up_values.loc[level, self.growthRate]) if exp is None else exp
        level: int = random.randint(1, 10) if level is None else level

        self.level, self.exp = level, exp
        self.level_exp: int = int(level_up_values.loc[level, self.growthRate])
        self.level_up_exp: int = int(level_up_values.loc[level+1, self.growthRate])
        self.evolveLevel: int = oldData.Evolve_Level

        if moves is None:
            possible_moves = [name for name, level in self.moveData if level <= self.level]
            move_names = random.choices(possible_moves, k=min([4, len(possible_moves)]))
            move_pps = [None] * len(move_names)
        else:
            move_names = [move["name"] for move in moves]
            move_pps = [move["pp"] if "pp" in move else None for move in moves]

        self.moves = [getMove(name, move_pp) for name, move_pp in zip(move_names, move_pps)]

        self.EVs = EVs if EVs is not None else [0 for _ in range(6)]
        self.IVs = IVs if IVs is not None else [random.randint(0, 31) for _ in range(6)]

        self.stats = Stats(exp=data.Base_Exp)
        self.updateStats()

        self.health = health if health else self.stats.health
        self.friendly = friendly

        if gender:
            self.gender = gender.lower()
        else:
            genders = data.Gender
            self.gender = ("male" if random.random() * 100 < genders[0] else "female") if genders else None

        ability_name = ability_name if ability_name else random.choice(data.Abilities[:len(data.Abilities)])
        self.ability = Ability(name=ability_name)
        self.nature = nature if nature else natures.loc[random.randint(0, 24)].Name

        self.shiny = shiny if shiny else (True if random.randint(0, 4095) == 0 else False)

        self.sprite = PokemonSprite(self.ID, self.shiny, friendly=self.friendly)

        front, back, small = getImages(self.ID, self.shiny)

        self.image = back if friendly else front
        self.displayImage = self.image.copy()
        self.sprite_mask = pg.mask.from_surface(self.image)
        self.smallImage = small
        self.animation, self.small_animation = None, None

        # if Move_PPs:
        #     for idx, move in enumerate(self.moves):
        #         move.PP = Move_PPs[idx] if Move_PPs[idx] else move.maxPP

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

        self.sprite_mask = None

        self.load_images()

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

    @property
    def rect(self):
        img_rect = self.image.get_rect()
        img_rect.midbottom = pg.Vector2(64, 153) * 2 if self.friendly else pg.Vector2(192, 90) * 2
        return img_rect

    @property
    def is_koed(self):
        return self.health <= 0

    def getMoveDamage(self, move, target, ignoreModifiers=False):
        if move.category == "Physical":
            if move.power:
                if ignoreModifiers:
                    if target.statStages.defence >= 0:
                        #  ignore the targets positive stat stages
                        effectiveDefence = target.stats.defence
                    else:
                        effectiveDefence = target.stats.defence * stageMultipliers[target.statStages.defence]

                    if self.statStages.attack <= 0:
                        #  ignore the attackers negative stat stages
                        effectiveAttack = self.stats.attack
                    else:
                        effectiveAttack = self.stats.attack * stageMultipliers[self.statStages.attack]
                else:
                    effectiveDefence = target.stats.defence * stageMultipliers[target.statStages.defence]
                    effectiveAttack = self.stats.attack * stageMultipliers[self.statStages.attack]

                damage = floor(((2 * self.level / 5) + 2) * move.power *
                               effectiveAttack / effectiveDefence) / 50

            else:
                damage = 0

        elif move.category == "Special":
            if move.power:
                if ignoreModifiers:
                    if target.statStages.spDefence >= 0:
                        #  ignore the targets positive stat stages
                        effectiveDefence = target.stats.spDefence
                    else:
                        effectiveDefence = target.stats.spDefence * stageMultipliers[target.stats.spDefence]

                    if self.statStages.spAttack <= 0:
                        #  ignore the attackers negative stat stages
                        effectiveAttack = self.stats.spAttack
                    else:
                        effectiveAttack = self.stats.spAttack * stageMultipliers[self.statStages.spAttack]
                else:
                    effectiveDefence = target.stats.spDefence * stageMultipliers[target.statStages.spDefence]
                    effectiveAttack = self.stats.spAttack * stageMultipliers[self.statStages.spAttack]

                damage = floor(floor(floor(2 * self.level / 5) + 2) * move.power *
                               floor(effectiveAttack / effectiveDefence)) / 50
            else:
                damage = 0

        else:
            damage = 0

        return damage

    def useMove(self, move, target):
        critStage = 0

        if move.effect:
            inflictCondition, modify, hits, heal = move.effect.getEffect()

        else:
            inflictCondition = None
            modify = None
            hits = 1
            heal = 0

        num = random.randint(0, 99) / 100
        crit, critical = (True, 2) if num < critChance[critStage] else (False, 1)

        baseDamage = self.getMoveDamage(move, target, crit)

        if self.status == StatusEffect.Burned and move.type == "Physical":
            burn = 0.5
        else:
            burn = 1

        screen, targets, weather, FF = 1, 1, 1, 1

        damage = baseDamage * burn * screen * targets * weather * FF + 2

        item, first = 1, 1

        rand = random.randint(85, 100) / 100

        STAB = 1.5 if (move.type == self.type1 or move.type == self.type2) else 1

        type1 = effectiveness.loc[str.upper(move.type), target.type1]

        if target.type2:
            type2 = effectiveness.loc[str.upper(move.type), target.type2]
        else:
            type2 = 1

        SRF, EB, TL, Berry = 1, 1, 1, 1

        damage = damage * critical * item * first * rand * STAB * type1 * type2 * SRF * EB * TL * Berry

        move.PP -= 1

        damage = floor(damage)

        if move.category == "Status":
            damage = 0

        # the move will consist of the following properties:
        # -> damage     -> effective
        return damage, type1 * type2, inflictCondition, heal, modify, hits, crit

    def updateEVs(self, name):
        data = pokedex.loc[name]
        EVYield = data.EV_Yield
        for [idx, value] in enumerate(EVYield):
            self.EVs[idx] += value

    def getFaintXP(self):
        a, e, f, L, Lp, p, s, t, v = 1, 1, 1, 1, 1, 1, 1, 1, 1

        b = self.stats.exp
        L = self.level

        exp = (a * t * b * e * L * p * f * v) / (7 * s)
        return exp

    def updateStats(self):
        data = pokedex.loc[self.name]
        stats = data.Stats

        baseHP, baseAttack, baseDefence = stats[0], stats[1], stats[2]
        baseSpAttack, baseSpDefence, baseSpeed = stats[3], stats[4], stats[5]

        maxHealth = \
            floor((2 * baseHP + self.EVs[0] + floor(self.EVs[0] / 4)) * self.level / 100 + self.level + 10)
        attack = \
            floor(floor((2 * baseAttack + self.EVs[1] + floor(self.EVs[1] / 4)) * self.level / 100 + 5) * 1)
        defence = \
            floor(floor((2 * baseDefence + self.EVs[2] + floor(self.EVs[2] / 4)) * self.level / 100 + 5) * 1)
        spAttack = \
            floor(floor((2 * baseSpAttack + self.EVs[3] + floor(self.EVs[3] / 4)) * self.level / 100 + 5) * 1)
        spDefence = \
            floor(floor((2 * baseSpDefence + self.EVs[4] + floor(self.EVs[4] / 4)) * self.level / 100 + 5) * 1)
        speed = \
            floor(floor((2 * baseSpeed + self.EVs[5] + floor(self.EVs[5] / 4)) * self.level / 100 + 5) * 1)

        self.stats = Stats(maxHealth, attack, defence, spAttack, spDefence, speed, self.stats.exp)

    def level_up(self):
        self.level += 1
        self.level_exp = int(level_up_values.loc[self.level, self.growthRate])
        self.level_up_exp = int(level_up_values.loc[self.level + 1, self.growthRate])
        self.updateStats()

    def get_new_moves(self):
        return [getMove(move_name) for move_name, level in self.moveData if level == self.level]

    def switch_image(self, direction="back"):
        front, back, small = getImages(self.ID, self.shiny)
        self.image = back if direction == "back" else front

    def get_evolution(self):
        return oldPokedex[oldPokedex["ID"] == self.ID + 1].index[0]

    def _clear_images(self):
        self.image = None
        self.animation = None

        self.displayImage = None

        self.smallImage = None
        self.small_animation = None
        self.sprite = None
        self.sprite_mask = None

    def load_images(self, animations: None | Animations = None):
        front, back, small = getImages(self.ID, self.shiny)
        self.image = back if self.friendly else front

        self.smallImage = small
        if not animations:
            animations = createAnimation(self.name)

        self.small_animation = animations.small
        self.animation = animations.front

    def reset_stat_stages(self):
        self.statStages = StatStages()

    def restore(self):
        self.health = self.stats.health
        self.status = None

        for move in self.moves:
            move.PP = move.maxPP

    # ========== DISPLAY FUNCTIONS BELOW  =============
    def get_json_data(self):
        movePPs = [move.PP for move in self.moves]
        status = self.status.value if self.status else None
        # self.visible = True if self.friendly else self.visible

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
