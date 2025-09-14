# spatial_combat.py

"""
Spatial Combat System for D&D 5e

This module implements a grid-based spatial combat system following D&D 5e rules.
It includes terrain types, movement mechanics, line of sight calculations,
cover mechanics, and a pygame-based visual interface.

Key Features:
- Grid-based positioning system
- D&D 5e movement rules (including difficult terrain)
- Line of sight and cover calculations
- Multiple terrain types (open, difficult, blocking, etc.)
- Visual combat grid using pygame
- Integration with existing combat system

Author: D&D World Generator
"""

import pygame
import math
import json
from enum import Enum
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
from abc import ABC, abstractmethod


class TerrainType(Enum):
    """
    Terrain types following D&D 5e rules.
    
    Each terrain type affects movement, line of sight, and cover mechanics
    according to D&D 5e guidelines.
    """
    OPEN = "open"                    # Normal movement, no cover
    DIFFICULT = "difficult"          # 2x movement cost, no cover
    BLOCKING = "blocking"            # Impassable, blocks line of sight
    PARTIAL_COVER = "partial_cover"  # Normal movement, provides partial cover (+2 AC)
    FULL_COVER = "full_cover"        # Normal movement, provides full cover (blocks attacks)
    WATER = "water"                  # Difficult terrain, special swimming rules
    PIT = "pit"                      # Impassable without special abilities
    ELEVATED = "elevated"            # Higher ground advantage
    

class CoverType(Enum):
    """Types of cover in D&D 5e."""
    NONE = "none"                    # No cover
    HALF = "half"                    # +2 bonus to AC and Dex saves
    THREE_QUARTERS = "three_quarters"  # +5 bonus to AC and Dex saves
    FULL = "full"                    # Target cannot be targeted directly


@dataclass
class GridPosition:
    """
    Represents a position on the combat grid.
    
    Uses standard D&D grid coordinates where each square represents 5 feet.
    """
    x: int
    y: int
    
    def __post_init__(self):
        """Ensure coordinates are valid."""
        if self.x < 0 or self.y < 0:
            raise ValueError("Grid coordinates must be non-negative")
    
    def distance_to(self, other: 'GridPosition') -> float:
        """
        Calculate distance to another position in feet.
        
        Uses D&D 5e diagonal movement rules where diagonal movement
        alternates between 5 and 10 feet.
        
        Args:
            other: Target position
            
        Returns:
            Distance in feet
        """
        dx = abs(self.x - other.x)
        dy = abs(self.y - other.y)
        
        # D&D 5e diagonal movement: first diagonal is 5ft, second is 10ft, etc.
        diagonal_moves = min(dx, dy)
        straight_moves = abs(dx - dy)
        
        # Alternating 5ft and 10ft for diagonals
        diagonal_distance = (diagonal_moves // 2) * 15 + (diagonal_moves % 2) * 5
        
        return diagonal_distance + (straight_moves * 5)
    
    def is_adjacent(self, other: 'GridPosition') -> bool:
        """Check if this position is adjacent to another (within 5 feet)."""
        return abs(self.x - other.x) <= 1 and abs(self.y - other.y) <= 1 and self != other
    
    def get_adjacent_positions(self) -> List['GridPosition']:
        """Get all adjacent positions (8 directions)."""
        adjacent = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                new_x, new_y = self.x + dx, self.y + dy
                if new_x >= 0 and new_y >= 0:
                    adjacent.append(GridPosition(new_x, new_y))
        return adjacent
    
    def __eq__(self, other):
        if not isinstance(other, GridPosition):
            return False
        return self.x == other.x and self.y == other.y
    
    def __hash__(self):
        return hash((self.x, self.y))
    
    def __str__(self):
        return f"({self.x}, {self.y})"


@dataclass
class TerrainTile:
    """
    Represents a single tile on the combat grid.
    
    Each tile has a terrain type that affects movement and combat mechanics.
    """
    terrain_type: TerrainType
    movement_cost: float = field(init=False)  # Movement cost multiplier
    blocks_line_of_sight: bool = field(init=False)
    provides_cover: CoverType = field(init=False)
    description: str = ""
    
    def __post_init__(self):
        """Initialize derived properties based on terrain type."""
        terrain_properties = {
            TerrainType.OPEN: (1.0, False, CoverType.NONE),
            TerrainType.DIFFICULT: (2.0, False, CoverType.NONE),
            TerrainType.BLOCKING: (float('inf'), True, CoverType.FULL),
            TerrainType.PARTIAL_COVER: (1.0, False, CoverType.HALF),
            TerrainType.FULL_COVER: (1.0, False, CoverType.FULL),
            TerrainType.WATER: (2.0, False, CoverType.NONE),
            TerrainType.PIT: (float('inf'), False, CoverType.NONE),
            TerrainType.ELEVATED: (1.0, False, CoverType.NONE),
        }
        
        self.movement_cost, self.blocks_line_of_sight, self.provides_cover = \
            terrain_properties[self.terrain_type]


class SpatialCombatGrid:
    """
    Main grid system for spatial combat.
    
    Manages the combat grid, terrain, and spatial relationships between
    combatants. Provides methods for movement validation, line of sight
    calculations, and cover determination.
    """
    
    def __init__(self, width: int, height: int):
        """
        Initialize combat grid.
        
        Args:
            width: Grid width in squares (each square = 5 feet)
            height: Grid height in squares
        """
        if width <= 0 or height <= 0:
            raise ValueError("Grid dimensions must be positive")
            
        self.width = width
        self.height = height
        
        # Initialize grid with open terrain
        self.grid: List[List[TerrainTile]] = [
            [TerrainTile(TerrainType.OPEN) for _ in range(width)]
            for _ in range(height)
        ]
        
        # Track combatant positions
        self.combatant_positions: Dict[int, GridPosition] = {}
        
        # Cache for expensive calculations
        self._line_of_sight_cache: Dict[Tuple[GridPosition, GridPosition], bool] = {}
        self._cover_cache: Dict[Tuple[GridPosition, GridPosition], CoverType] = {}
    
    def is_valid_position(self, position: GridPosition) -> bool:
        """Check if a position is within grid bounds."""
        return (0 <= position.x < self.width and 
                0 <= position.y < self.height)
    
    def get_terrain(self, position: GridPosition) -> TerrainTile:
        """Get terrain at a specific position."""
        if not self.is_valid_position(position):
            raise ValueError(f"Position {position} is outside grid bounds")
        return self.grid[position.y][position.x]
    
    def set_terrain(self, position: GridPosition, terrain_type: TerrainType, 
                   description: str = "") -> None:
        """
        Set terrain type at a specific position.
        
        Args:
            position: Grid position to modify
            terrain_type: New terrain type
            description: Optional description of the terrain feature
        """
        if not self.is_valid_position(position):
            raise ValueError(f"Position {position} is outside grid bounds")
        
        self.grid[position.y][position.x] = TerrainTile(terrain_type, description=description)
        
        # Clear relevant caches
        self._clear_position_caches(position)
    
    def _clear_position_caches(self, position: GridPosition) -> None:
        """Clear cached calculations involving a specific position."""
        keys_to_remove = []
        
        for key in self._line_of_sight_cache:
            if position in key:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._line_of_sight_cache[key]
            
        # Clear cover cache similarly
        keys_to_remove = []
        for key in self._cover_cache:
            if position in key:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._cover_cache[key]
            
        # Also clear cache for any line that might pass through this position
        # This is more comprehensive but less efficient
        self._line_of_sight_cache.clear()
        self._cover_cache.clear()
    
    def place_combatant(self, combatant_id: int, position: GridPosition) -> bool:
        """
        Place a combatant at a specific position.
        
        Args:
            combatant_id: Unique identifier for the combatant
            position: Desired position
            
        Returns:
            True if placement successful, False otherwise
        """
        if not self.is_valid_position(position):
            return False
        
        # Check if position is passable
        terrain = self.get_terrain(position)
        if terrain.movement_cost == float('inf'):
            return False
        
        # Check if position is already occupied
        if self.is_position_occupied(position, exclude_combatant=combatant_id):
            return False
        
        self.combatant_positions[combatant_id] = position
        return True
    
    def move_combatant(self, combatant_id: int, new_position: GridPosition) -> bool:
        """
        Move a combatant to a new position.
        
        Args:
            combatant_id: Combatant to move
            new_position: Target position
            
        Returns:
            True if move successful, False otherwise
        """
        if combatant_id not in self.combatant_positions:
            return False
        
        return self.place_combatant(combatant_id, new_position)
    
    def remove_combatant(self, combatant_id: int) -> bool:
        """Remove a combatant from the grid."""
        if combatant_id in self.combatant_positions:
            del self.combatant_positions[combatant_id]
            return True
        return False
    
    def get_combatant_position(self, combatant_id: int) -> Optional[GridPosition]:
        """Get the current position of a combatant."""
        return self.combatant_positions.get(combatant_id)
    
    def is_position_occupied(self, position: GridPosition, 
                           exclude_combatant: Optional[int] = None) -> bool:
        """
        Check if a position is occupied by a combatant.
        
        Args:
            position: Position to check
            exclude_combatant: Combatant ID to exclude from check
            
        Returns:
            True if position is occupied
        """
        for combatant_id, pos in self.combatant_positions.items():
            if combatant_id != exclude_combatant and pos == position:
                return True
        return False
    
    def get_combatants_at_position(self, position: GridPosition) -> List[int]:
        """Get all combatants at a specific position."""
        combatants = []
        for combatant_id, pos in self.combatant_positions.items():
            if pos == position:
                combatants.append(combatant_id)
        return combatants
    
    def calculate_movement_cost(self, from_pos: GridPosition, 
                              to_pos: GridPosition) -> float:
        """
        Calculate movement cost between two positions.
        
        Takes into account terrain types and diagonal movement rules.
        
        Args:
            from_pos: Starting position
            to_pos: Target position
            
        Returns:
            Movement cost in feet, or infinity if path is blocked
        """
        if not self.is_valid_position(to_pos):
            return float('inf')
        
        terrain = self.get_terrain(to_pos)
        if terrain.movement_cost == float('inf'):
            return float('inf')
        
        base_distance = from_pos.distance_to(to_pos)
        return base_distance * terrain.movement_cost
    
    def has_line_of_sight(self, from_pos: GridPosition, 
                         to_pos: GridPosition) -> bool:
        """
        Determine if there's a clear line of sight between two positions.
        
        Uses Bresenham's line algorithm to check each grid square along the path.
        Includes caching for performance optimization.
        
        Args:
            from_pos: Starting position
            to_pos: Target position
            
        Returns:
            True if line of sight exists
        """
        if from_pos == to_pos:
            return True
        
        # Check cache first
        cache_key = (from_pos, to_pos)
        if cache_key in self._line_of_sight_cache:
            return self._line_of_sight_cache[cache_key]
        
        # Use Bresenham's line algorithm
        line_points = self._bresenham_line(from_pos, to_pos)
        
        # Check each point along the line (excluding start and end)
        for point in line_points[1:-1]:  # Exclude start and end positions
            if not self.is_valid_position(point):
                continue
            
            terrain = self.get_terrain(point)
            if terrain.blocks_line_of_sight:
                self._line_of_sight_cache[cache_key] = False
                return False
        
        self._line_of_sight_cache[cache_key] = True
        return True
    
    def _bresenham_line(self, start: GridPosition, end: GridPosition) -> List[GridPosition]:
        """
        Generate points along a line using Bresenham's algorithm.
        
        This is used for line of sight calculations and ensures we check
        every grid square that the line passes through.
        """
        points = []
        x0, y0 = start.x, start.y
        x1, y1 = end.x, end.y
        
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        x, y = x0, y0
        
        while True:
            points.append(GridPosition(x, y))
            
            if x == x1 and y == y1:
                break
                
            e2 = 2 * err
            
            if e2 > -dy:
                err -= dy
                x += sx
                
            if e2 < dx:
                err += dx
                y += sy
        
        return points
    
    def get_cover_type(self, attacker_pos: GridPosition, 
                      target_pos: GridPosition) -> CoverType:
        """
        Determine cover type between attacker and target.
        
        Follows D&D 5e cover rules:
        - Half cover: +2 AC and Dex saves
        - Three-quarters cover: +5 AC and Dex saves  
        - Full cover: Cannot be targeted
        
        Args:
            attacker_pos: Attacker's position
            target_pos: Target's position
            
        Returns:
            Type of cover the target has
        """
        if attacker_pos == target_pos:
            return CoverType.NONE
        
        # Check cache first
        cache_key = (attacker_pos, target_pos)
        if cache_key in self._cover_cache:
            return self._cover_cache[cache_key]
        
        # If no line of sight, it's full cover
        if not self.has_line_of_sight(attacker_pos, target_pos):
            self._cover_cache[cache_key] = CoverType.FULL
            return CoverType.FULL
        
        # Check terrain along the line for partial cover
        line_points = self._bresenham_line(attacker_pos, target_pos)
        cover_points = 0
        
        for point in line_points[1:-1]:  # Exclude start and end
            if not self.is_valid_position(point):
                continue
                
            terrain = self.get_terrain(point)
            if terrain.provides_cover in [CoverType.HALF, CoverType.THREE_QUARTERS]:
                cover_points += 1
            elif terrain.provides_cover == CoverType.FULL:
                self._cover_cache[cache_key] = CoverType.FULL
                return CoverType.FULL
        
        # Determine cover based on number of intervening cover points
        if cover_points == 0:
            cover = CoverType.NONE
        elif cover_points <= 2:
            cover = CoverType.HALF
        else:
            cover = CoverType.THREE_QUARTERS
        
        self._cover_cache[cache_key] = cover
        return cover
    
    def get_valid_moves(self, combatant_id: int, 
                       movement_speed: int) -> List[GridPosition]:
        """
        Get all valid positions a combatant can move to.
        
        Args:
            combatant_id: Combatant to check movement for
            movement_speed: Movement speed in feet
            
        Returns:
            List of valid positions within movement range
        """
        current_pos = self.get_combatant_position(combatant_id)
        if not current_pos:
            return []
        
        valid_positions = []
        
        # Check all positions within reasonable range
        max_squares = (movement_speed // 5) + 2  # Extra buffer for diagonal movement
        
        for x in range(max(0, current_pos.x - max_squares), 
                      min(self.width, current_pos.x + max_squares + 1)):
            for y in range(max(0, current_pos.y - max_squares),
                          min(self.height, current_pos.y + max_squares + 1)):
                target_pos = GridPosition(x, y)
                
                # Skip current position
                if target_pos == current_pos:
                    continue
                
                # Check if position is reachable within movement
                cost = self.calculate_movement_cost(current_pos, target_pos)
                if cost <= movement_speed and not self.is_position_occupied(target_pos, combatant_id):
                    valid_positions.append(target_pos)
        
        return valid_positions
    
    def get_attack_range_positions(self, attacker_id: int, 
                                 weapon_range: int) -> List[GridPosition]:
        """
        Get all positions within attack range of a combatant.
        
        Args:
            attacker_id: Attacking combatant
            weapon_range: Weapon range in feet
            
        Returns:
            List of positions within attack range
        """
        attacker_pos = self.get_combatant_position(attacker_id)
        if not attacker_pos:
            return []
        
        positions_in_range = []
        
        # Check all positions within weapon range
        max_squares = (weapon_range // 5) + 1
        
        for x in range(max(0, attacker_pos.x - max_squares),
                      min(self.width, attacker_pos.x + max_squares + 1)):
            for y in range(max(0, attacker_pos.y - max_squares),
                          min(self.height, attacker_pos.y + max_squares + 1)):
                target_pos = GridPosition(x, y)
                
                # Skip attacker's position
                if target_pos == attacker_pos:
                    continue
                
                distance = attacker_pos.distance_to(target_pos)
                if distance <= weapon_range:
                    positions_in_range.append(target_pos)
        
        return positions_in_range
    
    def to_dict(self) -> Dict:
        """Serialize grid to dictionary for saving/loading."""
        return {
            'width': self.width,
            'height': self.height,
            'terrain': [
                [{'type': tile.terrain_type.value, 'description': tile.description}
                 for tile in row]
                for row in self.grid
            ],
            'combatant_positions': {
                str(combatant_id): {'x': pos.x, 'y': pos.y}
                for combatant_id, pos in self.combatant_positions.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SpatialCombatGrid':
        """Load grid from dictionary."""
        grid = cls(data['width'], data['height'])
        
        # Load terrain
        for y, row in enumerate(data['terrain']):
            for x, tile_data in enumerate(row):
                terrain_type = TerrainType(tile_data['type'])
                description = tile_data.get('description', '')
                grid.set_terrain(GridPosition(x, y), terrain_type, description)
        
        # Load combatant positions
        for combatant_id_str, pos_data in data['combatant_positions'].items():
            combatant_id = int(combatant_id_str)
            position = GridPosition(pos_data['x'], pos_data['y'])
            grid.combatant_positions[combatant_id] = position
        
        return grid


class MovementValidator:
    """
    Validates movement according to D&D 5e rules.
    
    This class encapsulates movement validation logic including:
    - Speed limitations
    - Terrain cost calculations
    - Opportunity attack triggers
    - Special movement types (flying, swimming, etc.)
    """
    
    @staticmethod
    def can_move_to(grid: SpatialCombatGrid, combatant_id: int,
                   target_position: GridPosition, movement_speed: int,
                   ignore_opportunity_attacks: bool = False) -> Tuple[bool, str]:
        """
        Validate if a combatant can move to a target position.
        
        Args:
            grid: Combat grid
            combatant_id: Combatant attempting to move
            target_position: Desired destination
            movement_speed: Available movement in feet
            ignore_opportunity_attacks: Whether to ignore opportunity attack considerations
            
        Returns:
            Tuple of (can_move, reason_if_cannot)
        """
        current_pos = grid.get_combatant_position(combatant_id)
        if not current_pos:
            return False, "Combatant not found on grid"
        
        if not grid.is_valid_position(target_position):
            return False, "Target position is outside grid bounds"
        
        if grid.is_position_occupied(target_position, exclude_combatant=combatant_id):
            return False, "Target position is occupied"
        
        movement_cost = grid.calculate_movement_cost(current_pos, target_position)
        if movement_cost == float('inf'):
            return False, "Target position is impassable"
        
        if movement_cost > movement_speed:
            return False, f"Insufficient movement (need {movement_cost}ft, have {movement_speed}ft)"
        
        # Check for opportunity attacks if not ignoring them
        if not ignore_opportunity_attacks:
            opportunity_attackers = MovementValidator._get_opportunity_attackers(
                grid, combatant_id, current_pos, target_position
            )
            if opportunity_attackers:
                attacker_names = ', '.join(map(str, opportunity_attackers))
                return False, f"Movement would provoke opportunity attacks from: {attacker_names}"
        
        return True, ""
    
    @staticmethod
    def _get_opportunity_attackers(grid: SpatialCombatGrid, moving_combatant: int,
                                 from_pos: GridPosition, 
                                 to_pos: GridPosition) -> List[int]:
        """
        Get list of combatants that would get opportunity attacks.
        
        In D&D 5e, you provoke opportunity attacks when you move out of
        an enemy's reach (adjacent squares for most weapons).
        """
        opportunity_attackers = []
        
        # Get all adjacent positions to the starting position
        adjacent_to_start = from_pos.get_adjacent_positions()
        
        for adj_pos in adjacent_to_start:
            combatants_at_pos = grid.get_combatants_at_position(adj_pos)
            for combatant_id in combatants_at_pos:
                if combatant_id != moving_combatant:
                    # Check if the destination is also adjacent (no opportunity attack)
                    if not adj_pos.is_adjacent(to_pos):
                        opportunity_attackers.append(combatant_id)
        
        return opportunity_attackers


@dataclass 
class SpatialCombatState:
    """
    Manages the complete state of a spatial combat encounter.
    
    This class serves as the main interface between the spatial combat system
    and the existing combat mechanics, providing a bridge between grid-based
    positioning and traditional turn-based combat.
    """
    combat_id: int
    grid: SpatialCombatGrid
    turn_order: List[int] = field(default_factory=list)
    current_turn_index: int = 0
    round_number: int = 1
    
    def get_current_combatant(self) -> Optional[int]:
        """Get the combatant whose turn it currently is."""
        if 0 <= self.current_turn_index < len(self.turn_order):
            return self.turn_order[self.current_turn_index]
        return None
    
    def next_turn(self) -> None:
        """Advance to the next combatant's turn."""
        if self.turn_order:
            self.current_turn_index = (self.current_turn_index + 1) % len(self.turn_order)
            if self.current_turn_index == 0:
                self.round_number += 1
    
    def add_combatant(self, combatant_id: int, position: GridPosition, 
                     initiative: int) -> bool:
        """Add a combatant to the spatial combat."""
        if self.grid.place_combatant(combatant_id, position):
            # Insert into turn order based on initiative
            inserted = False
            for i, existing_id in enumerate(self.turn_order):
                # Higher initiative goes first (we'd need to get initiative from database)
                # For now, just append to end
                pass
            
            if not inserted:
                self.turn_order.append(combatant_id)
            
            return True
        return False
    
    def remove_combatant(self, combatant_id: int) -> bool:
        """Remove a combatant from spatial combat."""
        removed_from_grid = self.grid.remove_combatant(combatant_id)
        
        if combatant_id in self.turn_order:
            old_index = self.turn_order.index(combatant_id)
            self.turn_order.remove(combatant_id)
            
            # Adjust current turn index if needed
            if old_index <= self.current_turn_index and self.current_turn_index > 0:
                self.current_turn_index -= 1
        
        return removed_from_grid


# Integration with existing combat system will be handled in the next file
# This provides the core spatial mechanics that can be plugged into the existing system