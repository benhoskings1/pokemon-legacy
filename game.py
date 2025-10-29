import json
import random
import shutil
import sys
import time
import warnings
from datetime import datetime

from bag import BagV2
from battle import Battle, State, BattleOutcome
from maps.game_map import TallGrass
from maps.pokecenter import PokeCenter
from pokedex import Pokedex
from game_log.game_log import GameLog, GameEvent, GameEventType

from displays.load_display import LoadDisplay
from general.Animations import createAnimation
from general.utils import *
from general.controller import Controller
from general.Time import Time
from general.Route import Route

# ======= Load displays =====
from displays.game_display import GameDisplay, GameDisplayStates
from displays.menu.menu_display_team import MenuTeamDisplay
from displays.menu.menu_display_bag import MenuBagDisplay


from trainer import Trainer, Player2, Movement, Direction
from pokemon import Pokemon

from pokemon_module.pokemon_generator import PokemonGenerator

from poketech.poketech import Poketech
from team import Team


pokedex = pd.read_csv("game_data/pokedex/Local Dex.tsv", delimiter='\t', index_col=1)


class Game:
    def __init__(self, new=False, overwrite=False, save_slot=1):

        self.overwrite: bool = overwrite
        self.save_slot: int = save_slot
        self.running: bool = True

        self.data_path: str = f"game_data/save_states/{'save_state_' + str(save_slot) if not new else 'start'}"

        native_size = pg.Vector2(256, 382)
        self.graphics_scale = 2

        self.displaySize = native_size * self.graphics_scale

        # initialise the display properties
        self.window: None | pg.Surface  = None
        self.topSurf: None | pg.Surface  = None
        self.bottomSurf: None | pg.Surface = None
        self.loadDisplay: None | LoadDisplay = None

        self.load_displays()

        self.animations = {}

        # ==== JSON FILE INITIALISATION ====
        with open(os.path.join(self.data_path, "bag.json"), "r") as read_file:
            # Convert JSON file to Python Types
            bag_data = json.load(read_file)
        self.bag = BagV2(bag_data)

        with open(os.path.join(self.data_path, "team.json"), "r") as read_file:
            # Convert JSON file to Python Types
            team_data = json.load(read_file)
        self.team = Team(team_data)

        # ==== PICKLE DATA INITIALISATION ====
        game_data = None

        if not new and not os.path.exists(os.path.join(self.data_path, "game.pickle")):
            print("No pickle data not present / corrupted")

        elif not new and os.path.exists(os.path.join(self.data_path, "game.pickle")):
            with open(os.path.join(self.data_path, "game.pickle"), 'rb') as game_file:
                game_data = pickle.load(game_file)

            self.load_displays()

            self.player = game_data.player
            self.poketech = game_data.poketech

            self.battle = game_data.battle if game_data.battle else None
            if self.battle:
                self.battle.load_displays(self)

        else:
            self.player = Player2(position=pg.Vector2(31, 14), team=self.team, scale=self.graphics_scale)
            self.poketech = Poketech(self.topSurf.get_size(), self.time, team=self.team, scale=self.graphics_scale)
            self.battle = None

        # ========== DISPLAY INITIALISATION =========
        self.controller = Controller()
        self.pokedex = Pokedex(self) if not game_data else game_data.pokedex
        if new:
            self.pokedex.data.loc[[pk.name for pk in self.team], "appearances"] += 1

        self.pokedex.load_surfaces()

        self.game_display = GameDisplay(self.topSurf.get_size(), self.player, window=self.topSurf,
                                        scale=self.graphics_scale)

        self.menu_objects = {
            GameDisplayStates.pokedex: self.pokedex,
            GameDisplayStates.team: MenuTeamDisplay(self.displaySize, self.graphics_scale, self),
            GameDisplayStates.bag: MenuBagDisplay(self.displaySize, self.graphics_scale, self),
        }

        self.menu_active = False

        # ==== LOG INITIALISATION ====
        self.log, self.log_dir = GameLog(), "game_data/logs"
        self.log.add_event(GameEvent(name="startup complete"))

        # ========== POST INITIALISATION =========
        # happens after all attributes initialised
        self.loadDisplay.finish()
        top, bottom = self.loadDisplay.getScreens()
        self.topSurf.blit(top, (0, 0))
        self.bottomSurf.blit(bottom, (0, 0))
        pg.display.flip()
        pg.time.delay(750)

        self.fade_to_black(500)

    def __getstate__(self):
        self.window = None
        self.topSurf = None
        self.bottomSurf = None

        # the remove all object surfaces
        self.pokedex.clear_surfaces()

        # need to set all pygame surfaces to none
        self.game_display = None
        self.animations = None
        self.loadDisplay = None

        self.bag = None
        self.menu_objects = None

        return self.__dict__

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.load_displays()

    @property
    def time(self):
        return datetime.now()

    @property
    def time_of_day(self):
        if 6 < self.time.hour <= 16:
            return Time.day
        elif 16 < self.time.hour <= 20:
            return Time.evening
        else:
            return Time.night

    @staticmethod
    def create_pokemon(name, friendly=False, level=None, exp=None, evs=None, ivs=None, shiny=None,):
        # TODO: create generator object that holds animations in memory
        return Pokemon(name, level=level, exp=exp, EVs=evs, IVs=ivs, friendly=friendly, shiny=shiny)

    def load_displays(self):
        self.window = pg.display.set_mode(self.displaySize)
        self.topSurf = self.window.subsurface(((0, 0), (self.displaySize.x, self.displaySize.y / 2)))
        self.bottomSurf = self.window.subsurface(((0, self.displaySize.y / 2),
                                                  (self.displaySize.x, self.displaySize.y / 2)))
        self.bottomSurf.fill(Colours.white.value)
        self.loadDisplay = LoadDisplay(self.topSurf.get_size())

    def fade_to_black(self, duration):
        black_surf = pg.Surface(self.topSurf.get_size())
        black_surf.fill(Colours.black.value)
        black_surf.set_alpha(0)
        count = 100
        for t in range(0, count):
            black_surf.set_alpha(round(t / count * 255))
            pg.time.delay(int(duration / count))
            self.topSurf.blit(black_surf, (0, 0))
            self.bottomSurf.blit(black_surf, (0, 0))
            pg.display.flip()

    def fade_from_black(self, duration, battle=False):
        black_surf = pg.Surface(self.topSurf.get_size())
        black_surf.fill(Colours.black.value)
        black_surf.set_alpha(255)
        count = 100
        for t in range(0, count):
            black_surf.set_alpha(int((count - t) / count * 255))
            pg.time.delay(int(duration / count))
            if not battle:
                self.update_display(flip=False)
            else:
                if self.battle.state == State.home:
                    self.battle.update_screen(cover=True, flip=False)
                else:
                    self.battle.update_screen(flip=False)

            self.topSurf.blit(black_surf, (0, 0))
            self.bottomSurf.blit(black_surf, (0, 0))
            pg.display.flip()

    def update_display(self, flip=True, cover_lower=False, cover_upper=False):
        """ update the game screen """
        self.game_display.refresh()
        self.topSurf.blit(self.game_display.joint_map_surface, (0, 0))
        self.bottomSurf.blit(self.poketech.get_surface(), (0, 0))
        if flip:
            pg.display.flip()

    def move_player(self, direction, detect_grass=True, force_battle=False) -> bool:
        """ move the player

        :param direction: the direction to move the player
        :param detect_grass: whether to detect grass or not
        :return: bool
        """

        map_obj, moved, edge = self.game_display.move_player(direction, self.topSurf)

        if isinstance(map_obj, PokeCenter):
            map_obj: PokeCenter
            map_obj.loop(self.topSurf)

        if moved:
            self.player.steps += 1
            self.poketech.pedometerSteps += 1
            self.poketech.update_pedometer()

            if detect_grass and isinstance(map_obj, TallGrass):
                grass = map_obj
                num = random.randint(0, (1 if force_battle else 255))
                if num < grass.encounterNum:
                    pg.time.delay(100)
                    self.battle_intro(250)
                    self.start_battle(route=grass.route)

            trainer = map_obj if isinstance(map_obj, Trainer) else None

            if trainer and not trainer.battled:
                # calculate steps towards player!
                trainer: Trainer

                trainer_pos = pg.Vector2(trainer.map_positions[self.game_display.map])
                player_pos = pg.Vector2(self.player.map_positions[self.game_display.map])

                move_count = player_pos.distance_to(trainer_pos)

                upper_obj_layer = self.game_display.map.object_layers[len(self.game_display.map.object_layers) - 1]
                self.game_display.map.object_layer_sprites[upper_obj_layer.id].add(trainer.attention_bubble)
                self.game_display.map.render()
                self.update_display()
                pg.time.delay(1000)
                self.game_display.map.object_layer_sprites[upper_obj_layer.id].remove(trainer.attention_bubble)

                for i in range(round(move_count - 1)):
                    self.game_display.map.move_trainer(trainer, trainer.facing_direction, self.topSurf, move_duration=200)

                self.game_display.map.display_message("May I trouble you for a battle please?", self.topSurf, 2000)
                self.wait_for_key(break_on_timeout=False)
                self.start_battle(foe_team=trainer.team, trainer=trainer)
                trainer.battled = True
                self.update_display()

        self.player.facing_direction = direction
        self.update_display()

        if not moved:
            # add an optional delay here
            return False

        return moved

    def start_battle(self, foe_team: None | list[Pokemon] | Team=None, route="Route 201", trainer=None) -> None:
        """ Start a battle. """
        if not foe_team:
            route = Route(route)
            wild_name, wild_level = route.encounter(self.time)
            wild_pk: Pokemon = self.create_pokemon(wild_name, level=wild_level)
            foe_team = [wild_pk]

        for pk in foe_team:
            self.pokedex.data.loc[pk.name, "appearances"] += 1

        self.log.add_event(GameEvent(name=f"battle started against {foe_team}", event_type=GameEventType.game))
        self.battle = Battle(self, self.team, foe_team, route_name=route, trainer=trainer)
        outcome = self.battle.run()

        if outcome == BattleOutcome.quit:
            self.running = False
        else:
            self.battle = None
            self.log.add_event(GameEvent(name=f"battle completed with outcome {outcome}", event_type=GameEventType.game))

        if trainer is not None:
            trainer.battled = True

    def battle_intro(self, time_delay):
        # TODO: migrate this to game display
        black_surf = pg.Surface(self.topSurf.get_size())
        black_surf.fill(Colours.darkGrey.value)
        for count in range(2):
            self.topSurf.blit(black_surf, (0, 0))
            pg.display.flip()
            pg.time.delay(time_delay)
            self.update_display()
            pg.time.delay(time_delay)

            if count == 0:
                self.bottomSurf.blit(black_surf, (0, 0))

        current_game_display = self.game_display.get_surface()
        left_cut, right_cut = current_game_display, current_game_display.copy()

        # create stripy left/right surfaces
        for i in range(20):
            bar_rect = pg.Rect(0, i * 10 * self.graphics_scale, current_game_display.get_width(), 5 * self.graphics_scale)
            pg.draw.rect(right_cut, pg.Color(0, 0, 0, 0), bar_rect)
            bar_rect = bar_rect.move(0, 5 * self.graphics_scale)
            pg.draw.rect(left_cut, pg.Color(0, 0, 0, 0), bar_rect)

        max_frames = 30
        for frame in range(max_frames):
            black_surf.fill(Colours.black.value)
            offset = (frame+1) * self.game_display.size.x / max_frames
            black_surf.blit(left_cut, (-offset, 0))
            black_surf.blit(right_cut, (offset, 0))
            self.topSurf.blit(black_surf, (0, 0))

            pg.display.flip()
            pg.time.delay(20)

    def wait_for_key(self, key=None, break_on_timeout=True) -> bool:
        key = key if key is not None else self.controller.a

        t0 = time.monotonic()
        pg.event.clear()
        while True:
            event = pg.event.wait()
            if event.type == pg.QUIT:
                self.save_and_exit()

            elif event.type == pg.KEYDOWN:
                if event.key == key:
                    return True

            if time.monotonic() - t0 > 10 and break_on_timeout:
                # timeout at 10s
                return True

    def display_message(self, text, duration=1000):
        self.update_display()
        pg.display.flip()

        for char_idx in range(1, len(text) + 1):
            self.game_display.update_display_text(text, max_chars=char_idx)
            self.update_display()
            pg.display.flip()
            pg.time.delay(round(duration * 0.7 / len(text)))

        self.game_display.sprites.remove(self.game_display.text_box)

    def loop(self):
        if self.battle:
            self.battle.update_screen(flip=False)
            self.fade_from_black(500, battle=True)
            outcome = self.battle.loop()

            if outcome == BattleOutcome.quit:
                self.running = False
            else:
                self.battle = None
                self.log.add_event(
                    GameEvent(name=f"battle completed with outcome {outcome}", event_type=GameEventType.game))

        else:
            self.update_display(flip=False)
            self.fade_from_black(500)

        self.update_display()

        while self.running:
            pg.time.delay(25)  # set the debounce-time for keys
            keys = pg.key.get_pressed()

            if keys[self.controller.up]:
                self.move_player(Direction.up)
            elif keys[self.controller.down]:
                self.move_player(Direction.down)
            elif keys[self.controller.left]:
                self.move_player(Direction.left)
            elif keys[self.controller.right]:
                self.move_player(Direction.right)

            if keys[self.controller.b]:
                self.player.movement = Movement.running
            else:
                if self.player.movement != Movement.walking:
                    self.player.movement = Movement.walking
                    self.player.update()
                    self.update_display()

            # load poketech clock update

            if self.time.minute != datetime.now().minute:
                self.update_display()

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
                            self.update_display()
                        self.update_display()

                    elif event.key == self.controller.a:
                        obj = self.game_display.map.check_collision(self.player, direction=Direction.up)
                        if isinstance(obj, Trainer):
                            trainer = obj
                            if trainer and not trainer.battled and self.player.facing_direction == Direction.up:
                                self.log.add_event(GameEvent(f"Trainer battle with {trainer}", event_type=GameEventType.game))
                                # add display text box

                                self.display_message("May I trouble you for a battle please?", 2000)
                                self.wait_for_key(break_on_timeout=False)
                                self.start_battle(foe_team=trainer.team, trainer=trainer)
                                trainer.battled = True
                                self.update_display()

                elif event.type == pg.MOUSEBUTTONDOWN:
                    relative_pos = pg.Vector2(pg.mouse.get_pos()) - pg.Vector2(0, self.topSurf.get_size()[1])

                    if self.poketech.button.is_clicked(relative_pos):
                        self.poketech.cycle_screens(self.bottomSurf)

                    self.update_display()
                    pg.time.delay(100)

            # TODO: add call to game update for NPC walking/tree shaking etc.

        if self.overwrite:
            self.save()

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

            with open(os.path.join(save_dir, "bag.json"), "w") as write_file:
                json.dump(self.bag.get_json_data(), write_file, indent=4)

            self.team = None

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
            self.log.add_event(GameEvent(str(e), GameEventType.error))
            warnings.warn("Pickle Failed...\nThe data was not overwritten")
            # raise e
        if not save_error:
            self.log.add_event(GameEvent("game save successfully"))
        self.log.write_log(log_dir=self.log_dir)

    def save_and_exit(self):
        self.save()
        sys.exit(0)
