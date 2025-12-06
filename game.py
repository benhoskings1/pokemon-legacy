import os
import json
import random
import shutil
import sys
import warnings
import time
import pickle
from datetime import datetime

from dataclasses import dataclass

import pandas as pd
import pygame as pg

from engine import pokemon_generator, item_generator

from engine.bag.bag import BagV2
from engine.battle.battle import Battle, BattleOutcome
from engine.game_world.game_map import TallGrass
from engine.game_world.game_obejct import PokeballTile
from engine.pokedex.pokedex import Pokedex
from engine.game_log.game_log import GameLog, GameEvent, GameEventType

from displays.load_display import LoadDisplay
from engine.general.controller import Controller
from engine.general.Time import Time
from engine.general.Route import Route
from engine.general.utils import Colours, wait_for_key

# ======= Load displays =====
from displays.game_display import GameDisplay, GameDisplayStates
from displays.menu.menu_display_team import MenuTeamDisplay
from engine.bag.menu_display_bag import MenuBagDisplay

from engine.characters.character import Movement, Direction
from engine.characters.npc import NPC, ProfessorRowan
from engine.characters.trainer import Trainer, Rival, Dawn
from engine.characters.player import Player2

from engine.storyline.game_action import *
from engine.storyline.game_state import GameState, build_game_state_machine
from engine.storyline.story_event import *

from engine.pokemon.pokemon import Pokemon

from engine.poketech.poketech import Poketech
from engine.pokemon.team import Team


pokedex = pd.read_csv("game_data/pokedex/Local Dex.tsv", delimiter='\t', index_col=1)


@dataclass
class GameConfig:
    # active stats
    text_speed: float = 3.0
    graphics_scale: float = 1.0

    render_mode: int = 0
    explore_mode: bool = False

    # save config
    save_slot: None | int = None
    overwrite_mode: bool = False


class Game:

    def __init__(
            self,
            new=False,
            overwrite=False,
            save_slot=1,

            game_state: GameState = GameState.going_to_lake_verity,
            cfg: GameConfig = GameConfig(),
    ):

        self.cfg = cfg

        self.overwrite: bool = overwrite
        self.save_slot: int = save_slot
        self.running: bool = True

        self.data_path: str = f"game_data/save_states/{'save_state_' + str(save_slot) if not new else 'start'}"

        native_size = pg.Vector2(256, 382)
        self.graphics_scale = 2

        self.displaySize = native_size * self.graphics_scale

        self.player = Player2(
            team=Team(),
            bag=BagV2(),
            scale=self.graphics_scale,
        )

        # initialise the display properties
        self.window: None | pg.Surface  = None
        self.topSurf: None | pg.Surface  = None
        self.bottomSurf: None | pg.Surface = None
        self.loadDisplay: None | LoadDisplay = None
        self.game_display = None

        self.load_displays()
        self.game_display = GameDisplay(
            self.topSurf.get_size(),
            self.player,
            window=self.topSurf,
            scale=self.graphics_scale,
            render_mode=self.cfg.render_mode
        )

        self.animations = {}

        # ==== PICKLE DATA INITIALISATION ====
        self.game_state_machine = build_game_state_machine(initial=game_state)

        self.battle = None

        self.controller = Controller()
        self.poketech = Poketech(self.topSurf.get_size(), self.time, team=self.player.team, scale=self.graphics_scale)
        self.pokedex = Pokedex(self)
        self.pokedex.data.loc[[pk.name for pk in self.player.team], "appearances"] += 1
        self.pokedex.load_surfaces()

        # ========== DISPLAY INITIALISATION =========

        self.menu_objects = {
            GameDisplayStates.pokedex: self.pokedex,
            GameDisplayStates.team: MenuTeamDisplay(self.displaySize, self.graphics_scale, self),
            GameDisplayStates.bag: MenuBagDisplay(self.displaySize, self.graphics_scale, self),
        }

        self.menu_active = False

        # === initialise the game characters ===
        self.rival = Rival(scale=self.graphics_scale)
        self.professor_rowan = ProfessorRowan(scale=self.graphics_scale)
        self.dawn = Dawn(scale=self.graphics_scale)

        self.storyline_events = [
            SelectStarterPokemon()
        ]

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

        self.game_display.fade_to_black(self.topSurf, self.bottomSurf, 500)

    # GET JSON
    def _get_json_data(self):
        game_state = {
            "game_state": self.game_state_machine.current_state_value.name,
            "player": self.player.get_json_data(),
            "game_display": self.game_display.get_json_data(),
        }

        return game_state

    def _load_from_save_state(self):
        if self.cfg.save_slot:
            save_file = f"game_data/save_states/save_state_{self.cfg.save_slot}/game_state.json"
        else:
            save_file = f"game_data/save_states/start/game_state.json"

        save_data = json.load(open(save_file))
        self.game_state_machine = build_game_state_machine(initial=GameState[save_data.get("game_state", "new_game")])

        self.player.load_from_state(save_data.get("player"))

        active_map = save_data["game_display"]["map_name"]
        active_collection = save_data["game_display"]["collection_name"]
        self.game_display = GameDisplay(
            self.topSurf.get_size(),
            self.player,
            window=self.topSurf,
            scale=self.graphics_scale,
            render_mode=self.cfg.render_mode,
            start_map=active_map,
            start_collection=active_collection,
        )

        self.load_game_state()
        self.game_display.load_from_state(save_data)

    # === GAME SETUP ===
    def __getstate__(self):
        save_file = f"game_data/save_states/save_state_{self.cfg.save_slot}/game_state.json"
        with open(save_file, "w") as f:
            json.dump(self._get_json_data(), f, indent=4)

        self.window = None
        self.topSurf = None
        self.bottomSurf = None

        # need to set all pygame surfaces to none
        self.game_display = None
        self.animations = None
        self.loadDisplay = None

        self.menu_objects = None

        self.game_state_machine = None

        return self.__dict__

    def __setstate__(self, state: dict):
        self.__dict__.update(state)
        self.running = True
        self.load_displays()
        self._load_from_save_state()

    # === DYNAMIC PROPERTIES ===
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
    def create_pokemon(
            name,
            **kwargs
    ):
        return pokemon_generator.generate_pokemon(name, **kwargs)

    def load_displays(self):
        self.window = pg.display.set_mode(self.displaySize)
        self.topSurf = self.window.subsurface(((0, 0), (self.displaySize.x, self.displaySize.y / 2)))
        self.bottomSurf = self.window.subsurface(((0, self.displaySize.y / 2),
                                                  (self.displaySize.x, self.displaySize.y / 2)))
        self.bottomSurf.fill(Colours.white.value)
        self.loadDisplay = LoadDisplay(self.topSurf.get_size())

    def update_display(self, flip=True):
        """ update the game screen """
        self.game_display.refresh()
        self.topSurf.blit(self.game_display.get_surface(), (0, 0))
        self.bottomSurf.blit(self.poketech.get_surface(), (0, 0))
        if flip:
            pg.display.flip()

    def move_player(
            self,
            direction,
            force_battle: bool = False,
            check_direction: bool = True,
            duration: int = 200
    ) -> bool:
        """
        Move the player

        :param direction: the direction to move the player
        :param check_direction: require the player to be facing the moving direction before moving
        :param force_battle: force battle or not
        :param duration: how long to move the player (in milliseconds)
        :return: bool
        """

        map_obj, moved, edge = self.game_display.move_player(
            direction, self.topSurf, check_facing_direction=check_direction, duration=duration
        )

        if moved:
            self.update_display()
            self.player.steps += 1
            self.poketech.pedometerSteps += 1
            self.poketech.update_pedometer()

            if (
                not self.cfg.explore_mode
                and isinstance(map_obj, TallGrass)
                and self.game_state_machine.current_state_value > GameState.going_to_lake_verity
            ):
                grass = map_obj
                num = random.randint(0, (1 if force_battle else 255))
                if num < grass.encounterNum:
                    pg.time.delay(100)
                    self.game_display.battle_intro(self.topSurf, self.bottomSurf, 250)
                    self.start_battle(route=grass.route)

            if isinstance(map_obj, Trainer):
                trainer = map_obj
                interaction = trainer.interaction(
                    self.game_state_machine.current_state_value,
                    player=self.player,
                    auto=True,
                    game_map=self.game_display.map,
                )

                if interaction is not None:
                    self.process_game_interaction(interaction)

            elif isinstance(map_obj, NPC):
                npc = map_obj
                interaction = npc.interaction(
                    self.game_state_machine.current_state_value,
                    player=self.player,
                    auto=True,
                    game_map=self.game_display.map,
                )

                if interaction is not None:
                    self.process_game_interaction(interaction)

            story_event = self.check_story_triggers()
            if story_event is not None:
                if isinstance(story_event, SelectStarterPokemon):
                    game_events = story_event.run_event(
                        characters=[self.player, self.rival, self.professor_rowan, self.dawn],
                    )
                    self.process_game_interaction(game_events)


        self.player.facing_direction = direction
        self.update_display()

        if not moved:
            # add an optional delay here
            pg.time.delay(100)

        return moved

    def start_battle(
            self,
            foe_team: None | list[Pokemon] | Team = None,
            route="Route 201",
            trainer=None
    ) -> None:
        """ Start a battle. """
        if not foe_team:
            route = Route(route)
            wild_name, wild_level = route.encounter(self.time)
            wild_pk: Pokemon = self.create_pokemon(wild_name, level=wild_level)
            foe_team = [wild_pk]

        for pk in foe_team:
            self.pokedex.data.loc[pk.name, "appearances"] += 1

        self.log.add_event(GameEvent(name=f"battle started against {foe_team}", event_type=GameEventType.game))
        self.battle = Battle(self, self.player.team, foe_team, route_name=route, trainer=trainer)
        outcome = self.battle.run()

        if outcome == BattleOutcome.quit:
            self.running = False
        else:
            self.battle = None
            self.log.add_event(GameEvent(name=f"battle completed with outcome {outcome}", event_type=GameEventType.game))

        if trainer is not None:
            trainer.battled = True

    def battle_intro(
            self,
            time_delay
    ):
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

    def wait_for_key(
            self,
            *,
            key: int = None,
            break_on_timeout: bool=True
    ) -> bool:
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

    def display_message(
            self,
            text: str
    ):
        """
        Add a message to the game screen.
        Delivered via the active TiledMap.

        :param text: The text to display
        """
        self.game_display.map.display_message(text, self.topSurf, speed=self.cfg.text_speed)

    def process_game_interaction(self, interaction: list[GameAction]):
        for action in interaction:
            if action.action_type == GameActionType.move:
                action: MoveAction

                if action.actor == self.player:
                    self.move_player(action.direction, check_direction=False)
                else:
                    action.actor.facing_direction = action.direction
                    self.game_display.move_trainer(
                        action.actor, action.direction, self.topSurf,
                        step_count=action.steps, move_duration=action.duration,
                        ignore_solid_objects=action.ignore_solid_objects
                    )

                action.actor._moving = False

            elif action.action_type == GameActionType.talk:
                action: TalkAction
                for sentence in action.texts:
                    self.display_message(sentence)
                    self.wait_for_key()

            elif action.action_type == GameActionType.attention_bubble:
                action: AttentionAction
                upper_obj_layer = self.game_display.map.object_layers[len(self.game_display.map.object_layers) - 1]
                self.game_display.map.object_layer_sprites[upper_obj_layer.id].add(action.actor.attention_bubble)
                self.game_display.update(force_refresh=True)
                self.update_display()

                pg.time.delay(action.duration)
                self.game_display.map.object_layer_sprites[upper_obj_layer.id].remove(action.actor.attention_bubble)

            elif action.action_type == GameActionType.set_game_state:
                action: SetGameState
                transition_name = f"{self.game_state_machine.current_state_value.name}_to_{action.game_state.name}"
                if hasattr(self.game_state_machine, transition_name):
                    transition = getattr(self.game_state_machine, transition_name)
                    transition()

                    if self.game_state_machine.current_state_value == GameState.following_rival:
                        # now add the rival into the rival house waiting for the player
                        set_map = self.game_display.get_map("floor_1", "rival_house")
                        set_map.add_character(self.rival, position=pg.Vector2(9, 5))
                        self.game_display.update(force_refresh=True)

                    if self.game_state_machine.current_state_value == GameState.going_to_lake_verity:
                        # now add the rival into the rival house waiting for the player
                        set_map = self.game_display.get_map("route_201", "route_orchestrator")
                        print(set_map)
                        set_map.add_character(self.rival, position=pg.Vector2(16, 19))
                        self.rival.visible = True
                        self.game_display.update(force_refresh=True)
                else:
                    print(f"No such transition: {transition_name}")

            elif action.action_type == GameActionType.set_character_visibility:
                self.game_display.map.remove_character(action.actor)

            elif action.action_type == GameActionType.move_camera_position:
                action: MoveCameraPosition
                for tile in range(action.tiles):
                    self.game_display.camera_offset += action.direction.value
                    self.game_display.update(force_refresh=True)
                    self.update_display()
                    pg.time.delay(200)
                    print(self.game_display.camera_offset)

            elif action.action_type == GameActionType.set_facing_direction:
                action.actor.facing_direction = action.direction
                self.game_display.update(force_refresh=True)
                self.update_display()
                pg.time.delay(action.duration)

            self.update_display()

    def loop(self):
        self.load_game_state()

        if self.battle:
            self.battle.update_screen(flip=False)
            # self.game_display.fade_to_black(500, battle=True)
            outcome = self.battle.loop()

            if outcome == BattleOutcome.quit:
                self.running = False
            else:
                self.battle = None
                self.log.add_event(
                    GameEvent(name=f"battle completed with outcome {outcome}", event_type=GameEventType.game))

        else:
            self.update_display(flip=False)
            # self.fade_from_black(500)

        self.update_display()

        while self.running:
            pg.time.delay(25)  # set the debounce-time for keys

            # load poketech clock update

            if self.time.minute != datetime.now().minute:
                self.update_display()

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.running = False

                elif event.type == pg.KEYDOWN:
                    if event.key in self.controller.move_keys:
                        player_moving = True
                        prev_event = event
                        event_2 = event
                        while player_moving:
                            if event_2.type == pg.KEYUP:
                                keys_2 = pg.key.get_pressed()
                                dir_keys = [keys_2[dir_key] for dir_key in self.controller.move_keys]
                                if not keys_2[self.controller.b]:
                                    self.player.movement = Movement.walking
                                    event_2 = prev_event

                                if not any(dir_keys):
                                    player_moving = False
                                else:
                                    event_2 = prev_event

                            elif event_2.type == pg.KEYDOWN:
                                if event_2.key == self.controller.b:
                                    self.player.movement = Movement.running
                                    event_2 = prev_event

                                if event_2.key in self.controller.move_keys:
                                    self.move_player(self.controller.direction_key_bindings[event_2.key])
                                    self.topSurf.blit(self.game_display.get_surface(), (0, 0))

                            poll = pg.event.poll()
                            if poll.type != pg.NOEVENT:
                                # print(f"poll: {poll}")
                                prev_event = event_2
                                event_2 = poll

                        self.player._moving = False
                        self.game_display.update(force_refresh=True)
                        self.topSurf.blit(self.game_display.get_surface(), (0, 0))
                        pg.display.flip()

                    if event.key == self.controller.y:
                        print("looping")
                        action = self.game_display.menu_loop(self)
                        while action:
                            if isinstance(action, GameDisplayStates):
                                if action in self.menu_objects.keys():
                                    self.menu_objects[action].loop()

                            action = self.game_display.menu_loop(self)
                            self.update_display()
                        self.update_display()

                    elif event.key == self.controller.a:
                        obj = self.game_display.map.check_collision(self.player, direction=self.player.facing_direction)
                        if isinstance(obj, NPC):
                            interaction = obj.interaction(self.game_state_machine.current_state_value, auto=False)
                            if interaction is not None:
                                self.process_game_interaction(interaction)

                        elif isinstance(obj, Trainer):
                            trainer = obj
                            if trainer and not trainer.battled and self.player.facing_direction == Direction.up:
                                self.log.add_event(GameEvent(f"Trainer battle with {trainer}", event_type=GameEventType.game))
                                # add display text box

                        elif isinstance(obj, PokeballTile):

                            item = item_generator.generate_item(obj.item)
                            # remove pokeball from map
                            obj.kill()
                            self.game_display.update(force_refresh=True)
                            self.update_display()

                            self.display_message(
                                f"{self.player.name} found an {item.name}"
                            )
                            wait_for_key()
                            self.display_message(
                                f"{self.player.name} put the {item.name} in the"
                                f" {item.item_type.name.upper()} Pocket."
                            )
                            wait_for_key(break_on_timeout=False)
                            self.update_display()

                            self.bag.add_item(item)

                        elif obj:
                            self.game_display.map.object_interaction(obj, self.topSurf)

                elif event.type == pg.MOUSEBUTTONDOWN:
                    relative_pos = pg.Vector2(pg.mouse.get_pos()) - pg.Vector2(0, self.topSurf.get_size()[1])

                    if self.poketech.button.is_clicked(relative_pos):
                        self.poketech.cycle_screens(self.bottomSurf)

                    self.update_display()
                    pg.time.delay(100)

            self.game_display.update()
            self.update_display()

        if self.overwrite:
            self.save()

    def save(self):
        # save_temp = f"game_data/save_states/save_{self.save_slot}_temp"
        save_dir = f"game_data/save_states/save_state_{self.save_slot}"
        save_error = False
        if not os.path.exists(save_dir):
            os.mkdir(save_dir)

        try:
            with open(os.path.join(save_dir, "game_temp.pickle"), 'wb') as f:

                pickle.dump(self, f)
                print("Successfully pickled")
                shutil.copy(
                    os.path.join(save_dir, "game_temp.pickle"),
                    os.path.join(save_dir, "game.pickle")
                )
                # os.remove(os.path.join(save_dir, "game_temp.pickle"))

        except TypeError as e:
            save_error = True
            self.log.add_event(GameEvent("Pickle failed", GameEventType.error))
            self.log.add_event(GameEvent(str(e), GameEventType.error))
            warnings.warn("Pickle Failed...\nThe data was not overwritten")
            raise e

        if not save_error:
            self.log.add_event(GameEvent("game save successfully"))
        self.log.write_log(log_dir=self.log_dir)

    def save_and_exit(self):
        self.save()
        sys.exit(0)

    def load_game_state(self):
        print(f"Loading game state... {self.game_state_machine.current_state_value}")

        if self.game_state_machine.current_state_value == GameState.new_game:
            # initialise the other Dynamic NPCs
            self.rival.map_positions[self.game_display.route_orchestrator.map] = pg.Vector2(11, 11)
            add_layer = self.game_display.route_orchestrator.map.object_layers[0]
            self.game_display.route_orchestrator.map.object_layer_sprites[add_layer.id].add(self.rival)

        if self.game_state_machine.current_state_value == GameState.going_to_lake_verity:
            # initialise the other Dynamic NPCs
            lake_verity = self.game_display.get_map("verity_lakefront", "route_orchestrator")

            self.professor_rowan.map_positions[lake_verity] = pg.Vector2(10, 10)
            self.dawn.map_positions[lake_verity] = pg.Vector2(11, 10)
            self.rival.map_positions[lake_verity] = pg.Vector2(9, 21)
            add_layer = lake_verity.object_layers[0]

            lake_verity.object_layer_sprites[add_layer.id].add(self.rival)
            lake_verity.object_layer_sprites[add_layer.id].add(self.professor_rowan)
            lake_verity.object_layer_sprites[add_layer.id].add(self.dawn)

            print(self.dawn.map_positions)

    def check_story_triggers(self):
        def check_trigger_activated(trigger: MapInteraction):
            subject = None
            if trigger.game_state and self.game_state_machine.current_state_value != trigger.game_state:
                return False

            if trigger.character_name == "player":
                subject = self.player

            if subject is not None:
                game_map = self.game_display.get_map(trigger.map_name, trigger.collection_name)
                # scale the interaction rect to that of the map
                interact_rect = pg.Rect(
                    pg.Vector2(trigger.rect.topleft)*game_map.map_scale,
                    pg.Vector2(trigger.rect.size)*game_map.map_scale
                )
                if interact_rect.colliderect(subject.map_rects[game_map]):
                    return True

            return False

        for story_event in self.storyline_events:
            if check_trigger_activated(story_event.trigger_criteria):
                return story_event

        return None

