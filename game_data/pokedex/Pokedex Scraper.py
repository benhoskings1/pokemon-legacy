import json
import pickle
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup


def getdata(url):
    r = requests.get(url)
    return r.text


def scrapeData(pkName):
    pageName = pkName.replace("'", "").replace("♀", "-f").replace("♂", "-m")\
        .replace("é", "e").replace(":", "").replace(" ", "-")
    try:
        htmldata = getdata(str.format("https://pokemondb.net/pokedex/{}", pageName))
    except KeyError:
        print("Key error")
        return

    soup = BeautifulSoup(htmldata, 'html.parser')
    # print(soup)

    names = []
    panelNames = soup.find("div", class_="sv-tabs-tab-list")
    for name in panelNames:
        if name != "\n":
            names.append(name.text)

    for idx, name in enumerate(names):
        if str.format("{}{}", pkName[0].upper(), pkName[1:]) not in name:
            names[idx] = str.format("{} ({})", str.format("{}{}", pkName[0].upper(), pkName[1:]), name)
        else:
            names[idx] = str.format("{}{}", name[0].upper(), name[1:])

    panelData = soup.find("div", "sv-tabs-panel-list")
    # panels
    panels = panelData.find_all("div", "sv-tabs-panel")

    data = []

    for idx, panel in enumerate(panels):
        if idx < len(names):
            pkData = {"Name": names[idx]}
            tables = panel.find_all("table", class_="vitals-table")
            for table in tables:
                for tableData in table.findChildren("tr"):
                    stat = tableData.find_next("th")
                    value = tableData.find_next("td")
                    pkData[stat.text] = value.text

            data.append(pkData)

    return data


def cleanData(pkData: dict):
    # print(pkData)
    if len(pkData.keys()) == 1:
        return None

    types = pkData["Type"].replace("\n", "").strip()
    if " " in types:
        type1, type2 = types.split(" ")
        types = (type1, type2.strip())
    pkData["Type"] = types

    pkData["Species"] = pkData["Species"].replace("é", "e")

    height, _ = pkData["Height"].split("\xa0")
    pkData["Height"] = float(height)

    try:
        weight, _, _ = pkData["Weight"].split("\xa0")
        pkData["Weight"] = float(weight)
    except ValueError:
        pkData["Weight"] = None

    abilities = pkData["Abilities"]
    abilities = abilities.replace("1.", "").strip()
    abilityList = []

    if "2." in abilities:
        idx = abilities.find("2")
        abilityList.append(abilities[:idx])
        abilities = abilities[idx:]
        abilities = abilities.replace("2.", "")

    abilities = abilities.replace("(hidden ability)", "").strip()

    idx = 0
    idx2 = 0
    for word in abilities.split(" "):
        if word.title() != word:
            for idx2, char in enumerate(word[1:]):
                if char.upper() == char:
                    break
        else:
            if idx2 == 0:
                idx += len(word) + 1

    ability1 = abilities[:idx + idx2 + 1]
    ability2 = abilities[idx + idx2 + 1:]

    abilityList.append(ability1)
    abilityList.append(ability2)

    if len(abilityList) > 1:
        pkData["Abilities"] = tuple(abilityList)
    else:
        pkData["Abilities"] = abilityList[0]

    local = pkData["Local №"]
    localData = {}

    if "Red" in local:
        try:
            idx = local.find("Red")
            num = local[idx - 5: idx - 2]
            localData["R/B/Y"] = int(num)
        except ValueError:
            pass

    if "Gold/Silver" in local:
        idx = local.find("Gold")
        num = local[idx - 5: idx - 2]
        localData["G/S/C"] = int(num)

    if "Fire" in local:
        idx = local.find("Fire")
        num = local[idx - 5: idx - 2]
        localData["FR/LG"] = int(num)

    if "Heart" in local:
        idx = local.find("Heart")
        num = local[idx - 5: idx - 2]
        localData["HG/SS"] = int(num)

    if "Ruby/Sapphire" in local:
        idx = local.find("Ruby/Sapphire")
        num = local[idx - 5: idx - 2]
        localData["R/S/E"] = int(num)

    if "Omega" in local:
        idx = local.find("Omega")
        num = local[idx - 5: idx - 2]
        localData["OR/AS"] = int(num)

    if "Diamond" in local:
        idx = local.find("Diamond")
        local = local[idx - 5: idx - 2]
        localData["D/P"] = int(local)

    if "Platinum" in local:
        idx = local.find("Platinum")
        local = local[idx - 5: idx - 2]
        localData["P"] = int(local)

    if "Brilliant" in local:
        idx = local.find("Brilliant")
        local = local[idx - 5: idx - 2]
        localData["BD/SP"] = int(local)

    if "Black 2" in local:
        idx = local.find("Black 2")
        num = local[idx - 5: idx - 2]
        localData["B2/W2"] = int(num)

    if "Black" in local:
        idx = local.find("Black")
        num = local[idx - 5: idx - 2]
        localData["B/W"] = int(num)

    if "X/Y" in local:
        idx = local.find("X/Y")
        num = local[idx - 5: idx - 2]
        localData["X/Y"] = int(num)

    if "Sun/Moon" in local:
        idx = local.find("Sun")
        num = local[idx - 5: idx - 2]
        localData["S/M"] = int(num)

    if "U.Sun" in local:
        idx = local.find("U.Sun")
        num = local[idx - 5: idx - 2]
        localData["US/UM"] = int(num)

    if "Sword" in local:
        idx = local.find("Sword")
        num = local[idx - 5: idx - 2]
        localData["S/S"] = int(num)

    if "Legends" in local:
        idx = local.find("Legends")
        num = local[idx - 5: idx - 2]
        localData["LA"] = int(num)

    pkData["Local_Num"] = localData

    num = pkData["National №"]
    pkData["National_Num"] = int(num)

    try:
        rate = pkData["Catch rate"]
        rate = rate.replace("\n", "")
        rate = rate.split(" ")[0]
        pkData["Catch_Rate"] = int(rate)

    except ValueError:
        pkData["Catch_Rate"] = None

    pkData["Growth_Rate"] = pkData["Growth Rate"]

    try:
        yields = pkData["EV yield"]
        yields = yields.replace("\n", "").strip()
        yields = tuple(yields.split(", "))
        yieldList = [0 for _ in range(6)]
        for stat in yields:
            if "Special Attack" in stat:
                yieldList[3] = int(stat[0])
            elif "Attack" in stat:
                yieldList[1] = int(stat[0])
            if "Special Defense" in stat:
                yieldList[4] = int(stat[0])
            elif "Defense" in stat:
                yieldList[2] = int(stat[0])
            elif "Speed" in stat:
                yieldList[5] = int(stat[0])
            elif "HP" in stat:
                yieldList[0] = int(stat[0])

        pkData["EV_Yield"] = yieldList

    except ValueError:
        pkData["EV_Yield"] = None

    try:
        friendship = pkData["Base Friendship"]
        friendship = friendship.replace("\n", "").strip()
        friendship = friendship.split(" ")[0]
        pkData["Base_Friendship"] = int(friendship)

    except ValueError:
        pkData["Base_Friendship"] = None

    try:
        pkData["Base_Exp"] = int(pkData["Base Exp."])

    except ValueError:
        pkData["Base_Exp"] = None

    try:
        if len(pkData["Egg Groups"].split(", ")) > 1:
            pkData["Egg_Groups"] = tuple(pkData["Egg Groups"].split(", "))
        else:
            pkData["Egg_Groups"] = pkData["Egg Groups"]

    except ValueError:
        pkData["Egg_Groups"] = None

    gender = pkData["Gender"]

    try:
        male, female = gender.split(", ")
        pkData["Gender"] = (float(male.split("%")[0]), float(female.split("%")[0]))
    except ValueError:
        pkData["Gender"] = None

    try:
        pkData["Egg_Cycles"] = int(pkData["Egg cycles"].split(" ")[0])
    except ValueError:
        pkData["Egg_Cycles"] = None

    pkData["Stats"] = [int(pkData["HP"]), int(pkData["Attack"]), int(pkData["Defense"]),
                       int(pkData["Sp. Atk"]), int(pkData["Sp. Def"]), int(pkData["Speed"])]

    pkData["Total"] = int(pkData["Total"])

    data = {}

    keys = ["Name", "Type", "Species", "Height", "Weight", "Abilities", "Local_Num", "National_Num",
            "Catch_Rate", "EV_Yield", "Base_Friendship", "Base_Exp", "Growth_Rate", "Egg_Groups",
            "Gender", "Egg_Cycles", "Stats", "Total"]

    for key in keys:
        data[key] = pkData[key]

    return data


def scrapeMoves(pkName):
    pageName = pkName.replace("'", "").replace("♀", "-f").replace("♂", "-m").replace("é", "e").replace(":", "")
    try:
        htmldata = getdata(str.format("https://pokemondb.net/pokedex/{}/moves/4", pageName))
        soup = BeautifulSoup(htmldata, 'html.parser')
        panelData = soup.find("div", "sv-tabs-panel-list")
        # other panels
        table = panelData.find("table", "data-table")
        data = table.find("tbody")

    except AttributeError:
        gen = 5
        while gen < 9:
            try:
                htmldata = getdata(str.format("https://pokemondb.net/pokedex/{}/moves/{}", pkName.replace("'", ""), gen))
                soup = BeautifulSoup(htmldata, 'html.parser')
                panelData = soup.find("div", "sv-tabs-panel-list")
                # other panels
                table = panelData.find("table", "data-table")
                data = table.find("tbody")
                break

            except AttributeError:
                gen += 1
        if gen == 9:
            return None

    except KeyError:
        print("Key error")
        return

    movesData = []

    for move in data:
        result = move.find_all("td")
        name = result[1].text
        idx = 0
        for idx, char in enumerate(name[1:]):
            if char == char.upper():
                break

        idx += 1
        if idx != len(name) - 1:
            if name[idx] != " ":
                name = name[0:idx] + " " + name[idx:]

        moveData = (name, int(result[0].text))

        movesData.append(moveData)

    return movesData


def createDataFile(rangeLimit=None, testNames=None):
    try:
        htmldata = getdata("https://pokemondb.net/pokedex/national")
    except KeyError:
        print("Key error")
        return

    soup = BeautifulSoup(htmldata, 'html.parser')
    # print(soup.prettify())

    allData = soup.find_all("span", class_="infocard-lg-data text-muted")
    names = []
    for pkData in allData:
        nameData = str(pkData.text).split(" ")
        nameData = nameData[1:]
        if "·" in nameData:
            nameData = nameData[:len(nameData) - 3]
        else:
            nameData = nameData[:len(nameData) - 1]

        names.append(str.join(" ", nameData).replace(".", "").replace(" ", "-"))

    jsonData = {}
    keys = ["Name", "Type", "Species", "Height", "Weight", "Abilities", "Local_Num", "National_Num",
            "Catch_Rate", "EV_Yield", "Base_Friendship", "Base_Exp", "Growth_Rate", "Egg_Groups",
            "Gender", "Egg_Cycles", "Stats", "Total"]
    tsvData = pd.DataFrame(columns=keys)
    tsvData = tsvData.assign(Learnset=[])

    failedNames = []
    start = time.time()
    if testNames:
        names = testNames

    for name in names[:rangeLimit]:
        try:
            pkData = scrapeData(name.lower())
            scrapedMoves = scrapeMoves(name.lower())
            for variationData in pkData:
                cleanedData = cleanData(variationData)
                if cleanedData:
                    cleanedData["Learnset"] = scrapedMoves
                    jsonData[cleanedData["Name"]] = cleanedData
                    tsvData.loc[len(tsvData)] = cleanedData
                    print(str.format("Successfully loaded {}'s data", cleanedData["Name"]))

        except TypeError:
            print("Type error")
            print(str.format("Failed to to scrape {}'s data", name))
            failedNames.append(name)

        except ValueError:
            print("Attribute error")
            print(str.format("Failed to to scrape {}'s data", name))
            failedNames.append(name)

    end = time.time()

    print(str.format("\nCompleted in {} seconds\n", end - start))
    tsvData = tsvData.set_index("Name", drop=True)
    return jsonData, tsvData, failedNames


data, data2, failed = createDataFile()

if failed:
    print(str.format("Failed to load: {}\n", failed))

with open("NationalDex/NationalDex.json", "w") as write_file:
    json.dump(data, write_file, indent=4)
    print("Successfully writen to json")

data2.to_csv("NationalDex/NationalDex.tsv", sep="\t", index=True)
print("Successfully writen to tsv")

with open("NationalDex/NationalDex.pickle", 'wb') as f:
    pickle.dump(data2, f)
    print("Successfully pickled")
