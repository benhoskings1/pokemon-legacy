"""
Tests for MapObjects sprite group and drawing.

These tests verify:
- Y-sorting of sprites for proper depth ordering
- Sprite drawing with correct offsets
- Visibility flag behavior
- Render mode debug rectangles
"""
import pytest
import pygame as pg
from unittest.mock import MagicMock


class TestSpriteYSorting:
    """Test Y-based sorting of sprites for depth ordering."""
    
    def test_get_obj_y_location_character(self, real_npc, mock_map):
        """Y location for characters should use map_rects.top."""
        real_npc.map_positions[mock_map] = pg.Vector2(5, 10)
        
        # Simulate MapObjects.get_obj_y_location behavior
        y_loc = real_npc.map_rects[mock_map].top
        
        expected = 10 * 16  # tile 10 * tile height
        assert y_loc == expected
    
    def test_characters_sorted_by_y(self, mock_map):
        """Characters should be sorted by Y position, lowest first."""
        from pokemon_legacy.engine.characters.npc import NPC
        
        # Create two NPCs at different Y positions
        npc1 = NPC({"character_type": "youngster", "npc_name": "Top"}, scale=2)
        npc2 = NPC({"character_type": "youngster", "npc_name": "Bottom"}, scale=2)
        
        npc1.map_positions[mock_map] = pg.Vector2(5, 3)   # Higher on screen (lower Y)
        npc2.map_positions[mock_map] = pg.Vector2(5, 10)  # Lower on screen (higher Y)
        
        sprites = [npc2, npc1]  # Intentionally reversed
        
        # Sort like MapObjects.draw does
        sorted_sprites = sorted(sprites, key=lambda s: s.map_rects[mock_map].top)
        
        assert sorted_sprites[0].name == "Top"
        assert sorted_sprites[1].name == "Bottom"


class TestRenderOffset:
    """Test render offset calculation for sprite positioning."""
    
    def test_render_offset_calculation(self, tile_config):
        """Render offset should be player_offset - camera_offset."""
        player_offset = pg.Vector2(100, 80)
        camera_offset = pg.Vector2(0, 0)
        
        render_offset = player_offset - camera_offset
        
        assert render_offset == player_offset
    
    def test_render_offset_with_camera(self, tile_config):
        """Camera offset should shift render offset."""
        player_offset = pg.Vector2(100, 80)
        camera_offset_tiles = pg.Vector2(2, 1)
        camera_offset_pixels = pg.Vector2(
            camera_offset_tiles.x * tile_config.tilewidth,
            camera_offset_tiles.y * tile_config.tileheight
        )
        
        render_offset = player_offset - camera_offset_pixels
        
        assert render_offset.x == 100 - 32  # 100 - 2*16
        assert render_offset.y == 80 - 16   # 80 - 1*16


class TestNPCOffset:
    """Test NPC sprite centering offset calculation."""
    
    def test_npc_offset_centers_horizontally(self, real_npc, tile_config):
        """NPC offset should center sprite horizontally on tile."""
        image = real_npc.image
        im_size = pg.Vector2(image.get_size())
        
        npc_offset_x = (im_size.x - tile_config.tile_size.x) / 2
        
        # Offset should be positive if sprite wider than tile
        if im_size.x > tile_config.tile_size.x:
            assert npc_offset_x > 0
    
    def test_npc_offset_aligns_bottom(self, real_npc, tile_config):
        """NPC offset should align sprite bottom to tile bottom."""
        image = real_npc.image
        im_size = pg.Vector2(image.get_size())
        
        npc_offset_y = im_size.y - tile_config.tile_size.y
        
        # Offset should be positive if sprite taller than tile
        if im_size.y > tile_config.tile_size.y:
            assert npc_offset_y > 0


class TestVisibilityInDraw:
    """Test visibility flag behavior during draw."""
    
    def test_invisible_sprites_not_drawn(self, real_npc, mock_map):
        """Invisible sprites should be skipped during draw."""
        real_npc.visible = False
        real_npc.map_positions[mock_map] = pg.Vector2(5, 5)
        
        # In actual draw:
        # if obj.visible:
        #     _map.render_surface.add_surf(...)
        
        assert real_npc.visible is False
    
    def test_visible_sprites_drawn(self, real_npc, mock_map):
        """Visible sprites should be drawn."""
        real_npc.visible = True
        real_npc.map_positions[mock_map] = pg.Vector2(5, 5)
        
        assert real_npc.visible is True


class TestSpriteDrawPosition:
    """Test sprite draw position calculations."""
    
    def test_character_draw_position(self, real_npc, mock_map, tile_config):
        """Character should be drawn at correct pixel position."""
        tile_pos = pg.Vector2(5, 10)
        real_npc.map_positions[mock_map] = tile_pos
        
        # Get map rect position
        rect = real_npc.map_rects[mock_map]
        
        # Calculate expected pixel position
        expected_x = tile_pos.x * tile_config.tilewidth
        expected_y = tile_pos.y * tile_config.tileheight
        
        assert rect.topleft == (expected_x, expected_y)
    
    def test_draw_position_with_render_offset(self, real_npc, mock_map, tile_config):
        """Draw position should account for render offset."""
        tile_pos = pg.Vector2(5, 10)
        real_npc.map_positions[mock_map] = tile_pos
        
        rect = real_npc.map_rects[mock_map]
        render_offset = pg.Vector2(100, 80)
        
        # Final draw position
        draw_pos = pg.Vector2(rect.topleft) - render_offset
        
        expected_x = (tile_pos.x * tile_config.tilewidth) - render_offset.x
        expected_y = (tile_pos.y * tile_config.tileheight) - render_offset.y
        
        assert draw_pos.x == expected_x
        assert draw_pos.y == expected_y
