# spatial_combat.py

"""
Spatial combat system for D&D combat encounters.

This module implements grid-based positional combat with movement,
range checking, and spatial awareness for tactical gameplay.
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
from enum import Enum
import math

class TerrainType(Enum):
    """Types of terrain that can affect movement and combat."""
    OPEN = "open"
    DIFFICULT = "difficult"  # Costs 2 movement to enter
    OBSTACLE = "obstacle"    # Cannot be entered
    COVER = "cover"         # Provides cover bonuses
    WATER = "water"         # May require swim checks
    ELEVATED = "elevated"   # Height advantage

@dataclass
class Position:
    """Represents a position on the combat grid."""
    x: int
    y: int
    z: int = 0  # Height for 3D combat
    
    def distance_to(self, other: 'Position') -> float:
        """Calculate distance to another position in feet (5ft squares)."""
        dx = abs(self.x - other.x)
        dy = abs(self.y - other.y)
        dz = abs(self.z - other.z)
        
        # D&D 5e uses 5-foot squares, and diagonal movement
        # Use Euclidean distance but convert to 5-foot increments
        distance_squares = math.sqrt(dx**2 + dy**2 + dz**2)
        return distance_squares * 5  # Convert to feet
    
    def is_adjacent(self, other: 'Position') -> bool:
        """Check if another position is adjacent (within 5 feet)."""
        return self.distance_to(other) <= 5
    
    def get_line_to(self, other: 'Position') -> List['Position']:
        """Get all positions in a straight line to another position."""
        positions = []
        
        # Bresenham's line algorithm adapted for grid
        x0, y0 = self.x, self.y
        x1, y1 = other.x, other.y
        
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        
        x, y = x0, y0
        
        x_inc = 1 if x1 > x0 else -1
        y_inc = 1 if y1 > y0 else -1
        
        error = dx - dy
        
        while True:
            positions.append(Position(x, y, self.z))
            
            if x == x1 and y == y1:
                break
                
            e2 = 2 * error
            
            if e2 > -dy:
                error -= dy
                x += x_inc
                
            if e2 < dx:
                error += dx
                y += y_inc
        
        return positions

@dataclass
class MapTile:
    """Represents a single tile on the combat map."""
    position: Position
    terrain: TerrainType = TerrainType.OPEN
    cover_bonus: int = 0  # AC bonus for cover (+2 or +5)
    description: str = ""

class CombatMap:
    """Manages the spatial grid for combat encounters."""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.tiles: Dict[Tuple[int, int], MapTile] = {}
        self.combatant_positions: Dict[int, Position] = {}  # combatant_id -> position
        
        # Initialize with open terrain
        for x in range(width):
            for y in range(height):
                pos = Position(x, y)
                self.tiles[(x, y)] = MapTile(pos, TerrainType.OPEN)
    
    def get_tile(self, position: Position) -> Optional[MapTile]:
        """Get the tile at a specific position."""
        return self.tiles.get((position.x, position.y))
    
    def set_terrain(self, position: Position, terrain: TerrainType, cover_bonus: int = 0, description: str = ""):
        """Set terrain type for a specific position."""
        if (position.x, position.y) in self.tiles:
            tile = self.tiles[(position.x, position.y)]
            tile.terrain = terrain
            tile.cover_bonus = cover_bonus
            tile.description = description
    
    def is_valid_position(self, position: Position) -> bool:
        """Check if a position is within map bounds and not an obstacle."""
        if position.x < 0 or position.x >= self.width or position.y < 0 or position.y >= self.height:
            return False
        
        tile = self.get_tile(position)
        return tile and tile.terrain != TerrainType.OBSTACLE
    
    def is_occupied(self, position: Position) -> bool:
        """Check if a position is occupied by a combatant."""
        return position in self.combatant_positions.values()
    
    def can_move_to(self, position: Position) -> bool:
        """Check if a combatant can move to a position."""
        return self.is_valid_position(position) and not self.is_occupied(position)
    
    def place_combatant(self, combatant_id: int, position: Position) -> bool:
        """Place a combatant at a specific position."""
        if self.can_move_to(position):
            # Remove from old position if exists
            if combatant_id in self.combatant_positions:
                del self.combatant_positions[combatant_id]
            
            self.combatant_positions[combatant_id] = position
            return True
        return False
    
    def move_combatant(self, combatant_id: int, new_position: Position) -> bool:
        """Move a combatant to a new position."""
        if combatant_id not in self.combatant_positions:
            return False
        
        if self.can_move_to(new_position):
            self.combatant_positions[combatant_id] = new_position
            return True
        return False
    
    def get_combatant_position(self, combatant_id: int) -> Optional[Position]:
        """Get the current position of a combatant."""
        return self.combatant_positions.get(combatant_id)
    
    def calculate_movement_cost(self, from_pos: Position, to_pos: Position) -> int:
        """Calculate movement cost between two positions."""
        if not self.is_valid_position(to_pos):
            return float('inf')
        
        tile = self.get_tile(to_pos)
        base_cost = 5  # 5 feet per square
        
        if tile.terrain == TerrainType.DIFFICULT:
            base_cost *= 2
        elif tile.terrain == TerrainType.WATER:
            base_cost *= 2  # Swimming is difficult terrain
        
        # Diagonal movement (simplified - treat as same cost)
        return base_cost
    
    def find_path(self, start: Position, end: Position, max_distance: int) -> List[Position]:
        """Find the shortest path between two positions within movement range."""
        if not self.is_valid_position(start) or not self.can_move_to(end):
            return []
        
        # Simple breadth-first search for pathfinding
        from collections import deque
        
        queue = deque([(start, [start], 0)])  # (position, path, cost)
        visited = set()
        
        while queue:
            current_pos, path, total_cost = queue.popleft()
            
            if (current_pos.x, current_pos.y) in visited:
                continue
            
            visited.add((current_pos.x, current_pos.y))
            
            if current_pos.x == end.x and current_pos.y == end.y:
                return path
            
            # Check adjacent squares
            for dx, dy in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
                new_pos = Position(current_pos.x + dx, current_pos.y + dy, current_pos.z)
                
                if (new_pos.x, new_pos.y) not in visited:
                    move_cost = self.calculate_movement_cost(current_pos, new_pos)
                    new_total_cost = total_cost + move_cost
                    
                    if new_total_cost <= max_distance and (self.can_move_to(new_pos) or (new_pos.x == end.x and new_pos.y == end.y)):
                        new_path = path + [new_pos]
                        queue.append((new_pos, new_path, new_total_cost))
        
        return []  # No path found
    
    def has_line_of_sight(self, start: Position, end: Position) -> bool:
        """Check if there's a clear line of sight between two positions."""
        if start == end:
            return True
        
        # Get all positions along the line
        line_positions = start.get_line_to(end)
        
        # Check each position along the line for obstacles
        for pos in line_positions[1:-1]:  # Skip start and end positions
            tile = self.get_tile(pos)
            if tile and tile.terrain == TerrainType.OBSTACLE:
                return False
        
        return True
    
    def get_cover_bonus(self, attacker_pos: Position, target_pos: Position) -> int:
        """Calculate cover bonus for a target based on terrain."""
        # Check the target's tile for cover
        target_tile = self.get_tile(target_pos)
        if target_tile and target_tile.cover_bonus > 0:
            return target_tile.cover_bonus
        
        # Check for cover from intervening terrain
        line_positions = attacker_pos.get_line_to(target_pos)
        
        for pos in line_positions[1:-1]:  # Skip start and end
            tile = self.get_tile(pos)
            if tile and tile.terrain == TerrainType.COVER:
                return 2  # Half cover
        
        return 0
    
    def get_positions_within_range(self, center: Position, range_feet: int) -> List[Position]:
        """Get all valid positions within a certain range."""
        positions = []
        range_squares = range_feet // 5
        
        for x in range(max(0, center.x - range_squares), min(self.width, center.x + range_squares + 1)):
            for y in range(max(0, center.y - range_squares), min(self.height, center.y + range_squares + 1)):
                pos = Position(x, y, center.z)
                if center.distance_to(pos) <= range_feet and self.is_valid_position(pos):
                    positions.append(pos)
        
        return positions

class SpatialCombatEngine:
    """Extended combat engine with spatial awareness."""
    
    def __init__(self, combat_map: CombatMap):
        self.map = combat_map
    
    def can_attack_target(self, attacker_id: int, target_id: int, weapon_range: int = 5) -> Tuple[bool, str]:
        """Check if an attacker can target a specific combatant."""
        attacker_pos = self.map.get_combatant_position(attacker_id)
        target_pos = self.map.get_combatant_position(target_id)
        
        if not attacker_pos or not target_pos:
            return False, "Combatant position not found"
        
        distance = attacker_pos.distance_to(target_pos)
        
        if distance > weapon_range:
            return False, f"Target is {distance}ft away, weapon range is {weapon_range}ft"
        
        if weapon_range > 5 and not self.map.has_line_of_sight(attacker_pos, target_pos):
            return False, "No line of sight to target"
        
        return True, "Target is in range"
    
    def move_combatant(self, combatant_id: int, target_position: Position, movement_speed: int) -> Tuple[bool, str, List[Position]]:
        """Move a combatant to a target position using pathfinding."""
        current_pos = self.map.get_combatant_position(combatant_id)
        
        if not current_pos:
            return False, "Combatant position not found", []
        
        # Find path to target
        path = self.map.find_path(current_pos, target_position, movement_speed)
        
        if not path:
            return False, "No valid path to target position", []
        
        if len(path) > 1:  # More than just starting position
            # Calculate total movement cost
            total_cost = 0
            for i in range(len(path) - 1):
                total_cost += self.map.calculate_movement_cost(path[i], path[i + 1])
            
            if total_cost > movement_speed:
                # Find how far we can actually move
                partial_path = [path[0]]
                current_cost = 0
                
                for i in range(len(path) - 1):
                    step_cost = self.map.calculate_movement_cost(path[i], path[i + 1])
                    if current_cost + step_cost <= movement_speed:
                        partial_path.append(path[i + 1])
                        current_cost += step_cost
                    else:
                        break
                
                if len(partial_path) > 1:
                    final_pos = partial_path[-1]
                    self.map.move_combatant(combatant_id, final_pos)
                    return True, f"Moved {current_cost}ft (partial movement)", partial_path
                else:
                    return False, "Not enough movement to reach any closer position", []
            else:
                # Can reach target
                self.map.move_combatant(combatant_id, target_position)
                return True, f"Moved {total_cost}ft to target", path
        
        return False, "Already at target position", [current_pos]
    
    def get_attack_modifiers(self, attacker_id: int, target_id: int) -> Dict[str, int]:
        """Get attack modifiers based on positioning."""
        modifiers = {}
        
        attacker_pos = self.map.get_combatant_position(attacker_id)
        target_pos = self.map.get_combatant_position(target_id)
        
        if attacker_pos and target_pos:
            # Cover bonus to AC
            cover_bonus = self.map.get_cover_bonus(attacker_pos, target_pos)
            if cover_bonus > 0:
                modifiers['cover_ac_bonus'] = cover_bonus
            
            # Height advantage (if implemented)
            if attacker_pos.z > target_pos.z:
                modifiers['height_advantage'] = 1  # Small bonus for being elevated
        
        return modifiers

def create_default_combat_map(width: int = 20, height: int = 20) -> CombatMap:
    """Create a default combat map with some terrain features."""
    combat_map = CombatMap(width, height)
    
    # Add some sample terrain
    # Add walls around the edges
    for x in range(width):
        combat_map.set_terrain(Position(x, 0), TerrainType.OBSTACLE, description="Wall")
        combat_map.set_terrain(Position(x, height-1), TerrainType.OBSTACLE, description="Wall")
    
    for y in range(height):
        combat_map.set_terrain(Position(0, y), TerrainType.OBSTACLE, description="Wall")
        combat_map.set_terrain(Position(width-1, y), TerrainType.OBSTACLE, description="Wall")
    
    # Add some cover in the middle
    mid_x, mid_y = width // 2, height // 2
    combat_map.set_terrain(Position(mid_x, mid_y), TerrainType.COVER, cover_bonus=2, description="Pillar")
    combat_map.set_terrain(Position(mid_x-3, mid_y-2), TerrainType.COVER, cover_bonus=2, description="Rock")
    combat_map.set_terrain(Position(mid_x+3, mid_y+2), TerrainType.COVER, cover_bonus=2, description="Tree")
    
    # Add some difficult terrain
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx != 0 or dy != 0:  # Don't overwrite the pillar
                pos = Position(mid_x + dx + 5, mid_y + dy + 5)
                if combat_map.is_valid_position(pos):
                    combat_map.set_terrain(pos, TerrainType.DIFFICULT, description="Rubble")
    
    return combat_map