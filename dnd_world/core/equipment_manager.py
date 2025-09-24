"""
Equipment Management System
"""

from items import ALL_ITEMS, CharacterEquipment, EquipmentSlot, ItemType
from ..utils.database import db

class EquipmentManager:
    """Manages character equipment and inventory"""
    
    @staticmethod
    def get_item_by_name(item_name):
        """
        Get an item template by name.
        
        Args:
            item_name (str): Name of the item
            
        Returns:
            Item template or None if not found
        """
        return ALL_ITEMS.get(item_name)
    
    @staticmethod
    def get_items_by_type(item_type):
        """
        Get all items of a specific type.
        
        Args:
            item_type (str): Type of item ('weapon', 'armor', etc.)
            
        Returns:
            dict: Dictionary of items of the specified type
        """
        return {name: item for name, item in ALL_ITEMS.items() 
                if hasattr(item, 'item_type') and item.item_type == item_type}
    
    @staticmethod
    def get_weapons():
        """Get all weapon items."""
        return EquipmentManager.get_items_by_type('weapon')
    
    @staticmethod
    def get_armor():
        """Get all armor items."""
        return EquipmentManager.get_items_by_type('armor')
    
    @staticmethod
    def get_gear():
        """Get all gear items."""
        return EquipmentManager.get_items_by_type('gear')
    
    @staticmethod
    def add_custom_item_to_character(character, item_data):
        """
        Add a custom item to a character's inventory.
        
        Args:
            character (Character): The character
            item_data (dict): Item data dictionary
            
        Returns:
            Item: The created item
        """
        return character.add_item(**item_data)
    
    @staticmethod
    def add_template_item_to_character(character, item_name, quantity=1):
        """
        Add an item from the template library to a character.
        
        Args:
            character (Character): The character
            item_name (str): Name of the template item
            quantity (int): Number of items to add
            
        Returns:
            list: List of created items
        """
        template = EquipmentManager.get_item_by_name(item_name)
        if not template:
            raise ValueError(f"Item template '{item_name}' not found")
        
        items = []
        for _ in range(quantity):
            item = character.add_item(
                name=template.name,
                item_type=getattr(template, 'item_type', 'gear'),
                description=template.description,
                weight=template.weight,
                value=getattr(template, 'cost', 0),
                # Add specific properties based on item type
                **EquipmentManager._extract_template_properties(template)
            )
            items.append(item)
        
        return items
    
    @staticmethod
    def _extract_template_properties(template):
        """Extract properties from item template for database storage."""
        properties = {}
        
        # Weapon properties
        if hasattr(template, 'damage'):
            properties['damage'] = template.damage
        if hasattr(template, 'damage_type'):
            properties['damage_type'] = template.damage_type
        if hasattr(template, 'properties'):
            properties['weapon_properties'] = template.properties
        
        # Armor properties
        if hasattr(template, 'ac'):
            properties['base_ac'] = template.ac
        if hasattr(template, 'armor_type'):
            properties['armor_type'] = template.armor_type
        if hasattr(template, 'strength_req'):
            properties['strength_req'] = template.strength_req
        if hasattr(template, 'stealth_disadvantage'):
            properties['stealth_disadvantage'] = template.stealth_disadvantage
        
        # Magic item properties
        if hasattr(template, 'magical'):
            properties['magical'] = template.magical
        if hasattr(template, 'requires_attunement'):
            properties['requires_attunement'] = template.requires_attunement
        if hasattr(template, 'rarity'):
            properties['rarity'] = template.rarity.value if hasattr(template.rarity, 'value') else str(template.rarity)
        
        return properties
    
    @staticmethod
    def equip_item_to_character(character, item_id, slot_name):
        """
        Equip an item to a character.
        
        Args:
            character (Character): The character
            item_id (int): ID of the item to equip
            slot_name (str): Name of the equipment slot
            
        Returns:
            tuple: (success, message)
        """
        return character.equip_item(item_id, slot_name)
    
    @staticmethod
    def unequip_item_from_character(character, slot_name):
        """
        Unequip an item from a character.
        
        Args:
            character (Character): The character
            slot_name (str): Name of the equipment slot
            
        Returns:
            tuple: (success, message)
        """
        return character.unequip_item(slot_name)
    
    @staticmethod
    def get_character_equipped_items(character):
        """
        Get all equipped items for a character.
        
        Args:
            character (Character): The character
            
        Returns:
            dict: Dictionary mapping slot names to items
        """
        equipped_items = {}
        for item in character.inventory:
            if item.equipped_slot:
                equipped_items[item.equipped_slot] = item
        return equipped_items
    
    @staticmethod
    def calculate_character_ac(character):
        """
        Calculate character's armor class based on equipped items.
        
        Args:
            character (Character): The character
            
        Returns:
            int: Calculated armor class
        """
        base_ac = 10 + character.dexterity_modifier
        
        # Find equipped armor
        equipped_items = EquipmentManager.get_character_equipped_items(character)
        
        # Check for armor
        armor = equipped_items.get('armor')
        if armor and armor.base_ac:
            if armor.armor_type == 'light':
                base_ac = armor.base_ac + character.dexterity_modifier
            elif armor.armor_type == 'medium':
                base_ac = armor.base_ac + min(character.dexterity_modifier, 2)
            elif armor.armor_type == 'heavy':
                base_ac = armor.base_ac
        
        # Add shield bonus
        shield = equipped_items.get('shield')
        if shield and shield.base_ac:
            base_ac += shield.base_ac
        
        # Add enchantment bonuses (if any)
        for item in equipped_items.values():
            if item.enchantment_bonus:
                base_ac += item.enchantment_bonus
        
        return base_ac
    
    @staticmethod
    def get_available_equipment_slots():
        """Get list of available equipment slots."""
        return [slot.value for slot in EquipmentSlot]