"""
Enemy/Monster Models
"""

import json
from ..utils.database import db

class Enemy(db.Model):
    """
    Database model for enemy/monster templates.
    
    This model stores enemy statistics and abilities for use in combat encounters.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    creature_type = db.Column(db.String(50), nullable=False)
    size = db.Column(db.String(20), nullable=False)
    armor_class = db.Column(db.Integer, nullable=False)
    hit_points = db.Column(db.Integer, nullable=False)
    speed = db.Column(db.Integer, nullable=False, default=30)
    
    # Ability scores
    strength = db.Column(db.Integer, nullable=False)
    dexterity = db.Column(db.Integer, nullable=False)
    constitution = db.Column(db.Integer, nullable=False)
    intelligence = db.Column(db.Integer, nullable=False)
    wisdom = db.Column(db.Integer, nullable=False)
    charisma = db.Column(db.Integer, nullable=False)
    
    # Challenge rating and XP
    challenge_rating = db.Column(db.Float, nullable=False)
    experience_points = db.Column(db.Integer, nullable=False)
    
    # Senses and special properties
    passive_perception = db.Column(db.Integer, default=10)
    darkvision = db.Column(db.Integer, default=0)
    
    # JSON fields for complex data
    saving_throws = db.Column(db.Text)  # JSON
    skills = db.Column(db.Text)  # JSON
    damage_resistances = db.Column(db.Text)  # JSON
    damage_immunities = db.Column(db.Text)  # JSON
    condition_immunities = db.Column(db.Text)  # JSON
    languages = db.Column(db.Text)  # JSON
    actions = db.Column(db.Text)  # JSON
    special_abilities = db.Column(db.Text)  # JSON
    
    @property
    def strength_modifier(self):
        return (self.strength - 10) // 2
    
    @property
    def dexterity_modifier(self):
        return (self.dexterity - 10) // 2
    
    @property
    def constitution_modifier(self):
        return (self.constitution - 10) // 2
    
    @property
    def intelligence_modifier(self):
        return (self.intelligence - 10) // 2
    
    @property
    def wisdom_modifier(self):
        return (self.wisdom - 10) // 2
    
    @property
    def charisma_modifier(self):
        return (self.charisma - 10) // 2
    
    def get_actions_list(self):
        """Parse actions JSON string into list."""
        if self.actions:
            try:
                return json.loads(self.actions)
            except:
                return []
        return []
    
    def get_special_abilities_list(self):
        """Parse special abilities JSON string into list."""
        if self.special_abilities:
            try:
                return json.loads(self.special_abilities)
            except:
                return []
        return []
    
    def get_saving_throws_dict(self):
        """Parse saving throws JSON string into dict."""
        if self.saving_throws:
            try:
                return json.loads(self.saving_throws)
            except:
                return {}
        return {}
    
    def get_skills_dict(self):
        """Parse skills JSON string into dict."""
        if self.skills:
            try:
                return json.loads(self.skills)
            except:
                return {}
        return {}
    
    def get_damage_resistances_list(self):
        """Parse damage resistances JSON string into list."""
        if self.damage_resistances:
            try:
                return json.loads(self.damage_resistances)
            except:
                return []
        return []
    
    def get_damage_immunities_list(self):
        """Parse damage immunities JSON string into list."""
        if self.damage_immunities:
            try:
                return json.loads(self.damage_immunities)
            except:
                return []
        return []
    
    def get_condition_immunities_list(self):
        """Parse condition immunities JSON string into list."""
        if self.condition_immunities:
            try:
                return json.loads(self.condition_immunities)
            except:
                return []
        return []
    
    def get_languages_list(self):
        """Parse languages JSON string into list."""
        if self.languages:
            try:
                return json.loads(self.languages)
            except:
                return []
        return []