"""
Name Generation System
"""

from pynames import GENDER
from pynames.generators.elven import WarhammerNamesGenerator, DnDNamesGenerator
from pynames.generators.goblin import GoblinGenerator
from pynames.generators.korean import KoreanNamesGenerator
from pynames.generators.mongolian import MongolianNamesGenerator
from pynames.generators.orc import OrcNamesGenerator
from pynames.generators.russian import PaganNamesGenerator
from pynames.generators.scandinavian import ScandinavianNamesGenerator

class NameGenerators:
    """Manages name generation for different D&D races"""
    
    # Mapping races to pynames generators
    RACE_TO_GENERATOR = {
        'dwarf': KoreanNamesGenerator(),
        'elf': DnDNamesGenerator(),
        'half-orc': OrcNamesGenerator(),
        'gnome': GoblinGenerator(),
        # Using a generic fantasy generator for races without a specific one
        'human': ScandinavianNamesGenerator(),
        'halfling': KoreanNamesGenerator(),
        'dragonborn': KoreanNamesGenerator(),
        'half-elf': WarhammerNamesGenerator(),  # Using Warhammer names for half-elves
        'tiefling': PaganNamesGenerator(),
    }
    
    @classmethod
    def generate_name(cls, race, gender_str):
        """
        Generate a name for the specified race and gender.
        
        Args:
            race (str): Character race
            gender_str (str): Gender string ('male' or 'female')
            
        Returns:
            str: Generated name
        """
        gender = GENDER.MALE if gender_str == 'male' else GENDER.FEMALE
        generator = cls.RACE_TO_GENERATOR.get(race.lower(), ScandinavianNamesGenerator())
        
        # Not all generators support gender, so we handle that
        try:
            name = generator.get_name_simple(gender)
        except TypeError:
            name = generator.get_name_simple()
        
        return name
    
    @classmethod
    def get_available_races(cls):
        """Get list of available races for name generation."""
        return list(cls.RACE_TO_GENERATOR.keys())
    
    @classmethod
    def add_generator(cls, race, generator):
        """Add a custom name generator for a race."""
        cls.RACE_TO_GENERATOR[race.lower()] = generator