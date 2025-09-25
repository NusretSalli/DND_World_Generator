"""Story generation endpoints."""

from flask import jsonify, request

from dnd_world.models import Character
from dnd_world.core.story import story_generator

from . import bp


@bp.route('/generate_story', methods=['POST'])
def generate_story():
    payload = request.get_json(silent=True) or request.form.to_dict()
    prompt = (payload.get('prompt') or '').strip()
    character_id = payload.get('character_id')
    encounter_type = payload.get('encounter_type')
    environment = payload.get('environment', 'any')
    character_level = payload.get('character_level', 1)

    if not prompt and not encounter_type:
        return jsonify({'error': 'Provide a story prompt or select an encounter type.'}), 400

    character_context = ''
    if character_id:
        character = Character.query.get(character_id)
        if character:
            character_context = (
                f"Character: {character.name}, Class: {character.character_class}, "
                f"Level: {character.level}.\n"
            )
            if not character_level:
                character_level = character.level

    story = story_generator.generate_story(
        prompt=prompt,
        encounter_type=encounter_type,
        character_context=character_context,
        environment=environment,
        character_level=character_level,
    )
    return jsonify({'story': story})


@bp.route('/story_prompt_suggestions')
def story_prompt_suggestions():
    suggestions = [
        "The party arrives at a mysterious village just before sunset.",
        "A wounded messenger collapses at the heroes' feet, clutching a sealed letter.",
        "Strange lights flicker in the depths of the ancient forest.",
        "A noble requests the party's aid to investigate a haunted estate.",
    ]
    return jsonify({'suggestions': suggestions})
