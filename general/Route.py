from enum import Enum
from random import choice

import pandas as pd


class Route:
    def __init__(self, name):
        data = pd.read_csv(str.format("game_data/Locations/{}.tsv", name), delimiter='\t', index_col=0)
        self.name = name
        self.data = {}
        for time in data.index:
            timeData = data.loc[time]
            startLevels = list(map(int, (timeData.Start_Levels[1: len(timeData.Start_Levels) - 1].split(","))))
            endLevels = list(map(int, (timeData.End_Levels[1: len(timeData.End_Levels) - 1].split(","))))
            levels = []
            for [idx, value] in enumerate(startLevels):
                levels.append((value, endLevels[idx]))

            timeData = {"Pokemon": timeData.Pokemon[1: len(timeData.Pokemon) - 1].split(", "),
                        "Rarity": timeData.Rarity[1: len(timeData.Rarity) - 1].split(", "),
                        "Levels": levels}
            dictValue = {time: timeData}
            self.data.update(dictValue)

    def __repr__(self):
        return f"Route({self.name})"

    def encounter(self, time):
        if time.hour < 12:
            data = self.data["Morning"]
        elif time.hour < 20:
            data = self.data["Day"]
        else:
            data = self.data["Night"]

        idx, pokemon = choice(list(enumerate(data["Pokemon"])))
        levels = data["Levels"][idx]
        if levels[1] != levels[0]:
            level = choice(range(levels[0], levels[1]))
        else:
            level = levels[0]

        return pokemon, level


class Routes(Enum):
    route201 = Route("Route 201")
    route202 = Route("Route 202")
    route203 = Route("Route 203")
    route204N = Route("Route 204 North")
    route204S = Route("Route 204 South")
    route205N = Route("Route 205 North")
