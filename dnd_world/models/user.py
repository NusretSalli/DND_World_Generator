"""SQLAlchemy model for user accounts."""

from dnd_world.database import db
import hashlib
import secrets

class User(db.Model):
    """
    Database model for user accounts.
    
    Simple authentication system for campaign management.
    Each user can have multiple characters in their campaign.
    """
    # Basic information
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    salt = db.Column(db.String(32), nullable=False)
    
    # Relationship to characters - each user owns their characters
    characters = db.relationship(
        'Character',
        backref=db.backref('user'),
        lazy=True,
        cascade='all, delete-orphan'
    )
    
    def __repr__(self):
        """String representation of the user."""
        return f'<User {self.username}>'
    
    def set_password(self, password):
        """Set password with proper hashing and salt."""
        self.salt = secrets.token_hex(32)
        password_with_salt = password + self.salt
        self.password_hash = hashlib.sha256(password_with_salt.encode()).hexdigest()
    
    def check_password(self, password):
        """Check if provided password matches stored hash."""
        password_with_salt = password + self.salt
        return self.password_hash == hashlib.sha256(password_with_salt.encode()).hexdigest()
    
    @classmethod
    def authenticate(cls, username, password):
        """Authenticate user by username and password."""
        user = cls.query.filter_by(username=username).first()
        if user and user.check_password(password):
            return user
        return None
    
    @classmethod
    def create_user(cls, username, password):
        """Create a new user account."""
        # Check if username already exists
        if cls.query.filter_by(username=username).first():
            return None, "Username already exists"
        
        # Create new user
        user = cls(username=username)
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            return user, "User created successfully"
        except Exception as e:
            db.session.rollback()
            return None, f"Error creating user: {str(e)}"