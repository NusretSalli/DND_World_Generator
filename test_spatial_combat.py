#!/usr/bin/env python3

"""
Test script for the spatial combat system

This script tests the core functionality of the spatial combat system
to ensure everything works correctly before integration testing.
"""

import sys
import os

# Add the project directory to the path so we can import our modules
sys.path.insert(0, '/home/runner/work/DND_World_Generator/DND_World_Generator')

from spatial_combat import (
    SpatialCombatGrid, GridPosition, TerrainType, SpatialCombatState,
    MovementValidator
)
from spatial_combat_visual import create_example_combat


def test_grid_creation():
    """Test basic grid creation and terrain setting."""
    print("Testing grid creation...")
    
    grid = SpatialCombatGrid(10, 10)
    assert grid.width == 10
    assert grid.height == 10
    
    # Test terrain setting
    pos = GridPosition(5, 5)
    grid.set_terrain(pos, TerrainType.BLOCKING, "Test Wall")
    terrain = grid.get_terrain(pos)
    assert terrain.terrain_type == TerrainType.BLOCKING
    assert terrain.description == "Test Wall"
    
    print("✓ Grid creation test passed")


def test_combatant_positioning():
    """Test combatant placement and movement."""
    print("Testing combatant positioning...")
    
    grid = SpatialCombatGrid(10, 10)
    
    # Place combatants
    pos1 = GridPosition(2, 2)
    pos2 = GridPosition(7, 7)
    
    assert grid.place_combatant(1, pos1) == True
    assert grid.place_combatant(2, pos2) == True
    
    # Test position retrieval
    assert grid.get_combatant_position(1) == pos1
    assert grid.get_combatant_position(2) == pos2
    
    # Test movement
    new_pos = GridPosition(3, 3)
    assert grid.move_combatant(1, new_pos) == True
    assert grid.get_combatant_position(1) == new_pos
    
    print("✓ Combatant positioning test passed")


def test_line_of_sight():
    """Test line of sight calculations."""
    print("Testing line of sight...")
    
    grid = SpatialCombatGrid(10, 10)
    
    pos1 = GridPosition(1, 1)
    pos2 = GridPosition(8, 8)
    
    # Clear line of sight
    assert grid.has_line_of_sight(pos1, pos2) == True
    
    # Block line of sight
    blocking_pos = GridPosition(4, 4)
    grid.set_terrain(blocking_pos, TerrainType.BLOCKING)
    assert grid.has_line_of_sight(pos1, pos2) == False
    
    print("✓ Line of sight test passed")


def test_movement_validation():
    """Test movement validation."""
    print("Testing movement validation...")
    
    grid = SpatialCombatGrid(10, 10)
    
    start_pos = GridPosition(1, 1)
    target_pos = GridPosition(3, 3)
    
    grid.place_combatant(1, start_pos)
    
    # Valid movement
    can_move, reason = MovementValidator.can_move_to(grid, 1, target_pos, 30)
    assert can_move == True
    
    # Invalid movement (too far)
    far_pos = GridPosition(9, 9)
    can_move, reason = MovementValidator.can_move_to(grid, 1, far_pos, 10)
    assert can_move == False
    
    print("✓ Movement validation test passed")


def test_cover_calculation():
    """Test cover calculation."""
    print("Testing cover calculation...")
    
    grid = SpatialCombatGrid(10, 10)
    
    attacker_pos = GridPosition(1, 1)
    target_pos = GridPosition(8, 8)
    
    # No cover
    cover = grid.get_cover_type(attacker_pos, target_pos)
    assert cover.value == 'none'
    
    # Add partial cover
    cover_pos = GridPosition(4, 4)
    grid.set_terrain(cover_pos, TerrainType.PARTIAL_COVER)
    cover = grid.get_cover_type(attacker_pos, target_pos)
    assert cover.value == 'half'
    
    print("✓ Cover calculation test passed")


def test_spatial_combat_state():
    """Test spatial combat state management."""
    print("Testing spatial combat state...")
    
    grid = SpatialCombatGrid(15, 15)
    state = SpatialCombatState(combat_id=1, grid=grid)
    
    # Add combatants
    pos1 = GridPosition(2, 2)
    pos2 = GridPosition(12, 12)
    
    assert state.add_combatant(1, pos1, 15) == True
    assert state.add_combatant(2, pos2, 12) == True
    
    # Check turn order
    assert len(state.turn_order) == 2
    
    # Test turn advancement
    current = state.get_current_combatant()
    state.next_turn()
    next_combatant = state.get_current_combatant()
    assert current != next_combatant or len(state.turn_order) == 1
    
    print("✓ Spatial combat state test passed")


def test_grid_serialization():
    """Test grid serialization and deserialization."""
    print("Testing grid serialization...")
    
    # Create a grid with some terrain and combatants
    grid = SpatialCombatGrid(5, 5)
    grid.set_terrain(GridPosition(2, 2), TerrainType.BLOCKING, "Wall")
    grid.place_combatant(1, GridPosition(1, 1))
    grid.place_combatant(2, GridPosition(3, 3))
    
    # Serialize
    data = grid.to_dict()
    
    # Deserialize
    new_grid = SpatialCombatGrid.from_dict(data)
    
    # Verify
    assert new_grid.width == grid.width
    assert new_grid.height == grid.height
    assert new_grid.get_terrain(GridPosition(2, 2)).terrain_type == TerrainType.BLOCKING
    assert new_grid.get_combatant_position(1) == GridPosition(1, 1)
    assert new_grid.get_combatant_position(2) == GridPosition(3, 3)
    
    print("✓ Grid serialization test passed")


def run_visual_test():
    """Run a visual test using pygame (if display is available)."""
    print("Testing visual interface...")
    
    try:
        import pygame
        pygame.init()
        
        # Test if we can create a display (might fail in headless environment)
        test_surface = pygame.display.set_mode((100, 100))
        pygame.quit()
        
        print("✓ Pygame is available for visual interface")
        return True
        
    except Exception as e:
        print(f"⚠ Pygame visual interface not available: {e}")
        return False


def main():
    """Run all tests."""
    print("Running Spatial Combat System Tests")
    print("=" * 50)
    
    try:
        test_grid_creation()
        test_combatant_positioning()
        test_line_of_sight()
        test_movement_validation()
        test_cover_calculation()
        test_spatial_combat_state()
        test_grid_serialization()
        run_visual_test()
        
        print("\n" + "=" * 50)
        print("✅ All tests passed! Spatial combat system is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)