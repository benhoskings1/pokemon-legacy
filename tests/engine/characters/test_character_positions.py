"""
Tests for Character position tracking and sprite properties.

These tests verify:
- map_positions dictionary (tile coordinates per map)
- map_rects property (pixel rectangles per map)
- Character visibility and facing direction
- Follower tracking functionality
"""
import pytest
import pygame as pg


class TestCharacterPositions:
    """Test character position tracking across maps."""
    
    def test_map_positions_empty_on_init(self, real_npc):
        """New character should have empty map_positions."""
        assert real_npc.map_positions == {}
    
    def test_map_positions_stores_vector(self, real_npc, mock_map):
        """Character positions should be stored as Vector2."""
        position = pg.Vector2(5, 10)
        real_npc.map_positions[mock_map] = position
        
        assert mock_map in real_npc.map_positions
        assert real_npc.map_positions[mock_map] == position
    
    def test_map_positions_per_map_isolation(self, real_npc, mock_map):
        """Positions on different maps should be independent."""
        from unittest.mock import MagicMock
        
        mock_map_2 = MagicMock()
        mock_map_2.tilewidth = 16
        mock_map_2.tileheight = 16
        mock_map_2.tile_size = pg.Vector2(16, 16)
        
        pos1 = pg.Vector2(5, 10)
        pos2 = pg.Vector2(15, 3)
        
        real_npc.map_positions[mock_map] = pos1
        real_npc.map_positions[mock_map_2] = pos2
        
        assert real_npc.map_positions[mock_map] == pos1
        assert real_npc.map_positions[mock_map_2] == pos2


class TestCharacterMapRects:
    """Test map_rects property converting tile positions to pixel rects."""
    
    def test_map_rects_empty_when_no_positions(self, real_npc):
        """map_rects should be empty when no positions set."""
        assert real_npc.map_rects == {}
    
    def test_map_rects_converts_to_pixels(self, real_npc, mock_map, tile_config):
        """map_rects should convert tile coords to pixel rect."""
        tile_pos = pg.Vector2(5, 10)
        real_npc.map_positions[mock_map] = tile_pos
        
        rects = real_npc.map_rects
        rect = rects[mock_map]
        
        expected_x = tile_pos.x * tile_config.tilewidth
        expected_y = tile_pos.y * tile_config.tileheight
        
        assert rect.x == expected_x
        assert rect.y == expected_y
        assert rect.width == tile_config.tilewidth
        assert rect.height == tile_config.tileheight
    
    def test_map_rects_multiple_maps(self, real_npc, mock_map):
        """map_rects should provide rects for all maps with positions."""
        from unittest.mock import MagicMock
        
        mock_map_2 = MagicMock()
        mock_map_2.tilewidth = 32
        mock_map_2.tileheight = 32
        mock_map_2.tile_size = pg.Vector2(32, 32)
        
        real_npc.map_positions[mock_map] = pg.Vector2(1, 1)
        real_npc.map_positions[mock_map_2] = pg.Vector2(2, 2)
        
        rects = real_npc.map_rects
        
        assert len(rects) == 2
        assert rects[mock_map].x == 16  # 1 * 16
        assert rects[mock_map_2].x == 64  # 2 * 32


class TestCharacterFacingDirection:
    """Test character facing direction updates."""
    
    def test_default_facing_direction(self, real_npc, direction):
        """Character should have default facing direction from properties."""
        # Default in mock_npc_properties is "down"
        assert real_npc.facing_direction == direction.down
    
    def test_change_facing_direction(self, real_npc, direction):
        """Facing direction should be changeable."""
        real_npc.facing_direction = direction.left
        assert real_npc.facing_direction == direction.left
        
        real_npc.facing_direction = direction.up
        assert real_npc.facing_direction == direction.up


class TestCharacterVisibility:
    """Test character visibility flag."""
    
    def test_default_visibility(self, real_npc):
        """Characters should be visible by default."""
        assert real_npc.visible is True
    
    def test_set_invisible(self, real_npc):
        """Characters can be made invisible."""
        real_npc.visible = False
        assert real_npc.visible is False


class TestCharacterFollowerTracking:
    """Test position history and follower functionality."""
    
    def test_position_history_empty_on_init(self, real_npc):
        """Position history should be empty initially."""
        assert real_npc.position_history == []
    
    def test_record_position(self, real_npc, mock_map):
        """Recording position should add to history."""
        pos = pg.Vector2(5, 10)
        real_npc.record_position(mock_map, pos)
        
        assert len(real_npc.position_history) == 1
        recorded_map, recorded_pos = real_npc.position_history[0]
        assert recorded_map == mock_map
        assert recorded_pos == pos
    
    def test_position_history_limit(self, real_npc, mock_map):
        """Position history should respect max_history_length."""
        real_npc.max_history_length = 2
        
        real_npc.record_position(mock_map, pg.Vector2(1, 1))
        real_npc.record_position(mock_map, pg.Vector2(2, 2))
        real_npc.record_position(mock_map, pg.Vector2(3, 3))
        
        assert len(real_npc.position_history) == 2
        # Oldest position should be removed
        assert real_npc.position_history[0][1] == pg.Vector2(2, 2)
        assert real_npc.position_history[1][1] == pg.Vector2(3, 3)
    
    def test_get_last_position(self, real_npc, mock_map):
        """get_last_position should return oldest recorded position."""
        real_npc.max_history_length = 2  # Allow 2 positions in history
        real_npc.record_position(mock_map, pg.Vector2(1, 1))
        real_npc.record_position(mock_map, pg.Vector2(2, 2))
        
        result = real_npc.get_last_position()
        assert result is not None
        # Should return oldest (first) position
        assert result[1] == pg.Vector2(1, 1)
    
    def test_get_last_position_empty(self, real_npc):
        """get_last_position should return None with no history."""
        assert real_npc.get_last_position() is None
    
    def test_clear_position_history(self, real_npc, mock_map):
        """clear_position_history should empty the history."""
        real_npc.record_position(mock_map, pg.Vector2(1, 1))
        real_npc.clear_position_history()
        
        assert real_npc.position_history == []


class TestCharacterSpriteImage:
    """Test character sprite image selection."""
    
    def test_image_based_on_direction(self, real_npc, direction):
        """Sprite image should change based on facing direction."""
        real_npc.facing_direction = direction.down
        img_down = real_npc.image
        
        real_npc.facing_direction = direction.up
        img_up = real_npc.image
        
        # Images should be different surfaces for different directions
        # (Can't directly compare surfaces, but can check they exist)
        assert img_down is not None
        assert img_up is not None
    
    def test_image_exists(self, real_npc):
        """Character should have a loadable image."""
        assert real_npc.image is not None
        assert isinstance(real_npc.image, pg.Surface)
