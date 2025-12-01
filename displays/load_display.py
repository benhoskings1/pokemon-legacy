from math import ceil

import pygame as pg

from engine.graphics.screen_V2 import Screen, BlitLocation


class LoadDisplay:
    def __init__(self, size):
        self.topScreen = Screen(size)
        self.bottomScreen = Screen(size, colour=pg.Color(255, 255, 255))

        self.topScreen.load_image("Images/Load displays/Upper.png", base=True, scale=2)
        self.topScreen.load_image("Images/Load displays/Title Image.png", pos=pg.Vector2(256, 156), size=(380, 120),
                                 base=True, location=BlitLocation.centre)

        self.topScreen.refresh()
        self.bottomScreen.refresh()

    def updateAnimationLocation(self, directory):
        self.bottomScreen.refresh()
        self.bottomScreen.addText("Loading Animations", pos=(256, 50), location=BlitLocation.centre)
        self.bottomScreen.addText("From Directory", pos=(256, 100), location=BlitLocation.centre)
        self.bottomScreen.addText(directory, pos=(256, 150), lines=ceil(len(directory) / 28),
                                   location=BlitLocation.centre)

    def loadTeam(self, name):
        self.bottomScreen.refresh()
        self.bottomScreen.addText("Loading Team Animations", pos=(256, 50), location=BlitLocation.centre)
        self.bottomScreen.addText(name.title(), pos=(256, 100), location=BlitLocation.centre)

    def loadFoe(self, name):
        self.bottomScreen.refresh()
        self.bottomScreen.addText("Loading Foe Animations", pos=(256, 50), location=BlitLocation.centre)
        self.bottomScreen.addText(name.title(), pos=(256, 100), location=BlitLocation.centre)

    def finish(self):
        self.bottomScreen.refresh()
        self.bottomScreen.addText("Finished Setup", pos=(256, 50), location=BlitLocation.centre)

    def getScreens(self):
        return self.topScreen.get_surface(), self.bottomScreen.get_surface()
