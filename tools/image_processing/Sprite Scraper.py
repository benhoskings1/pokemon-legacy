import os

import PIL
import pandas as pd
import requests
from PIL import Image
from bs4 import BeautifulSoup

nationalDex = pd.read_csv("game_data/National Dex.csv", index_col=1)

pokedex = pd.read_csv("game_data/pokedex/Local Dex.tsv", delimiter='\t', index_col=1)
attributes = pd.read_csv("game_data/pokedex/AttributeDex.tsv", delimiter='\t', index_col=1)


def getNumberString(num):
    if num < 100:
        return str.format("0{}", num)
    else:
        return str(num)


def getdata(url):
    r = requests.get(url)
    return r.text


def scrapeSprites(name, saveDirectory, save=False):
    try:
        htmldata = getdata(str.format("https://archives.bulbagarden.net/wiki/Category:{}", name))
    except KeyError:
        print("Key error")
        return
    ID = nationalDex.loc[name].ID

    soup = BeautifulSoup(htmldata, 'html.parser')

    saveDir = name

    for item in soup.find_all('img'):
        url = item['src']
        if ("4d" in url) and ("Ani" not in url):
            directory, tail = os.path.split(item['src'])

            dir2, tail2 = os.path.split(directory)
            if tail2.endswith(".png"):
                tail = tail2

            codeName, ext = tail.split(".")
            codeName = codeName.replace("Spr_", "")
            codeName = codeName.replace("4d_", "")

            if codeName.split("_")[0] == "b":
                if codeName.split("_")[1] == getNumberString(ID):
                    if len(codeName.split("_")) > 2:
                        if codeName.split("_")[2] == "s":
                            name = "Back_Shiny"
                        elif codeName.split("_")[2] == "f":
                            if len(codeName.split("_")) > 3:
                                if codeName.split("_")[3] == "s":
                                    name = "Back_Shiny_Female"
                                else:
                                    name = None
                            else:
                                name = "Back_Female"

                        elif codeName.split("_")[2] == "m":
                            if len(codeName.split("_")) > 3:
                                if codeName.split("_")[3] == "s":
                                    name = "Back_Shiny_Male"
                                else:
                                    name = None

                            else:
                                name = "Back_Male"
                        else:
                            name = None
                    else:
                        name = "Back"
                else:
                    name = None
            else:
                if codeName.split("_")[0] == getNumberString(ID):
                    if len(codeName.split("_")) > 1:
                        if codeName.split("_")[1] == "s":
                            name = "Front_Shiny"
                        elif codeName.split("_")[1] == "f":
                            if len(codeName.split("_")) > 2:
                                if codeName.split("_")[2] == "s":
                                    name = "Front_Shiny_Female"
                                else:
                                    name = None
                            else:
                                name = "Front_Female"

                        elif codeName.split("_")[1] == "m":
                            if len(codeName.split("_")) > 2:
                                if codeName.split("_")[2] == "s":
                                    name = "Front_Shiny_Male"
                                else:
                                    name = None

                            else:
                                name = "Front_Male"
                        else:
                            name = None
                    else:
                        name = "Front"
                else:
                    name = None

            if name and save:
                image = None
                while not image:
                    try:
                        resp = requests.get(url, stream=True).raw
                        image = Image.open(resp)

                    except PIL.UnidentifiedImageError:
                        print(url)

                if image.n_frames > 1:
                    images = []
                    for frame in range(image.n_frames):
                        image.seek(frame)
                        newFrame = image.copy()
                        frameData = newFrame.convert("RGBA")
                        images.append(frameData)
                    path = os.path.join(saveDirectory, saveDir, str.format("{}.gif", name))
                    images[0].save(path, save_all=True, append_images=images[1:], disposal=2)

                else:
                    path = os.path.join(saveDirectory, saveDir, str.format("{}.png", name))
                    image.save(path)

        elif "Ani" in item['src'] and "MS" in item['src']:
            if save:
                url = item['src']
                image = None
                while not image:
                    try:
                        resp = requests.get(url, stream=True).raw
                        image = Image.open(resp)

                    except PIL.UnidentifiedImageError:
                        print(url)

                images = []
                for frame in range(image.n_frames):
                    image.seek(frame)
                    newFrame = image.copy()
                    frameData = newFrame.convert("RGBA")
                    images.append(frameData)
                images[0].save(os.path.join(saveDirectory, saveDir, "Small.gif"), save_all=True,
                               append_images=images[1:], disposal=2)


directory = "Sprites/Pokemon/Gen IV"
names = pokedex.index
if not os.path.exists(directory):
    os.mkdir(directory)
else:
    directory = str.format("{} copy", directory)
    if not os.path.exists(directory):
        os.mkdir(directory)

for name in names:
    if os.path.isdir(os.path.join(directory, name)):
        if not (len(os.listdir(os.path.join(directory, name))) == 5 or
                len(os.listdir(os.path.join(directory, name))) == 9):
            print(name, len(os.listdir(os.path.join(directory, name))))
            scrapeSprites(name, directory, save=True)
    else:
        print(name)
        os.mkdir(os.path.join(directory, name))
        scrapeSprites(name, directory, save=True)

# check if all sprites are present in their folders
for name in names:
    dirName = os.path.join(directory, name)
    if not os.path.isdir(dirName):
        print("Directory not even present")

    else:
        femaleForm = attributes.loc[name].Female_Form
        if femaleForm == True:
            fileNames = ["Front_Shiny_Female.gif", "Front_Shiny_Male.gif",
                         "Front_Female.gif", "Front_Male.gif",
                         "Back_Shiny_Female.png", "Back_Shiny_Male.png",
                         "Back_Female.png", "Back_Male.png"]

        else:
            fileNames = ["Front_Shiny.gif", "Front.gif",
                         "Back_Shiny.png", "Back.png"]

        fileNames.append("Small.gif")

        for file in fileNames:
            filePath = os.path.join(dirName, file)
            if not os.path.exists(filePath):
                print(filePath)
