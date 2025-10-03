"""Backend application factory."""
from __future__ import annotations

from flask import Flask
import secrets

from dnd_world.database import db, init_app as init_database
from .routes import bp, ensure_default_character, populate_standard_enemies


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dnd_characters.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_SORT_KEYS'] = False
    app.config['SECRET_KEY'] = secrets.token_hex(32)

    if config:
        app.config.update(config)

    init_database(app)
    app.register_blueprint(bp)

    with app.app_context():
        db.create_all()
        populate_standard_enemies()
        ensure_default_character()

    return app


__all__ = ["create_app"]
