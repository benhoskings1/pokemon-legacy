import time

from enum import Enum
from dataclasses import dataclass
import pygame as pg

from pokemon_legacy.engine.general import Colours

from pokemon_legacy.engine.game_world.map_collection import MapCollection
from pokemon_legacy.engine.graphics.sprite_screen import SpriteScreen

from pokemon_legacy.engine.general.direction import Direction
from pokemon_legacy.engine.game_world.game_map import RoutePopup
from pokemon_legacy.engine.graphics.text_box import TextBox
from pokemon_legacy.displays.menu.menu_display_popup import MenuDisplayPopup
from pokemon_legacy.engine.game_world.route_orchestrator import RouteOrchestrator
from pokemon_legacy.engine.game_world.tiled_map import TiledMap2, MapLinkTile, WallTile
from pokemon_legacy.engine.game_world.tiled_building import TiledBuilding

from pokemon_legacy.engine.errors import MapError


class GameDisplayStates(Enum):
    pokedex = 0
    team = 1
    bag = 2
    player = 3
    save = 4
    options = 5
    exit = 6


@dataclass
class GameDisplayConfig:
    update_rate: int = 4


class GameDisplay(SpriteScreen):
    def __init__(
            self,
            size,
            player,
            window,
            scale: int | float = 1,
            start_map: str = "verity_lakefront",
            start_collection = "route_orchestrator",
            render_mode: int = 0,
            config: GameDisplayConfig = GameDisplayConfig(),
    ):
        # ==== INIT ====
        SpriteScreen.__init__(self, size)
        self.cfg = config

        self.player = player

        # === SETUP ===
        self.route_orchestrator = RouteOrchestrator(
            size,
            player,
            window,
            start_map=start_map,
            map_scale=2,
            obj_scale=2,
            render_mode=render_mode,
        )

        if start_collection != "route_orchestrator":
            self._active_map_collection = self.route_orchestrator._get_map_node(start_map).parent_collection
        else:
            self._active_map_collection = self.route_orchestrator

        self.scale = scale

        self.text_box = TextBox(sprite_id="text_box", scale=scale, static=True)
        self.text_box.rect.topleft += pg.Vector2(3, 0) * scale

        self.last_game_map = self.map

        self.camera_offset = pg.Vector2(0, 0)

        self.last_refresh_time = time.monotonic()

    @property
    def map(self):
        active_map = self._active_map_collection.map
        if isinstance(active_map, TiledMap2):
            return active_map
        if isinstance(active_map, TiledBuilding):
            return active_map.map

        raise MapError("Map not found")

    @map.setter
    def map(
            self,
            new_map: TiledMap2
    ):
        if new_map.parent_collection == self.map.parent_collection:
            self._active_map_collection.map = new_map
        else:
            self._active_map_collection = new_map.parent_collection

    def get_surface(
            self,
            show_sprites: bool = True,
            offset: None | pg.Vector2 = None
    ) -> pg.Surface:

        self.sprites.update()

        if show_sprites:
            self.sprites.draw(self)

        self.add_image(
            self._active_map_collection.get_surface(
                camera_offset=self.camera_offset
            ),
            pos=(0, 0)
        )

        display_surf = self.base_surface.copy()
        display_surf.blit(self.surface, (0, 0))
        display_surf.blit(self.sprite_surface, (0, 0))

        return display_surf

    def update(
            self,
            force_refresh: bool = False
    ):
        current_time = time.monotonic()
        if (current_time - self.last_refresh_time > self.cfg.update_rate) or force_refresh:
            self._active_map_collection.update_sprites()
            self._active_map_collection.render(camera_offset=self.camera_offset)
            self.sprites.update()

            self.last_refresh_time = current_time
            return True

        return False

    def update_display_text(
            self,
            text,
            max_chars=None
    ):
        if self.text_box not in self.sprites:
            self.sprites.add(self.text_box)

        self.text_box.refresh()

        text_rect = pg.Rect(pg.Vector2(10, 4) * self.scale, pg.Vector2(201, 40) * self.scale)
        self.text_box.add_text_2(text, text_rect.inflate(-10, -18), max_chars=max_chars)
        self.text_box.update_image()

    def menu_loop(
            self,
            game
    ):
        """
        Loop to return an action based on the menu selection
        :return:
        """
        action = None
        popup = MenuDisplayPopup(scale=game.graphics_scale)
        self.sprites.add(popup)
        game.update_display()

        while not action:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    game.running = False
                elif event.type == pg.KEYDOWN:
                    if event.key in (game.controller.y, game.controller.b):
                        popup.kill()
                        return None
                    elif event.key == game.controller.a and GameDisplayStates(popup.selector.position_idx) in game.menu_objects:
                        popup.kill()
                        return GameDisplayStates(popup.selector.position_idx)

                    else:
                        popup.process_input(event.key, controller=game.controller)
                        # game.menu_active = not game.menu_active
                        game.update_display()

    def refresh(
            self,
            sprite_only=False
    ):
        if not sprite_only:
            self.surface = pg.Surface(self.size, pg.SRCALPHA)
        self.sprite_surface = pg.Surface(self.size, pg.SRCALPHA)

    def move_trainer(
            self,
            trainer,
            direction: Direction,
            window,
            step_count:int = 1,
            **kwargs
    ):
        for step_idx in range(step_count):
            map_obj, moved = self.map.move_trainer(
                trainer,
                direction,
                window,
                **kwargs,
                camera_offset=self.camera_offset
            )

        trainer._moving = False

        return map_obj, moved

    def move_follower(self, leader, window) -> bool:
        """
        Move the follower to the leader's previous position.
        
        :param leader: The character being followed (usually player)
        :param window: The game window surface
        :return: True if follower moved, False otherwise
        """
        if not leader.has_follower:
            return False
            
        follower = leader.follower
        last_position = leader.get_last_position()
        
        if last_position is None:
            return False
            
        target_map, target_pos = last_position
        
        # Get follower's current position on the target map
        if target_map not in follower.map_positions:
            # Follower isn't on the same map yet, place them there
            follower.map_positions[target_map] = target_pos
            return True
            
        current_pos = follower.map_positions[target_map]
        
        # Calculate direction from current to target
        delta = target_pos - current_pos
        
        if delta.length() < 0.1:
            # Already at target position
            return False
        
        # Determine the direction to move
        move_direction = None
        for direction in Direction:
            if delta.normalize() == direction.value:
                move_direction = direction
                break
        
        if move_direction is None:
            # Handle diagonal or complex movement - prioritize x or y
            if abs(delta.x) >= abs(delta.y):
                move_direction = Direction.right if delta.x > 0 else Direction.left
            else:
                move_direction = Direction.down if delta.y > 0 else Direction.up
        
        # Move the follower
        self.move_trainer(
            follower,
            move_direction,
            window,
            step_count=1,
            move_duration=200,
            ignore_solid_objects=True  # Followers can phase through objects to keep up
        )
        
        return True

    def move_player(
            self,
            direction: Direction,
            window,
            frames = 5,
            duration = 200,
            check_facing_direction = True
    ):
        # Record player's current position for follower tracking
        if self.player.has_follower and self.map in self.player.map_positions:
            self.player.record_position(self.map, self.player.map_positions[self.map])
            
        map_obj, moved, edge = self.map.move_player(
            direction,
            window,
            check_facing_direction=check_facing_direction,
            camera_offset=self.camera_offset
        )
        step_count = 1 if moved else 0
        if isinstance(map_obj, TiledMap2):
            self.last_game_map = self.map
            self.map = map_obj
            return self.map.check_trainer_collision(), True, None

        elif isinstance(map_obj, TiledBuilding):
            self.map = map_obj.map
            return self.map.check_trainer_collision(), True, None

        elif isinstance(map_obj, MapLinkTile):
            self.map = self._active_map_collection._get_map_node(map_obj.linked_map_name)
            self.player.map_positions[self.map] = map_obj.location

            return self.map.check_trainer_collision(), True, None

        elif isinstance(map_obj, WallTile) and moved:
            step_count += 1

        for step_idx in range(step_count):
            self.player._moving = True
            self.update(force_refresh=True)

            edges = self.map.detect_map_edge()
            joint_maps = self._active_map_collection._get_adjoining_maps(edges)

            render_maps = [self.map]

            if joint_maps is not None:
                render_maps += [_map.active_floor if isinstance(_map, TiledBuilding) else _map for _map in joint_maps]

                new_map, map_link = list(joint_maps.items())[0]

                player_diff = self.player.map_positions[self.map] - map_link[self.map.map_name]
                new_map_pos = map_link[new_map.map_name] + player_diff
                self.player.map_positions[new_map] = new_map_pos

            start_positions = {_map: self.player.map_positions[_map] for _map in render_maps}

            for frame in range(frames):
                frame_start = pg.time.get_ticks()

                for _map, map_start in start_positions.items():
                    self.player.map_positions[_map] = map_start + direction.value * frame / frames
                    _map.render(start_pos=map_start, camera_offset=self.camera_offset)

                window.blit(self.get_surface(), (0, 0))
                pg.display.flip()
                frame_dur = pg.time.get_ticks() - frame_start
                pg.time.delay(int(duration / frames) - frame_dur)

            self.player._leg = not self.player._leg

            for _map, map_start in start_positions.items():
                self.player.map_positions[_map] = map_start + direction.value
                _map.render(camera_offset=self.camera_offset)

            player_pos = self.player.map_positions[self.map]
            if not self.map.border_rect.collidepoint(player_pos):
                if joint_maps is not None:
                    new_map, map_link = list(joint_maps.items())[0]

                    self.map = new_map

                    route_popup = RoutePopup(self.map.map_name, scale=self.scale)
                    self.sprites.add(route_popup)

        trainer = self.map.check_trainer_collision()

        map_obj = trainer if trainer is not None else map_obj
        
        # Move follower to player's previous position if player moved
        if moved and self.player.has_follower:
            self.move_follower(self.player, window)

        return map_obj, moved, edge

    def get_map_collections(self):
        cols = [self.route_orchestrator]
        all_collections = self.route_orchestrator._get_sprites(sprite_type=MapCollection)
        for _, collections in all_collections.items():
            cols.extend(collections)

        return cols

    def get_map(
            self,
            map_name: str,
            collection_name: str = None
    ):
        if collection_name is None:
            collection = self._active_map_collection
        else:
            map_collections: list[MapCollection] = self.get_map_collections()

            collection = next((col for col in map_collections if col.collection_name == collection_name), None)
            if collection is None:
                return None

        _map = next((_map for _map in collection.maps if _map.map_name == map_name), None)

        return _map

    def get_json_data(self):
        return {
            "map_name": self.map.map_name,
            "collection_name": self.map.parent_collection.collection_name,
        }

    def load_from_state(
            self,
            state: dict
    ):
        for position in state["player"].get("positions", []):
            map_name, collection, pos = position[0], position[1], position[2]

            _map = self.get_map(map_name, collection)

            self.player.map_positions[_map] = pg.Vector2(pos)

        self._active_map_collection.render(camera_offset=self.camera_offset)

    # === Display functions ===
    @staticmethod
    def fade_to_black(
            main_window,
            touch_window,
            duration
    ):
        black_surf = pg.Surface(main_window.get_size())
        black_surf.fill(Colours.black.value)
        black_surf.set_alpha(0)
        count = 100
        for t in range(0, count):
            black_surf.set_alpha(round(t / count * 255))
            pg.time.delay(int(duration / count))
            main_window.blit(black_surf, (0, 0))
            touch_window.blit(black_surf, (0, 0))
            pg.display.flip()

    def battle_intro(
            self,
            main_window,
            touch_window,
            time_delay
    ):
        black_surf = pg.Surface(main_window.get_size())
        black_surf.fill(Colours.darkGrey.value)
        for count in range(2):
            main_window.blit(black_surf, (0, 0))
            pg.display.flip()
            pg.time.delay(time_delay)
            self.update_display(main_window)
            pg.time.delay(time_delay)

            if count == 0:
                touch_window.blit(black_surf, (0, 0))

        current_game_display = self.get_surface()
        left_cut, right_cut = current_game_display, current_game_display.copy()

        # create stripy left/right surfaces
        for i in range(20):
            bar_rect = pg.Rect(0, i * 10 * self.scale, current_game_display.get_width(), 5 * self.scale)
            pg.draw.rect(right_cut, pg.Color(0, 0, 0, 0), bar_rect)
            bar_rect = bar_rect.move(0, 5 * self.scale)
            pg.draw.rect(left_cut, pg.Color(0, 0, 0, 0), bar_rect)

        max_frames = 30
        for frame in range(max_frames):
            black_surf.fill(Colours.black.value)
            offset = (frame+1) * self.size.x / max_frames
            black_surf.blit(left_cut, (-offset, 0))
            black_surf.blit(right_cut, (offset, 0))
            main_window.blit(black_surf, (0, 0))

            pg.display.flip()
            pg.time.delay(20)

    def update_display(
            self,
            main_window,
            flip=True
    ):
        """ update the game screen """
        self.refresh()
        main_window.blit(self.get_surface(), (0, 0))
        # self.bottomSurf.blit(self.poketech.get_surface(), (0, 0))
        if flip:
            pg.display.flip()
