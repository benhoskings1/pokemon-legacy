import pygame as pg

from engine.characters.character import CharacterTypes
from engine.characters.npc import NPC

# from trainer import Trainer, TrainerTypes, NPC
from engine.general.direction import Direction
from engine.general.utils import Colours, wait_for_key
from engine.general.controller import Controller

from engine.game_world.tiled_map import TiledMap2, GameObject, Obstacle, MapLinkTile
from maps.buildings.pokecenter.pokecenter_containers import (
    ConfirmContainer, ConfirmOption, PokeballIncubator,
    ComputerSelector, ComputerSelectOption, ComputerActionSelector,
    ComputerAction
)

from statemachine import StateMachine, State

import importlib.resources as resources
MODULE_PATH = resources.files(__package__)


class DeskTile(GameObject):
    def __init__(self, rect: pg.Rect, obj_id: int, scale=1, render_mode=0):
        GameObject.__init__(self, rect, obj_id, solid=True, scale=scale)
        if render_mode > 0:
            self.image = pg.Surface(self.rect.size, pg.SRCALPHA)
            pg.draw.rect(self.image, Colours.blue.value, self.image.get_rect(), 1)


class ComputerTile(Obstacle):
    def __init__(self, rect: pg.Rect, obj_id: int, scale=1):
        Obstacle.__init__(self, rect, obj_id, scale=scale)


tile_object_mapping = {
    "desk": DeskTile,
    "computer": ComputerTile,
}


class PokeCenter(TiledMap2, MapLinkTile, StateMachine):

    idle = State("idle", initial=True)
    inquiry = State("inquiry")
    selecting_computer = State("selecting_computer")
    selecting_action = State("selecting_action")

    desk_inquiry = idle.to(inquiry, on="start_inquiry_action")
    heal_team = inquiry.to.itself(on="heal_team_action")
    select_computer = idle.to(selecting_computer, on="select_computer_transition")
    select_computer_action = selecting_computer.to(selecting_action, on="select_computer_action_transition")

    rowans_pc = selecting_computer.to.itself(on="rowans_pc_action")

    go_back = (
            inquiry.to(idle, on="cancel_inquiry")
            | selecting_computer.to(idle, on="quit_computer")
            | selecting_action.to(selecting_computer, on="select_computer_transition")
            | idle.to.itself()
    )

    controller = Controller()

    def __init__(self, rect, player, map_scale=1, obj_scale=1, parent_map_scale=1.0):
        size = pg.Vector2(256, 192) * map_scale

        MapLinkTile.__init__(self, rect, obj_id=0, linked_map_name="pokecenter",)

        StateMachine.__init__(self)

        TiledMap2.__init__(
            self,
            "maps/buildings/pokecenter/pokecenter.tmx",
            size,
            player,
            player_position=pg.Vector2(8, 14),
            map_scale=map_scale,
            object_scale=obj_scale,
            player_layer="5_player_layer",
            view_screen_tile_size=pg.Vector2(19, 18),
            map_directory=MODULE_PATH,
        )

        self.base_surface.fill(Colours.black.value)

        self.running = False
        self.render_window = None

        # === INITIALISE CONTAINERS ===
        self.active_selector = None
        self.desk_confirm_container = ConfirmContainer(scale=self.map_scale)
        self.computer_selector = ComputerSelector(scale=self.map_scale)
        self.incubator = PokeballIncubator(scale=self.map_scale)
        self.computer_action_selector = ComputerActionSelector(scale=self.map_scale)

    def __repr__(self):
        return f"PokeCenter({self.rect})"

    # === STATEMACHINE API ===
    # STATE ENTER/EXIT
    def on_exit_selecting_computer(self):
        self.computer_selector.reset()
        self.sprites.remove(self.computer_selector)
        self.update_render_window()

    # TRANSITIONS
    def rowans_pc_action(self):
        self.display_message("Accessed Professor Rowan's PC.", window=self.render_window)
        wait_for_key()
        self.display_message("Hmm...", window=self.render_window)
        wait_for_key()
        self.display_message(f"You've spotted {3} Pokémon in Sinnoh...", window=self.render_window)
        wait_for_key()
        self.display_message(f"Look harder for wild Pokémon.", window=self.render_window)
        wait_for_key()
        self.display_message(f"Don't be afraid of going into tall grass.", window=self.render_window)

    def select_computer_action_transition(self):
        self.sprites.remove(self.computer_selector)
        self.sprites.remove(self.computer_action_selector)
        self.refresh()
        self.display_message(
            "The Pokémon Storage System was accessed.",
            window=self.render_window,
            keep_textbox=True
        )

        self.update_render_window(self.render_window)
        self.sprites.add(self.computer_action_selector)
        text = "Pokémon in your party may be stored in the storage system's Boxes."
        self.update_display_text(text)
        self.update_render_window(self.render_window)

        self.active_selector = self.computer_action_selector
        print(self.active_selector)


    def select_computer_transition(self):
        self.sprites.remove(self.computer_selector)
        self.sprites.remove(self.computer_action_selector)
        self.refresh()

        self.display_message(
            "Which PC should be accessed?",
            self.render_window,
            keep_textbox=True
        )
        self.active_selector = self.computer_selector
        self.sprites.add(self.computer_selector)
        self.update_render_window()

    def quit_computer(self):
        self.sprites.empty()
        self.update_render_window()

    # === END STATEMACHINE TRANSITIONS ===
    def load_objects(self):
        # load default objects
        super().load_objects()

        for layer in self.object_layers:
            sprite_group = self.object_layer_sprites[layer.id]
            for obj in layer:
                rect = pg.Rect(obj.x, obj.y, obj.width, obj.height)

                if obj.type in tile_object_mapping:
                    obj_tile = tile_object_mapping[obj.type](rect, obj.id, scale=self.map_scale)
                    sprite_group.add(obj_tile)

    def object_interaction(self, sprite: pg.sprite.Sprite, render_surface: pg.Surface):
        map_obj, action_complete = super().object_interaction(sprite)
        if map_obj and action_complete:
            return map_obj, True

        elif isinstance(sprite, DeskTile):
            self.desk_interaction(render_surface)

        elif isinstance(sprite, ComputerTile):
            self.computer_interaction(render_surface)

        return None, True

    def update_render_window(self, render=False):
        self.refresh()
        if render:
            self.render()
        self.render_window.blit(self.get_surface(), (0, 0))
        pg.display.flip()

    def heal_team_action(self):
        self.sprites.remove(self.desk_confirm_container)
        self.update_render_window()

        pokecenter_lady: NPC | None = next(
            (npc for npc in self.get_sprite_types(NPC) if npc.character_type == CharacterTypes.pokecenter_lady),
            None
        )

        self.display_message(
            "Ok, I'll take you Pokémon for a few seconds.",
            window=self.render_window,
        )
        pokecenter_lady.facing_direction = Direction.left
        self.update_render_window(render=True)

        self.sprites.add(self.incubator)
        for _ in self.player.team:
            self.incubator.add_pokeball()
            self.update_render_window()
            pg.time.delay(500)

        pg.time.delay(1500)
        self.incubator.reset()
        self.sprites.remove(self.incubator)
        self.update_render_window()
        pg.time.delay(200)

        pokecenter_lady.facing_direction = Direction.down
        self.update_render_window(render=True)

        self.display_message(
            "Thank you for waiting.",
            window=self.render_window,
        )
        wait_for_key()
        self.display_message(
            "We've restored your Pokémon to full health.",
            window=self.render_window,
        )
        # self.render_window.blit(self.get_surface(), (0, 0))
        # pg.display.flip()
        self.player.team.restore()

    def start_inquiry_action(self):
        self.active_selector = self.desk_confirm_container
        self.sprites.add(self.desk_confirm_container)
        self.render_window.blit(self.get_surface(), (0, 0))
        pg.display.flip()

    def cancel_inquiry(self):
        self.desk_confirm_container.reset()
        self.sprites.remove(self.desk_confirm_container)
        self.refresh()
        self.render_window.blit(self.get_surface(), (0, 0))
        pg.display.flip()

        self.display_message(
            "We hope to see you again!",
            window=self.render_window,
        )

    def desk_interaction(self, render_surface: pg.Surface):
        self.display_message(
            "Hello and welcome to the pokecenter.",
            window=render_surface,
        )
        wait_for_key()

        self.display_message(
            "We restore your tired Pokémon to full health.",
            window=render_surface,
        )
        wait_for_key()
        self.display_message(
            "Would you like to rest your Pokémon?",
            window=render_surface,
            keep_textbox=True,
        )
        # wait_for_key()

        self.render_window = render_surface
        self.send("desk_inquiry")

        while self.current_state != self.idle:
            for event in pg.event.get():
                if event.type == pg.KEYDOWN:
                    if event.key in self.controller.move_keys:
                        direction = self.controller.direction_key_bindings[event.key]
                        self.active_selector.process_interaction(direction)

                        render_surface.blit(self.get_surface(), (0, 0))
                        pg.display.flip()

                    elif event.key == self.controller.a:
                        selected = self.active_selector.selected

                        if isinstance(selected, ConfirmOption):
                            if selected == ConfirmOption.yes:
                                self.send("heal_team")
                                wait_for_key()
                                self.send("go_back")

                            else:
                                self.send("go_back")

                    elif event.key == self.controller.b:
                        self.send("go_back")


        self.player.team.restore()
        self.render()

    def computer_interaction(self, render_surface: pg.Surface):
        self.display_message(f"{self.player.name} booted up the PC.", render_surface)
        wait_for_key()
        self.render_window = render_surface

        # self.display_message("Which PC should be accessed?", render_surface, keep_textbox=True)
        # self.active_selector = self.computer_selector
        # self.sprites.add(self.computer_selector)
        # self.update_render_window()
        self.send("select_computer")

        while self.current_state != self.idle:
            for event in pg.event.get():
                if event.type == pg.KEYDOWN:
                    if event.key in self.controller.move_keys:
                        direction = self.controller.direction_key_bindings[event.key]
                        print(direction)
                        self.active_selector.process_interaction(direction)

                        render_surface.blit(self.get_surface(), (0, 0))
                        pg.display.flip()

                    elif event.key == self.controller.a:
                        selected = self.active_selector.selected

                        if isinstance(selected, ComputerSelectOption):
                            if selected == ComputerSelectOption.someones:
                                self.send("select_computer_action")

                            elif selected == ComputerSelectOption.players:
                                ...
                            elif selected == ComputerSelectOption.rowans:
                                self.send("rowans_pc")

                            else:
                                self.send("go_back")

                        elif isinstance(selected, ComputerAction):
                            if selected == ComputerAction.deposit:
                                ...

                            elif selected == ComputerAction.withdraw:
                                ...

                            elif selected == ComputerAction.move_pokemon:
                                ...

                            elif selected == ComputerAction.move_items:
                                ...

                            else:
                                self.send("go_back")

                    elif event.key == self.controller.b:
                        self.send("go_back")

if __name__ == '__main__':
    ...
