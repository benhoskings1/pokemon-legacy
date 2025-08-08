import argparse
import json

import pygame as pg
from game import Game


def map_properties(obj, path="root", seen=None, filter_types=None, results=None):
    if seen is None:
        seen = set()
    if results is None:
        results = []

    if id(obj) in seen:
        return results  # Avoid circular references
    seen.add(id(obj))

    # Check the object type against filter
    def matches_filter(value):
        return (
            not filter_types or
            isinstance(value, tuple(filter_types))
        )

    if isinstance(obj, dict):
        for key, value in obj.items():
            key_path = f"{path}['{key}']"
            if matches_filter(value):
                results.append((key_path, type(value).__name__))
            map_properties(value, key_path, seen, filter_types, results)
    elif isinstance(obj, (list, tuple, set)):
        for i, item in enumerate(obj):
            item_path = f"{path}[{i}]"
            if matches_filter(item):
                results.append((item_path, type(item).__name__))
            map_properties(item, item_path, seen, filter_types, results)
    elif hasattr(obj, "__dict__"):
        for attr, value in vars(obj).items():
            attr_path = f"{path}.{attr}"
            if matches_filter(value):
                results.append((attr_path, type(value).__name__))
            map_properties(value, attr_path, seen, filter_types, results)
    else:
        if matches_filter(obj):
            results.append((path, type(obj).__name__))

    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--new", action="store_true")

    args = parser.parse_args()

    pg.init()
    pg.event.pump()

    game = Game(overwrite=True, save_slot=1, new=args.new)
    game.loop()

    object_map = map_properties(game, filter_types=[pg.Surface])
    print("writing file")
    with open("matched_properties.json", "w") as f:
        json.dump(object_map, f, indent=2)

