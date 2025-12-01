
__all__ = ['GameError', 'MapError',]

class GameError(Exception):
    """Base class for all app-level errors."""
    pass

class MapError(GameError):
    pass
