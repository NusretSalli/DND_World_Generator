"""
Main Flask Application - API Only
"""

import os
from flask import Flask, jsonify
from .config import config
from .utils.database import DatabaseManager
from .api.character_routes import character_bp
from .api.story_routes import story_bp  
from .api.combat_routes import combat_bp

def create_app(config_name=None):
    """Create and configure the Flask application."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize database
    DatabaseManager.init_app(app)
    
    # Register blueprints
    app.register_blueprint(character_bp)
    app.register_blueprint(story_bp)
    app.register_blueprint(combat_bp)
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        return jsonify({'status': 'healthy', 'message': 'D&D World Generator API is running'})
    
    # API documentation endpoint
    @app.route('/api')
    def api_documentation():
        return jsonify({
            'message': 'D&D World Generator API',
            'version': '2.0.0',
            'endpoints': {
                'characters': '/api/characters',
                'story': '/api/story', 
                'combat': '/api/combat',
                'health': '/api/health'
            }
        })
    
    return app

def setup_database(app):
    """Setup database tables."""
    with app.app_context():
        DatabaseManager.create_tables(app)
        
        # Populate standard enemies if needed
        from .models.enemy import Enemy
        from enemies import STANDARD_ENEMIES
        import json
        
        for enemy_data in STANDARD_ENEMIES.values():
            # Check if enemy already exists
            existing = Enemy.query.filter_by(name=enemy_data.name).first()
            if existing:
                continue
                
            enemy = Enemy(
                name=enemy_data.name,
                creature_type=enemy_data.creature_type.value,
                size=enemy_data.size.value,
                armor_class=enemy_data.armor_class,
                hit_points=enemy_data.hit_points,
                speed=enemy_data.speed,
                strength=enemy_data.strength,
                dexterity=enemy_data.dexterity,
                constitution=enemy_data.constitution,
                intelligence=enemy_data.intelligence,
                wisdom=enemy_data.wisdom,
                charisma=enemy_data.charisma,
                challenge_rating=enemy_data.challenge_rating,
                experience_points=enemy_data.experience_points,
                passive_perception=enemy_data.passive_perception,
                darkvision=enemy_data.darkvision,
                saving_throws=json.dumps(enemy_data.saving_throws),
                skills=json.dumps(enemy_data.skills),
                damage_resistances=json.dumps(enemy_data.damage_resistances),
                damage_immunities=json.dumps(enemy_data.damage_immunities),
                condition_immunities=json.dumps(enemy_data.condition_immunities),
                languages=json.dumps(enemy_data.languages),
                actions=json.dumps([{
                    'name': action.name,
                    'description': action.description,
                    'damage_dice': getattr(action, 'damage_dice', ''),
                    'damage_type': getattr(action, 'damage_type', ''),
                    'attack_bonus': getattr(action, 'attack_bonus', 0)
                } for action in enemy_data.actions]),
                special_abilities=json.dumps([{
                    'name': ability.name if hasattr(ability, 'name') else str(ability),
                    'description': ability.description if hasattr(ability, 'description') else str(ability)
                } for ability in enemy_data.special_abilities])
            )
            
            from .utils.database import db
            db.session.add(enemy)
        
        from .utils.database import db
        db.session.commit()
        print("Standard enemies populated successfully!")

if __name__ == '__main__':
    app = create_app('development')
    setup_database(app)
    app.run(
        debug=app.config['DEBUG'],
        host=app.config['API_HOST'],
        port=app.config['API_PORT']
    )