from enum import Enum

from pokemon_legacy.engine.general.Status_Conditions.Burn import Burn
from pokemon_legacy.engine.general.Status_Conditions.Poison import Poison


class StatusCondition(Enum):
    poison = Poison()
    burn = Burn()
