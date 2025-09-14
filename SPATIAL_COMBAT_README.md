# Spatial Combat System Documentation

## Overview

The Spatial Combat System is a comprehensive grid-based combat enhancement for the D&D World Generator that follows D&D 5e rules. It provides visual, tactical combat with terrain effects, line of sight, cover mechanics, and movement validation.

## Features

### Core Functionality
- **Grid-based positioning**: 20x15 grid where each square represents 5 feet
- **D&D 5e movement rules**: Including diagonal movement costs and difficult terrain
- **Line of sight calculations**: Using Bresenham's algorithm for precise line tracing
- **Cover mechanics**: Half, three-quarters, and full cover following D&D 5e rules
- **Terrain types**: Multiple terrain types affecting movement and combat
- **Visual interface**: Real-time pygame-based grid visualization

### Terrain Types
- **Open**: Normal movement, no cover
- **Difficult**: 2x movement cost (swamp, thick vegetation)
- **Blocking**: Impassable terrain that blocks line of sight (walls, large rocks)
- **Partial Cover**: Normal movement, provides +2 AC bonus
- **Full Cover**: Normal movement, provides complete protection from ranged attacks
- **Water**: Difficult terrain with special swimming rules
- **Pit**: Impassable without special abilities
- **Elevated**: Higher ground for tactical advantage

### Movement and Combat
- **Movement validation**: Ensures moves follow D&D 5e rules
- **Opportunity attacks**: Triggered when leaving enemy reach
- **Range calculations**: Accurate distance measurement for weapons and spells
- **Cover assessment**: Automatic calculation of cover bonuses
- **Turn-based integration**: Seamlessly integrates with existing combat system

## Installation and Setup

### Requirements
- Python 3.8+
- pygame (for visual interface)
- Flask (existing requirement)
- All existing D&D World Generator dependencies

### Installation
```bash
pip install pygame
```

The spatial combat system is automatically integrated when the application starts.

## Usage

### Web Interface

1. **Start a Combat Encounter**
   - Create characters and start combat as usual
   - The spatial combat section will appear in the combat interface

2. **Enable Spatial Combat**
   - Click "Enable Spatial Combat" to create the grid
   - Optionally select a terrain template before enabling
   - Combatants will be automatically placed on the grid

3. **Grid Interaction**
   - Click combatant tokens to select them
   - Click grid squares to move selected combatants
   - Use control buttons to show movement/attack ranges

4. **Terrain Templates**
   - **Dungeon Room**: Classic dungeon with walls and pillars
   - **Forest Clearing**: Outdoor combat with trees and undergrowth
   - **Castle Courtyard**: Defensive structures and elevated positions

### Visual Interface (Pygame)

1. **Launch Visual Interface**
   - Click "Launch Pygame Interface" for a dedicated window
   - Provides enhanced visualization and interaction

2. **Controls**
   - **Left Click**: Select combatant or move to position
   - **Right Click**: Toggle attack range display
   - **Mouse Wheel**: Zoom in/out
   - **Middle Mouse + Drag**: Pan camera
   - **Space**: End current turn
   - **Escape**: Deselect combatant

### API Integration

The spatial combat system provides REST API endpoints:

```javascript
// Create spatial combat
POST /api/spatial_combat/{combat_id}/create
{
    "width": 20,
    "height": 15,
    "terrain_setup": { /* optional terrain template */ }
}

// Move combatant
POST /api/spatial_combat/{combat_id}/move
{
    "combatant_id": 1,
    "target_x": 5,
    "target_y": 3,
    "movement_speed": 30
}

// Get valid movement positions
GET /api/spatial_combat/{combat_id}/valid_moves/{combatant_id}?movement_speed=30

// Get attack range positions
GET /api/spatial_combat/{combat_id}/attack_range/{combatant_id}?weapon_range=25

// Get attack modifiers for positioning
GET /api/spatial_combat/{combat_id}/attack_modifiers?attacker_id=1&target_id=2
```

## Technical Implementation

### Architecture

The spatial combat system follows a modular design:

1. **Core System** (`spatial_combat.py`)
   - Grid management and terrain handling
   - Position tracking and movement validation
   - Line of sight and cover calculations
   - State persistence and serialization

2. **Visual Interface** (`spatial_combat_visual.py`)
   - Pygame-based rendering engine
   - User interaction handling
   - Real-time grid visualization
   - Camera controls and zooming

3. **Integration Layer** (`spatial_combat_integration.py`)
   - Flask API endpoints
   - Database integration
   - State management
   - Template system

### Key Classes

- **`SpatialCombatGrid`**: Core grid management
- **`GridPosition`**: Position representation with D&D distance calculations
- **`TerrainTile`**: Terrain type and properties
- **`SpatialCombatState`**: Complete combat state management
- **`MovementValidator`**: Movement rule validation
- **`GridRenderer`**: Visual rendering engine
- **`SpatialCombatInterface`**: Complete visual interface

### Performance Optimizations

- **Caching**: Line of sight and cover calculations are cached
- **Lazy rendering**: Grid background is cached and only updated when terrain changes
- **Efficient algorithms**: Bresenham's algorithm for line tracing
- **Optimized drawing**: Only visible elements are rendered

## Combat Rules Implementation

### Movement
- **Speed**: Characters move at their listed speed in feet per turn
- **Diagonal movement**: Alternates between 5ft and 10ft cost following D&D 5e optional rules
- **Difficult terrain**: Costs 2x movement to enter
- **Opportunity attacks**: Triggered when leaving adjacent enemy squares

### Line of Sight
- **Clear path**: Must have unobstructed line between centers of squares
- **Blocking terrain**: Walls, large objects block line of sight completely
- **Partial cover**: Low walls, debris provide cover but don't block sight

### Cover Mechanics
- **Half Cover**: +2 bonus to AC and Dexterity saving throws
- **Three-Quarters Cover**: +5 bonus to AC and Dexterity saving throws
- **Full Cover**: Cannot be targeted by most attacks and spells

### Attack Range
- **Melee weapons**: Adjacent squares (5 feet)
- **Ranged weapons**: Based on weapon properties
- **Reach weapons**: Extended melee range
- **Spells**: Range based on spell description

## Customization and Extension

### Adding New Terrain Types
```python
# In spatial_combat.py
class TerrainType(Enum):
    CUSTOM_TERRAIN = "custom_terrain"

# Update terrain properties in TerrainTile.__post_init__
terrain_properties = {
    # existing terrain...
    TerrainType.CUSTOM_TERRAIN: (movement_cost, blocks_los, cover_type),
}
```

### Creating Custom Terrain Templates
```python
# In spatial_combat_integration.py
TERRAIN_TEMPLATES['custom_template'] = {
    'name': 'Custom Template',
    'description': 'A custom terrain setup',
    'features': [
        {
            'type': 'blocking',
            'description': 'Custom Wall',
            'positions': [{'x': 5, 'y': 5}, {'x': 6, 'y': 5}]
        }
    ]
}
```

### Extending Visual Interface
The pygame interface can be extended with:
- Custom rendering effects
- Additional UI elements
- Sound effects
- Animation systems
- Special effect overlays

## Troubleshooting

### Common Issues

1. **Pygame not displaying**: Check if display is available in your environment
2. **Movement validation failing**: Verify terrain setup and movement speed
3. **Line of sight incorrect**: Ensure terrain cache is cleared after terrain changes
4. **Performance issues**: Reduce grid size or disable visual effects

### Debug Mode
Enable debug logging by setting environment variable:
```bash
export SPATIAL_COMBAT_DEBUG=1
python app.py
```

### Testing
Run the comprehensive test suite:
```bash
python test_spatial_combat.py
```

## Future Enhancements

Planned features for future versions:
- **3D visualization**: Height levels and flying creatures
- **Weather effects**: Environmental conditions affecting combat
- **Spell effects**: Visual representation of area effects
- **Multiplayer support**: Real-time collaborative combat
- **AI opponents**: Automated enemy behavior
- **VTT integration**: Import/export for virtual tabletop tools

## Contributing

When contributing to the spatial combat system:
1. Follow the existing modular architecture
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Ensure backwards compatibility with existing combat system
5. Test both web and pygame interfaces

## License

The spatial combat system is part of the D&D World Generator project and follows the same license terms.