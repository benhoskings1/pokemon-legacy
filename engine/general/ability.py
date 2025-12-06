import os

import pandas as pd

ABIlITIES = pd.read_csv("game_data/abilities.tsv", sep="\t", index_col=0)


class Ability:
    def __init__(self, ability_id=None, name=None):
        if not ability_id and not name:
            raise ValueError("Ability ID or name must be specified")

        data = ABIlITIES.loc[ability_id] if not name else ABIlITIES.loc[ABIlITIES["name"] == name]
        if not data.empty:
            data: pd.Series = data.iloc[0]
            self.id = ability_id if ability_id else data.name
            self.name = data["name"]
            self.description = data["description"]
            self.generation = data["generation"]
        else:
            self.id = ability_id
            self.name = name
            self.description = None
            self.generation = None

    def __str__(self):
        return f"{self.name} ({self.id}): {self.description}"


if __name__ == "__main__":
    ability = Ability(ability_id=3)
    print(ability)