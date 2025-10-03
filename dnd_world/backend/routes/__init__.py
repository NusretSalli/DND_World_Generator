"""Blueprint registration for backend routes."""

from flask import Blueprint

bp = Blueprint('api', __name__)

from . import system
from . import characters
from . import combat
from . import story
from . import auth

from .combat import populate_standard_enemies
from .characters import ensure_default_character

__all__ = ["bp", "populate_standard_enemies", "ensure_default_character"]
