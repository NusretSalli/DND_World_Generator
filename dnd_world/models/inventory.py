"""
Inventory and Item Models
"""

import json
from ..utils.database import db

class Item(db.Model):
    """
    Database model for items in character inventory.
    
    This model represents all types of items including weapons, armor, gear,
    consumables, and magical items with comprehensive D&D 5e properties.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    item_type = db.Column(db.String(50), nullable=False)  # weapon, armor, gear, etc.
    description = db.Column(db.Text)
    weight = db.Column(db.Float)
    value = db.Column(db.Integer)  # in gold pieces
    character_id = db.Column(db.Integer, db.ForeignKey('character.id', ondelete='CASCADE'))
    
    # Enhanced D&D properties
    rarity = db.Column(db.String(20), default='common')  # common, uncommon, rare, very_rare, legendary, artifact
    magical = db.Column(db.Boolean, default=False)
    requires_attunement = db.Column(db.Boolean, default=False)
    tags = db.Column(db.Text)  # JSON string for flexible categorization
    effects = db.Column(db.Text)  # JSON string for item effects
    equipped_slot = db.Column(db.String(50))  # Equipment slot if equipped
    
    # Weapon-specific properties
    damage = db.Column(db.String(20))
    damage_type = db.Column(db.String(20))
    weapon_properties = db.Column(db.Text)  # JSON string
    enchantment_bonus = db.Column(db.Integer, default=0)
    
    # Armor-specific properties  
    base_ac = db.Column(db.Integer)
    armor_type = db.Column(db.String(20))
    strength_req = db.Column(db.Integer, default=0)
    stealth_disadvantage = db.Column(db.Boolean, default=False)
    
    # Consumable properties
    uses = db.Column(db.Integer)
    max_uses = db.Column(db.Integer)
    
    # Magical item properties
    charges = db.Column(db.Integer)
    max_charges = db.Column(db.Integer)

    def __repr__(self):
        """String representation of the item."""
        return f'<Item {self.name}>'
    
    def get_effects_list(self):
        """
        Parse effects JSON string into list.
        
        Returns:
            list: List of effect descriptions or empty list if none
        """
        if self.effects:
            try:
                return json.loads(self.effects)
            except:
                return []
        return []
    
    def set_effects_list(self, effects_list):
        """
        Store effects list as JSON string.
        
        Args:
            effects_list (list): List of effect descriptions
        """
        self.effects = json.dumps(effects_list) if effects_list else None
    
    def get_tags_list(self):
        """
        Parse tags JSON string into list.
        
        Returns:
            list: List of tags or empty list if none
        """
        if self.tags:
            try:
                return json.loads(self.tags)
            except:
                return []
        return []
    
    def set_tags_list(self, tags_list):
        """
        Store tags list as JSON string.
        
        Args:
            tags_list (list): List of tags
        """
        self.tags = json.dumps(tags_list) if tags_list else None


# For backwards compatibility with existing code
CharacterInventory = Item