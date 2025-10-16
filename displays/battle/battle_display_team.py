from enum import Enum

TEAM_CONTAINER_POSITIONS = [(1, 1), (129, 9), (1, 49), (129, 56), (1, 96), (129, 104)]


# =========== SETUP =============
class TeamDisplayStates(Enum):
    home = 0
    select = 1
    summary = 2
    moves = 3
    move_summary = 4



