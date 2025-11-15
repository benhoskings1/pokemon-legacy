from engine.characters.character import Character


class NPC(Character):
    """
    Returns a NPC Object.
    """
    def __init__(self, properties: dict = None, scale: float = 1.0):
        """
        NPC Class
        """

        Character.__init__(
            self,
            properties,
            scale
        )


class TwinleafGuard(NPC):
    def __init__(self, properties: dict = None, scale: float = 1.0):
        properties["npc_type"] = "twinleaf_guard"
        NPC.__init__(
            self,
            properties,
            scale
        )

class ProfessorRowan(NPC):
    def __init__(self, properties: dict = None, scale: float = 1.0):
        NPC.__init__(
            self,
            properties,
            scale
        )

