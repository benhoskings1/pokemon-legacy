import json
import random
import shutil
import sys
import time
import warnings
from datetime import datetime

from bag import BagV2
from battle import Battle, State, BattleOutcome
from pokedex import Pokedex
from game_log.game_log import GameLog, GameEvent, GameEventType

from displays.load_display import LoadDisplay
from general.Animations import createAnimation
from general.utils import *
from general.Controller import Controller
from general.Direction import Direction
from general.Time import Time
from general.Route import Route

# ======= Load displays =====
from displays.game_display import GameDisplay, GameDisplayStates
from displays.menu.menu_display_team import MenuTeamDisplay
from displays.menu.menu_display_bag import MenuBagDisplay

from player import Player, Movement
from pokemon import Pokemon
from poketech.poketech import Poketech
from team import Team


pokedex = pd.read_csv("game_data/pokedex/Local Dex.tsv", delimiter='\t', index_col=1)


class Game:
    def __init__(self, scale, optimize=False, new=False, overwrite=False, save_slot=1):

        self.overwrite: bool = overwrite
        self.save_slot: int = save_slot

        self.data_path = f"game_data/save_states/{'save_state_' + str(save_slot) if not new else 'start'}"

        self.running = True

        self.controller = Controller()

        native_size = pg.Vector2(256, 382)
        self.graphics_scale = 2

        self.displaySize = native_size * self.graphics_scale

        # initialise the display properties
        self.window: None | pg.Surface  = None
        self.topSurf: None | pg.Surface  = None
        self.bottomSurf: None | pg.Surface = None
        self.loadDisplay: None | LoadDisplay = None

        self.animations = {}

        # load the displays
        self.load_displays()

        with open(os.path.join(self.data_path, "team.json"), "r") as read_file:
            # Convert JSON file to Python Types
            teamData = json.load(read_file)

        self.team = Team(teamData)

        for pk in self.team.pokemon:
            if not (pk.name in self.animations.keys()):
                self.loadDisplay.loadTeam(pk.name)
                top, bottom = self.loadDisplay.getScreens()
                self.topSurf.blit(top, (0, 0))
                self.bottomSurf.blit(bottom, (0, 0))
                pg.display.flip()
                # print("Creating ", repr(pk))
                self.animations[pk.name] = createAnimation(pk.name)
                animations = self.animations[pk.name]
                pk.loadImages(animations)
            else:
                pk.loadImages(self.animations[pk.name])

        self.team.pokemon = self.team.pokemon

        with open(os.path.join(self.data_path, "bag.json"), "r") as read_file:
            # Convert JSON file to Python Types
            bagData = json.load(read_file)

        self.bag = BagV2(bagData)

        spriteDirectory = "Sprites/Pokemon Sprites/Gen IV 2"
        gameData = None

        if not new and not os.path.exists(os.path.join(self.data_path, "game.pickle")):
            print("No pickle data not present / corrupted")

        if not new and os.path.exists(os.path.join(self.data_path, "game.pickle")):
            gameFile = open(os.path.join(self.data_path, "game.pickle"), 'rb')
            gameData = pickle.load(gameFile, encoding='bytes')

            self.load_displays()

            # update player with the Surfaces
            self.player = gameData.player
            self.player.load_surfaces("Sprites/Player Sprites")
            self.player.update()

            # update poketech with the Surfaces
            self.poketech = gameData.poketech
            self.poketech.load_surfaces()

            # update each of the Pokémon with their surfaces

            # print(gameData.battle.__dict__ if gameData.battle else 'no battle')
            self.battle = gameData.battle if gameData.battle else None
            self.appearances = gameData.appearances

        else:
            # create new player instance
            self.player = Player("Sprites/Player Sprites", position=pg.Vector2(35, 18))

            self.poketech = Poketech(self.displaySize, self.time, scale=self.graphics_scale)

            self.battle = None

            self.appearances = {}

        if optimize:
            totalSeen = 0
            for key in self.appearances:
                totalSeen += int(self.appearances[key])

            if totalSeen != 0:
                for idx, name in enumerate(pokedex.index):
                    if name in self.appearances.keys():
                        appearanceRatio = self.appearances[name] / totalSeen
                        if appearanceRatio >= 0.4:
                            print(name, appearanceRatio)
                            directory = os.path.join(spriteDirectory, name)
                            self.loadDisplay.updateAnimationLocation(directory)
                            top, bottom = self.loadDisplay.getScreens()
                            self.topSurf.blit(top, (0, 0))
                            self.bottomSurf.blit(bottom, (0, 0))
                            pg.display.flip()
                            pkAnimations = createAnimation(name)
                            self.animations[name] = pkAnimations

        self.log, self.log_dir = GameLog(), "game_data/logs"

        # ========== DISPLAY INITIALISATION =========
        self.game_display = GameDisplay(self.topSurf.get_size(), self.player, scale=self.graphics_scale)

        self.pokedex = Pokedex(self) if not gameData else gameData.pokedex
        self.pokedex.game = self
        self.pokedex.load_surfaces()
        self.pokedex.national_dex = pd.read_csv("game_data/pokedex/NationalDex/NationalDex.tsv", delimiter='\t', index_col=0)

        self.menu_active = False

        self.menu_objects = {
            GameDisplayStates.pokedex: self.pokedex,
            GameDisplayStates.team: MenuTeamDisplay(self.displaySize, self.graphics_scale, self),
            GameDisplayStates.bag: MenuBagDisplay(self.displaySize, self.graphics_scale, self),
        }

        # ========== POST INITIALISATION =========
        # happens after all attributes initialised
        self.loadDisplay.finish()
        top, bottom = self.loadDisplay.getScreens()
        self.topSurf.blit(top, (0, 0))
        self.bottomSurf.blit(bottom, (0, 0))
        pg.display.flip()
        pg.time.delay(750)

        self.fadeToBlack(500)

        self.log.add_event(GameEvent(name="startup complete"))

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.load_displays()

    @property
    def time(self):
        return datetime.now()

    def load_displays(self):
        self.window = pg.display.set_mode(self.displaySize)
        self.topSurf = self.window.subsurface(((0, 0), (self.displaySize.x, self.displaySize.y / 2)))
        self.bottomSurf = self.window.subsurface(((0, self.displaySize.y / 2),
                                                  (self.displaySize.x, self.displaySize.y / 2)))
        self.bottomSurf.fill(Colours.white.value)
        self.loadDisplay = LoadDisplay(self.topSurf.get_size())

    def createPokemon(self, name, friendly=False, level=None, exp=None, moveNames=None, EVs=None, IVs=None, shiny=None,):

        if not friendly:
            self.pokedex.data.loc[name, "appearances"] += 1

        if not (name in self.animations.keys()):
            # print("Creating ", name)
            self.animations[name] = createAnimation(name)

        animations = self.animations[name]

        pokemon = Pokemon(name, level=level, XP=exp, Move_Names=moveNames, EVs=EVs, IVs=IVs,
                          Friendly=friendly, Shiny=shiny)

        pokemon.animation = animations.front
        pokemon.small_animation = animations.small

        return pokemon

    def fadeToBlack(self, duration):
        blackSurf = pg.Surface(self.topSurf.get_size())
        blackSurf.fill(Colours.black.value)
        blackSurf.set_alpha(0)
        count = 100
        for t in range(0, count):
            blackSurf.set_alpha(round(t / count * 255))
            pg.time.delay(int(duration / count))
            self.topSurf.blit(blackSurf, (0, 0))
            self.bottomSurf.blit(blackSurf, (0, 0))
            pg.display.flip()

    def fadeFromBlack(self, duration, battle=False):
        blackSurf = pg.Surface(self.topSurf.get_size())
        blackSurf.fill(Colours.black.value)
        blackSurf.set_alpha(255)
        count = 100
        for t in range(0, count):
            blackSurf.set_alpha((count - t) / count * 255)
            pg.time.delay(int(duration / count))
            if not battle:
                self.updateDisplay(flip=False)
            else:
                if self.battle.state == State.home:
                    self.battle.update_screen(cover=True, flip=False)
                else:
                    self.battle.update_screen(flip=False)

            self.topSurf.blit(blackSurf, (0, 0))
            self.bottomSurf.blit(blackSurf, (0, 0))
            pg.display.flip()

    @property
    def time_of_day(self):
        if 6 < self.time.hour <= 16:
            return Time.day
        elif 16 < self.time.hour <= 20:
            return Time.evening
        else:
            return Time.night

    def updateDisplay(self, flip=True):

        self.game_display.refresh()
        self.topSurf.blit(self.game_display.get_surface(), (0, 0))
        self.bottomSurf.blit(self.poketech.get_surface(), (0, 0))
        if flip:
            pg.display.flip()

    def movePlayer(self, direction, detectGrass=True):
        self.player.update()

        moved = False

        if self.player.facingDirection == direction:
            if not self.check_collision(direction):
                moved = True
                # shift the map
                self.player._moving = True
                move_duration = 200 if self.player.movement == Movement.walking else 125
                self.game_display.move_animation(self.topSurf, direction, duration=move_duration)
                self.player._moving = False

        self.player.update()
        self.updateDisplay()
        if moved:
            if detectGrass:
                self.detectGrassCollision()
            self.player.steps += 1
            self.poketech.pedometerSteps += 1
            self.poketech.update_pedometer()

        self.player.facingDirection = direction
        self.player._leg = not self.player._leg

        if not moved:
            # add an optional delay here
            pass

        return moved

    def check_collision(self, direction):
        new_rect = self.player.rect.move(direction.value * self.game_display.map.tilewidth)

        ob_collision = new_rect.collideobjects(self.game_display.map.obstacles.sprites(), key=lambda o: o.rect)
        if ob_collision:
            return ob_collision

        trainer_collision = new_rect.collideobjects(self.game_display.map.map_objects.sprites(), key=lambda o: o.rect)
        if trainer_collision:
            return trainer_collision

        return False

    def detectGrassCollision(self, battle=False) -> None:
        collide = self.game_display.map.detect_collision()
        if any(collide):
            grass = collide[0]
            num = random.randint(0, (1 if battle else 255))
            if num < grass.encounterNum:
                pg.time.delay(100)
                self.battleIntro(250)
                self.start_battle(route=grass.route)

    def start_battle(self, foe_team: None | list[Pokemon] | Team=None, route="Route 201", trainer=None) -> None:
        """ Start a battle. """
        if not foe_team:
            route = Route(route)
            wild_name, wild_level = route.encounter(self.time)
            wild_pk: Pokemon = self.createPokemon(wild_name, level=wild_level)
            foe_team = [wild_pk]

        self.log.add_event(GameEvent(name=f"battle started against {foe_team}", event_type=GameEventType.game))
        self.battle = Battle(self, self.team, foe_team, route_name=route, trainer=trainer)
        outcome = self.battle.run()

        if outcome == BattleOutcome.quit:
            self.running = False
        else:
            self.battle = None
            self.log.add_event(GameEvent(name=f"battle completed with outcome {outcome}", event_type=GameEventType.game))

    def battleIntro(self, time_delay):
        blackSurf = pg.Surface(self.topSurf.get_size())
        blackSurf.fill(Colours.darkGrey.value)
        for count in range(2):
            self.topSurf.blit(blackSurf, (0, 0))
            pg.display.flip()
            pg.time.delay(time_delay)
            self.updateDisplay()
            pg.time.delay(time_delay)

    def wait_for_key(self, key=None, break_on_timeout=True) -> bool:
        key = key if key is not None else self.controller.a

        t0 = time.monotonic()
        pg.event.clear()
        while True:
            event = pg.event.wait()
            if event.type == pg.QUIT:
                ...
            elif event.type == pg.KEYDOWN:
                if event.key == key:
                    return True

            if time.monotonic() - t0 > 10 and break_on_timeout:
                # timeout at 10s
                return True

    def display_message(self, text, duration=1000):
        self.updateDisplay()
        # self.game.bottomSurf.blit(self.lowerScreenBase, (0, 0))
        pg.display.flip()

        for char_idx in range(1, len(text) + 1):
            self.game_display.update_display_text(text, max_chars=char_idx)
            self.updateDisplay()
            pg.display.flip()
            pg.time.delay(round(duration * 0.7 / len(text)))
            # self.wait(round(duration * 0.7 / len(text)))

        self.game_display.sprites.remove(self.game_display.text_box)

    def loop(self):
        if self.battle:
            self.battle.update_screen(flip=False)
            self.fadeFromBlack(500, battle=True)
            outcome = self.battle.loop()
            self.battle = None
            self.updateDisplay()
        else:
            self.updateDisplay(flip=False)
            self.fadeFromBlack(500)

        self.updateDisplay()
        print("load_disp")

        while self.running:
            pg.time.delay(25)  # set the debounce-time for keys
            keys = pg.key.get_pressed()
            mouse = pg.mouse.get_pressed()
            if keys[self.controller.up]:
                self.player.spriteIdx = 0
                self.movePlayer(Direction.up)
            elif keys[self.controller.down]:
                self.player.spriteIdx = 3
                self.movePlayer(Direction.down)
            elif keys[self.controller.left]:
                self.player.spriteIdx = 6
                self.movePlayer(Direction.left)
            elif keys[self.controller.right]:
                self.player.spriteIdx = 9
                self.movePlayer(Direction.right)

            elif keys[pg.K_h]:
                print("Restoring all pokemon in team")
                for pk in self.team.pokemon:
                    pk.restore()

                pg.time.delay(100)

            if keys[self.controller.b]:
                self.player.movement = Movement.running

            else:
                if self.player.movement != Movement.walking:
                    self.player.movement = Movement.walking
                    self.player.update()
                    self.updateDisplay()

            if any(mouse):
                # self.poketech.interact(pg.mouse.get_pos())
                self.updateDisplay()
                pg.time.delay(100)

            if self.time.minute != datetime.now().minute:
                self.updateDisplay()

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.running = False
                elif event.type == pg.KEYDOWN:
                    if event.key == self.controller.y:
                        action = self.game_display.menu_loop(self)
                        while action:
                            if isinstance(action, GameDisplayStates):
                                if action in self.menu_objects.keys():
                                    self.menu_objects[action].loop()

                            action = self.game_display.menu_loop(self)
                            self.updateDisplay()
                        self.updateDisplay()

                    elif event.key == self.controller.a:
                        trainer = self.check_collision(direction=Direction.up)
                        if trainer and not trainer.battled and self.player.facingDirection == Direction.up:
                            self.log.add_event(GameEvent(f"Trainer battle with {trainer}", event_type=GameEventType.game))
                            # add display text box

                            # self.game_display.z
                            self.display_message("May I trouble you for a battle please?", 2000)
                            self.wait_for_key(break_on_timeout=False)
                            self.start_battle(foe_team=trainer.team, trainer=trainer)
                            trainer.battled = True

                            # self.startBattle(trainer)

        if self.overwrite:
            self.save()

    def demo(self):
        pg.event.pump()
        self.player.position = pg.Vector2(10, 9)

        self.player.spriteIdx = 9
        for step in range(10):
            self.movePlayer(Direction.right)
            pg.time.delay(25)

        self.player.movement = Movement.running
        self.player.update()

        for step in range(6):
            self.movePlayer(Direction.right)
            pg.time.delay(25)

        for idx in [3, 6, 0, 9, 3]:
            self.player.spriteIdx = idx
            self.player.update()
            self.updateDisplay()
            pg.time.delay(750)

        self.player.movement = Movement.walking
        self.player.update()

        for step in range(4):
            self.player.spriteIdx = 3
            self.movePlayer(Direction.down, detectGrass=False)

        pg.time.delay(500)
        self.movePlayer(Direction.down, detectGrass=False)
        self.detectGrassCollision(battle=True)

        while True:
            pg.time.delay(1000)
            pg.event.pump()

    def save(self):
        # save_temp = f"game_data/save_states/save_{self.save_slot}_temp"
        save_dir = f"game_data/save_states/save_state_{self.save_slot}"
        save_error = False
        if not os.path.exists(save_dir):
            os.mkdir(save_dir)

        try:
            # write team json file
            with open(os.path.join(save_dir, "team.json"), "w") as write_file:
                json.dump([pk.get_json_data() for pk in self.team], write_file, indent=4)

            # need to set all pygame surfaces to none
            self.game_display = None
            self.animations = None
            self.loadDisplay = None

            # the remove all object surfaces
            self.player.clear_surfaces()
            self.pokedex.clear_surfaces()
            self.poketech.clear_surfaces()

            self.bag = None
            # self.menu_objects = None
            self.team = None

            self.window = None
            self.topSurf = None
            self.bottomSurf = None

            if self.battle:
                self.battle.clear_surfaces()
                self.battle = None # battle loading not yet implemented

            self.menu_objects = None

            with open(os.path.join(save_dir, "game_temp.pickle"), 'wb') as f:
                pickle.dump(self, f)
                print("Successfully pickled")
                shutil.copyfile(
                    os.path.join(save_dir, "game_temp.pickle"),
                    os.path.join(save_dir, "game.pickle")
                )
                os.remove(os.path.join(save_dir, "game_temp.pickle"))

        except TypeError as e:
            save_error = True
            self.log.add_event(GameEvent("Pickle failed", GameEventType.error))
            self.log.add_event(GameEvent(str(e.__dict__), GameEventType.error))
            warnings.warn("Pickle Failed...\nThe data was not overwritten")
            # raise e
        if not save_error:
            self.log.add_event(GameEvent("game save successfully"))
        self.log.write_log(log_dir=self.log_dir)

    def save_and_exit(self):
        self.save()
        sys.exit(0)
