import os.path
from enum import Enum
import pygame as pg

from engine.pokemon.pokemon import Pokemon
from engine.battle.battle_animation import BattleAnimation, ANIMATION_PATH


class BattleActionType(Enum):
    attack = "attack",
    catch = "catch",
    heal = "heal",
    switch = "switch"
    run = "run"


class BattleAction:
    def __init__(self, battle_action_type: BattleActionType, ):
        self.action_type = battle_action_type


class BattleAttack(pg.sprite.Sprite, BattleAction, ):
    def __init__(self, target: Pokemon, move, animation_size=pg.Vector2(256, 192)):
        """
        Battle attacks are an object that allows the tracking of battle moves and contains the
        wrapper for their animations too. Battle animations are stored according to whom the move
        is affecting.

        For example if the move affects the foe, and the relevant animation frames can be found at
        assets/battle/move_animations/move/foe/move_XX.png

        :param target:
        :param move:
        :param animation_size:
        """
        pg.sprite.Sprite.__init__(self)
        BattleAction.__init__(self, BattleActionType.attack)

        self.image_size = pg.Vector2(60, 60)
        self.image = pg.Surface((60, 60), pg.SRCALPHA)
        # pg.draw.circle(self.image, (255, 0, 0), (30, 30), 30)

        self.sprite_type = "animation"
        self.friendly_action = target.friendly

        target_type = "friendly" if self.friendly_action else "foe"

        # print(f"Move: {move}, Target: {repr(target)}, Target type: {target_type}")

        if move.name in ["Growl"]:
            target_type = "foe" if self.friendly_action else "friendly"

        if os.path.isdir(f"assets/battle/move_animations/{move.name}/{target_type}"):
            # print("Creating animation")
            frame_path = os.path.join(ANIMATION_PATH, move.name.lower(), target_type)
            self.animation = BattleAnimation(frame_dir=frame_path, size=animation_size, opacity=220)
            self.frame_count = len(self.animation.frames)
            self.frame_idx = 0
        else:
            self.animation = None
            self.frame_count, self.frame_idx = 0, 0

    def get_animation_frame(self, idx):
        return self.animation[idx]


class BattleTagIn(pg.sprite.Sprite, BattleAction, ):
    def __init__(self, animation_size=pg.Vector2(256, 192)):
        """

        :param animation_size:
        """
        pg.sprite.Sprite.__init__(self)
        BattleAction.__init__(self, BattleActionType.switch)

        self.image_size = pg.Vector2(60, 60)
        self.image = pg.Surface((60, 60), pg.SRCALPHA)

        self.sprite_type = "animation"

        frame_path = os.path.join(ANIMATION_PATH, "tag_in")
        if os.path.isdir(frame_path):
            print("Creating animation")

            self.animation = BattleAnimation(frame_dir=frame_path, size=animation_size)
            self.frame_count = len(self.animation.frames)
            self.frame_idx = 0
        else:
            self.animation = None
            self.frame_count, self.frame_idx = 0, 0

    def get_animation_frame(self, idx):
        return self.animation[idx]


if __name__ == '__main__':
    display = pg.display.set_mode((592, 384))
    background = pg.Surface(display.get_size())
    background.fill((255, 255, 255))

    attack = BattleTagIn(animation_size=display.get_size())

    animation = attack.animation

    pg.event.pump()

    while True:
        for frame in animation.frames:
            display.blit(background, (0, 0))
            display.blit(frame, (0, 0))
            pg.display.flip()
            pg.time.wait(15)

        display.blit(background, (0, 0))
        pg.display.flip()
        pg.time.wait(1500)
