"""Database extensions and helpers."""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import event
from sqlalchemy.engine import Engine


db = SQLAlchemy()
migrate = Migrate()


def init_app(app):
    """Register database extensions with the Flask app."""
    db.init_app(app)
    migrate.init_app(app, db)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, _):
    """Ensure SQLite enforces foreign keys."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


__all__ = ["db", "migrate", "init_app"]
