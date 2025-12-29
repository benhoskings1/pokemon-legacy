import json
import pygame as pg

from engine.general.item import Item, Pokeball, MedicineItem, BattleItemType, ItemType
from collections import Counter


class BagV2:
    def __init__(self, data = None):
        if data is None or data == {}:
            self.data = {}

        else:
            self.data = {ItemType(k): v for k, v in data.items()}

            self.data[ItemType.medicine] = Counter({MedicineItem(k): v for k, v in self.data[ItemType.medicine].items()})
            self.data[ItemType.pokeball] = Counter({Pokeball(k): v for k, v in self.data[ItemType.pokeball].items()})

        # protect items attribute
        self._items = {}

    # def __getstate__(self):

    @property
    def items(self):
        return self._items

    def get_items(self, item_type: ItemType = None, battle_item_type: BattleItemType = None):
        """ Return items """
        if item_type:
            return self.data.get(item_type, {})

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

    def decrement_item(self, item) -> None:
        self.data[item.item_type][item] -= 1

        if self.data[item.item_type][item] == 0:
            self.data[item.item_type].pop(item)

    def get_json_data(self) -> dict:
        """ Return JSON data """
        json_data = {
            item_type.value: {
                item.name: count for item, count in values.items()
            } for item_type, values in self.data.items()
        }

        return json_data

    def add_item(self, item: Item, item_count: int = 1):
        # check to identify if there is already an instance of the object
        matching_item = next(
            (bag_item for bag_item in self.data[item.item_type] if bag_item.name == item.name),
            item
        )
        self.data[item.item_type][matching_item] += item_count


class BagV3(dict):
    def __init__(self, data):
        super().__init__(data)

    def __setitem__(self, key, value):
        ...



if __name__ == "__main__":
    # pygame setup
    pg.init()
    window = pg.display.set_mode(pg.Vector2(240, 180) * 2)

    with open("test_data/bag/test_bag.json", "r") as read_file:
        bag_data = json.load(read_file)

    demo_bag = BagV2(bag_data)

    antidote = MedicineItem("Antidote")

    print(demo_bag.data[ItemType.medicine])

    demo_bag.add_item(antidote)
    demo_bag.add_item(antidote)
    # item_list = list(demo_bag.get_items(item_type=ItemType.mail).items())
    # print(item_list)
    # print(sorted(item_list, key=lambda item: item[0].item_id))
