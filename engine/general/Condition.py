from enum import Enum

from engine.general.Status_Conditions.Burn import Burn
from engine.general.Status_Conditions.Poison import Poison


class StatusCondition(Enum):
    poison = Poison()
    burn = Burn()
