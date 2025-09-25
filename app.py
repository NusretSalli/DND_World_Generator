"""WSGI entry point for the D&D World Generator backend."""

from dnd_world.backend import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
