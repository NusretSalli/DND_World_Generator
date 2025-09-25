#!/usr/bin/env python3
"""
Minimal Flask app for testing D&D World Generator without AI dependencies
"""

from flask import Flask
from dnd_world.database import db
from dnd_world.backend.routes import bp

def create_test_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_dnd.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_SORT_KEYS'] = False
    app.config['SECRET_KEY'] = 'test-key'
    
    db.init_app(app)
    app.register_blueprint(bp)
    
    with app.app_context():
        db.create_all()
        # Import after app context is created
        from dnd_world.backend.routes.combat import populate_standard_enemies
        from dnd_world.backend.routes.characters import ensure_default_character
        try:
            populate_standard_enemies()
            ensure_default_character()
        except Exception as e:
            print(f"Warning: Could not populate defaults: {e}")
    
    return app

if __name__ == '__main__':
    app = create_test_app()
    print("Starting minimal Flask app on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)