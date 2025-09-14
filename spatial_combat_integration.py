# spatial_combat_integration.py

"""
Integration layer for Spatial Combat System with Flask Application

This module provides the bridge between the spatial combat system and the
existing D&D World Generator Flask application. It extends the existing
combat system with spatial positioning while maintaining compatibility
with the current database schema and API.

Key Features:
- Seamless integration with existing combat system
- Database storage of spatial combat states
- API endpoints for spatial combat operations
- Web interface for grid-based combat
- Backwards compatibility with traditional combat

Author: D&D World Generator
"""

import json
import threading
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import asdict
from flask import jsonify, request

from spatial_combat import (
    SpatialCombatGrid, GridPosition, TerrainType, SpatialCombatState,
    MovementValidator
)
from spatial_combat_visual import SpatialCombatInterface, CombatantVisual


class SpatialCombatManager:
    """
    Manages spatial combat encounters and integrates with the existing combat system.
    
    This class serves as the main interface between the Flask application and
    the spatial combat system, handling state persistence, API operations,
    and coordination with the visual interface.
    """
    
    def __init__(self, app_context):
        """
        Initialize the spatial combat manager.
        
        Args:
            app_context: Flask application context for database access
        """
        self.app = app_context
        
        # Active spatial combat sessions
        self.active_combats: Dict[int, SpatialCombatState] = {}
        
        # Visual interfaces (for standalone pygame windows)
        self.visual_interfaces: Dict[int, SpatialCombatInterface] = {}
        
        # Thread management for visual interfaces
        self.interface_threads: Dict[int, threading.Thread] = {}
    
    def create_spatial_combat(self, combat_id: int, width: int = 20, height: int = 15,
                            terrain_setup: Optional[Dict] = None) -> SpatialCombatState:
        """
        Create a new spatial combat encounter.
        
        Args:
            combat_id: ID of the combat from the existing system
            width: Grid width in squares
            height: Grid height in squares
            terrain_setup: Optional terrain configuration
            
        Returns:
            Created spatial combat state
        """
        from app import Combat, Combatant, db
        
        # Get existing combat data
        combat = Combat.query.get(combat_id)
        if not combat:
            raise ValueError(f"Combat {combat_id} not found")
        
        # Create spatial grid
        grid = SpatialCombatGrid(width, height)
        
        # Apply terrain setup if provided
        if terrain_setup:
            self._apply_terrain_setup(grid, terrain_setup)
        
        # Create spatial combat state
        spatial_state = SpatialCombatState(
            combat_id=combat_id,
            grid=grid,
            round_number=combat.current_round
        )
        
        # Add existing combatants to spatial grid
        for combatant in combat.combatants:
            # Place combatants in default positions (can be customized)
            position = self._get_default_position(grid, combatant.id)
            spatial_state.add_combatant(combatant.id, position, combatant.initiative)
        
        # Store the spatial combat state
        self.active_combats[combat_id] = spatial_state
        
        # Save spatial state to database
        self._save_spatial_state(combat_id, spatial_state)
        
        return spatial_state
    
    def _apply_terrain_setup(self, grid: SpatialCombatGrid, terrain_setup: Dict) -> None:
        """
        Apply terrain configuration to a grid.
        
        Args:
            grid: Grid to modify
            terrain_setup: Terrain configuration dictionary
        """
        for feature in terrain_setup.get('features', []):
            terrain_type = TerrainType(feature['type'])
            positions = feature['positions']
            description = feature.get('description', '')
            
            for pos_data in positions:
                position = GridPosition(pos_data['x'], pos_data['y'])
                if grid.is_valid_position(position):
                    grid.set_terrain(position, terrain_type, description)
    
    def _get_default_position(self, grid: SpatialCombatGrid, combatant_id: int) -> GridPosition:
        """
        Get a default starting position for a combatant.
        
        Args:
            grid: Combat grid
            combatant_id: ID of the combatant
            
        Returns:
            Default position for the combatant
        """
        # Simple placement strategy: spread combatants around the edges
        # In a real implementation, this could be more sophisticated
        
        occupied_positions = set(grid.combatant_positions.values())
        
        # Try positions along the edges
        edge_positions = []
        
        # Left edge
        for y in range(grid.height):
            edge_positions.append(GridPosition(1, y))
        
        # Right edge  
        for y in range(grid.height):
            edge_positions.append(GridPosition(grid.width - 2, y))
        
        # Top edge
        for x in range(1, grid.width - 1):
            edge_positions.append(GridPosition(x, 1))
        
        # Bottom edge
        for x in range(1, grid.width - 1):
            edge_positions.append(GridPosition(x, grid.height - 2))
        
        # Find first available position
        for position in edge_positions:
            if (position not in occupied_positions and 
                grid.is_valid_position(position) and
                grid.get_terrain(position).movement_cost != float('inf')):
                return position
        
        # Fallback: find any open position
        for x in range(grid.width):
            for y in range(grid.height):
                position = GridPosition(x, y)
                if (position not in occupied_positions and
                    grid.is_valid_position(position) and
                    grid.get_terrain(position).movement_cost != float('inf')):
                    return position
        
        # Final fallback
        return GridPosition(0, 0)
    
    def get_spatial_combat(self, combat_id: int) -> Optional[SpatialCombatState]:
        """Get spatial combat state by ID."""
        return self.active_combats.get(combat_id)
    
    def move_combatant(self, combat_id: int, combatant_id: int, 
                      target_x: int, target_y: int, 
                      movement_speed: int = 30) -> Tuple[bool, str]:
        """
        Move a combatant to a new position.
        
        Args:
            combat_id: Combat encounter ID
            combatant_id: Combatant to move
            target_x: Target X coordinate
            target_y: Target Y coordinate  
            movement_speed: Available movement in feet
            
        Returns:
            Tuple of (success, message)
        """
        spatial_state = self.get_spatial_combat(combat_id)
        if not spatial_state:
            return False, "Spatial combat not found"
        
        target_position = GridPosition(target_x, target_y)
        
        # Validate movement
        can_move, reason = MovementValidator.can_move_to(
            spatial_state.grid, combatant_id, target_position, movement_speed
        )
        
        if not can_move:
            return False, reason
        
        # Execute movement
        success = spatial_state.grid.move_combatant(combatant_id, target_position)
        if success:
            # Save updated state
            self._save_spatial_state(combat_id, spatial_state)
            return True, "Movement successful"
        else:
            return False, "Failed to move combatant"
    
    def get_combat_grid_data(self, combat_id: int) -> Optional[Dict]:
        """
        Get complete grid data for a combat encounter.
        
        Args:
            combat_id: Combat encounter ID
            
        Returns:
            Dictionary with grid data or None if not found
        """
        spatial_state = self.get_spatial_combat(combat_id)
        if not spatial_state:
            return None
        
        from app import Combat, Combatant
        
        # Get combatant data from database
        combat = Combat.query.get(combat_id)
        if not combat:
            return None
        
        combatants_data = []
        for combatant in combat.combatants:
            position = spatial_state.grid.get_combatant_position(combatant.id)
            combatants_data.append({
                'id': combatant.id,
                'character_id': combatant.character_id,
                'character_name': combatant.character.name,
                'character_class': combatant.character.character_class,
                'current_hp': combatant.current_hp,
                'max_hp': combatant.character.max_hp,
                'ac': combatant.character.armor_class,
                'initiative': combatant.initiative,
                'position': {'x': position.x, 'y': position.y} if position else None,
                'conditions': combatant.conditions_list,
                'has_action': combatant.has_action,
                'has_bonus_action': combatant.has_bonus_action,
                'has_movement': combatant.has_movement,
                'has_reaction': combatant.has_reaction
            })
        
        return {
            'combat_id': combat_id,
            'grid': spatial_state.grid.to_dict(),
            'combatants': combatants_data,
            'current_turn': spatial_state.current_turn_index,
            'round_number': spatial_state.round_number,
            'turn_order': spatial_state.turn_order
        }
    
    def calculate_attack_modifiers(self, combat_id: int, attacker_id: int, 
                                 target_id: int) -> Dict:
        """
        Calculate attack modifiers based on spatial positioning.
        
        Args:
            combat_id: Combat encounter ID
            attacker_id: Attacking combatant ID
            target_id: Target combatant ID
            
        Returns:
            Dictionary with attack modifiers
        """
        spatial_state = self.get_spatial_combat(combat_id)
        if not spatial_state:
            return {'ac_bonus': 0, 'cover_type': 'none', 'disadvantage': False}
        
        attacker_pos = spatial_state.grid.get_combatant_position(attacker_id)
        target_pos = spatial_state.grid.get_combatant_position(target_id)
        
        if not attacker_pos or not target_pos:
            return {'ac_bonus': 0, 'cover_type': 'none', 'disadvantage': False}
        
        # Calculate cover
        cover_type = spatial_state.grid.get_cover_type(attacker_pos, target_pos)
        
        # Cover bonuses according to D&D 5e
        ac_bonus = 0
        if cover_type.value == 'half':
            ac_bonus = 2
        elif cover_type.value == 'three_quarters':
            ac_bonus = 5
        elif cover_type.value == 'full':
            ac_bonus = 999  # Cannot target
        
        # Check for disadvantage conditions
        disadvantage = False
        
        # Long range disadvantage (simplified - would need weapon data)
        distance = attacker_pos.distance_to(target_pos)
        if distance > 60:  # Beyond normal range for most weapons
            disadvantage = True
        
        return {
            'ac_bonus': ac_bonus,
            'cover_type': cover_type.value,
            'disadvantage': disadvantage,
            'distance': distance
        }
    
    def get_valid_movements(self, combat_id: int, combatant_id: int, 
                          movement_speed: int = 30) -> List[Dict]:
        """
        Get all valid movement positions for a combatant.
        
        Args:
            combat_id: Combat encounter ID
            combatant_id: Combatant ID
            movement_speed: Available movement in feet
            
        Returns:
            List of valid position dictionaries
        """
        spatial_state = self.get_spatial_combat(combat_id)
        if not spatial_state:
            return []
        
        valid_positions = spatial_state.grid.get_valid_moves(combatant_id, movement_speed)
        
        return [{'x': pos.x, 'y': pos.y} for pos in valid_positions]
    
    def get_attack_range_positions(self, combat_id: int, combatant_id: int,
                                 weapon_range: int = 5) -> List[Dict]:
        """
        Get all positions within attack range.
        
        Args:
            combat_id: Combat encounter ID
            combatant_id: Combatant ID
            weapon_range: Weapon range in feet
            
        Returns:
            List of position dictionaries within range
        """
        spatial_state = self.get_spatial_combat(combat_id)
        if not spatial_state:
            return []
        
        range_positions = spatial_state.grid.get_attack_range_positions(combatant_id, weapon_range)
        
        return [{'x': pos.x, 'y': pos.y} for pos in range_positions]
    
    def launch_visual_interface(self, combat_id: int) -> bool:
        """
        Launch a pygame visual interface for the combat.
        
        Args:
            combat_id: Combat encounter ID
            
        Returns:
            True if interface launched successfully
        """
        spatial_state = self.get_spatial_combat(combat_id)
        if not spatial_state:
            return False
        
        # Don't launch if already running
        if combat_id in self.visual_interfaces:
            return True
        
        try:
            # Create visual interface
            interface = SpatialCombatInterface(spatial_state.grid, spatial_state)
            
            # Add combatant visual data
            from app import Combat
            combat = Combat.query.get(combat_id)
            if combat:
                for combatant in combat.combatants:
                    interface.add_combatant_visual(
                        combatant.id,
                        combatant.character.name,
                        combatant.character.max_hp,
                        combatant.current_hp,
                        is_player=True  # Could determine this based on character ownership
                    )
            
            # Store interface
            self.visual_interfaces[combat_id] = interface
            
            # Launch in separate thread
            def run_interface():
                interface.run()
                # Clean up when interface closes
                if combat_id in self.visual_interfaces:
                    del self.visual_interfaces[combat_id]
                if combat_id in self.interface_threads:
                    del self.interface_threads[combat_id]
            
            thread = threading.Thread(target=run_interface, daemon=True)
            thread.start()
            self.interface_threads[combat_id] = thread
            
            return True
            
        except Exception as e:
            print(f"Failed to launch visual interface: {e}")
            return False
    
    def close_visual_interface(self, combat_id: int) -> bool:
        """Close the visual interface for a combat."""
        if combat_id in self.visual_interfaces:
            interface = self.visual_interfaces[combat_id]
            interface.running = False
            return True
        return False
    
    def _save_spatial_state(self, combat_id: int, spatial_state: SpatialCombatState) -> None:
        """
        Save spatial combat state to database.
        
        Args:
            combat_id: Combat encounter ID
            spatial_state: Spatial state to save
        """
        from app import db
        
        # For now, we'll store the spatial state as JSON in a simple way
        # In a production system, you might want dedicated tables for spatial data
        
        state_data = {
            'grid': spatial_state.grid.to_dict(),
            'turn_order': spatial_state.turn_order,
            'current_turn_index': spatial_state.current_turn_index,
            'round_number': spatial_state.round_number
        }
        
        # Store in a file or database field (simplified for this implementation)
        # You could add a spatial_state field to the Combat model
        try:
            with open(f'/tmp/spatial_combat_{combat_id}.json', 'w') as f:
                json.dump(state_data, f)
        except Exception as e:
            print(f"Failed to save spatial state: {e}")
    
    def _load_spatial_state(self, combat_id: int) -> Optional[SpatialCombatState]:
        """Load spatial combat state from storage."""
        try:
            with open(f'/tmp/spatial_combat_{combat_id}.json', 'r') as f:
                state_data = json.load(f)
            
            grid = SpatialCombatGrid.from_dict(state_data['grid'])
            spatial_state = SpatialCombatState(
                combat_id=combat_id,
                grid=grid,
                turn_order=state_data['turn_order'],
                current_turn_index=state_data['current_turn_index'],
                round_number=state_data['round_number']
            )
            
            return spatial_state
            
        except Exception as e:
            print(f"Failed to load spatial state: {e}")
            return None
    
    def end_spatial_combat(self, combat_id: int) -> bool:
        """
        End a spatial combat encounter and clean up resources.
        
        Args:
            combat_id: Combat encounter ID
            
        Returns:
            True if cleanup successful
        """
        # Close visual interface if running
        self.close_visual_interface(combat_id)
        
        # Remove from active combats
        if combat_id in self.active_combats:
            del self.active_combats[combat_id]
        
        # Clean up saved state
        try:
            import os
            os.remove(f'/tmp/spatial_combat_{combat_id}.json')
        except:
            pass
        
        return True


# Flask API integration functions
def setup_spatial_combat_routes(app, spatial_manager: SpatialCombatManager):
    """
    Set up Flask routes for spatial combat API.
    
    Args:
        app: Flask application
        spatial_manager: Spatial combat manager instance
    """
    
    @app.route('/api/spatial_combat/<int:combat_id>/create', methods=['POST'])
    def create_spatial_combat_api(combat_id):
        """Create a new spatial combat encounter."""
        try:
            data = request.get_json() or {}
            width = data.get('width', 20)
            height = data.get('height', 15)
            terrain_setup = data.get('terrain_setup')
            
            spatial_state = spatial_manager.create_spatial_combat(
                combat_id, width, height, terrain_setup
            )
            
            return jsonify({
                'success': True,
                'combat_id': combat_id,
                'grid_data': spatial_manager.get_combat_grid_data(combat_id)
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/spatial_combat/<int:combat_id>/grid')
    def get_spatial_combat_grid(combat_id):
        """Get grid data for a spatial combat."""
        try:
            grid_data = spatial_manager.get_combat_grid_data(combat_id)
            if grid_data:
                return jsonify({'success': True, 'data': grid_data})
            else:
                return jsonify({'success': False, 'error': 'Combat not found'}), 404
                
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/spatial_combat/<int:combat_id>/move', methods=['POST'])
    def move_combatant_api(combat_id):
        """Move a combatant to a new position."""
        try:
            data = request.get_json()
            combatant_id = data.get('combatant_id')
            target_x = data.get('target_x')
            target_y = data.get('target_y')
            movement_speed = data.get('movement_speed', 30)
            
            if combatant_id is None or target_x is None or target_y is None:
                return jsonify({'success': False, 'error': 'Missing required parameters'}), 400
            
            success, message = spatial_manager.move_combatant(
                combat_id, combatant_id, target_x, target_y, movement_speed
            )
            
            return jsonify({'success': success, 'message': message})
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/spatial_combat/<int:combat_id>/valid_moves/<int:combatant_id>')
    def get_valid_moves_api(combat_id, combatant_id):
        """Get valid movement positions for a combatant."""
        try:
            movement_speed = request.args.get('movement_speed', 30, type=int)
            
            valid_moves = spatial_manager.get_valid_movements(
                combat_id, combatant_id, movement_speed
            )
            
            return jsonify({'success': True, 'valid_moves': valid_moves})
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/spatial_combat/<int:combat_id>/attack_range/<int:combatant_id>')
    def get_attack_range_api(combat_id, combatant_id):
        """Get attack range positions for a combatant."""
        try:
            weapon_range = request.args.get('weapon_range', 5, type=int)
            
            range_positions = spatial_manager.get_attack_range_positions(
                combat_id, combatant_id, weapon_range
            )
            
            return jsonify({'success': True, 'attack_range': range_positions})
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/spatial_combat/<int:combat_id>/attack_modifiers')
    def get_attack_modifiers_api(combat_id):
        """Get attack modifiers based on positioning."""
        try:
            attacker_id = request.args.get('attacker_id', type=int)
            target_id = request.args.get('target_id', type=int)
            
            if attacker_id is None or target_id is None:
                return jsonify({'success': False, 'error': 'Missing attacker_id or target_id'}), 400
            
            modifiers = spatial_manager.calculate_attack_modifiers(
                combat_id, attacker_id, target_id
            )
            
            return jsonify({'success': True, 'modifiers': modifiers})
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/spatial_combat/<int:combat_id>/visual', methods=['POST'])
    def launch_visual_interface_api(combat_id):
        """Launch pygame visual interface for combat."""
        try:
            success = spatial_manager.launch_visual_interface(combat_id)
            
            if success:
                return jsonify({'success': True, 'message': 'Visual interface launched'})
            else:
                return jsonify({'success': False, 'error': 'Failed to launch interface'}), 500
                
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/spatial_combat/<int:combat_id>/visual', methods=['DELETE'])
    def close_visual_interface_api(combat_id):
        """Close pygame visual interface for combat."""
        try:
            success = spatial_manager.close_visual_interface(combat_id)
            
            return jsonify({'success': success})
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500


# Prebuilt terrain templates for quick setup
TERRAIN_TEMPLATES = {
    'dungeon_room': {
        'name': 'Dungeon Room',
        'description': 'A typical dungeon room with walls and some cover',
        'features': [
            {
                'type': 'blocking',
                'description': 'Stone Wall',
                'positions': [
                    {'x': x, 'y': 0} for x in range(20)
                ] + [
                    {'x': x, 'y': 14} for x in range(20)
                ] + [
                    {'x': 0, 'y': y} for y in range(15)
                ] + [
                    {'x': 19, 'y': y} for y in range(15)
                ]
            },
            {
                'type': 'partial_cover',
                'description': 'Stone Pillar',
                'positions': [
                    {'x': 6, 'y': 5}, {'x': 13, 'y': 5},
                    {'x': 6, 'y': 9}, {'x': 13, 'y': 9}
                ]
            }
        ]
    },
    
    'forest_clearing': {
        'name': 'Forest Clearing',
        'description': 'An outdoor combat in a forest clearing',
        'features': [
            {
                'type': 'difficult',
                'description': 'Dense Undergrowth',
                'positions': [
                    {'x': x, 'y': y} 
                    for x in range(0, 5) for y in range(0, 15)
                ] + [
                    {'x': x, 'y': y}
                    for x in range(15, 20) for y in range(0, 15)
                ]
            },
            {
                'type': 'blocking',
                'description': 'Large Tree',
                'positions': [
                    {'x': 8, 'y': 3}, {'x': 11, 'y': 8}, {'x': 15, 'y': 12}
                ]
            },
            {
                'type': 'partial_cover',
                'description': 'Fallen Log',
                'positions': [
                    {'x': x, 'y': 7} for x in range(5, 10)
                ]
            }
        ]
    },
    
    'castle_courtyard': {
        'name': 'Castle Courtyard',
        'description': 'A castle courtyard with various defensive features',
        'features': [
            {
                'type': 'blocking',
                'description': 'Castle Wall',
                'positions': [
                    {'x': x, 'y': 0} for x in range(20)
                ] + [
                    {'x': 0, 'y': y} for y in range(8)
                ] + [
                    {'x': 19, 'y': y} for y in range(8)
                ]
            },
            {
                'type': 'elevated',
                'description': 'Raised Platform',
                'positions': [
                    {'x': x, 'y': y} 
                    for x in range(8, 12) for y in range(2, 5)
                ]
            },
            {
                'type': 'full_cover',
                'description': 'Guard Tower',
                'positions': [
                    {'x': 15, 'y': 2}, {'x': 16, 'y': 2},
                    {'x': 15, 'y': 3}, {'x': 16, 'y': 3}
                ]
            },
            {
                'type': 'water',
                'description': 'Moat',
                'positions': [
                    {'x': x, 'y': 12} for x in range(5, 15)
                ]
            }
        ]
    }
}