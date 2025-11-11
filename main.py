import argparse
import json

import pygame as pg
from game import Game

from general.utils import map_properties

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--new", action="store_true")
    parser.add_argument("-o", "--overwrite", action="store_false")

    parser.add_argument("-e", "--explore-mode", action="store_true")
    parser.add_argument('-r', '--render-mode', action='count', default=0)

    args = parser.parse_args()

    pg.init()
    pg.event.pump()

    print(f"starting game with mode: {args}")

    game = Game(
        overwrite=args.overwrite,
        save_slot=1,
        new=args.new,
        explore_mode=args.explore_mode,
        render_mode=args.render_mode
    )
    game.loop()

    object_map = map_properties(game, filter_types=[pg.Surface])
    print("writing file")
    with open("matched_properties.json", "w") as f:
        json.dump(object_map, f, indent=2)

