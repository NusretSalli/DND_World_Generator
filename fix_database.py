#!/usr/bin/env python3
"""
Database migration script to add user_id column to character table
and create user table if they don't exist.
"""

import sqlite3
import os
from pathlib import Path

# Database paths to check
db_paths = [
    "instance/dnd_characters.db",
    "dnd_world/instance/dnd_characters.db",
    "dnd_characters.db"
]

def find_database():
    """Find the database file."""
    for path in db_paths:
        if os.path.exists(path):
            print(f"Found database at: {path}")
            return path
    print("No database found, will create new one")
    return "instance/dnd_characters.db"

def migrate_database(db_path):
    """Add missing columns and tables to the database."""
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if user table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user';")
        user_table_exists = cursor.fetchone() is not None
        
        if not user_table_exists:
            print("Creating user table...")
            cursor.execute("""
                CREATE TABLE user (
                    id INTEGER NOT NULL PRIMARY KEY,
                    username VARCHAR(80) NOT NULL UNIQUE,
                    password_hash VARCHAR(128) NOT NULL,
                    salt VARCHAR(32) NOT NULL
                )
            """)
            print("User table created successfully")
        else:
            print("User table already exists")
        
        # Check if user_id column exists in character table
        cursor.execute("PRAGMA table_info(character);")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'user_id' not in columns:
            print("Adding user_id column to character table...")
            cursor.execute("ALTER TABLE character ADD COLUMN user_id INTEGER;")
            print("user_id column added successfully")
        else:
            print("user_id column already exists")
        
        # Check if character table exists at all
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='character';")
        character_table_exists = cursor.fetchone() is not None
        
        if not character_table_exists:
            print("Character table doesn't exist - will be created by Flask app")
        
        conn.commit()
        print("Database migration completed successfully!")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
    except Exception as e:
        print(f"Unexpected error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    db_path = find_database()
    migrate_database(db_path)