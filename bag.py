import json

import pandas as pd
import pygame as pg


from general.Item import Item, Pokeball, MedicineItem, BattleItemType, ItemType


pokeballs = pd.read_csv("game_data/Items/pokeballs.tsv", delimiter="\t", index_col=0)


class BagV2:
    def __init__(self, data):
        self.data = {ItemType(k): v for k, v in data.items()}

        self.data[ItemType.medicine] = {MedicineItem(k): v for k, v in self.data[ItemType.medicine].items()}
        self.data[ItemType.pokeball] = {Pokeball(k): v for k, v in self.data[ItemType.pokeball].items()}

    def get_items(self, item_type: ItemType = None, battle_item_type: BattleItemType = None):
        if item_type:
            return self.data[item_type]

        elif battle_item_type:
            items = {}
            for v in self.data.values():
                items.update({k: v for k, v in v.items() if k.battle_item_type == battle_item_type})

            return items

        else:
            items = {}
            for v in self.data.values():
                items.update({k: v for k, v in v.items()})

            return items

    def decrement_item(self, item):
        count = self.data[item.item_type][item] - 1
        self.data[item.item_type][item] = count

        if self.data[item.item_type][item] == 0:
            self.data[item.item_type].pop(item)

    def get_json_data(self):
        ...


if __name__ == "__main__":
    # pygame setup
    pg.init()
    window = pg.display.set_mode(pg.Vector2(240, 180) * 2)

    with open("test_data/bag/test_bag.json", "r") as read_file:
        bag_data = json.load(read_file)

    demo_bag = BagV2(bag_data)
    item_list = list(demo_bag.get_items(item_type=ItemType.mail).items())
    print(item_list)
    print(sorted(item_list, key=lambda item: item[0].item_id))
