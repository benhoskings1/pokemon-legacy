import pygame as pg
import pytmx
from pytmx import TiledMap
from pytmx.util_pygame import pygame_image_loader

from general.utils import Colours
from Map_Files.Map_Objects.Tall_Grass import TallGrass, Obstacle
from sprite_screen import SpriteScreen

from player import Player
from trainer import Trainer, TrainerTypes


class MapObjects(pg.sprite.Group):
    def __init__(self):
        pg.sprite.Group.__init__(self)

    def draw(self, surface, player_offset: pg.Vector2=pg.Vector2(0, 0), special_flags: int = 0):
        for obj in self.sprites():
            if isinstance(obj, Trainer):
                surface.blit(obj.image, obj.rect.topleft - player_offset - pg.Vector2(obj.image.get_size()) / 2)
            else:
                print(f"Object {obj} not implemented yet")
                ...


class TiledMap2(TiledMap, SpriteScreen):
    def __init__(self, file_path, size, player, scale=1):
        """
        This map dynamically renders the players immediate surroundings, rather than the entire map.

        :param file_path:
        :param size:
        :param scale:
        """
        args = []
        kwargs = {"pixelalpha": True, "image_loader": pygame_image_loader}
        TiledMap.__init__(self, file_path, *args, **kwargs)

        size = pg.Vector2(size[0], size[1]) + 4 * pg.Vector2(self.tilewidth, self.tileheight)
        SpriteScreen.__init__(self, size)

        self.scale = scale
        self.grassObjects = pg.sprite.Group()
        self.obstacles = pg.sprite.Group()

        self.map_objects = MapObjects()

        self.border_limits = pg.Vector2(3, 5)

        self.x_limits = (8, self.width - 8)
        self.y_limits = (7, self.height - 6)

        for obj in self.objects:
            rect = pg.Rect(obj.x, obj.y, obj.width, obj.height)
            if obj.name == "Grass":
                grass = TallGrass(rect, self.scale, obj.Location)
                self.grassObjects.add(grass)
            elif obj.name == "Obstacle":
                obstacle = Obstacle(rect, self.scale)
                self.obstacles.add(obstacle)
            elif obj.name == "NPC":
                trainer = Trainer(rect, obj.properties)
                self.map_objects.add(trainer)

        self.player = player
        self.render(self.player.position)

        # self.sprites = self.map_objects

    def render(self, player_pos: pg.Vector2, grid_lines=False):
        self.refresh()

        # ====== render static ======
        for layer in self.layers:
            count = 0
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    if player_pos.x - 10 <= x <= player_pos.x + 10 and player_pos.y - 6 <= y+1 <= player_pos.y + 11:
                        tile_image = self.get_tile_image_by_gid(gid)
                        if tile_image:
                            (width, height) = tile_image.get_size()

                            pos = (
                                (self.size / 2)
                                + pg.Vector2(
                                    (x - player_pos.x - 0.5) * self.tilewidth,
                                    (y - player_pos.y + 1) * self.tileheight - height
                                )
                            )
                            self.add_image(tile_image, pos)
                            if grid_lines:
                                pg.draw.rect(self.surface, Colours.red.value, pg.Rect(pos, tile_image.get_size()), width=2)
                        count += 1
        if grid_lines:
            pg.draw.line(self.surface, Colours.green.value, self.surface.get_rect().midtop,
                         self.surface.get_rect().midbottom, width=5)

        # ===== render trainers ======
        self.map_objects.draw(self.surface, player_offset=pg.Vector2(self.player.rect.topleft)-self.size/2)


    def detect_collision(self) -> list[pg.sprite.Sprite]:
        """
        Detects collisions between the player and the grass objects.
        """
        return pg.sprite.spritecollide(self.player, self.grassObjects, dokill=False)


if __name__ == '__main__':
    pg.init()
    native_size = pg.Vector2(256, 192)
    graphics_scale = 2
    displaySize = native_size * graphics_scale
    window = pg.display.set_mode(displaySize)

    # load all attributes which utilise any pygame surfaces!
    pg.display.set_caption('Map Files')
    pg.event.pump()

    player = Player("Sprites/Player Sprites", position=pg.Vector2(14, 13))

    sinnoh_map = TiledMap2('Map_Files/Sinnoh Map.tmx', displaySize, player=player)
    sinnoh_map.render(player.position)
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
            elif event.type == pg.KEYDOWN:
                ...

        window.blit(sinnoh_map.get_surface(), (32, 32))
        pg.display.flip()
