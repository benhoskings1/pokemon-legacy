import pandas as pd
import pygame as pg

from engine.pokemon.pokemon import StatusEffect
from enum import Enum

item_data = pd.read_csv("game_data/items.tsv", delimiter="\t")
item_types = pd.read_csv("game_data/item_types.tsv", delimiter="\t", index_col=0)
battle_item_types = pd.read_csv("game_data/battle_item_types.tsv", delimiter="\t", index_col=0)
pokeballs = pd.read_csv("game_data/Items/pokeballs.tsv", delimiter="\t", index_col=0)
medicine = pd.read_csv("game_data/Items/medicine.tsv", delimiter="\t", index_col=0)

item_data = item_data.merge(item_types, on="item_type_id", how="left", suffixes=["", "_item_type"])
item_data = item_data.merge(battle_item_types, on="battle_item_type_id", how="left", suffixes=["", "_battle_item_type"])
item_data = item_data.merge(medicine, on="item_id", how="left").merge(pokeballs, on="item_id", how="left")

item_data = item_data.set_index("item_id")


class ItemType(Enum):
    item = "Items"
    medicine = "Medicine"
    pokeball = "Pokeballs"
    tm = "TMs"
    berries = "Berries"
    mail = "Mail"
    battle_item = "Battle_Items"
    key_item = "Key_Items"


class BattleItemType(Enum):
    healer = "healer"
    pokeball = "pokeball"
    restore = "restore"
    battle_item = "battle_item"


class Item:
    def __init__(self, data, item_type, description=""):
        self.item_id = data.name
        self.name = data["name"]
        self.type = item_type
        try:
            self.image = pg.image.load(str.format("Sprites/Items/{}/{}.png", self.type, data["name"]))
        except FileNotFoundError:
            self.image = None

        self.buyPrice = None if pd.isna(data.buy_price) else data.buy_price
        self.sellPrice = None if pd.isna(data.sell_price) else data.sell_price

        self.description = description

        self.item_type = None if pd.isna(data.name_item_type) else ItemType(data.name_item_type)
        self.battle_item_type = None if pd.isna(data.name_battle_item_type) else BattleItemType(data.name_battle_item_type)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.item_id}, {self.name})"


class Pokeball(Item):
    def __init__(self, name):
        data = item_data.loc[item_data["name"] == name].iloc[0]
        if pd.isna(data.description):
            super().__init__(data, item_type="Pokeball")
        else:
            super().__init__(data, item_type="Pokeball", description=data.description)

        self.modifier = data.Rate_Modifier

        if pd.isna(data.Conditions):
            self.conditions = None
        else:
            self.conditions = data.Conditions

    def __repr__(self):
        return f"Pokeball({self.name}, {self.modifier}, {self.conditions})"


class MedicineItem(Item):
    def __init__(self, name):
        data = item_data.loc[item_data["name"].str.lower() == name.lower()].iloc[0]
        if pd.isna(data.description):
            super().__init__(data, item_type="Medicine")
        else:
            super().__init__(data, item_type="Medicine", description=data.description)

        self.heal = False if pd.isna(data.heal_amount) else int(data.heal_amount)
        self.status = None if pd.isna(data.status) else StatusEffect(data.status)
        self.battle_type = None if pd.isna(data.battle_type) else data.battle_type

    def __repr__(self):
        return f"Medicine({self.name}, {self.heal if self.heal else 0}, {self.status})"


class ItemGenerator:
    item_data = pd.read_csv("game_data/items.tsv", delimiter="\t")
    item_types = pd.read_csv("game_data/item_types.tsv", delimiter="\t", index_col=0)
    battle_item_types = pd.read_csv("game_data/battle_item_types.tsv", delimiter="\t", index_col=0)
    pokeballs = pd.read_csv("game_data/Items/pokeballs.tsv", delimiter="\t", index_col=0)
    medicine = pd.read_csv("game_data/Items/medicine.tsv", delimiter="\t", index_col=0)

    item_data = item_data.merge(item_types, on="item_type_id", how="left", suffixes=["", "_item_type"])
    item_data = item_data.merge(battle_item_types, on="battle_item_type_id", how="left",
                                suffixes=["", "_battle_item_type"])
    item_data = item_data.merge(medicine, on="item_id", how="left").merge(pokeballs, on="item_id", how="left")

    item_data = item_data.set_index("item_id")

    item_class_bindings = {
        ItemType.item: Item,
        ItemType.pokeball: Pokeball,
        ItemType.medicine: MedicineItem,
    }

    def __init__(self):
        ...

    @classmethod
    def generate_item(cls, item_name: str) -> None | Item | MedicineItem | Pokeball:
        """ Return item from name """
        item_data = cls.item_data.loc[cls.item_data["name"].str.lower() == item_name.lower()]
        if item_data.empty:
            return None

        item_type = ItemType(item_data.iloc[0]["name_item_type"])

        item_class = cls.item_class_bindings[item_type]

        return item_class(item_name)


if __name__ == "__main__":
    # os.chdir("../")
    # print(os.getcwd())
    generator = ItemGenerator()

    pokeball = generator.generate_item("potion")
    print(isinstance(pokeball, Item))
