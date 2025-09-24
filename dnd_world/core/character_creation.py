"""
Character Creation System
"""

from ..utils.dice import DiceRoller, apply_racial_bonuses, calculate_ability_modifier
from ..models.character import Character
from ..utils.database import db
from items import CLASS_EQUIPMENT

class CharacterCreator:
    """Handles character creation logic"""
    
    # Hit dice by class
    HIT_DICE = {
        'barbarian': 12,
        'fighter': 10,
        'paladin': 10,
        'ranger': 10,
        'bard': 8,
        'cleric': 8,
        'druid': 8,
        'monk': 8,
        'rogue': 8,
        'warlock': 8,
        'sorcerer': 6,
        'wizard': 6
    }
    
    @classmethod
    def create_character(cls, name, race, character_class, gender, ability_scores=None):
        """
        Create a new character with proper D&D mechanics.
        
        Args:
            name (str): Character name
            race (str): Character race
            character_class (str): Character class
            gender (str): Character gender
            ability_scores (dict, optional): Custom ability scores
            
        Returns:
            Character: The created character
        """
        # Generate ability scores if not provided
        if ability_scores is None:
            scores = DiceRoller.roll_ability_scores()
            ability_scores = {
                'strength': scores[0],
                'dexterity': scores[1],
                'constitution': scores[2],
                'intelligence': scores[3],
                'wisdom': scores[4],
                'charisma': scores[5]
            }
        
        # Apply racial bonuses
        ability_scores = apply_racial_bonuses(race, ability_scores)
        
        # Calculate constitution modifier for HP
        constitution_mod = calculate_ability_modifier(ability_scores['constitution'])
        
        # Calculate max HP
        hit_die = cls.HIT_DICE.get(character_class.lower(), 8)
        max_hp = cls.calculate_max_hp(character_class, constitution_mod, level=1)
        
        # Calculate starting AC (10 + Dex modifier)
        dex_mod = calculate_ability_modifier(ability_scores['dexterity'])
        base_ac = 10 + dex_mod
        
        # Create character
        character = Character(
            name=name,
            race=race,
            character_class=character_class,
            gender=gender,
            level=1,
            experience=0,
            max_hp=max_hp,
            current_hp=max_hp,
            armor_class=base_ac,
            strength=ability_scores['strength'],
            dexterity=ability_scores['dexterity'],
            constitution=ability_scores['constitution'],
            intelligence=ability_scores['intelligence'],
            wisdom=ability_scores['wisdom'],
            charisma=ability_scores['charisma'],
            # Starting currency (random or class-based)
            gold=DiceRoller.roll("4d4") * 10  # Basic starting gold
        )
        
        # Save to database
        db.session.add(character)
        db.session.commit()
        
        # Add starting equipment
        cls.add_starting_equipment(character)
        
        return character
    
    @classmethod
    def calculate_max_hp(cls, char_class, constitution_mod, level=1):
        """
        Calculate maximum HP for a character.
        
        Args:
            char_class (str): Character class
            constitution_mod (int): Constitution modifier
            level (int): Character level
            
        Returns:
            int: Maximum hit points
        """
        hit_die = cls.HIT_DICE.get(char_class.lower(), 8)
        
        if level == 1:
            # Maximum HP at first level
            return hit_die + constitution_mod
        else:
            # Roll for additional levels
            return DiceRoller.roll_hit_points(hit_die, constitution_mod, level)
    
    @classmethod
    def add_starting_equipment(cls, character):
        """
        Add enhanced starting equipment based on character class.
        
        Args:
            character (Character): The character to equip
        """
        class_equipment = CLASS_EQUIPMENT.get(character.character_class.lower())
        if not class_equipment:
            return
        
        # Add gear items
        for item_template in class_equipment.get('gear', []):
            character.add_item(
                name=item_template.name,
                item_type='gear',
                description=item_template.description,
                weight=item_template.weight,
                value=getattr(item_template, 'cost', getattr(item_template, 'value', 0))
            )
        
        # Add weapons
        for weapon_template in class_equipment.get('weapons', []):
            character.add_item(
                name=weapon_template.name,
                item_type='weapon',
                description=weapon_template.description,
                weight=weapon_template.weight,
                value=getattr(weapon_template, 'cost', getattr(weapon_template, 'value', 0)),
                damage=getattr(weapon_template, 'damage', ''),
                damage_type=getattr(weapon_template, 'damage_type', ''),
                weapon_properties=getattr(weapon_template, 'properties', [])
            )
        
        # Add armor
        for armor_template in class_equipment.get('armor', []):
            character.add_item(
                name=armor_template.name,
                item_type='armor',
                description=armor_template.description,
                weight=armor_template.weight,
                value=getattr(armor_template, 'cost', getattr(armor_template, 'value', 0)),
                base_ac=getattr(armor_template, 'ac', 0),
                armor_type=getattr(armor_template, 'armor_type', ''),
                strength_req=getattr(armor_template, 'strength_req', 0),
                stealth_disadvantage=getattr(armor_template, 'stealth_disadvantage', False)
            )
        
        db.session.commit()
    
    @classmethod
    def level_up_character(cls, character):
        """
        Level up a character with proper mechanics.
        
        Args:
            character (Character): The character to level up
        """
        character.level += 1
        
        # Roll for additional HP
        hit_die = cls.HIT_DICE.get(character.character_class.lower(), 8)
        additional_hp = DiceRoller.roll(f"1d{hit_die}") + character.constitution_modifier
        additional_hp = max(additional_hp, 1)  # Minimum 1 HP per level
        
        character.max_hp += additional_hp
        character.current_hp += additional_hp  # Heal to full on level up
        
        # Refresh spell slots if spellcaster
        if character.is_spellcaster():
            character.refresh_spell_slots()
        
        db.session.commit()