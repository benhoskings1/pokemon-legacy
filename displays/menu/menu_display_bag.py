import os
import re

import pandas as pd
import pygame as pg
from enum import Enum

from graphics.screen_V2 import BlitLocation, FontOption
from bag import BagV2
from general.utils import Colours
from general.Item import ItemType, Item
from graphics.sprite_screen import SpriteScreen, DisplayContainer


BUTTON_POSITIONS = [(11, 36), (19, 84), (43, 124), (83, 148), (139, 148), (179, 124), (203, 84), (211, 36)]

# ==== Enums ====
class MenuTeamDisplayStates(Enum):
    items = 0
    medicine = 1
    pokeballs = 2
    HMs_and_TMs = 3
    berries = 4
    mail = 5
    battle_items = 6
    key_items = 7
    exit = 8


# ==== Sprites ====
class PocketButton(pg.sprite.Sprite):
    def __init__(self, item_type: MenuTeamDisplayStates, scale=1):
        pg.sprite.Sprite.__init__(self, )

        self.sprite_dir = f"assets/menu/bag/pocket_buttons/{item_type.name}"

        self.images = {im_type: pg.image.load(f"{self.sprite_dir}/{im_type}.png") for im_type in ("regular", "clicked", "selected")}
        self.images.update({im_type: pg.transform.scale(img, pg.Vector2(img.get_size())*scale) for im_type, img in self.images.items()})

        self.image = self.images["regular"]
        self.rect = pg.Rect(pg.Vector2(BUTTON_POSITIONS[item_type.value])*scale, self.image.get_size())

        # pg.draw.rect(self.image, (255, 0, 0), self.image.get_rect(), width=2)

        self.sprite_type = "pocket_button"
        self.id = item_type

    def update_image(self, status):
        self.image = self.images[status]

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

    def click_return(self):
        return self.sprite_type, self.id


class ItemSelector(pg.sprite.Sprite):
    def __init__(self, scale=1):
        pg.sprite.Sprite.__init__(self)
        self.image = pg.image.load("assets/menu/bag/selector_large.png")
        self.image = pg.transform.scale(self.image, pg.Vector2(self.image.get_size())*scale)
        self.rect = pg.Rect(pg.Vector2(105, 15)*scale, self.image.get_size())
        self.scale = scale

        self.sprite_type = "selector"
        self.id = None


# ==== Containers =====
class SelectedContainer(DisplayContainer):
    def __init__(self, item, scale=1):
        DisplayContainer.__init__(
            self, "assets/containers/menu/bag/item_selected.png", item, pg.Vector2(35, 146)*scale, scale=scale
        )

        self.add_text_2(f"{item.name} was selected", pg.Rect(pg.Vector2(13, 9)*scale, pg.Vector2(100, 28)*scale))

        self.rect.topleft = pg.Vector2(35, 146)*scale


class SelectorPopup(DisplayContainer):
    def __init__(self, item, scale=1):
        ...


class ItemSetContainer(DisplayContainer):
    def __init__(self, bag, scale=1):
        DisplayContainer.__init__(
            self, "assets/containers/menu/bag/item_set_container.png", "item_container",
            pg.Vector2(106, 5), scale=scale
        )
        self.bag: BagV2 = bag

        self.active_item_type = MenuTeamDisplayStates.items

    def update_image(self, item_type: ItemType, item_idx):
        self.refresh()

        bag_items = list(self.bag.get_items(item_type=item_type).items())

        bag_items += [(Item(
            pd.Series({"name": "Close","buy_price": None, "sell_price": None,
                       "name_item_type": None, "name_battle_item_type":None}, name=100),
            item_type
        ), 0)]

        offset = max(0, item_idx-4)

        sorted_items = sorted(bag_items, key=lambda item: item[0].item_id)[offset:min(offset+7, len(bag_items))]

        for idx, (item, count) in enumerate(sorted_items):
            if item.name == "Close":
                self.addText(f"CLOSE BAG", pg.Vector2(9, 14 + 16*idx)*self.scale)
                continue

            self.addText(f"No{item.item_id:02}", pg.Vector2(9, 17 + 16*idx)*self.scale, fontOption=FontOption.level)
            self.addText(item.name, pg.Vector2(41, 14 + 16*idx)*self.scale,)
            self.addText("x", pg.Vector2(115, 17 + 16 * idx) * self.scale, )
            self.addText(f"{count}", pg.Vector2(140, 14 + 16 * idx) * self.scale, location=BlitLocation.topRight)

        return sorted_items[item_idx - offset][0] if sorted_items else None


# ==== Displays ====
class MenuBagDisplay(SpriteScreen):
    def __init__(self, size, scale, game):
        SpriteScreen.__init__(self, pg.Vector2(size.x, size.y / 2))
        self.load_image("assets/menu/bag/background_upper.png", base=True, scale=scale)
        self.game = game

        self.selector = ItemSelector(scale=scale)
        self.container = ItemSetContainer(self.game.bag, scale=scale)

        self.sprites.add([self.container, self.selector])

        self.active_display_state = MenuTeamDisplayStates.items
        self.item_ids = [0 for _ in MenuTeamDisplayStates]
        self.item_counts = [len(self.game.bag.get_items(item_type=item_type)) for item_type in ItemType]

        self.selected_item = None

        self.scale = scale
        self.touch_display = SpriteScreen(pg.Vector2(size.x, size.y / 2))
        self.touch_display.load_image("assets/menu/bag/background_lower.png", base=True, scale=scale)
        self.pokeball_frame_idx = 0
        files = [file_name for file_name in os.listdir("assets/menu/bag/pokeball_rotations") if
                 re.match(r"frame_\d", file_name)]
        self.pokeball_frame_count = len(files)

        self.pocket_buttons = [PocketButton(item_type, scale=self.scale) for item_type in MenuTeamDisplayStates
                               if item_type != MenuTeamDisplayStates.items.exit]

        self.touch_display.sprites.add(self.pocket_buttons)
        self.update_display()

    def map_state_to_item_type(self) -> ItemType:
        if self.active_display_state == MenuTeamDisplayStates.HMs_and_TMs:
            return ItemType.tm
        return ItemType(self.active_display_state.name.title())

    def update_display(self):
        self.refresh()
        self.touch_display.refresh()

        self.addText(
            self.active_display_state.name.upper().replace("_", " "),
            pg.Vector2(50, 109)*self.scale, location=BlitLocation.midTop
        )

        if os.path.exists(f"assets/menu/bag/bag_{self.active_display_state.name}.png"):
            self.load_image(
                f"assets/menu/bag/bag_{self.active_display_state.name}.png",
                pg.Vector2(48, 53)*self.scale, scale=self.scale, location=BlitLocation.centre
            )

        self.load_image(
            "assets/menu/bag/selector_small.png",
            pg.Vector2(5 + 11 * self.active_display_state.value, 89) * self.scale, scale=self.scale
        )

        self.selected_item = self.container.update_image(self.map_state_to_item_type(), self.item_ids[self.active_display_state.value])
        if self.selected_item:
            if self.selected_item.image:
                self.add_image(
                    self.selected_item.image, pg.Vector2(18, 167)*self.scale, location=BlitLocation.centre, scale=self.scale
                )

            self.add_text_2(
                self.selected_item.description.replace("é", "e"),
                pg.Rect(pg.Vector2(40, 147)*self.scale, pg.Vector2(210, 44)*self.scale),
                sep=0, vsep=1.2, colour=Colours.white, shadow_colour=Colours.darkGrey,
            )

        self.touch_display.load_image(
            f"assets/menu/bag/pokeball_rotations/frame_{self.pokeball_frame_idx}.png",
            pg.Vector2(128, 80)*self.scale, location=BlitLocation.centre, scale=self.scale
        )

        self.game.topSurf.blit(self.get_surface(), (0, 0))
        self.game.bottomSurf.blit(self.touch_display.get_surface(), (0, 0))
        pg.display.flip()

    def process_input(self, key, controller):
        if key == controller.right or key == controller.left:

            self.pocket_buttons[self.active_display_state.value].update_image("regular")
            self.active_display_state = MenuTeamDisplayStates(
                (self.active_display_state.value + (1 if key == controller.right else - 1)) %
                (len(MenuTeamDisplayStates) - 1)
            )

        elif key == controller.down:
            new_val = min(self.item_ids[self.active_display_state.value] + 1,
                          max(0, self.item_counts[self.active_display_state.value]))
            if new_val != self.item_ids[self.active_display_state.value]:
                self.item_ids[self.active_display_state.value] = new_val
                self.pokeball_frame_idx = (self.pokeball_frame_idx + 1) % (self.pokeball_frame_count - 1)

        elif key == controller.up:
            new_val = max(0, self.item_ids[self.active_display_state.value] - 1)

            if new_val != self.item_ids[self.active_display_state.value]:
                self.item_ids[self.active_display_state.value] = new_val
                self.pokeball_frame_idx = (self.pokeball_frame_idx - 1) % (self.pokeball_frame_count - 1)

        elif key == controller.a:
            if self.selected_item:
                selected_container = SelectedContainer(self.selected_item, scale=self.scale)
                popup_container = ...
                self.sprites.add(selected_container)
                self.update_display()
                # item loop here!

                return self.selected_item

        elif key == controller.b:
            return MenuTeamDisplayStates.exit

        self.selector.rect.top = (15 + 16 * min([4, self.item_ids[self.active_display_state.value]])) * self.scale

        self.update_display()
        return True

    def loop(self):
        self.update_display()
        controller = self.game.controller

        while True:
            for event in pg.event.get():
                if event.type == pg.KEYDOWN:
                    if event.key in controller.keys:
                        action = self.process_input(event.key, controller)
                        if isinstance(action, Item):
                            print(action)

                        elif isinstance(action, MenuTeamDisplayStates):
                            if action == MenuTeamDisplayStates.exit:
                                return MenuTeamDisplayStates.exit

                elif event.type == pg.MOUSEBUTTONDOWN:
                    pos = pg.Vector2(pg.mouse.get_pos()) - pg.Vector2(0, self.size.y)
                    clicked = self.touch_display.click_test(pos)

                    if clicked:
                        self.pocket_buttons[self.active_display_state.value].update_image("regular")
                        self.pocket_buttons[clicked[1].value].update_image("clicked")
                        self.update_display()
                        pg.time.wait(200)
                        self.pocket_buttons[clicked[1].value].update_image("selected")

                        self.active_display_state = clicked[1]
                        self.selector.rect.top = (15 + 16 * min(
                            [4, self.item_ids[self.active_display_state.value]])) * self.scale
                        self.update_display()

            # self.update_display()
