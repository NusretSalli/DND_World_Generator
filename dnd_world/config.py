"""
Configuration Management
"""

import os

class Config:
    """Base configuration class."""
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///dnd_characters.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Story Generation
    STORY_MODEL_NAME = os.environ.get('STORY_MODEL_NAME') or 'distilgpt2'
    ENABLE_AI_STORY_GENERATION = os.environ.get('ENABLE_AI_STORY_GENERATION', 'True').lower() == 'true'
    
    # API
    API_HOST = os.environ.get('API_HOST') or '127.0.0.1'
    API_PORT = int(os.environ.get('API_PORT') or 5000)
    
    # Streamlit Frontend
    STREAMLIT_HOST = os.environ.get('STREAMLIT_HOST') or '127.0.0.1'
    STREAMLIT_PORT = int(os.environ.get('STREAMLIT_PORT') or 8501)

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///dnd_characters_dev.db'

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    # SECRET_KEY validation will be done at runtime when this config is selected

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}