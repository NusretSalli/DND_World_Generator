# items.py

from enum import Enum

class ItemRarity(Enum):
    """Item rarity levels following D&D 5E standards."""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    VERY_RARE = "very_rare"
    LEGENDARY = "legendary"
    ARTIFACT = "artifact"

class ItemType(Enum):
    """Item types for better categorization."""
    WEAPON = "weapon"
    ARMOR = "armor"
    SHIELD = "shield"
    GEAR = "gear"
    TOOL = "tool"
    CONSUMABLE = "consumable"
    MAGIC_ITEM = "magic_item"
    TREASURE = "treasure"

class Item:
    """Base class for all items."""
    def __init__(self, name, description, weight, value, rarity=ItemRarity.COMMON, 
                 magical=False, requires_attunement=False, tags=None):
        self.name = name
        self.description = description
        self.weight = weight
        self.value = value  # in gold pieces
        self.rarity = rarity
        self.magical = magical
        self.requires_attunement = requires_attunement
        self.tags = tags or []  # For flexible categorization
        self.effects = []  # For storing item effects on character stats

    def __repr__(self):
        return f"{self.name}"
    
    def add_effect(self, effect_type, value, description=""):
        """Add an effect that this item provides when equipped."""
        self.effects.append({
            'type': effect_type,
            'value': value,
            'description': description
        })
    
    def get_effects_summary(self):
        """Get a human-readable summary of item effects."""
        if not self.effects:
            return ""
        return "; ".join([f"{e['type']}: {e['value']}" for e in self.effects])

class Gear(Item):
    """Class for general gear."""
    def __init__(self, name, description, weight, value, rarity=ItemRarity.COMMON, 
                 magical=False, requires_attunement=False, gear_type="miscellaneous", tags=None):
        super().__init__(name, description, weight, value, rarity, magical, requires_attunement, tags)
        self.item_type = ItemType.GEAR
        self.gear_type = gear_type  # adventuring_gear, tools, consumable, etc.

class Weapon(Item):
    """Class for weapons."""
    def __init__(self, name, description, weight, value, damage, damage_type, 
                 rarity=ItemRarity.COMMON, magical=False, requires_attunement=False,
                 properties=None, weapon_type="simple", tags=None):
        super().__init__(name, description, weight, value, rarity, magical, requires_attunement, tags)
        self.item_type = ItemType.WEAPON
        self.damage = damage
        self.damage_type = damage_type
        self.properties = properties if properties else []
        self.weapon_type = weapon_type  # simple, martial
        self.enchantment_bonus = 0  # For magical weapons (+1, +2, +3)
    
    def set_magical_bonus(self, bonus):
        """Set magical enhancement bonus."""
        self.enchantment_bonus = bonus
        self.magical = True
        if bonus > 0:
            self.add_effect("attack_bonus", bonus, f"+{bonus} to attack and damage rolls")
            self.add_effect("damage_bonus", bonus)

class Armor(Item):
    """Class for armor and shields."""
    def __init__(self, name, description, weight, value, base_ac, armor_type, 
                 rarity=ItemRarity.COMMON, magical=False, requires_attunement=False,
                 strength_req=0, stealth_disadvantage=False, tags=None):
        super().__init__(name, description, weight, value, rarity, magical, requires_attunement, tags)
        self.item_type = ItemType.ARMOR if armor_type != 'shield' else ItemType.SHIELD
        self.base_ac = base_ac
        self.armor_type = armor_type  # light, medium, heavy, shield
        self.strength_req = strength_req
        self.stealth_disadvantage = stealth_disadvantage
        self.enchantment_bonus = 0  # For magical armor (+1, +2, +3)
    
    def set_magical_bonus(self, bonus):
        """Set magical enhancement bonus."""
        self.enchantment_bonus = bonus
        self.magical = True
        if bonus > 0:
            self.add_effect("ac_bonus", bonus, f"+{bonus} to AC")

class MagicItem(Item):
    """Class for magical items that don't fit other categories."""
    def __init__(self, name, description, weight, value, rarity=ItemRarity.UNCOMMON,
                 requires_attunement=False, charges=None, tags=None):
        super().__init__(name, description, weight, value, rarity, magical=True, 
                        requires_attunement=requires_attunement, tags=tags)
        self.item_type = ItemType.MAGIC_ITEM
        self.charges = charges  # For items with limited uses
        self.max_charges = charges

class Consumable(Item):
    """Class for consumable items like potions, scrolls, etc."""
    def __init__(self, name, description, weight, value, uses=1, 
                 rarity=ItemRarity.COMMON, magical=False, tags=None):
        super().__init__(name, description, weight, value, rarity, magical, 
                        requires_attunement=False, tags=tags)
        self.item_type = ItemType.CONSUMABLE
        self.uses = uses
        self.max_uses = uses

# Equipment Slot System for Characters
class EquipmentSlot(Enum):
    """Equipment slots for character gear."""
    MAIN_HAND = "main_hand"
    OFF_HAND = "off_hand"
    ARMOR = "armor"
    SHIELD = "shield"
    HELMET = "helmet"
    GLOVES = "gloves"
    BOOTS = "boots"
    CLOAK = "cloak"
    RING_1 = "ring_1"
    RING_2 = "ring_2"
    AMULET = "amulet"
    BELT = "belt"

class CharacterEquipment:
    """Manages character equipment slots."""
    def __init__(self):
        self.slots = {slot: None for slot in EquipmentSlot}
        self.attuned_items = []  # List of items requiring attunement
    
    def equip_item(self, item, slot):
        """Equip an item to a specific slot."""
        if slot not in self.slots:
            return False, "Invalid equipment slot"
        
        # Check if slot is compatible with item type
        if not self._is_slot_compatible(item, slot):
            return False, f"Item {item.name} cannot be equipped to {slot.value}"
        
        # Check attunement requirements
        if item.requires_attunement and len(self.attuned_items) >= 3:
            if item not in self.attuned_items:
                return False, "Maximum of 3 attuned items allowed"
        
        # Unequip current item if any
        current_item = self.slots[slot]
        if current_item:
            self.unequip_item(slot)
        
        # Equip new item
        self.slots[slot] = item
        if item.requires_attunement and item not in self.attuned_items:
            self.attuned_items.append(item)
        
        return True, f"Equipped {item.name} to {slot.value}"
    
    def unequip_item(self, slot):
        """Unequip an item from a specific slot."""
        item = self.slots[slot]
        if item:
            self.slots[slot] = None
            if item in self.attuned_items:
                self.attuned_items.remove(item)
            return item
        return None
    
    def _is_slot_compatible(self, item, slot):
        """Check if an item can be equipped to a specific slot."""
        # Handle both database Item objects and item definition objects
        item_type_value = item.item_type
        if hasattr(item_type_value, 'value'):
            item_type_value = item_type_value.value
        elif hasattr(item, 'item_type') and hasattr(item.item_type, 'value'):
            item_type_value = item.item_type.value
            
        compatibility = {
            EquipmentSlot.MAIN_HAND: ["weapon"],
            EquipmentSlot.OFF_HAND: ["weapon", "shield"],
            EquipmentSlot.ARMOR: ["armor"],
            EquipmentSlot.SHIELD: ["shield"],
            EquipmentSlot.HELMET: ["gear", "magic_item"],
            EquipmentSlot.GLOVES: ["gear", "magic_item"],
            EquipmentSlot.BOOTS: ["gear", "magic_item"],
            EquipmentSlot.CLOAK: ["gear", "magic_item"],
            EquipmentSlot.RING_1: ["gear", "magic_item"],
            EquipmentSlot.RING_2: ["gear", "magic_item"],
            EquipmentSlot.AMULET: ["gear", "magic_item"],
            EquipmentSlot.BELT: ["gear", "magic_item"],
        }
        
        return item_type_value in compatibility.get(slot, [])
    
    def get_equipped_items(self):
        """Get all currently equipped items."""
        return {slot: item for slot, item in self.slots.items() if item is not None}
    
    def get_total_ac(self, base_ac=10):
        """Calculate total AC from equipped items."""
        total_ac = base_ac
        
        # Add armor AC
        armor = self.slots.get(EquipmentSlot.ARMOR)
        if armor and hasattr(armor, 'base_ac') and armor.base_ac:
            enchantment_bonus = getattr(armor, 'enchantment_bonus', 0) or 0
            total_ac = armor.base_ac + enchantment_bonus
        
        # Add shield AC
        shield = self.slots.get(EquipmentSlot.SHIELD)
        if shield and hasattr(shield, 'base_ac') and shield.base_ac:
            enchantment_bonus = getattr(shield, 'enchantment_bonus', 0) or 0
            total_ac += shield.base_ac + enchantment_bonus
        
        # Add magical AC bonuses from other items
        for item in self.slots.values():
            if item and hasattr(item, 'get_effects_list'):
                effects = item.get_effects_list()
                for effect in effects:
                    if isinstance(effect, dict) and effect.get('type') == 'ac_bonus':
                        try:
                            total_ac += int(effect['value'])
                        except (ValueError, TypeError):
                            continue
        
        return total_ac

# --- Item Definitions ---

# Enhanced Gear with categories

# Gear
GEAR = {
    'Abacus': Gear('Abacus', 'A tool for performing calculations.', 2, 2),
    'Acid (vial)': Gear('Acid (vial)', 'As an action, you can splash the contents of this vial onto a creature within 5 feet of you or throw the vial up to 20 feet, shattering it on impact.', 1, 25),
    'Alchemist\'s fire (flask)': Gear('Alchemist\'s fire (flask)', 'This sticky, adhesive fluid ignites when exposed to air.', 1, 50),
    'Amulet': Gear('Amulet', 'A holy symbol, can be used as a spellcasting focus.', 1, 5),
    'Antitoxin (vial)': Gear('Antitoxin (vial)', 'A creature that drinks this vial of liquid gains advantage on saving throws against poison for 1 hour.', 0, 50),
    'Backpack': Gear('Backpack', 'A sturdy backpack that can hold 1 cubic foot/30 pounds of gear.', 5, 2),
    'Ball bearings (bag of 1,000)': Gear('Ball bearings (bag of 1,000)', 'As an action, you can spill these tiny metal balls from their pouch to cover a level, square area 10 feet on a side.', 2, 1),
    'Barrel': Gear('Barrel', 'A large wooden barrel.', 70, 2),
    'Basket': Gear('Basket', 'A simple woven basket.', 2, 0.4),
    'Bedroll': Gear('Bedroll', 'A warm bedroll for resting.', 7, 1),
    'Bell': Gear('Bell', 'A small, handheld bell.', 0, 1),
    'Blanket': Gear('Blanket', 'A warm, woolen blanket.', 3, 0.5),
    'Block and tackle': Gear('Block and tackle', 'A set of pulleys with a cable threaded through them and a hook to attach to objects, a block and tackle allows you to hoist up to four times the weight you can normally lift.', 5, 1),
    'Book': Gear('Book', 'A book might contain poetry, historical accounts, information pertaining to a particular field of lore, diagrams and notes on gnomish contraptions, or just about anything else that can be represented using text or pictures.', 5, 25),
    'Bottle, glass': Gear('Bottle, glass', 'A glass bottle.', 2, 2),
    'Bucket': Gear('Bucket', 'A simple wooden bucket.', 2, 0.05),
    'Caltrops (bag of 20)': Gear('Caltrops (bag of 20)', 'As an action, you can spread a single bag of caltrops to cover a square area that is 5 feet on a side.', 2, 1),
    'Candle': Gear('Candle', 'For 1 hour, a candle sheds bright light in a 5-foot radius and dim light for an additional 5 feet.', 0, 0.01),
    'Case, crossbow bolt': Gear('Case, crossbow bolt', 'This wooden case can hold up to twenty crossbow bolts.', 1, 1),
    'Case, map or scroll': Gear('Case, map or scroll', 'This cylindrical leather case can hold up to ten rolled-up sheets of paper or five rolled-up sheets of parchment.', 1, 1),
    'Chain (10 feet)': Gear('Chain (10 feet)', 'A chain has 10 hit points. It can be burst with a successful DC 20 Strength check.', 10, 5),
    'Chalk (1 piece)': Gear('Chalk (1 piece)', 'A piece of chalk for marking surfaces.', 0, 0.01),
    'Chest': Gear('Chest', 'A wooden chest.', 25, 5),
    'Climber\'s kit': Gear('Climber\'s kit', 'This kit includes special pitons, boot tips, gloves, and a harness.', 12, 25),
    'Clothes, common': Gear('Clothes, common', 'Simple, functional clothing.', 3, 0.5),
    'Clothes, costume': Gear('Clothes, costume', 'Elaborate clothing for performances or special occasions.', 4, 5),
    'Clothes, fine': Gear('Clothes, fine', 'Well-made clothing for formal events.', 6, 15),
    'Clothes, traveler\'s': Gear('Clothes, traveler\'s', 'Sturdy clothing for long journeys.', 4, 2),
    'Component pouch': Gear('Component pouch', 'A small pouch for holding spell components.', 2, 25),
    'Crowbar': Gear('Crowbar', 'Using a crowbar grants advantage to Strength checks where the crowbar\'s leverage can be applied.', 5, 2),
    'Crystal': Gear('Crystal', 'A crystal, can be used as a spellcasting focus.', 1, 10),
    'Emblem': Gear('Emblem', 'A holy symbol, can be used as a spellcasting focus.', 0, 5),
    'Fishing tackle': Gear('Fishing tackle', 'This kit includes a wooden rod, silken line, corkwood bobbers, steel hooks, lead sinkers, velvet lures, and narrow netting.', 4, 1),
    'Flask or tankard': Gear('Flask or tankard', 'A simple container for liquids.', 1, 0.02),
    'Grappling hook': Gear('Grappling hook', 'A hook with barbs, for climbing.', 4, 2),
    'Hammer': Gear('Hammer', 'A standard hammer.', 3, 1),
    'Hammer, sledge': Gear('Hammer, sledge', 'A heavy hammer for driving spikes or smashing objects.', 10, 2),
    'Healer\'s kit': Gear('Healer\'s kit', 'This kit is a leather pouch containing bandages, salves, and splints. The kit has ten uses.', 3, 5),
    'Holy Symbol': Gear('Holy Symbol', 'A representation of a god or pantheon.', 1, 5),
    'Holy water (flask)': Gear('Holy water (flask)', 'As an action, you can splash the contents of this flask onto a creature within 5 feet of you or throw it up to 20 feet, shattering it on impact.', 1, 25),
    'Hourglass': Gear('Hourglass', 'A device for measuring time.', 1, 25),
    'Hunting trap': Gear('Hunting trap', 'When you use your action to set it, this trap forms a saw-toothed steel ring that snaps shut when a creature steps on a pressure plate in the center.', 25, 5),
    'Ink (1 ounce bottle)': Gear('Ink (1 ounce bottle)', 'A small bottle of black ink.', 0, 10),
    'Ink pen': Gear('Ink pen', 'A simple quill pen.', 0, 0.02),
    'Jug or pitcher': Gear('Jug or pitcher', 'A container for liquids.', 4, 0.02),
    'Ladder (10-foot)': Gear('Ladder (10-foot)', 'A straight, 10-foot ladder.', 25, 0.1),
    'Lamp': Gear('Lamp', 'A lamp sheds bright light in a 15-foot radius and dim light for an additional 30 feet. Once lit, it burns for 6 hours on one flask (1 pint) of oil.', 1, 0.5),
    'Lantern, bullseye': Gear('Lantern, bullseye', 'A bullseye lantern casts bright light in a 60-foot cone and dim light in an additional 60-foot cone.', 2, 10),
    'Lantern, hooded': Gear('Lantern, hooded', 'A hooded lantern casts bright light in a 30-foot radius and dim light for an additional 30 feet.', 2, 5),
    'Lock': Gear('Lock', 'A key is provided with the lock. Without the key, a creature proficient with thieves\' tools can pick this lock with a successful DC 15 Dexterity check.', 1, 10),
    'Magnifying glass': Gear('Magnifying glass', 'This lens allows a closer look at small objects.', 0, 100),
    'Manacles': Gear('Manacles', 'These metal restraints can bind a Small or Medium creature.', 6, 2),
    'Mess kit': Gear('Mess kit', 'A tin box containing a cup and simple cutlery.', 1, 0.2),
    'Mirror, steel': Gear('Mirror, steel', 'A small, polished steel mirror.', 0.5, 5),
    'Oil (flask)': Gear('Oil (flask)', 'Usually sold in a clay flask that holds 1 pint.', 1, 0.1),
    'Paper (one sheet)': Gear('Paper (one sheet)', 'A single sheet of paper.', 0, 0.2),
    'Parchment (one sheet)': Gear('Parchment (one sheet)', 'A single sheet of parchment.', 0, 0.1),
    'Perfume (vial)': Gear('Perfume (vial)', 'A small vial of perfume.', 0, 5),
    'Pick, miner\'s': Gear('Pick, miner\'s', 'A heavy-duty pick for mining.', 10, 2),
    'Piton': Gear('Piton', 'A small metal spike.', 0.25, 0.05),
    'Poison, basic (vial)': Gear('Poison, basic (vial)', 'You can use the poison in this vial to coat one slashing or piercing weapon or up to three pieces of ammunition.', 0, 100),
    'Pole (10-foot)': Gear('Pole (10-foot)', 'A 10-foot long wooden pole.', 7, 0.05),
    'Pot, iron': Gear('Pot, iron', 'A sturdy iron pot.', 10, 2),
    'Potion of healing': Gear('Potion of healing', 'A character who drinks the magical red fluid in this vial regains 2d4 + 2 hit points.', 0.5, 50),
    'Pouch': Gear('Pouch', 'A cloth or leather pouch can hold up to 20 sling bullets or 50 sling stones, or other things.', 1, 0.5),
    'Quiver': Gear('Quiver', 'A quiver can hold up to 20 arrows.', 1, 1),
    'Ram, portable': Gear('Ram, portable', 'You can use a portable ram to break down doors.', 35, 4),
    'Rations (1 day)': Gear('Rations (1 day)', 'Dried food and jerky, enough for one day.', 2, 0.5),
    'Reliquary': Gear('Reliquary', 'A holy symbol, can be used as a spellcasting focus.', 2, 5),
    'Robes': Gear('Robes', 'Simple, flowing robes.', 4, 1),
    'Rod': Gear('Rod', 'A rod, can be used as a spellcasting focus.', 2, 10),
    'Rope, hempen (50 feet)': Gear('Rope, hempen (50 feet)', 'A coil of strong rope.', 10, 1),
    'Rope, silk (50 feet)': Gear('Rope, silk (50 feet)', 'A coil of smooth, strong rope.', 5, 10),
    'Sack': Gear('Sack', 'A simple cloth sack.', 0.5, 0.01),
    'Scale, merchant\'s': Gear('Scale, merchant\'s', 'A scale includes a small balance, pans, and a suitable assortment of weights up to 2 pounds.', 3, 5),
    'Sealing wax': Gear('Sealing wax', 'A stick of sealing wax.', 0, 0.5),
    'Shovel': Gear('Shovel', 'A tool for digging.', 5, 2),
    'Signal whistle': Gear('Signal whistle', 'A small whistle for signaling.', 0, 0.05),
    'Signet ring': Gear('Signet ring', 'A ring used to stamp a personal seal.', 0, 5),
    'Soap': Gear('Soap', 'A bar of soap.', 0, 0.02),
    'Spellbook': Gear('Spellbook', 'A book for recording spells (for wizards).', 3, 50),
    'Spikes, iron (10)': Gear('Spikes, iron (10)', 'A set of 10 iron spikes.', 5, 1),
    'Spyglass': Gear('Spyglass', 'Objects viewed through a spyglass are magnified to twice their size.', 1, 1000),
    'Staff': Gear('Staff', 'A staff, can be used as a spellcasting focus.', 4, 5),
    'Tent, two-person': Gear('Tent, two-person', 'A simple tent that can house two people.', 20, 2),
    'Tinderbox': Gear('Tinderbox', 'Contains flint, fire steel, and tinder for starting fires.', 1, 0.5),
    'Torch': Gear('Torch', 'A wooden rod with a rag soaked in oil, burns for 1 hour.', 1, 0.01),
    'Vial': Gear('Vial', 'A small glass vial.', 0, 1),
    'Wand': Gear('Wand', 'A wand, can be used as a spellcasting focus.', 1, 10),
    'Waterskin': Gear('Waterskin', 'A leather container for water, holds 4 pints.', 5, 0.2),
    'Whetstone': Gear('Whetstone', 'A stone for sharpening blades.', 1, 0.01),
}

# Weapons
WEAPONS = {
    # Simple Melee
    'Club': Weapon('Club', 'A simple wooden club.', 2, 0.1, '1d4', 'bludgeoning'),
    'Dagger': Weapon('Dagger', 'A simple dagger.', 1, 2, '1d4', 'piercing', ['finesse', 'light', 'thrown (range 20/60)']),
    'Greatclub': Weapon('Greatclub', 'A two-handed wooden club.', 10, 0.2, '1d8', 'bludgeoning', ['two-handed']),
    'Handaxe': Weapon('Handaxe', 'Can be used as a melee or thrown weapon.', 2, 5, '1d6', 'slashing', ['light', 'thrown (range 20/60)']),
    'Javelin': Weapon('Javelin', 'A light spear designed for throwing.', 2, 0.5, '1d6', 'piercing', ['thrown (range 30/120)']),
    'Light Hammer': Weapon('Light Hammer', 'Can be used as a melee or thrown weapon.', 2, 2, '1d4', 'bludgeoning', ['light', 'thrown (range 20/60)']),
    'Mace': Weapon('Mace', 'A blunt weapon with a heavy head.', 4, 5, '1d6', 'bludgeoning'),
    'Quarterstaff': Weapon('Quarterstaff', 'A wooden staff.', 4, 0.2, '1d6', 'bludgeoning', ['versatile (1d8)']),
    'Sickle': Weapon('Sickle', 'A curved blade.', 2, 1, '1d4', 'slashing', ['light']),
    'Spear': Weapon('Spear', 'A pole weapon with a pointed head.', 3, 1, '1d6', 'piercing', ['thrown (range 20/60)', 'versatile (1d8)']),

    # Simple Ranged
    'Light Crossbow': Weapon('Light Crossbow', 'A simple crossbow.', 5, 25, '1d8', 'piercing', ['ammunition (range 80/320)', 'loading', 'two-handed']),
    'Dart': Weapon('Dart', 'A small, thrown projectile.', 0.25, 0.05, '1d4', 'piercing', ['finesse', 'thrown (range 20/60)']),
    'Shortbow': Weapon('Shortbow', 'A small bow.', 2, 25, '1d6', 'piercing', ['ammunition (range 80/320)', 'two-handed']),
    'Sling': Weapon('Sling', 'A simple ranged weapon.', 0, 0.1, '1d4', 'bludgeoning', ['ammunition (range 30/120)']),

    # Martial Melee
    'Battleaxe': Weapon('Battleaxe', 'A powerful axe.', 4, 10, '1d8', 'slashing', ['versatile (1d10)']),
    'Flail': Weapon('Flail', 'A weapon with a striking head attached to a handle by a flexible chain.', 2, 10, '1d8', 'bludgeoning'),
    'Glaive': Weapon('Glaive', 'A polearm with a single-edged blade on the end.', 6, 20, '1d10', 'slashing', ['heavy', 'reach', 'two-handed']),
    'Greataxe': Weapon('Greataxe', 'A large, two-handed axe.', 7, 30, '1d12', 'slashing', ['heavy', 'two-handed']),
    'Greatsword': Weapon('Greatsword', 'A large two-handed sword.', 6, 50, '2d6', 'slashing', ['heavy', 'two-handed']),
    'Halberd': Weapon('Halberd', 'A two-handed pole weapon.', 6, 20, '1d10', 'slashing', ['heavy', 'reach', 'two-handed']),
    'Lance': Weapon('Lance', 'A long weapon for use on horseback.', 6, 10, '1d12', 'piercing', ['reach', 'special']),
    'Longsword': Weapon('Longsword', 'A versatile and widely used sword.', 3, 15, '1d8', 'slashing', ['versatile (1d10)']),
    'Maul': Weapon('Maul', 'A massive hammer.', 10, 10, '2d6', 'bludgeoning', ['heavy', 'two-handed']),
    'Morningstar': Weapon('Morningstar', 'A spiked club.', 4, 15, '1d8', 'piercing'),
    'Pike': Weapon('Pike', 'A very long spear.', 18, 5, '1d10', 'piercing', ['heavy', 'reach', 'two-handed']),
    'Rapier': Weapon('Rapier', 'A thin, light sword for thrusting.', 2, 25, '1d8', 'piercing', ['finesse']),
    'Scimitar': Weapon('Scimitar', 'A curved, single-edged sword.', 3, 25, '1d6', 'slashing', ['finesse', 'light']),
    'Shortsword': Weapon('Shortsword', 'A light, double-edged sword.', 2, 10, '1d6', 'piercing', ['finesse', 'light']),
    'Trident': Weapon('Trident', 'A three-pronged spear.', 4, 5, '1d6', 'piercing', ['thrown (range 20/60)', 'versatile (1d8)']),
    'War pick': Weapon('War pick', 'A pointed weapon for piercing armor.', 2, 5, '1d8', 'piercing'),
    'Warhammer': Weapon('Warhammer', 'A heavy hammer for combat.', 2, 15, '1d8', 'bludgeoning', ['versatile (1d10)']),
    'Whip': Weapon('Whip', 'A flexible weapon.', 3, 2, '1d4', 'slashing', ['finesse', 'reach']),

    # Martial Ranged
    'Blowgun': Weapon('Blowgun', 'A tube for shooting darts.', 1, 10, '1', 'piercing', ['ammunition (range 25/100)', 'loading']),
    'Hand Crossbow': Weapon('Hand Crossbow', 'A small crossbow that can be used with one hand.', 3, 75, '1d6', 'piercing', ['ammunition (range 30/120)', 'light', 'loading']),
    'Heavy Crossbow': Weapon('Heavy Crossbow', 'A powerful crossbow.', 18, 50, '1d10', 'piercing', ['ammunition (range 100/400)', 'heavy', 'loading', 'two-handed']),
    'Longbow': Weapon('Longbow', 'A large, powerful bow.', 2, 50, '1d8', 'piercing', ['ammunition (range 150/600)', 'heavy', 'two-handed']),
    'Net': Weapon('Net', 'A net for entangling creatures.', 3, 1, '', '', ['special', 'thrown (range 5/15)']),
}

# Armor
ARMOR = {
    # Light Armor
    'Padded': Armor('Padded', 'Padded armor made of quilted layers of cloth and batting.', 8, 5, 11, 'light', stealth_disadvantage=True),
    'Leather': Armor('Leather', 'Armor made from stiff, boiled leather.', 10, 10, 11, 'light'),
    'Studded Leather': Armor('Studded Leather', 'Leather armor reinforced with rivets.', 13, 45, 12, 'light'),

    # Medium Armor
    'Hide': Armor('Hide', 'Armor made from thick furs and pelts.', 12, 10, 12, 'medium'),
    'Chain Shirt': Armor('Chain Shirt', 'A shirt made of interlocking metal rings.', 20, 50, 13, 'medium'),
    'Scale Mail': Armor('Scale Mail', 'Armor with overlapping pieces of metal, like fish scales.', 45, 50, 14, 'medium', stealth_disadvantage=True),
    'Breastplate': Armor('Breastplate', 'A metal plate that covers the torso.', 20, 400, 14, 'medium'),
    'Half Plate': Armor('Half Plate', 'Armor that consists of shaped metal plates that cover most of the body.', 40, 750, 15, 'medium', stealth_disadvantage=True),

    # Heavy Armor
    'Ring Mail': Armor('Ring Mail', 'Leather armor with heavy rings sewn into it.', 40, 30, 14, 'heavy', stealth_disadvantage=True),
    'Chain Mail': Armor('Chain Mail', 'Heavy armor made of interlocking metal rings.', 55, 75, 16, 'heavy', strength_req=13, stealth_disadvantage=True),
    'Splint': Armor('Splint', 'Armor made of narrow vertical strips of metal.', 60, 200, 17, 'heavy', strength_req=15, stealth_disadvantage=True),
    'Plate': Armor('Plate', 'Full plate armor.', 65, 1500, 18, 'heavy', strength_req=15, stealth_disadvantage=True),

    # Shields
    'Shield': Armor('Shield', 'A wooden or metal shield carried in one hand.', 6, 10, 2, 'shield'),
}

# --- Class Starting Equipment ---

CLASS_EQUIPMENT = {
    'barbarian': {
        'gear': [GEAR['Backpack'], GEAR['Bedroll'], GEAR['Mess kit'], GEAR['Tinderbox'], GEAR['Torch'], GEAR['Rations (1 day)']],
        'weapons': [WEAPONS['Greataxe'], WEAPONS['Handaxe'], WEAPONS['Javelin']],
        'armor': []
    },
    'bard': {
        'gear': [GEAR['Backpack'], GEAR['Bedroll'], GEAR['Candle'], GEAR['Rations (1 day)']],
        'weapons': [WEAPONS['Rapier'], WEAPONS['Dagger']],
        'armor': [ARMOR['Leather']]
    },
    'cleric': {
        'gear': [GEAR['Backpack'], GEAR['Blanket'], GEAR['Tinderbox'], GEAR['Holy Symbol'], GEAR['Rations (1 day)']],
        'weapons': [WEAPONS['Mace']],
        'armor': [ARMOR['Chain Mail'], ARMOR['Shield']]
    },
    'druid': {
        'gear': [GEAR['Backpack'], GEAR['Bedroll'], GEAR['Mess kit'], GEAR['Rations (1 day)']],
        'weapons': [WEAPONS['Scimitar']],
        'armor': [ARMOR['Leather'], ARMOR['Shield']]
    },
    'fighter': {
        'gear': [GEAR['Backpack'], GEAR['Bedroll'], GEAR['Mess kit'], GEAR['Tinderbox'], GEAR['Torch'], GEAR['Rations (1 day)']],
        'weapons': [WEAPONS['Longsword']],
        'armor': [ARMOR['Chain Mail'], ARMOR['Shield']]
    },
    'monk': {
        'gear': [GEAR['Backpack'], GEAR['Bedroll'], GEAR['Mess kit'], GEAR['Rations (1 day)']],
        'weapons': [WEAPONS['Shortsword']],
        'armor': []
    },
    'paladin': {
        'gear': [GEAR['Backpack'], GEAR['Bedroll'], GEAR['Mess kit'], GEAR['Tinderbox'], GEAR['Holy Symbol'], GEAR['Rations (1 day)']],
        'weapons': [WEAPONS['Longsword']],
        'armor': [ARMOR['Chain Mail'], ARMOR['Shield']]
    },
    'ranger': {
        'gear': [GEAR['Backpack'], GEAR['Bedroll'], GEAR['Mess kit'], GEAR['Tinderbox'], GEAR['Rations (1 day)']],
        'weapons': [WEAPONS['Shortsword'], WEAPONS['Longbow']],
        'armor': [ARMOR['Leather']]
    },
    'rogue': {
        'gear': [GEAR['Backpack'], GEAR['Tinderbox'], GEAR['Rations (1 day)']],
        'weapons': [WEAPONS['Shortsword'], WEAPONS['Dagger']],
        'armor': [ARMOR['Leather']]
    },
    'sorcerer': {
        'gear': [GEAR['Backpack'], GEAR['Bedroll'], GEAR['Candle'], GEAR['Rations (1 day)']],
        'weapons': [WEAPONS['Light Crossbow'], WEAPONS['Dagger']],
        'armor': []
    },
    'warlock': {
        'gear': [GEAR['Backpack'], GEAR['Bedroll'], GEAR['Candle'], GEAR['Rations (1 day)']],
        'weapons': [WEAPONS['Light Crossbow'], WEAPONS['Dagger']],
        'armor': [ARMOR['Leather']]
    },
    'wizard': {
        'gear': [GEAR['Backpack'], GEAR['Spellbook'], GEAR['Component pouch'], GEAR['Rations (1 day)']],
        'weapons': [WEAPONS['Quarterstaff']],
        'armor': []
    },
}

# Enhanced Weapons with magical options
ENHANCED_WEAPONS = {
    # Add some magical weapons as examples
    'Longsword +1': Weapon('Longsword +1', 'A magically enhanced longsword.', 3, 315, '1d8', 'slashing', 
                           ItemRarity.UNCOMMON, magical=True, properties=['versatile (1d10)']),
    'Flame Tongue': Weapon('Flame Tongue', 'This magic sword\'s blade is wreathed in flames.', 3, 5000, '1d8', 'slashing',
                          ItemRarity.RARE, magical=True, requires_attunement=True, properties=['versatile (1d10)']),
    'Dagger of Venom': Weapon('Dagger of Venom', 'A dagger coated with magical poison.', 1, 500, '1d4', 'piercing',
                             ItemRarity.RARE, magical=True, properties=['finesse', 'light', 'thrown (range 20/60)']),
}

# Initialize magical weapons with proper effects
ENHANCED_WEAPONS['Longsword +1'].set_magical_bonus(1)
ENHANCED_WEAPONS['Flame Tongue'].set_magical_bonus(1)
ENHANCED_WEAPONS['Flame Tongue'].add_effect("fire_damage", "2d6", "Extra fire damage on critical hit")
ENHANCED_WEAPONS['Dagger of Venom'].add_effect("poison_damage", "2d10", "Poison damage (DC 15 Constitution save)")

# Magical Items
MAGIC_ITEMS = {
    'Ring of Protection': MagicItem('Ring of Protection', 'Grants protection to the wearer.', 0, 3500,
                                   ItemRarity.RARE, requires_attunement=True, tags=['ring', 'protection']),
    'Cloak of Elvenkind': MagicItem('Cloak of Elvenkind', 'Grants stealth bonuses.', 1, 5000,
                                   ItemRarity.UNCOMMON, requires_attunement=True, tags=['cloak', 'stealth']),
    'Bag of Holding': MagicItem('Bag of Holding', 'Extradimensional storage space.', 15, 4000,
                               ItemRarity.UNCOMMON, tags=['storage', 'utility']),
    'Boots of Speed': MagicItem('Boots of Speed', 'Doubles your speed for 10 minutes.', 1, 4000,
                               ItemRarity.RARE, requires_attunement=True, charges=3, tags=['boots', 'movement']),
}

# Add effects to magical items
MAGIC_ITEMS['Ring of Protection'].add_effect("ac_bonus", 1, "+1 to AC and saving throws")
MAGIC_ITEMS['Ring of Protection'].add_effect("saving_throw_bonus", 1)
MAGIC_ITEMS['Cloak of Elvenkind'].add_effect("stealth_advantage", 1, "Advantage on Dexterity (Stealth) checks")
MAGIC_ITEMS['Bag of Holding'].add_effect("carrying_capacity", 500, "500 lbs extra carrying capacity")

# Enhanced Consumables
CONSUMABLES = {
    'Potion of Healing': Consumable('Potion of Healing', 'Restores 2d4+2 hit points.', 0.5, 50, uses=1),
    'Potion of Greater Healing': Consumable('Potion of Greater Healing', 'Restores 4d4+4 hit points.', 0.5, 150, 
                                           uses=1, rarity=ItemRarity.UNCOMMON),
    'Scroll of Fireball': Consumable('Scroll of Fireball', 'Cast fireball spell (3rd level).', 0, 150, 
                                    uses=1, rarity=ItemRarity.UNCOMMON, magical=True),
    'Oil of Slipperiness': Consumable('Oil of Slipperiness', 'Makes surface or creature slippery.', 0.5, 480,
                                     uses=1, rarity=ItemRarity.UNCOMMON, magical=True),
}

# Add effects to consumables
CONSUMABLES['Potion of Healing'].add_effect("healing", "2d4+2", "Restore hit points")
CONSUMABLES['Potion of Greater Healing'].add_effect("healing", "4d4+4", "Restore hit points")

# Enhanced Armor with magical options  
ENHANCED_ARMOR = {
    # Add some magical armor
    'Leather Armor +1': Armor('Leather Armor +1', 'Magically enhanced leather armor.', 10, 160, 12, 'light',
                              ItemRarity.UNCOMMON, magical=True),
    'Studded Leather +2': Armor('Studded Leather +2', 'Powerfully enchanted studded leather.', 13, 1045, 14, 'light',
                                ItemRarity.RARE, magical=True),
    'Plate Armor of Fire Resistance': Armor('Plate Armor of Fire Resistance', 'Plate armor that protects against fire.', 65, 6500, 18, 'heavy',
                                           ItemRarity.RARE, magical=True, requires_attunement=True, strength_req=15, stealth_disadvantage=True),
}

# Initialize magical armor with effects
ENHANCED_ARMOR['Leather Armor +1'].set_magical_bonus(1)
ENHANCED_ARMOR['Studded Leather +2'].set_magical_bonus(2)
ENHANCED_ARMOR['Plate Armor of Fire Resistance'].add_effect("fire_resistance", 1, "Resistance to fire damage")

# Combined item collections for easy access
ALL_ITEMS = {
    **GEAR,
    **WEAPONS,
    **ENHANCED_WEAPONS,
    **ARMOR,
    **ENHANCED_ARMOR,
    **MAGIC_ITEMS,
    **CONSUMABLES,
}
