import os

import pygame
import pygame as pg
import pytmx
from pytmx import TiledMap, TiledObject
from pytmx.util_pygame import pygame_image_loader

from math import floor, ceil

from general.utils import Colours, BlitLocation
from general.controller import Controller

from graphics.sprite_screen import SpriteScreen
from graphics.text_box import TextBox

from trainer import NPC, Trainer, Player2, Direction, Movement, AttentionBubble

from maps.game_obejct import GameObject


class Obstacle(GameObject):
    def __init__(self, rect, obj_id, scale: int | float = 1.0):
        GameObject.__init__(self, rect, obj_id, solid=True, scale=scale)


class EntryTile(GameObject):
    def __init__(self, rect: pg.Rect, obj_id: int, scale=1.0):
        GameObject.__init__(self, rect, obj_id, solid=True, scale=scale)


class ExitTile(GameObject):
    def __init__(self, rect: pg.Rect, obj_id: int, scale=1):
        GameObject.__init__(self, rect, obj_id, solid=True, scale=scale)


class TiledMap2(TiledMap, SpriteScreen):

    tile_object_mapping = {
        "obstacle": Obstacle,
        "exit": ExitTile,
    }

    def __init__(
            self,
            file_path,
            size: tuple[int, int] | pg.Vector2,
            player: Player2,
            player_position,
            player_layer: None | str = None,
            map_scale: float = 1.0,
            object_scale: float = 1.0,
            view_screen_tile_size=pg.Vector2(25, 18),
            view_field = None,
            map_directory: str = None
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
        """
        args = []
        kwargs = {"pixelalpha": True, "image_loader": pygame_image_loader}
        TiledMap.__init__(self, file_path, *args, **kwargs)

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

        SpriteScreen.__init__(self, size, colour=Colours.red)

        self.map_scale = map_scale
        self.obj_scale = object_scale

        self.render_surface = SpriteScreen(view_screen_size, )

        self.grassObjects = pg.sprite.Group()
        self.obstacles = pg.sprite.Group()

        self.map_objects = None

        self.player = player
        self.object_layer_sprites: dict[int, MapObjects] = {}
        self.load_objects()

        # add trainer map position
        player.map_positions.update({self: player_position})
        add_layer = None
        if player_layer:
            add_layer = next((obj for obj in self.object_layers if obj.name == player_layer), None)

        if add_layer is None:
            add_layer = self.object_layers[0]

        self.object_layer_sprites[add_layer.id].add(player)

        # TODO: fix the static scale here
        self.text_box = TextBox(sprite_id="text_box", scale=2, static=True)
        self.text_box.rect.topleft += pg.Vector2(6, 0)

        # self.load_custom_object_layers()

        self.render(player_position)

    def check_collision(self, trainer, direction: Direction) -> None | GameObject:
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
            npc_sprites = [s for s in object_group.sprites() if isinstance(s, NPC)]
            map_collision = new_rect.collideobjects(npc_sprites, key=lambda o: o.map_rects[self])
            if map_collision:
                return map_collision

            # get all solid objects
            other_sprites = [s for s in object_group.sprites() if s.solid and not isinstance(s, NPC)]
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
    ) -> tuple[GameObject | None, bool]:
        """ moves the specified trainer in a given direction """

        # only move player if facing the right direction
        if not trainer.facing_direction == direction:
            trainer.facing_direction = direction
            self.render()
            window.blit(self.get_surface(), (0, 0))
            pygame.display.flip()
            return None, False

        obj_collision = self.check_collision(trainer, direction)

        if obj_collision and obj_collision.solid:
            return self.object_interaction(obj_collision), False

        self.player._moving = True

        if not move_duration:
            move_duration = 200 if self.player.movement == Movement.walking else 125

        self.trainer_move_animation(trainer, direction, window, duration=move_duration)
        trainer._leg = not trainer._leg
        self.player._moving = False

        return obj_collision, True

    def trainer_move_animation(self, trainer: Trainer, direction: Direction, window: pg.Surface, frames: int = 5, duration: int = 200):
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
            self.render()

            start_pos = self.player.map_positions[self]

            for frame in range(frames):
                self.player.map_positions[self] = start_pos + direction.value * frame / frames
                self.render(start_pos=start_pos)
                window.blit(self.get_surface(), (0, 0))
                pg.display.flip()
                pg.time.delay(int(duration / frames))

            self.player.map_positions[self] = start_pos + direction.value

            self.player._moving = False
            self.render()

        else:
            # trainer._moving = True
            start_pos = trainer.map_positions[self]
            trainer._moving = True
            for frame_idx in range(frames):
                trainer.map_positions[self] = start_pos + direction.value * frame_idx / frames

                self.render()
                window.blit(self.get_surface(), (0, 0))
                pg.display.flip()
                pg.time.wait(round(duration / frames))

            trainer._moving = False

            # set back to integer values
            trainer.map_positions[self] = start_pos + direction.value
            # trainer.position += direction.value
            self.render()

        window.blit(self.get_surface(), (0, 0))
        pg.display.flip()

    def object_interaction(self, sprite: pg.sprite.Sprite):
        """ hook for automatic object interactions """
        if isinstance(sprite, ExitTile):
            self.running = False
            return sprite

        return None

    def load_objects(self):
        """
        Loads any default objects. Supported types are: 'npc', 'obstacle'
        """

        def create_object(obj_type, *args, **kwargs):
            return self.tile_object_mapping[obj_type](*args, **kwargs)

        for layer in self.object_layers:
            sprite_group = MapObjects(tile_size=self.tile_size)
            for obj in layer:
                rect = pg.Rect(obj.x, obj.y, obj.width, obj.height)
                if obj.type == "npc":
                    npc = NPC(obj.properties, scale=2)
                    npc.map_positions[self] = pg.Vector2(
                        (rect.x / self.tile_size_og.x),
                        (rect.y / self.tile_size_og.y)
                    )
                    npc._load_surfaces()
                    sprite_group.add(npc)

                elif obj.type == "trainer":
                    trainer = Trainer(obj.properties, scale=2)
                    trainer.map_positions[self] = pg.Vector2(
                        round(rect.x / self.tile_size_og.x),
                        round(rect.y / self.tile_size_og.y)
                    )

                    trainer._load_surfaces()
                    sprite_group.add(trainer)

                else:
                    if obj.type in self.tile_object_mapping.keys():
                        game_object = create_object(obj.type, rect, obj.id, scale=self.map_scale)
                        sprite_group.add(game_object)

                #     obj.type == "obstacle":
                #     obstacle = Obstacle(rect, obj_id=obj.id, scale=self.map_scale)
                #     sprite_group.add(obstacle)
                #
                # elif obj.type == "exit":
                #     exit_tile = ExitTile(rect, obj_id=obj.id, scale=self.map_scale)
                #     sprite_group.add(exit_tile)

            self.object_layer_sprites[layer.id] = sprite_group

    def move_player(self, direction: Direction, window):
        """ Moves the player by a given direction """
        collision, moved = self.move_trainer(self.player, direction, window)

        trainers = self.get_sprite_types(Trainer)
        trainer = self.player.map_rects[self].collideobjects(trainers, key=lambda o: o.get_vision_rect(self))
        if trainer is not None:
            collision = trainer

        return collision, moved

    def render(self, grid_lines=False, start_pos=None, verbose=False):
        """
        Renders the map

        Creates the underlying surface as the with extra column, then shifts the view -0.5 tiles to center align the
        map

        :param grid_lines:
        :return:
        """
        self.refresh()
        self.render_surface.refresh()

        player_pos = self.player.map_positions[self]

        render_pos = player_pos if not start_pos else start_pos

        tile_render_rect = pg.Rect(
            ceil(render_pos.x - self.view_screen_tile_size.x / 2),
            ceil(render_pos.y - 1 - self.view_screen_tile_size.y / 2),
            self.view_screen_tile_size.x, self.view_screen_tile_size.y
        )
        # ====== render static ======
        for layer in self.layers:
            if verbose:
                print(f"rendering layer {layer}")
            if isinstance(layer, pytmx.TiledImageLayer):
                source = getattr(layer, 'source', None)
                if source:
                    img_offset = pg.Vector2(layer.offsetx, layer.offsety) * self.map_scale
                    path = os.path.join("maps", self.map_directory, source)

                    # TODO: work out why these 0.5s are here?
                    pos = pg.Vector2((player_pos.x + 0.5 - self.view_field.x // 2) * self.tilewidth,
                                     (player_pos.y - self.view_field.y // 2) * self.tileheight)

                    pos -= img_offset
                    pos += self.extra_offset

                    self.render_surface.load_image(
                        path,
                        pos=-pos,
                        scale=self.map_scale,
                        # base=True
                    )

            elif isinstance(layer, pytmx.TiledTileLayer):
                offset = pg.Vector2(0, 0) if start_pos is None else player_pos - start_pos
                # print(f"offset: {offset}")
                for x, y, gid in layer:
                    if ((tile_render_rect.left <= x <= tile_render_rect.right)
                            and (tile_render_rect.top <= y <= tile_render_rect.bottom)):

                        tile_image = self.get_tile_image_by_gid(gid)
                        if tile_image:
                            (width, height) = tile_image.get_size()

                            pos = pg.Vector2(
                                (x - tile_render_rect.left - offset.x) * self.tilewidth * self.map_scale,
                                (y - tile_render_rect.top - offset.y) * self.tileheight * self.map_scale - height
                            )

                            self.render_surface.add_image(tile_image, pos, scale=self.map_scale)
                            if grid_lines:
                                pg.draw.rect(
                                    self.render_surface.surface,
                                    Colours.red.value,
                                    pg.Rect(pos, tile_image.get_size()),
                                    width=1
                                )

            elif isinstance(layer, pytmx.TiledObjectGroup):
                # draw spites that correspond to the layer
                pos = pg.Vector2((player_pos.x + 0.5 - self.view_field.x // 2) * self.tilewidth,
                                 (player_pos.y - self.view_field.y // 2) * self.tileheight)

                pos += self.extra_offset

                self.object_layer_sprites[layer.id].draw(self, player_offset=pos)

            else:
                print(type(layer), layer.__dict__)

        if grid_lines:
            pg.draw.line(self.surface, Colours.green.value, self.surface.get_rect().midtop,
                         self.surface.get_rect().midbottom, width=5)

    def get_surface(self, show_sprites=True, offset=None):

        if show_sprites:
            self.sprites.draw(self)

        display_surf = self.base_surface.copy()

        display_surf.blit(self.surface, (0, 0))

        display_surf.blit(self.render_surface.get_surface(),
                          self.extra_offset if not offset else self.extra_offset + offset)

        display_surf.blit(self.sprite_surface, (0, 0))

        return display_surf

    def update_display_text(self, text, max_chars=None):
        if self.text_box not in self.sprites:
            self.sprites.add(self.text_box)

        self.text_box.refresh()

        text_rect = self.text_box.image.get_rect().inflate(-20 * self.text_box.scale, -18*self.text_box.scale)
        # text_rect = pg.Rect(pg.Vector2(10, 4) * self.text_box.scale, pg.Vector2(201, 40) * self.text_box.scale)
        self.text_box.add_text_2(text, text_rect, max_chars=max_chars)
        self.text_box.update_image()

    def display_message(self, text, window, duration=1000):

        for char_idx in range(1, len(text) + 1):
            self.update_display_text(text, max_chars=char_idx)
            window.blit(self.get_surface(), (0, 0))
            pg.display.flip()
            pg.time.delay(round(duration * 0.7 / len(text)))

        self.sprites.remove(self.text_box)

    def get_sprite_types(self, sprite_type) -> list[pg.sprite.Sprite]:
        sprite_list = []
        for group in self.object_layer_sprites.values():
            for sprite in group.sprites():
                if isinstance(sprite, sprite_type):
                    sprite_list.append(sprite)

        return sprite_list

    def loop(self, render_surface, controller=Controller()):
        self.render()
        render_surface.blit(self.get_surface(), (0, 0))
        pg.display.flip()
        print("starting pokecenter loop")
        self.running = True
        while self.running:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.running = False

                elif event.type == pg.KEYDOWN:
                    if event.key in controller.move_keys:
                        player_moving = True

                        while player_moving:
                            collision, moved = self.move_player(
                                controller.direction_key_bindings[event.key],
                                window=render_surface
                            )

                            if collision:
                                self.object_interaction(collision)
                                if not self.running:
                                    break

                            pg.display.flip()

                            for event_2 in pg.event.get():
                                if event_2.type == pg.KEYUP:
                                    player_moving = False

                    elif event.key == controller.a:
                        obj_collision = self.check_collision(self.player, self.player.facing_direction)

                        if obj_collision:
                            print(obj_collision)
                            self.intentional_interaction(obj_collision, render_surface)



class MapObjects(pg.sprite.Group):
    def __init__(self, tile_size):
        pg.sprite.Group.__init__(self)

        self.tile_size = tile_size

    def __repr__(self):
        return f"<MapObjects> {self.sprites}"

    @staticmethod
    def get_obj_y_location(obj, _map):
        return obj.map_rects[_map].top if isinstance(obj, NPC) else obj.rect.top

    def draw(
        self,
        _map: TiledMap2,
        player_offset: pg.Vector2 = pg.Vector2(0, 0),
        special_flags: int = 0,
        verbose=False
    ):
        """ Custom sprite drawing """
        sprite_set = sorted(self.sprites(), key=lambda sprite: self.get_obj_y_location(sprite, _map))
        for obj in sprite_set:
            if isinstance(obj, NPC):
                im_size = pg.Vector2(obj.image.get_size())
                npc_offset = pg.Vector2((im_size.x - self.tile_size.x) / 2, im_size.y - self.tile_size.y)
                _map.render_surface.add_surf(obj.image, obj.map_rects[_map].topleft - player_offset - npc_offset)

                player_rect = obj.map_rects[_map].move(-player_offset.x, -player_offset.y)
                pg.draw.rect(_map.render_surface.surface, Colours.green.value, player_rect, width=1)

            elif isinstance(obj, AttentionBubble):
                im_size = pg.Vector2(obj.trainer.image.get_size())
                npc_offset = pg.Vector2((im_size.x - self.tile_size.x) / 2, im_size.y - self.tile_size.y)

                trainer_rect = obj.trainer.map_rects[_map].move(-npc_offset)
                obj.rect.midbottom = trainer_rect.midtop
                _map.render_surface.add_surf(obj.image, obj.rect.topleft - player_offset)

            else:
                if getattr(obj, "image", None) is not None:
                    _map.render_surface.add_surf(obj.image, obj.rect.topleft - player_offset)
