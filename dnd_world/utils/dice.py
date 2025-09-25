"""
Dice rolling utilities for D&D mechanics.

This module provides comprehensive dice rolling functionality following D&D 5e rules,
inspired by the py-dnd library architecture. It supports standard dice notation
(e.g., "3d6+2", "1d20") and includes specialized methods for character creation.
"""

import re
import random
from typing import List, Tuple, Optional, Union
from dataclasses import dataclass


@dataclass
class DiceResult:
    """
    Represents the result of a dice roll.
    
    Attributes:
        total: The final result after all modifiers
        rolls: List of individual die results
        modifier: Any modifier applied to the roll
        dice_notation: The original dice notation used
    """
    total: int
    rolls: List[int]
    modifier: int
    dice_notation: str
    
    def __str__(self):
        rolls_str = ", ".join(map(str, self.rolls))
        if self.modifier != 0:
            modifier_str = f" {'+' if self.modifier >= 0 else ''}{self.modifier}"
        else:
            modifier_str = ""
        return f"{self.dice_notation}: [{rolls_str}]{modifier_str} = {self.total}"


class DiceRoller:
    """
    Comprehensive dice rolling utility for D&D 5e mechanics.
    
    Supports standard dice notation parsing and specialized methods for
    character creation, combat, and other game mechanics.
    """
    
    # Regex pattern for dice notation (e.g., "3d6+2", "1d20-1", "2d8")
    DICE_PATTERN = re.compile(r'^(\d+)?d(\d+)([+-]\d+)?$', re.IGNORECASE)
    
    @classmethod
    def roll(cls, dice_notation: str) -> DiceResult:
        """
        Roll dice using standard D&D notation.
        
        Args:
            dice_notation: String like "3d6+2", "1d20", "4d6-1"
            
        Returns:
            DiceResult: Complete information about the roll
            
        Raises:
            ValueError: If dice notation is invalid
            
        Examples:
            >>> DiceRoller.roll("3d6+2")
            DiceResult(total=14, rolls=[4, 5, 3], modifier=2, dice_notation="3d6+2")
            
            >>> DiceRoller.roll("1d20")
            DiceResult(total=15, rolls=[15], modifier=0, dice_notation="1d20")
        """
        dice_notation = dice_notation.strip().replace(" ", "")
        match = cls.DICE_PATTERN.match(dice_notation)
        
        if not match:
            raise ValueError(f"Invalid dice notation: {dice_notation}")
        
        num_dice_str, die_size_str, modifier_str = match.groups()
        
        # Parse components
        num_dice = int(num_dice_str) if num_dice_str else 1
        die_size = int(die_size_str)
        modifier = int(modifier_str) if modifier_str else 0
        
        # Validate inputs
        if num_dice <= 0:
            raise ValueError("Number of dice must be positive")
        if die_size <= 0:
            raise ValueError("Die size must be positive")
        if num_dice > 100:  # Reasonable limit
            raise ValueError("Too many dice (maximum 100)")
        
        # Roll the dice
        rolls = [random.randint(1, die_size) for _ in range(num_dice)]
        total = sum(rolls) + modifier
        
        return DiceResult(
            total=total,
            rolls=rolls,
            modifier=modifier,
            dice_notation=dice_notation
        )
    
    @classmethod
    def roll_ability_score_4d6_drop_lowest(cls) -> DiceResult:
        """
        Roll an ability score using the standard 4d6 drop lowest method.
        
        This is the most common method for generating ability scores in D&D 5e.
        Roll 4d6, drop the lowest die, sum the remaining three.
        
        Returns:
            DiceResult: The result with the lowest die removed
        """
        # Roll 4d6
        all_rolls = [random.randint(1, 6) for _ in range(4)]
        
        # Drop the lowest
        all_rolls.sort()
        kept_rolls = all_rolls[1:]  # Remove the lowest (first after sorting)
        total = sum(kept_rolls)
        
        return DiceResult(
            total=total,
            rolls=kept_rolls,
            modifier=0,
            dice_notation=f"4d6 drop lowest (dropped: {all_rolls[0]})"
        )
    
    @classmethod
    def roll_full_ability_scores(cls) -> dict:
        """
        Generate a complete set of ability scores using 4d6 drop lowest.
        
        Returns:
            dict: Ability scores keyed by ability name
            
        Example:
            >>> DiceRoller.roll_full_ability_scores()
            {
                'strength': 15,
                'dexterity': 14,
                'constitution': 13,
                'intelligence': 12,
                'wisdom': 10,
                'charisma': 8
            }
        """
        abilities = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
        return {ability: cls.roll_ability_score_4d6_drop_lowest().total for ability in abilities}
    
    @classmethod
    def standard_array(cls) -> dict:
        """
        Return the D&D 5e standard array for ability scores.
        
        Returns:
            dict: The standard array values
        """
        abilities = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
        standard_values = [15, 14, 13, 12, 10, 8]
        
        # Note: In a real implementation, you'd let the player assign these
        # For now, we'll assign them in order
        return dict(zip(abilities, standard_values))
    
    @classmethod
    def point_buy_base(cls) -> dict:
        """
        Return the base scores for point buy system.
        
        In point buy, all abilities start at 8 and you have 27 points to spend.
        This returns the starting values.
        
        Returns:
            dict: All abilities starting at 8
        """
        abilities = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
        return {ability: 8 for ability in abilities}
    
    @classmethod
    def roll_hit_points(cls, hit_die_size: int, constitution_modifier: int) -> int:
        """
        Roll hit points for leveling up.
        
        Args:
            hit_die_size: Size of the class's hit die (e.g., 8 for Rogue, 12 for Barbarian)
            constitution_modifier: Character's Constitution modifier
            
        Returns:
            int: Hit points gained (minimum 1)
        """
        roll = random.randint(1, hit_die_size)
        hp_gain = roll + constitution_modifier
        return max(1, hp_gain)  # Minimum 1 HP per level
    
    @classmethod
    def roll_attack(cls, attack_bonus: int) -> DiceResult:
        """
        Roll a d20 attack roll with bonus.
        
        Args:
            attack_bonus: Total attack bonus to add
            
        Returns:
            DiceResult: The attack roll result
        """
        return cls.roll(f"1d20{'+' if attack_bonus >= 0 else ''}{attack_bonus}")
    
    @classmethod
    def roll_damage(cls, damage_dice: str) -> DiceResult:
        """
        Roll damage dice.
        
        Args:
            damage_dice: Damage notation like "1d6+3" or "2d8"
            
        Returns:
            DiceResult: The damage roll result
        """
        return cls.roll(damage_dice)
    
    @classmethod
    def roll_saving_throw(cls, ability_modifier: int, proficiency_bonus: int = 0) -> DiceResult:
        """
        Roll a saving throw.
        
        Args:
            ability_modifier: Relevant ability modifier
            proficiency_bonus: Proficiency bonus if proficient (0 if not)
            
        Returns:
            DiceResult: The saving throw result
        """
        total_bonus = ability_modifier + proficiency_bonus
        return cls.roll(f"1d20{'+' if total_bonus >= 0 else ''}{total_bonus}")
    
    @classmethod
    def roll_skill_check(cls, ability_modifier: int, proficiency_bonus: int = 0, expertise: bool = False) -> DiceResult:
        """
        Roll a skill check.
        
        Args:
            ability_modifier: Relevant ability modifier
            proficiency_bonus: Proficiency bonus if proficient (0 if not)
            expertise: Whether the character has expertise (doubles proficiency)
            
        Returns:
            DiceResult: The skill check result
        """
        prof_bonus = proficiency_bonus * (2 if expertise else 1)
        total_bonus = ability_modifier + prof_bonus
        return cls.roll(f"1d20{'+' if total_bonus >= 0 else ''}{total_bonus}")


def calculate_ability_modifier(ability_score: int) -> int:
    """
    Calculate the ability modifier for a given ability score.
    
    Args:
        ability_score: The ability score (1-20+ typically)
        
    Returns:
        int: The ability modifier
        
    Examples:
        >>> calculate_ability_modifier(10)
        0
        >>> calculate_ability_modifier(16)
        3
        >>> calculate_ability_modifier(8)
        -1
    """
    return (ability_score - 10) // 2


def calculate_proficiency_bonus(level: int) -> int:
    """
    Calculate proficiency bonus based on character level.
    
    Args:
        level: Character level (1-20)
        
    Returns:
        int: Proficiency bonus
    """
    if level < 1:
        return 0
    elif level <= 4:
        return 2
    elif level <= 8:
        return 3
    elif level <= 12:
        return 4
    elif level <= 16:
        return 5
    else:
        return 6


# Racial ability score bonuses from D&D 5e
RACIAL_BONUSES = {
    'human': {'strength': 1, 'dexterity': 1, 'constitution': 1, 'intelligence': 1, 'wisdom': 1, 'charisma': 1},
    'elf': {'dexterity': 2},
    'dwarf': {'constitution': 2},
    'halfling': {'dexterity': 2},
    'dragonborn': {'strength': 2, 'charisma': 1},
    'gnome': {'intelligence': 2},
    'half-elf': {'charisma': 2, 'choice_two': 1},  # Plus two abilities of choice
    'half-orc': {'strength': 2, 'constitution': 1},
    'tiefling': {'intelligence': 1, 'charisma': 2},
}


def apply_racial_bonuses(base_scores: dict, race: str) -> dict:
    """
    Apply racial ability score bonuses to base ability scores.
    
    Args:
        base_scores: Dictionary of base ability scores
        race: Character race
        
    Returns:
        dict: Ability scores with racial bonuses applied
        
    Note:
        This is a simplified implementation. Some races have choice-based bonuses
        that would require user input in a full implementation.
    """
    modified_scores = base_scores.copy()
    bonuses = RACIAL_BONUSES.get(race.lower(), {})
    
    for ability, bonus in bonuses.items():
        if ability == 'choice_two':
            # For races like half-elf, this would need user choice
            # For now, apply to highest non-charisma stats
            continue
        if ability in modified_scores:
            modified_scores[ability] += bonus
    
    return modified_scores