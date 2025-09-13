# enemies.py

"""
Standard D&D 5e monsters and enemies for combat encounters.

This module contains definitions for common D&D monsters that can be 
used in combat encounters, following D&D 5e statistics and abilities.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum

class CreatureType(Enum):
    """D&D 5e creature types."""
    ABERRATION = "aberration"
    BEAST = "beast"
    CELESTIAL = "celestial"
    CONSTRUCT = "construct"
    DRAGON = "dragon"
    ELEMENTAL = "elemental"
    FEY = "fey"
    FIEND = "fiend"
    GIANT = "giant"
    HUMANOID = "humanoid"
    MONSTROSITY = "monstrosity"
    OOZE = "ooze"
    PLANT = "plant"
    UNDEAD = "undead"

class Size(Enum):
    """D&D 5e creature sizes."""
    TINY = "tiny"
    SMALL = "small" 
    MEDIUM = "medium"
    LARGE = "large"
    HUGE = "huge"
    GARGANTUAN = "gargantuan"

@dataclass
class Action:
    """Represents a creature action."""
    name: str
    description: str
    attack_bonus: int = 0
    damage_dice: str = ""
    damage_type: str = ""
    range: int = 5  # in feet
    recharge: Optional[str] = None  # e.g., "5-6" for recharge on 5 or 6

@dataclass
class Enemy:
    """Represents a D&D 5e monster/enemy."""
    name: str
    size: Size
    creature_type: CreatureType
    armor_class: int
    hit_points: int
    speed: int  # feet per round
    
    # Ability scores
    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    wisdom: int
    charisma: int
    
    # Challenge rating
    challenge_rating: float
    experience_points: int
    
    # Proficiencies and resistances
    saving_throws: Dict[str, int] = None  # e.g., {"dex": 3, "wis": 2}
    skills: Dict[str, int] = None  # e.g., {"stealth": 4, "perception": 2}
    damage_resistances: List[str] = None
    damage_immunities: List[str] = None
    condition_immunities: List[str] = None
    
    # Senses
    passive_perception: int = 10
    darkvision: int = 0  # in feet
    
    # Languages
    languages: List[str] = None
    
    # Actions
    actions: List[Action] = None
    
    # Special abilities
    special_abilities: List[str] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.saving_throws is None:
            self.saving_throws = {}
        if self.skills is None:
            self.skills = {}
        if self.damage_resistances is None:
            self.damage_resistances = []
        if self.damage_immunities is None:
            self.damage_immunities = []
        if self.condition_immunities is None:
            self.condition_immunities = []
        if self.languages is None:
            self.languages = []
        if self.actions is None:
            self.actions = []
        if self.special_abilities is None:
            self.special_abilities = []
    
    @property
    def strength_modifier(self):
        """Calculate strength modifier."""
        return (self.strength - 10) // 2
    
    @property
    def dexterity_modifier(self):
        """Calculate dexterity modifier."""
        return (self.dexterity - 10) // 2
    
    @property
    def constitution_modifier(self):
        """Calculate constitution modifier."""
        return (self.constitution - 10) // 2
    
    @property
    def intelligence_modifier(self):
        """Calculate intelligence modifier."""
        return (self.intelligence - 10) // 2
    
    @property
    def wisdom_modifier(self):
        """Calculate wisdom modifier."""
        return (self.wisdom - 10) // 2
    
    @property
    def charisma_modifier(self):
        """Calculate charisma modifier."""
        return (self.charisma - 10) // 2

# Standard D&D 5e Enemies
STANDARD_ENEMIES = {
    'goblin': Enemy(
        name="Goblin",
        size=Size.SMALL,
        creature_type=CreatureType.HUMANOID,
        armor_class=15,  # Leather armor + shield
        hit_points=7,
        speed=30,
        strength=8,
        dexterity=14,
        constitution=10,
        intelligence=10,
        wisdom=8,
        charisma=8,
        challenge_rating=0.25,
        experience_points=50,
        skills={"stealth": 6},
        passive_perception=9,
        darkvision=60,
        languages=["Common", "Goblin"],
        actions=[
            Action(
                name="Scimitar",
                description="Melee Weapon Attack",
                attack_bonus=4,
                damage_dice="1d6+2",
                damage_type="slashing",
                range=5
            ),
            Action(
                name="Shortbow",
                description="Ranged Weapon Attack", 
                attack_bonus=4,
                damage_dice="1d6+2",
                damage_type="piercing",
                range=150
            )
        ],
        special_abilities=["Nimble Escape: The goblin can take the Disengage or Hide action as a bonus action on each of its turns."]
    ),
    
    'orc': Enemy(
        name="Orc",
        size=Size.MEDIUM,
        creature_type=CreatureType.HUMANOID,
        armor_class=13,  # Hide armor
        hit_points=15,
        speed=30,
        strength=16,
        dexterity=12,
        constitution=13,
        intelligence=7,
        wisdom=11,
        charisma=10,
        challenge_rating=0.5,
        experience_points=100,
        skills={"intimidation": 2},
        passive_perception=10,
        darkvision=60,
        languages=["Common", "Orc"],
        actions=[
            Action(
                name="Greataxe",
                description="Melee Weapon Attack",
                attack_bonus=5,
                damage_dice="1d12+3",
                damage_type="slashing",
                range=5
            ),
            Action(
                name="Javelin",
                description="Melee or Ranged Weapon Attack",
                attack_bonus=5,
                damage_dice="1d6+3",
                damage_type="piercing",
                range=30
            )
        ],
        special_abilities=["Aggressive: As a bonus action, the orc can move up to its speed toward a hostile creature that it can see."]
    ),
    
    'skeleton': Enemy(
        name="Skeleton",
        size=Size.MEDIUM,
        creature_type=CreatureType.UNDEAD,
        armor_class=13,  # Armor scraps
        hit_points=13,
        speed=30,
        strength=10,
        dexterity=14,
        constitution=15,
        intelligence=6,
        wisdom=8,
        charisma=5,
        challenge_rating=0.25,
        experience_points=50,
        damage_vulnerabilities=["bludgeoning"],
        damage_immunities=["poison"],
        condition_immunities=["exhaustion", "poisoned"],
        passive_perception=9,
        darkvision=60,
        languages=["understands languages it knew in life but can't speak"],
        actions=[
            Action(
                name="Shortsword",
                description="Melee Weapon Attack",
                attack_bonus=4,
                damage_dice="1d6+2",
                damage_type="piercing",
                range=5
            ),
            Action(
                name="Shortbow",
                description="Ranged Weapon Attack",
                attack_bonus=4,
                damage_dice="1d6+2", 
                damage_type="piercing",
                range=80
            )
        ]
    ),
    
    'wolf': Enemy(
        name="Wolf",
        size=Size.MEDIUM,
        creature_type=CreatureType.BEAST,
        armor_class=13,  # Natural armor
        hit_points=11,
        speed=40,
        strength=12,
        dexterity=15,
        constitution=12,
        intelligence=3,
        wisdom=12,
        charisma=6,
        challenge_rating=0.25,
        experience_points=50,
        skills={"perception": 3, "stealth": 4},
        passive_perception=13,
        languages=[],
        actions=[
            Action(
                name="Bite",
                description="Melee Weapon Attack",
                attack_bonus=4,
                damage_dice="2d4+2",
                damage_type="piercing",
                range=5
            )
        ],
        special_abilities=[
            "Keen Hearing and Smell: The wolf has advantage on Wisdom (Perception) checks that rely on hearing or smell.",
            "Pack Tactics: The wolf has advantage on an attack roll against a creature if at least one of the wolf's allies is within 5 feet of the creature and the ally isn't incapacitated."
        ]
    ),
    
    'kobold': Enemy(
        name="Kobold",
        size=Size.SMALL,
        creature_type=CreatureType.HUMANOID,
        armor_class=12,  # Natural armor
        hit_points=5,
        speed=30,
        strength=7,
        dexterity=15,
        constitution=9,
        intelligence=8,
        wisdom=7,
        charisma=8,
        challenge_rating=0.125,
        experience_points=25,
        passive_perception=8,
        darkvision=60,
        languages=["Common", "Draconic"],
        actions=[
            Action(
                name="Dagger",
                description="Melee Weapon Attack",
                attack_bonus=4,
                damage_dice="1d4+2",
                damage_type="piercing",
                range=5
            ),
            Action(
                name="Sling",
                description="Ranged Weapon Attack",
                attack_bonus=4,
                damage_dice="1d4+2",
                damage_type="bludgeoning",
                range=30
            )
        ],
        special_abilities=[
            "Sunlight Sensitivity: While in sunlight, the kobold has disadvantage on attack rolls, as well as on Wisdom (Perception) checks that rely on sight.",
            "Pack Tactics: The kobold has advantage on an attack roll against a creature if at least one of the kobold's allies is within 5 feet of the creature and the ally isn't incapacitated."
        ]
    ),
    
    'bandit': Enemy(
        name="Bandit",
        size=Size.MEDIUM,
        creature_type=CreatureType.HUMANOID,
        armor_class=12,  # Leather armor
        hit_points=11,
        speed=30,
        strength=11,
        dexterity=12,
        constitution=12,
        intelligence=10,
        wisdom=10,
        charisma=10,
        challenge_rating=0.125,
        experience_points=25,
        passive_perception=10,
        languages=["Common"],
        actions=[
            Action(
                name="Scimitar",
                description="Melee Weapon Attack",
                attack_bonus=3,
                damage_dice="1d6+1",
                damage_type="slashing",
                range=5
            ),
            Action(
                name="Light Crossbow",
                description="Ranged Weapon Attack",
                attack_bonus=3,
                damage_dice="1d8+1",
                damage_type="piercing",
                range=80
            )
        ]
    )
}

def get_enemy_by_name(name: str) -> Optional[Enemy]:
    """Get an enemy by name."""
    return STANDARD_ENEMIES.get(name.lower())

def get_enemies_by_cr(challenge_rating: float) -> List[Enemy]:
    """Get all enemies with the specified challenge rating."""
    return [enemy for enemy in STANDARD_ENEMIES.values() if enemy.challenge_rating == challenge_rating]

def get_random_enemy_for_level(party_level: int) -> Enemy:
    """Get a random enemy appropriate for the party level."""
    import random
    
    # Simple mapping of party level to appropriate CR
    if party_level <= 1:
        suitable_enemies = get_enemies_by_cr(0.125) + get_enemies_by_cr(0.25)
    elif party_level <= 3:
        suitable_enemies = get_enemies_by_cr(0.25) + get_enemies_by_cr(0.5)
    elif party_level <= 5:
        suitable_enemies = get_enemies_by_cr(0.5) + get_enemies_by_cr(1.0)
    else:
        suitable_enemies = list(STANDARD_ENEMIES.values())
    
    return random.choice(suitable_enemies) if suitable_enemies else STANDARD_ENEMIES['goblin']