"""
Pytest configuration and shared fixtures for Pokemon Legacy tests.

These fixtures provide mock objects and initialized components for testing
the rendering and movement systems without requiring a full game setup.
"""
import os
import sys
from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import pytest
import pygame as pg

# Add src to path so we can import from pokemon_legacy
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture(scope="session", autouse=True)
def pygame_init():
    """Initialize pygame once for all tests."""
    os.environ['SDL_VIDEODRIVER'] = 'dummy'  # Use dummy video driver for headless testing
    pg.init()
    pg.display.set_mode((256, 192))
    yield
    pg.quit()


@pytest.fixture
def mock_surface():
    """Create a mock pygame surface for testing."""
    surface = pg.Surface((256, 192))
    return surface


@pytest.fixture
def mock_window(mock_surface):
    """Create a mock window surface."""
    return mock_surface


@dataclass
class MockTileSize:
    """Mock tile size configuration."""
    tilewidth: int = 16
    tileheight: int = 16
    tile_size: pg.Vector2 = None
    
    def __post_init__(self):
        self.tile_size = pg.Vector2(self.tilewidth, self.tileheight)


@pytest.fixture
def tile_config():
    """Provide tile size configuration."""
    return MockTileSize()


@pytest.fixture
def mock_map(tile_config):
    """
    Create a minimal mock TiledMap2 for testing.
    
    This mock provides the essential attributes and methods needed
    for character positioning and movement tests.
    """
    mock = MagicMock()
    mock.tilewidth = tile_config.tilewidth
    mock.tileheight = tile_config.tileheight
    mock.tile_size = tile_config.tile_size
    mock.map_name = "test_map"
    mock.width = 20
    mock.height = 20
    mock.border_rect = pg.Rect(0, 0, 20, 20)
    mock.map_scale = 2.0
    mock.view_screen_tile_size = pg.Vector2(19, 18)
    mock.view_field = pg.Vector2(16, 12)
    mock.object_layer_sprites = {}
    mock.object_layers = []
    
    # Mock render method
    mock.render = MagicMock()
    mock.get_surface = MagicMock(return_value=pg.Surface((256, 192)))
    mock.check_collision = MagicMock(return_value=None)
    mock.detect_map_edge = MagicMock(return_value=None)
    
    return mock


@pytest.fixture
def mock_player_properties():
    """Provide minimal properties dict for creating a player."""
    return {
        "character_type": "player_male",
        "character_id": -1,
        "npc_name": "TestPlayer",
        "trainer_id": "1001",
        "facing_direction": "down"
    }


@pytest.fixture
def mock_npc_properties():
    """Provide minimal properties dict for creating an NPC."""
    return {
        "character_type": "youngster",
        "character_id": 1,
        "npc_name": "TestNPC",
        "facing_direction": "down"
    }


@pytest.fixture
def direction():
    """Import Direction enum for tests."""
    from pokemon_legacy.engine.general.direction import Direction
    return Direction


@pytest.fixture
def movement():
    """Import Movement enum for tests."""
    from pokemon_legacy.engine.characters.character import Movement
    return Movement


# === Integration Test Fixtures ===

@pytest.fixture
def real_player():
    """
    Create a real Player2 instance for integration tests.
    
    Note: This requires loading sprite assets and may be slow.
    Use mock_player for unit tests where possible.
    """
    from pokemon_legacy.engine.characters.player import Player2
    from pokemon_legacy.engine.pokemon.team import Team
    from pokemon_legacy.engine.bag.bag import BagV2
    
    player = Player2(
        team=Team(),
        bag=BagV2(),
        scale=2.0
    )
    return player


@pytest.fixture
def real_npc(mock_npc_properties):
    """Create a real NPC instance for integration tests."""
    from pokemon_legacy.engine.characters.npc import NPC
    
    npc = NPC(properties=mock_npc_properties, scale=2.0)
    return npc


# === Camera Offset Test Fixtures ===

@pytest.fixture
def camera_offset_zero():
    """Provide zero camera offset."""
    return pg.Vector2(0, 0)


@pytest.fixture
def camera_offset_sample():
    """Provide a sample non-zero camera offset."""
    return pg.Vector2(3, -2)  # 3 tiles right, 2 tiles up


# === Map Collection Fixtures ===

@pytest.fixture
def mock_map_collection(mock_map):
    """Create a mock MapCollection for testing."""
    mock = MagicMock()
    mock.map = mock_map
    mock._active_map = mock_map
    mock.maps = [mock_map]
    mock.collection_name = "test_collection"
    mock.render = MagicMock()
    mock.get_surface = MagicMock(return_value=pg.Surface((256, 192)))
    mock.update_sprites = MagicMock()
    mock._get_active_maps = MagicMock(return_value=[mock_map])
    mock._get_adjoining_maps = MagicMock(return_value=None)
    
    return mock
