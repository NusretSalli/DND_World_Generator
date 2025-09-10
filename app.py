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
from items import CLASS_EQUIPMENT

app = Flask(__name__)
# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dnd_characters.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Item Model
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    item_type = db.Column(db.String(50), nullable=False)  # weapon, armor, gear, etc.
    description = db.Column(db.Text)
    weight = db.Column(db.Float)
    value = db.Column(db.Integer)  # in gold pieces
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'))

    def __repr__(self):
        return f'<Item {self.name}>'

# Character Model
class Character(db.Model):
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
    
    # Ability Scores
    strength = db.Column(db.Integer, nullable=False)
    dexterity = db.Column(db.Integer, nullable=False)
    constitution = db.Column(db.Integer, nullable=False)
    intelligence = db.Column(db.Integer, nullable=False)
    wisdom = db.Column(db.Integer, nullable=False)
    charisma = db.Column(db.Integer, nullable=False)
    
    # Currency
    copper = db.Column(db.Integer, default=0)
    silver = db.Column(db.Integer, default=0)
    gold = db.Column(db.Integer, default=0)
    platinum = db.Column(db.Integer, default=0)
    
    # Relationships
    inventory = db.relationship('Item', backref='owner', lazy=True)

    def __repr__(self):
        return f'<Character {self.name}>'
    
    def add_item(self, name, item_type, description="", weight=0, value=0):
        item = Item(
            name=name,
            item_type=item_type,
            description=description,
            weight=weight,
            value=value,
            character_id=self.id
        )
        db.session.add(item)
        db.session.commit()
    
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
    """Add basic starting equipment based on character class"""
    char_class = character.character_class.lower()
    
    if char_class in CLASS_EQUIPMENT:
        equipment = CLASS_EQUIPMENT[char_class]
        
        # Add all items from the class equipment list
        for item_list in equipment.values():
            for item in item_list:
                character.add_item(
                    name=item.name,
                    item_type=item.item_type,
                    description=item.description,
                    weight=item.weight,
                    value=item.value
                )

@app.route('/characters')
def view_characters():
    characters = Character.query.all()
    return render_template('characters.html', characters=characters)

@app.route('/delete_character/<int:character_id>', methods=['POST'])
def delete_character(character_id):
    character = Character.query.get_or_404(character_id)
    db.session.delete(character)
    db.session.commit()
    return redirect(url_for('view_characters'))

def upgrade_db():
    # Import necessary modules here to avoid circular imports
    from flask_migrate import Migrate, upgrade
    
    with app.app_context():
        migrate = Migrate(app, db)
        try:
            # Generate migration if there are changes
            from flask_migrate import migrate as migrate_command
            migrate_command()
        except Exception as e:
            print(f"Migration warning (this is normal if there are no changes): {e}")
        
        try:
            # Apply any pending migrations
            upgrade()
        except Exception as e:
            print(f"Upgrade error: {e}")

if __name__ == '__main__':
    upgrade_db()  # Run migrations automatically
    app.run(debug=True)
