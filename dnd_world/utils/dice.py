"""
Dice rolling utilities and D&D mechanics
"""

# Copy the existing dice_utils.py content
import random
import re

class DiceRoller:
    """
    Handles dice rolling for D&D mechanics with D&D-specific features.
    
    Supports standard dice notation (e.g., "1d20", "3d6") and includes
    critical hit mechanics, advantage/disadvantage, and special D&D rules.
    """
    
    @staticmethod
    def roll(notation):
        """
        Roll dice using standard notation.
        
        Args:
            notation (str): Dice notation like "1d20", "3d6+2", "2d8-1"
            
        Returns:
            int: The total result of the dice roll
        """
        # Parse dice notation
        pattern = r'(\d+)d(\d+)([+-]\d+)?'
        match = re.match(pattern, notation.replace(' ', ''))
        
        if not match:
            try:
                # If it's just a number, return it
                return int(notation)
            except:
                raise ValueError(f"Invalid dice notation: {notation}")
        
        num_dice = int(match.group(1))
        die_size = int(match.group(2))
        modifier = int(match.group(3)) if match.group(3) else 0
        
        # Roll the dice
        total = sum(random.randint(1, die_size) for _ in range(num_dice))
        return total + modifier
    
    @staticmethod
    def roll_with_advantage():
        """Roll 1d20 with advantage (roll twice, take higher)."""
        roll1 = random.randint(1, 20)
        roll2 = random.randint(1, 20)
        return max(roll1, roll2)
    
    @staticmethod
    def roll_with_disadvantage():
        """Roll 1d20 with disadvantage (roll twice, take lower)."""
        roll1 = random.randint(1, 20)
        roll2 = random.randint(1, 20)
        return min(roll1, roll2)
    
    @staticmethod
    def roll_ability_scores():
        """
        Roll ability scores using 4d6 drop lowest method.
        
        Returns:
            list: Six ability scores rolled using the standard method
        """
        scores = []
        for _ in range(6):
            # Roll 4d6, drop lowest
            rolls = [random.randint(1, 6) for _ in range(4)]
            rolls.sort(reverse=True)
            score = sum(rolls[:3])  # Take the highest 3
            scores.append(score)
        return scores
    
    @staticmethod
    def roll_hit_points(hit_die, constitution_modifier, level=1):
        """
        Roll hit points for a character.
        
        Args:
            hit_die (int): Size of the hit die (8 for d8, 10 for d10, etc.)
            constitution_modifier (int): Constitution modifier
            level (int): Character level
            
        Returns:
            int: Total hit points
        """
        if level == 1:
            # Max HP at first level
            return hit_die + constitution_modifier
        
        # Roll for additional levels
        hp = hit_die + constitution_modifier  # First level max
        for _ in range(level - 1):
            roll = random.randint(1, hit_die)
            hp += roll + constitution_modifier
        
        return max(hp, level)  # Minimum 1 HP per level
    
    @staticmethod
    def roll_initiative(dexterity_modifier):
        """
        Roll initiative (1d20 + Dex modifier).
        
        Args:
            dexterity_modifier (int): Dexterity modifier
            
        Returns:
            int: Initiative result
        """
        return random.randint(1, 20) + dexterity_modifier
    
    @staticmethod
    def is_critical_hit(roll):
        """
        Check if a d20 roll is a critical hit (natural 20).
        
        Args:
            roll (int): The d20 roll result
            
        Returns:
            bool: True if it's a critical hit
        """
        return roll == 20
    
    @staticmethod
    def is_critical_miss(roll):
        """
        Check if a d20 roll is a critical miss (natural 1).
        
        Args:
            roll (int): The d20 roll result
            
        Returns:
            bool: True if it's a critical miss
        """
        return roll == 1

def calculate_ability_modifier(ability_score):
    """
    Calculate D&D ability modifier from ability score.
    
    Args:
        ability_score (int): The ability score (usually 1-30)
        
    Returns:
        int: The ability modifier
    """
    return (ability_score - 10) // 2

def apply_racial_bonuses(race, ability_scores):
    """
    Apply racial ability score bonuses according to D&D 5e rules.
    
    Args:
        race (str): Character race
        ability_scores (dict): Dictionary with ability scores
        
    Returns:
        dict: Updated ability scores with racial bonuses applied
    """
    # Copy the scores to avoid modifying the original
    updated_scores = ability_scores.copy()
    
    racial_bonuses = {
        'human': {'strength': 1, 'dexterity': 1, 'constitution': 1, 
                 'intelligence': 1, 'wisdom': 1, 'charisma': 1},
        'elf': {'dexterity': 2},
        'dwarf': {'constitution': 2},
        'halfling': {'dexterity': 2},
        'dragonborn': {'strength': 2, 'charisma': 1},
        'gnome': {'intelligence': 2},
        'half-elf': {'charisma': 2},  # Plus +1 to two different abilities
        'half-orc': {'strength': 2, 'constitution': 1},
        'tiefling': {'intelligence': 1, 'charisma': 2}
    }
    
    bonuses = racial_bonuses.get(race.lower(), {})
    for ability, bonus in bonuses.items():
        if ability in updated_scores:
            updated_scores[ability] += bonus
    
    return updated_scores

def get_proficiency_bonus(level):
    """
    Get proficiency bonus based on character level.
    
    Args:
        level (int): Character level (1-20)
        
    Returns:
        int: Proficiency bonus
    """
    if level <= 4:
        return 2
    elif level <= 8:
        return 3
    elif level <= 12:
        return 4
    elif level <= 16:
        return 5
    else:
        return 6