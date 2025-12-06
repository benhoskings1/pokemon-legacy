
from enum import Enum

from engine.general.direction import Direction
from engine.storyline.game_state import GameState


__all__ = [
    "GameAction", "GameActionType", "MoveAction",
    "TalkAction", "WaitForKeyAction", "AttentionAction",
    "SetGameState", "SetCharacterVisibility", "TrainerBattle",
    "SetFacingDirection", "SetFollowingCharacter", "MoveCameraPosition",
]


class GameActionType(Enum):
    wait_for_key = 0
    move = 1
    talk = 2
    attention_bubble = 3
    set_game_state = 4
    set_character_visibility = 5
    set_following_character = 6
    trainer_battle = 7
    set_facing_direction = 8
    move_camera_position = 9


class GameAction:
    def __init__(self, actor, action_type: GameActionType):
        self.actor = actor
        self.action_type: GameActionType = action_type

    def __repr__(self):
        return f"{self.__class__.__name__}(actor={self.actor}, action_type={self.action_type})"


class WaitForKeyAction(GameAction):
    def __init__(self):
        GameAction.__init__(self, None, GameActionType.wait_for_key)


class TalkAction(GameAction):
    def __init__(self, actor, texts, ):
        GameAction.__init__(self, actor, GameActionType.talk)
        self.texts: list[str] = texts


class MoveAction(GameAction):
    def __init__(
            self,
            actor,
            direction: Direction,
            steps: int,
            *,
            duration: int = 200,
            ignore_facing_direction: bool = False,
            ignore_solid_objects: bool = False,
    ):
        GameAction.__init__(self, actor, GameActionType.move)
        self.direction = direction
        self.steps = steps

        self.duration = duration
        self.ignore_facing_direction = ignore_facing_direction
        self.ignore_solid_objects = ignore_solid_objects


class AttentionAction(GameAction):
    def __init__(self, actor, duration=2000):
        GameAction.__init__(self, actor, GameActionType.attention_bubble)
        self.duration = duration


class SetCharacterVisibility(GameAction):
    def __init__(self, actor, visible: bool):
        GameAction.__init__(self, actor, action_type=GameActionType.set_character_visibility)
        self.visible = visible


class SetFollowingCharacter(GameAction):
    def __init__(self, actor):
        GameAction.__init__(self, actor, action_type=GameActionType.set_following_character)


class TrainerBattle(GameAction):
    def __init__(self, actor):
        GameAction.__init__(self, actor, GameActionType.trainer_battle)


class SetGameState(GameAction):
    def __init__(self, game_state: GameState):
        GameAction.__init__(self, None, GameActionType.set_game_state)
        self.game_state = game_state


class SetFacingDirection(GameAction):
    def __init__(self, actor, direction: Direction, duration: int = 200):
        GameAction.__init__(self, actor, GameActionType.set_facing_direction)
        self.direction = direction
        self.duration = duration


class MoveCameraPosition(GameAction):
    def __init__(self, direction: Direction, tiles: int = 1):
        GameAction.__init__(self, None, action_type=GameActionType.move_camera_position)
        self.direction = direction
        self.tiles = tiles


if __name__ == "__main__":
    move_action = MoveAction("test_actor", direction=Direction.down, steps=3)

    print(move_action.actor)