# combat.py

import random
import json
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class AttackResult:
    """Result of an attack action."""
    hit: bool
    attack_roll: int
    damage_roll: int
    damage_type: str
    critical: bool = False
    damage_dealt: int = 0

@dataclass  
class DamageRoll:
    """Represents a damage roll."""
    dice_count: int
    dice_size: int
    modifier: int = 0
    damage_type: str = "bludgeoning"

class CombatEngine:
    """Core combat mechanics following D&D 5e rules."""
    
    @staticmethod
    def roll_d20() -> int:
        """Roll a d20."""
        return random.randint(1, 20)
    
    @staticmethod
    def roll_dice(count: int, size: int, modifier: int = 0) -> int:
        """Roll dice and return the total."""
        total = sum(random.randint(1, size) for _ in range(count))
        return total + modifier
    
    @staticmethod
    def parse_damage_dice(damage_string: str) -> DamageRoll:
        """Parse damage dice string like '1d6' or '2d8+3'."""
        if not damage_string:
            return DamageRoll(1, 4, 0)  # Default to 1d4
        
        # Handle format like "1d6" or "2d8+3"
        damage_string = damage_string.strip().lower()
        modifier = 0
        
        # Extract modifier
        if '+' in damage_string:
            dice_part, mod_part = damage_string.split('+')
            modifier = int(mod_part.strip())
        elif '-' in damage_string and damage_string.count('-') == 1:
            dice_part, mod_part = damage_string.split('-')
            modifier = -int(mod_part.strip())
        else:
            dice_part = damage_string
        
        # Parse dice part
        if 'd' in dice_part:
            count_str, size_str = dice_part.split('d')
            count = int(count_str.strip()) if count_str.strip() else 1
            size = int(size_str.strip())
        else:
            # Flat damage value
            count = 0
            size = 1
            modifier = int(dice_part.strip())
        
        return DamageRoll(count, size, modifier)
    
    @staticmethod
    def roll_initiative(dex_modifier: int) -> int:
        """Roll initiative (d20 + dex modifier)."""
        return CombatEngine.roll_d20() + dex_modifier
    
    @staticmethod
    def make_attack_roll(attack_bonus: int, target_ac: int) -> Tuple[bool, int, bool]:
        """
        Make an attack roll.
        
        Returns:
            Tuple of (hit, attack_roll, critical)
        """
        roll = CombatEngine.roll_d20()
        attack_roll = roll + attack_bonus
        
        # Critical hit on natural 20
        critical = (roll == 20)
        
        # Critical miss on natural 1 (always misses)
        if roll == 1:
            return False, attack_roll, False
        
        # Critical hit always hits
        if critical:
            return True, attack_roll, critical
        
        # Normal hit/miss
        hit = attack_roll >= target_ac
        return hit, attack_roll, critical
    
    @staticmethod
    def calculate_weapon_attack_bonus(character, weapon) -> int:
        """Calculate attack bonus for a weapon."""
        # Base proficiency bonus by level
        proficiency_bonus = CombatEngine.get_proficiency_bonus(character.level)
        
        # Use STR for melee, DEX for ranged (simplified)
        if weapon and hasattr(weapon, 'weapon_properties'):
            # Check for finesse property (allows DEX for melee)
            properties = weapon.weapon_properties or ""
            if "finesse" in properties.lower():
                ability_mod = max(character.strength_modifier, character.dexterity_modifier)
            elif "ranged" in properties.lower() or weapon.item_type == "ranged":
                ability_mod = character.dexterity_modifier
            else:
                ability_mod = character.strength_modifier
        else:
            # Default to STR for unknown weapons
            ability_mod = character.strength_modifier
        
        # Enchantment bonus
        enchantment = getattr(weapon, 'enchantment_bonus', 0) if weapon else 0
        
        return proficiency_bonus + ability_mod + enchantment
    
    @staticmethod
    def calculate_weapon_damage(character, weapon, critical: bool = False) -> DamageRoll:
        """Calculate damage for a weapon attack."""
        if not weapon or not weapon.damage:
            # Unarmed strike: 1 + STR modifier
            return DamageRoll(1, 1, character.strength_modifier, "bludgeoning")
        
        damage_roll = CombatEngine.parse_damage_dice(weapon.damage)
        
        # Add ability modifier
        if hasattr(weapon, 'weapon_properties') and weapon.weapon_properties:
            properties = weapon.weapon_properties.lower()
            if "finesse" in properties:
                ability_mod = max(character.strength_modifier, character.dexterity_modifier)
            elif "ranged" in properties:
                ability_mod = character.dexterity_modifier
            else:
                ability_mod = character.strength_modifier
        else:
            ability_mod = character.strength_modifier
        
        damage_roll.modifier += ability_mod
        
        # Add enchantment bonus
        enchantment = getattr(weapon, 'enchantment_bonus', 0)
        damage_roll.modifier += enchantment
        
        # Critical hit: double dice
        if critical:
            damage_roll.dice_count *= 2
        
        # Set damage type
        if hasattr(weapon, 'damage_type') and weapon.damage_type:
            damage_roll.damage_type = weapon.damage_type
        
        return damage_roll
    
    @staticmethod
    def get_proficiency_bonus(level: int) -> int:
        """Get proficiency bonus by character level."""
        if level >= 17:
            return 6
        elif level >= 13:
            return 5
        elif level >= 9:
            return 4
        elif level >= 5:
            return 3
        else:
            return 2
    
    @staticmethod
    def make_saving_throw(ability_modifier: int, proficiency: bool, proficiency_bonus: int, dc: int) -> Tuple[bool, int]:
        """
        Make a saving throw.
        
        Returns:
            Tuple of (success, roll_result)
        """
        roll = CombatEngine.roll_d20()
        bonus = ability_modifier + (proficiency_bonus if proficiency else 0)
        total = roll + bonus
        
        return total >= dc, total
    
    @staticmethod
    def make_death_saving_throw() -> Tuple[bool, bool, int]:
        """
        Make a death saving throw.
        
        Returns:
            Tuple of (success, critical, roll)
        """
        roll = CombatEngine.roll_d20()
        
        if roll == 20:
            return True, True, roll  # Critical success - regain 1 HP
        elif roll == 1:
            return False, True, roll  # Critical failure - counts as 2 failures
        else:
            return roll >= 10, False, roll
    
    @staticmethod
    def calculate_ac(character, armor=None) -> int:
        """Calculate armor class for a character."""
        base_ac = 10
        dex_mod = character.dexterity_modifier
        
        if armor:
            if armor.armor_type == "light":
                return armor.base_ac + dex_mod
            elif armor.armor_type == "medium":
                return armor.base_ac + min(dex_mod, 2)
            elif armor.armor_type == "heavy":
                return armor.base_ac
        
        # No armor - base 10 + DEX
        return base_ac + dex_mod

class CombatManager:
    """High-level combat management."""
    
    def __init__(self, app_context):
        self.app = app_context
    
    def start_combat(self, combat_name: str, character_ids: List[int]) -> 'Combat':
        """Start a new combat encounter with given characters."""
        from app import Combat, Combatant, Character, db
        
        combat = Combat(name=combat_name)
        db.session.add(combat)
        db.session.commit()
        
        # Add combatants and roll initiative
        for char_id in character_ids:
            character = Character.query.get(char_id)
            if character:
                initiative = CombatEngine.roll_initiative(character.dexterity_modifier)
                
                combatant = Combatant(
                    combat_id=combat.id,
                    character_id=char_id,
                    initiative=initiative,
                    current_hp=character.current_hp
                )
                db.session.add(combatant)
        
        db.session.commit()
        return combat
    
    def make_weapon_attack(self, attacker_id: int, target_id: int, weapon_id: int = None) -> AttackResult:
        """Execute a weapon attack between combatants."""
        from app import Combatant, Item, db
        
        attacker = Combatant.query.get(attacker_id)
        target = Combatant.query.get(target_id)
        
        if not attacker or not target:
            raise ValueError("Invalid combatant IDs")
        
        # Get weapon
        weapon = None
        if weapon_id:
            weapon = Item.query.get(weapon_id)
            if not weapon or weapon.character_id != attacker.character_id:
                raise ValueError("Invalid weapon")
        
        # Calculate attack
        attack_bonus = CombatEngine.calculate_weapon_attack_bonus(attacker.character, weapon)
        target_ac = CombatEngine.calculate_ac(target.character)  # TODO: Include armor from equipped items
        
        hit, attack_roll, critical = CombatEngine.make_attack_roll(attack_bonus, target_ac)
        
        damage_dealt = 0
        damage_roll = 0
        damage_type = "bludgeoning"
        
        if hit:
            damage_info = CombatEngine.calculate_weapon_damage(attacker.character, weapon, critical)
            damage_roll = CombatEngine.roll_dice(damage_info.dice_count, damage_info.dice_size, damage_info.modifier)
            damage_type = damage_info.damage_type
            
            # Apply damage
            if damage_roll > 0:
                target.apply_damage(damage_roll)
                damage_dealt = damage_roll
        
        # Use action
        attacker.has_action = False
        db.session.commit()
        
        return AttackResult(
            hit=hit,
            attack_roll=attack_roll,
            damage_roll=damage_roll,
            damage_type=damage_type,
            critical=critical,
            damage_dealt=damage_dealt
        )
    
    def end_turn(self, combat_id: int) -> None:
        """End current combatant's turn and advance to next."""
        from app import Combat, db
        
        combat = Combat.query.get(combat_id)
        if combat:
            current = combat.current_combatant
            if current:
                current.reset_turn_actions()
            
            combat.next_turn()
            
            # Reset reactions for the new turn
            new_current = combat.current_combatant
            if new_current:
                new_current.has_reaction = True
                db.session.commit()