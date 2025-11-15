
from enum import Enum

from dataclasses import dataclass
from engine.characters.character import Character


class GameActionType(Enum):
    move = 0
    rotate = 1
    talk = 2


@dataclass
class GameAction:
    actor: Character
    action_type: GameActionType