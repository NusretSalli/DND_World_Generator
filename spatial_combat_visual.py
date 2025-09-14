# spatial_combat_visual.py

"""
Pygame Visual Interface for Spatial Combat System

This module provides a pygame-based visual interface for the spatial combat grid.
It handles rendering the grid, terrain, combatants, and interactive elements
like movement previews and attack range indicators.

Key Features:
- Real-time grid rendering with terrain visualization
- Combatant position display with health indicators
- Interactive movement and attack range visualization
- Click-to-move and click-to-attack interface
- Zoom and pan functionality for large grids
- Visual feedback for cover and line of sight

Author: D&D World Generator
"""

import pygame
import math
import os
import sys
from typing import Dict, List, Tuple, Optional, Set
from enum import Enum
from dataclasses import dataclass

from spatial_combat import (
    SpatialCombatGrid, GridPosition, TerrainType, CoverType,
    SpatialCombatState, MovementValidator
)


# Color constants for visual elements
class Colors:
    """Color palette for the combat grid visualization."""
    
    # Terrain colors
    OPEN = (245, 245, 220)          # Beige
    DIFFICULT = (139, 119, 101)     # Saddle brown  
    BLOCKING = (105, 105, 105)      # Dim gray
    PARTIAL_COVER = (154, 205, 50)  # Yellow green
    FULL_COVER = (34, 139, 34)      # Forest green
    WATER = (100, 149, 237)         # Cornflower blue
    PIT = (25, 25, 25)              # Very dark gray
    ELEVATED = (210, 180, 140)      # Tan
    
    # Grid and UI colors
    GRID_LINE = (200, 200, 200)     # Light gray
    GRID_LINE_MAJOR = (150, 150, 150)  # Darker gray for every 5th line
    BACKGROUND = (240, 240, 240)    # Very light gray
    
    # Combatant colors
    PLAYER = (0, 100, 200)          # Blue
    ENEMY = (200, 50, 50)           # Red
    ALLY = (50, 200, 50)            # Green
    NEUTRAL = (150, 150, 150)       # Gray
    
    # Action colors
    MOVEMENT_RANGE = (100, 200, 100, 80)    # Semi-transparent green
    ATTACK_RANGE = (200, 100, 100, 80)      # Semi-transparent red
    SELECTED = (255, 255, 0, 120)           # Semi-transparent yellow
    PATH_PREVIEW = (100, 100, 200, 150)     # Semi-transparent blue
    
    # Status colors
    COVER_HALF = (255, 165, 0, 100)         # Semi-transparent orange
    COVER_THREE_QUARTERS = (255, 140, 0, 120)  # Semi-transparent dark orange
    COVER_FULL = (255, 0, 0, 150)          # Semi-transparent red
    
    # Health bar colors
    HEALTH_HIGH = (0, 255, 0)       # Green
    HEALTH_MID = (255, 255, 0)      # Yellow
    HEALTH_LOW = (255, 0, 0)        # Red
    HEALTH_BACKGROUND = (100, 100, 100)  # Dark gray


@dataclass
class CombatantVisual:
    """Visual representation data for a combatant."""
    combatant_id: int
    name: str
    color: Tuple[int, int, int]
    max_hp: int
    current_hp: int
    size: int = 1  # Size in grid squares (1 = Medium, 2 = Large, etc.)
    is_player: bool = True


class GridRenderer:
    """
    Handles rendering of the combat grid and all visual elements.
    
    This class manages the pygame surface and provides methods for drawing
    the grid, terrain, combatants, and UI elements with proper scaling
    and positioning.
    """
    
    def __init__(self, screen_width: int = 1200, screen_height: int = 800):
        """
        Initialize the grid renderer.
        
        Args:
            screen_width: Width of the pygame window
            screen_height: Height of the pygame window
        """
        pygame.init()
        
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("D&D Spatial Combat Grid")
        
        # Grid display settings
        self.cell_size = 40  # Pixels per grid square
        self.min_cell_size = 20
        self.max_cell_size = 80
        
        # Camera settings for panning and zooming
        self.camera_x = 0
        self.camera_y = 0
        self.zoom = 1.0
        self.min_zoom = 0.5
        self.max_zoom = 3.0
        
        # Fonts for text rendering
        self.font_small = pygame.font.Font(None, 16)
        self.font_medium = pygame.font.Font(None, 24)
        self.font_large = pygame.font.Font(None, 32)
        
        # Terrain color mapping
        self.terrain_colors = {
            TerrainType.OPEN: Colors.OPEN,
            TerrainType.DIFFICULT: Colors.DIFFICULT,
            TerrainType.BLOCKING: Colors.BLOCKING,
            TerrainType.PARTIAL_COVER: Colors.PARTIAL_COVER,
            TerrainType.FULL_COVER: Colors.FULL_COVER,
            TerrainType.WATER: Colors.WATER,
            TerrainType.PIT: Colors.PIT,
            TerrainType.ELEVATED: Colors.ELEVATED,
        }
        
        # Track visual state
        self.selected_combatant: Optional[int] = None
        self.show_movement_range: bool = False
        self.show_attack_range: bool = False
        self.movement_path: List[GridPosition] = []
        
        # Performance optimization
        self.grid_surface: Optional[pygame.Surface] = None
        self.grid_surface_dirty = True
    
    def world_to_screen(self, grid_pos: GridPosition) -> Tuple[int, int]:
        """
        Convert grid coordinates to screen pixel coordinates.
        
        Args:
            grid_pos: Position on the grid
            
        Returns:
            Tuple of (screen_x, screen_y) pixel coordinates
        """
        scaled_cell_size = self.cell_size * self.zoom
        screen_x = (grid_pos.x * scaled_cell_size) - self.camera_x
        screen_y = (grid_pos.y * scaled_cell_size) - self.camera_y
        return int(screen_x), int(screen_y)
    
    def screen_to_world(self, screen_x: int, screen_y: int) -> GridPosition:
        """
        Convert screen pixel coordinates to grid coordinates.
        
        Args:
            screen_x: X pixel coordinate
            screen_y: Y pixel coordinate
            
        Returns:
            Grid position (may be outside valid grid bounds)
        """
        scaled_cell_size = self.cell_size * self.zoom
        grid_x = int((screen_x + self.camera_x) // scaled_cell_size)
        grid_y = int((screen_y + self.camera_y) // scaled_cell_size)
        return GridPosition(grid_x, grid_y)
    
    def zoom_at_point(self, zoom_delta: float, screen_x: int, screen_y: int) -> None:
        """
        Zoom in/out centered on a specific screen point.
        
        Args:
            zoom_delta: Amount to change zoom (positive = zoom in)
            screen_x: X coordinate of zoom center
            screen_y: Y coordinate of zoom center
        """
        old_zoom = self.zoom
        self.zoom = max(self.min_zoom, min(self.max_zoom, self.zoom + zoom_delta))
        
        if self.zoom != old_zoom:
            # Adjust camera to keep zoom point stationary
            zoom_ratio = self.zoom / old_zoom
            self.camera_x = screen_x + (self.camera_x - screen_x) * zoom_ratio
            self.camera_y = screen_y + (self.camera_y - screen_y) * zoom_ratio
            self.grid_surface_dirty = True
    
    def pan_camera(self, dx: int, dy: int) -> None:
        """
        Pan the camera by the specified pixel amounts.
        
        Args:
            dx: Horizontal pan distance in pixels
            dy: Vertical pan distance in pixels
        """
        self.camera_x += dx
        self.camera_y += dy
    
    def center_on_position(self, grid_pos: GridPosition) -> None:
        """Center the camera on a specific grid position."""
        scaled_cell_size = self.cell_size * self.zoom
        self.camera_x = (grid_pos.x * scaled_cell_size) - (self.screen_width // 2)
        self.camera_y = (grid_pos.y * scaled_cell_size) - (self.screen_height // 2)
    
    def render_grid_background(self, grid: SpatialCombatGrid) -> None:
        """
        Render the grid background with terrain.
        
        This method creates a cached surface for the grid background to improve
        performance when only combatants or overlays change.
        """
        if not self.grid_surface_dirty and self.grid_surface:
            return
        
        # Create surface for grid background
        scaled_cell_size = int(self.cell_size * self.zoom)
        grid_width = grid.width * scaled_cell_size
        grid_height = grid.height * scaled_cell_size
        
        self.grid_surface = pygame.Surface((grid_width, grid_height))
        self.grid_surface.fill(Colors.BACKGROUND)
        
        # Draw terrain
        for y in range(grid.height):
            for x in range(grid.width):
                terrain = grid.get_terrain(GridPosition(x, y))
                color = self.terrain_colors[terrain.terrain_type]
                
                rect = pygame.Rect(
                    x * scaled_cell_size,
                    y * scaled_cell_size,
                    scaled_cell_size,
                    scaled_cell_size
                )
                
                pygame.draw.rect(self.grid_surface, color, rect)
                
                # Draw terrain description if present and zoom is high enough
                if terrain.description and self.zoom > 1.5:
                    text = self.font_small.render(terrain.description[:10], True, (0, 0, 0))
                    text_rect = text.get_rect()
                    text_rect.center = rect.center
                    self.grid_surface.blit(text, text_rect)
        
        # Draw grid lines
        line_color = Colors.GRID_LINE
        major_line_color = Colors.GRID_LINE_MAJOR
        
        # Vertical lines
        for x in range(grid.width + 1):
            color = major_line_color if x % 5 == 0 else line_color
            start_pos = (x * scaled_cell_size, 0)
            end_pos = (x * scaled_cell_size, grid_height)
            pygame.draw.line(self.grid_surface, color, start_pos, end_pos, 1)
        
        # Horizontal lines
        for y in range(grid.height + 1):
            color = major_line_color if y % 5 == 0 else line_color
            start_pos = (0, y * scaled_cell_size)
            end_pos = (grid_width, y * scaled_cell_size)
            pygame.draw.line(self.grid_surface, color, start_pos, end_pos, 1)
        
        self.grid_surface_dirty = False
    
    def render_range_overlay(self, grid: SpatialCombatGrid, positions: List[GridPosition],
                           color: Tuple[int, int, int, int]) -> None:
        """
        Render a semi-transparent overlay for movement/attack ranges.
        
        Args:
            grid: Combat grid
            positions: List of positions to highlight
            color: RGBA color for the overlay
        """
        if not positions:
            return
        
        # Create temporary surface with alpha
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        
        scaled_cell_size = int(self.cell_size * self.zoom)
        
        for pos in positions:
            if grid.is_valid_position(pos):
                screen_x, screen_y = self.world_to_screen(pos)
                
                # Only draw if visible on screen
                if (-scaled_cell_size <= screen_x <= self.screen_width and
                    -scaled_cell_size <= screen_y <= self.screen_height):
                    
                    rect = pygame.Rect(screen_x, screen_y, scaled_cell_size, scaled_cell_size)
                    pygame.draw.rect(overlay, color, rect)
        
        self.screen.blit(overlay, (0, 0))
    
    def render_combatants(self, grid: SpatialCombatGrid, 
                         combatants: Dict[int, CombatantVisual]) -> None:
        """
        Render all combatants on the grid.
        
        Args:
            grid: Combat grid
            combatants: Dictionary of combatant visual data
        """
        scaled_cell_size = int(self.cell_size * self.zoom)
        
        for combatant_id, visual_data in combatants.items():
            position = grid.get_combatant_position(combatant_id)
            if not position:
                continue
            
            screen_x, screen_y = self.world_to_screen(position)
            
            # Only render if visible on screen
            if (-scaled_cell_size <= screen_x <= self.screen_width and
                -scaled_cell_size <= screen_y <= self.screen_height):
                
                self._render_single_combatant(screen_x, screen_y, scaled_cell_size, visual_data)
    
    def _render_single_combatant(self, screen_x: int, screen_y: int, 
                               cell_size: int, visual_data: CombatantVisual) -> None:
        """
        Render a single combatant with health bar and name.
        
        Args:
            screen_x: Screen X coordinate
            screen_y: Screen Y coordinate
            cell_size: Size of grid cell in pixels
            visual_data: Visual data for the combatant
        """
        # Calculate combatant rectangle
        combatant_size = cell_size - 4  # Small margin
        combatant_rect = pygame.Rect(
            screen_x + 2, screen_y + 2,
            combatant_size, combatant_size
        )
        
        # Draw selection highlight if selected
        if self.selected_combatant == visual_data.combatant_id:
            highlight_rect = pygame.Rect(screen_x - 2, screen_y - 2, 
                                       cell_size + 4, cell_size + 4)
            pygame.draw.rect(self.screen, Colors.SELECTED[:3], highlight_rect)
        
        # Draw combatant circle
        center = combatant_rect.center
        radius = min(combatant_rect.width, combatant_rect.height) // 2 - 2
        pygame.draw.circle(self.screen, visual_data.color, center, radius)
        pygame.draw.circle(self.screen, (0, 0, 0), center, radius, 2)  # Black border
        
        # Draw health bar
        if visual_data.max_hp > 0:
            health_ratio = visual_data.current_hp / visual_data.max_hp
            health_color = self._get_health_color(health_ratio)
            
            # Health bar background
            health_bg_rect = pygame.Rect(screen_x, screen_y - 8, cell_size, 4)
            pygame.draw.rect(self.screen, Colors.HEALTH_BACKGROUND, health_bg_rect)
            
            # Health bar foreground
            health_width = int(cell_size * health_ratio)
            health_rect = pygame.Rect(screen_x, screen_y - 8, health_width, 4)
            pygame.draw.rect(self.screen, health_color, health_rect)
        
        # Draw name if zoom is high enough
        if self.zoom > 1.0:
            name_text = self.font_small.render(visual_data.name[:8], True, (0, 0, 0))
            name_rect = name_text.get_rect()
            name_rect.centerx = center[0]
            name_rect.top = screen_y + cell_size + 2
            self.screen.blit(name_text, name_rect)
    
    def _get_health_color(self, health_ratio: float) -> Tuple[int, int, int]:
        """Get color for health bar based on health ratio."""
        if health_ratio > 0.6:
            return Colors.HEALTH_HIGH
        elif health_ratio > 0.3:
            return Colors.HEALTH_MID
        else:
            return Colors.HEALTH_LOW
    
    def render_cover_indicators(self, grid: SpatialCombatGrid, 
                              attacker_id: int, target_positions: List[GridPosition]) -> None:
        """
        Render cover indicators between an attacker and potential targets.
        
        Args:
            grid: Combat grid
            attacker_id: ID of attacking combatant
            target_positions: Positions to check cover for
        """
        attacker_pos = grid.get_combatant_position(attacker_id)
        if not attacker_pos:
            return
        
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        scaled_cell_size = int(self.cell_size * self.zoom)
        
        for target_pos in target_positions:
            cover_type = grid.get_cover_type(attacker_pos, target_pos)
            
            if cover_type != CoverType.NONE:
                screen_x, screen_y = self.world_to_screen(target_pos)
                
                if (-scaled_cell_size <= screen_x <= self.screen_width and
                    -scaled_cell_size <= screen_y <= self.screen_height):
                    
                    # Choose color based on cover type
                    if cover_type == CoverType.HALF:
                        color = Colors.COVER_HALF
                    elif cover_type == CoverType.THREE_QUARTERS:
                        color = Colors.COVER_THREE_QUARTERS
                    else:  # FULL
                        color = Colors.COVER_FULL
                    
                    rect = pygame.Rect(screen_x, screen_y, scaled_cell_size, scaled_cell_size)
                    pygame.draw.rect(overlay, color, rect)
        
        self.screen.blit(overlay, (0, 0))
    
    def render_ui_panel(self, combat_state: SpatialCombatState,
                       current_combatant: Optional[CombatantVisual]) -> None:
        """
        Render UI panel with combat information.
        
        Args:
            combat_state: Current combat state
            current_combatant: Visual data for current combatant
        """
        panel_width = 300
        panel_height = self.screen_height
        panel_rect = pygame.Rect(self.screen_width - panel_width, 0, panel_width, panel_height)
        
        # Draw panel background
        pygame.draw.rect(self.screen, (50, 50, 50), panel_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), panel_rect, 2)
        
        y_offset = 10
        
        # Round and turn information
        round_text = self.font_large.render(f"Round {combat_state.round_number}", True, (255, 255, 255))
        self.screen.blit(round_text, (panel_rect.x + 10, y_offset))
        y_offset += 40
        
        if current_combatant:
            turn_text = self.font_medium.render(f"Current Turn: {current_combatant.name}", True, (255, 255, 255))
            self.screen.blit(turn_text, (panel_rect.x + 10, y_offset))
            y_offset += 30
            
            hp_text = self.font_small.render(f"HP: {current_combatant.current_hp}/{current_combatant.max_hp}", True, (255, 255, 255))
            self.screen.blit(hp_text, (panel_rect.x + 10, y_offset))
            y_offset += 50
        
        # Instructions
        instructions = [
            "Controls:",
            "Left Click - Select/Move",
            "Right Click - Attack Range",
            "Mouse Wheel - Zoom",
            "Middle Drag - Pan",
            "Space - End Turn"
        ]
        
        for instruction in instructions:
            text = self.font_small.render(instruction, True, (200, 200, 200))
            self.screen.blit(text, (panel_rect.x + 10, y_offset))
            y_offset += 20
    
    def render_frame(self, grid: SpatialCombatGrid, 
                    combat_state: SpatialCombatState,
                    combatants: Dict[int, CombatantVisual]) -> None:
        """
        Render a complete frame of the combat visualization.
        
        Args:
            grid: Combat grid to render
            combat_state: Current combat state
            combatants: Dictionary of combatant visual data
        """
        # Clear screen
        self.screen.fill(Colors.BACKGROUND)
        
        # Render grid background
        self.render_grid_background(grid)
        
        # Draw the grid surface to screen with camera offset
        if self.grid_surface:
            self.screen.blit(self.grid_surface, (-self.camera_x, -self.camera_y))
        
        # Render movement range if showing
        if self.show_movement_range and self.selected_combatant:
            movement_positions = grid.get_valid_moves(self.selected_combatant, 30)  # 30ft movement
            self.render_range_overlay(grid, movement_positions, Colors.MOVEMENT_RANGE)
        
        # Render attack range if showing
        if self.show_attack_range and self.selected_combatant:
            attack_positions = grid.get_attack_range_positions(self.selected_combatant, 25)  # 25ft range
            self.render_range_overlay(grid, attack_positions, Colors.ATTACK_RANGE)
            
            # Show cover indicators
            self.render_cover_indicators(grid, self.selected_combatant, attack_positions)
        
        # Render movement path preview
        if self.movement_path:
            self.render_range_overlay(grid, self.movement_path, Colors.PATH_PREVIEW)
        
        # Render combatants
        self.render_combatants(grid, combatants)
        
        # Render UI panel
        current_combatant_id = combat_state.get_current_combatant()
        current_combatant = combatants.get(current_combatant_id) if current_combatant_id else None
        self.render_ui_panel(combat_state, current_combatant)
        
        # Update display
        pygame.display.flip()
    
    def cleanup(self) -> None:
        """Clean up pygame resources."""
        pygame.quit()


class SpatialCombatInterface:
    """
    Main interface class for the spatial combat system.
    
    This class handles the game loop, user input, and coordinates between
    the visual renderer and the combat logic.
    """
    
    def __init__(self, grid: SpatialCombatGrid, combat_state: SpatialCombatState):
        """
        Initialize the spatial combat interface.
        
        Args:
            grid: Combat grid
            combat_state: Combat state manager
        """
        self.grid = grid
        self.combat_state = combat_state
        self.renderer = GridRenderer()
        self.combatants: Dict[int, CombatantVisual] = {}
        
        # Input state
        self.mouse_dragging = False
        self.last_mouse_pos = (0, 0)
        
        # Game state
        self.running = True
        self.clock = pygame.time.Clock()
    
    def add_combatant_visual(self, combatant_id: int, name: str, 
                           max_hp: int, current_hp: int, 
                           is_player: bool = True) -> None:
        """Add visual representation for a combatant."""
        color = Colors.PLAYER if is_player else Colors.ENEMY
        self.combatants[combatant_id] = CombatantVisual(
            combatant_id=combatant_id,
            name=name,
            color=color,
            max_hp=max_hp,
            current_hp=current_hp,
            is_player=is_player
        )
    
    def handle_events(self) -> None:
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mouse_down(event)
            
            elif event.type == pygame.MOUSEBUTTONUP:
                self._handle_mouse_up(event)
            
            elif event.type == pygame.MOUSEMOTION:
                self._handle_mouse_motion(event)
            
            elif event.type == pygame.MOUSEWHEEL:
                self._handle_mouse_wheel(event)
            
            elif event.type == pygame.KEYDOWN:
                self._handle_key_down(event)
    
    def _handle_mouse_down(self, event) -> None:
        """Handle mouse button press events."""
        if event.button == 1:  # Left click
            grid_pos = self.renderer.screen_to_world(event.pos[0], event.pos[1])
            
            if self.grid.is_valid_position(grid_pos):
                # Check if clicking on a combatant
                combatants_at_pos = self.grid.get_combatants_at_position(grid_pos)
                
                if combatants_at_pos:
                    # Select combatant
                    self.renderer.selected_combatant = combatants_at_pos[0]
                    self.renderer.show_movement_range = True
                    self.renderer.show_attack_range = False
                else:
                    # Try to move selected combatant
                    if (self.renderer.selected_combatant and 
                        self.renderer.selected_combatant == self.combat_state.get_current_combatant()):
                        
                        can_move, reason = MovementValidator.can_move_to(
                            self.grid, self.renderer.selected_combatant, grid_pos, 30
                        )
                        
                        if can_move:
                            self.grid.move_combatant(self.renderer.selected_combatant, grid_pos)
                            self.renderer.show_movement_range = False
        
        elif event.button == 3:  # Right click
            if self.renderer.selected_combatant:
                self.renderer.show_attack_range = not self.renderer.show_attack_range
                self.renderer.show_movement_range = False
        
        elif event.button == 2:  # Middle click - start dragging
            self.mouse_dragging = True
            self.last_mouse_pos = event.pos
    
    def _handle_mouse_up(self, event) -> None:
        """Handle mouse button release events."""
        if event.button == 2:  # Middle click release
            self.mouse_dragging = False
    
    def _handle_mouse_motion(self, event) -> None:
        """Handle mouse movement events."""
        if self.mouse_dragging:
            dx = self.last_mouse_pos[0] - event.pos[0]
            dy = self.last_mouse_pos[1] - event.pos[1]
            self.renderer.pan_camera(dx, dy)
            self.last_mouse_pos = event.pos
        
        # Update movement path preview
        if self.renderer.selected_combatant and self.renderer.show_movement_range:
            target_pos = self.renderer.screen_to_world(event.pos[0], event.pos[1])
            if self.grid.is_valid_position(target_pos):
                current_pos = self.grid.get_combatant_position(self.renderer.selected_combatant)
                if current_pos:
                    self.renderer.movement_path = [target_pos]
    
    def _handle_mouse_wheel(self, event) -> None:
        """Handle mouse wheel events for zooming."""
        mouse_pos = pygame.mouse.get_pos()
        zoom_delta = event.y * 0.1
        self.renderer.zoom_at_point(zoom_delta, mouse_pos[0], mouse_pos[1])
    
    def _handle_key_down(self, event) -> None:
        """Handle keyboard events."""
        if event.key == pygame.K_SPACE:
            # End turn
            self.combat_state.next_turn()
            self.renderer.selected_combatant = self.combat_state.get_current_combatant()
            self.renderer.show_movement_range = False
            self.renderer.show_attack_range = False
        
        elif event.key == pygame.K_ESCAPE:
            # Deselect
            self.renderer.selected_combatant = None
            self.renderer.show_movement_range = False
            self.renderer.show_attack_range = False
    
    def run(self) -> None:
        """Run the main game loop."""
        while self.running:
            self.handle_events()
            
            # Render frame
            self.renderer.render_frame(self.grid, self.combat_state, self.combatants)
            
            # Control frame rate
            self.clock.tick(60)
        
        # Cleanup
        self.renderer.cleanup()


# Example usage and testing functions
def create_example_combat() -> Tuple[SpatialCombatGrid, SpatialCombatState]:
    """Create an example combat scenario for testing."""
    # Create 20x15 grid
    grid = SpatialCombatGrid(20, 15)
    
    # Add some terrain features
    # Add a wall
    for x in range(8, 12):
        grid.set_terrain(GridPosition(x, 7), TerrainType.BLOCKING, "Stone Wall")
    
    # Add difficult terrain (forest)
    for x in range(15, 18):
        for y in range(3, 8):
            grid.set_terrain(GridPosition(x, y), TerrainType.DIFFICULT, "Dense Forest")
    
    # Add partial cover (low walls)
    for x in range(5, 8):
        grid.set_terrain(GridPosition(x, 10), TerrainType.PARTIAL_COVER, "Low Wall")
    
    # Add water
    for x in range(2, 6):
        for y in range(12, 15):
            grid.set_terrain(GridPosition(x, y), TerrainType.WATER, "Stream")
    
    # Create combat state
    combat_state = SpatialCombatState(combat_id=1, grid=grid)
    
    # Add some combatants
    combat_state.add_combatant(1, GridPosition(2, 2), 15)  # Player character
    combat_state.add_combatant(2, GridPosition(18, 8), 12)  # Enemy
    combat_state.add_combatant(3, GridPosition(10, 12), 8)  # Another enemy
    
    return grid, combat_state


if __name__ == "__main__":
    """Run a standalone test of the spatial combat visual system."""
    
    # Create example combat
    grid, combat_state = create_example_combat()
    
    # Create interface
    interface = SpatialCombatInterface(grid, combat_state)
    
    # Add visual data for combatants
    interface.add_combatant_visual(1, "Hero", 25, 25, is_player=True)
    interface.add_combatant_visual(2, "Orc", 15, 15, is_player=False)
    interface.add_combatant_visual(3, "Goblin", 7, 7, is_player=False)
    
    # Start with first combatant selected
    interface.renderer.selected_combatant = 1
    interface.renderer.show_movement_range = True
    
    # Run the interface
    interface.run()