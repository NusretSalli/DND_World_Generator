"""
Database configuration and management utilities
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Global database instance
db = SQLAlchemy()
migrate = Migrate()

class DatabaseManager:
    """Manages database operations and initialization"""
    
    @staticmethod
    def init_app(app: Flask):
        """Initialize database with Flask app"""
        # Configuration is handled by Flask config
        db.init_app(app)
        migrate.init_app(app, db)
        
        return db
    
    @staticmethod
    def create_tables(app: Flask):
        """Create all database tables"""
        with app.app_context():
            try:
                db.create_all()
                print("Database tables created/updated successfully")
            except Exception as e:
                print(f"Database setup: {e}")