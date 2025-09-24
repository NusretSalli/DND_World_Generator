"""
API Routes and Endpoints
"""

from .character_routes import character_bp
from .story_routes import story_bp
from .combat_routes import combat_bp

__all__ = ['character_bp', 'story_bp', 'combat_bp']