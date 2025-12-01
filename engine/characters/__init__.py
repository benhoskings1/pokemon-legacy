from .character import CharacterTypes
from .npc import *

__all__ = ["npc_custom_mapping"]

npc_custom_mapping = {
    CharacterTypes.twinleaf_guard: TwinleafGuard,
    CharacterTypes.player_mum: PlayerMum,
}
