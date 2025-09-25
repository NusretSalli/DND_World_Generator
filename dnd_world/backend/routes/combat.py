"""Combat endpoints and helpers."""
from __future__ import annotations

import json
from typing import Dict

from flask import jsonify, request

from dnd_world.database import db
from dnd_world.models import Character, Combat, Combatant, CombatAction, Enemy
from dnd_world.core.enemies import STANDARD_ENEMIES, get_enemy_by_name, get_random_enemy_for_level
from dnd_world.core.combat_engine import CombatEngine

from . import bp


GRID_COLS = 20
GRID_ROWS = 15
spatial_states: Dict[int, Dict[str, object]] = {}


def _manhattan(a, b):
    return abs(a['x'] - b['x']) + abs(a['y'] - b['y'])


def _init_spatial_positions(combat_id: int):
    combat = Combat.query.get(combat_id)
    if not combat:
        return
    positions = {}
    left_col = 1
    right_col = GRID_COLS - 2
    y_left = 1
    y_right = 1
    for combatant in sorted(combat.combatants, key=lambda x: x.initiative, reverse=True):
        is_monster = (combatant.character.character_class or '').lower() == 'monster'
        if is_monster:
            positions[combatant.id] = {'x': right_col, 'y': y_right}
            y_right = y_right + 2 if y_right + 2 < GRID_ROWS - 1 else 1
        else:
            positions[combatant.id] = {'x': left_col, 'y': y_left}
            y_left = y_left + 2 if y_left + 2 < GRID_ROWS - 1 else 1
    spatial_states[combat_id] = {'positions': positions, 'initialized': True}


def _get_spatial_state(combat_id: int):
    state = spatial_states.get(combat_id)
    if state is None or not state.get('initialized'):
        _init_spatial_positions(combat_id)
        state = spatial_states.get(combat_id)
    return state


def _is_occupied(positions: dict, x: int, y: int, ignore_id: int = None) -> bool:
    for cid, pos in positions.items():
        if ignore_id is not None and cid == ignore_id:
            continue
        if pos['x'] == x and pos['y'] == y:
            return True
    return False


def _place_new_combatant(combat_id: int, combatant: Combatant):
    state = _get_spatial_state(combat_id)
    if not state:
        return
    positions = state['positions']
    is_monster = (combatant.character.character_class or '').lower() == 'monster'
    col = GRID_COLS - 2 if is_monster else 1
    for y in range(1, GRID_ROWS - 1):
        if not _is_occupied(positions, col, y):
            positions[combatant.id] = {'x': col, 'y': y}
            break


def populate_standard_enemies():
    for enemy_data in STANDARD_ENEMIES.values():
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
            actions=json.dumps([
                {
                    'name': action.name,
                    'description': action.description,
                    'attack_bonus': action.attack_bonus,
                    'damage_dice': action.damage_dice,
                    'damage_type': action.damage_type,
                    'range': action.range,
                    'recharge': action.recharge,
                }
                for action in enemy_data.actions
            ]),
            special_abilities=json.dumps(enemy_data.special_abilities),
        )
        db.session.add(enemy)
    db.session.commit()


@bp.route('/combat/start', methods=['POST'])
def start_combat():
    data = request.get_json() or {}
    combat_name = data.get('name', 'Combat Encounter')
    character_ids = data.get('character_ids', [])
    if not character_ids:
        return jsonify({'error': 'No characters provided'}), 400

    combat = Combat(name=combat_name)
    db.session.add(combat)
    db.session.flush()

    for char_id in character_ids:
        character = Character.query.get(char_id)
        if not character:
            continue
        initiative = CombatEngine.roll_initiative(character.dexterity_modifier)
        combatant = Combatant(
            combat_id=combat.id,
            character_id=char_id,
            initiative=initiative,
            current_hp=character.current_hp,
        )
        db.session.add(combatant)
    db.session.commit()

    _init_spatial_positions(combat.id)

    return jsonify(combat_status_payload(combat))


def combat_status_payload(combat: Combat) -> dict:
    combatants = []
    for combatant in combat.combatants:
        combatants.append({
            'id': combatant.id,
            'character_name': combatant.character.name,
            'character_class': combatant.character.character_class,
            'initiative': combatant.initiative,
            'current_hp': combatant.current_hp,
            'max_hp': combatant.character.max_hp,
            'temp_hp': combatant.temp_hp,
            'ac': combatant.character.armor_class,
            'conditions': combatant.conditions_list,
            'is_conscious': combatant.is_conscious,
            'is_dead': combatant.is_dead,
            'has_action': combatant.has_action,
            'has_bonus_action': combatant.has_bonus_action,
            'has_movement': combatant.has_movement,
            'has_reaction': combatant.has_reaction,
            'death_saves': {
                'successes': combatant.death_save_successes,
                'failures': combatant.death_save_failures,
            },
        })
    current_combatant = combat.current_combatant
    return {
        'combat_id': combat.id,
        'name': combat.name,
        'round': combat.current_round,
        'is_active': combat.is_active,
        'combatants': combatants,
        'current_combatant_id': current_combatant.id if current_combatant else None,
        'current_combatant_name': current_combatant.character.name if current_combatant else None,
    }


@bp.route('/combat/<int:combat_id>/status')
def combat_status(combat_id: int):
    combat = Combat.query.get_or_404(combat_id)
    return jsonify(combat_status_payload(combat))


@bp.route('/combat/<int:combat_id>/end_turn', methods=['POST'])
def end_turn(combat_id: int):
    combat = Combat.query.get_or_404(combat_id)
    current = combat.current_combatant
    if current:
        current.reset_turn_actions()
    combat.next_turn()
    db.session.commit()
    return jsonify(combat_status_payload(combat))


@bp.route('/combat/<int:combat_id>/add_enemy', methods=['POST'])
def add_enemy_to_combat(combat_id: int):
    data = request.get_json() or {}
    enemy_name = data.get('name')
    combat = Combat.query.get_or_404(combat_id)

    if enemy_name:
        enemy_template = get_enemy_by_name(enemy_name)
    else:
        party_level = sum(c.character.level for c in combat.combatants) // max(len(combat.combatants), 1)
        enemy_template = get_random_enemy_for_level(party_level)

    if not enemy_template:
        return jsonify({'error': 'Enemy template not found'}), 404

    enemy_character = Character(
        name=enemy_template.name,
        gender='N/A',
        race=enemy_template.creature_type.value,
        character_class='monster',
        level=max(1, int(enemy_template.challenge_rating or 1)),
        experience=0,
        max_hp=enemy_template.hit_points,
        current_hp=enemy_template.hit_points,
        armor_class=enemy_template.armor_class,
        strength=enemy_template.strength,
        dexterity=enemy_template.dexterity,
        constitution=enemy_template.constitution,
        intelligence=enemy_template.intelligence,
        wisdom=enemy_template.wisdom,
        charisma=enemy_template.charisma,
    )
    db.session.add(enemy_character)
    db.session.flush()

    initiative = CombatEngine.roll_initiative(enemy_template.dexterity_mod)
    combatant = Combatant(
        combat_id=combat_id,
        character_id=enemy_character.id,
        initiative=initiative,
        current_hp=enemy_template.hit_points,
    )
    db.session.add(combatant)
    db.session.commit()

    _place_new_combatant(combat_id, combatant)

    return jsonify({'success': True, 'combatant_id': combatant.id})


@bp.route('/api/spatial/<int:combat_id>/state')
def spatial_state(combat_id: int):
    combat = Combat.query.get_or_404(combat_id)
    state = _get_spatial_state(combat_id)
    if not state:
        return jsonify({'error': 'Spatial state unavailable'}), 500
    positions = state['positions']
    roster = []
    for combatant in combat.combatants:
        pos = positions.get(combatant.id, {'x': 0, 'y': 0})
        roster.append({
            'id': combatant.id,
            'name': combatant.character.name,
            'hp': combatant.current_hp,
            'max_hp': combatant.character.max_hp,
            'ac': combatant.character.armor_class,
            'is_conscious': combatant.is_conscious,
            'is_dead': combatant.is_dead,
            'x': pos['x'],
            'y': pos['y'],
        })
    return jsonify({
        'grid': {'cols': GRID_COLS, 'rows': GRID_ROWS},
        'positions': positions,
        'combat_id': combat.id,
        'name': combat.name,
        'round': combat.current_round,
        'combatants': roster,
    })


@bp.route('/api/spatial/<int:combat_id>/move', methods=['POST'])
def spatial_move(combat_id: int):
    data = request.get_json() or {}
    combatant_id = data.get('combatant_id')
    x = data.get('x')
    y = data.get('y')
    if combatant_id is None or x is None or y is None:
        return jsonify({'error': 'combatant_id, x and y are required'}), 400

    combatant = Combatant.query.get_or_404(int(combatant_id))
    combat = Combat.query.get_or_404(combat_id)

    if combat.current_combatant is None or combat.current_combatant.id != combatant.id:
        return jsonify({'error': 'Not your turn'}), 400
    if not combatant.has_movement:
        return jsonify({'error': 'No movement left'}), 400

    state = _get_spatial_state(combat_id)
    if not state:
        return jsonify({'error': 'Spatial state not initialized'}), 500
    positions = state['positions']
    start = positions.get(combatant.id)
    if not start:
        return jsonify({'error': 'No start position'}), 400
    x = int(x)
    y = int(y)
    if x < 0 or y < 0 or x >= GRID_COLS or y >= GRID_ROWS:
        return jsonify({'error': 'Out of bounds'}), 400
    if _manhattan(start, {'x': x, 'y': y}) > 6:
        return jsonify({'error': 'Destination too far (max 6)'}), 400
    if _is_occupied(positions, x, y, ignore_id=combatant.id):
        return jsonify({'error': 'Tile occupied'}), 400

    positions[combatant.id] = {'x': x, 'y': y}
    combatant.has_movement = False
    db.session.commit()
    return jsonify({'success': True})


@bp.route('/api/spatial/<int:combat_id>/attack', methods=['POST'])
def spatial_attack(combat_id: int):
    data = request.get_json() or {}
    attacker_id = int(data.get('attacker_id', 0))
    target_id = int(data.get('target_id', 0))
    if not attacker_id or not target_id:
        return jsonify({'error': 'attacker_id and target_id are required'}), 400

    combat = Combat.query.get_or_404(combat_id)
    attacker = Combatant.query.get_or_404(attacker_id)
    target = Combatant.query.get_or_404(target_id)

    if combat.current_combatant is None or combat.current_combatant.id != attacker_id:
        return jsonify({'error': "Not attacker's turn"}), 400
    if not attacker.has_action:
        return jsonify({'error': 'No action available'}), 400

    state = _get_spatial_state(combat_id)
    if not state:
        return jsonify({'error': 'Spatial state not initialized'}), 500
    positions = state['positions']
    a_pos = positions.get(attacker_id)
    t_pos = positions.get(target_id)
    if not a_pos or not t_pos:
        return jsonify({'error': 'Positions unknown'}), 400
    if _manhattan(a_pos, t_pos) > 1:
        return jsonify({'error': 'Target out of melee range'}), 400

    attack_bonus = CombatEngine.calculate_weapon_attack_bonus(attacker.character, None)
    target_ac = CombatEngine.calculate_ac(target.character)
    hit, attack_roll, critical = CombatEngine.make_attack_roll(attack_bonus, target_ac)

    damage_dealt = 0
    damage_type = 'bludgeoning'
    if hit:
        dmg = CombatEngine.calculate_weapon_damage(attacker.character, None, critical)
        total = CombatEngine.roll_dice(dmg.dice_count, dmg.dice_size, dmg.modifier)
        if total > 0:
            target.apply_damage(total)
            damage_dealt = total
        damage_type = dmg.damage_type

    attacker.has_action = False
    db.session.commit()

    action = CombatAction(
        combat_id=combat_id,
        actor_id=attacker_id,
        target_id=target_id,
        action_type='attack',
        round_number=combat.current_round,
        action_data=json.dumps({'spatial': True, 'attack_roll': attack_roll, 'critical': critical}),
        result=json.dumps({'hit': hit, 'damage': damage_dealt, 'damage_type': damage_type}),
    )
    db.session.add(action)
    db.session.commit()

    return jsonify({'success': True, 'hit': hit, 'attack_roll': attack_roll, 'critical': critical, 'damage': damage_dealt, 'damage_type': damage_type})
