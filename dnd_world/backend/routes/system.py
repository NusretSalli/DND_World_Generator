"""System-level endpoints: health checks, name generation, dice utilities."""

from flask import jsonify, request
from pynames import GENDER
from pynames.generators.elven import WarhammerNamesGenerator, DnDNamesGenerator
from pynames.generators.goblin import GoblinGenerator
from pynames.generators.korean import KoreanNamesGenerator
from pynames.generators.orc import OrcNamesGenerator
from pynames.generators.russian import PaganNamesGenerator
from pynames.generators.scandinavian import ScandinavianNamesGenerator

from dnd_world.utils.dice import DiceRoller, apply_racial_bonuses, calculate_ability_modifier
from dnd_world.database import cleanup_old_combat_sessions, cleanup_orphaned_items, get_database_stats

from . import bp


RACE_TO_GENERATOR = {
    'dwarf': KoreanNamesGenerator(),
    'elf': DnDNamesGenerator(),
    'half-orc': OrcNamesGenerator(),
    'gnome': GoblinGenerator(),
    'human': ScandinavianNamesGenerator(),
    'halfling': KoreanNamesGenerator(),
    'dragonborn': KoreanNamesGenerator(),
    'half-elf': WarhammerNamesGenerator(),
    'tiefling': PaganNamesGenerator(),
}


@bp.route('/')
def index():
    """Simple health check endpoint for the API."""
    return jsonify({'status': 'ok', 'service': 'dnd_world_api'})


@bp.route('/generate_name')
def generate_name():
    race = request.args.get('race', 'human')
    gender_str = request.args.get('gender', 'male')
    gender = GENDER.MALE if gender_str.lower() == 'male' else GENDER.FEMALE
    generator = RACE_TO_GENERATOR.get(race.lower(), ScandinavianNamesGenerator())
    try:
        name = generator.get_name_simple(gender)
    except TypeError:
        name = generator.get_name_simple()
    return jsonify({'name': name})


@bp.route('/generate_ability_scores')
def generate_ability_scores():
    method = request.args.get('method', '4d6').lower()
    race = request.args.get('race', 'human')
    if method == 'standard':
        base_scores = DiceRoller.standard_array()
    elif method == 'point_buy':
        base_scores = DiceRoller.point_buy_base()
    else:
        base_scores = DiceRoller.roll_full_ability_scores()
    final_scores = apply_racial_bonuses(base_scores, race)
    modifiers = {ability: calculate_ability_modifier(score) for ability, score in final_scores.items()}
    return jsonify({'scores': final_scores, 'modifiers': modifiers, 'method': method, 'race': race})


@bp.route('/roll_dice')
def roll_dice():
    dice_notation = request.args.get('dice', '1d20')
    try:
        result = DiceRoller.roll(dice_notation)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    return jsonify({
        'total': result.total,
        'rolls': result.rolls,
        'modifier': result.modifier,
        'notation': result.dice_notation,
        'description': str(result),
    })


@bp.route('/database/cleanup', methods=['POST'])
def cleanup_database():
    """Clean up old data from the database to prevent clutter."""
    data = request.get_json(silent=True) or {}
    days_old = data.get('days_old', 7)
    
    try:
        # Clean up old combat sessions
        combat_cleaned = cleanup_old_combat_sessions(days_old)
        
        # Clean up orphaned items
        items_cleaned = cleanup_orphaned_items()
        
        return jsonify({
            'success': True,
            'combats_removed': combat_cleaned,
            'items_removed': items_cleaned,
            'message': f'Cleaned {combat_cleaned} old combat sessions and {items_cleaned} orphaned items'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/database/stats')
def database_stats():
    """Get database statistics."""
    try:
        stats = get_database_stats()
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
