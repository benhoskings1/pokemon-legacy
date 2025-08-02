import math
import os

import pandas as pd
import pygame as pg

localDex = pd.read_csv("/Users/benhoskings/Documents/Coding/Pokemon/Game Data/pokedex/Local Dex.tsv",
                       delimiter='\t', index_col=1)


def createSheet(baseDir, spriteSize, perRow, gridWidth=0, path=None):
    # images 80x80
    surfLength = math.ceil(len(localDex.index) / (perRow/4)) + 1
    sheet = pg.Surface((spriteSize.x * perRow + ((perRow + 1) * gridWidth),
                        spriteSize.y * surfLength + ((surfLength + 1) * gridWidth)), pg.SRCALPHA)

    if gridWidth != 0:
        for idx in range(perRow + 1):
            pg.draw.line(sheet, pg.Color(50, 50, 200), (2 + idx * (gridWidth + spriteSize.x), 0),
                         (2 + idx * (gridWidth + spriteSize.x), sheet.get_size()[0]), width=gridWidth)

        for idx in range(surfLength + 1):
            pg.draw.line(sheet, pg.Color(50, 50, 200), (0, 2 + idx * (gridWidth + spriteSize.y)),
                         (sheet.get_size()[0], 2 + idx * (gridWidth + spriteSize.y)), width=gridWidth)

    for name in localDex.index:
        folderDir = os.path.join(baseDir, name.title())
        if os.path.exists(folderDir):
            front, front_shiny, back, back_shiny = None, None, None, None
            if os.path.exists(os.path.join(folderDir, "Front.gif")):
                front = pg.image.load(os.path.join(folderDir, "Front.gif"))
                pos = -pg.Vector2(int((front.get_width() - spriteSize.x) / 2),
                                  int((front.get_height() - spriteSize.y) / 2))
                cropped = pg.Surface(spriteSize, pg.SRCALPHA)
                cropped.blit(front, pos)
                front = cropped

            elif os.path.exists(os.path.join(folderDir, "Front_Male.gif")):
                front = pg.image.load(os.path.join(folderDir, "Front_Male.gif"))
                pos = -pg.Vector2(int((front.get_width() - spriteSize.x) / 2),
                                  int((front.get_height() - spriteSize.y) / 2))
                cropped = pg.Surface(spriteSize, pg.SRCALPHA)
                cropped.blit(front, pos)
                front = cropped

            else:
                print(str.format("No front image for {}", name))

            if os.path.exists(os.path.join(folderDir, "Front_Shiny.gif")):

                front_shiny = pg.image.load(os.path.join(folderDir, "Front_Shiny.gif"))
                pos = -pg.Vector2(int((front_shiny.get_width() - spriteSize.x) / 2),
                                  int((front_shiny.get_height() - spriteSize.y) / 2))
                cropped = pg.Surface(spriteSize, pg.SRCALPHA)
                cropped.blit(front_shiny, pos)
                front_shiny = cropped

            elif os.path.exists(os.path.join(folderDir, "Front_Shiny_Male.gif")):
                front_shiny = pg.image.load(os.path.join(folderDir, "Front_Shiny_Male.gif"))
                pos = -pg.Vector2(int((front_shiny.get_width() - spriteSize.x) / 2),
                                  int((front_shiny.get_height() - spriteSize.y) / 2))
                cropped = pg.Surface(spriteSize, pg.SRCALPHA)
                cropped.blit(front_shiny, pos)
                front_shiny = cropped

            else:
                print(str.format("No front shiny image for {}", name))

            if os.path.exists(os.path.join(folderDir, "Back.png")):
                back = pg.image.load(os.path.join(folderDir, "Back.png"))
                pos = -pg.Vector2(int((back.get_width() - spriteSize.x) / 2),
                                  int((back.get_height() - spriteSize.y) / 2))
                cropped = pg.Surface(spriteSize, pg.SRCALPHA)
                cropped.blit(back, pos)
                back = cropped

            elif os.path.exists(os.path.join(folderDir, "Back_Male.png")):
                back = pg.image.load(os.path.join(folderDir, "Back_Male.png"))
                pos = -pg.Vector2(int((back.get_width() - spriteSize.x) / 2),
                                  int((back.get_height() - spriteSize.y) / 2))
                cropped = pg.Surface(spriteSize, pg.SRCALPHA)
                cropped.blit(back, pos)
                back = cropped

            else:
                print(str.format("No back image for {}", name))

            if os.path.exists(os.path.join(folderDir, "Back_Shiny.png")):
                back_shiny = pg.image.load(os.path.join(folderDir, "Back_Shiny.png"))
                pos = -pg.Vector2(int((back_shiny.get_width() - spriteSize.x) / 2),
                                  int((back_shiny.get_height() - spriteSize.y) / 2))
                cropped = pg.Surface(spriteSize, pg.SRCALPHA)
                cropped.blit(back_shiny, pos)
                back_shiny = cropped

            elif os.path.exists(os.path.join(folderDir, "Back_Shiny_Male.png")):
                back_shiny = pg.image.load(os.path.join(folderDir, "Back_Shiny_Male.png"))
                pos = -pg.Vector2(int((back_shiny.get_width() - spriteSize.x) / 2),
                                  int((back_shiny.get_height() - spriteSize.y) / 2))
                cropped = pg.Surface(spriteSize, pg.SRCALPHA)
                cropped.blit(back_shiny, pos)
                back_shiny = cropped

            else:
                print(str.format("No back shiny image for {}", name))

            count = (localDex.loc[name, "ID"] * 2) - 2

            pos = pg.Vector2((count % perRow) * spriteSize.x + (gridWidth * ((count%perRow) + 1)),
                             (math.floor(count / perRow) * (spriteSize.y + gridWidth)) * 2 + gridWidth)
            print(name, pos)

            if front:
                sheet.blit(front, pos)
            if front_shiny:
                sheet.blit(front_shiny, pos + pg.Vector2(0, 80 + gridWidth))
            if back:
                sheet.blit(back, pos + pg.Vector2(80 + gridWidth, 0))
            if back_shiny:
                sheet.blit(back_shiny, pos + pg.Vector2(80 + gridWidth, 80 + gridWidth))

        else:
            pass
            # print(str.format("Missing images for {}", name))
    #
    if path:
        pg.image.save(sheet, path)


def createSmallSheet(baseDir, spriteSize, perRow, gridWidth=0, path=None):
    # images 80x80
    surfLength = math.ceil(len(localDex.index) / (perRow))
    sheet = pg.Surface((spriteSize.x * perRow + ((perRow + 1) * gridWidth),
                        spriteSize.y * surfLength + ((surfLength + 1) * gridWidth)), pg.SRCALPHA)

    if gridWidth != 0:
        for idx in range(perRow + 1):
            pg.draw.line(sheet, pg.Color(50, 50, 200), (2 + idx * (gridWidth + spriteSize.x), 0),
                         (2 + idx * (gridWidth + spriteSize.x), sheet.get_size()[0]), width=gridWidth)

        for idx in range(surfLength + 1):
            pg.draw.line(sheet, pg.Color(50, 50, 200), (0, 2 + idx * (gridWidth + spriteSize.y)),
                         (sheet.get_size()[0], 2 + idx * (gridWidth + spriteSize.y)), width=gridWidth)

    for name in localDex.index:
        folderDir = os.path.join(baseDir, name.title())
        if os.path.exists(folderDir):
            small = None
            if os.path.exists(os.path.join(folderDir, "Small.gif")):
                small = pg.image.load(os.path.join(folderDir, "Small.gif"))
                pos = -pg.Vector2(int((small.get_width() - spriteSize.x) / 2),
                                  int((small.get_height() - spriteSize.y) / 2))
                cropped = pg.Surface(spriteSize, pg.SRCALPHA)
                cropped.blit(small, pos)
                small = cropped

            count = (localDex.loc[name, "ID"]) - 1

            pos = pg.Vector2((count % perRow) * spriteSize.x + (gridWidth * ((count % perRow) + 1)),
                             (math.floor(count / perRow) * (spriteSize.y + gridWidth)) + gridWidth)
            print(name, pos)

            if small:
                sheet.blit(small, pos)

        else:
            pass
            print(str.format("Missing images for {}", name))
    #
    if path:
        pg.image.save(sheet, path)


createSheet("Gen IV", pg.Vector2(80, 80), 32, 5, "Gen_IV_Sprites.png")
createSmallSheet("Gen IV", pg.Vector2(32, 32), 16, 5, "Gen_IV_Small_Sprites.png")
