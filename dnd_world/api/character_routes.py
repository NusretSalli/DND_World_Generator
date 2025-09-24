"""
Character API Routes
"""

from flask import Blueprint, request, jsonify
from ..models.character import Character
from ..models.inventory import Item
from ..core.character_creation import CharacterCreator
from ..core.name_generator import NameGenerators
from ..utils.database import db

character_bp = Blueprint('character', __name__, url_prefix='/api/characters')

@character_bp.route('', methods=['GET'])
def list_characters():
    """Get all characters."""
    try:
        characters = Character.query.all()
        
        character_list = []
        for char in characters:
            character_list.append({
                'id': char.id,
                'name': char.name,
                'character_class': char.character_class,
                'level': char.level,
                'current_hp': char.current_hp,
                'max_hp': char.max_hp,
                'armor_class': char.armor_class,
                'race': char.race,
                'gender': char.gender,
                'experience': char.experience,
                'abilities': {
                    'strength': char.strength,
                    'dexterity': char.dexterity,
                    'constitution': char.constitution,
                    'intelligence': char.intelligence,
                    'wisdom': char.wisdom,
                    'charisma': char.charisma
                }
            })
        
        return jsonify(character_list)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@character_bp.route('', methods=['POST'])
def create_character():
    """Create a new character."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'race', 'character_class', 'gender']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create character using character creator
        character = CharacterCreator.create_character(
            name=data['name'],
            race=data['race'],
            character_class=data['character_class'],
            gender=data['gender'],
            ability_scores=data.get('ability_scores')
        )
        
        return jsonify({
            'id': character.id,
            'name': character.name,
            'message': f'Character {character.name} created successfully!'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@character_bp.route('/<int:character_id>', methods=['GET'])
def get_character(character_id):
    """Get detailed character information."""
    try:
        character = Character.query.get_or_404(character_id)
        
        return jsonify({
            'id': character.id,
            'name': character.name,
            'race': character.race,
            'character_class': character.character_class,
            'gender': character.gender,
            'level': character.level,
            'experience': character.experience,
            'current_hp': character.current_hp,
            'max_hp': character.max_hp,
            'armor_class': character.armor_class,
            'abilities': {
                'strength': character.strength,
                'dexterity': character.dexterity,
                'constitution': character.constitution,
                'intelligence': character.intelligence,
                'wisdom': character.wisdom,
                'charisma': character.charisma
            },
            'modifiers': {
                'strength': character.strength_modifier,
                'dexterity': character.dexterity_modifier,
                'constitution': character.constitution_modifier,
                'intelligence': character.intelligence_modifier,
                'wisdom': character.wisdom_modifier,
                'charisma': character.charisma_modifier
            },
            'currency': {
                'copper': character.copper,
                'silver': character.silver,
                'gold': character.gold,
                'platinum': character.platinum
            },
            'inventory_count': len(character.inventory),
            'total_weight': character.total_weight,
            'carrying_capacity': character.carrying_capacity
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@character_bp.route('/<int:character_id>', methods=['DELETE'])
def delete_character(character_id):
    """Delete a character."""
    try:
        character = Character.query.get_or_404(character_id)
        name = character.name
        
        db.session.delete(character)
        db.session.commit()
        
        return jsonify({'message': f'Character {name} deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@character_bp.route('/<int:character_id>/inventory', methods=['GET'])
def get_character_inventory(character_id):
    """Get character inventory."""
    try:
        character = Character.query.get_or_404(character_id)
        
        inventory = []
        for item in character.inventory:
            inventory.append({
                'id': item.id,
                'name': item.name,
                'item_type': item.item_type,
                'description': item.description,
                'weight': item.weight,
                'value': item.value,
                'rarity': item.rarity,
                'magical': item.magical,
                'equipped_slot': item.equipped_slot,
                'damage': item.damage,
                'damage_type': item.damage_type,
                'base_ac': item.base_ac,
                'armor_type': item.armor_type
            })
        
        return jsonify(inventory)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@character_bp.route('/<int:character_id>/inventory', methods=['POST'])
def add_item_to_character(character_id):
    """Add an item to character inventory."""
    try:
        character = Character.query.get_or_404(character_id)
        data = request.get_json()
        
        # Validate required fields
        if 'name' not in data or 'item_type' not in data:
            return jsonify({'error': 'Missing required fields: name, item_type'}), 400
        
        # Create item
        item = character.add_item(**data)
        
        return jsonify({
            'id': item.id,
            'name': item.name,
            'message': f'Item {item.name} added to {character.name}\'s inventory'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@character_bp.route('/generate_name', methods=['GET'])
def generate_name():
    """Generate a name for a character."""
    try:
        race = request.args.get('race', 'human')
        gender = request.args.get('gender', 'male')
        
        name = NameGenerators.generate_name(race, gender)
        
        return jsonify({'name': name})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500