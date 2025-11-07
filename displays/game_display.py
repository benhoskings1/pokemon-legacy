from enum import Enum
import pygame as pg

from graphics.sprite_screen import SpriteScreen

from general.direction import Direction
from maps.game_map import RoutePopup, GameMap
from displays.battle.battle_display_main import TextBox
from displays.menu.menu_display_popup import MenuDisplayPopup
from maps.route_orchestrator import RouteOrchestrator
from maps.tiled_map import TiledMap2, ExitTile, WallTile


class GameDisplayStates(Enum):
    pokedex = 0
    team = 1
    bag = 2
    player = 3
    save = 4
    options = 5
    exit = 6


class GameDisplay(SpriteScreen):
    def __init__(
            self,
            size,
            player,
            window,
            scale: int | float = 1,
            # _map: str = "Twinleaf Town.tmx",
            start_map: str = "sandgem_town",
            render_mode: int = 0
    ):
        # ==== INIT ====
        SpriteScreen.__init__(self, size)

        self.player = player

        # === SETUP ===
        self.route_orchestrator = RouteOrchestrator(
            size,
            player,
            window,
            map_scale=2,
            obj_scale=2,
            render_mode=render_mode,
        )

        self.map = self.route_orchestrator.get_map_node(start_map)
        self.player.map_positions[self.map] = pg.Vector2(17, 10)
        self.map.render()

        self.scale = scale

        self.text_box = TextBox(sprite_id="text_box", scale=scale, static=True)
        self.text_box.rect.topleft += pg.Vector2(3, 0) * scale

        self.last_game_map = self.map

    def get_surface(
            self,
            show_sprites: bool = True,
            offset: None | pg.Vector2 = None
    ) -> pg.Surface:

        self.sprites.update()

        if show_sprites:
            self.sprites.draw(self)

        self.add_image(self.joint_map_surface, (0, 0))

        display_surf = self.base_surface.copy()
        display_surf.blit(self.surface, (0, 0))
        display_surf.blit(self.sprite_surface, (0, 0))

        return display_surf

    def update(self):
        self.sprites.update()

    def update_display_text(self, text, max_chars=None):
        if self.text_box not in self.sprites:
            self.sprites.add(self.text_box)

        self.text_box.refresh()

        text_rect = pg.Rect(pg.Vector2(10, 4) * self.scale, pg.Vector2(201, 40) * self.scale)
        self.text_box.add_text_2(text, text_rect.inflate(-10, -18), max_chars=max_chars)
        self.text_box.update_image()

    def menu_loop(self, game):
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

    def refresh(self, sprite_only=False):
        if not sprite_only:
            self.surface = pg.Surface(self.size, pg.SRCALPHA)
        self.sprite_surface = pg.Surface(self.size, pg.SRCALPHA)

    def move_player(self, direction: Direction, window, frames=5, duration=200):
        map_obj, moved, edge = self.map.move_player(direction, window)

        step_count = 1 if moved else 0
        if isinstance(map_obj, TiledMap2):
            self.last_game_map = self.map
            self.map = map_obj
            return map_obj, False, None

        elif isinstance(map_obj, ExitTile):
            print(map_obj)
            self.map = self.last_game_map
            return map_obj, False, None

        elif isinstance(map_obj, WallTile) and moved:
            step_count += 1

        for step_idx in range(step_count):
            self.player._moving = True
            self.map.render()

            edges = self.map.detect_map_edge()
            joint_maps = self.route_orchestrator.get_adjoining_map(self.map, edges)

            render_maps = [self.map]

            if joint_maps is not None:
                render_maps += joint_maps

                new_map, map_link = list(joint_maps.items())[0]

                player_diff = self.player.map_positions[self.map] - map_link[self.map.map_name]
                new_map_pos = map_link[new_map.map_name] + player_diff
                self.player.map_positions[new_map] = new_map_pos

            start_positions = {_map: self.player.map_positions[_map] for _map in render_maps}

            for frame in range(frames):
                frame_start = pg.time.get_ticks()

                for _map, map_start in start_positions.items():
                    self.player.map_positions[_map] = map_start + direction.value * frame / frames
                    _map.render(start_pos=map_start)

                window.blit(self.get_surface(), (0, 0))
                pg.display.flip()
                frame_dur = pg.time.get_ticks() - frame_start
                pg.time.delay(int(duration / frames) - frame_dur)

            self.player._leg = not self.player._leg

            for _map, map_start in start_positions.items():
                self.player.map_positions[_map] = map_start + direction.value
                _map.render()

            player_pos = self.player.map_positions[self.map]
            if not self.map.border_rect.collidepoint(player_pos):
                if joint_maps is not None:
                    new_map, map_link = list(joint_maps.items())[0]

                    self.map = new_map

                    route_popup = RoutePopup(self.map.map_name, scale=self.scale)
                    self.sprites.add(route_popup)

                    print(f"new map {self.map}")

        trainer = self.map.check_trainer_collision()

        map_obj = trainer if trainer is not None else map_obj

        return map_obj, moved, edge

    @property
    def joint_map_surface(self):
        edges = self.map.detect_map_edge()
        joint_maps = self.route_orchestrator.get_adjoining_map(self.map, edges)

        maps = [self.map]

        if joint_maps is not None:
            for new_map, map_link in joint_maps.items():
                maps.append(new_map)

        # reverse the order of maps
        maps.reverse()
        surface = maps[0].get_surface()
        for _map in maps[1:]:
            surface.blit(_map.get_surface(), (0, 0))

        return surface
