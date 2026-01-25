import pandas as pd

localDex = pd.read_csv("pokedex/Local Dex.tsv", delimiter='\t', index_col=1)
movesets = pd.read_csv("Movesets.tsv", delimiter='\t', index_col=0)

newDex = pd.DataFrame(columns=["Name", "Type_1", "Type_2", "Stats", "EVs", "XP", "XP_Type", "Moves", "Move_Levels"])
newDex.index.name = "ID"

for (idx, name) in enumerate(localDex.index):
    localDex.loc[name, "Moves"] = movesets.loc[name, "Moves"]
    localDex.loc[name, "Move_Levels"] = movesets.loc[name, "Move_Levels"]

print(localDex)
localDex.to_csv("pokedex/Local Dex.tsv", sep='\t')
