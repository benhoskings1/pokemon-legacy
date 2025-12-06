from enum import Enum

import pygame as pg

from engine.graphics.screen_V2 import BlitLocation, Colours
from engine.graphics.sprite_screen import SpriteScreen
from engine.general.Move import Move2
from displays.battle.battle_display_touch import DisplayContainer, BattleDisplaySummary, MoveContainer2, MOVE_SUMMARY_POSITIONS


# =========== SETUP =============
class LearnMoveStates(Enum):
    start = 0
    choose = 1
    select = 2
    give_up = 3


# =========== CONFIGURE SUB-DISPLAYS =============
class LearnMoveStart(SpriteScreen):
    def __init__(self, size, scale):
        SpriteScreen.__init__(self, size)
        self.display_type = LearnMoveStates.start
        self.scale = scale

        # load the base background
        self.load_image("assets/battle/touch_display/background_main.png", scale=scale, base=True)

        forget_container = DisplayContainer(
            "assets/containers/learn_move/container_1.png", LearnMoveStates.choose,
            scale=scale, pos=pg.Vector2(4, 40)
        )
        forget_container.addText(
            "Forget a move!", pos=pg.Vector2(124, 28) * scale, location=BlitLocation.midTop,
            colour=Colours.white.value, shadowColour=Colours.lightGrey.value
        )
        forget_container.image = forget_container.get_surface()

        pass_container = DisplayContainer(
            "assets/containers/learn_move/container_2.png", LearnMoveStates.give_up,
            scale=scale, pos=pg.Vector2(4, 107)
        )
        pass_container.addText(
            "Keep old moves!", pos=pg.Vector2(124, 28) * scale, location=BlitLocation.midTop,
            colour=Colours.white.value, shadowColour=Colours.lightGrey.value
        )
        pass_container.image = pass_container.get_surface()

        self.sprites.add([forget_container, pass_container])


class LearnMoveChoose(BattleDisplaySummary):
    def __init__(self, size, pokemon, new_move, scale=1):
        BattleDisplaySummary.__init__(self, size, pokemon, scale)
        self.display_type = LearnMoveStates.choose
        self.scale = scale

        self.load_image("assets/battle/touch_display/learn_move/background_choose.png", scale=scale, base=True)

        move_containers = [
            MoveContainer2(
                move, pos=(MOVE_SUMMARY_POSITIONS + [(65, 144)])[idx], scale=scale, colour="green" if idx != 4 else "red"
            ) for idx, move in enumerate(pokemon.moves + [new_move])
        ]

        return_container = DisplayContainer(
            "assets/containers/bag_return.png", LearnMoveStates.give_up, pos=(217, 152), scale=scale
        )

        self.sprites.add(move_containers + [return_container])


class LearnMoveSelect(BattleDisplaySummary):
    def __init__(self, size, pokemon, move, new=False, scale=1):
        BattleDisplaySummary.__init__(self, size, pokemon, scale)
        self.display_type = LearnMoveStates.select
        self.scale = scale

        self.load_image("assets/battle/touch_display/learn_move/background_select.png", scale=scale, base=True)

        self.addText("CATEGORY", pg.Vector2(32, 67) * self.scale,
                     colour=Colours.white.value, shadowColour=Colours.black.value, base=True)
        self.addText("POWER", pg.Vector2(8, 107) * self.scale,
                     colour=Colours.white.value, shadowColour=Colours.black.value, base=True)
        self.addText("ACCURACY", pg.Vector2(8, 131) * self.scale,
                     colour=Colours.white.value, shadowColour=Colours.black.value, base=True)

        return_container = DisplayContainer(
            "assets/containers/bag_return.png", LearnMoveStates.choose, pos=(217, 152), scale=scale
        )

        container_text = "FORGET" if not new else "CANCEL"
        select_container = DisplayContainer(
            "assets/containers/learn_move/select_container.png", move, pos=(1, 152), scale=scale
        )
        select_container.addText(
            container_text, pos=pg.Vector2(103, 20) * scale, location=BlitLocation.centre,
            colour=Colours.white.value, shadowColour=Colours.lightGrey.value
        )
        select_container.image = select_container.get_surface()

        self.sprites.add([select_container, return_container])

        self.load_move_details(move)

    def load_move_details(self, move: Move2):
        self.addText(move.name, pos=pg.Vector2(32, 43) * self.scale, colour=Colours.white.value, shadowColour=Colours.black.value)
        self.load_image(f"Images/Type Labels/{move.type} Label.png", pos=pg.Vector2(120, 41) * self.scale,
                        scale=pg.Vector2(self.scale))
        self.addText("PP", pos=pg.Vector2(160, 43) * self.scale, colour=Colours.white.value,
                     shadowColour=Colours.black.value)

        self.addText(f"{move.PP}/{move.maxPP}", pg.Vector2(204, 43) * self.scale, location=BlitLocation.midTop,
                     colour=Colours.white.value, shadowColour=Colours.black.value)
        self.addText(move.category, pos=pg.Vector2(76, 83) * self.scale, colour=Colours.darkGrey.value,
                     shadowColour=Colours.lightGrey.value, location=BlitLocation.midTop)

        self.load_image(f"assets/battle/touch_display/pokemon/{move.category}.png", pos=pg.Vector2(8, 81) * self.scale,
                        scale=pg.Vector2(self.scale, self.scale))

        self.addText(f"{move.power if move.power else '--'}", pos=pg.Vector2(103, 107) * self.scale, colour=Colours.darkGrey.value,
                     shadowColour=Colours.lightGrey.value, location=BlitLocation.topRight)

        self.addText(f"{move.accuracy if move.accuracy else '--'}", pos=pg.Vector2(103, 131) * self.scale, colour=Colours.darkGrey.value,
                     shadowColour=Colours.lightGrey.value, location=BlitLocation.topRight)

        if move.description is not None:
            self.addText(move.description, pos=pg.Vector2(128, 67) * self.scale, colour=Colours.darkGrey.value,
                        shadowColour=Colours.lightGrey.value, lines=5)


class LearnMoveGiveUp(SpriteScreen):
    def __init__(self, size, move: Move2, scale=1):
        SpriteScreen.__init__(self, size)
        self.display_type = LearnMoveStates.start
        self.scale = scale

        # load the base background
        self.load_image("assets/battle/touch_display/background_main.png", scale=scale, base=True)

        give_up_container = DisplayContainer(
            "assets/containers/learn_move/container_1.png", "give_up",
            scale=scale, pos=pg.Vector2(4, 40)
        )
        give_up_container.addText(
            f"Give up on {move.name}!", pos=pg.Vector2(124, 28) * scale, location=BlitLocation.midTop,
            colour=Colours.white.value, shadowColour=Colours.lightGrey.value
        )
        give_up_container.image = give_up_container.get_surface()

        continue_container = DisplayContainer(
            "assets/containers/learn_move/container_2.png", LearnMoveStates.start,
            scale=scale, pos=pg.Vector2(4, 107)
        )
        continue_container.addText(
            f"Dont give up on {move.name}!", pos=pg.Vector2(124, 28) * scale, location=BlitLocation.midTop,
            colour=Colours.white.value, shadowColour=Colours.lightGrey.value
        )
        continue_container.image = continue_container.get_surface()

        self.sprites.add([give_up_container, continue_container])


# =========== CONFIGURE MAIN DISPLAY =============
class LearnMoveDisplay:
    def __init__(self, size, pokemon, move, scale=1):
        self.size, self.scale = size, scale

        self.pokemon, self.new_move = pokemon, move
        self.selected_move_idx = 0

        self.state = LearnMoveStates.start

        self.displays = {
            LearnMoveStates.start: LearnMoveStart(self.size, self.scale),
            LearnMoveStates.choose: LearnMoveChoose(self.size, pokemon=pokemon, new_move=move, scale=self.scale),
            LearnMoveStates.select: LearnMoveSelect(self.size, pokemon=pokemon, move=move, scale=self.scale),
            LearnMoveStates.give_up: LearnMoveGiveUp(self.size, move=move, scale=self.scale),
        }

        self.active_display = self.displays[self.state]

        # LearnMoveSelect(self.size, pokemon=pokemon, move=move, scale=self.scale)

    def transition_start(self, battle):
        battle.display_message(f"{self.pokemon.name} wants to learn the move {self.new_move.name.title()}", 2000)
        battle.display_message(f"But {self.pokemon.name} cant learn more than four moves", 2000)
        battle.display_message("Make it forget another move?", 2000)

    def select_action(self, battle):
        action = None

        battle.active_touch_display = self.active_display
        battle.battle_display.refresh()
        battle.update_screen(cover=True)
        self.transition_start(battle)

        while not action:
            for event in pg.event.get():
                if event.type == pg.MOUSEBUTTONDOWN:
                    pos = pg.mouse.get_pos()
                    pos = pg.Vector2(pos) - pg.Vector2(0, self.size.y)
                    clicked = self.active_display.click_test(pos)

                    if clicked:
                        name, value = clicked
                        if isinstance(value, LearnMoveStates):
                            self.active_display = self.displays[value]
                            battle.active_touch_display = self.active_display

                            if self.state == LearnMoveStates.start and value == LearnMoveStates.choose:
                                battle.display_message(f"Which move should be forgotten?", 2000)

                            elif value == LearnMoveStates.start:
                                self.transition_start(battle)

                            elif value == LearnMoveStates.give_up:
                                battle.display_message(f"Well then ...", 2000)
                                battle.display_message(f"Should this Pokemon give up on learning this new move?", 2000)

                            self.state = value

                        elif isinstance(value, Move2):
                            if self.state == LearnMoveStates.choose:
                                new_move = True if value == self.new_move else False
                                self.displays[LearnMoveStates.select] = LearnMoveSelect(
                                    self.size, pokemon=self.pokemon, move=value, scale=self.scale, new=new_move
                                )
                                self.state = LearnMoveStates.select
                                self.active_display = self.displays[self.state]
                                battle.active_touch_display = self.active_display
                            else:
                                # select move to delete.
                                if value == self.new_move:
                                    battle.display_message(f"Well then ...", 2000)
                                    battle.display_message(f"Should this Pokemon give up on learning this new move?",
                                                           2000)
                                    self.state = LearnMoveStates.give_up
                                    self.active_display = self.displays[self.state]
                                    battle.active_touch_display = self.active_display
                                else:
                                    return value

                        elif value == "give_up":
                            return None

                elif event.type == pg.KEYDOWN:
                    # send event key to display selector
                    ...

            battle.update_screen()

        return action
