"""
Combat API Routes
"""

from flask import Blueprint, request, jsonify
from ..models.combat import Combat, CombatParticipant
from ..models.character import Character
from ..models.enemy import Enemy
from ..utils.database import db

combat_bp = Blueprint('combat', __name__, url_prefix='/api/combat')

@combat_bp.route('/start', methods=['POST'])
def start_combat():
    """Start a new combat encounter."""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'name' not in data:
            return jsonify({'error': 'Combat name is required'}), 400
        
        # Create new combat
        combat = Combat(name=data['name'])
        db.session.add(combat)
        db.session.commit()
        
        return jsonify({
            'combat_id': combat.id,
            'name': combat.name,
            'message': f'Combat "{combat.name}" started!'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@combat_bp.route('/<int:combat_id>/status', methods=['GET'])
def combat_status(combat_id):
    """Get current combat status."""
    try:
        combat = Combat.query.get_or_404(combat_id)
        
        combatants = []
        for combatant in combat.turn_order:
            character = Character.query.get(combatant.character_id)
            combatants.append({
                'id': combatant.id,
                'character_name': character.name if character else 'Unknown',
                'initiative': combatant.initiative,
                'current_hp': combatant.current_hp,
                'temp_hp': combatant.temp_hp,
                'is_current_turn': combat.current_combatant and combat.current_combatant.id == combatant.id,
                'has_action': combatant.has_action,
                'has_bonus_action': combatant.has_bonus_action,
                'has_movement': combatant.has_movement,
                'has_reaction': combatant.has_reaction
            })
        
        return jsonify({
            'combat_id': combat.id,
            'name': combat.name,
            'current_round': combat.current_round,
            'is_active': combat.is_active,
            'combatants': combatants,
            'current_turn': combat.current_turn
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@combat_bp.route('/<int:combat_id>/add_participant', methods=['POST'])
def add_participant(combat_id):
    """Add a participant to combat."""
    try:
        combat = Combat.query.get_or_404(combat_id)
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['character_id', 'initiative']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        character = Character.query.get_or_404(data['character_id'])
        
        # Create combatant
        combatant = CombatParticipant(
            combat_id=combat.id,
            character_id=character.id,
            initiative=data['initiative'],
            current_hp=data.get('current_hp', character.current_hp),
            temp_hp=data.get('temp_hp', 0)
        )
        
        db.session.add(combatant)
        db.session.commit()
        
        return jsonify({
            'combatant_id': combatant.id,
            'message': f'{character.name} added to combat with initiative {combatant.initiative}'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@combat_bp.route('/<int:combat_id>/next_turn', methods=['POST'])
def next_turn(combat_id):
    """Advance to next turn in combat."""
    try:
        combat = Combat.query.get_or_404(combat_id)
        
        if not combat.is_active:
            return jsonify({'error': 'Combat is not active'}), 400
        
        # Reset current combatant's actions
        current_combatant = combat.current_combatant
        if current_combatant:
            current_combatant.reset_turn_actions()
        
        # Advance turn
        combat.next_turn()
        
        next_combatant = combat.current_combatant
        character_name = "Unknown"
        if next_combatant:
            character = Character.query.get(next_combatant.character_id)
            if character:
                character_name = character.name
        
        return jsonify({
            'current_round': combat.current_round,
            'current_turn': combat.current_turn,
            'current_combatant': character_name,
            'message': f"It's now {character_name}'s turn (Round {combat.current_round})"
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@combat_bp.route('/<int:combat_id>/end', methods=['POST'])
def end_combat(combat_id):
    """End combat encounter."""
    try:
        combat = Combat.query.get_or_404(combat_id)
        combat.is_active = False
        db.session.commit()
        
        return jsonify({
            'message': f'Combat "{combat.name}" has ended'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500