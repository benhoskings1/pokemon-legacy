import argparse
import json
import pickle

import pygame as pg
from game import Game, GameConfig

from engine.general.utils import map_properties

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--new", action="store_true")
    parser.add_argument("-o", "--overwrite", action="store_false")

    parser.add_argument("-e", "--explore-mode", action="store_true")
    parser.add_argument("-l", "--lazy-load", action="store_true")
    parser.add_argument('-r', '--render-mode', action='count', default=0)

    args = parser.parse_args()

    pg.init()
    pg.event.pump()
    pg.display.set_mode((800, 600))

    print(f"starting game with mode: {args}")

    cfg = GameConfig(
        text_speed=3.0,
        render_mode=args.render_mode,
        explore_mode=args.explore_mode,
        save_slot=1
    )

    if args.new:
        game = Game(
            overwrite=args.overwrite,
            save_slot=1,
            new=args.new,
            cfg=cfg,
        )
    else:
        save_dir = f"game_data/save_states/save_state_{cfg.save_slot}/"
        with open(save_dir + "game_temp.pickle", "rb") as f:
            game = pickle.load(f)

    game.loop()

    object_map = map_properties(game.rival, filter_types=[pg.Surface])
    print("writing file")
    with open("matched_properties.json", "w") as f:
        json.dump(object_map, f, indent=2)

