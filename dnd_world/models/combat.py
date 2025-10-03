"""SQLAlchemy models for combat encounters."""

from dnd_world.database import db


class Combat(db.Model):
    """
    Database model for combat encounters.
    
    Manages the overall state of a combat encounter including turn order,
    current round, and active status.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    current_round = db.Column(db.Integer, default=1)
    current_turn = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    combatants = db.relationship('Combatant', backref='combat', lazy=True, cascade='all, delete-orphan')
    
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
            if self.current_turn == 0:
                self.current_round += 1
            db.session.commit()

class Combatant(db.Model):
    """
    Database model for combatants in a specific combat encounter.
    
    Links characters to combat encounters and tracks combat-specific state
    like initiative, conditions, and temporary HP.
    """
    id = db.Column(db.Integer, primary_key=True)
    combat_id = db.Column(db.Integer, db.ForeignKey('combat.id', ondelete='CASCADE'), nullable=False)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id', ondelete='CASCADE'), nullable=False)
    
    initiative = db.Column(db.Integer, nullable=False)
    current_hp = db.Column(db.Integer, nullable=False)
    temp_hp = db.Column(db.Integer, default=0)
    conditions = db.Column(db.Text)
    
    death_save_successes = db.Column(db.Integer, default=0)
    death_save_failures = db.Column(db.Integer, default=0)
    
    has_action = db.Column(db.Boolean, default=True)
    has_bonus_action = db.Column(db.Boolean, default=True)
    has_movement = db.Column(db.Boolean, default=True)
    has_reaction = db.Column(db.Boolean, default=True)
    
    character = db.relationship(
        'Character',
        backref=db.backref('combatant_instances', cascade='all, delete-orphan'),
        lazy=True
    )
    
    def __repr__(self):
        return f'<Combatant {self.character.name}>'
    
    @property
    def effective_hp(self):
        """Get total effective HP including temporary HP."""
        return self.current_hp + self.temp_hp
    
    @property
    def is_conscious(self):
        """Check if combatant is conscious (HP > 0)."""
        return self.current_hp > 0
    
    @property
    def is_dead(self):
        """Check if combatant is dead (3 death save failures or massive damage)."""
        return self.death_save_failures >= 3 or self.current_hp <= -self.character.max_hp
    
    @property
    def conditions_list(self):
        """Get list of active conditions."""
        if self.conditions:
            import json
            try:
                return json.loads(self.conditions)
            except:
                return []
        return []
    
    def add_condition(self, condition):
        """Add a condition to the combatant."""
        conditions = self.conditions_list
        if condition not in conditions:
            conditions.append(condition)
            import json
            self.conditions = json.dumps(conditions)
            db.session.commit()
    
    def remove_condition(self, condition):
        """Remove a condition from the combatant."""
        conditions = self.conditions_list
        if condition in conditions:
            conditions.remove(condition)
            import json
            self.conditions = json.dumps(conditions) if conditions else None
            db.session.commit()
    
    def reset_turn_actions(self):
        """Reset actions for the start of a new turn."""
        self.has_action = True
        self.has_bonus_action = True
        self.has_movement = True
        db.session.commit()
    
    def apply_damage(self, damage):
        """Apply damage to the combatant, handling temp HP."""
        if self.temp_hp > 0:
            if damage <= self.temp_hp:
                self.temp_hp -= damage
                damage = 0
            else:
                damage -= self.temp_hp
                self.temp_hp = 0
        
        self.current_hp -= damage
        
        if self.current_hp <= 0 and not self.is_dead:
            self.current_hp = 0
            self.add_condition('unconscious')
        
        db.session.commit()
    
    def heal(self, healing):
        """Apply healing to the combatant."""
        if self.current_hp > 0:
            self.current_hp = min(self.current_hp + healing, self.character.max_hp)
        elif self.current_hp == 0 and healing > 0:
            self.current_hp = healing
            self.death_save_successes = 0
            self.death_save_failures = 0
            self.remove_condition('unconscious')
        
        db.session.commit()

class CombatAction(db.Model):
    """
    Database model for actions taken during combat.
    
    Records all actions for replay and analysis purposes.
    """
    id = db.Column(db.Integer, primary_key=True)
    combat_id = db.Column(db.Integer, db.ForeignKey('combat.id', ondelete='CASCADE'), nullable=False)
    actor_id = db.Column(db.Integer, db.ForeignKey('combatant.id', ondelete='CASCADE'), nullable=False)
    target_id = db.Column(db.Integer, db.ForeignKey('combatant.id', ondelete='SET NULL'), nullable=True)
    
    action_type = db.Column(db.String(50), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    action_data = db.Column(db.Text)
    result = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    actor = db.relationship(
        'Combatant',
        foreign_keys=[actor_id],
        backref=db.backref('actions_taken', passive_deletes=True)
    )
    target = db.relationship(
        'Combatant',
        foreign_keys=[target_id],
        backref=db.backref('actions_received', passive_deletes=True)
    )

class Enemy(db.Model):
    """
    Database model for enemy/monster templates.
    
    This model stores enemy statistics and abilities for use in combat encounters.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    creature_type = db.Column(db.String(50), nullable=False)
    size = db.Column(db.String(20), nullable=False)
    armor_class = db.Column(db.Integer, nullable=False)
    hit_points = db.Column(db.Integer, nullable=False)
    speed = db.Column(db.Integer, nullable=False, default=30)
    
    strength = db.Column(db.Integer, nullable=False)
    dexterity = db.Column(db.Integer, nullable=False)
    constitution = db.Column(db.Integer, nullable=False)
    intelligence = db.Column(db.Integer, nullable=False)
    wisdom = db.Column(db.Integer, nullable=False)
    charisma = db.Column(db.Integer, nullable=False)
    
    challenge_rating = db.Column(db.Float, nullable=False)
    experience_points = db.Column(db.Integer, nullable=False)
    
    passive_perception = db.Column(db.Integer, default=10)
    darkvision = db.Column(db.Integer, default=0)
    
    saving_throws = db.Column(db.Text)
    skills = db.Column(db.Text)
    damage_resistances = db.Column(db.Text)
    damage_immunities = db.Column(db.Text)
    condition_immunities = db.Column(db.Text)
    languages = db.Column(db.Text)
    actions = db.Column(db.Text)
    special_abilities = db.Column(db.Text)
    
    @property
    def strength_modifier(self):
        return (self.strength - 10) // 2
    
    @property
    def dexterity_modifier(self):
        return (self.dexterity - 10) // 2
    
    @property
    def constitution_modifier(self):
        return (self.constitution - 10) // 2
    
    @property
    def intelligence_modifier(self):
        return (self.intelligence - 10) // 2
    
    @property
    def wisdom_modifier(self):
        return (self.wisdom - 10) // 2
    
    @property
    def charisma_modifier(self):
        return (self.charisma - 10) // 2
    
    def get_actions_list(self):
        """Parse actions JSON string into list."""
        if self.actions:
            try:
                return json.loads(self.actions)
            except:
                return []
        return []
    
    def get_special_abilities_list(self):
        """Parse special abilities JSON string into list."""
        if self.special_abilities:
            try:
                return json.loads(self.special_abilities)
            except:
                return []
        return []

