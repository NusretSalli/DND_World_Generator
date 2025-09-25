"""
Spell system for D&D 5e character management.

This module provides spell management functionality inspired by py-dnd library,
including spell lists by class, spell slot tracking, and spellcasting mechanics.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Set
from enum import Enum


class SpellLevel(Enum):
    """Spell levels in D&D 5e."""
    CANTRIP = 0
    FIRST = 1
    SECOND = 2
    THIRD = 3
    FOURTH = 4
    FIFTH = 5
    SIXTH = 6
    SEVENTH = 7
    EIGHTH = 8
    NINTH = 9


class SpellSchool(Enum):
    """Schools of magic in D&D 5e."""
    ABJURATION = "abjuration"
    CONJURATION = "conjuration"
    DIVINATION = "divination"
    ENCHANTMENT = "enchantment"
    EVOCATION = "evocation"
    ILLUSION = "illusion"
    NECROMANCY = "necromancy"
    TRANSMUTATION = "transmutation"


@dataclass
class Spell:
    """
    Represents a D&D 5e spell.
    
    Attributes:
        name: The spell's name
        level: Spell level (0 for cantrips, 1-9 for leveled spells)
        school: School of magic
        casting_time: How long it takes to cast
        range: Spell range
        components: Components required (V, S, M)
        duration: How long the spell lasts
        description: Full spell description
        classes: List of classes that can learn this spell
        damage_dice: Damage dice if applicable
        save_type: Saving throw type if applicable
        ritual: Whether this spell can be cast as a ritual
    """
    name: str
    level: SpellLevel
    school: SpellSchool
    casting_time: str
    range: str
    components: List[str]
    duration: str
    description: str
    classes: List[str]
    damage_dice: Optional[str] = None
    save_type: Optional[str] = None
    ritual: bool = False
    
    def __str__(self):
        return f"{self.name} ({self.level.name.lower()} level {self.school.value})"


# Spell slot progression table for each class
SPELL_SLOTS_BY_CLASS_LEVEL = {
    'wizard': {
        1: {1: 2}, 2: {1: 3}, 3: {1: 4, 2: 2}, 4: {1: 4, 2: 3},
        5: {1: 4, 2: 3, 3: 2}, 6: {1: 4, 2: 3, 3: 3}, 7: {1: 4, 2: 3, 3: 3, 4: 1},
        8: {1: 4, 2: 3, 3: 3, 4: 2}, 9: {1: 4, 2: 3, 3: 3, 4: 3, 5: 1},
        10: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2}, 11: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1},
        12: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1}, 13: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1},
        14: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1}, 15: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1},
        16: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1}, 17: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1, 9: 1},
        18: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 1, 7: 1, 8: 1, 9: 1}, 19: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 1, 8: 1, 9: 1},
        20: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 2, 8: 1, 9: 1}
    },
    'sorcerer': {
        1: {1: 2}, 2: {1: 3}, 3: {1: 4, 2: 2}, 4: {1: 4, 2: 3},
        5: {1: 4, 2: 3, 3: 2}, 6: {1: 4, 2: 3, 3: 3}, 7: {1: 4, 2: 3, 3: 3, 4: 1},
        8: {1: 4, 2: 3, 3: 3, 4: 2}, 9: {1: 4, 2: 3, 3: 3, 4: 3, 5: 1},
        10: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2}, 11: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1},
        12: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1}, 13: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1},
        14: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1}, 15: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1},
        16: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1}, 17: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1, 9: 1},
        18: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 1, 7: 1, 8: 1, 9: 1}, 19: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 1, 8: 1, 9: 1},
        20: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 2, 8: 1, 9: 1}
    },
    'cleric': {
        1: {1: 2}, 2: {1: 3}, 3: {1: 4, 2: 2}, 4: {1: 4, 2: 3},
        5: {1: 4, 2: 3, 3: 2}, 6: {1: 4, 2: 3, 3: 3}, 7: {1: 4, 2: 3, 3: 3, 4: 1},
        8: {1: 4, 2: 3, 3: 3, 4: 2}, 9: {1: 4, 2: 3, 3: 3, 4: 3, 5: 1},
        10: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2}, 11: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1},
        12: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1}, 13: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1},
        14: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1}, 15: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1},
        16: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1}, 17: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1, 9: 1},
        18: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 1, 7: 1, 8: 1, 9: 1}, 19: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 1, 8: 1, 9: 1},
        20: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 2, 8: 1, 9: 1}
    },
    'bard': {
        1: {1: 2}, 2: {1: 3}, 3: {1: 4, 2: 2}, 4: {1: 4, 2: 3},
        5: {1: 4, 2: 3, 3: 2}, 6: {1: 4, 2: 3, 3: 3}, 7: {1: 4, 2: 3, 3: 3, 4: 1},
        8: {1: 4, 2: 3, 3: 3, 4: 2}, 9: {1: 4, 2: 3, 3: 3, 4: 3, 5: 1},
        10: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2}, 11: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1},
        12: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1}, 13: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1},
        14: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1}, 15: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1},
        16: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1}, 17: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1, 9: 1},
        18: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 1, 7: 1, 8: 1, 9: 1}, 19: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 1, 8: 1, 9: 1},
        20: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 2, 8: 1, 9: 1}
    },
    'druid': {
        1: {1: 2}, 2: {1: 3}, 3: {1: 4, 2: 2}, 4: {1: 4, 2: 3},
        5: {1: 4, 2: 3, 3: 2}, 6: {1: 4, 2: 3, 3: 3}, 7: {1: 4, 2: 3, 3: 3, 4: 1},
        8: {1: 4, 2: 3, 3: 3, 4: 2}, 9: {1: 4, 2: 3, 3: 3, 4: 3, 5: 1},
        10: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2}, 11: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1},
        12: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1}, 13: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1},
        14: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1}, 15: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1},
        16: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1}, 17: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1, 9: 1},
        18: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 1, 7: 1, 8: 1, 9: 1}, 19: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 1, 8: 1, 9: 1},
        20: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 2, 8: 1, 9: 1}
    },
    'warlock': {
        # Warlocks are special - they have fewer spell slots but they're all at their highest known level
        1: {1: 1}, 2: {1: 2}, 3: {2: 2}, 4: {2: 2},
        5: {3: 2}, 6: {3: 2}, 7: {4: 2}, 8: {4: 2},
        9: {5: 2}, 10: {5: 2}, 11: {5: 3}, 12: {5: 3},
        13: {5: 3}, 14: {5: 3}, 15: {5: 3}, 16: {5: 3},
        17: {5: 4}, 18: {5: 4}, 19: {5: 4}, 20: {5: 4}
    }
}

# Common spells for each class
CLASS_SPELL_LISTS = {
    'wizard': {
        0: ['Mage Hand', 'Prestidigitation', 'Ray of Frost', 'Fire Bolt', 'Light', 'Minor Illusion'],
        1: ['Magic Missile', 'Shield', 'Detect Magic', 'Identify', 'Sleep', 'Burning Hands'],
        2: ['Misty Step', 'Web', 'Scorching Ray', 'Suggestion', 'Invisibility', 'Mirror Image'],
        3: ['Fireball', 'Lightning Bolt', 'Counterspell', 'Dispel Magic', 'Fly', 'Haste']
    },
    'sorcerer': {
        0: ['Fire Bolt', 'Ray of Frost', 'Mage Hand', 'Prestidigitation', 'Light', 'Minor Illusion'],
        1: ['Magic Missile', 'Shield', 'Burning Hands', 'Charm Person', 'Sleep', 'Disguise Self'],
        2: ['Misty Step', 'Scorching Ray', 'Web', 'Suggestion', 'Mirror Image', 'Blur'],
        3: ['Fireball', 'Lightning Bolt', 'Counterspell', 'Haste', 'Fly', 'Hypnotic Pattern']
    },
    'cleric': {
        0: ['Sacred Flame', 'Guidance', 'Light', 'Mending', 'Resistance', 'Thaumaturgy'],
        1: ['Cure Wounds', 'Healing Word', 'Bless', 'Shield of Faith', 'Command', 'Detect Magic'],
        2: ['Spiritual Weapon', 'Aid', 'Lesser Restoration', 'Hold Person', 'Silence', 'Prayer of Healing'],
        3: ['Spirit Guardians', 'Dispel Magic', 'Mass Healing Word', 'Revivify', 'Beacon of Hope', 'Remove Curse']
    },
    'bard': {
        0: ['Vicious Mockery', 'Minor Illusion', 'Mage Hand', 'Prestidigitation', 'Dancing Lights', 'Message'],
        1: ['Healing Word', 'Charm Person', 'Dissonant Whispers', 'Faerie Fire', 'Sleep', 'Thunderwave'],
        2: ['Heat Metal', 'Suggestion', 'Shatter', 'Invisibility', 'Lesser Restoration', 'Calm Emotions'],
        3: ['Counterspell', 'Hypnotic Pattern', 'Dispel Magic', 'Leomund\'s Tiny Hut', 'Mass Healing Word', 'Plant Growth']
    },
    'druid': {
        0: ['Druidcraft', 'Guidance', 'Produce Flame', 'Resistance', 'Thorn Whip', 'Shillelagh'],
        1: ['Cure Wounds', 'Entangle', 'Faerie Fire', 'Goodberry', 'Healing Word', 'Speak with Animals'],
        2: ['Barkskin', 'Flame Blade', 'Heat Metal', 'Moonbeam', 'Pass without Trace', 'Spike Growth'],
        3: ['Call Lightning', 'Conjure Animals', 'Daylight', 'Dispel Magic', 'Plant Growth', 'Water Breathing']
    },
    'warlock': {
        0: ['Eldritch Blast', 'Mage Hand', 'Minor Illusion', 'Prestidigitation', 'Chill Touch', 'Toll the Dead'],
        1: ['Hex', 'Arms of Hadar', 'Charm Person', 'Comprehend Languages', 'Expeditious Retreat', 'Protection from Evil and Good'],
        2: ['Darkness', 'Hold Person', 'Invisibility', 'Mirror Image', 'Misty Step', 'Suggestion'],
        3: ['Counterspell', 'Dispel Magic', 'Fly', 'Hunger of Hadar', 'Hypnotic Pattern', 'Vampiric Touch']
    }
}


@dataclass
class SpellSlots:
    """Tracks available spell slots for a character."""
    max_slots: Dict[int, int]  # {spell_level: max_slots}
    current_slots: Dict[int, int]  # {spell_level: current_slots}
    
    def __post_init__(self):
        # Initialize current slots to match max slots
        if not self.current_slots:
            self.current_slots = self.max_slots.copy()
    
    def has_slot(self, level: int) -> bool:
        """Check if character has an available spell slot of the given level."""
        return self.current_slots.get(level, 0) > 0
    
    def use_slot(self, level: int) -> bool:
        """Use a spell slot of the given level. Returns True if successful."""
        if self.has_slot(level):
            self.current_slots[level] -= 1
            return True
        return False
    
    def restore_slot(self, level: int) -> bool:
        """Restore one spell slot of the given level. Returns True if successful."""
        max_slots = self.max_slots.get(level, 0)
        current = self.current_slots.get(level, 0)
        if current < max_slots:
            self.current_slots[level] = current + 1
            return True
        return False
    
    def long_rest(self):
        """Restore all spell slots (long rest)."""
        self.current_slots = self.max_slots.copy()
    
    def short_rest(self):
        """Handle short rest spell slot recovery (relevant for some classes)."""
        # For most classes, short rest doesn't restore spell slots
        # Warlocks are an exception but that would be handled separately
        pass


class SpellManager:
    """Manages spells for a character."""
    
    def __init__(self, character_class: str, level: int):
        self.character_class = character_class.lower()
        self.level = level
        self.known_spells: Set[str] = set()
        self.prepared_spells: Set[str] = set()
        self.spell_slots = self._calculate_spell_slots()
    
    def _calculate_spell_slots(self) -> SpellSlots:
        """Calculate spell slots based on class and level."""
        class_progression = SPELL_SLOTS_BY_CLASS_LEVEL.get(self.character_class, {})
        max_slots = class_progression.get(self.level, {})
        return SpellSlots(max_slots=max_slots, current_slots=max_slots.copy())
    
    def is_spellcaster(self) -> bool:
        """Check if this class can cast spells."""
        return self.character_class in SPELL_SLOTS_BY_CLASS_LEVEL
    
    def get_available_spells(self, spell_level: int) -> List[str]:
        """Get available spells for the class at the given level."""
        class_spells = CLASS_SPELL_LISTS.get(self.character_class, {})
        return class_spells.get(spell_level, [])
    
    def can_learn_spell(self, spell_name: str, spell_level: int) -> bool:
        """Check if character can learn this spell."""
        available_spells = self.get_available_spells(spell_level)
        return spell_name in available_spells
    
    def learn_spell(self, spell_name: str, spell_level: int) -> bool:
        """Learn a new spell."""
        if self.can_learn_spell(spell_name, spell_level):
            self.known_spells.add(spell_name)
            return True
        return False
    
    def prepare_spell(self, spell_name: str) -> bool:
        """Prepare a known spell."""
        if spell_name in self.known_spells:
            self.prepared_spells.add(spell_name)
            return True
        return False
    
    def cast_spell(self, spell_name: str, spell_level: int) -> bool:
        """Cast a prepared spell using a spell slot."""
        if spell_name not in self.prepared_spells:
            return False
        
        # Find the lowest available spell slot that can cast this spell
        for slot_level in range(spell_level, 10):
            if self.spell_slots.use_slot(slot_level):
                return True
        
        return False
    
    def get_spell_slot_summary(self) -> Dict[int, Dict[str, int]]:
        """Get a summary of current vs max spell slots."""
        summary = {}
        for level in range(1, 10):
            max_slots = self.spell_slots.max_slots.get(level, 0)
            current_slots = self.spell_slots.current_slots.get(level, 0)
            if max_slots > 0:
                summary[level] = {'current': current_slots, 'max': max_slots}
        return summary


def get_cantrips_known(character_class: str, level: int) -> int:
    """Get number of cantrips known for a class at a given level."""
    cantrip_progression = {
        'wizard': {1: 3, 4: 4, 10: 5},
        'sorcerer': {1: 4, 4: 5, 10: 6},
        'cleric': {1: 3, 4: 4, 10: 5},
        'bard': {1: 2, 4: 3, 10: 4},
        'druid': {1: 2, 4: 3, 10: 4},
        'warlock': {1: 2, 4: 3, 10: 4}
    }
    
    class_progression = cantrip_progression.get(character_class.lower(), {})
    cantrips = 0
    for required_level in sorted(class_progression.keys()):
        if level >= required_level:
            cantrips = class_progression[required_level]
    
    return cantrips


def get_spells_known(character_class: str, level: int) -> int:
    """Get number of spells known for classes that know spells (like Sorcerer)."""
    spells_known_progression = {
        'sorcerer': {1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9, 9: 10, 10: 11, 11: 12, 12: 12, 13: 13, 14: 13, 15: 14, 16: 14, 17: 15, 18: 15, 19: 15, 20: 15},
        'bard': {1: 4, 2: 5, 3: 6, 4: 7, 5: 8, 6: 9, 7: 10, 8: 11, 9: 12, 10: 14, 11: 15, 12: 15, 13: 16, 14: 18, 15: 19, 16: 19, 17: 20, 18: 22, 19: 22, 20: 22},
        'warlock': {1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9, 9: 10, 10: 10, 11: 11, 12: 11, 13: 12, 14: 12, 15: 13, 16: 13, 17: 14, 18: 14, 19: 15, 20: 15}
    }
    
    class_progression = spells_known_progression.get(character_class.lower(), {})
    return class_progression.get(level, 0)