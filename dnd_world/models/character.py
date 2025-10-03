"""SQLAlchemy model for player characters."""

from dnd_world.database import db
from dnd_world.core.items import CharacterEquipment, EquipmentSlot
from .item import Item

# Character Model - Represents player characters with D&D 5e statistics and capabilities
class Character(db.Model):
    """
    Database model for player characters.
    
    This model implements D&D 5e rules for character statistics, abilities,
    inventory management, and equipment. It handles character creation, stat
    calculations, and game mechanics.
    """
    # Basic information
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    race = db.Column(db.String(50), nullable=False)
    character_class = db.Column(db.String(50), nullable=False)
    level = db.Column(db.Integer, nullable=False, default=1)
    experience = db.Column(db.Integer, nullable=False, default=0)
    max_hp = db.Column(db.Integer, nullable=False)
    current_hp = db.Column(db.Integer, nullable=False)
    armor_class = db.Column(db.Integer, nullable=False, default=10)
    
    # User relationship - each character belongs to a user
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # nullable for backward compatibility
    
    # Ability Scores - D&D 5e core stats
    strength = db.Column(db.Integer, nullable=False)
    dexterity = db.Column(db.Integer, nullable=False)
    constitution = db.Column(db.Integer, nullable=False)
    intelligence = db.Column(db.Integer, nullable=False)
    wisdom = db.Column(db.Integer, nullable=False)
    charisma = db.Column(db.Integer, nullable=False)
    
    # Currency - D&D 5e uses a multi-currency system
    copper = db.Column(db.Integer, default=0)
    silver = db.Column(db.Integer, default=0)
    gold = db.Column(db.Integer, default=0)
    platinum = db.Column(db.Integer, default=0)
    
    # Spell System - Track current spell slots (max slots calculated dynamically)
    current_spell_slots_1 = db.Column(db.Integer, default=0)
    current_spell_slots_2 = db.Column(db.Integer, default=0)
    current_spell_slots_3 = db.Column(db.Integer, default=0)
    current_spell_slots_4 = db.Column(db.Integer, default=0)
    current_spell_slots_5 = db.Column(db.Integer, default=0)
    current_spell_slots_6 = db.Column(db.Integer, default=0)
    current_spell_slots_7 = db.Column(db.Integer, default=0)
    current_spell_slots_8 = db.Column(db.Integer, default=0)
    current_spell_slots_9 = db.Column(db.Integer, default=0)
    
    # Known and prepared spells (stored as JSON strings)
    known_spells = db.Column(db.Text, default='[]')  # JSON list of spell names
    prepared_spells = db.Column(db.Text, default='[]')  # JSON list of prepared spell names
    
    # Relationships - Link to items owned by this character
    inventory = db.relationship(
        'Item',
        backref=db.backref('owner'),
        lazy=True,
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        """String representation of the character."""
        return f'<Character {self.name}>'
    
    @property
    def equipment(self):
        """
        Get character equipment manager.
        
        This property provides access to the CharacterEquipment class that manages
        equipment slots and attunement. It's lazily initialized and cached.
        
        Returns:
            CharacterEquipment: An equipment manager for this character
        """
        if not hasattr(self, '_equipment') or self._equipment is None:
            self._equipment = CharacterEquipment()
            # Load equipped items from database
            equipped_items = Item.query.filter_by(character_id=self.id).filter(Item.equipped_slot.isnot(None)).all()
            for item in equipped_items:
                try:
                    slot = EquipmentSlot(item.equipped_slot)
                    self._equipment.slots[slot] = item
                    if item.requires_attunement:
                        self._equipment.attuned_items.append(item)
                except ValueError:
                    # Invalid slot, skip this item
                    continue
        return self._equipment
    
    def equip_item(self, item_id, slot_name):
        """
        Equip an item to a specific slot.
        
        This method handles equipping an item from the character's inventory
        to a specific equipment slot.
        
        Args:
            item_id (int): ID of the item to equip
            slot_name (str): Name of the equipment slot
            
        Returns:
            tuple: (success, message) where success is a boolean and message is a string
        """
        item = Item.query.get(item_id)
        if not item or item.character_id != self.id:
            return False, "Item not found in inventory"
        
        try:
            slot = EquipmentSlot(slot_name)
        except ValueError:
            return False, "Invalid equipment slot"
        
        # Use equipment manager to equip item
        success, message = self.equipment.equip_item(item, slot)
        if success:
            # Update database
            item.equipped_slot = slot.value
            db.session.commit()
        
        return success, message
    
    def unequip_item(self, slot_name):
        """
        Unequip an item from a specific slot.
        
        This method handles removing an item from an equipment slot.
        
        Args:
            slot_name (str): Name of the equipment slot
            
        Returns:
            tuple: (success, message) where success is a boolean and message is a string
        """
        try:
            slot = EquipmentSlot(slot_name)
        except ValueError:
            return False, "Invalid equipment slot"
        
        item = self.equipment.unequip_item(slot)
        if item:
            # Update database
            item.equipped_slot = None
            db.session.commit()
            return True, f"Unequipped {item.name}"
        
        return False, "No item equipped in that slot"
    
    def add_item(self, name, item_type, description="", weight=0, value=0, **kwargs):
        """
        Add an item to character inventory with enhanced properties.
        
        This method creates a new Item instance and adds it to the character's
        inventory with all the specified properties.
        
        Args:
            name (str): Name of the item
            item_type (str): Type of item (weapon, armor, gear, etc.)
            description (str, optional): Item description. Defaults to "".
            weight (float, optional): Item weight in pounds. Defaults to 0.
            value (int, optional): Item value in gold pieces. Defaults to 0.
            **kwargs: Additional item properties:
                - rarity: Item rarity (common, uncommon, rare, etc.)
                - magical: Whether the item is magical
                - requires_attunement: Whether the item requires attunement
                - damage: Damage dice (e.g., "1d6")
                - damage_type: Type of damage (slashing, piercing, etc.)
                - base_ac: Base armor class for armor
                - armor_type: Type of armor (light, medium, heavy)
                - strength_req: Minimum strength requirement
                - stealth_disadvantage: Whether armor imposes disadvantage on stealth
                - enchantment_bonus: Magic bonus (+1, +2, etc.)
                - uses/max_uses: For consumable items
                - charges/max_charges: For items with charges
                - tags: List of tags for the item
                - effects: List of effects the item provides
                
        Returns:
            Item: The newly created and added item
        """
        item = Item(
            name=name,
            item_type=item_type,
            description=description,
            weight=weight,
            value=value,
            character_id=self.id,
            # Enhanced properties
            rarity=kwargs.get('rarity', 'common'),
            magical=kwargs.get('magical', False),
            requires_attunement=kwargs.get('requires_attunement', False),
            damage=kwargs.get('damage'),
            damage_type=kwargs.get('damage_type'),
            base_ac=kwargs.get('base_ac'),
            armor_type=kwargs.get('armor_type'),
            strength_req=kwargs.get('strength_req', 0),
            stealth_disadvantage=kwargs.get('stealth_disadvantage', False),
            enchantment_bonus=kwargs.get('enchantment_bonus', 0),
            uses=kwargs.get('uses'),
            max_uses=kwargs.get('max_uses'),
            charges=kwargs.get('charges'),
            max_charges=kwargs.get('max_charges')
        )
        
        # Handle complex properties
        if 'tags' in kwargs:
            item.set_tags_list(kwargs['tags'])
        if 'effects' in kwargs:
            item.set_effects_list(kwargs['effects'])
        if 'weapon_properties' in kwargs:
            import json
            item.weapon_properties = json.dumps(kwargs['weapon_properties'])
        
        db.session.add(item)
        db.session.commit()
        return item
    
    def remove_item(self, item_id):
        item = Item.query.get(item_id)
        if item and item.character_id == self.id:
            db.session.delete(item)
            db.session.commit()
            return True
        return False
    
    @property
    def total_weight(self):
        return sum(item.weight for item in self.inventory)
    
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
    
    @property
    def carrying_capacity(self):
        return self.strength * 15  # Basic carrying capacity rules
    
    # Spell Management Methods
    def get_spell_manager(self):
        """Get a spell manager for this character."""
        from dnd_world.core.spells import SpellManager
        return SpellManager(self.character_class, self.level)
    
    def is_spellcaster(self):
        """Check if this character can cast spells."""
        return self.get_spell_manager().is_spellcaster()
    
    def get_max_spell_slots(self):
        """Get maximum spell slots for this character's class and level."""
        if not self.is_spellcaster():
            return {}
        
        from dnd_world.core.spells import SPELL_SLOTS_BY_CLASS_LEVEL
        class_progression = SPELL_SLOTS_BY_CLASS_LEVEL.get(self.character_class.lower(), {})
        return class_progression.get(self.level, {})
    
    def get_current_spell_slots(self):
        """Get current available spell slots."""
        return {
            1: self.current_spell_slots_1,
            2: self.current_spell_slots_2,
            3: self.current_spell_slots_3,
            4: self.current_spell_slots_4,
            5: self.current_spell_slots_5,
            6: self.current_spell_slots_6,
            7: self.current_spell_slots_7,
            8: self.current_spell_slots_8,
            9: self.current_spell_slots_9,
        }
    
    def set_current_spell_slots(self, slots_dict):
        """Set current spell slots from a dictionary."""
        self.current_spell_slots_1 = slots_dict.get(1, 0)
        self.current_spell_slots_2 = slots_dict.get(2, 0)
        self.current_spell_slots_3 = slots_dict.get(3, 0)
        self.current_spell_slots_4 = slots_dict.get(4, 0)
        self.current_spell_slots_5 = slots_dict.get(5, 0)
        self.current_spell_slots_6 = slots_dict.get(6, 0)
        self.current_spell_slots_7 = slots_dict.get(7, 0)
        self.current_spell_slots_8 = slots_dict.get(8, 0)
        self.current_spell_slots_9 = slots_dict.get(9, 0)
    
    def refresh_spell_slots(self):
        """Refresh spell slots to maximum (long rest)."""
        max_slots = self.get_max_spell_slots()
        self.set_current_spell_slots(max_slots)
    
    def use_spell_slot(self, level):
        """Use a spell slot of the given level."""
        current_slots = self.get_current_spell_slots()
        if current_slots.get(level, 0) > 0:
            slot_attr = f'current_spell_slots_{level}'
            current_value = getattr(self, slot_attr)
            setattr(self, slot_attr, current_value - 1)
            return True
        return False
    
    def get_known_spells_list(self):
        """Get list of known spells."""
        import json
        try:
            return json.loads(self.known_spells or '[]')
        except:
            return []
    
    def set_known_spells_list(self, spells):
        """Set list of known spells."""
        import json
        self.known_spells = json.dumps(spells)
    
    def get_prepared_spells_list(self):
        """Get list of prepared spells."""
        import json
        try:
            return json.loads(self.prepared_spells or '[]')
        except:
            return []
    
    def set_prepared_spells_list(self, spells):
        """Set list of prepared spells."""
        import json
        self.prepared_spells = json.dumps(spells)

