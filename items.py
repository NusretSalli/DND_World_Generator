# items.py

class Item:
    """Base class for all items."""
    def __init__(self, name, description, weight, value):
        self.name = name
        self.description = description
        self.weight = weight
        self.value = value  # in gold pieces

    def __repr__(self):
        return f"{self.name}"

class Gear(Item):
    """Class for general gear."""
    def __init__(self, name, description, weight, value):
        super().__init__(name, description, weight, value)
        self.item_type = 'gear'

class Weapon(Item):
    """Class for weapons."""
    def __init__(self, name, description, weight, value, damage, damage_type, properties=None):
        super().__init__(name, description, weight, value)
        self.item_type = 'weapon'
        self.damage = damage
        self.damage_type = damage_type
        self.properties = properties if properties else []

class Armor(Item):
    """Class for armor and shields."""
    def __init__(self, name, description, weight, value, base_ac, armor_type, strength_req=0, stealth_disadvantage=False):
        super().__init__(name, description, weight, value)
        self.item_type = 'armor'
        self.base_ac = base_ac
        self.armor_type = armor_type  # e.g., 'light', 'medium', 'heavy', 'shield'
        self.strength_req = strength_req
        self.stealth_disadvantage = stealth_disadvantage

# --- Item Definitions ---

# Gear
GEAR = {
    'Backpack': Gear('Backpack', 'A sturdy backpack that can hold 1 cubic foot/30 pounds of gear.', 5, 2),
    'Bedroll': Gear('Bedroll', 'A warm bedroll for resting.', 7, 1),
    'Rope, hempen (50 feet)': Gear('Rope, hempen (50 feet)', 'A coil of strong rope.', 10, 1),
    'Waterskin': Gear('Waterskin', 'A leather container for water, holds 4 pints.', 5, 0.2),
    'Tinderbox': Gear('Tinderbox', 'Contains flint, fire steel, and tinder for starting fires.', 1, 0.5),
    'Mess kit': Gear('Mess kit', 'A tin box containing a cup and simple cutlery.', 1, 0.2),
    'Torch': Gear('Torch', 'A wooden rod with a rag soaked in oil, burns for 1 hour.', 1, 0.01),
    'Rations (1 day)': Gear('Rations (1 day)', 'Dried food and jerky, enough for one day.', 2, 0.5),
    'Spellbook': Gear('Spellbook', 'A book for recording spells (for wizards).', 3, 50),
    'Component pouch': Gear('Component pouch', 'A small pouch for holding spell components.', 2, 25),
    'Holy Symbol': Gear('Holy Symbol', 'A representation of a god or pantheon.', 1, 5),
}

# Weapons
WEAPONS = {
    # Simple Melee
    'Dagger': Weapon('Dagger', 'A simple dagger.', 1, 2, '1d4', 'piercing', ['finesse', 'light', 'thrown (range 20/60)']),
    'Mace': Weapon('Mace', 'A blunt weapon with a heavy head.', 4, 5, '1d6', 'bludgeoning', []),
    'Quarterstaff': Weapon('Quarterstaff', 'A wooden staff.', 4, 0.2, '1d6', 'bludgeoning', ['versatile (1d8)']),
    
    # Martial Melee
    'Longsword': Weapon('Longsword', 'A versatile and widely used sword.', 3, 15, '1d8', 'slashing', ['versatile (1d10)']),
    'Shortsword': Weapon('Shortsword', 'A light, double-edged sword.', 2, 10, '1d6', 'piercing', ['finesse', 'light']),
}

# Armor
ARMOR = {
    # Light Armor
    'Leather': Armor('Leather', 'Armor made from stiff, boiled leather.', 10, 10, 11, 'light'),
    
    # Heavy Armor
    'Chain Mail': Armor('Chain Mail', 'Heavy armor made of interlocking metal rings.', 55, 75, 16, 'heavy', strength_req=13, stealth_disadvantage=True),

    # Shields
    'Shield': Armor('Shield', 'A wooden or metal shield carried in one hand.', 6, 10, 2, 'shield'),
}

# --- Class Starting Equipment ---

CLASS_EQUIPMENT = {
    'fighter': {
        'gear': [GEAR['Backpack'], GEAR['Bedroll'], GEAR['Mess kit'], GEAR['Tinderbox'], GEAR['Torch'], GEAR['Rations (1 day)']],
        'weapons': [WEAPONS['Longsword']],
        'armor': [ARMOR['Chain Mail'], ARMOR['Shield']]
    },
    'wizard': {
        'gear': [GEAR['Backpack'], GEAR['Spellbook'], GEAR['Component pouch'], GEAR['Rations (1 day)']],
        'weapons': [WEAPONS['Quarterstaff']],
        'armor': []
    },
    'rogue': {
        'gear': [GEAR['Backpack'], GEAR['Tinderbox'], GEAR['Rations (1 day)']],
        'weapons': [WEAPONS['Shortsword'], WEAPONS['Dagger']],
        'armor': [ARMOR['Leather']]
    },
    'cleric': {
        'gear': [GEAR['Backpack'], GEAR['Holy Symbol']],
        'weapons': [WEAPONS['Mace']],
        'armor': [ARMOR['Chain Mail'], ARMOR['Shield']]
    },
}
