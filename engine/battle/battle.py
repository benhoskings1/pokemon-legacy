import importlib.resources as resources
import datetime
import math
from math import floor
from random import randint, choice

from game_logic.battle_action import BattleAttack, BattleTagIn
from displays.battle.battle_display_main import BattleDisplayMain, LevelUpBox
from displays.battle.battle_display_touch import *
from displays.battle.learn_move_display import LearnMoveDisplay
from displays.battle.battle_catch_display import BattleCatchDisplay

from general.utils import *
from general.Condition import StatusCondition
from general.Environment import Environment
from general.Item import Item, Pokeball, MedicineItem
from general.Move import Move2
from general.Status_Conditions.Burn import Burn
from general.Status_Conditions.Poison import Poison
from engine.pokemon.pokemon import Pokemon
from engine.pokemon.team import Team

from engine.characters.trainer import Trainer

MODULE_PATH = resources.files(__package__)


class State(Enum):
    home = 0
    fight = 1
    bag = 2
    run = 3
    pokemon = 4
    learnMove = 5
    evolve = 6


class BattleOutcome(Enum):
    quit = -1
    run = 0
    foe_ko = 1      # this is team based
    friendly_ko = 2 # this is team based
    catch = 3


class Battle:
    def __init__(self, game, friendly_team: Team | list[Pokemon], foe_team: Team | list[Pokemon],
                 environment=Environment.grassland, route_name="Route 201", pickle_data=None, trainer: Trainer=None):
        self.game = game
        self.running = True
        self.battle_location = route_name

        self.friendly_team = friendly_team
        self.foe_team = foe_team if isinstance(foe_team, Team) else Team(foe_team)

        # print(self.foe_team)

        self.trainer = trainer
        self.trainer_battle = True if isinstance(trainer, Trainer) else False

        # set up the displays
        self.friendly: Pokemon = self.friendly_team.get_active_pokemon()
        self.foe: Pokemon = self.foe_team[0]

        self.played_pokemon: set[Pokemon] = {self.friendly}

        self.screenSize = pg.Vector2(game.topSurf.get_size())

        self.environment = pickle_data.environment if pickle_data else environment
        self.state = pickle_data.state if pickle_data else State.home

        self.battle_display: None | BattleDisplayMain = None
        self.touch_displays = None
        self.active_touch_display = None
        self.lowerScreenBase = None

        self.load_displays(game)
        self.update_screen(cover=True)


    def __getstate__(self):
        self._clear_surfaces()
        return self.__dict__

    def __setstate__(self, state):
        self.game = None
        self.__dict__.update(state)

    @property
    def active_pokemon(self):
        return [self.friendly, self.foe]

    def load_displays(self, game):
        self.game = game

        self.battle_display = BattleDisplayMain(game.topSurf, self.screenSize, game.time_of_day, self.environment)
        self.battle_display.add_pokemon_sprites(self.active_pokemon)

        self.touch_displays = {
            TouchDisplayStates.home: BattleDisplayTouch(game.bottomSurf, self.screenSize,
                                                        game.graphics_scale),
            TouchDisplayStates.fight: BattleDisplayFight(game.bottomSurf, self.screenSize,
                                                         game.graphics_scale),
            TouchDisplayStates.bag: BattleDisplayBag(game.bottomSurf, self.screenSize, game.bag,
                                                     game.graphics_scale),
            TouchDisplayStates.team: BattleDisplayTeam(self.screenSize, self.friendly_team, game.graphics_scale),
        }

        self.touch_displays[TouchDisplayStates.fight].load_move_sprites(self.friendly.moves)
        self.active_touch_display = self.touch_displays[TouchDisplayStates.home]

        lower_screen_base = pg.image.load("Images/Battle/Other/Lower Base.png")
        self.lowerScreenBase = pg.transform.scale(lower_screen_base, game.bottomSurf.get_size())

    # ======== GRAPHICS HANDLERS =========
    def update_upper_screen(self):
        self.game.topSurf.blit(self.battle_display.get_surface(show_sprites=True), (0, 0))

    def update_lower_screen(self, cover=False):
        if cover:
            self.game.bottomSurf.blit(self.lowerScreenBase, (0, 0))
        else:
            self.game.bottomSurf.blit(self.active_touch_display.get_surface(show_sprites=True), (0, 0))

    def update_screen(self, cover=False, flip=True):
        self.update_upper_screen()
        self.update_lower_screen(cover)
        if flip:
            pg.display.flip()

    def learn_move(self, move):
        pokemon = self.active_pokemon[0]
        if len(pokemon.moves) < 4:
            self.battle_display.refresh()
            self.update_upper_screen()
            self.display_message(f"{pokemon.name} learned {move.name.title()}!", duration=2000)
            pokemon.moves.append(move)
        else:
            learn_display = LearnMoveDisplay(self.screenSize, pokemon, move, scale=2)
            forget_move = learn_display.select_action(battle=self)

            if forget_move:
                print(forget_move)
                self.display_message("1 2 and... ... Poof!", duration=2000)
                self.display_message(f"{pokemon.name} forgot how to use {forget_move.name}.", duration=2000)
                self.display_message("And...", duration=2000)
                self.display_message(f"{pokemon.name} learned {move.name}!", duration=2000)

                # replace the pokemon's move
                self.active_pokemon[0].moves[pokemon.moves.index(forget_move)] = move

            else:
                self.display_message(f"{pokemon.name} did not learn {move.name}", duration=2000)

    def wait(self, duration):
        """ Wait for the given time in milliseconds"""
        start = time.monotonic()

        duration = duration / 1000
        while time.monotonic() - start < duration:
            self.update_screen(cover=True)

    # ======== BATTLE FUNCTIONS ==========
    def attack(self, attacker: Pokemon, target: Pokemon, move):

        display_time, graphics_time, attack_time, effect_time = 1000, 500, 1000, 1000

        frames = 100
        attack_time_per_frame = attack_time / frames

        [damage, effective, inflictCondition, heal, modify, hits, crit] = attacker.use_move(move, target)

        damage = min([target.health, damage])

        self.game.bottomSurf.blit(self.lowerScreenBase, (0, 0))

        hit_count = 0
        for hit in range(hits):
            if not target.is_koed:
                hit_count += 1
                if hit == 0:
                    self.display_message(f"{attacker.name} used {move.name}!", display_time)
                else:
                    self.display_message(None, display_time)

                # Do attack graphics
                battle_attack = BattleAttack(target=target, move=move, animation_size=self.battle_display.size)
                # self.battle_display.sprites.add(battle_attack)
                self.battle_display.bounce_friendly_stat = False

                if battle_attack.animation:
                    print(battle_attack.frame_count)
                    for frame in range(battle_attack.frame_count):
                        battle_attack.frame_idx = frame
                        battle_attack.update()
                        if battle_attack.animation.frames:
                            self.battle_display.screens["animations"].surface = battle_attack.get_animation_frame(frame)
                        self.game.topSurf.blit(self.battle_display.get_surface(show_sprites=True), (0, 0))
                        pg.display.flip()
                        pg.time.delay(15)
                        self.battle_display.refresh(text=False)

                    self.battle_display.screens["animations"].refresh()

                # Health reduction
                self.reduce_health(target, damage, frames, attack_time_per_frame)
                self.battle_display.bounce_friendly_stat = True

        if heal:
            health = floor(damage * (heal / 100))
            health = max([health, 1])

            attacker.health += health
            if attacker.health > attacker.stats.health:
                attacker.health = attacker.stats.health

            self.display_message(str.format("{} had its energy drained", target.name), 1000)

        if not target.is_koed:
            if inflictCondition:
                for condition in StatusCondition:
                    if condition.value.name == inflictCondition:
                        self.display_message(str.format("The wild {} was {}nd", target.name, inflictCondition), 1000)
                        target.status = condition.value

        if damage != 0:
            if crit:
                self.display_message("A critical hit!", effect_time)

            if hits != 1:
                self.display_message(str.format("Hit {} times(s)", hit_count), effect_time)

            if effective != 1:
                if effective > 1:
                    self.display_message("It's super effective", effect_time)
                else:
                    self.display_message("It's not very effective...", effect_time)

        if not target.is_koed:
            if modify:
                limit = False
                if modify[3] == "Raise":
                    change = modify[0]
                    descriptor = "rose"
                    if abs(change) > 1:
                        descriptor = "sharply rose"
                else:
                    change = -modify[0]
                    descriptor = "fell"
                    if abs(change) > 1:
                        descriptor = "harshly fell"

                if modify[2] == "Self":
                    modified = attacker
                else:
                    modified = target

                if modify[1] == "Attack":
                    modified.stat_stages.attack += change
                    if modified.stat_stages.attack < -6:
                        modified.stat_stages.attack = -6
                        limit = True
                    elif modified.stat_stages.attack > 6:
                        modified.stat_stages.attack = 6
                        limit = True

                elif modify[1] == "Defence":
                    modified.stat_stages.defence += change
                    if modified.stat_stages.defence < -6:
                        modified.stat_stages.defence = -6
                        limit = True
                    elif modified.stat_stages.defence > 6:
                        modified.stat_stages.defence = 6
                        limit = True

                elif modify[1] == "Sp Attack":
                    modified.stat_stages.spAttack += change
                    if modified.stat_stages.spAttack < -6:
                        modified.stat_stages.spAttack = -6
                        limit = True
                    elif modified.stat_stages.spAttack > 6:
                        modified.stat_stages.spAttack = 6
                        limit = True
                elif modify[1] == "Sp Defence":
                    modified.stat_stages.spDefence += change
                    if modified.stat_stages.spDefence < -6:
                        modified.stat_stages.spDefence = -6
                        limit = True
                    elif modified.stat_stages.spDefence > 6:
                        modified.stat_stages.spDefence = 6
                        limit = True
                elif modify[1] == "Speed":
                    modified.stat_stages.speed += change
                    if modified.stat_stages.speed < -6:
                        modified.stat_stages.speed = -6
                        limit = True
                    elif modified.stat_stages.speed > 6:
                        modified.stat_stages.speed = 6
                        limit = True

                start = "" if modified.friendly else "The wild "

                if limit:
                    descriptor = f"won't go any {'higher' if change > 0 else 'lower'}"

                self.display_message(str.format("{}{}'s {} {}", start, modified.name, modify[1], descriptor), 2000)
                direction = "raise" if change > 0 else "lower"
                self.battle_display.render_pokemon_animation(self.game.topSurf, target, f"stat_{direction}", duration=2000)

        target.health = round(target.health)

        self.touch_displays[TouchDisplayStates.team].update_stats()

    def display_message(self, text: str | None, duration=1000):
        self.battle_display.update_display_text(text)
        self.update_upper_screen()
        self.game.bottomSurf.blit(self.lowerScreenBase, (0, 0))
        pg.display.flip()

        for char_idx in range(1, len(text)+1):
            self.battle_display.update_display_text(text, max_chars=char_idx)
            self.update_upper_screen()
            self.game.bottomSurf.blit(self.lowerScreenBase, (0, 0))
            pg.display.flip()
            self.wait(round(duration * 0.7 / len(text)))

        self.wait(duration * 0.3)

    def fade_out(self, duration):
        black_surf = pg.Surface(self.screenSize)
        black_surf.fill(Colours.black.value)
        black_surf.set_alpha(0)
        count = 100
        for t in range(0, count):
            black_surf.set_alpha(round(t / count * 255))
            pg.time.delay(int(duration / count))
            self.game.topSurf.blit(black_surf, (0, 0))
            self.game.bottomSurf.blit(black_surf, (0, 0))
            pg.display.flip()

    def foe_ko(self) -> None | BattleOutcome:
        self.friendly.update_evs(self.foe.name)
        self.update_upper_screen()
        pg.display.flip()
        self.ko_animation(1500, self.foe)

        frames, duration = 100, 1500
        exp_gain = round(self.foe.get_faint_xp() / len(self.played_pokemon))

        for pk in self.played_pokemon:
            self.display_message(f"{pk.name} gained {exp_gain} Exp.", duration=2000)
            for frame in range(frames):
                pk.exp += exp_gain / frames
                self.battle_display.render_pokemon_details()
                self.update_upper_screen()
                pg.display.flip()
                pg.time.delay(int(duration / frames))
                if pk.exp >= pk.level_up_exp:
                    self.level_up_friendly(pk, 1000)
                    new_moves = pk.get_new_moves()
                    if new_moves:
                        for move in new_moves:
                            self.learn_move(move)

            pk.exp = round(pk.exp)

        if self.foe_team.all_koed:
            return BattleOutcome.foe_ko
        else:
            self.foe = choice(self.foe_team.alive_pokemon)
            # apply battle tag in for the foe!
            self.foe.visible = True
            self.battle_display.screens["stats"].sprites.empty()
            self.battle_display.add_pokemon_sprites(self.active_pokemon)
            print(f"new pokemon {repr(self.foe)}")
            return None

    def friendly_ko(self):
        # self.battleDisplay.text = str.format("{} fainted!", self.friendly.name)
        self.update_upper_screen()
        pg.display.flip()
        self.ko_animation(1500, self.friendly)

    def level_up_friendly(self, pokemon: Pokemon, duration=1000):

        prev_stats = pokemon.stats
        pokemon.level_up()
        new_stats = pokemon.stats
        pokemon.health += new_stats.health - prev_stats.health

        self.display_message(f"{pokemon.name} grew to Lv. {pokemon.level}!", duration=duration)

        for old_stats in [prev_stats, None]:
            level_up_box = LevelUpBox("level_up", self.game.graphics_scale, new_stats=new_stats, old_stats=old_stats)
            self.battle_display.sprites.add(level_up_box)
            self.update_upper_screen()
            pg.display.flip()
            pg.time.delay(duration)
            level_up_box.kill()

    def quit_check(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                if self.game.overwrite:
                    self.game.save()
                quit()

    def use_item(self, item, target_friendly=True) -> None | BattleOutcome:
        """ Use the selected item. """
        # Ensure that the pokeball targets the friendly Pokémon
        if item.type == "Pokeball":
            target_friendly = False

        self.display_message(str.format("Used the {}", item.name), 1000)

        target = self.friendly if target_friendly else self.foe

        count = self.game.bag.data[item.item_type][item] -1
        self.game.bag.decrement_item(item)

        # self.active_touch_display.update_container(item, count)

        if isinstance(item, Pokeball):
            item: Pokeball
            if target.status:
                if target.status.name == "Sleeping" or target.status.name == "Frozen":
                    status_modifier = 2
                elif target.status.name == "Paralysed" or target.status.name == "Poisoned" or \
                        target.status.name == "Burned":
                    status_modifier = 1.5
                else:
                    status_modifier = 1
            else:
                status_modifier = 1

            a = ((3 * target.stats.health - 2 * target.health) * target.catch_rate * item.modifier * status_modifier) \
                / (3 * target.stats.health)

            b = floor(1048560 / floor(math.sqrt(floor(math.sqrt(floor(16711680 / a))))))

            fail = False
            check = 0
            for check in range(4):
                num = randint(0, 65535)
                if num >= b:
                    fail = True

                if fail:
                    break

            self.battle_display.catch_animation(3000, check)

            if not fail:
                self.display_message(str.format("The wild {} was caught!", target.name), 2000)
                target.catchDate = datetime.datetime.now()
                target.catchLocation = self.battle_location
                target.catchLevel = target.level
                target.friendly = True
                target.visible = False
                self.friendly_team.pokemon.append(target)
                self.game.pokedex.data.loc[target.name, "caught"] = True
                self.running = False
                return BattleOutcome.catch
            else:
                target.image.set_alpha(255)
                return None

        elif isinstance(item, MedicineItem):
            item: MedicineItem
            print(item.heal)
            if item.heal:
                if target.health + item.heal > target.stats.health:
                    heal_amount = target.stats.health - target.health
                else:
                    heal_amount = item.heal

                self.display_message(str.format("{}'s health was restored by {} Points", target.name, int(heal_amount)))

                self.reduce_health(target, -heal_amount, 100, 10)

            if item.status:
                target.status = None
                if item.status == "Burned":
                    self.display_message(str.format("{} was cured of its burn", target.name), 1500)
                elif item.status == "Poisoned":
                    self.display_message(str.format("{} was cured of its poison", target.name), 1500)
                elif item.status == "Sleeping":
                    self.display_message(str.format("{} woke up", target.name), 1500)

        return None

    def check_kos(self) -> list[Pokemon] | BattleOutcome:
        """Return any Pokémon that are knocked out"""
        return [pk for pk in self.active_pokemon if pk.is_koed]

    def ko_animation(self, duration, pokemon):
        container_type = "friendly" if pokemon.friendly else "foe"
        move_direction = 1 if pokemon.friendly else -1

        stat_container = self.battle_display.screens["stats"].get_object(f"{container_type}_stats")
        container_size = stat_container.image.get_size()[0]

        initial_position = stat_container.rect.topleft

        count = 100
        for frame in range(0, count):
            opacity = (1 - frame / count) * 255
            pokemon.image.set_alpha(opacity)

            stat_container.rect.topleft = initial_position + pg.Vector2(move_direction * frame * (container_size / count), 0)

            self.update_upper_screen()
            pg.display.flip()
            pg.time.delay(int(duration / count))

        self.foe.visible = False
        stat_container.kill()

    def reduce_health(self, target, damage, frames, delay):
        start_health = target.health
        for frame in range(frames):
            target.health = max(0, target.health - damage / frames)
            self.battle_display.render_pokemon_details()
            self.update_upper_screen()
            pg.display.flip()
            pg.time.delay(int(delay))

        target.health = max([0, start_health - damage])

    def select_action(self):
        def process_input(res):
            if res[0] == "container" and res[1] in self.touch_displays.keys():
                self.state = res[1]
                self.active_touch_display = self.touch_displays[res[1]]
                self.update_screen()

            elif res[0] == "container" and self.state == TouchDisplayStates.bag:
                self.active_touch_display = self.touch_displays[TouchDisplayStates.bag].sub_displays[res[1]]
                self.update_screen()

            elif res[0] == "container" and res[1] == "run":
                if self.trainer_battle:
                    self.display_message("No! There's no running from a trainer battle!", 1500)

                elif self.friendly.stats.speed > self.foe.stats.speed:
                    self.display_message("Successfully fled the battle", 1500)
                    return BattleOutcome.run
                else:
                    self.display_message("Couldn't Escape!", 1500)

                self.battle_display.update_display_text(f"What will {self.friendly.name} do?")
                return None

            elif res[0] == "container" and res[1] == TeamDisplayStates.select:
                self.active_touch_display = self.touch_displays[TouchDisplayStates.team].sub_displays[TeamDisplayStates.select]
                display_pk_idx = self.touch_displays[TouchDisplayStates.team].select_idx
                pk_select = self.friendly_team.pokemon[display_pk_idx]
                self.active_touch_display.load_pk_details(pk_select)

            elif res[0] == "container" and (res[1] == TeamDisplayStates.summary or res[1] == TeamDisplayStates.moves):
                self.active_touch_display = self.touch_displays[TouchDisplayStates.team].sub_displays[res[1]]
                display_pk_idx = self.touch_displays[TouchDisplayStates.team].select_idx
                pk_select = self.friendly_team.pokemon[display_pk_idx]
                self.active_touch_display.refresh()
                self.active_touch_display.load_pk_details(pk_select)

            elif res[0] == "container" and (res[1] == "up" or res[1] == "down"):
                pk_idx = self.touch_displays[TouchDisplayStates.team].select_idx
                if res[1] == "up":
                    pk, self.touch_displays[TouchDisplayStates.team].select_idx = self.friendly_team.get_pk_up(pk_idx)

                else:
                    pk, self.touch_displays[TouchDisplayStates.team].select_idx = self.friendly_team.get_pk_down(pk_idx)

                self.active_touch_display.refresh()
                self.active_touch_display.load_pk_details(pk)
                self.update_screen()

            elif (res[0] == "move_container" or res[0] == "move_summary_select") and isinstance(res[1], Move2):
                self.active_touch_display = self.touch_displays[TouchDisplayStates.team].sub_displays[TeamDisplayStates.move_summary]
                pk_idx = self.touch_displays[TouchDisplayStates.team].select_idx
                self.active_touch_display.load_pk_details(self.friendly_team.pokemon[pk_idx])
                self.active_touch_display.load_move_details(res[1])

            elif res[0] == "move":
                return res[1]  # returns the selected move

            elif res[0] == "item_container":
                item, count = res[1]
                select_display = BattleDisplayItemSelect(self.screenSize, item=item, count=count,
                                                         parent=self.active_touch_display.parent_display_type,
                                                         scale=2)
                self.active_touch_display = select_display
                self.update_screen()

            elif res[0] == "item":
                item = res[1]
                if isinstance(item, MedicineItem):
                    # only these items have the heal attribute
                    if (item.heal and self.friendly.health == self.friendly.stats.health) or \
                            (item.status != self.friendly.status):
                        # print(item.status, self.friendly.status)
                        self.display_message("It will have no effect...", 1500)
                        self.battle_display.update_display_text(f"What will {self.friendly.name} do?")
                        self.update_screen()
                    else:
                        parent_display_type = self.active_touch_display.parent_display_type
                        self.active_touch_display = self.touch_displays[TouchDisplayStates.bag].sub_displays[
                            parent_display_type]
                        return item

                elif isinstance(item, Pokeball) and self.trainer_battle:
                    self.display_message("You cant use that here...", 1500)
                    self.battle_display.update_display_text(f"What will {self.friendly.name} do?")
                    self.update_screen()
                else:
                    return item

            elif res[0] == "pokemon_container" and res[1] is not None:
                pokemon = res[1]
                self.active_touch_display.select_idx = self.friendly_team.get_index(pokemon)
                self.active_touch_display.set_sub_displays()
                self.active_touch_display = self.active_touch_display.sub_displays[TeamDisplayStates.select]
                self.update_screen()

            elif res[0] == "pokemon_select":
                pokemon = res[1]
                print(f"{repr(pokemon)} now in battle")
                return pokemon

        action = None
        pg.event.clear()
        while not action:
            for event in pg.event.get():
                if event.type == pg.MOUSEBUTTONDOWN:
                    pos = pg.mouse.get_pos()
                    pos = pg.Vector2(pos) - pg.Vector2(0, self.battle_display.size.y)
                    clicked = self.active_touch_display.click_test(pos)

                    if clicked:
                        action = process_input(clicked)
                        if action:
                            return action

                elif event.type == pg.KEYDOWN:
                    # send event key to display selector
                    ...

                elif event.type == pg.QUIT:
                    return BattleOutcome.quit

            self.update_screen()

        return action

    def take_turn(self, pokemon: Pokemon, action) -> None | BattleOutcome:
        """ Take battle turn based on action selected """
        if isinstance(action, Move2):
            if pokemon.friendly:
                self.attack(attacker=pokemon, target=self.foe, move=action)
                self.touch_displays[TouchDisplayStates.fight].update_container(action)
            else:
                self.attack(attacker=pokemon, target=self.friendly, move=action)

            return None

        elif isinstance(action, Item):
            res = self.use_item(action, target_friendly=True)
            if res:
                return res

        elif isinstance(action, Pokemon):
            self.tag_in_teammate(action)
            return None

        return None

    def tag_in_teammate(self, teammate: Pokemon):
        self.display_message(f"{self.active_pokemon[0].name} switch out", duration=1000)
        tag_in = BattleTagIn(animation_size=self.screenSize)
        self.battle_display.bounce_friendly_stat = False
        self.friendly.visible = False

        if tag_in.animation:
            for frame in range(tag_in.frame_count):
                tag_in.frame_idx = frame
                tag_in.update()
                if tag_in.animation.frames:
                    self.battle_display.screens["animations"].surface = tag_in.get_animation_frame(frame)
                self.game.topSurf.blit(self.battle_display.get_surface(show_sprites=True), (0, 0))
                pg.display.flip()
                pg.time.delay(15)
                self.battle_display.refresh(text=False)
            self.battle_display.screens["animations"].refresh()

        self.friendly_team.swap_pokemon(self.friendly, teammate)

        # add to list so that we can assign exp
        self.played_pokemon.add(teammate)

        self.touch_displays[TouchDisplayStates.team].load_pk_containers()

        self.friendly = teammate
        self.battle_display.switch_active_pokemon(teammate)
        self.touch_displays[TouchDisplayStates.fight].load_move_sprites(self.friendly.moves)
        self.touch_displays[TouchDisplayStates.fight].refresh()
        self.friendly.visible = True

        self.update_upper_screen()

    def wild_catch_display(self):
        self.display_message(f"{self.foe.name}'s data was added to the pokedex", duration=2000)
        catch_display = BattleCatchDisplay(self.screenSize, self.foe, scale=2)
        self.game.topSurf.blit(catch_display.get_surface(), (0, 0))
        pg.display.flip()
        # wait for key
        self.game.wait_for_key()

    def loop(self) -> BattleOutcome | None:
        """
        Main battle loop.
        :return: Battle outcome
        """
        while self.running:
            # get speed of wild Pokémon
            self.battle_display.update_display_text(f"What will {self.friendly.name} do?")
            friendly_action: BattleOutcome | Pokemon | Item | None = self.select_action()

            # process non-fighting moves
            if isinstance(friendly_action, BattleOutcome):
                # path to return battle outcome quit or run.
                return friendly_action

            elif isinstance(friendly_action, Pokemon):
                ...

            foe_action = self.foe.moves[randint(0, len(self.foe.moves) - 1)]

            order: list[Pokemon] = sorted(self.active_pokemon, key=lambda pk: pk.stats.speed, reverse=True)

            for pk in order:
                if not pk.is_koed:
                    res = self.take_turn(pk, friendly_action if pk.friendly else foe_action)
                    if isinstance(res, BattleOutcome):
                        return res

                    # check if both Pokémon are still alive
                    res = self.check_kos()
                    for pk_ko in res:
                        outcome = self.friendly_ko() if pk_ko.friendly else self.foe_ko()
                        if isinstance(outcome, BattleOutcome):
                            print(outcome)
                            return outcome
                        else:
                            ...

            end = False
            for pokemon in order:
                if not pokemon.is_koed and not end:
                    if pokemon.status:
                        if type(pokemon.status) == Burn:
                            # self.battleDisplay.text = str.format("{} is hurt by its burn", pokemon.name)
                            self.reduce_health(pokemon, pokemon.status.damage * pokemon.stats.health, 100, 10)
                        elif type(pokemon.status) == Poison:
                            pokemon.health -= pokemon.status.damage * pokemon.stats.health
                            self.display_message(str.format("{} is hurt by its poison", pokemon.name), 1000)

            self.check_kos()

            self.state = State.home

            self.active_touch_display = self.touch_displays[TouchDisplayStates.home]
            self.update_screen()

        return None

    def entry_sequence(self) -> None:
        """ Pre-battle animations"""
        if self.game.player.battle_animation.frames is not None:
            player_sprite = self.game.player.battle_sprite
            self.battle_display.screens["animations"].sprites.add(player_sprite)
            self.update_upper_screen()
            pg.display.flip()

            if self.trainer is not None:
                # if self.trainer.battle_font is not None:
                battle_sprite = self.trainer.battle_sprite
                self.battle_display.screens["animations"].sprites.add(battle_sprite)

                self.display_message(
                    f"You are challenged by {self.trainer.trainer_type.name.title()} {self.trainer.name}! ", 2000
                )
                self.display_message(
                    f"{self.trainer.trainer_type.name.title()} {self.trainer.name} sent out {self.foe.name.upper()}!",
                    2000
                )

                x_dist, count = self.battle_display.size.x - battle_sprite.rect.topleft[0], 30
                for i in range(count):
                    # shift the sprite to the right
                    battle_sprite.rect = battle_sprite.rect.move(x_dist / count, 0)
                    self.update_screen(cover=True)
                    self.battle_display.screens["animations"].refresh()
                    pg.time.delay(25)

                battle_sprite.kill()

                self.foe.visible = True
                self.update_screen(cover=True)
                self.battle_display.intro_animations(self.game.topSurf, 2000)

            else:
                self.foe.visible = True
                self.battle_display.intro_animations(self.game.topSurf, 2000)
                self.display_message(f"A wild {self.foe.name.upper()} appeared!", duration=2000)

            self.display_message(f"Go! {self.friendly.name.upper()}!", duration=1000)

            x_dist, frames = player_sprite.rect.right, 30
            for i in range(frames):
                frame_count = (i * len(self.game.player.battle_animation.frames)) // frames
                player_sprite.image = self.game.player.battle_animation.frames[frame_count]
                player_sprite.rect = player_sprite.rect.move(-x_dist / frames, 0)
                self.update_screen(cover=True)
                self.battle_display.screens["animations"].refresh()
                pg.time.delay(25)

            self.battle_display.screens["animations"].sprites.remove(player_sprite)
            player_sprite.image = self.game.player.battle_animation.frames[0]
            self.game.player.reset_battle_sprite()

            # TODO: add pokeball animation

        else:
            print("no battle_animation for the player")

        self.friendly.visible = True
        self.battle_display.bounce_friendly_stat = True

        self.display_message(f"What will {self.friendly.name} do?", 1000)

    def exit_sequence(self, outcome: BattleOutcome | None):
        if outcome == BattleOutcome.catch:
            # add pokemon to the pokedex
            self.wild_catch_display()

        # clear up pk stats
        for pk in self.friendly_team:
            pk.reset_stat_stages()
            pk.visible = False

        self.game.bottomSurf.blit(self.lowerScreenBase, (0, 0))
        pg.display.flip()
        self.fade_out(1000)

        self.friendly.visible = False

    def run(self):
        self.entry_sequence()

        outcome = self.loop()

        if outcome == BattleOutcome.quit:
            return outcome

        self.exit_sequence(outcome)
        return outcome

    def _clear_surfaces(self):
        self.battle_display = None
        self.active_touch_display = None
        self.lowerScreenBase = None
        self.touch_displays = None


if __name__ == '__main__':
    from game import Game
    from engine.bag import BagV2
    from general.Route import Route
    import json

    pg.init()
    pg.event.pump()

    with open("../../test_data/bag/test_bag.json", "r") as read_file:
        bag_data = json.load(read_file)

    demo_game = Game(overwrite=False, new=True)
    print("game loaded")

    demo_game.bag = BagV2(bag_data)

    route = Route("Route 201")

    wild_name, wild_level = route.encounter(demo_game.time)
    wild_pk: Pokemon = demo_game.create_pokemon(wild_name, level=wild_level)

    battle = Battle(demo_game, demo_game.team, foe_team=[wild_pk])

    battle.run()
