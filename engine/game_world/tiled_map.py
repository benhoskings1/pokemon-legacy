import os
import time
from importlib.resources.abc import Traversable
from enum import Enum

import pygame
import pygame as pg
import pytmx
from pytmx import TiledMap
from pytmx.util_pygame import pygame_image_loader

from math import ceil

from engine.general.utils import Colours
from engine.general.direction import Direction

from engine.graphics.sprite_screen import SpriteScreen
from engine.graphics.main_screen import MainScreen

from engine.characters import npc_custom_mapping
from engine.characters.character import Character, AttentionBubble, Movement, CharacterTypes
from engine.characters.npc import NPC
from engine.characters.trainer import Trainer
from engine.characters.player import Player2

from engine.game_world.game_obejct import GameObject


class LinkType(Enum):
    adjacency = 1
    parent = 2
    child = 3
    map_link = 4


class MapLinkTile(GameObject):
    def __init__(
            self,
            rect: pg.Rect,
            obj_id: int,
            linked_map_name: str,
            map_link_type: LinkType,
            building_link: bool = False,
            location: None | str = None,
            scale=1.0,
    ):
        GameObject.__init__(
            self,
            rect,
            obj_id,
            solid=True,
            auto_interact=True,
            scale=scale,
        )
        self.map_link_type = map_link_type
        self.linked_map_name = linked_map_name
        self.building_link = building_link
        if location:
            vals = [int(char) for char in location.split(",")]
            self.location = pg.Vector2(vals[0], vals[1])
        else:
            self.location = None

    def __repr__(self):
        return f"MapLinkTile({self.map_link_type.name},{self.linked_map_name},{self.location})"


class Obstacle(GameObject):
    def __init__(self, rect, obj_id, **kwargs):
        GameObject.__init__(self, rect, obj_id, solid=True, **kwargs)


class WallTile(GameObject):
    def __init__(self, rect: pg.Rect, obj_id: int, direction="down", scale=1):
        GameObject.__init__(self, rect, obj_id, solid=True, scale=scale, auto_interact=True)
        self.direction = next((d for d in Direction if d.name == direction), None)


class TiledMap2(TiledMap, MainScreen):
    tile_object_mapping = {
        "obstacle": Obstacle,
    }

    def __init__(
            self,
            file_path,
            size: tuple[int, int] | pg.Vector2,
            player: Player2,
            player_position = pg.Vector2(0, 0),
            *,
            player_layer: None | str = None,
            map_scale: float = 1.0,
            object_scale: float = 1.0,
            view_screen_tile_size=pg.Vector2(29, 22),
            view_field = None,
            map_directory: str | Traversable = None,
            render_mode=0,
            parent_collection = None,
            base_colour: None | Colours = None,
    ):
        """
        This map dynamically renders the players immediate surroundings, rather than the entire map.

        :param file_path:
        :param size: the size of the map render window (in pixels)
        :param player: the player sprite to display on the map
        :param player_position: the initial position of the player on the map
        :param player_layer: the layer of the map to blit the player
        :param map_scale: the scale factor of the map display
        :param object_scale: the scale factor of the object display
        :param view_screen_tile_size: the screen tile size of the map display
        :param view_field: the screen tile size of the map display
        :param map_directory: the directory of the map
        :param render_mode: the level of verbosity in rendering the map

        """
        TiledMap.__init__(self, file_path, pixelalpha=True, image_loader=pygame_image_loader)

        self.render_mode = render_mode

        # === PROPERTY SETUP ===
        self.map_name = os.path.basename(file_path).replace(".tmx", "")
        self.border_rect = pg.Rect(0, 0, self.width, self.height)

        self.map_directory = map_directory

        self.layers = sorted(self.layers, key=lambda layer: layer.name)

        self.object_layers = [
            layer for layer in self.layers if isinstance(layer, pytmx.TiledObjectGroup)
        ]

        self.tile_size_og = pg.Vector2(self.tilewidth, self.tileheight)

        self.tilewidth *= map_scale
        self.tileheight *= map_scale
        self.tile_size = pg.Vector2(self.tilewidth, self.tileheight)

        default_view_field = pg.Vector2(round(size[0] / self.tile_size.x),
                                        round(size[1] / self.tile_size.y))

        self.view_field = default_view_field if view_field is None else view_field

        self.render_padding = pg.Vector2(5, 5)
        self.view_screen_tile_size = view_screen_tile_size
        view_screen_size = pg.Vector2(
            self.view_screen_tile_size.x * self.tilewidth * map_scale,
            self.view_screen_tile_size.y * self.tileheight * map_scale,
        )

        self.extra_size = (self.view_screen_tile_size - self.view_field) / 2
        self.extra_offset = -pg.Vector2(self.extra_size[0] * self.tile_size.x,
                                       self.extra_size[1] * self.tile_size.y)

        MainScreen.__init__(self, size)

        self.map_scale = map_scale
        self.obj_scale = object_scale

        self.render_surface = SpriteScreen(view_screen_size, colour=base_colour)

        self.grassObjects = pg.sprite.Group()
        self.obstacles = pg.sprite.Group()

        self.map_objects = None

        self.player = player
        self.object_layer_sprites: dict[int, MapObjects] = {}
        self.load_objects()
        self.sprite_refresh_last = time.monotonic()

        # add trainer map position
        self.add_character(player, player_position, layer_name=player_layer)

        self.tile_surface_mapping = {
        }

        self.render()

        self.parent_collection = parent_collection

    def __repr__(self):
        return f"TiledMap({self.map_name})"

    def check_collision(
            self,
            trainer,
            direction: Direction
    ) -> None | GameObject:
        """
        Check if the player will collide with a map object in the next move

        :param trainer: the trainer object that is moving
        :param direction: the direction the player is attempting to move

        :return: the sprite collision, if any, else None
        """
        new_rect = trainer.map_rects[self].move(
            pg.Vector2(
                direction.value.x * self.tilewidth,
                direction.value.y * self.tileheight
            )
        )

        for layer_id, object_group in self.object_layer_sprites.items():
            npc_sprites = [s for s in object_group.sprites() if isinstance(s, Character)]
            map_collision = new_rect.collideobjects(npc_sprites, key=lambda o: o.map_rects[self])
            if map_collision:
                return map_collision

            # get all solid objects
            other_sprites = [s for s in object_group.sprites() if not isinstance(s, Character)]
            map_collision = new_rect.collideobjects(other_sprites, key=lambda o: o.rect)
            if map_collision:
                return map_collision

        return None

    def move_trainer(
            self,
            trainer: Trainer,
            direction: Direction,
            window: pg.Surface,
            move_duration: int = None,
            *,
            check_facing_direction: bool = True,
            ignore_solid_objects: bool = False,
            camera_offset: pg.Vector2 = pg.Vector2(0, 0),
    ) -> tuple[GameObject | None, bool]:
        """ moves the specified trainer in a given direction """

        # only move player if facing the right direction
        if check_facing_direction and not trainer.facing_direction == direction:
            trainer.facing_direction = direction
            self.render(camera_offset=camera_offset)
            window.blit(self.get_surface(), (0, 0))
            pygame.display.flip()
            return None, False

        obj_collision = self.check_collision(trainer, direction)

        if obj_collision and obj_collision.solid and not ignore_solid_objects:
            if not obj_collision.auto_interact:
                return None, False

            if isinstance(obj_collision, WallTile):
                if obj_collision.direction != direction:
                    sprite, _ = self.object_interaction(obj_collision, window)
                    return sprite, False
            else:
                sprite, _ = self.object_interaction(obj_collision, window)
                return sprite, False

        self.player._moving = True

        if not move_duration:
            move_duration = 200 if self.player.movement == Movement.walking else 125

        if not isinstance(trainer, Player2):
            self.trainer_move_animation(
                trainer,
                direction,
                window,
                duration=move_duration,
                camera_offset=camera_offset
            )
            trainer._leg = not trainer._leg

        self.player._moving = False

        return obj_collision, True

    def trainer_move_animation(
            self,
            trainer: Trainer,
            direction: Direction,
            window: pg.Surface,
            *,
            frames: int = 5,
            duration: int = 200,
            camera_offset: pg.Vector2 = pg.Vector2(0, 0),
    ):
        """
        Moves the specified trainer in a given direction. If the trainer is a player, move the map
        else, move the trainer.

        :param trainer: the trainer object that is moving
        :param direction: direction the player is attempting to move
        :param window: the pygame surface window
        :param frames: the number of frames to use in the animation
        :param duration: total duration of the animation

        :return: None
        """
        if isinstance(trainer, Player2):
            self.player._moving = True
            self.render(camera_offset=camera_offset)

            start_pos = self.player.map_positions[self]

            for frame in range(frames):
                self.player.map_positions[self] = start_pos + direction.value * frame / frames
                self.render(start_pos=start_pos, camera_offset=camera_offset)
                window.blit(self.get_surface(), (0, 0))
                pg.display.flip()
                pg.time.delay(int(duration / frames))

            self.player.map_positions[self] = start_pos + direction.value

            self.player._moving = False
            self.render(camera_offset=camera_offset)

        else:
            # trainer._moving = True
            start_pos = trainer.map_positions[self]
            trainer._moving = True
            for frame_idx in range(frames):
                trainer.map_positions[self] = start_pos + direction.value * frame_idx / frames

                self.render(camera_offset=camera_offset)
                window.blit(self.get_surface(), (0, 0))
                pg.display.flip()
                pg.time.wait(round(duration / frames))

            trainer._moving = False

            # set back to integer values
            trainer.map_positions[self] = start_pos + direction.value
            # trainer.position += direction.value
            self.render(camera_offset=camera_offset)

        window.blit(self.get_surface(), (0, 0))
        pg.display.flip()

    def object_interaction(
            self,
            sprite: GameObject,
            *args
    ) -> tuple[GameObject | None, bool]:
        """ hook for automatic object interactions """
        return sprite, False

    def load_objects(self):
        """
        Loads any default objects. Supported types are: 'npc', 'obstacle'
        """

        def create_object(obj_type, *args, **kwargs):
            return self.tile_object_mapping[obj_type](*args, **kwargs)

        for layer in self.object_layers:
            sprite_group = MapObjects(tile_size=self.tile_size)
            for obj in layer:
                rect, properties = pg.Rect(obj.x, obj.y, obj.width, obj.height), obj.properties
                tile = None
                if obj.type == "npc":
                    character_type_str = obj.properties.get("character_type", None)
                    if character_type_str:
                        # look to see if there is a custom loader
                        character_type = CharacterTypes[character_type_str]
                        npc_template = npc_custom_mapping.get(character_type, NPC)
                    else:
                        npc_template = NPC

                    tile = npc_template(obj.properties, scale=2)
                    tile.map_positions[self] = pg.Vector2(
                        (rect.x / self.tile_size_og.x),
                        (rect.y / self.tile_size_og.y)
                    )
                    tile._load_surfaces()

                elif obj.type == "trainer":
                    tile = Trainer(obj.properties, scale=2)
                    tile.map_positions[self] = pg.Vector2(
                        round(rect.x / self.tile_size_og.x),
                        round(rect.y / self.tile_size_og.y)
                    )

                    tile._load_surfaces()

                elif obj.type == "wall":
                    direction = properties.get("direction", None)
                    tile = WallTile(rect, obj.id, direction, scale=2)

                elif obj.type == "map_link":
                    tile = MapLinkTile(
                        rect,
                        obj.id,
                        properties.get("linked_map", obj.name),
                        map_link_type=LinkType.map_link,
                        building_link=properties.get("building_link", None),
                        location=properties.get("location", None),
                        scale=self.map_scale,
                    )

                else:
                    if obj.type in self.tile_object_mapping.keys():
                        tile = create_object(
                            obj.type,
                            rect,
                            obj.id,
                            scale=self.map_scale,
                            render_mode=self.render_mode,
                        )

                if tile is not None:
                    sprite_group.add(tile)

            self.object_layer_sprites[layer.id] = sprite_group

    def move_player(
            self,
            direction: Direction,
            window,
            check_facing_direction=True,
            camera_offset: pg.Vector2 = pg.Vector2(0, 0),
    ):
        """ Moves the player by a given direction """
        collision, moved = self.move_trainer(
            self.player, direction, window,
            check_facing_direction=check_facing_direction,
            camera_offset=camera_offset
        )
        edge = self.detect_map_edge()
        return collision, moved, edge

    def check_trainer_collision(self):
        trainers = self.get_sprite_types(Character)
        trainers = [c for c in trainers if hasattr(c, "vision_rect")]
        trainer = self.player.map_rects[self].collideobjects(trainers, key=lambda o: o.get_vision_rect(self))
        return trainer

    def render(
            self,
            grid_lines: bool = False,
            start_pos=None,
            camera_offset: pg.Vector2 = pg.Vector2(0, 0),
    ):
        """
        Renders the map

        Creates the underlying surface as the with extra column, then shifts the view -0.5 tiles to center align the
        map

        :param grid_lines:
        :param start_pos: the initial position of the player on the map
        :param camera_offset: the camera offset of the player on the map
        :return: None
        """
        self.refresh()
        self.render_surface.refresh()

        player_pos = self.player.map_positions[self]

        render_pos = player_pos if not start_pos else start_pos

        if camera_offset is None:
            camera_offset = pg.Vector2(0, 0)

        tile_render_rect = pg.Rect(
            ceil(render_pos.x - self.view_screen_tile_size.x / 2),
            ceil(render_pos.y - 1 - self.view_screen_tile_size.y / 2),
            self.view_screen_tile_size.x, self.view_screen_tile_size.y
        )

        if camera_offset != pg.Vector2(0, 0):
            tile_render_rect = tile_render_rect.move(camera_offset)

        camera_offset_pixels = pg.Vector2(camera_offset.x * self.tilewidth, camera_offset.y * self.tileheight)

        # ====== render static ======
        for layer in self.layers:
            if isinstance(layer, pytmx.TiledImageLayer):
                source = getattr(layer, 'source', None)
                if source:
                    img_offset = pg.Vector2(layer.offsetx, layer.offsety) * self.map_scale
                    if not self.map_directory:
                        path = os.path.join("maps", source)
                    else:
                        path = os.path.join("maps", self.map_directory, source)

                    # TODO: work out why these 0.5s are here?
                    pos = pg.Vector2((player_pos.x + 0.5 - self.view_field.x // 2) * self.tilewidth,
                                     (player_pos.y - self.view_field.y // 2) * self.tileheight)

                    pos -= img_offset
                    pos += self.extra_offset - camera_offset_pixels

                    self.render_surface.load_image(
                        path,
                        pos=-pos,
                        scale=self.map_scale,
                    )

            elif isinstance(layer, pytmx.TiledTileLayer):
                layer_offset = pg.Vector2(layer.offsetx, layer.offsety) * self.map_scale

                offset = pg.Vector2(0, 0) if start_pos is None else player_pos - start_pos

                start_x = max(0, tile_render_rect.left)
                end_x = min(self.width, tile_render_rect.right + 1)
                start_y = max(0, tile_render_rect.top)
                end_y = min(self.height, tile_render_rect.bottom + 1)

                for y in range(start_y, end_y):
                    for x in range(start_x, end_x):
                        gid = layer.data[y][x]
                        if gid == 0:
                            continue  # empty tile

                        tile_image = self.get_tile_image_by_gid(gid)
                        if tile_image:
                            (width, height) = tile_image.get_size()

                            pos = pg.Vector2(
                                (x - tile_render_rect.left - offset.x) * self.tilewidth,
                                (y - tile_render_rect.top - offset.y) * self.tileheight - height * self.map_scale
                            )

                            self.render_surface.add_image(tile_image, pos + layer_offset, scale=self.map_scale)
                            if grid_lines:
                                pg.draw.rect(
                                    self.render_surface.surface,
                                    Colours.red.value,
                                    pg.Rect(pos, tile_image.get_size()),
                                    width=1
                                )

            elif isinstance(layer, pytmx.TiledObjectGroup):
                # draw spites that correspond to the layer
                player_offset_pixels = pg.Vector2(
                    (player_pos.x + 0.5 - self.view_field.x // 2) * self.tilewidth,
                    (player_pos.y - self.view_field.y // 2) * self.tileheight
                )

                player_offset_pixels += self.extra_offset

                self.object_layer_sprites[layer.id].draw(
                    self,
                    player_offset=player_offset_pixels,
                    camera_offset=-camera_offset_pixels
                )

            else:
                print(type(layer), layer.__dict__)

        if grid_lines:
            pg.draw.line(self.surface, Colours.green.value, self.surface.get_rect().midtop,
                         self.surface.get_rect().midbottom, width=5)

    def get_surface(
            self,
            show_sprites: bool = True,
            offset=None
    ):
        if show_sprites:
            self.sprites.draw(self)

        display_surf = self.base_surface.copy()

        display_surf.blit(self.surface, (0, 0))

        display_surf.blit(self.render_surface.get_surface(),
                          self.extra_offset if not offset else self.extra_offset + offset)

        display_surf.blit(self.sprite_surface, (0, 0))

        return display_surf

    # def update_display_text(self, text, max_chars=None):
    #     if self.text_box not in self.sprites:
    #         self.sprites.add(self.text_box)
    #
    #     self.text_box.refresh()
    #
    #     text_rect = pg.Rect(pg.Vector2(12, 8) * self.text_box.scale, pg.Vector2(221, 34) * self.text_box.scale)
    #     self.text_box.add_text_2(text, text_rect, max_chars=max_chars)
    #     self.text_box.update_image()
    #
    # def display_message(
    #         self,
    #         text,
    #         window,
    #         *,
    #         speed: int | float = 1.0,
    #         keep_textbox: bool =False,
    #         offset: None = None,
    # ):
    #     for char_idx in range(1, len(text) + 1):
    #         self.update_display_text(text, max_chars=char_idx)
    #         window.blit(self.get_surface(offset=offset), (0, 0))
    #         pg.display.flip()
    #         # 20 ms per character
    #         pg.time.delay(int(40 / speed))
    #
    #     if not keep_textbox:
    #         self.sprites.remove(self.text_box)

    def get_sprite_types(self, sprite_type) -> list[pg.sprite.Sprite]:
        sprite_list = []
        for group in self.object_layer_sprites.values():
            for sprite in group.sprites():
                if isinstance(sprite, sprite_type):
                    sprite_list.append(sprite)

        return sprite_list

    def detect_map_edge(self) -> None | list[str]:
        """ Return a bool representing if the map edge is detected """

        player_pos = self.player.map_positions[self]

        tile_render_rect = pg.Rect(
            ceil(player_pos.x - self.view_screen_tile_size.x / 2),
            ceil(player_pos.y - 1 - self.view_screen_tile_size.y / 2),
            self.view_screen_tile_size.x, self.view_screen_tile_size.y
        )

        edges = []
        if tile_render_rect.top < 0:
            edges.append("top")
        if tile_render_rect.bottom > self.height:
            edges.append("bottom")
        if tile_render_rect.left < 0:
            edges.append("left")
        if tile_render_rect.right > self.width:
            edges.append("right")

        return edges if len(edges) > 0 else None

    def update_sprites(self):
        for _, sp_group in self.object_layer_sprites.items():
            sp_group: MapObjects
            sp_group.update()

    def add_character(
            self,
            character: Character,
            position: pg.Vector2,
            *,
            layer_name: str = None
    ):
        add_layer = None
        if layer_name:
            add_layer = next((obj_layer for obj_layer in self.object_layers if obj_layer.name == layer_name), None)

        if add_layer is None:
            add_layer = self.object_layers[0]

        character.map_positions.update({self: position})
        self.object_layer_sprites[add_layer.id].add(character)

    def remove_character(self, character: Character) -> bool:
        sprite_groups = self.object_layer_sprites.values()
        for sprite_group in sprite_groups:
            if character in sprite_group:
                sprite_group.remove(character)
                return True

        return False


class MapObjects(pg.sprite.Group):
    def __init__(self, tile_size, render_mode=0):
        pg.sprite.Group.__init__(self)

        self.tile_size = tile_size
        self.render_mode = render_mode

    def __repr__(self):
        return f"<MapObjects> {self.sprites}"

    # def add(
    #     self, *sprites
    # ):
    #     super().add(*sprites)
    #     self.spritedict = sorted(
    #         self.spritedict.items(), key=lambda sprite: self.get_obj_y_location(sprite, _map)
    #     )

    @staticmethod
    def get_obj_y_location(obj, _map):
        return obj.map_rects[_map].top if isinstance(obj, Character) else obj.rect.top

    def draw(
        self,
        _map: TiledMap2,
        player_offset: pg.Vector2 = pg.Vector2(0, 0),
        camera_offset: pg.Vector2 = pg.Vector2(0, 0),
        special_flags: int = 0,
        verbose=False
    ):
        """
        Custom sprite drawing.

        :param _map: Map object to draw sprites onto
        :param player_offset: Player offset to draw sprites on. Units are pixels.
        :param camera_offset: Optional camera offset to draw sprites on. Units are pixels.
        :param special_flags: Special flags.
        :param verbose: Verbose flag.
        """
        sprite_set = sorted(self.sprites(), key=lambda sprite: self.get_obj_y_location(sprite, _map))
        render_offset = player_offset - camera_offset
        for obj in sprite_set:
            if isinstance(obj, Character):
                im_size = pg.Vector2(obj.image.get_size())
                npc_offset = pg.Vector2((im_size.x - self.tile_size.x) / 2, im_size.y - self.tile_size.y)
                if obj.visible:
                    _map.render_surface.add_surf(obj.image, obj.map_rects[_map].topleft - render_offset - npc_offset)

                if self.render_mode > 0:
                    player_rect = obj.map_rects[_map].move(-render_offset.x, -render_offset.y)
                    pg.draw.rect(_map.render_surface.surface, Colours.green.value, player_rect, width=1)

                    if isinstance(obj, Trainer) and not isinstance(obj, Player2):
                        vision_rect = obj.get_vision_rect(_map).move(-render_offset.x, -render_offset.y)
                        pg.draw.rect(_map.render_surface.surface, Colours.red.value, vision_rect, width=1)

            elif isinstance(obj, AttentionBubble):
                im_size = pg.Vector2(obj.character.image.get_size())
                npc_offset = pg.Vector2((im_size.x - self.tile_size.x) / 2, im_size.y - self.tile_size.y)

                trainer_rect = obj.character.map_rects[_map].move(-npc_offset)
                obj.rect.midbottom = trainer_rect.midtop
                _map.render_surface.add_surf(obj.image, obj.rect.topleft - render_offset)

            else:
                if getattr(obj, "image", None) is not None:
                    _map.render_surface.add_surf(obj.image, obj.rect.topleft - render_offset)
