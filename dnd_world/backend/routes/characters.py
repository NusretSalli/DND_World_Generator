"""Character management endpoints."""
from __future__ import annotations

from typing import Any, Dict

from flask import jsonify, request, session

from dnd_world.database import db
from dnd_world.models import Character, Item
from dnd_world.core.items import (
    CLASS_EQUIPMENT,
    ALL_ITEMS,
    EquipmentSlot,
)
from dnd_world.core.spells import get_cantrips_known, get_spells_known

from . import bp



def _to_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"1", "true", "yes", "on"}
    return bool(value)


def calculate_max_hp(char_class: str, constitution_mod: int, level: int = 1) -> int:
    class_hit_dice = {
        'barbarian': 12,
        'fighter': 10, 'paladin': 10, 'ranger': 10,
        'bard': 8, 'cleric': 8, 'druid': 8, 'monk': 8, 'rogue': 8, 'warlock': 8,
        'sorcerer': 6, 'wizard': 6
    }
    base_hp = class_hit_dice.get((char_class or '').lower(), 8)
    max_hp = base_hp + constitution_mod
    if level > 1:
        avg_hp_per_level = ((base_hp + 1) // 2) + constitution_mod
        max_hp += (level - 1) * max(1, avg_hp_per_level)
    return max_hp


def _payload() -> Dict[str, Any]:
    data = request.get_json(silent=True)
    if data is None or not isinstance(data, dict):
        data = request.form.to_dict()
    return data


def _serialize_item(item: Item) -> Dict[str, Any]:
    return {
        'id': item.id,
        'name': item.name,
        'item_type': item.item_type,
        'description': item.description,
        'weight': item.weight,
        'value': item.value,
        'rarity': item.rarity,
        'magical': item.magical,
        'requires_attunement': item.requires_attunement,
        'equipped_slot': item.equipped_slot,
        'damage': item.damage,
        'damage_type': item.damage_type,
        'armor_type': item.armor_type,
        'base_ac': item.base_ac,
        'strength_req': item.strength_req,
        'stealth_disadvantage': item.stealth_disadvantage,
        'charges': item.charges,
        'max_charges': item.max_charges,
    }


def _serialize_character(character: Character) -> Dict[str, Any]:
    return {
        'id': character.id,
        'name': character.name,
        'gender': character.gender,
        'race': character.race,
        'character_class': character.character_class,
        'level': character.level,
        'experience': character.experience,
        'current_hp': character.current_hp,
        'max_hp': character.max_hp,
        'armor_class': character.armor_class,
        'strength': character.strength,
        'dexterity': character.dexterity,
        'constitution': character.constitution,
        'intelligence': character.intelligence,
        'wisdom': character.wisdom,
        'charisma': character.charisma,
        'gold': character.gold,
        'silver': character.silver,
        'copper': character.copper,
        'platinum': character.platinum,
    }


def add_starting_equipment(character: Character) -> None:
    equipment = CLASS_EQUIPMENT.get((character.character_class or '').lower())
    if not equipment:
        return
    for item_list in equipment.values():
        for template in item_list:
            character.add_item(
                name=template.name,
                item_type=getattr(template.item_type, 'value', str(template.item_type)),
                description=template.description,
                weight=template.weight,
                value=template.value,
                rarity=getattr(template.rarity, 'value', str(template.rarity)),
                magical=template.magical,
                requires_attunement=template.requires_attunement,
                tags=template.tags,
                effects=[{'type': e['type'], 'value': e['value'], 'description': e['description']} for e in template.effects],
                damage=getattr(template, 'damage', None),
                damage_type=getattr(template, 'damage_type', None),
                weapon_properties=getattr(template, 'properties', []),
                enchantment_bonus=getattr(template, 'enchantment_bonus', 0),
                base_ac=getattr(template, 'base_ac', None),
                armor_type=getattr(template, 'armor_type', None),
                strength_req=getattr(template, 'strength_req', 0),
                stealth_disadvantage=getattr(template, 'stealth_disadvantage', False),
                uses=getattr(template, 'uses', None),
                max_uses=getattr(template, 'max_uses', None),
                charges=getattr(template, 'charges', None),
                max_charges=getattr(template, 'max_charges', None),
            )


@bp.route('/create_character', methods=['POST'])
def create_character():
    data = _payload()
    required = ['name', 'gender', 'race', 'class', 'strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
    missing = [field for field in required if field not in data]
    if missing:
        return jsonify({'error': f"Missing fields: {', '.join(missing)}"}), 400

    try:
        constitution = _to_int(data.get('constitution'))
        constitution_mod = (constitution - 10) // 2
        char_class = data['class']
        level = _to_int(data.get('level'), 1)
        max_hp = calculate_max_hp(char_class, constitution_mod, level)
        dexterity = _to_int(data.get('dexterity'))
        
        # Get current user ID from session
        user_id = session.get('user_id')
        
        new_character = Character(
            name=data['name'],
            gender=data['gender'],
            race=data['race'],
            character_class=char_class,
            level=level,
            experience=_to_int(data.get('experience')),
            max_hp=max_hp,
            current_hp=max_hp,
            armor_class=10 + ((dexterity - 10) // 2),
            strength=_to_int(data.get('strength')),
            dexterity=dexterity,
            constitution=constitution,
            intelligence=_to_int(data.get('intelligence')),
            wisdom=_to_int(data.get('wisdom')),
            charisma=_to_int(data.get('charisma')),
            gold=_to_int(data.get('gold'), 50),
            silver=_to_int(data.get('silver')),
            copper=_to_int(data.get('copper')),
            platinum=_to_int(data.get('platinum')),
            user_id=user_id,  # Associate character with current user
        )
    except ValueError:
        return jsonify({'error': 'Ability scores must be integers.'}), 400

    db.session.add(new_character)
    db.session.commit()

    if new_character.is_spellcaster():
        new_character.refresh_spell_slots()
        spell_manager = new_character.get_spell_manager()
        available_cantrips = spell_manager.get_available_spells(0)
        available_first = spell_manager.get_available_spells(1)
        cantrips_known = get_cantrips_known(char_class, level)
        spells_known = get_spells_known(char_class, level)
        starting_spells = []
        starting_spells.extend(available_cantrips[:cantrips_known])
        if spells_known > 0:
            starting_spells.extend(available_first[:spells_known])
        new_character.set_known_spells_list(starting_spells)
        new_character.set_prepared_spells_list(starting_spells)
        db.session.commit()

    add_starting_equipment(new_character)
    db.session.commit()

    return jsonify({'success': True, 'character': _serialize_character(new_character)})


@bp.route('/delete_character/<int:character_id>', methods=['POST'])
def delete_character(character_id: int):
    character = Character.query.get_or_404(character_id)
    db.session.delete(character)
    db.session.commit()
    return jsonify({'success': True})


@bp.route('/api/characters')
def api_characters():
    """Get characters for the current user, or all characters if not logged in (backward compatibility)."""
    user_id = session.get('user_id')
    
    if user_id:
        # Return only characters belonging to the logged-in user
        characters = Character.query.filter_by(user_id=user_id).all()
    else:
        # Backward compatibility: return characters without user_id (legacy characters)
        characters = Character.query.filter_by(user_id=None).all()
    
    return jsonify([_serialize_character(char) for char in characters])


@bp.route('/character/<int:character_id>/inventory')
def character_inventory(character_id: int):
    character = Character.query.get_or_404(character_id)
    equipped_items = Item.query.filter_by(character_id=character_id).filter(Item.equipped_slot.isnot(None)).all()
    carried_items = Item.query.filter_by(character_id=character_id).filter(Item.equipped_slot.is_(None)).all()
    equipment_slots = {slot.value: None for slot in EquipmentSlot}
    for item in equipped_items:
        equipment_slots[item.equipped_slot] = item.id
    return jsonify({
        'character_id': character.id,
        'equipped_items': [_serialize_item(item) for item in equipped_items],
        'carried_items': [_serialize_item(item) for item in carried_items],
        'equipment_slots': equipment_slots,
    })


@bp.route('/character/<int:character_id>/equip/<int:item_id>', methods=['POST'])
def equip_item(character_id: int, item_id: int):
    character = Character.query.get_or_404(character_id)
    data = _payload()
    slot = data.get('slot')
    if not slot:
        return jsonify({'success': False, 'message': 'slot is required'}), 400
    success, message = character.equip_item(item_id, slot)
    status = 200 if success else 400
    return jsonify({'success': success, 'message': message}), status


@bp.route('/character/<int:character_id>/unequip', methods=['POST'])
def unequip_item(character_id: int):
    character = Character.query.get_or_404(character_id)
    data = _payload()
    slot = data.get('slot')
    if not slot:
        return jsonify({'success': False, 'message': 'slot is required'}), 400
    success, message = character.unequip_item(slot)
    status = 200 if success else 400
    return jsonify({'success': success, 'message': message}), status


@bp.route('/character/<int:character_id>/add_item', methods=['GET', 'POST'])
def add_item_to_character(character_id: int):
    character = Character.query.get_or_404(character_id)
    if request.method == 'GET':
        return jsonify({'available_items': list(ALL_ITEMS.keys())})

    data = _payload()
    item_name = data.get('item_name')
    if not item_name:
        return jsonify({'success': False, 'message': 'item_name is required'}), 400

    if item_name in ALL_ITEMS:
        template = ALL_ITEMS[item_name]
        character.add_item(
            name=template.name,
            item_type=getattr(template.item_type, 'value', str(template.item_type)),
            description=template.description,
            weight=template.weight,
            value=template.value,
            rarity=getattr(template.rarity, 'value', str(template.rarity)),
            magical=template.magical,
            requires_attunement=template.requires_attunement,
            tags=template.tags,
            effects=[{'type': e['type'], 'value': e['value'], 'description': e['description']} for e in template.effects],
        )
    else:
        character.add_item(
            name=item_name,
            item_type=data.get('item_type', 'gear'),
            description=data.get('description', ''),
            weight=float(data.get('weight', 0)),
            value=int(data.get('value', 0)),
            rarity=data.get('rarity', 'common'),
            magical=bool(data.get('magical', False)),
            requires_attunement=bool(data.get('requires_attunement', False)),
            tags=data.get('tags', []),
            effects=data.get('effects', []),
        )
    db.session.commit()
    return jsonify({'success': True})


@bp.route('/character/<int:character_id>/spells')
def character_spells(character_id: int):
    character = Character.query.get_or_404(character_id)
    if not character.is_spellcaster():
        return jsonify({'character_id': character.id, 'is_spellcaster': False})
    spell_manager = character.get_spell_manager()
    available_spells = {level: spell_manager.get_available_spells(level) for level in range(0, 10)}
    return jsonify({
        'character_id': character.id,
        'character_name': character.name,
        'character_class': character.character_class,
        'level': character.level,
        'is_spellcaster': True,
        'max_slots': character.get_max_spell_slots(),
        'current_slots': character.get_current_spell_slots(),
        'known_spells': character.get_known_spells_list(),
        'prepared_spells': character.get_prepared_spells_list(),
        'available_spells': available_spells,
        'cantrips_known': get_cantrips_known(character.character_class, character.level),
        'spells_known': get_spells_known(character.character_class, character.level),
    })


@bp.route('/character/<int:character_id>/cast_spell', methods=['POST'])
def cast_spell(character_id: int):
    character = Character.query.get_or_404(character_id)
    data = _payload()
    spell_name = data.get('spell_name')
    spell_level = int(data.get('spell_level', 1))
    if not character.is_spellcaster():
        return jsonify({'error': 'Character cannot cast spells'}), 400
    if spell_name not in character.get_prepared_spells_list():
        return jsonify({'error': 'Spell not prepared'}), 400
    if spell_level == 0:
        return jsonify({'success': True, 'message': f'Cast {spell_name} (cantrip)'})
    if character.use_spell_slot(spell_level):
        db.session.commit()
        return jsonify({'success': True, 'message': f'Cast {spell_name}', 'current_slots': character.get_current_spell_slots()})
    return jsonify({'error': 'No spell slots available'}), 400


@bp.route('/character/<int:character_id>/long_rest', methods=['POST'])
def long_rest(character_id: int):
    character = Character.query.get_or_404(character_id)
    character.current_hp = character.max_hp
    if character.is_spellcaster():
        character.refresh_spell_slots()
    db.session.commit()
    return jsonify({'success': True, 'current_hp': character.current_hp, 'current_slots': character.get_current_spell_slots()})


DEFAULT_CHARACTER_NAME = 'Default Adventurer'


def ensure_default_character() -> None:
    if Character.query.filter_by(name=DEFAULT_CHARACTER_NAME).first():
        return
    abilities = {
        'strength': 15,
        'dexterity': 14,
        'constitution': 13,
        'intelligence': 12,
        'wisdom': 10,
        'charisma': 8,
    }
    constitution_mod = (abilities['constitution'] - 10) // 2
    max_hp = calculate_max_hp('fighter', constitution_mod, level=1)
    default_character = Character(
        name=DEFAULT_CHARACTER_NAME,
        gender='Unknown',
        race='Human',
        character_class='Fighter',
        level=1,
        experience=0,
        max_hp=max_hp,
        current_hp=max_hp,
        armor_class=10 + ((abilities['dexterity'] - 10) // 2),
        gold=50,
        silver=0,
        copper=0,
        platinum=0,
        **abilities,
    )
    db.session.add(default_character)
    db.session.commit()
    add_starting_equipment(default_character)
    db.session.commit()
