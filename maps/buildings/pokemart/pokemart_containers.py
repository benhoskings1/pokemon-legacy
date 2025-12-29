import os
import importlib.resources as resources
from enum import Enum

import pygame as pg
import pandas as pd

from engine.general.direction import Direction
from engine.general.item import Item
from engine.graphics.screen_V2 import BlitLocation
from engine.graphics.sprite_screen import DisplayContainer
from engine.graphics.selector_display import SelectorDisplay

from engine.characters.player import Player2


MODULE_PATH = resources.files(__package__)


class MoneyContainer(DisplayContainer):
    def __init__(self, player: Player2, scale=1.0):
        image_path = os.path.join(MODULE_PATH, "assets/containers/money_container.png")
        DisplayContainer.__init__(self, image_path, "money_container", pg.Vector2(2, 2), scale=scale)
        self.image_path = image_path
        self.player = player

        self.update()

    def update(self):
        self.refresh()
        self.addText(f"{self.player.money:.0f}", pg.Vector2(86, 25)*self.scale, location=BlitLocation.topRight, )


class ItemSetContainer(SelectorDisplay):
    def __init__(self, items: list[Item], scale=1.0):
        container_img_path = os.path.join(MODULE_PATH, "assets/containers/item_set_container.png")
        selector_img_path = os.path.join(MODULE_PATH, "assets/containers/item_selector.png")

        cancel_item = Item(
            data=pd.Series({
                "name": "CANCEL",
                "buy_price": None,
                "sell_price": None,
                "name_item_type": None,
                "name_battle_item_type": None
            }),
            item_type=None
        )

        cancel_item.image = pg.image.load(os.path.join(MODULE_PATH, "assets/cancel_item.png"))

        items += [cancel_item]

        positions = [pg.Vector2(3, 11 + i * 16) for i in range(len(items))]
        SelectorDisplay.__init__(
            self,
            container_img_path,
            selector_img_path,
            options=items,
            option_positions=positions,
            display_posistion=pg.Vector2(95, 0),
            scale=scale,
        )

        # define node links here
        for idx in range(len(items)-1):
            self.link_options(items[idx], items[idx+1], direction=Direction.down, reverse=True)

        self._load_items(items, scale)

    def _load_items(self, items: list[Item], scale=1.0):
        for idx, item in enumerate(items):
            v_pos = 15 + idx * 16
            self.addText(item.name, pg.Vector2(9, v_pos) * scale, base=True,)
            if item.buyPrice is not None:
                self.addText(
                    f"{item.buyPrice:.0f}",
                    pg.Vector2(153, v_pos) * scale,
                    location=BlitLocation.topRight,
                    base=True
                )

    def reset(self):
        self.refresh()
        self.selector.reset()


class DisplayBar(DisplayContainer):
    def __init__(self, scale=1.0):
        image_path = os.path.join(MODULE_PATH, "assets/containers/display_bar.png")
        DisplayContainer.__init__(self, image_path, "display_bar", pg.Vector2(0, 141), scale=scale)

        self.text_rect = pg.Rect(pg.Vector2(40, 6)*scale, pg.Vector2(210, 44) * scale)

    def display_item(self, item: Item):
        self.refresh()
        if hasattr(item, "image"):
            if item.image is not None:
                item_image = item.image
                if self.scale != 1.0:
                    item_image = pg.transform.scale(item_image, pg.Vector2(item_image.get_size())* self.scale)

                self.add_surf(item_image, pg.Vector2(18, 26) * self.scale, location=BlitLocation.centre,)

        if item.description is not None:
            self.add_text_2(item.description, self.text_rect, vsep=1.2)


class BagCountContainer(DisplayContainer):
    def __init__(self, item_count, scale=1.0):
        image_path = os.path.join(MODULE_PATH, "assets/containers/bag_count_container.png")
        DisplayContainer.__init__(self, image_path, "bag_count_container", pg.Vector2(2, 114), scale=scale)

        # self.addText()


class PriceCounter(DisplayContainer):
    def __init__(self, item_price, player, scale=1.0):
        image_path = os.path.join(MODULE_PATH, "assets/containers/price_counter.png")
        DisplayContainer.__init__(self, image_path, "price_counter", pg.Vector2(146, 98), scale=scale)

        self.player = player
        self.item_price = item_price
        self.item_count = 1

    @property
    def selected(self):
        return self.item_count

    @property
    def total_price(self):
        return self.item_count * self.item_price

    def get_surface(self, show_sprites=True):
        self.refresh()
        self.addText(f"{self.total_price:.0f}",
                     location=BlitLocation.topRight, pos=pg.Vector2(102, 17)*self.scale)

        self.addText(f"x{self.item_count:02.0f}", pg.Vector2(6, 17) * self.scale)

        return super().get_surface()

    def process_interaction(self, direction: Direction, ):
        max_count = self.player.money // self.item_price
        overflow = self.item_count == max_count
        underflow = self.item_count == 1

        self.item_count = self.item_count - direction.value.y + direction.value. x * 10
        if self.total_price > self.player.money:
            if overflow:
                self.item_count = 1
            else:
                self.item_count = max_count
        elif self.item_count <= 0:
            if underflow:
                self.item_count = max_count
            else:
                self.item_count = 1

    def reset(self):
        self.refresh()
        self.item_count = 1


class ConfirmOption(Enum):
    yes = 1
    no = 0

class ConfirmContainer(SelectorDisplay):
    def __init__(self, scale=1.0):
        container_img_path = os.path.join(MODULE_PATH, "assets/containers/confirm_container.png")
        selector_img_path = os.path.join(MODULE_PATH, "assets/selector_arrow.png")

        SelectorDisplay.__init__(
            self,
            container_img_path,
            selector_img_path,
            scale=scale,
            options=[ConfirmOption.yes, ConfirmOption.no],
            option_positions=[(6, 9), (6, 25)],
            display_posistion=pg.Vector2(178, 98),
        )

        self.link_options(ConfirmOption.yes, ConfirmOption.no, direction=Direction.down, reverse=True)