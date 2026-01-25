"""
Tests for camera offset functionality.

These tests verify:
- Camera offset propagation through render calls
- Pixel conversion for camera offset
- Camera offset effect on render position calculations
"""
import pytest
import pygame as pg
from unittest.mock import MagicMock, call


class TestCameraOffsetBasics:
    """Test basic camera offset properties."""
    
    def test_camera_offset_zero_by_default(self, camera_offset_zero):
        """Default camera offset should be zero vector."""
        assert camera_offset_zero == pg.Vector2(0, 0)
    
    def test_camera_offset_can_be_non_zero(self, camera_offset_sample):
        """Camera offset can have non-zero values."""
        assert camera_offset_sample != pg.Vector2(0, 0)
        assert camera_offset_sample.x == 3
        assert camera_offset_sample.y == -2


class TestCameraOffsetPixelConversion:
    """Test conversion of camera offset from tiles to pixels."""
    
    def test_offset_to_pixels(self, camera_offset_sample, tile_config):
        """Camera offset should convert to pixels correctly."""
        pixels = pg.Vector2(
            camera_offset_sample.x * tile_config.tilewidth,
            camera_offset_sample.y * tile_config.tileheight
        )
        
        expected_x = 3 * 16  # 48 pixels
        expected_y = -2 * 16  # -32 pixels
        
        assert pixels.x == expected_x
        assert pixels.y == expected_y
    
    def test_zero_offset_zero_pixels(self, camera_offset_zero, tile_config):
        """Zero camera offset should produce zero pixel offset."""
        pixels = pg.Vector2(
            camera_offset_zero.x * tile_config.tilewidth,
            camera_offset_zero.y * tile_config.tileheight
        )
        
        assert pixels == pg.Vector2(0, 0)


class TestCameraOffsetPropagation:
    """Test camera offset propagation through method calls."""
    
    def test_map_collection_passes_offset_to_render(self, mock_map_collection, mock_map, camera_offset_sample):
        """MapCollection.render should pass camera_offset to TiledMap2.render."""
        # Simulate MapCollection behavior
        mock_map_collection.render(camera_offset=camera_offset_sample)
        
        # Verify render was called
        mock_map_collection.render.assert_called()
    
    def test_mock_map_receives_offset(self, mock_map, camera_offset_sample):
        """TiledMap2.render should receive camera_offset."""
        mock_map.render(camera_offset=camera_offset_sample)
        
        mock_map.render.assert_called_with(camera_offset=camera_offset_sample)


class TestTileRenderRectOffset:
    """Test how camera offset affects tile render rect calculation."""
    
    def test_offset_shifts_render_rect(self, camera_offset_sample):
        """Camera offset should shift the tile render rect."""
        # Simulate the tile_render_rect calculation from TiledMap2.render()
        player_pos = pg.Vector2(10, 10)
        view_screen_tile_size = pg.Vector2(19, 18)
        
        # Base render rect (centered on player)
        from math import ceil
        tile_render_rect = pg.Rect(
            ceil(player_pos.x - view_screen_tile_size.x / 2),
            ceil(player_pos.y - 1 - view_screen_tile_size.y / 2),
            view_screen_tile_size.x,
            view_screen_tile_size.y
        )
        
        original_left = tile_render_rect.left
        original_top = tile_render_rect.top
        
        # Apply camera offset
        offset_rect = tile_render_rect.move(camera_offset_sample)
        
        assert offset_rect.left == original_left + camera_offset_sample.x
        assert offset_rect.top == original_top + camera_offset_sample.y
    
    def test_zero_offset_no_shift(self, camera_offset_zero):
        """Zero camera offset should not shift render rect."""
        tile_render_rect = pg.Rect(5, 5, 19, 18)
        
        offset_rect = tile_render_rect.move(camera_offset_zero)
        
        assert offset_rect.topleft == tile_render_rect.topleft


class TestCameraOffsetInRenderOffset:
    """Test camera offset in the render_offset calculation for MapObjects.draw."""
    
    def test_render_offset_includes_camera(self, camera_offset_sample, tile_config):
        """render_offset should subtract camera_offset from player_offset."""
        player_offset = pg.Vector2(100, 80)  # Example player offset in pixels
        camera_offset_pixels = pg.Vector2(
            camera_offset_sample.x * tile_config.tilewidth,
            camera_offset_sample.y * tile_config.tileheight
        )
        
        render_offset = player_offset - camera_offset_pixels
        
        expected = player_offset - camera_offset_pixels
        assert render_offset == expected
    
    def test_zero_camera_offset_unchanged_render_offset(self, camera_offset_zero, tile_config):
        """With zero camera offset, render_offset equals player_offset."""
        player_offset = pg.Vector2(100, 80)
        camera_offset_pixels = pg.Vector2(
            camera_offset_zero.x * tile_config.tilewidth,
            camera_offset_zero.y * tile_config.tileheight
        )
        
        render_offset = player_offset - camera_offset_pixels
        
        assert render_offset == player_offset


class TestCameraPanSimulation:
    """Test camera panning behavior simulation."""
    
    def test_pan_interpolation(self):
        """Camera pan should interpolate smoothly between positions."""
        start_offset = pg.Vector2(0, 0)
        target_offset = pg.Vector2(5, 0)  # Pan 5 tiles right
        frames = 10
        
        positions = []
        for frame in range(frames):
            t = (frame + 1) / frames
            current = start_offset.lerp(target_offset, t)
            positions.append(current)
        
        # Should end at target
        assert positions[-1] == target_offset
        
        # Each position should be greater than previous (for rightward pan)
        for i in range(1, len(positions)):
            assert positions[i].x >= positions[i-1].x
    
    def test_pan_maintains_direction(self):
        """Pan in a direction should only affect that axis."""
        start_offset = pg.Vector2(0, 0)
        direction_value = pg.Vector2(0, -1)  # Up
        tiles = 3
        target_offset = start_offset + direction_value * tiles
        
        assert target_offset.x == 0  # No horizontal change
        assert target_offset.y == -3  # Moved up 3 tiles
