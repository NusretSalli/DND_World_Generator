"""
Simple API Server Launcher
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dnd_world.app import create_app, setup_database

if __name__ == "__main__":
    print("🐉 D&D World Generator API v2.0")
    print("Setting up database and starting server...")
    
    app = create_app()
    setup_database(app)
    
    print("API server starting on http://localhost:5000")
    print("Available endpoints:")
    print("- GET  /api/health - Health check")
    print("- GET  /api/characters - List characters")
    print("- POST /api/characters - Create character")
    print("- POST /api/story/generate - Generate story")
    print("- POST /api/combat/start - Start combat")
    
    app.run(debug=True, port=5000)