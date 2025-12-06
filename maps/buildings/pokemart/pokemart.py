import os
import importlib.resources as resources
from dataclasses import dataclass
import json

from enum import Enum
import pygame as pg
import networkx as nx
from statemachine import StateMachine, State

from engine.general.utils import Colours, wait_for_key
from engine.general import Item
from engine.general.controller import Controller
from engine.general.direction import Direction, opposite_direction_mapping
from engine.graphics.sprite_screen import DisplayContainer
from engine.game_world.tiled_map import TiledMap2, GameObject, MapLinkTile
from maps.buildings.pokemart.pokemart_containers import (
    MoneyContainer, ItemSetContainer, DisplayBar, BagCountContainer, PriceCounter,
    ConfirmContainer, ConfirmOption
)

from engine.general.Item import ItemGenerator


MODULE_PATH = resources.files(__package__)


class PopupOption(Enum):
    buy = 0
    sell = 1
    see_ya = 2


@dataclass(frozen=True)
class SelectorNode:
    """ Properties to store on the selector node"""
    value: Enum
    pos: pg.Vector2 | tuple[int, int]
    scale: int | float = 1.0


# ==== Sprites =======
class ArrowSelector(pg.sprite.Sprite):
    def __init__(self, scale=1):
        super().__init__()
        self.image = pg.image.load("assets/containers/menu/team/popup_arrow.png")
        self.image = pg.transform.scale(
            self.image, pg.Vector2(self.image.get_size()) * scale
        )
        # self.rect = self.image.get_rect()
        # self.rect.topleft = pg.Vector2(7, 9) * scale
        self.sprite_type = "arrow"

        self.selected = PopupOption.buy

        self.scale = scale

        self.option_graph = nx.DiGraph()

        positions = [(7, 9), (7, 25), (7, 41)]

        for option in PopupOption:
            graph_node = SelectorNode(option, positions[option.value], scale=scale)
            self.option_graph.add_node(graph_node)

        self.link_options(PopupOption.buy, PopupOption.sell, Direction.down, reverse=True)
        self.link_options(PopupOption.sell, PopupOption.see_ya, Direction.down, reverse=True)

    @property
    def rect(self):
        selected_node = self.get_map_node(self.selected)
        return pg.Rect(pg.Vector2(selected_node.pos)*selected_node.scale, self.image.get_size())

    def get_map_node(self, option_value: Enum) -> SelectorNode:
        """ Get a map node that matches the map name """
        return next((n for n in self.option_graph.nodes if n.value == option_value), None)

    def link_options(
            self,
            option_1: Enum,
            option_2: Enum,
            direction: Direction,
            reverse=True
    ):
        node_1 = self.get_map_node(option_1)
        node_2 = self.get_map_node(option_2)

        try:
            for n in [node_1, node_2]:
                assert n is not None, (
                    f"{option_1 if n is node_1 else option_2} is not a valid option. "
                    f"Please make sure to link one of these values: "
                    f"{[node.map_name for node in self.option_graph.nodes]}"
                )
        except AssertionError as e:
            raise e

        self.option_graph.add_edge(node_1, node_2, link=direction)  # unpack edge tuple*

        if reverse:
            self.option_graph.add_edge(node_2, node_1, link=opposite_direction_mapping[direction])


    def process_interaction(self, direction: Direction):
        node_neighbors = self.option_graph.adj[self.get_map_node(self.selected)]

        match = next((nbr for nbr, link_dict in node_neighbors.items() if link_dict["link"] == direction), None)
        if match:
            self.selected = match.value

        return match

    def reset(self):
        self.selected = list(self.option_graph.nodes)[0].value


class ActionSelector(DisplayContainer):
    def __init__(self, scale=1.0):
        image_path = os.path.join(MODULE_PATH, "assets/desk_popup_1.png")
        DisplayContainer.__init__(self, image_path, sprite_id=0, pos=pg.Vector2(2, 2), scale=scale)

        self.selector = ArrowSelector(scale=self.scale)
        self.sprites.add(self.selector)

    @property
    def selected(self):
        return self.selector.selected

    def process_interaction(self, direction: Direction):
        self.refresh()
        self.selector.process_interaction(direction)

    def reset(self):
        self.refresh()
        self.selector.reset()


# === nice ===
class DeskTile(GameObject):
    def __init__(self, rect: pg.Rect, obj_id: int, scale=1, render_mode=0):
        GameObject.__init__(self, rect, obj_id, solid=True, scale=scale)
        if render_mode > 0:
            self.image = pg.Surface(self.rect.size, pg.SRCALPHA)
            pg.draw.rect(self.image, Colours.blue.value, self.image.get_rect(), 1)


class PokeMart(TiledMap2, MapLinkTile, StateMachine):

    custom_tile_object_mapping = {
        "desk": DeskTile,
        # "computer": ComputerTile,
    }

    item_generator = ItemGenerator()

    controller = Controller()

    idle = State("idle", initial=True)
    inquiry = State("inquiry")
    select_buy_item = State("select_buy_item")
    select_item_count = State("select_item_count")
    confirming_purchase= State("confirming_item")

    desk_interact = idle.to(inquiry)
    browse_items = inquiry.to(select_buy_item, on="slide_to_buy")
    choose_item_count = select_buy_item.to(select_item_count)
    cancel_buy_item = select_buy_item.to(inquiry)
    confirm_purchase = select_item_count.to(confirming_purchase, on="confirm_purchase_action")
    complete_purchase = confirming_purchase.to(confirming_purchase, on="complete_purchase_action")

    go_back = (
            inquiry.to(idle)
            | select_buy_item.to(inquiry, on="stop_browsing")
            | select_item_count.to(select_buy_item, on="cancel_purchase")
            | confirming_purchase.to(select_buy_item, on="cancel_purchase")
            | idle.to.itself()
    )

    with open('game_data/game_config/pokemart_data.json', 'r') as file:
        pokemart_data: list[dict] = json.load(file)

    def __init__(self, rect, player, map_scale=1, obj_scale=1, parent_map_scale=1.0, properties=None):
        size = pg.Vector2(256, 192) * map_scale

        StateMachine.__init__(self)

        MapLinkTile.__init__(self, rect, obj_id=0, linked_map_name="pokemart",)

        TiledMap2.__init__(
            self,
            "maps/buildings/pokemart/pokemart.tmx",
            size,
            player,
            player_position=pg.Vector2(3, 12),
            map_scale=map_scale,
            object_scale=obj_scale,
            player_layer="3_player_layer",
            view_screen_tile_size=pg.Vector2(19, 18),
            map_directory=MODULE_PATH,
        )

        pokemart_id = 0
        if properties is not None:
            pokemart_id = properties.get("pokemart_id", 0)

        buy_items = next(
            (data_dict["buy_items"] for data_dict in self.pokemart_data if data_dict["pokemart_id"] == pokemart_id),
            []
        )

        self.buy_items = [self.item_generator.generate_item(item) for item in buy_items]

        self.base_surface.fill(Colours.black.value)
        self.running = False

        self.action_selector = ActionSelector(scale=self.map_scale)

        # === Container Init ===
        self.money_container = MoneyContainer(player=player, scale=self.map_scale)
        self.buy_container = ItemSetContainer(self.buy_items, scale=self.map_scale)
        self.display_bar = DisplayBar(scale=self.map_scale)
        self.display_bar.display_item(self.selected_buy_item)
        self.bag_count_container = BagCountContainer(0, scale=self.map_scale)
        self.price_counter = PriceCounter(200, player=player, scale=self.map_scale)
        self.confirm_container = ConfirmContainer(scale=self.map_scale)

        self.active_selector = self.action_selector

        self.purchase_render_offset = pg.Vector2(0, 0)

        self.render_window = None

    def __repr__(self):
        return f"{self.__class__.__name__}({self.rect})"

    @property
    def selected_buy_item(self):
        return self.buy_container.selected

    # === DEFINE STATE TRANSITIONS ===
    def slide_to_buy(self, event):
        self.slide_animation()

        self.refresh()
        self.sprites.remove(self.action_selector)
        self.sprites.add(self.money_container)
        self.sprites.add(self.buy_container)
        self.sprites.add(self.display_bar)

        self.active_selector = self.buy_container
        self.price_counter.reset()

    def stop_browsing(self, *args, **kwargs):
        self.sprites.empty()
        self.refresh()
        self.slide_animation(reverse=True)
        self.display_message(
            "Is there anything else I can do for you?",
            window=self.render_window,
            offset = self.purchase_render_offset,
            keep_textbox=True,
        )
        self.sprites.add(self.action_selector)
        self.active_selector = self.action_selector

        self.buy_container.reset()

    def cancel_purchase(self, *args, **kwargs):
        self.sprites.remove(self.confirm_container)

        self.price_counter.reset()

    def on_exit_select_item_count(self, event):
        self.active_selector = self.buy_container
        self.sprites.remove(self.price_counter)
        self.sprites.remove(self.bag_count_container)
        self.sprites.remove(self.text_box)

        self.refresh()
        self.render_window.blit(self.get_surface(offset=self.purchase_render_offset), (0, 0))
        pg.display.flip()

    def on_enter_select_item_count(self, event):
        item: Item = self.buy_container.selected
        self.display_message(
            f"{item.name}? Certainly. How many would you like?",
            window=self.render_window,
            keep_textbox=True,
            offset=self.purchase_render_offset,
        )
        self.price_counter.item_price = item.buyPrice

        self.sprites.add(self.price_counter)
        self.sprites.add(self.bag_count_container)
        self.render_window.blit(self.get_surface(offset=self.purchase_render_offset), (0, 0))
        pg.display.flip()

        self.active_selector = self.price_counter

    def confirm_purchase_action(self, *args, **kwargs):
        item = self.buy_container.selected
        item_count = self.price_counter.item_count
        self.display_message(
            f"{item.name}, and you want {item_count:.0f}. "
            f"That will be {self.price_counter.total_price:.0f}. OK?",
            window=self.render_window,
            keep_textbox=True,
            offset=self.purchase_render_offset,
        )

        self.sprites.remove(self.price_counter)
        self.sprites.remove(self.bag_count_container)
        self.sprites.add(self.confirm_container)
        self.active_selector = self.confirm_container

    def complete_purchase_action(self):
        item = self.buy_container.selected
        self.sprites.remove(self.confirm_container)
        self.sprites.remove(self.text_box)
        self.display_message(
            "Here you are! Thank you!",
            window=self.render_window,
            duration=2000,
            offset=self.purchase_render_offset
        )

        self.display_message(
            f"You put away the {item.name}"
            f"{'s' if self.price_counter.item_count > 1 else ''} "
            f"in the {item.item_type.value} Pocket.",
            window=self.render_window, duration=2000, keep_textbox=True,
            offset=self.purchase_render_offset
        )

        self.player.bag.add_item(item, item_count=self.price_counter.item_count)
        self.player.money -= self.price_counter.total_price

        self.money_container.update()
        self.sprites.remove(self.confirm_container)
        self.render_window.blit(self.get_surface(offset=self.purchase_render_offset), (0, 0))
        pg.display.flip()

    def on_exit_confirming_purchase(self):
        self.confirm_container.reset()

    # === Custom Logic ===

    def load_objects(self):
        # load default objects
        TiledMap2.load_objects(self)

        for layer in self.object_layers:
            sprite_group = self.object_layer_sprites[layer.id]
            for obj in layer:
                rect = pg.Rect(obj.x, obj.y, obj.width, obj.height)

                if obj.type in self.custom_tile_object_mapping:
                    obj_tile = self.custom_tile_object_mapping[obj.type](rect, obj.id, scale=self.map_scale)
                    sprite_group.add(obj_tile)

    def object_interaction(self, sprite: pg.sprite.Sprite, render_surface: pg.Surface):
        map_obj, action_complete = super().object_interaction(sprite)
        if map_obj and action_complete:
            return map_obj, True

        elif isinstance(sprite, DeskTile):
            self.desk_loop(render_surface)

        return None, True

    def slide_animation(self, frames=10, duration=400, reverse=False):
        if self.render_window is None:
            return

        final_offset = -pg.Vector2(5 * self.tile_size.x, 0)

        for i in range(1, frames+1):
            ratio = (i / frames) if not reverse else ((frames-i) / frames)
            self.purchase_render_offset = final_offset * ratio
            self.render_window.blit(self.get_surface(offset=self.purchase_render_offset), (0, 0))
            pg.display.flip()
            pg.time.wait(int(duration / frames))

    def desk_loop(self, render_surface: pg.Surface):
        self.sprites.add(self.action_selector)
        self.display_message(
            "Welcome! What do you need?",
            window=render_surface,
            offset=self.purchase_render_offset,
        )
        self.running = True
        self.active_selector = self.action_selector
        self.render_window = render_surface

        self.send("desk_interact")
        while self.current_state != self.idle:
            for event in pg.event.get():
                if event.type == pg.KEYDOWN:
                    if event.key in self.controller.move_keys:
                        direction = self.controller.direction_key_bindings[event.key]
                        self.active_selector.process_interaction(direction)

                        self.display_bar.display_item(self.selected_buy_item)
                        render_surface.blit(self.get_surface(offset=self.purchase_render_offset), (0, 0))
                        pg.display.flip()

                    elif event.key == self.controller.b:
                        self.send("go_back")

                    elif event.key == self.controller.a:
                        selected = self.active_selector.selected
                        if isinstance(selected, PopupOption):
                            if selected == PopupOption.buy:
                                self.send("browse_items")

                            elif selected == PopupOption.see_ya:
                                self.send("go_back")

                        elif isinstance(selected, Item):
                            item: Item = self.active_selector.selected
                            if item.name == "CANCEL":
                                self.send("go_back")

                            else:
                                self.send("choose_item_count")

                        elif self.active_selector == self.price_counter:
                            self.send("confirm_purchase")

                        elif isinstance(selected, ConfirmOption):
                            if selected == ConfirmOption.yes:
                                self.send("complete_purchase")
                                wait_for_key()
                                self.send("go_back")

                            else:
                                # self.sprites.remove(self.confirm_container)
                                self.send("go_back")

                            self.sprites.remove(self.text_box)
                            self.active_selector = self.buy_container
                            self.price_counter.reset()

                        self.refresh()
                        render_surface.blit(self.get_surface(offset=self.purchase_render_offset), (0, 0))
                        pg.display.flip()

        self.action_selector.reset()
        self.sprites.remove(self.action_selector)
        self.refresh()

        # self.send("exit_interaction")
        self.display_message("Please come again!", window=render_surface, offset=self.purchase_render_offset)
        wait_for_key()

        self.refresh()
        render_surface.blit(self.get_surface(self.purchase_render_offset), (0, 0))
        pg.display.flip()


if __name__ == '__main__':
    ...
