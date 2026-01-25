import json
import pickle

import pandas as pd

with open("NationalDex/NationalDex.pickle", 'rb') as f:
    nationalDex: pd.DataFrame = pickle.load(f)
    print("Successfully loaded from pickle")

localDex = pd.DataFrame(columns=nationalDex.columns)

for name in nationalDex.index:
    pkData = nationalDex.loc[name]
    localData: dict = pkData["Local_Num"]
    if "D/P" in localData.keys():
        print(name, localData["D/P"])
        pkData.loc["Local_Num"] = localData["D/P"]
        localDex.loc[name] = pkData

localDex.sort_values(by="Local_Num", inplace=True)
cols = list(localDex.columns)
newCols = cols[5:6] + cols[0:5] + cols[6:]
localDex = localDex[newCols]

with open("LocalDex/LocalDex.json", "w") as write_file:
    json.dump(localDex.to_json(), write_file, indent=4)
    print("Successfully writen to json")

localDex.to_csv("LocalDex/LocalDex.tsv", sep="\t", index=True)
print("Successfully writen to tsv")

with open("LocalDex/LocalDex.pickle", 'wb') as f:
    pickle.dump(localDex, f)
    print("Successfully pickled")

