
from enum import Enum

from pokemon_legacy.engine.general.direction import Direction
from pokemon_legacy.engine.storyline.game_state import GameState


__all__ = [
    "GameAction", "GameActionType", "MoveAction",
    "TalkAction", "WaitForKeyAction", "AttentionAction",
    "SetGameState", "SetCharacterVisibility", "TrainerBattle",
    "SetFacingDirection", "SetFollowingCharacter", "MoveCameraPosition",
    "EasingType",
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
    def __init__(self, actor, following: bool = True, distance: int = 1):
        """
        Set a character to follow the player.
        
        :param actor: The character to follow/stop following
        :param following: True to start following, False to stop
        :param distance: How many tiles behind to follow (default 1)
        """
        GameAction.__init__(self, actor, action_type=GameActionType.set_following_character)
        self.following = following
        self.distance = distance


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


class EasingType(Enum):
    """Easing functions for smooth animations."""
    LINEAR = "linear"
    EASE_IN = "ease_in"           # Slow start, fast end
    EASE_OUT = "ease_out"         # Fast start, slow end  
    EASE_IN_OUT = "ease_in_out"   # Slow start and end, fast middle
    SMOOTH_STEP = "smooth_step"   # Hermite interpolation (very smooth)


class MoveCameraPosition(GameAction):
    """
    Pan the camera smoothly in a direction.
    
    :param direction: Direction to pan (up, down, left, right)
    :param tiles: Number of tiles to pan
    :param duration: Total duration in milliseconds
    :param frames: Number of interpolation frames (higher = smoother)
    :param easing: Type of easing function for smooth motion
    :param return_to_start: If True, automatically pan back after reaching target
    :param pause_at_target: Milliseconds to pause at target before returning (if return_to_start)
    """
    def __init__(
            self, 
            direction: Direction, 
            tiles: int = 1, 
            duration: int = 1000, 
            frames: int = 60,
            easing: EasingType = EasingType.EASE_IN_OUT,
            return_to_start: bool = False,
            pause_at_target: int = 500,
    ):
        GameAction.__init__(self, None, action_type=GameActionType.move_camera_position)
        self.direction = direction
        self.tiles = tiles
        self.duration = duration
        self.frames = max(frames, 10)  # Minimum 10 frames for smoothness
        self.easing = easing
        self.return_to_start = return_to_start
        self.pause_at_target = pause_at_target
    
    @staticmethod
    def apply_easing(t: float, easing: EasingType) -> float:
        """
        Apply easing function to normalized time value.
        
        :param t: Normalized time (0.0 to 1.0)
        :param easing: Type of easing to apply
        :return: Eased value (0.0 to 1.0)
        """
        if easing == EasingType.LINEAR:
            return t
        elif easing == EasingType.EASE_IN:
            # Quadratic ease in: slow start
            return t * t
        elif easing == EasingType.EASE_OUT:
            # Quadratic ease out: slow end
            return 1 - (1 - t) * (1 - t)
        elif easing == EasingType.EASE_IN_OUT:
            # Cubic ease in-out: slow start and end
            if t < 0.5:
                return 4 * t * t * t
            else:
                return 1 - pow(-2 * t + 2, 3) / 2
        elif easing == EasingType.SMOOTH_STEP:
            # Hermite smooth step: very smooth S-curve
            return t * t * (3 - 2 * t)
        else:
            return t


if __name__ == "__main__":
    move_action = MoveAction("test_actor", direction=Direction.down, steps=3)

    print(move_action.actor)