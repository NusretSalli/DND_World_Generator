"""
Combat System Models
"""

from ..utils.database import db

class Combat(db.Model):
    """
    Database model for combat encounters.
    
    Manages the overall state of a combat encounter including turn order,
    current round, and active status.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    current_round = db.Column(db.Integer, default=1)
    current_turn = db.Column(db.Integer, default=0)  # Index in turn order
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Relationships
    combatants = db.relationship('CombatParticipant', backref='combat', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Combat {self.name}>'
    
    @property
    def turn_order(self):
        """Get combatants ordered by initiative (highest first)."""
        return sorted(self.combatants, key=lambda c: c.initiative, reverse=True)
    
    @property 
    def current_combatant(self):
        """Get the combatant whose turn it currently is."""
        turn_order = self.turn_order
        if turn_order and 0 <= self.current_turn < len(turn_order):
            return turn_order[self.current_turn]
        return None
    
    def next_turn(self):
        """Advance to the next combatant's turn."""
        turn_order = self.turn_order
        if turn_order:
            self.current_turn = (self.current_turn + 1) % len(turn_order)
            if self.current_turn == 0:  # Back to first combatant
                self.current_round += 1
            db.session.commit()

class CombatParticipant(db.Model):
    """
    Database model for combatants in a specific combat encounter.
    
    Links characters to combat encounters and tracks combat-specific state
    like initiative, conditions, and temporary HP.
    """
    __tablename__ = 'combatant'  # For backwards compatibility
    
    id = db.Column(db.Integer, primary_key=True)
    combat_id = db.Column(db.Integer, db.ForeignKey('combat.id', ondelete='CASCADE'), nullable=False)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id', ondelete='CASCADE'), nullable=False)
    
    # Combat state
    initiative = db.Column(db.Integer, nullable=False)
    current_hp = db.Column(db.Integer, nullable=False)  # Can be different from character HP
    temp_hp = db.Column(db.Integer, default=0)
    conditions = db.Column(db.Text)  # JSON string for status conditions
    
    # Death saving throws
    death_save_successes = db.Column(db.Integer, default=0)
    death_save_failures = db.Column(db.Integer, default=0)
    
    # Actions this turn
    has_action = db.Column(db.Boolean, default=True)
    has_bonus_action = db.Column(db.Boolean, default=True)
    has_movement = db.Column(db.Boolean, default=True)
    has_reaction = db.Column(db.Boolean, default=True)
    
    # Movement tracking
    movement_used = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<Combatant {self.character_id} in Combat {self.combat_id}>'
    
    def reset_turn_actions(self):
        """Reset actions at the start of turn."""
        self.has_action = True
        self.has_bonus_action = True
        self.has_movement = True
        self.movement_used = 0
        # Reaction is typically reset at start of each turn
        self.has_reaction = True
    
    def use_action(self):
        """Use the main action."""
        self.has_action = False
    
    def use_bonus_action(self):
        """Use the bonus action."""
        self.has_bonus_action = False
    
    def use_reaction(self):
        """Use the reaction."""
        self.has_reaction = False
    
    def use_movement(self, distance):
        """Use movement up to the specified distance."""
        self.movement_used += distance
    
    @property
    def is_conscious(self):
        """Check if combatant is conscious (HP > 0)."""
        return self.current_hp > 0
    
    @property
    def is_stable(self):
        """Check if combatant is stable (not dying)."""
        return self.current_hp > 0 or self.death_save_successes >= 3


# For backwards compatibility
Combatant = CombatParticipant