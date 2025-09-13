from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from pynames import GENDER, LANGUAGE
from pynames.generators.elven import WarhammerNamesGenerator, DnDNamesGenerator
from pynames.generators.goblin import GoblinGenerator
from pynames.generators.korean import KoreanNamesGenerator
from pynames.generators.mongolian import MongolianNamesGenerator
from pynames.generators.orc import OrcNamesGenerator
from pynames.generators.russian import PaganNamesGenerator
from pynames.generators.scandinavian import ScandinavianNamesGenerator
import os
from items import CLASS_EQUIPMENT, ALL_ITEMS, CharacterEquipment, EquipmentSlot, ItemRarity, ItemType
from story import story_generator

# Initialize Flask application
app = Flask(__name__)
# Configure SQLAlchemy to use SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dnd_characters.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Initialize database and migration handling
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Item Model - Represents all objects that can be owned by characters
class Item(db.Model):
    """
    Database model for all items in the game.
    
    This model represents equipment, weapons, armor, and other objects that characters
    can possess. It contains both core properties shared by all items and specialized
    properties for different item types.
    """
    # Core properties
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    item_type = db.Column(db.String(50), nullable=False)  # weapon, armor, gear, etc.
    description = db.Column(db.Text)
    weight = db.Column(db.Float)
    value = db.Column(db.Integer)  # in gold pieces
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'))
    
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
            import json
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
        import json
        self.effects = json.dumps(effects_list) if effects_list else None
    
    def get_tags_list(self):
        """
        Parse tags JSON string into list.
        
        Returns:
            list: List of tags or empty list if none
        """
        if self.tags:
            import json
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
        import json
        self.tags = json.dumps(tags_list) if tags_list else None

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
    
    # Relationships - Link to items owned by this character
    inventory = db.relationship('Item', backref='owner', lazy=True)

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
    def carrying_capacity(self):
        return self.strength * 15  # Basic carrying capacity rules

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

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/generate_name')
def generate_name():
    race = request.args.get('race', 'human')
    gender_str = request.args.get('gender', 'male')
    
    gender = GENDER.MALE if gender_str == 'male' else GENDER.FEMALE
    
    generator = RACE_TO_GENERATOR.get(race, ScandinavianNamesGenerator())
    
    # Not all generators support gender, so we handle that
    try:
        name = generator.get_name_simple(gender)
    except TypeError:
        name = generator.get_name_simple()

    return jsonify(name=name)

def calculate_max_hp(char_class, constitution_mod, level=1):
    # Base HP calculation for D&D 5E
    class_hit_dice = {
        'barbarian': 12,
        'fighter': 10, 'paladin': 10, 'ranger': 10,
        'bard': 8, 'cleric': 8, 'druid': 8, 'monk': 8, 'rogue': 8, 'warlock': 8,
        'sorcerer': 6, 'wizard': 6
    }
    
    base_hp = class_hit_dice.get(char_class.lower(), 8)  # default to 8 if class not found
    
    # At 1st level, you get maximum hit dice + constitution modifier
    max_hp = base_hp + constitution_mod
    
    # For each level after 1st, add average hit dice + constitution modifier
    if level > 1:
        avg_hp_per_level = ((base_hp + 1) // 2) + constitution_mod  # average of hit dice + con mod
        max_hp += (level - 1) * avg_hp_per_level
    
    return max_hp

@app.route('/create_character', methods=['POST'])
def create_character():
    # Calculate ability modifiers
    constitution = int(request.form.get('constitution'))
    constitution_mod = (constitution - 10) // 2
    
    # Get character class and calculate HP
    char_class = request.form.get('class')
    max_hp = calculate_max_hp(char_class, constitution_mod)
    
    # Create a new character instance
    new_character = Character(
        name=request.form.get('name'),
        gender=request.form.get('gender'),
        race=request.form.get('race'),
        character_class=char_class,
        level=1,  # Starting at level 1
        experience=0,  # Starting with 0 XP
        max_hp=max_hp,
        current_hp=max_hp,  # Starting at full health
        armor_class=10 + ((int(request.form.get('dexterity')) - 10) // 2),  # Base AC + DEX modifier
        strength=int(request.form.get('strength')),
        dexterity=int(request.form.get('dexterity')),
        constitution=constitution,
        intelligence=int(request.form.get('intelligence')),
        wisdom=int(request.form.get('wisdom')),
        charisma=int(request.form.get('charisma')),
        gold=50  # Starting gold for most 5E characters
    )
    
    # Add and commit to database
    db.session.add(new_character)
    db.session.commit()
    
    # Add starting equipment based on class
    add_starting_equipment(new_character)
    
    return redirect(url_for('view_characters'))

def add_starting_equipment(character):
    """Add enhanced starting equipment based on character class"""
    char_class = character.character_class.lower()
    
    if char_class in CLASS_EQUIPMENT:
        equipment = CLASS_EQUIPMENT[char_class]
        
        # Add all items from the class equipment list
        for item_list in equipment.values():
            for item in item_list:
                # Convert item object to database item with enhanced properties
                character.add_item(
                    name=item.name,
                    item_type=item.item_type.value if hasattr(item.item_type, 'value') else str(item.item_type),
                    description=item.description,
                    weight=item.weight,
                    value=item.value,
                    rarity=item.rarity.value if hasattr(item.rarity, 'value') else str(item.rarity),
                    magical=item.magical,
                    requires_attunement=item.requires_attunement,
                    tags=item.tags,
                    effects=[{'type': e['type'], 'value': e['value'], 'description': e['description']} 
                            for e in item.effects],
                    # Weapon properties
                    damage=getattr(item, 'damage', None),
                    damage_type=getattr(item, 'damage_type', None),
                    weapon_properties=getattr(item, 'properties', []),
                    enchantment_bonus=getattr(item, 'enchantment_bonus', 0),
                    # Armor properties
                    base_ac=getattr(item, 'base_ac', None),
                    armor_type=getattr(item, 'armor_type', None),
                    strength_req=getattr(item, 'strength_req', 0),
                    stealth_disadvantage=getattr(item, 'stealth_disadvantage', False),
                    # Consumable properties
                    uses=getattr(item, 'uses', None),
                    max_uses=getattr(item, 'max_uses', None),
                    # Magical item properties
                    charges=getattr(item, 'charges', None),
                    max_charges=getattr(item, 'max_charges', None)
                )

@app.route('/characters')
def view_characters():
    characters = Character.query.all()
    return render_template('characters.html', characters=characters)

@app.route('/character/<int:character_id>/inventory')
def character_inventory(character_id):
    """View detailed character inventory and equipment."""
    character = Character.query.get_or_404(character_id)
    
    # Separate equipped and carried items
    equipped_items = Item.query.filter_by(character_id=character_id).filter(Item.equipped_slot.isnot(None)).all()
    carried_items = Item.query.filter_by(character_id=character_id).filter(Item.equipped_slot.is_(None)).all()
    
    # Get equipment slots info
    equipment_slots = {slot.value: None for slot in EquipmentSlot}
    for item in equipped_items:
        equipment_slots[item.equipped_slot] = item
    
    return render_template('inventory.html', 
                         character=character, 
                         equipped_items=equipped_items,
                         carried_items=carried_items,
                         equipment_slots=equipment_slots,
                         available_slots=EquipmentSlot)

@app.route('/character/<int:character_id>/equip/<int:item_id>', methods=['POST'])
def equip_item(character_id, item_id):
    """Equip an item to a character."""
    character = Character.query.get_or_404(character_id)
    slot_name = request.form.get('slot')
    
    success, message = character.equip_item(item_id, slot_name)
    
    if request.headers.get('Content-Type') == 'application/json':
        return jsonify({'success': success, 'message': message})
    else:
        return redirect(url_for('character_inventory', character_id=character_id))

@app.route('/character/<int:character_id>/unequip', methods=['POST'])
def unequip_item(character_id):
    """Unequip an item from a character."""
    character = Character.query.get_or_404(character_id)
    slot_name = request.form.get('slot')
    
    success, message = character.unequip_item(slot_name)
    
    if request.headers.get('Content-Type') == 'application/json':
        return jsonify({'success': success, 'message': message})
    else:
        return redirect(url_for('character_inventory', character_id=character_id))

@app.route('/character/<int:character_id>/add_item', methods=['GET', 'POST'])
def add_item_to_character(character_id):
    """Add a new item to character inventory."""
    character = Character.query.get_or_404(character_id)
    
    if request.method == 'POST':
        # Add item from form data
        item_name = request.form.get('item_name')
        
        # Check if it's a predefined item
        if item_name in ALL_ITEMS:
            item_template = ALL_ITEMS[item_name]
            character.add_item(
                name=item_template.name,
                item_type=item_template.item_type.value if hasattr(item_template.item_type, 'value') else str(item_template.item_type),
                description=item_template.description,
                weight=item_template.weight,
                value=item_template.value,
                rarity=item_template.rarity.value if hasattr(item_template.rarity, 'value') else str(item_template.rarity),
                magical=item_template.magical,
                requires_attunement=item_template.requires_attunement,
                tags=item_template.tags,
                effects=[{'type': e['type'], 'value': e['value'], 'description': e['description']} 
                        for e in item_template.effects]
            )
        else:
            # Create custom item
            character.add_item(
                name=request.form.get('item_name'),
                item_type=request.form.get('item_type', 'gear'),
                description=request.form.get('description', ''),
                weight=float(request.form.get('weight', 0)),
                value=int(request.form.get('value', 0))
            )
        
        return redirect(url_for('character_inventory', character_id=character_id))
    
    # GET request - show form
    return render_template('add_item.html', character=character, available_items=ALL_ITEMS)

@app.route('/delete_character/<int:character_id>', methods=['POST'])
def delete_character(character_id):
    character = Character.query.get_or_404(character_id)
    db.session.delete(character)
    db.session.commit()
    return redirect(url_for('view_characters'))

@app.route('/story')
def story_interface():
    """Main story interface for LLM interaction."""
    characters = Character.query.all()
    return render_template('story.html', characters=characters)

@app.route('/generate_story', methods=['POST'])
def generate_story():
    """Generate story content using the LLM."""
    try:
        prompt = request.form.get('prompt', '').strip()
        character_id = request.form.get('character_id')
        encounter_type = request.form.get('encounter_type')
        
        if not prompt and not encounter_type:
            return jsonify({'error': 'Please provide a story prompt or select an encounter type.'})
        
        character_context = ""
        if character_id:
            character = Character.query.get(character_id)
            if character:
                character_context = f"{character.name}, a level {character.level} {character.race} {character.character_class}"
        
        # Generate different types of content
        if encounter_type == 'random_encounter':
            level = 1
            if character_id:
                character = Character.query.get(character_id)
                if character:
                    level = character.level
            story_text = story_generator.generate_encounter(character_level=level)
        elif encounter_type == 'npc_dialogue':
            story_text = story_generator.generate_npc_dialogue()
        else:
            # Regular story continuation
            story_text = story_generator.generate_story_continuation(prompt, character_context)
        
        return jsonify({'story': story_text})
        
    except Exception as e:
        print(f"Error generating story: {e}")
        return jsonify({'error': 'Failed to generate story. The mystical forces are disrupted.'})

@app.route('/story_prompt_suggestions')
def story_prompt_suggestions():
    """Get suggested story prompts."""
    suggestions = [
        "The party enters a mysterious tavern where something seems off...",
        "A hooded figure approaches you on the road...",
        "You discover an ancient ruin hidden in the forest...",
        "The local villagers speak of strange disappearances...",
        "A treasure map leads you to a dangerous location...",
        "You hear rumors of a powerful artifact...",
        "The weather suddenly changes as dark clouds gather...",
        "You stumble upon a group of bandits arguing..."
    ]
    return jsonify({'suggestions': suggestions})

def upgrade_db():
    """Initialize and upgrade database."""
    with app.app_context():
        try:
            # Create all tables directly for development
            db.create_all()
            print("Database tables created/updated successfully")
        except Exception as e:
            print(f"Database setup: {e}")

if __name__ == '__main__':
    upgrade_db()  # Set up database
    app.run(debug=True)
