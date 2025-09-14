from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file
from sqlalchemy import event
from sqlalchemy.engine import Engine
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
import json
from items import CLASS_EQUIPMENT, ALL_ITEMS, CharacterEquipment, EquipmentSlot, ItemRarity, ItemType
from story import story_generator
from enemies import STANDARD_ENEMIES, get_enemy_by_name, get_random_enemy_for_level

# Initialize Flask application
app = Flask(__name__)
# Configure SQLAlchemy to use SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dnd_characters.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Initialize database and migration handling
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# ---- Spatial combat (in-memory grid state) ----
# Grid dimensions (tiles)
GRID_COLS = 20
GRID_ROWS = 15

# In-memory spatial state per combat_id
# { combat_id: { 'positions': {combatant_id: {'x': int,'y': int}}, 'initialized': bool } }
spatial_states = {}

def _manhattan(a, b):
    return abs(a['x'] - b['x']) + abs(a['y'] - b['y'])

def _init_spatial_positions(combat_id: int):
    """Place combatants on a grid: players on left, monsters on right."""
    combat = Combat.query.get(combat_id)
    if not combat:
        return
    positions = {}
    left_col = 1
    right_col = GRID_COLS - 2
    y_left = 1
    y_right = 1
    for c in sorted(combat.combatants, key=lambda x: x.initiative, reverse=True):
        is_monster = (c.character.character_class or '').lower() == 'monster'
        if is_monster:
            positions[c.id] = {'x': right_col, 'y': y_right}
            y_right = y_right + 2 if y_right + 2 < GRID_ROWS - 1 else 1
        else:
            positions[c.id] = {'x': left_col, 'y': y_left}
            y_left = y_left + 2 if y_left + 2 < GRID_ROWS - 1 else 1
    spatial_states[combat_id] = {'positions': positions, 'initialized': True}

def _get_spatial_state(combat_id: int):
    state = spatial_states.get(combat_id)
    if state is None or not state.get('initialized'):
        _init_spatial_positions(combat_id)
        state = spatial_states.get(combat_id)
    return state

def _is_occupied(positions: dict, x: int, y: int, ignore_id: int = None) -> bool:
    for cid, pos in positions.items():
        if ignore_id is not None and cid == ignore_id:
            continue
        if pos['x'] == x and pos['y'] == y:
            return True
    return False

def _place_new_combatant(combat_id: int, combatant: "Combatant"):
    state = _get_spatial_state(combat_id)
    if not state:
        return
    positions = state['positions']
    is_monster = (combatant.character.character_class or '').lower() == 'monster'
    col = GRID_COLS - 2 if is_monster else 1
    # Find first free row
    for y in range(1, GRID_ROWS - 1):
        if not _is_occupied(positions, col, y):
            positions[combatant.id] = {'x': col, 'y': y}
            break

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

# Combat System Models

class Combat(db.Model):
    """
    Database model for combat encounters.
    
    Manages the overall state of a combat encounter including turn order,
    current round, and active status.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    current_round = db.Column(db.Integer, default=1)
    current_turn = db.Column(db.Integer, default=0)  # Index in turn order
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Relationships
    combatants = db.relationship('Combatant', backref='combat', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Combat {self.name}>'
    
    @property
    def turn_order(self):
        """Get combatants ordered by initiative (highest first)."""
        return sorted(self.combatants, key=lambda c: c.initiative, reverse=True)
    
    @property 
    def current_combatant(self):
        """Get the combatant whose turn it currently is."""
        turn_order = self.turn_order
        if turn_order and 0 <= self.current_turn < len(turn_order):
            return turn_order[self.current_turn]
        return None
    
    def next_turn(self):
        """Advance to the next combatant's turn."""
        turn_order = self.turn_order
        if turn_order:
            self.current_turn = (self.current_turn + 1) % len(turn_order)
            if self.current_turn == 0:  # Back to first combatant
                self.current_round += 1
            db.session.commit()

class Combatant(db.Model):
    """
    Database model for combatants in a specific combat encounter.
    
    Links characters to combat encounters and tracks combat-specific state
    like initiative, conditions, and temporary HP.
    """
    id = db.Column(db.Integer, primary_key=True)
    combat_id = db.Column(db.Integer, db.ForeignKey('combat.id', ondelete='CASCADE'), nullable=False)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id', ondelete='CASCADE'), nullable=False)
    
    # Combat state
    initiative = db.Column(db.Integer, nullable=False)
    current_hp = db.Column(db.Integer, nullable=False)  # Can be different from character HP
    temp_hp = db.Column(db.Integer, default=0)
    conditions = db.Column(db.Text)  # JSON string for status conditions
    
    # Death saving throws
    death_save_successes = db.Column(db.Integer, default=0)
    death_save_failures = db.Column(db.Integer, default=0)
    
    # Actions this turn
    has_action = db.Column(db.Boolean, default=True)
    has_bonus_action = db.Column(db.Boolean, default=True)
    has_movement = db.Column(db.Boolean, default=True)
    has_reaction = db.Column(db.Boolean, default=True)
    
    # Relationships
    character = db.relationship(
        'Character',
        backref=db.backref('combatant_instances', cascade='all, delete-orphan'),
        lazy=True
    )
    
    def __repr__(self):
        return f'<Combatant {self.character.name}>'
    
    @property
    def effective_hp(self):
        """Get total effective HP including temporary HP."""
        return self.current_hp + self.temp_hp
    
    @property
    def is_conscious(self):
        """Check if combatant is conscious (HP > 0)."""
        return self.current_hp > 0
    
    @property
    def is_dead(self):
        """Check if combatant is dead (3 death save failures or massive damage)."""
        return self.death_save_failures >= 3 or self.current_hp <= -self.character.max_hp
    
    @property
    def conditions_list(self):
        """Get list of active conditions."""
        if self.conditions:
            import json
            try:
                return json.loads(self.conditions)
            except:
                return []
        return []
    
    def add_condition(self, condition):
        """Add a condition to the combatant."""
        conditions = self.conditions_list
        if condition not in conditions:
            conditions.append(condition)
            import json
            self.conditions = json.dumps(conditions)
            db.session.commit()
    
    def remove_condition(self, condition):
        """Remove a condition from the combatant."""
        conditions = self.conditions_list
        if condition in conditions:
            conditions.remove(condition)
            import json
            self.conditions = json.dumps(conditions) if conditions else None
            db.session.commit()
    
    def reset_turn_actions(self):
        """Reset actions for the start of a new turn."""
        self.has_action = True
        self.has_bonus_action = True
        self.has_movement = True
        # Reaction stays until start of next turn
        db.session.commit()
    
    def apply_damage(self, damage):
        """Apply damage to the combatant, handling temp HP."""
        if self.temp_hp > 0:
            if damage <= self.temp_hp:
                self.temp_hp -= damage
                damage = 0
            else:
                damage -= self.temp_hp
                self.temp_hp = 0
        
        self.current_hp -= damage
        
        # If dropped to 0 or below, start death saves if not already dead
        if self.current_hp <= 0 and not self.is_dead:
            self.current_hp = 0
            # Add unconscious condition
            self.add_condition('unconscious')
        
        db.session.commit()
    
    def heal(self, healing):
        """Apply healing to the combatant."""
        if self.current_hp > 0:  # Can only heal conscious creatures
            self.current_hp = min(self.current_hp + healing, self.character.max_hp)
        elif self.current_hp == 0 and healing > 0:  # Revive from unconscious
            self.current_hp = healing
            self.death_save_successes = 0
            self.death_save_failures = 0
            self.remove_condition('unconscious')
        
        db.session.commit()

class CombatAction(db.Model):
    """
    Database model for actions taken during combat.
    
    Records all actions for replay and analysis purposes.
    """
    id = db.Column(db.Integer, primary_key=True)
    combat_id = db.Column(db.Integer, db.ForeignKey('combat.id', ondelete='CASCADE'), nullable=False)
    actor_id = db.Column(db.Integer, db.ForeignKey('combatant.id', ondelete='CASCADE'), nullable=False)
    target_id = db.Column(db.Integer, db.ForeignKey('combatant.id', ondelete='SET NULL'), nullable=True)  # Can be null for non-targeted actions
    
    action_type = db.Column(db.String(50), nullable=False)  # attack, dodge, dash, etc.
    round_number = db.Column(db.Integer, nullable=False)
    
    # Action details (JSON)
    action_data = db.Column(db.Text)  # weapon used, damage dealt, etc.
    result = db.Column(db.Text)  # hit/miss, damage dealt, etc.
    
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Relationships
    actor = db.relationship(
        'Combatant',
        foreign_keys=[actor_id],
        backref=db.backref('actions_taken', passive_deletes=True)
    )
    target = db.relationship(
        'Combatant',
        foreign_keys=[target_id],
        backref=db.backref('actions_received', passive_deletes=True)
    )

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

def populate_standard_enemies():
    """Populate the database with standard D&D enemies."""
    for enemy_data in STANDARD_ENEMIES.values():
        # Check if enemy already exists
        existing = Enemy.query.filter_by(name=enemy_data.name).first()
        if existing:
            continue
            
        enemy = Enemy(
            name=enemy_data.name,
            creature_type=enemy_data.creature_type.value,
            size=enemy_data.size.value,
            armor_class=enemy_data.armor_class,
            hit_points=enemy_data.hit_points,
            speed=enemy_data.speed,
            strength=enemy_data.strength,
            dexterity=enemy_data.dexterity,
            constitution=enemy_data.constitution,
            intelligence=enemy_data.intelligence,
            wisdom=enemy_data.wisdom,
            charisma=enemy_data.charisma,
            challenge_rating=enemy_data.challenge_rating,
            experience_points=enemy_data.experience_points,
            passive_perception=enemy_data.passive_perception,
            darkvision=enemy_data.darkvision,
            saving_throws=json.dumps(enemy_data.saving_throws),
            skills=json.dumps(enemy_data.skills),
            damage_resistances=json.dumps(enemy_data.damage_resistances),
            damage_immunities=json.dumps(enemy_data.damage_immunities),
            condition_immunities=json.dumps(enemy_data.condition_immunities),
            languages=json.dumps(enemy_data.languages),
            actions=json.dumps([{
                'name': action.name,
                'description': action.description,
                'attack_bonus': action.attack_bonus,
                'damage_dice': action.damage_dice,
                'damage_type': action.damage_type,
                'range': action.range,
                'recharge': action.recharge
            } for action in enemy_data.actions]),
            special_abilities=json.dumps(enemy_data.special_abilities)
        )
        db.session.add(enemy)
    
    db.session.commit()

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/demo')
def demo():
    """Serve the demo.html file safely with proper encoding."""
    demo_path = os.path.join(app.root_path, 'demo.html')
    # Use send_file to avoid manual decoding issues (handles binary safely)
    return send_file(demo_path, mimetype='text/html; charset=utf-8')


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

# Combat API Routes

@app.route('/combat/start', methods=['POST'])
def start_combat():
    """Start a new combat encounter."""
    try:
        from combat import CombatEngine
        
        data = request.get_json()
        combat_name = data.get('name', 'Combat Encounter')
        character_ids = data.get('character_ids', [])
        
        if not character_ids:
            return jsonify({'error': 'No characters provided'}), 400
        
        # Create combat
        combat = Combat(name=combat_name)
        db.session.add(combat)
        db.session.flush()  # Get the ID
        
        # Add combatants and roll initiative
        for char_id in character_ids:
            character = Character.query.get(char_id)
            if character:
                initiative = CombatEngine.roll_initiative(character.dexterity_modifier)
                
                combatant = Combatant(
                    combat_id=combat.id,
                    character_id=char_id,
                    initiative=initiative,
                    current_hp=character.current_hp
                )
                db.session.add(combatant)
        
        db.session.commit()
        
        # Return combat state
        combatants = []
        for combatant in combat.combatants:
            combatants.append({
                'id': combatant.id,
                'character_name': combatant.character.name,
                'character_class': combatant.character.character_class,
                'initiative': combatant.initiative,
                'current_hp': combatant.current_hp,
                'max_hp': combatant.character.max_hp,
                'ac': combatant.character.armor_class,
                'conditions': combatant.conditions_list
            })
        
        # Ensure spatial positions initialized for this combat
        _init_spatial_positions(combat.id)

        return jsonify({
            'combat_id': combat.id,
            'name': combat.name,
            'round': combat.current_round,
            'combatants': combatants,
            'turn_order': [c['id'] for c in sorted(combatants, key=lambda x: x['initiative'], reverse=True)],
            'current_turn': combat.current_turn
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/combat/<int:combat_id>/status')
def combat_status(combat_id):
    """Get current combat status."""
    try:
        combat = Combat.query.get_or_404(combat_id)
        
        combatants = []
        for combatant in combat.combatants:
            combatants.append({
                'id': combatant.id,
                'character_name': combatant.character.name,
                'character_class': combatant.character.character_class,
                'initiative': combatant.initiative,
                'current_hp': combatant.current_hp,
                'max_hp': combatant.character.max_hp,
                'temp_hp': combatant.temp_hp,
                'ac': combatant.character.armor_class,
                'conditions': combatant.conditions_list,
                'is_conscious': combatant.is_conscious,
                'is_dead': combatant.is_dead,
                'has_action': combatant.has_action,
                'has_bonus_action': combatant.has_bonus_action,
                'has_movement': combatant.has_movement,
                'has_reaction': combatant.has_reaction,
                'death_saves': {
                    'successes': combatant.death_save_successes,
                    'failures': combatant.death_save_failures
                }
            })
        
        current_combatant = combat.current_combatant
        
        return jsonify({
            'combat_id': combat.id,
            'name': combat.name,
            'round': combat.current_round,
            'is_active': combat.is_active,
            'combatants': combatants,
            'current_combatant_id': current_combatant.id if current_combatant else None,
            'current_combatant_name': current_combatant.character.name if current_combatant else None
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/combat/<int:combat_id>/attack', methods=['POST'])
def make_attack(combat_id):
    """Make an attack action."""
    try:
        from combat import CombatEngine
        
        data = request.get_json()
        attacker_id = data.get('attacker_id')
        target_id = data.get('target_id') 
        weapon_id = data.get('weapon_id')
        
        if not attacker_id or not target_id:
            return jsonify({'error': 'Attacker and target required'}), 400
        
        attacker = Combatant.query.get(attacker_id)
        target = Combatant.query.get(target_id)
        
        if not attacker or not target:
            return jsonify({'error': 'Invalid combatant IDs'}), 400
        
        # Check if attacker has an action available
        if not attacker.has_action:
            return jsonify({'error': 'No action available. Actions can only be used once per turn.'}), 400
        
        # Get weapon
        weapon = None
        if weapon_id:
            weapon = Item.query.get(weapon_id)
            if not weapon or weapon.character_id != attacker.character_id:
                return jsonify({'error': 'Invalid weapon'}), 400
        
        # Calculate attack
        attack_bonus = CombatEngine.calculate_weapon_attack_bonus(attacker.character, weapon)
        target_ac = CombatEngine.calculate_ac(target.character)  # TODO: Include armor from equipped items
        
        hit, attack_roll, critical = CombatEngine.make_attack_roll(attack_bonus, target_ac)
        
        damage_dealt = 0
        damage_roll = 0
        damage_type = "bludgeoning"
        
        if hit:
            damage_info = CombatEngine.calculate_weapon_damage(attacker.character, weapon, critical)
            damage_roll = CombatEngine.roll_dice(damage_info.dice_count, damage_info.dice_size, damage_info.modifier)
            damage_type = damage_info.damage_type
            
            # Apply damage
            if damage_roll > 0:
                target.apply_damage(damage_roll)
                damage_dealt = damage_roll
        
        # Use action
        attacker.has_action = False
        db.session.commit()
        
        # Record the action
        action = CombatAction(
            combat_id=combat_id,
            actor_id=attacker_id,
            target_id=target_id,
            action_type='attack',
            round_number=Combat.query.get(combat_id).current_round,
            action_data=json.dumps({
                'weapon_id': weapon_id,
                'attack_roll': attack_roll,
                'critical': critical
            }),
            result=json.dumps({
                'hit': hit,
                'damage': damage_dealt,
                'damage_type': damage_type
            })
        )
        db.session.add(action)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'hit': hit,
            'attack_roll': attack_roll,
            'critical': critical,
            'damage': damage_dealt,
            'damage_type': damage_type
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/combat/<int:combat_id>/end_turn', methods=['POST'])
def end_turn(combat_id):
    """End the current combatant's turn."""
    try:
        combat = Combat.query.get(combat_id)
        if combat:
            current = combat.current_combatant
            if current:
                current.reset_turn_actions()
            
            combat.next_turn()
            
            # Reset reactions for the new turn
            new_current = combat.current_combatant
            if new_current:
                new_current.has_reaction = True
                db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/combat/<int:combat_id>/death_save', methods=['POST'])
def death_saving_throw(combat_id):
    """Make a death saving throw."""
    try:
        from combat import CombatEngine
        
        data = request.get_json()
        combatant_id = data.get('combatant_id')
        
        combatant = Combatant.query.get_or_404(combatant_id)
        
        if combatant.is_conscious:
            return jsonify({'error': 'Combatant is conscious'}), 400
        
        success, critical, roll = CombatEngine.make_death_saving_throw()
        
        if critical and success:
            # Natural 20 - regain 1 HP
            combatant.heal(1)
            message = f"Natural 20! {combatant.character.name} regains consciousness with 1 HP!"
        elif critical and not success:
            # Natural 1 - 2 failures
            combatant.death_save_failures += 2
            message = f"Natural 1! {combatant.character.name} gains 2 death save failures!"
        elif success:
            combatant.death_save_successes += 1
            message = f"{combatant.character.name} succeeds death save ({combatant.death_save_successes}/3)"
        else:
            combatant.death_save_failures += 1
            message = f"{combatant.character.name} fails death save ({combatant.death_save_failures}/3)"
        
        # Check if dead
        if combatant.death_save_failures >= 3:
            combatant.add_condition('dead')
            message += f" {combatant.character.name} has died!"
        elif combatant.death_save_successes >= 3:
            combatant.remove_condition('unconscious')
            combatant.death_save_successes = 0
            combatant.death_save_failures = 0
            message += f" {combatant.character.name} stabilizes but remains unconscious!"
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'roll': roll,
            'critical': critical,
            'death_save_success': success,
            'successes': combatant.death_save_successes,
            'failures': combatant.death_save_failures,
            'is_dead': combatant.is_dead,
            'message': message
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# D&D 5e classes that can cast healing spells
HEALING_CLASSES = {
    'cleric', 'bard', 'druid', 'paladin', 'ranger', 'sorcerer', 'warlock', 'wizard', 'artificer'
}

# Items that can be thrown and their damage/effects
THROWABLE_ITEMS = {
    'Acid (vial)': {'damage': '2d6', 'damage_type': 'acid', 'range': 20},
    'Alchemist\'s fire (flask)': {'damage': '1d4', 'damage_type': 'fire', 'range': 20, 'ongoing': '1d4 fire damage at start of turn'},
    'Holy water (flask)': {'damage': '2d6', 'damage_type': 'radiant', 'range': 20, 'condition': 'vs undead/fiends only'},
    'Oil (flask)': {'damage': '5', 'damage_type': 'fire', 'range': 20, 'condition': 'if target takes fire damage before end of next turn'},
    'Potion of healing': {'damage': '0', 'effect': 'heal 2d4+2 hp', 'range': 20},
    'Dagger': {'damage': '1d4', 'damage_type': 'piercing', 'range': 60},
    'Handaxe': {'damage': '1d6', 'damage_type': 'slashing', 'range': 60},
    'Javelin': {'damage': '1d6', 'damage_type': 'piercing', 'range': 120},
    'Light Hammer': {'damage': '1d4', 'damage_type': 'bludgeoning', 'range': 60},
    'Spear': {'damage': '1d6', 'damage_type': 'piercing', 'range': 60},
    'Dart': {'damage': '1d4', 'damage_type': 'piercing', 'range': 60},
    'Trident': {'damage': '1d6', 'damage_type': 'piercing', 'range': 60},
}

def can_heal(character_class):
    """Check if a character class can cast healing spells."""
    return character_class.lower() in HEALING_CLASSES

def can_throw_item(item_name):
    """Check if an item can be thrown."""
    return item_name in THROWABLE_ITEMS

def get_throw_damage(item_name):
    """Get throwing damage for an item."""
    return THROWABLE_ITEMS.get(item_name, {'damage': '1', 'damage_type': 'bludgeoning', 'range': 20})

@app.route('/combat/<int:combat_id>/heal', methods=['POST'])
def heal_combatant(combat_id):
    """Heal a combatant (restricted to spellcasting classes only)."""
    try:
        data = request.get_json()
        combatant_id = data.get('combatant_id')
        healing = data.get('healing', 0)
        healer_id = data.get('healer_id')  # Who is doing the healing
        
        if healing <= 0:
            return jsonify({'error': 'Healing amount must be positive'}), 400
        
        combatant = Combatant.query.get_or_404(combatant_id)
        healer = Combatant.query.get_or_404(healer_id) if healer_id else combatant
        
        # Check if the healer can actually cast healing spells
        if not can_heal(healer.character.character_class):
            return jsonify({
                'error': f'{healer.character.character_class.title()}s cannot cast healing spells. Only spellcasters like Clerics, Bards, Druids, Paladins, Rangers, Sorcerers, Warlocks, Wizards, and Artificers can heal.'
            }), 400
        
        # Check if healer has an action available (healing spells typically use an action)
        if not healer.has_action:
            return jsonify({'error': 'No action available. Healing spells require an action.'}), 400
        
        old_hp = combatant.current_hp
        combatant.heal(healing)
        
        # Use action for casting the healing spell
        healer.has_action = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'old_hp': old_hp,
            'new_hp': combatant.current_hp,
            'healing_applied': combatant.current_hp - old_hp,
            'is_conscious': combatant.is_conscious,
            'healer_name': healer.character.name
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/combat/<int:combat_id>/throw', methods=['POST'])
def throw_item(combat_id):
    """Throw an item at a target."""
    try:
        from combat import CombatEngine
        
        data = request.get_json()
        thrower_id = data.get('thrower_id')
        target_id = data.get('target_id')
        item_id = data.get('item_id')
        
        if not thrower_id or not target_id or not item_id:
            return jsonify({'error': 'Thrower, target, and item required'}), 400
        
        thrower = Combatant.query.get(thrower_id)
        target = Combatant.query.get(target_id)
        
        if not thrower or not target:
            return jsonify({'error': 'Invalid combatant IDs'}), 400
        
        # Check if thrower has an action available
        if not thrower.has_action:
            return jsonify({'error': 'No action available. Actions can only be used once per turn.'}), 400
        
        # For now, we'll simulate throwing with predefined item stats
        # In a full implementation, we'd look up the actual item in the database
        item_name = None
        item_mappings = {
            'acid_vial': 'Acid (vial)',
            'alchemist_fire': 'Alchemist\'s fire (flask)',
            'holy_water': 'Holy water (flask)',
            'dagger': 'Dagger',
            'javelin': 'Javelin',
            'healing_potion': 'Potion of healing'
        }
        
        item_name = item_mappings.get(item_id)
        if not item_name:
            return jsonify({'error': 'Invalid item selected'}), 400
        
        # Use the item name for throwing stats
        if not can_throw_item(item_name):
            return jsonify({'error': f'{item_name} cannot be thrown'}), 400
        
        # Get throwing stats
        throw_stats = get_throw_damage(item_name)
        
        # Calculate attack bonus (use DEX for thrown items)
        proficiency_bonus = CombatEngine.get_proficiency_bonus(thrower.character.level)
        attack_bonus = thrower.character.dexterity_modifier + proficiency_bonus
        
        # Make attack roll
        hit, attack_roll, critical = CombatEngine.make_attack_roll(attack_bonus, target.character.armor_class)
        
        damage_dealt = 0
        damage_roll = 0
        effect_message = ""
        
        if hit:
            # Parse and roll damage
            if throw_stats['damage'] and throw_stats['damage'] != '0':
                damage_info = CombatEngine.parse_damage_dice(throw_stats['damage'])
                damage_roll = CombatEngine.roll_dice(damage_info.dice_count, damage_info.dice_size, damage_info.modifier)
                
                if critical:
                    damage_roll = damage_roll * 2  # Simple critical damage
                
                # Apply damage if it's a damaging item
                if damage_roll > 0:
                    target.apply_damage(damage_roll)
                    damage_dealt = damage_roll
            
            # Handle special effects
            if 'effect' in throw_stats:
                if 'heal' in throw_stats['effect']:
                    # Healing potion thrown at target
                    healing_amount = 0
                    if '2d4+2' in throw_stats['effect']:
                        healing_amount = CombatEngine.roll_dice(2, 4, 2)
                    target.heal(healing_amount)
                    effect_message = f" and healed for {healing_amount} HP"
        
        # Consume/destroy the thrown item for consumables
        # For simulation purposes, we'll always consume consumable items
        consumable_items = ['Acid (vial)', 'Alchemist\'s fire (flask)', 'Holy water (flask)', 'Oil (flask)', 'Potion of healing']
        item_consumed = item_name in consumable_items
        
        # Use action
        thrower.has_action = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'hit': hit,
            'attack_roll': attack_roll,
            'damage': damage_dealt,
            'damage_type': throw_stats.get('damage_type', 'bludgeoning'),
            'critical': critical,
            'effect_message': effect_message,
            'item_consumed': item_consumed
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/enemies')
def list_enemies():
    """List all available enemies."""
    try:
        enemies = Enemy.query.all()
        
        # If no enemies in database, populate with standard ones
        if not enemies:
            populate_standard_enemies()
            enemies = Enemy.query.all()
        
        enemy_list = []
        for enemy in enemies:
            enemy_list.append({
                'id': enemy.id,
                'name': enemy.name,
                'creature_type': enemy.creature_type,
                'size': enemy.size,
                'armor_class': enemy.armor_class,
                'hit_points': enemy.hit_points,
                'challenge_rating': enemy.challenge_rating,
                'experience_points': enemy.experience_points
            })
        
        return jsonify({'enemies': enemy_list})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/combat/<int:combat_id>/bonus_action', methods=['POST'])
def use_bonus_action(combat_id):
    """Use a bonus action."""
    try:
        data = request.get_json()
        combatant_id = data.get('combatant_id')
        action_type = data.get('action_type')  # e.g., 'healing_word', 'cunning_action', etc.
        action_data = data.get('action_data', {})
        
        if not combatant_id or not action_type:
            return jsonify({'error': 'Combatant ID and action type required'}), 400
        
        combatant = Combatant.query.get_or_404(combatant_id)
        
        # Check if combatant has a bonus action available
        if not combatant.has_bonus_action:
            return jsonify({'error': 'No bonus action available. Bonus actions can only be used once per turn.'}), 400
        
        # Process specific bonus actions
        result = {}
        if action_type == 'healing_word':
            # Example bonus action healing spell (like Healing Word)
            if not can_heal(combatant.character.character_class):
                return jsonify({'error': 'Only spellcasters can cast Healing Word.'}), 400
            
            target_id = action_data.get('target_id')
            healing = action_data.get('healing', 4)  # Default healing for Healing Word
            
            if target_id:
                target = Combatant.query.get(target_id)
                if target:
                    old_hp = target.current_hp
                    target.heal(healing)
                    result = {
                        'target_name': target.character.name,
                        'healing_applied': target.current_hp - old_hp
                    }
        
        elif action_type == 'second_wind':
            # Fighter's Second Wind
            if combatant.character.character_class.lower() != 'fighter':
                return jsonify({'error': 'Only Fighters can use Second Wind.'}), 400
            
            healing = combatant.character.level + 10  # Second Wind healing formula
            old_hp = combatant.current_hp
            combatant.heal(healing)
            result = {
                'self_healing': combatant.current_hp - old_hp
            }
        
        else:
            # Generic bonus action
            result = {'action_performed': action_type}
        
        # Use bonus action
        combatant.has_bonus_action = False
        db.session.commit()
        
        # Record the action
        action = CombatAction(
            combat_id=combat_id,
            actor_id=combatant_id,
            action_type=f'bonus_action_{action_type}',
            round_number=Combat.query.get(combat_id).current_round,
            action_data=json.dumps(action_data),
            result=json.dumps(result)
        )
        db.session.add(action)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'action_type': action_type,
            **result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/combat/<int:combat_id>/reaction', methods=['POST'])
def use_reaction(combat_id):
    """Use a reaction."""
    try:
        data = request.get_json()
        combatant_id = data.get('combatant_id')
        reaction_type = data.get('reaction_type')  # e.g., 'opportunity_attack', 'counterspell', etc.
        trigger_data = data.get('trigger_data', {})
        
        if not combatant_id or not reaction_type:
            return jsonify({'error': 'Combatant ID and reaction type required'}), 400
        
        combatant = Combatant.query.get_or_404(combatant_id)
        
        # Check if combatant has a reaction available
        if not combatant.has_reaction:
            return jsonify({'error': 'No reaction available. Reactions can only be used once per round.'}), 400
        
        # Process specific reactions
        result = {}
        if reaction_type == 'opportunity_attack':
            # Make an opportunity attack
            target_id = trigger_data.get('target_id')
            if not target_id:
                return jsonify({'error': 'Target required for opportunity attack'}), 400
            
            target = Combatant.query.get(target_id)
            if not target:
                return jsonify({'error': 'Invalid target'}), 400
            
            # Make attack with the same logic as regular attack
            from combat import CombatEngine
            weapon = None  # Use natural weapon for simplicity
            attack_bonus = CombatEngine.calculate_weapon_attack_bonus(combatant.character, weapon)
            target_ac = CombatEngine.calculate_ac(target.character)
            
            hit, attack_roll, critical = CombatEngine.make_attack_roll(attack_bonus, target_ac)
            
            if hit:
                damage_info = CombatEngine.calculate_weapon_damage(combatant.character, weapon, critical)
                damage_roll = CombatEngine.roll_dice(damage_info.dice_count, damage_info.dice_size, damage_info.modifier)
                target.apply_damage(damage_roll)
                result = {
                    'hit': True,
                    'attack_roll': attack_roll,
                    'damage': damage_roll,
                    'critical': critical
                }
            else:
                result = {
                    'hit': False,
                    'attack_roll': attack_roll
                }
        
        else:
            # Generic reaction
            result = {'reaction_performed': reaction_type}
        
        # Use reaction
        combatant.has_reaction = False
        db.session.commit()
        
        # Record the action
        action = CombatAction(
            combat_id=combat_id,
            actor_id=combatant_id,
            action_type=f'reaction_{reaction_type}',
            round_number=Combat.query.get(combat_id).current_round,
            action_data=json.dumps(trigger_data),
            result=json.dumps(result)
        )
        db.session.add(action)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'reaction_type': reaction_type,
            **result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/combat/<int:combat_id>/add_enemy', methods=['POST'])
def add_enemy_to_combat(combat_id):
    """Add an enemy to an existing combat."""
    try:
        data = request.get_json()
        enemy_name = data.get('enemy_name')
        
        if not enemy_name:
            return jsonify({'error': 'Enemy name required'}), 400
        
        combat = Combat.query.get_or_404(combat_id)
        
        # Get enemy template
        enemy_template = Enemy.query.filter_by(name=enemy_name).first()
        if not enemy_template:
            return jsonify({'error': f'Enemy {enemy_name} not found'}), 404
        
        # Create a character-like entry for the enemy
        from combat import CombatEngine
        
        # Roll initiative for the enemy
        initiative = CombatEngine.roll_initiative(enemy_template.dexterity_modifier)
        
        # Create a temporary character for the enemy (we'd need a proper Enemy combatant type in a full implementation)
        # For now, we'll create a basic character entry
        enemy_character = Character(
            name=f"{enemy_template.name} #{len(combat.combatants) + 1}",
            gender="none",
            race=enemy_template.creature_type,
            character_class="monster",
            level=1,
            experience=0,
            max_hp=enemy_template.hit_points,
            current_hp=enemy_template.hit_points,
            armor_class=enemy_template.armor_class,
            strength=enemy_template.strength,
            dexterity=enemy_template.dexterity,
            constitution=enemy_template.constitution,
            intelligence=enemy_template.intelligence,
            wisdom=enemy_template.wisdom,
            charisma=enemy_template.charisma,
            gold=0
        )
        
        db.session.add(enemy_character)
        db.session.commit()
        
        # Add to combat
        combatant = Combatant(
            combat_id=combat.id,
            character_id=enemy_character.id,
            initiative=initiative,
            current_hp=enemy_template.hit_points
        )
        db.session.add(combatant)
        db.session.commit()

        # Place on grid
        _place_new_combatant(combat_id, combatant)

        return jsonify({
            'success': True,
            'combatant_id': combatant.id,
            'character_id': enemy_character.id,
            'name': enemy_character.name,
            'initiative': initiative,
            'hp': enemy_template.hit_points,
            'ac': enemy_template.armor_class
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/combats')
def list_combats():
    """List all combat encounters."""
    try:
        combats = Combat.query.all()
        
        combat_list = []
        for combat in combats:
            combat_list.append({
                'id': combat.id,
                'name': combat.name,
                'round': combat.current_round,
                'is_active': combat.is_active,
                'combatant_count': len(combat.combatants),
                'created_at': combat.created_at.isoformat() if combat.created_at else None
            })
        
        return jsonify({'combats': combat_list})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/combat')
def combat_page():
    """Render the combat management page."""
    return render_template('combat.html')

# --- Spatial API ---
@app.route('/api/spatial/<int:combat_id>/state')
def spatial_state(combat_id: int):
    combat = Combat.query.get_or_404(combat_id)
    state = _get_spatial_state(combat_id)
    if not state:
        return jsonify({'error': 'Spatial state unavailable'}), 500
    positions = state['positions']
    current = combat.current_combatant
    # Build minimal roster info
    roster = []
    for c in combat.combatants:
        pos = positions.get(c.id) or {'x': 0, 'y': 0}
        roster.append({
            'id': c.id,
            'name': c.character.name,
            'hp': c.current_hp,
            'max_hp': c.character.max_hp,
            'ac': c.character.armor_class,
            'is_conscious': c.is_conscious,
            'is_dead': c.is_dead,
            'x': pos['x'],
            'y': pos['y'],
        })
    return jsonify({
        'grid': {'cols': GRID_COLS, 'rows': GRID_ROWS},
        'positions': positions,
        'combat_id': combat.id,
        'name': combat.name,
        'round': combat.current_round,
        'current_combatant_id': current.id if current else None,
        'combatants': roster,
    })

@app.route('/api/spatial/<int:combat_id>/move', methods=['POST'])
def spatial_move(combat_id: int):
    try:
        data = request.get_json() or {}
        combatant_id = int(data.get('combatant_id'))
        x = int(data.get('x'))
        y = int(data.get('y'))

        combat = Combat.query.get_or_404(combat_id)
        c = Combatant.query.get_or_404(combatant_id)
        if combat.current_combatant is None or combat.current_combatant.id != combatant_id:
            return jsonify({'error': 'Not your turn'}), 400
        if not c.has_movement:
            return jsonify({'error': 'No movement left'}), 400

        state = _get_spatial_state(combat_id)
        if not state:
            return jsonify({'error': 'Spatial state not initialized'}), 500
        positions = state['positions']
        start = positions.get(combatant_id)
        if not start:
            return jsonify({'error': 'No start position'}), 400
        # Validate in bounds
        if x < 0 or y < 0 or x >= GRID_COLS or y >= GRID_ROWS:
            return jsonify({'error': 'Out of bounds'}), 400
        # Max move 6 tiles (roughly 30 ft)
        if _manhattan(start, {'x': x, 'y': y}) > 6:
            return jsonify({'error': 'Destination too far (max 6)'}), 400
        # Occupancy check
        if _is_occupied(positions, x, y, ignore_id=combatant_id):
            return jsonify({'error': 'Tile occupied'}), 400

        positions[combatant_id] = {'x': x, 'y': y}
        c.has_movement = False
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/spatial/<int:combat_id>/attack', methods=['POST'])
def spatial_attack(combat_id: int):
    try:
        from combat import CombatEngine
        data = request.get_json() or {}
        attacker_id = int(data.get('attacker_id'))
        target_id = int(data.get('target_id'))

        combat = Combat.query.get_or_404(combat_id)
        attacker = Combatant.query.get_or_404(attacker_id)
        target = Combatant.query.get_or_404(target_id)

        if combat.current_combatant is None or combat.current_combatant.id != attacker_id:
            return jsonify({'error': "Not attacker's turn"}), 400
        if not attacker.has_action:
            return jsonify({'error': 'No action available'}), 400

        state = _get_spatial_state(combat_id)
        if not state:
            return jsonify({'error': 'Spatial state not initialized'}), 500
        positions = state['positions']
        a_pos = positions.get(attacker_id)
        t_pos = positions.get(target_id)
        if not a_pos or not t_pos:
            return jsonify({'error': 'Positions unknown'}), 400
        # Require adjacency (radius 1 in manhattan distance)
        if _manhattan(a_pos, t_pos) > 1:
            return jsonify({'error': 'Target out of melee range'}), 400

        # Use existing attack logic (no weapon specified -> basic)
        attack_bonus = CombatEngine.calculate_weapon_attack_bonus(attacker.character, None)
        target_ac = CombatEngine.calculate_ac(target.character)
        hit, attack_roll, critical = CombatEngine.make_attack_roll(attack_bonus, target_ac)

        damage_dealt = 0
        damage_type = 'bludgeoning'
        if hit:
            dmg = CombatEngine.calculate_weapon_damage(attacker.character, None, critical)
            total = CombatEngine.roll_dice(dmg.dice_count, dmg.dice_size, dmg.modifier)
            if total > 0:
                target.apply_damage(total)
                damage_dealt = total
            damage_type = dmg.damage_type

        attacker.has_action = False
        db.session.commit()

        action = CombatAction(
            combat_id=combat_id,
            actor_id=attacker_id,
            target_id=target_id,
            action_type='attack',
            round_number=combat.current_round,
            action_data=json.dumps({'spatial': True, 'attack_roll': attack_roll, 'critical': critical}),
            result=json.dumps({'hit': hit, 'damage': damage_dealt, 'damage_type': damage_type})
        )
        db.session.add(action)
        db.session.commit()

        return jsonify({'success': True, 'hit': hit, 'attack_roll': attack_roll, 'critical': critical, 'damage': damage_dealt, 'damage_type': damage_type})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/characters')
def api_characters():
    """API endpoint to get character data as JSON."""
    try:
        characters = Character.query.all()
        
        character_list = []
        for char in characters:
            character_list.append({
                'id': char.id,
                'name': char.name,
                'character_class': char.character_class,
                'level': char.level,
                'current_hp': char.current_hp,
                'max_hp': char.max_hp,
                'armor_class': char.armor_class,
                'race': char.race,
                'gender': char.gender
            })
        
        return jsonify(character_list)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    # Ensure SQLite enforces foreign keys (needed for ON DELETE CASCADE)
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        except Exception:
            pass

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
