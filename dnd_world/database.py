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


def cleanup_old_combat_sessions(days_old=7):
    """Clean up combat sessions older than specified days.
    
    Args:
        days_old (int): Number of days to keep combat sessions
        
    Returns:
        int: Number of sessions deleted
    """
    from datetime import datetime, timedelta
    from dnd_world.models import Combat
    
    cutoff_date = datetime.utcnow() - timedelta(days=days_old)
    
    # Find old combat sessions
    old_combats = Combat.query.filter(
        Combat.created_at < cutoff_date,
        Combat.is_active == False
    ).all()
    
    count = len(old_combats)
    
    for combat in old_combats:
        db.session.delete(combat)
    
    db.session.commit()
    return count


def cleanup_orphaned_items():
    """Clean up items that are not associated with any character.
    
    Returns:
        int: Number of items deleted
    """
    from dnd_world.models import Item
    
    # Find items with no character_id
    orphaned_items = Item.query.filter(Item.character_id.is_(None)).all()
    
    count = len(orphaned_items)
    
    for item in orphaned_items:
        db.session.delete(item)
    
    db.session.commit()
    return count


def get_database_stats():
    """Get statistics about database usage.
    
    Returns:
        dict: Database statistics
    """
    from dnd_world.models import Character, Combat, Item, User
    
    stats = {
        'characters': Character.query.count(),
        'active_combats': Combat.query.filter_by(is_active=True).count(),
        'total_combats': Combat.query.count(),
        'items': Item.query.count(),
        'users': User.query.count()
    }
    
    return stats


__all__ = ["db", "migrate", "init_app", "cleanup_old_combat_sessions", 
           "cleanup_orphaned_items", "get_database_stats"]
