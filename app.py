from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_character', methods=['POST'])
def create_character():
    character = {
        'name': request.form.get('name'),
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
