"""
Story Generation API Routes
"""

from flask import Blueprint, request, jsonify
from ..models.character import Character
from ..core.story_generator import StorySystem

story_bp = Blueprint('story', __name__, url_prefix='/api/story')

# Initialize story system
story_system = StorySystem()

@story_bp.route('/generate', methods=['POST'])
def generate_story():
    """Generate story content using the LLM."""
    try:
        data = request.get_json()
        prompt = data.get('prompt', '').strip()
        character_id = data.get('character_id')
        encounter_type = data.get('encounter_type')
        
        if not prompt and not encounter_type:
            return jsonify({'error': 'Please provide a story prompt or select an encounter type.'}), 400
        
        character_context = ""
        if character_id:
            character = Character.query.get(character_id)
            if character:
                character_context = f"{character.name}, a level {character.level} {character.race} {character.character_class}"
        
        # Generate different types of content
        if encounter_type == 'random_encounter':
            level = 1
            if character_id:
                character = Character.query.get(character_id)
                if character:
                    level = character.level
            story_text = story_system.generate_encounter(character_level=level)
        elif encounter_type == 'npc_dialogue':
            story_text = story_system.generate_npc_dialogue()
        else:
            # Regular story continuation
            story_text = story_system.generate_story_continuation(prompt, character_context)
        
        return jsonify({'story': story_text})
        
    except Exception as e:
        print(f"Error generating story: {e}")
        return jsonify({'error': 'Failed to generate story. The mystical forces are disrupted.'}), 500

@story_bp.route('/suggestions', methods=['GET'])
def story_prompt_suggestions():
    """Get suggested story prompts."""
    suggestions = [
        "The party enters a mysterious tavern where something seems off...",
        "A hooded figure approaches you on the road...",
        "You discover an ancient ruin hidden in the forest...",
        "The local villagers speak of strange disappearances...",
        "A treasure map leads you to a dangerous location...",
        "You hear rumors of a powerful artifact...",
        "The weather suddenly changes as dark clouds gather...",
        "You stumble upon a group of bandits arguing..."
    ]
    return jsonify({'suggestions': suggestions})