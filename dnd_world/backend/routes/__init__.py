"""Blueprint registration for backend routes."""

from flask import Blueprint

bp = Blueprint('api', __name__)

# Import route modules to register endpoints
from . import system  # noqa: F401
from . import characters  # noqa: F401
from . import combat  # noqa: F401
from . import story  # noqa: F401
from . import auth  # noqa: F401

# Re-export seeding helpers
from .combat import populate_standard_enemies  # noqa: E402,F401
from .characters import ensure_default_character  # noqa: E402,F401

__all__ = ["bp", "populate_standard_enemies", "ensure_default_character"]
