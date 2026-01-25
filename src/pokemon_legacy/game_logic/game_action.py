from dataclasses import dataclass
from enum import Enum

class GameActionType(Enum):
    delay = 0
    movement = 1


@dataclass
class GameAction:
    """
    This is a base class to derive any game actions.
    It will form the basis for the event pipes of preset game interactions
    """
    action_type: GameActionType
    delay_duration: None | int = None  # optional duration in milliseconds
