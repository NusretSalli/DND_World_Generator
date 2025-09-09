from flask import Flask, render_template, request, jsonify
from pynames import GENDER, LANGUAGE
from pynames.generators.elven import WarhammerNamesGenerator, DnDNamesGenerator
from pynames.generators.goblin import GoblinGenerator
from pynames.generators.korean import KoreanNamesGenerator
from pynames.generators.mongolian import MongolianNamesGenerator
from pynames.generators.orc import OrcNamesGenerator
from pynames.generators.russian import PaganNamesGenerator
from pynames.generators.scandinavian import ScandinavianNamesGenerator

app = Flask(__name__)

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

@app.route('/create_character', methods=['POST'])
def create_character():
    character = {
        'name': request.form.get('name'),
        'gender': request.form.get('gender'),
        'race': request.form.get('race'),
        'class': request.form.get('class'),
        'strength': request.form.get('strength'),
        'dexterity': request.form.get('dexterity'),
        'constitution': request.form.get('constitution'),
        'intelligence': request.form.get('intelligence'),
        'wisdom': request.form.get('wisdom'),
        'charisma': request.form.get('charisma'),
    }
    # For now, we'll just print the character to the console
    # In the future, you would save this to a database
    print(character)
    return "Character created! Check the console."

if __name__ == '__main__':
    app.run(debug=True)
