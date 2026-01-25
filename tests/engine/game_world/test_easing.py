"""
Tests for EasingType functions and MoveCameraPosition action.

These tests verify:
- All easing functions produce correct values
- Easing functions are bounded (0 to 1 output for 0 to 1 input)
- MoveCameraPosition action properties
"""
import pytest
import pygame as pg


class TestEasingFunctions:
    """Test all easing functions produce correct curves."""
    
    @pytest.fixture
    def easing_type(self):
        """Import EasingType enum."""
        from pokemon_legacy.engine.storyline.game_action import EasingType
        return EasingType
    
    @pytest.fixture
    def apply_easing(self):
        """Import apply_easing function."""
        from pokemon_legacy.engine.storyline.game_action import MoveCameraPosition
        return MoveCameraPosition.apply_easing
    
    def test_linear_easing_returns_input(self, easing_type, apply_easing):
        """Linear easing should return exactly the input value."""
        for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
            result = apply_easing(t, easing_type.LINEAR)
            assert result == pytest.approx(t)
    
    def test_ease_in_starts_slow(self, easing_type, apply_easing):
        """Ease-in should start slower than linear."""
        t = 0.25
        linear = apply_easing(t, easing_type.LINEAR)
        ease_in = apply_easing(t, easing_type.EASE_IN)
        
        # Ease-in should be less than linear at start
        assert ease_in < linear
    
    def test_ease_out_ends_slow(self, easing_type, apply_easing):
        """Ease-out should end slower than linear."""
        t = 0.75
        linear = apply_easing(t, easing_type.LINEAR)
        ease_out = apply_easing(t, easing_type.EASE_OUT)
        
        # Ease-out should be greater than linear near end
        assert ease_out > linear
    
    def test_ease_in_out_symmetric(self, easing_type, apply_easing):
        """Ease-in-out should be at 0.5 when t=0.5."""
        result = apply_easing(0.5, easing_type.EASE_IN_OUT)
        assert result == pytest.approx(0.5, abs=0.01)
    
    def test_smooth_step_at_midpoint(self, easing_type, apply_easing):
        """Smooth step should be at 0.5 when t=0.5."""
        result = apply_easing(0.5, easing_type.SMOOTH_STEP)
        assert result == pytest.approx(0.5)
    
    def test_all_easings_bounded(self, easing_type, apply_easing):
        """All easing functions should return values between 0 and 1."""
        for easing in easing_type:
            for i in range(11):
                t = i / 10.0
                result = apply_easing(t, easing)
                assert 0.0 <= result <= 1.0, f"{easing.name} at t={t} returned {result}"
    
    def test_all_easings_start_at_zero(self, easing_type, apply_easing):
        """All easing functions should start at 0."""
        for easing in easing_type:
            result = apply_easing(0.0, easing)
            assert result == pytest.approx(0.0), f"{easing.name} at t=0 returned {result}"
    
    def test_all_easings_end_at_one(self, easing_type, apply_easing):
        """All easing functions should end at 1."""
        for easing in easing_type:
            result = apply_easing(1.0, easing)
            assert result == pytest.approx(1.0), f"{easing.name} at t=1 returned {result}"


class TestMoveCameraPositionAction:
    """Test MoveCameraPosition action configuration."""
    
    def test_default_values(self, direction):
        """Test default parameter values."""
        from pokemon_legacy.engine.storyline.game_action import MoveCameraPosition, EasingType
        
        action = MoveCameraPosition(direction.up)
        
        assert action.tiles == 1
        assert action.duration == 1000
        assert action.frames == 60
        assert action.easing == EasingType.EASE_IN_OUT
        assert action.return_to_start is False
        assert action.pause_at_target == 500
    
    def test_custom_values(self, direction):
        """Test custom parameter values."""
        from pokemon_legacy.engine.storyline.game_action import MoveCameraPosition, EasingType
        
        action = MoveCameraPosition(
            direction.right,
            tiles=5,
            duration=2000,
            frames=120,
            easing=EasingType.SMOOTH_STEP,
            return_to_start=True,
            pause_at_target=1000
        )
        
        assert action.direction == direction.right
        assert action.tiles == 5
        assert action.duration == 2000
        assert action.frames == 120
        assert action.easing == EasingType.SMOOTH_STEP
        assert action.return_to_start is True
        assert action.pause_at_target == 1000
    
    def test_minimum_frames_enforced(self, direction):
        """Frames should have minimum of 10 for smoothness."""
        from pokemon_legacy.engine.storyline.game_action import MoveCameraPosition
        
        action = MoveCameraPosition(direction.up, frames=5)
        
        assert action.frames == 10  # Enforced minimum


class TestCameraPanSimulation:
    """Test camera pan position calculations."""
    
    def test_position_interpolation(self, direction):
        """Test manual position interpolation with easing."""
        from pokemon_legacy.engine.storyline.game_action import MoveCameraPosition, EasingType
        
        start = pg.Vector2(0, 0)
        target = pg.Vector2(5, 0)  # 5 tiles right
        
        # Test at midpoint with ease-in-out
        t = 0.5
        eased_t = MoveCameraPosition.apply_easing(t, EasingType.EASE_IN_OUT)
        
        position = pg.Vector2(
            start.x + (target.x - start.x) * eased_t,
            start.y + (target.y - start.y) * eased_t
        )
        
        # At t=0.5, ease-in-out should be at ~0.5
        assert position.x == pytest.approx(2.5, abs=0.1)
        assert position.y == 0
    
    def test_return_to_start_option(self, direction):
        """Test return_to_start action configuration."""
        from pokemon_legacy.engine.storyline.game_action import MoveCameraPosition
        
        action = MoveCameraPosition(
            direction.up,
            tiles=3,
            return_to_start=True,
            pause_at_target=750
        )
        
        # Action should be configured for return
        assert action.return_to_start is True
        assert action.pause_at_target == 750
