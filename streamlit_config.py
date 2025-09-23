"""
Configuration file for D&D World Generator Streamlit App
Customize the application settings here
"""

# Flask Backend Configuration
FLASK_HOST = "localhost"
FLASK_PORT = 5000
FLASK_URL = f"http://{FLASK_HOST}:{FLASK_PORT}"

# Streamlit Configuration
STREAMLIT_PORT = 8501
STREAMLIT_HOST = "localhost"

# Application Settings
APP_TITLE = "🐉 D&D World Generator"
APP_ICON = "🐉"
LAYOUT = "wide"  # "centered" or "wide"

# Theme Configuration
DARK_THEME = True
PRIMARY_COLOR = "#4dabf7"
BACKGROUND_COLOR = "#0f1419"
SECONDARY_BACKGROUND = "#1a1a2e"
TEXT_COLOR = "#e6edf3"

# Combat Grid Settings
DEFAULT_GRID_SIZE = 20
GRID_LINE_COLOR = "#2d3742"
COMBATANT_MARKER_SIZE = 25

# Dice Roller Settings
DEFAULT_DICE = "1d20"
SHOW_INDIVIDUAL_ROLLS = True
SHOW_MODIFIERS = True
ENABLE_ADVANTAGE_DISADVANTAGE = True

# Character Creation Settings
DEFAULT_ABILITY_SCORE_METHOD = "4d6"  # "4d6", "standard", "manual"
RACIAL_BONUSES_ENABLED = True
AUTO_CALCULATE_MODIFIERS = True

# Spell System Settings
SHOW_SPELL_SLOTS_VISUAL = True
ENABLE_CANTRIP_CASTING = True
AUTO_DEDUCT_SPELL_SLOTS = True

# Story Generator Settings
DEFAULT_STORY_LENGTH = "medium"  # "short", "medium", "long"
ENABLE_CHARACTER_CONTEXT = True
DEFAULT_ENVIRONMENT = "any"

# UI Behavior
AUTO_REFRESH_INTERVAL = 5  # seconds
SHOW_SUCCESS_MESSAGES = True
SHOW_ERROR_DETAILS = True
ENABLE_TOOLTIPS = True

# Development Settings
DEBUG_MODE = False
SHOW_API_RESPONSES = False
LOG_DICE_ROLLS = False

# Desktop App Settings (for PyInstaller)
DESKTOP_APP_NAME = "DND_World_Generator"
DESKTOP_APP_VERSION = "1.0.0"
DESKTOP_APP_DESCRIPTION = "D&D Campaign Management System"

# API Timeout Settings (seconds)
API_TIMEOUT_SHORT = 3   # For quick operations
API_TIMEOUT_MEDIUM = 5  # For normal operations
API_TIMEOUT_LONG = 15   # For complex operations like story generation

# Cache Settings
CACHE_CHARACTER_DATA = True
CACHE_DURATION = 300  # 5 minutes

# Feature Flags
ENABLE_SPATIAL_COMBAT = True
ENABLE_STORY_GENERATOR = True
ENABLE_ADVANCED_DICE = True
ENABLE_SPELL_MANAGEMENT = True
ENABLE_INVENTORY_INTEGRATION = True

# Notification Settings
SHOW_CRITICAL_ROLL_NOTIFICATIONS = True
SHOW_COMBAT_NOTIFICATIONS = True
SHOW_SPELL_CAST_NOTIFICATIONS = True

# Data Validation
VALIDATE_CHARACTER_DATA = True
VALIDATE_DICE_NOTATION = True
VALIDATE_SPELL_SLOTS = True

# Export/Import Settings
ENABLE_CHARACTER_EXPORT = True
ENABLE_CAMPAIGN_BACKUP = True
EXPORT_FORMAT = "json"  # "json", "csv", "xml"

# Advanced Features
ENABLE_ANALYTICS = False
ENABLE_MULTIPLAYER = False  # Future feature
ENABLE_VOICE_COMMANDS = False  # Future feature

# Error Handling
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds
GRACEFUL_DEGRADATION = True  # Continue working even if some features fail