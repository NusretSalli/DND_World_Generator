"""
D&D World Generator - Streamlit Frontend
Enhanced UI for the Flask-based D&D character and campaign management system
"""

import streamlit as st
import requests
import plotly.graph_objects as go
import plotly.express as px
import json
import time
from typing import List, Dict, Optional

# Import configuration
try:
    from streamlit_config import *
except ImportError:
    # Optimized timeout values for better performance
    API_TIMEOUT_SHORT = 1.5  # Reduced from 2
    API_TIMEOUT_MEDIUM = 2.5  # Reduced from 3
    API_TIMEOUT_LONG = 6      # Reduced from 8
    ENABLE_CACHING = True

# Configure the app
st.set_page_config(
    page_title="🐉 D&D World Generator",
    page_icon="🐉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for D&D theme
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #2d1810, #4a2c17);
        padding: 20px;
        border-radius: 10px;
        color: #e6edf3;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    .character-card {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        padding: 20px;
        border-radius: 12px;
        border: 2px solid #3d4f73;
        margin: 10px 0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
    }
    
    .spell-slot-filled {
        background-color: #4dabf7;
        border-radius: 50%;
        width: 20px;
        height: 20px;
        display: inline-block;
        margin: 2px;
    }
    
    .spell-slot-empty {
        background-color: #495057;
        border-radius: 50%;
        width: 20px;
        height: 20px;
        display: inline-block;
        margin: 2px;
    }
    
    .combat-grid {
        background: #0f1419;
        border: 2px solid #2d3742;
        border-radius: 8px;
        padding: 10px;
    }
    
    .stMetric {
        background: linear-gradient(135deg, #17202a, #1e2a3a);
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #2d3742;
    }
    
    .dice-result {
        font-size: 2em;
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #4a2c17, #2d1810);
        border-radius: 10px;
        color: #e6edf3;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Flask backend configuration
FLASK_URL = "http://localhost:5000"

# Caching and performance optimization
@st.cache_data(ttl=30, show_spinner=False)  # Cache for 30 seconds
def check_flask_connection():
    """Check if Flask backend is running - cached"""
    try:
        response = requests.get(f"{FLASK_URL}/", timeout=2)
        return response.status_code == 200
    except:
        return False

@st.cache_data(ttl=30, show_spinner=False)  # Increased cache time to 30 seconds
def get_characters():
    """Fetch characters from Flask backend - cached"""
    try:
        response = requests.get(f"{FLASK_URL}/api/characters", timeout=3)
        return response.json() if response.status_code == 200 else []
    except:
        return []

def get_characters_optimized():
    """Optimized character loading with session state caching"""
    current_time = time.time()
    # Use cached data if it's less than 15 seconds old
    if (st.session_state.cached_characters is not None and 
        current_time - st.session_state.cache_timestamp < 15):
        return st.session_state.cached_characters
    
    # Fetch new data
    characters = get_characters()
    st.session_state.cached_characters = characters
    st.session_state.cache_timestamp = current_time
    return characters

# Manual cache invalidation function
def invalidate_character_cache():
    """Force refresh character data"""
    get_characters.clear()
    st.session_state.cached_characters = None
    st.session_state.cache_timestamp = 0
    if 'characters_last_update' in st.session_state:
        del st.session_state.characters_last_update

def invalidate_all_caches():
    """Clear all caches for fresh data"""
    get_characters.clear()
    get_character_spells.clear()
    get_combat_status.clear()
    st.session_state.cached_characters = None
    st.session_state.cache_timestamp = 0

def create_character(char_data):
    """Create character via Flask backend"""
    try:
        response = requests.post(f"{FLASK_URL}/create_character", data=char_data, timeout=8)
        success = response.status_code in [200, 302]  # 302 for redirect after creation
        if success:
            invalidate_character_cache()  # Clear cache when character is created
        return success
    except:
        return False

def delete_character(character_id: int) -> bool:
    """Delete a character"""
    try:
        response = requests.post(f"{FLASK_URL}/delete_character/{character_id}", timeout=API_TIMEOUT_SHORT)
        if response.status_code in [200, 302]:
            invalidate_character_cache()
            return True
        return False
    except Exception as e:
        print(f"Error deleting character: {e}")
        return False

@st.cache_data(ttl=60, show_spinner=False)  # Cache dice results for 1 minute
def roll_dice(notation):
    """Roll dice using Flask backend - cached for repeated identical rolls"""
    try:
        response = requests.get(f"{FLASK_URL}/roll_dice", params={"dice": notation}, timeout=3)
        return response.json() if response.status_code == 200 else None
    except:
        return None

@st.cache_data(ttl=300, show_spinner=False)  # Cache for 5 minutes
def generate_ability_scores(method="4d6", race="human"):
    """Generate ability scores using Flask backend - cached"""
    try:
        response = requests.get(f"{FLASK_URL}/generate_ability_scores", 
                              params={"method": method, "race": race}, timeout=3)
        return response.json() if response.status_code == 200 else None
    except:
        return None

# Inventory management functions
@st.cache_data(ttl=10, show_spinner=False)
def get_character_inventory(character_id: int):
    """Get character inventory data"""
    try:
        response = requests.get(f"{FLASK_URL}/character/{character_id}/inventory", timeout=API_TIMEOUT_SHORT)
        if response.status_code == 200:
            # Parse the HTML response to extract inventory data
            # For now, return a simple structure
            return {"equipped_items": [], "carried_items": [], "equipment_slots": {}}
        return None
    except:
        return None

def equip_item(character_id: int, item_id: int, slot: str) -> bool:
    """Equip an item to a character slot"""
    try:
        response = requests.post(
            f"{FLASK_URL}/character/{character_id}/equip/{item_id}",
            data={"slot": slot},
            timeout=API_TIMEOUT_SHORT
        )
        return response.status_code in [200, 302]
    except:
        return False

def unequip_item(character_id: int, slot: str) -> bool:
    """Unequip an item from a character slot"""
    try:
        response = requests.post(
            f"{FLASK_URL}/character/{character_id}/unequip",
            data={"slot": slot},
            timeout=API_TIMEOUT_SHORT
        )
        return response.status_code in [200, 302]
    except:
        return False

def add_item_to_character(character_id: int, item_name: str) -> bool:
    """Add an item to character inventory"""
    try:
        response = requests.post(
            f"{FLASK_URL}/character/{character_id}/add_item",
            data={"item_name": item_name},
            timeout=API_TIMEOUT_SHORT
        )
        return response.status_code in [200, 302]
    except:
        return False

def show_character_inventory(character):
    """Display character inventory management interface"""
    st.markdown("---")
    st.subheader("🎒 Inventory & Equipment")
    
    # Close inventory button
    if st.button("❌ Close Inventory", key="close_inventory"):
        st.session_state.show_inventory = False
        st.rerun()
    
    # Get inventory data (simplified for now since we'd need to parse HTML)
    st.info("📝 **Note:** This is a simplified inventory view. Full equipment management with visual slots coming soon!")
    
    # Mock equipment slots for demonstration
    st.markdown("### 🛡️ Equipment Slots")
    
    equipment_slots = [
        "Main Hand", "Off Hand", "Armor", "Shield", "Helmet", 
        "Gloves", "Boots", "Cloak", "Ring 1", "Ring 2", "Amulet", "Belt"
    ]
    
    cols = st.columns(3)
    for i, slot in enumerate(equipment_slots):
        with cols[i % 3]:
            with st.container():
                st.markdown(f"**{slot}**")
                st.text("Empty Slot")  # Placeholder
                if st.button(f"Manage {slot}", key=f"manage_{slot}_{character['id']}"):
                    st.info(f"Managing {slot} - Full functionality coming soon!")
    
    st.markdown("### 🎒 Carried Items")
    st.info("Carried items will be displayed here with equip/unequip options.")
    
    st.markdown("### ➕ Add New Item")
    with st.form(f"add_item_{character['id']}"):
        item_name = st.text_input("Item Name", placeholder="Enter item name")
        if st.form_submit_button("Add Item"):
            if item_name:
                if add_item_to_character(character['id'], item_name):
                    st.success(f"Added {item_name} to inventory!")
                    st.rerun()
                else:
                    st.error("Failed to add item!")
            else:
                st.error("Please enter an item name!")

def show_combat_actions(combat):
    """Display comprehensive combat action interface"""
    st.subheader("⚔️ Combat Actions")
    
    combat_id = st.session_state.combat_id
    combatants = combat.get('combatants', [])
    current_combatant = combat.get('current_combatant_name', 'Unknown')
    
    # Action tabs
    action_tab1, action_tab2, action_tab3 = st.tabs(["🗡️ Basic Actions", "🎯 Advanced Actions", "👥 Manage"])
    
    with action_tab1:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("⚔️ Attack", key="combat_attack"):
                # Attack interface
                show_attack_interface(combat_id, combatants)
        
        with col2:
            if st.button("❤️ Heal", key="combat_heal"):
                show_heal_interface(combat_id, combatants)
        
        with col3:
            if st.button("🏃 End Turn", key="combat_end_turn"):
                try:
                    response = requests.post(f"{FLASK_URL}/combat/{combat_id}/end_turn", timeout=5)
                    if response.status_code == 200:
                        st.success("Turn ended!")
                        st.rerun()
                    else:
                        st.error("Failed to end turn")
                except:
                    st.error("Error ending turn")
        
        with col4:
            if st.button("🏁 End Combat", key="combat_end"):
                del st.session_state.combat_id
                st.success("Combat ended!")
                st.rerun()
    
    with action_tab2:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("💀 Death Save", key="combat_death_save"):
                show_death_save_interface(combat_id, combatants)
        
        with col2:
            if st.button("🎯 Throw", key="combat_throw"):
                show_throw_interface(combat_id, combatants)
                
        with col3:
            if st.button("⚡ Bonus Action", key="combat_bonus"):
                show_bonus_action_interface(combat_id, combatants)
        
        with col4:
            if st.button("🛡️ Reaction", key="combat_reaction"):
                show_reaction_interface(combat_id, combatants)
    
    with action_tab3:
        if st.button("➕ Add Enemy", key="add_enemy"):
            show_add_enemy_interface(combat_id)

def show_attack_interface(combat_id, combatants):
    """Show attack interface"""
    st.subheader("⚔️ Attack")
    
    # Select attacker and target
    attacker_names = [f"{c.get('character_name', 'Unknown')} (HP: {c.get('current_hp', 0)})" for c in combatants if c.get('current_hp', 0) > 0]
    target_names = [f"{c.get('character_name', 'Unknown')} (HP: {c.get('current_hp', 0)})" for c in combatants]
    
    with st.form("attack_form"):
        attacker = st.selectbox("Attacker", attacker_names)
        target = st.selectbox("Target", target_names)
        
        if st.form_submit_button("🗡️ Execute Attack"):
            # Get character IDs (simplified - would need proper mapping)
            st.info("Attack executed! (Full implementation connects to Flask combat system)")

def show_heal_interface(combat_id, combatants):
    """Show heal interface"""
    st.subheader("❤️ Heal")
    
    with st.form("heal_form"):
        target_names = [f"{c.get('character_name', 'Unknown')} (HP: {c.get('current_hp', 0)})" for c in combatants]
        target = st.selectbox("Target", target_names)
        heal_amount = st.number_input("Heal Amount", min_value=1, max_value=100, value=10)
        
        if st.form_submit_button("💚 Heal"):
            try:
                # This would need proper character ID mapping
                st.success(f"Healed {heal_amount} HP!")
                st.rerun()
            except:
                st.error("Failed to heal!")

def show_death_save_interface(combat_id, combatants):
    """Show death save interface"""
    st.subheader("💀 Death Save")
    
    unconscious_chars = [c for c in combatants if c.get('current_hp', 0) <= 0]
    
    if not unconscious_chars:
        st.info("No unconscious characters need death saves.")
        return
    
    with st.form("death_save_form"):
        char_names = [f"{c.get('character_name', 'Unknown')}" for c in unconscious_chars]
        character = st.selectbox("Character", char_names)
        
        if st.form_submit_button("🎲 Roll Death Save"):
            st.info("Death save rolled! (Full implementation connects to Flask)")

def show_throw_interface(combat_id, combatants):
    """Show throw interface"""
    st.subheader("🎯 Throw Item")
    
    with st.form("throw_form"):
        thrower_names = [f"{c.get('character_name', 'Unknown')}" for c in combatants if c.get('current_hp', 0) > 0]
        target_names = [f"{c.get('character_name', 'Unknown')}" for c in combatants]
        
        thrower = st.selectbox("Thrower", thrower_names)
        target = st.selectbox("Target", target_names)
        item = st.text_input("Item to Throw", placeholder="e.g., Dagger, Rock")
        
        if st.form_submit_button("🎯 Throw"):
            st.info(f"Threw {item}! (Full implementation connects to Flask)")

def show_bonus_action_interface(combat_id, combatants):
    """Show bonus action interface"""
    st.subheader("⚡ Bonus Action")
    
    with st.form("bonus_action_form"):
        char_names = [f"{c.get('character_name', 'Unknown')}" for c in combatants if c.get('current_hp', 0) > 0]
        character = st.selectbox("Character", char_names)
        action = st.text_input("Bonus Action", placeholder="Describe the bonus action")
        
        if st.form_submit_button("⚡ Execute"):
            st.info(f"Bonus action: {action}! (Full implementation connects to Flask)")

def show_reaction_interface(combat_id, combatants):
    """Show reaction interface"""
    st.subheader("🛡️ Reaction")
    
    with st.form("reaction_form"):
        char_names = [f"{c.get('character_name', 'Unknown')}" for c in combatants if c.get('current_hp', 0) > 0]
        character = st.selectbox("Character", char_names)
        reaction = st.text_input("Reaction", placeholder="Describe the reaction")
        
        if st.form_submit_button("🛡️ React"):
            st.info(f"Reaction: {reaction}! (Full implementation connects to Flask)")

def show_add_enemy_interface(combat_id):
    """Show add enemy interface"""
    st.subheader("👹 Add Enemy")
    
    with st.form("add_enemy_form"):
        enemy_name = st.text_input("Enemy Name", placeholder="e.g., Goblin")
        enemy_hp = st.number_input("HP", min_value=1, max_value=500, value=10)
        enemy_ac = st.number_input("AC", min_value=1, max_value=30, value=12)
        
        if st.form_submit_button("➕ Add Enemy"):
            try:
                response = requests.post(
                    f"{FLASK_URL}/combat/{combat_id}/add_enemy",
                    json={"name": enemy_name, "hp": enemy_hp, "ac": enemy_ac},
                    timeout=5
                )
                if response.status_code == 200:
                    st.success(f"Added {enemy_name} to combat!")
                    st.rerun()
                else:
                    st.error("Failed to add enemy!")
            except:
                st.error("Error adding enemy!")

@st.cache_data(ttl=60, show_spinner=False)  # Cache for 1 minute
def get_character_spells(character_id):
    """Get character spell information from Flask API"""
    try:
        response = requests.get(f"{FLASK_URL}/character/{character_id}/spells", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def cast_spell(character_id, spell_name, spell_level):
    """Cast a spell and consume spell slot"""
    try:
        response = requests.post(
            f"{FLASK_URL}/character/{character_id}/cast_spell",
            json={"spell_name": spell_name, "spell_level": spell_level},
            timeout=5
        )
        return response.status_code == 200, response.json() if response.status_code == 200 else {}
    except:
        return False, {}

def long_rest_character(character_id):
    """Perform long rest to restore HP and spell slots"""
    try:
        response = requests.post(f"{FLASK_URL}/character/{character_id}/long_rest", timeout=5)
        return response.status_code == 200, response.json() if response.status_code == 200 else {}
    except:
        return False, {}

@st.cache_data(ttl=5, show_spinner=False)  # Cache combat status for 5 seconds
def get_combat_status(combat_id):
    """Get combat status with caching"""
    try:
        response = requests.get(f"{FLASK_URL}/combat/{combat_id}/status", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def show_character_spells(character):
    """Display character spell management interface"""
    st.markdown("---")
    st.subheader("🔮 Spells & Magic")
    
    # Close spells button
    if st.button("❌ Close Spells", key="close_spells"):
        st.session_state.show_spells = False
        st.rerun()
    
    # Lazy load spell data with loading indicator
    with st.spinner("Loading spell data..."):
        spell_data = get_character_spells(character['id'])
    
    if not spell_data:
        st.error("Failed to load spell data")
        return
    
    # Check if character is a spellcaster
    if not spell_data.get('is_spellcaster', False):
        st.info(f"**{character['name']}** is not a spellcasting class and cannot cast spells.")
        return
    
    # Spell statistics
    st.markdown("### 📊 Spell Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Cantrips Known", spell_data.get('cantrips_known', 0))
    with col2:
        st.metric("Spells Known", spell_data.get('spells_known', 0))
    with col3:
        st.metric("Currently Known", len(spell_data.get('known_spells', [])))
    with col4:
        st.metric("Prepared", len(spell_data.get('prepared_spells', [])))
    
    # Spell slots visualization
    st.markdown("### 🎯 Spell Slots")
    
    current_slots = spell_data.get('current_slots', {})
    max_slots = spell_data.get('max_slots', {})
    
    if max_slots:
        for level in range(1, 10):
            if max_slots.get(str(level), 0) > 0:
                current = current_slots.get(str(level), 0)
                maximum = max_slots.get(str(level), 0)
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    # Visual representation of spell slots
                    filled_slots = "●" * current
                    empty_slots = "○" * (maximum - current)
                    st.markdown(f"**Level {level}:** {filled_slots}{empty_slots}")
                with col2:
                    st.text(f"({current}/{maximum})")
    else:
        st.info("No spell slots available")
    
    # Long rest button
    if st.button("🛌 Take Long Rest", key="long_rest"):
        success, data = long_rest_character(character['id'])
        if success:
            st.success(data.get('message', 'Long rest completed! HP and spell slots restored.'))
            st.rerun()
        else:
            st.error("Failed to take long rest!")
    
    # Spell sections by level
    available_spells = spell_data.get('available_spells', {})
    known_spells = set(spell_data.get('known_spells', []))
    prepared_spells = set(spell_data.get('prepared_spells', []))
    
    for level in range(0, 4):  # Show levels 0-3 like HTML template
        level_spells = available_spells.get(str(level), [])
        if level_spells:
            st.markdown(f"### {'🔮 Cantrips' if level == 0 else f'⚡ Level {level} Spells'}")
            
            # Display spells in a grid-like format
            spell_cols = st.columns(2)
            for i, spell in enumerate(level_spells):
                with spell_cols[i % 2]:
                    with st.container():
                        # Spell status indicators
                        status_text = ""
                        if spell in known_spells:
                            if spell in prepared_spells:
                                status_text = "✅ Known & Prepared"
                                spell_color = "blue"
                            else:
                                status_text = "📚 Known (not prepared)"
                                spell_color = "green"
                        else:
                            status_text = "🔍 Available to learn"
                            spell_color = "gray"
                        
                        st.markdown(f"**{spell}**")
                        st.caption(status_text)
                        
                        # Cast button for prepared spells
                        if spell in prepared_spells:
                            cast_key = f"cast_{spell}_{level}_{character['id']}"
                            
                            if level == 0:  # Cantrips
                                if st.button(f"🔮 Cast Cantrip", key=cast_key):
                                    success, data = cast_spell(character['id'], spell, level)
                                    if success:
                                        st.success(f"Cast {spell}!")
                                    else:
                                        st.error("Failed to cast spell!")
                            else:  # Leveled spells
                                can_cast = current_slots.get(str(level), 0) > 0
                                if st.button(
                                    f"⚡ Cast (Level {level})", 
                                    key=cast_key,
                                    disabled=not can_cast
                                ):
                                    if can_cast:
                                        success, data = cast_spell(character['id'], spell, level)
                                        if success:
                                            st.success(f"Cast {spell}! Spell slot consumed.")
                                            st.rerun()
                                        else:
                                            st.error("Failed to cast spell!")
                                    else:
                                        st.warning("No spell slots remaining!")
                        
                        st.markdown("---")

# Initialize session state with performance optimizations
if 'selected_character' not in st.session_state:
    st.session_state.selected_character = None
if 'last_roll' not in st.session_state:
    st.session_state.last_roll = None
if 'generated_scores' not in st.session_state:
    st.session_state.generated_scores = None
if 'flask_connected' not in st.session_state:
    st.session_state.flask_connected = None
# Performance optimization: cache character data
if 'cached_characters' not in st.session_state:
    st.session_state.cached_characters = None
if 'cache_timestamp' not in st.session_state:
    st.session_state.cache_timestamp = 0

# Sidebar navigation
st.sidebar.markdown("# 🐉 D&D Manager")

# Performance controls
if st.sidebar.button("🔄 Refresh Data", help="Clear all caches and reload fresh data"):
    invalidate_all_caches()
    st.sidebar.success("Data refreshed!")
    st.rerun()

st.sidebar.markdown("---")

# Check Flask connection only if not recently checked (optimized)
current_time = time.time()
last_check = getattr(st.session_state, 'last_connection_check', 0)

if st.session_state.flask_connected is None or current_time - last_check > 30:
    st.session_state.flask_connected = check_flask_connection()
    st.session_state.last_connection_check = current_time

if not st.session_state.flask_connected:
    st.sidebar.error("⚠️ Flask backend not running!")
    st.sidebar.info("Please start the Flask app:\n```python app.py```")
    if st.sidebar.button("🔄 Retry Connection"):
        st.session_state.flask_connected = None  # Force recheck
        st.rerun()
else:
    st.sidebar.success("✅ Connected to Flask backend")

# Navigation menu
page = st.sidebar.selectbox(
    "Navigate to:",
    ["🏠 Dashboard", "👤 Characters", "⚔️ Combat", "📜 Spells", "🎲 Dice Roller", "📚 Story Generator", "🧙‍♂️ AI Game Master"],
    key="navigation"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Quick Actions")

# Quick character count - only if Flask is connected
if st.session_state.flask_connected:
    try:
        characters = get_characters()
        st.sidebar.metric("Total Characters", len(characters))
        
        if characters:
            alive_count = sum(1 for c in characters if c.get('current_hp', 0) > 0)
            st.sidebar.metric("Characters Alive", alive_count)
    except:
        st.sidebar.warning("⚠️ Could not load character data")
        st.session_state.flask_connected = False  # Mark as disconnected

# Main content area
def show_dashboard():
    """Dashboard page"""
    st.markdown('<div class="main-header"><h1>🐉 D&D World Generator</h1><p>Enhanced Campaign Management System</p></div>', unsafe_allow_html=True)
    
    # Get characters once for the entire dashboard
    characters = get_characters()
    
    if not characters:
        st.info("🎭 Welcome! Create your first character to get started.")
        if st.button("➕ Create Character"):
            st.session_state.navigation = "👤 Characters"
            st.rerun()
        return
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🧙 Characters", len(characters))
    
    with col2:
        active_chars = sum(1 for c in characters if c.get('current_hp', 0) > 0)
        st.metric("💚 Alive", active_chars)
    
    with col3:
        total_levels = sum(c.get('level', 1) for c in characters)
        st.metric("⭐ Total Levels", total_levels)
    
    with col4:
        avg_level = round(total_levels / len(characters), 1) if characters else 0
        st.metric("📊 Avg Level", f"{avg_level}")
    
    # Character overview chart
    st.subheader("📊 Party Overview")
    
    # Health status chart
    names = [c['name'] for c in characters]
    current_hp = [c.get('current_hp', 0) for c in characters]
    max_hp = [c.get('max_hp', 1) for c in characters]
    
    fig = go.Figure()
    
    # Current HP bars
    fig.add_trace(go.Bar(
        name='Current HP',
        x=names,
        y=current_hp,
        marker_color='#51cf66',
        text=current_hp,
        textposition='inside'
    ))
    
    # Max HP outline
    fig.add_trace(go.Bar(
        name='Max HP',
        x=names,
        y=max_hp,
        marker_color='rgba(73, 80, 87, 0.3)',
        marker_line=dict(color='#495057', width=2)
    ))
    
    fig.update_layout(
        title="Party Health Status",
        barmode='overlay',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='#e6edf3',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Recent activity (placeholder)
    st.subheader("📈 Recent Activity")
    st.info("Activity tracking coming soon!")

def show_characters():
    """Characters management page"""
    st.header("👤 Character Management")
    
    tab1, tab2 = st.tabs(["📋 View Characters", "➕ Create Character"])
    
    with tab1:
        st.subheader("Your Characters")
        
        # Get characters once for this tab (optimized)
        characters = get_characters_optimized()
        
        if not characters:
            st.info("No characters found. Create your first character!")
            return
        
        # Character selection
        char_names = [f"{c['name']} (Lv.{c['level']} {c['character_class']})" for c in characters]
        
        selected_idx = st.selectbox(
            "Select Character",
            range(len(char_names)),
            format_func=lambda x: char_names[x],
            key="char_selector"
        )
        
        if selected_idx is not None:
            char = characters[selected_idx]
            
            # Character details
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.markdown(f'<div class="character-card">', unsafe_allow_html=True)
                st.subheader(f"🧙 {char['name']}")
                
                # Basic Character Information
                info_col1, info_col2 = st.columns(2)
                with info_col1:
                    st.write(f"**Race:** {char['race'].title()}")
                    st.write(f"**Class:** {char['character_class'].title()}")
                    st.write(f"**Level:** {char['level']}")
                with info_col2:
                    st.write(f"**Gender:** {char['gender'].title()}")
                    st.write(f"**Experience:** {char.get('experience', 0)} XP")
                    st.write(f"**Proficiency Bonus:** +{2 + (char['level'] - 1) // 4}")
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                # Health and combat stats
                hp_percentage = char['current_hp'] / char['max_hp'] if char['max_hp'] > 0 else 0
                st.metric("❤️ Health", f"{char['current_hp']}/{char['max_hp']}")
                st.progress(hp_percentage)
                
                st.metric("🛡️ Armor Class", char['armor_class'])
                
                # Currency
                gold = char.get('gold', 0)
                silver = char.get('silver', 0)
                copper = char.get('copper', 0)
                platinum = char.get('platinum', 0)
                
                currency_text = []
                if platinum > 0: currency_text.append(f"{platinum}pp")
                if gold > 0: currency_text.append(f"{gold}gp")
                if silver > 0: currency_text.append(f"{silver}sp")
                if copper > 0: currency_text.append(f"{copper}cp")
                
                st.write(f"**💰 Currency:** {', '.join(currency_text) if currency_text else '0 gp'}")
            
            with col3:
                st.subheader("Actions")
                
                if st.button("📜 View Spells", key=f"view_spells_{char['id']}"):
                    st.session_state.selected_character = char['id']
                    st.session_state.navigation = "📜 Spells"
                    st.rerun()
                
                if st.button("🎒 Inventory", key=f"inventory_{char['id']}"):
                    st.session_state.selected_character = char['id']
                    st.session_state.navigation = "👤 Characters"
                    st.session_state.show_inventory = True
                    st.rerun()
                
                if st.button("🔮 Spells", key=f"manage_spells_{char['id']}"):
                    st.session_state.selected_character = char['id']
                    st.session_state.navigation = "👤 Characters"
                    st.session_state.show_spells = True
                    st.rerun()
                
                if st.button("⚔️ Combat", key=f"combat_{char['id']}"):
                    st.session_state.selected_character = char['id']
                    st.session_state.navigation = "⚔️ Combat"
                    st.rerun()
                
                # Delete button
                st.markdown("---")
                if st.button("🗑️ Delete Character", key=f"delete_{char['id']}", type="secondary"):
                    # Create a confirmation dialog using session state
                    st.session_state[f"confirm_delete_{char['id']}"] = True
                
                # Show confirmation dialog if delete was clicked
                if st.session_state.get(f"confirm_delete_{char['id']}", False):
                    st.warning(f"Are you sure you want to delete **{char['name']}**? This action cannot be undone!")
                    col_yes, col_no = st.columns(2)
                    with col_yes:
                        if st.button("✅ Yes, Delete", key=f"confirm_yes_{char['id']}", type="primary"):
                            if delete_character(char['id']):
                                st.success(f"Character {char['name']} deleted successfully!")
                                # Clear caches for fresh data
                                invalidate_character_cache()
                                # Clear the confirmation state
                                if f"confirm_delete_{char['id']}" in st.session_state:
                                    del st.session_state[f"confirm_delete_{char['id']}"]
                                st.rerun()
                            else:
                                st.error("Failed to delete character!")
                    with col_no:
                        if st.button("❌ Cancel", key=f"confirm_no_{char['id']}"):
                            # Clear the confirmation state
                            if f"confirm_delete_{char['id']}" in st.session_state:
                                del st.session_state[f"confirm_delete_{char['id']}"]
                            st.rerun()
            
            # Ability scores
            st.subheader("📊 Ability Scores")
            ability_cols = st.columns(6)
            
            abilities = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
            for i, ability in enumerate(abilities):
                score = char.get(ability, 10)
                modifier = (score - 10) // 2
                modifier_str = f"+{modifier}" if modifier >= 0 else str(modifier)
                
                with ability_cols[i]:
                    st.metric(
                        ability.upper()[:3],
                        score,
                        modifier_str
                    )
            
            # Currency display
            st.subheader("💰 Currency")
            currency_cols = st.columns(4)
            
            with currency_cols[0]:
                platinum = char.get('platinum', 0)
                if platinum > 0:
                    st.metric("Platinum", f"{platinum}p")
                else:
                    st.metric("Platinum", "0p")
            
            with currency_cols[1]:
                gold = char.get('gold', 0)
                if gold > 0:
                    st.metric("Gold", f"{gold}g")
                else:
                    st.metric("Gold", "0g")
            
            with currency_cols[2]:
                silver = char.get('silver', 0)
                if silver > 0:
                    st.metric("Silver", f"{silver}s")
                else:
                    st.metric("Silver", "0s")
            
            with currency_cols[3]:
                copper = char.get('copper', 0)
                if copper > 0:
                    st.metric("Copper", f"{copper}c")
                else:
                    st.metric("Copper", "0c")
            
            # Show inventory if requested
            if st.session_state.get('show_inventory', False):
                show_character_inventory(char)
            
            # Show spells if requested
            if st.session_state.get('show_spells', False):
                show_character_spells(char)
    
    with tab2:
        st.subheader("➕ Create New Character")
        
        with st.form("character_creation"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Basic Information")
                name = st.text_input("Character Name*", placeholder="Enter character name")
                
                race = st.selectbox("Race", [
                    "Human", "Elf", "Dwarf", "Halfling", "Dragonborn", 
                    "Half-Elf", "Half-Orc", "Tiefling", "Gnome"
                ])
                
                char_class = st.selectbox("Class", [
                    "Fighter", "Wizard", "Rogue", "Cleric", "Ranger", "Paladin",
                    "Barbarian", "Bard", "Druid", "Monk", "Sorcerer", "Warlock"
                ])
                
                gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            
            with col2:
                st.markdown("#### Ability Scores")
                
                # Score generation method
                generation_method = st.radio(
                    "Generation Method",
                    ["Manual Entry", "4d6 Drop Lowest", "Standard Array"],
                    horizontal=True
                )
                
                # Generate scores button
                if generation_method != "Manual Entry":
                    if st.button("🎲 Generate Ability Scores"):
                        method = "4d6" if generation_method == "4d6 Drop Lowest" else "standard"
                        scores_data = generate_ability_scores(method, race.lower())
                        
                        if scores_data:
                            st.session_state.generated_scores = scores_data['scores']
                            st.success("Ability scores generated!")
                        else:
                            st.error("Failed to generate scores")
                
                # Ability score inputs
                scores = st.session_state.generated_scores or {}
                
                strength = st.number_input("Strength", 3, 18, scores.get('strength', 10))
                dexterity = st.number_input("Dexterity", 3, 18, scores.get('dexterity', 10))
                constitution = st.number_input("Constitution", 3, 18, scores.get('constitution', 10))
                intelligence = st.number_input("Intelligence", 3, 18, scores.get('intelligence', 10))
                wisdom = st.number_input("Wisdom", 3, 18, scores.get('wisdom', 10))
                charisma = st.number_input("Charisma", 3, 18, scores.get('charisma', 10))
                
                # Show modifiers
                st.markdown("**Modifiers:**")
                abilities = [strength, dexterity, constitution, intelligence, wisdom, charisma]
                ability_names = ['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA']
                
                modifier_text = []
                for i, score in enumerate(abilities):
                    mod = (score - 10) // 2
                    mod_str = f"+{mod}" if mod >= 0 else str(mod)
                    modifier_text.append(f"{ability_names[i]}: {mod_str}")
                
                st.text(" | ".join(modifier_text))
            
            # Submit button
            submitted = st.form_submit_button("🎭 Create Character", use_container_width=True)
            
            if submitted:
                if not name.strip():
                    st.error("Please enter a character name!")
                else:
                    char_data = {
                        'name': name.strip(),
                        'race': race.lower(),
                        'class': char_class.lower(),
                        'gender': gender.lower(),
                        'strength': strength,
                        'dexterity': dexterity,
                        'constitution': constitution,
                        'intelligence': intelligence,
                        'wisdom': wisdom,
                        'charisma': charisma
                    }
                    
                    with st.spinner("Creating character..."):
                        if create_character(char_data):
                            st.success(f"✅ {name} has been created successfully!")
                            # Clear caches to show new character immediately
                            invalidate_character_cache()
                            st.session_state.generated_scores = None  # Clear generated scores
                            st.rerun()
                        else:
                            st.error("❌ Failed to create character. Please check your Flask backend.")

def show_combat():
    """Combat management page"""
    st.header("⚔️ Combat Manager")
    
    if not characters:
        st.info("Create characters first to start combat!")
        return
    
    tab1, tab2 = st.tabs(["🎯 Quick Combat", "🗺️ Spatial Combat"])
    
    with tab1:
        st.subheader("Quick Combat Setup")
        
        # Character selection for combat
        char_options = {}
        for c in characters:
            label = f"{c['name']} (Lv.{c['level']} {c['character_class'].title()})"
            char_options[label] = c['id']
        
        selected_chars = st.multiselect(
            "Select Combatants",
            list(char_options.keys()),
            help="Choose characters to participate in combat"
        )
        
        if selected_chars:
            st.write("**Selected Combatants:**")
            for char_name in selected_chars:
                char_id = char_options[char_name]
                char = next(c for c in characters if c['id'] == char_id)
                
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"• {char_name}")
                with col2:
                    st.write(f"HP: {char['current_hp']}/{char['max_hp']}")
                with col3:
                    st.write(f"AC: {char['armor_class']}")
            
            if st.button("⚔️ Start Combat", type="primary"):
                char_ids = [char_options[name] for name in selected_chars]
                
                try:
                    response = requests.post(
                        f"{FLASK_URL}/combat/start",
                        json={"character_ids": char_ids, "name": "Streamlit Combat"},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        combat_data = response.json()
                        st.session_state.combat_id = combat_data.get('combat_id')
                        st.success("Combat started successfully!")
                        st.rerun()
                    else:
                        st.error(f"Failed to start combat: {response.status_code}")
                except Exception as e:
                    st.error(f"Error starting combat: {str(e)}")
        
        # Active combat display
        if hasattr(st.session_state, 'combat_id') and st.session_state.combat_id:
            st.subheader("🎲 Active Combat")
            
            # Load combat status with caching
            combat = get_combat_status(st.session_state.combat_id)
            
            if combat:
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Round", combat.get('round', 1))
                    with col2:
                        current_combatant = combat.get('current_combatant_name', 'Unknown')
                        st.metric("Current Turn", current_combatant)
                    
                    # Combatants table
                    if 'combatants' in combat:
                        combatants_data = []
                        for c in combat['combatants']:
                            status = "💀" if c.get('current_hp', 0) <= 0 else "💚"
                            combatants_data.append({
                                "Name": c.get('character_name', 'Unknown'),
                                "Initiative": c.get('initiative', 0),
                                "HP": f"{c.get('current_hp', 0)}/{c.get('max_hp', 1)}",
                                "AC": c.get('ac', 10),
                                "Status": status
                            })
                        
                        st.dataframe(combatants_data, use_container_width=True)
                    
                    # Enhanced Combat Actions
                    show_combat_actions(combat)
            else:
                st.error("Failed to load combat status")
                if st.button("Clear Combat"):
                    del st.session_state.combat_id
                    st.rerun()
    
    with tab2:
        st.subheader("🗺️ Spatial Combat Grid")
        
        if hasattr(st.session_state, 'combat_id') and st.session_state.combat_id:
            try:
                response = requests.get(f"{FLASK_URL}/api/spatial/{st.session_state.combat_id}/state", timeout=5)
                
                if response.status_code == 200:
                    spatial_data = response.json()
                    
                    grid = spatial_data.get('grid', {})
                    combatants = spatial_data.get('combatants', [])
                    
                    if combatants:
                        # Create combat grid visualization
                        grid_size = 20  # Default grid size
                        
                        # Extract combatant positions
                        x_coords = [c.get('x', 0) for c in combatants]
                        y_coords = [c.get('y', 0) for c in combatants]
                        names = [c.get('name', 'Unknown') for c in combatants]
                        hover_text = [f"{c.get('name', 'Unknown')}<br>HP: {c.get('hp', 0)}/{c.get('max_hp', 1)}<br>Position: ({c.get('x', 0)}, {c.get('y', 0)})" for c in combatants]
                        
                        # Color based on health
                        colors = []
                        for c in combatants:
                            hp_ratio = c.get('hp', 0) / max(c.get('max_hp', 1), 1)
                            if hp_ratio > 0.7:
                                colors.append('#51cf66')  # Green - healthy
                            elif hp_ratio > 0.3:
                                colors.append('#ffd43b')  # Yellow - wounded
                            elif hp_ratio > 0:
                                colors.append('#ff6b6b')  # Red - badly wounded
                            else:
                                colors.append('#495057')  # Gray - unconscious/dead
                        
                        # Create the plot
                        fig = go.Figure()
                        
                        # Add grid lines
                        for i in range(grid_size + 1):
                            fig.add_shape(
                                type="line",
                                x0=i-0.5, y0=-0.5,
                                x1=i-0.5, y1=grid_size-0.5,
                                line=dict(color="#2d3742", width=1)
                            )
                            fig.add_shape(
                                type="line",
                                x0=-0.5, y0=i-0.5,
                                x1=grid_size-0.5, y1=i-0.5,
                                line=dict(color="#2d3742", width=1)
                            )
                        
                        # Add combatants
                        fig.add_trace(go.Scatter(
                            x=x_coords,
                            y=y_coords,
                            mode='markers+text',
                            marker=dict(
                                size=25,
                                color=colors,
                                line=dict(color='white', width=2)
                            ),
                            text=names,
                            textposition="middle center",
                            textfont=dict(color="white", size=10),
                            hovertext=hover_text,
                            hoverinfo="text",
                            name="Combatants"
                        ))
                        
                        fig.update_layout(
                            title="Combat Grid",
                            xaxis=dict(
                                range=[-0.5, grid_size-0.5],
                                dtick=1,
                                showgrid=False,
                                title="X"
                            ),
                            yaxis=dict(
                                range=[-0.5, grid_size-0.5],
                                dtick=1,
                                showgrid=False,
                                title="Y"
                            ),
                            paper_bgcolor='rgba(15, 20, 25, 0.8)',
                            plot_bgcolor='#0f1419',
                            height=600,
                            font_color='#e6edf3',
                            showlegend=False
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        st.info("💡 **Tip:** Use the Flask interface for advanced movement and combat actions!")
                        
                        # Quick movement controls
                        st.subheader("Quick Movement")
                        if combatants:
                            char_to_move = st.selectbox(
                                "Select character to move",
                                [c.get('name', 'Unknown') for c in combatants]
                            )
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                new_x = st.number_input("New X position", 0, grid_size-1, 0)
                            with col2:
                                new_y = st.number_input("New Y position", 0, grid_size-1, 0)
                            
                            if st.button("Move Character"):
                                st.info("Movement feature coming soon! Use Flask interface for now.")
                    else:
                        st.info("No combatants found in spatial combat.")
                else:
                    st.error("Failed to load spatial combat data")
            except Exception as e:
                st.error(f"Error loading spatial combat: {str(e)}")
        else:
            st.info("Start a combat first to use spatial features")

def show_spells():
    """Spells management page"""
    st.header("📜 Spell Management")
    
    # Filter spellcasting characters
    spellcasting_classes = ['wizard', 'sorcerer', 'cleric', 'bard', 'druid', 'warlock', 'paladin', 'ranger']
    spellcasters = [c for c in characters if c.get('character_class', '').lower() in spellcasting_classes]
    
    if not spellcasters:
        st.info("No spellcasting characters found. Create a spellcaster to manage spells!")
        return
    
    # Character selection
    if st.session_state.selected_character:
        # Try to find the selected character
        selected_char = next((c for c in spellcasters if c['id'] == st.session_state.selected_character), None)
        if not selected_char:
            st.session_state.selected_character = None
            selected_char = spellcasters[0]
    else:
        selected_char = spellcasters[0]
    
    char_names = [f"{c['name']} ({c['character_class'].title()})" for c in spellcasters]
    char_ids = [c['id'] for c in spellcasters]
    
    current_idx = char_ids.index(selected_char['id']) if selected_char['id'] in char_ids else 0
    
    selected_idx = st.selectbox(
        "Select Spellcaster",
        range(len(char_names)),
        format_func=lambda x: char_names[x],
        index=current_idx,
        key="spell_char_selector"
    )
    
    if selected_idx is not None:
        char = spellcasters[selected_idx]
        st.session_state.selected_character = char['id']
        
        # Character header
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader(f"🔮 {char['name']}'s Spells")
            st.write(f"{char['race'].title()} {char['character_class'].title()} (Level {char['level']})")
        
        with col2:
            if st.button("🌙 Long Rest"):
                try:
                    response = requests.post(f"{FLASK_URL}/character/{char['id']}/long_rest", timeout=5)
                    if response.status_code == 200:
                        st.success("🌙 Spell slots and HP restored!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Failed to complete long rest")
                except Exception as e:
                    st.error(f"Error during long rest: {str(e)}")
        
        # Spell slot visualization
        st.subheader("🔮 Spell Slots")
        
        # Mock spell slot data (replace with actual API call when available)
        spell_slots = {
            1: {"current": 2, "max": 3},
            2: {"current": 1, "max": 2},
            3: {"current": 0, "max": 1}
        }
        
        for level, slots in spell_slots.items():
            col1, col2 = st.columns([1, 4])
            
            with col1:
                st.write(f"**Level {level}:**")
            
            with col2:
                # Visual spell slots
                slot_html = ""
                for i in range(slots["max"]):
                    if i < slots["current"]:
                        slot_html += '<span class="spell-slot-filled">🔵</span>'
                    else:
                        slot_html += '<span class="spell-slot-empty">⚪</span>'
                
                slot_html += f' <span style="margin-left: 10px; color: #6c757d;">({slots["current"]}/{slots["max"]})</span>'
                st.markdown(slot_html, unsafe_allow_html=True)
        
        # Spell lists
        st.subheader("📚 Available Spells")
        
        # Mock spell data (replace with actual API call)
        spell_categories = {
            "Cantrips": ["Mage Hand", "Prestidigitation", "Fire Bolt", "Light"],
            "1st Level": ["Magic Missile", "Shield", "Cure Wounds", "Bless"],
            "2nd Level": ["Misty Step", "Web", "Hold Person"],
            "3rd Level": ["Fireball", "Counterspell", "Fly"]
        }
        
        for category, spells in spell_categories.items():
            with st.expander(f"✨ {category}", expanded=True):
                spell_cols = st.columns(min(len(spells), 3))
                
                for i, spell in enumerate(spells):
                    col_idx = i % len(spell_cols)
                    
                    with spell_cols[col_idx]:
                        st.markdown(f"**{spell}**")
                        
                        if category == "Cantrips":
                            if st.button(f"Cast {spell}", key=f"cast_{spell}_{char['id']}"):
                                st.success(f"✨ Cast {spell} (Cantrip)")
                        else:
                            level = int(category.split()[0][:-2])  # Extract level number
                            available_slots = spell_slots.get(level, {}).get("current", 0)
                            
                            if available_slots > 0:
                                if st.button(f"Cast {spell}", key=f"cast_{spell}_{char['id']}"):
                                    st.success(f"✨ Cast {spell} (Level {level})")
                                    # Here you would call the Flask API to actually cast the spell
                            else:
                                st.button(f"No Slots", disabled=True, key=f"no_slot_{spell}_{char['id']}")
        
        st.info("💡 **Note:** Full spell integration coming soon! Use the Flask interface for complete spell management.")

def show_dice_roller():
    """Dice roller page"""
    st.header("🎲 Dice Roller")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Quick Rolls")
        
        dice_presets = {
            "d20": "1d20",
            "d20 + 5": "1d20+5",
            "d20 Advantage": "2d20kh1",  # Keep highest
            "d20 Disadvantage": "2d20kl1",  # Keep lowest
            "2d6": "2d6",
            "3d6": "3d6",
            "4d6 Drop Lowest": "4d6dl1",
            "Damage 1d8+3": "1d8+3",
            "Fireball 8d6": "8d6",
            "Healing 1d4+2": "1d4+2"
        }
        
        for label, dice_notation in dice_presets.items():
            if st.button(f"🎲 {label}", key=f"preset_{label}", use_container_width=True):
                with st.spinner("Rolling..."):
                    result = roll_dice(dice_notation)
                if result:
                    st.session_state.last_roll = result
                    st.rerun()  # Refresh to show result immediately
                else:
                    # Fallback for unsupported notation
                    simple_notation = dice_notation.split('k')[0].split('d')[0] + 'd' + dice_notation.split('d')[1].split('k')[0].split('d')[0]
                    if '+' in dice_notation:
                        simple_notation += '+' + dice_notation.split('+')[1]
                    result = roll_dice(simple_notation)
                    if result:
                        st.session_state.last_roll = result
                        st.rerun()
                    else:
                        st.error("Failed to roll dice")
    
    with col2:
        st.subheader("Custom Roll")
        
        custom_dice = st.text_input(
            "Dice Notation",
            placeholder="1d20+5, 3d6, 2d8+3",
            value="1d20",
            help="Examples: 1d20, 3d6+2, 1d8+3"
        )
        
        col2a, col2b = st.columns(2)
        
        with col2a:
            if st.button("🎲 Roll Custom", type="primary", use_container_width=True):
                with st.spinner("Rolling..."):
                    result = roll_dice(custom_dice)
                if result:
                    st.session_state.last_roll = result
                    st.rerun()  # Refresh to show result immediately
                else:
                    st.error("Invalid dice notation or connection error")
        
        with col2b:
            if st.button("🔄 Roll Multiple", use_container_width=True):
                with st.spinner("Rolling multiple times..."):
                    results = []
                    for _ in range(5):
                        result = roll_dice(custom_dice)
                        if result:
                            results.append(result['total'])
                
                if results:
                    st.session_state.multiple_rolls = results
                    st.rerun()  # Refresh to show results immediately
                else:
                    st.error("Failed to roll dice")
        
        # Display last roll result
        if hasattr(st.session_state, 'last_roll') and st.session_state.last_roll:
            result = st.session_state.last_roll
            
            st.subheader("🎯 Last Roll Result")
            
            # Big result display
            st.markdown(f'<div class="dice-result">{result["total"]}</div>', unsafe_allow_html=True)
            
            # Details
            if result.get('rolls'):
                st.write(f"**Individual Rolls:** {result['rolls']}")
            if result.get('modifier', 0) != 0:
                modifier = result['modifier']
                st.write(f"**Modifier:** {'+' if modifier >= 0 else ''}{modifier}")
            
            st.write(f"**Notation:** {result.get('notation', custom_dice)}")
            
            # Result interpretation
            total = result['total']
            if 'd20' in result.get('notation', ''):
                if total == 20:
                    st.success("🎉 Natural 20! Critical Success!")
                elif total == 1:
                    st.error("💀 Natural 1! Critical Failure!")
                elif total >= 15:
                    st.info("👍 Great roll!")
                elif total <= 5:
                    st.warning("😬 That could have gone better...")
        
        # Display multiple rolls
        if hasattr(st.session_state, 'multiple_rolls') and st.session_state.multiple_rolls:
            st.subheader("🎲 Multiple Rolls")
            
            rolls = st.session_state.multiple_rolls
            
            col_rolls = st.columns(len(rolls))
            for i, roll in enumerate(rolls):
                with col_rolls[i]:
                    st.metric(f"Roll {i+1}", roll)
            
            # Statistics
            st.write(f"**Average:** {sum(rolls) / len(rolls):.1f}")
            st.write(f"**Total:** {sum(rolls)}")
            st.write(f"**Range:** {min(rolls)} - {max(rolls)}")

def show_story_generator():
    """Story generator page"""
    st.header("📚 Story Generator")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Generate Adventure Content")
        
        # Character context
        if characters:
            char_options = ["None"] + [c['name'] for c in characters]
            selected_char_name = st.selectbox("Focus Character (optional)", char_options)
            selected_char_id = ""
            
            if selected_char_name != "None":
                selected_char = next(c for c in characters if c['name'] == selected_char_name)
                selected_char_id = str(selected_char['id'])
        else:
            selected_char_id = ""
        
        # Story type
        story_type = st.selectbox(
            "Story Type",
            ["Custom Prompt", "Random Encounter", "NPC Dialogue", "Location Description", "Plot Hook"]
        )
        
        # Story prompt
        if story_type == "Custom Prompt":
            prompt = st.text_area(
                "Story Prompt",
                placeholder="Describe the situation or ask for a story continuation...",
                height=100
            )
        else:
            prompt = ""
            st.info(f"Will generate: {story_type}")
        
        # Environment/setting
        environment = st.selectbox(
            "Environment",
            ["Any", "Forest", "Dungeon", "City", "Mountains", "Swamp", "Desert", "Coast", "Plains"]
        )
        
        if st.button("✨ Generate Story", type="primary"):
            try:
                data = {
                    'prompt': prompt,
                    'character_id': selected_char_id,
                    'encounter_type': story_type.lower().replace(' ', '_'),
                    'environment': environment.lower()
                }
                
                with st.spinner("Generating story..."):
                    response = requests.post(f"{FLASK_URL}/generate_story", data=data, timeout=15)
                
                if response.status_code == 200:
                    story_data = response.json()
                    story = story_data.get('story', 'No story generated')
                    st.session_state.current_story = story
                else:
                    st.error("Failed to generate story")
            except Exception as e:
                st.error(f"Error generating story: {str(e)}")
    
    with col2:
        st.subheader("💡 Quick Ideas")
        
        # Quick story prompts
        quick_prompts = [
            "The party finds a mysterious locked chest",
            "A stranger approaches in the tavern",
            "Strange sounds echo from the forest",
            "The ground begins to shake",
            "A merchant offers a peculiar deal",
            "Ancient runes glow on the wall",
            "The weather suddenly changes",
            "A cry for help echoes nearby"
        ]
        
        for prompt in quick_prompts:
            if st.button(f"💭 {prompt[:25]}...", key=f"quick_{prompt}", use_container_width=True):
                st.session_state.suggested_prompt = prompt
                # Auto-fill the prompt
                st.rerun()
        
        st.markdown("---")
        
        # Story stats
        st.subheader("📊 Campaign Stats")
        st.metric("Total Characters", len(characters))
        
        if characters:
            total_levels = sum(c.get('level', 1) for c in characters)
            st.metric("Party Level", f"{total_levels // len(characters):.0f}")
            
            alive_chars = sum(1 for c in characters if c.get('current_hp', 0) > 0)
            st.metric("Characters Alive", alive_chars)
    
    # Display generated story
    if hasattr(st.session_state, 'current_story') and st.session_state.current_story:
        st.markdown("---")
        st.subheader("📖 Generated Story")
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #17202a, #1e2a3a); 
            padding: 25px; 
            border-radius: 12px; 
            border-left: 4px solid #8ab4f8;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            font-size: 16px;
            line-height: 1.6;
        ">
        {st.session_state.current_story}
        </div>
        """, unsafe_allow_html=True)
        
        # Story actions
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📋 Copy Story"):
                st.write("Copy functionality would be implemented here")
        
        with col2:
            if st.button("🔄 Generate Another"):
                st.session_state.current_story = None
                st.rerun()
        
        with col3:
            if st.button("💾 Save Story"):
                st.info("Story saving feature coming soon!")

# Main app logic
def main():
    """Main application logic"""
    
    # Add a refresh button in the sidebar for cache management
    if st.session_state.flask_connected:
        st.sidebar.markdown("---")
        if st.sidebar.button("🔄 Refresh Data"):
            invalidate_character_cache()
            st.session_state.flask_connected = None  # Force connection recheck
            st.cache_data.clear()  # Clear all cached data
            st.success("Data refreshed!")
            st.rerun()
        
        # Performance debugging (only show if there are issues)
        if st.sidebar.checkbox("🔧 Performance Debug", value=False):
            st.sidebar.markdown("**Cache Status:**")
            cache_info = get_characters.cache_info if hasattr(get_characters, 'cache_info') else None
            if cache_info:
                st.sidebar.text(f"Characters: {cache_info}")
            
            st.sidebar.markdown("**Connection:**")
            start_time = time.time()
            test_conn = check_flask_connection()
            conn_time = (time.time() - start_time) * 1000
            st.sidebar.text(f"Flask: {conn_time:.1f}ms")
            
            if st.sidebar.button("Clear All Cache"):
                st.cache_data.clear()
                st.sidebar.success("Cache cleared!")
    
    # Page routing with error handling
    try:
        if page == "🏠 Dashboard":
            show_dashboard()
        elif page == "👤 Characters":
            show_characters()
        elif page == "⚔️ Combat":
            show_combat()
        elif page == "📜 Spells":
            show_spells()
        elif page == "🎲 Dice Roller":
            show_dice_roller()
        elif page == "📚 Story Generator":
            show_story_generator()
        elif page == "🧙‍♂️ AI Game Master":
            show_ai_game_master()
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.info("Try refreshing the page or check your Flask backend connection.")

# AI Game Master Functions
def show_ai_game_master():
    """AI Game Master page with dynamic storytelling"""
    st.header("🧙‍♂️ AI Game Master")
    
    # Get characters for context
    characters = get_characters_optimized()
    
    # Initialize AI GM session state
    if 'gm_session' not in st.session_state:
        st.session_state.gm_session = {
            'story_log': [],
            'current_scene': None,
            'party_status': 'exploring',
            'scene_counter': 0,
            'active_npcs': [],
            'inventory_rewards': []
        }
    
    # GM Control Panel
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🎭 Active Campaign")
        
        # Current scene display
        if st.session_state.gm_session['current_scene']:
            scene = st.session_state.gm_session['current_scene']
            
            # Scene header
            scene_type_emoji = {
                'narrative': '📖',
                'combat': '⚔️',
                'social': '🗣️',
                'exploration': '🔍',
                'rest': '🏕️',
                'reward': '🎁'
            }
            
            st.markdown(f"## {scene_type_emoji.get(scene.get('type', 'narrative'), '📖')} {scene.get('title', 'Current Scene')}")
            
            # Scene description
            st.markdown(f"*{scene.get('description', 'The adventure continues...')}*")
            
            # Dynamic scene actions
            if scene.get('type') == 'combat':
                show_gm_combat_scene(scene, characters)
            elif scene.get('type') == 'social':
                show_gm_social_scene(scene, characters)
            elif scene.get('type') == 'exploration':
                show_gm_exploration_scene(scene, characters)
            elif scene.get('type') == 'reward':
                show_gm_reward_scene(scene, characters)
            else:
                show_gm_narrative_scene(scene, characters)
        
        else:
            st.info("🎬 Ready to begin your adventure! Generate a new scene to start.")
            
        # GM Action Buttons
        st.markdown("---")
        gm_col1, gm_col2, gm_col3, gm_col4 = st.columns(4)
        
        with gm_col1:
            if st.button("🎲 Generate Scene", type="primary"):
                generate_new_scene(characters)
                st.rerun()
        
        with gm_col2:
            if st.button("⚔️ Trigger Combat"):
                trigger_combat_encounter(characters)
                st.rerun()
        
        with gm_col3:
            if st.button("🎁 Give Reward"):
                trigger_reward_scene(characters)
                st.rerun()
        
        with gm_col4:
            if st.button("🔄 Continue Story"):
                continue_current_story(characters)
                st.rerun()
    
    with col2:
        st.subheader("📊 Campaign Status")
        
        # Party status
        status_colors = {
            'exploring': '🟢',
            'in_combat': '🔴',
            'resting': '🟡',
            'social': '🔵'
        }
        status = st.session_state.gm_session.get('party_status', 'exploring')
        st.markdown(f"**Party Status:** {status_colors.get(status, '⚪')} {status.title()}")
        
        st.metric("Scenes Played", st.session_state.gm_session.get('scene_counter', 0))
        
        # Active NPCs
        if st.session_state.gm_session.get('active_npcs'):
            st.markdown("**Active NPCs:**")
            for npc in st.session_state.gm_session['active_npcs']:
                st.markdown(f"• {npc.get('name', 'Unknown')} - {npc.get('role', 'NPC')}")
        
        # Recent rewards
        if st.session_state.gm_session.get('inventory_rewards'):
            st.markdown("**Recent Rewards:**")
            for reward in st.session_state.gm_session['inventory_rewards'][-3:]:
                st.markdown(f"• {reward}")
        
        st.markdown("---")
        
        # Campaign controls
        st.subheader("🎮 GM Controls")
        
        if st.button("📋 View Story Log"):
            show_story_log()
        
        if st.button("🔄 Reset Campaign"):
            if st.checkbox("Confirm Reset"):
                st.session_state.gm_session = {
                    'story_log': [],
                    'current_scene': None,
                    'party_status': 'exploring',
                    'scene_counter': 0,
                    'active_npcs': [],
                    'inventory_rewards': []
                }
                st.success("Campaign reset!")
                st.rerun()

def generate_new_scene(characters):
    """Generate a new scene with the AI GM"""
    scene_types = ['narrative', 'combat', 'social', 'exploration', 'rest', 'reward']
    import random
    
    # Create a dynamic scene based on party status and random elements
    scene_type = random.choice(scene_types)
    
    # Scene templates
    scene_templates = {
        'narrative': {
            'titles': ['The Path Ahead', 'A Strange Discovery', 'Whispers in the Wind', 'An Unexpected Turn'],
            'descriptions': [
                'As you continue your journey, something catches your attention in the distance...',
                'The ancient ruins hold secrets that beckon to be explored...',
                'A mysterious figure watches from the shadows...',
                'The very air seems to hum with magical energy...'
            ]
        },
        'combat': {
            'titles': ['Ambush!', 'Hostile Encounter', 'Battle Erupts', 'Enemies Attack'],
            'descriptions': [
                'Suddenly, enemies emerge from their hiding spots! Roll for initiative!',
                'The peaceful moment is shattered as combat begins!',
                'Your weapons are needed as danger presents itself!',
                'The tension breaks as battle is joined!'
            ]
        },
        'social': {
            'titles': ['A Chance Meeting', 'Diplomatic Encounter', 'Village Folk', 'The Stranger'],
            'descriptions': [
                'You encounter someone who might have information or need assistance...',
                'A conversation begins that could change your path...',
                'The locals have stories to tell and favors to ask...',
                'This meeting could lead to new opportunities...'
            ]
        },
        'exploration': {
            'titles': ['Hidden Passage', 'Secret Chamber', 'Mysterious Door', 'Ancient Mechanism'],
            'descriptions': [
                'You discover something that requires investigation...',
                'Your skills are needed to uncover hidden secrets...',
                'The environment holds challenges to overcome...',
                'Ancient puzzles await your clever solutions...'
            ]
        },
        'reward': {
            'titles': ['Treasure Found!', 'Hidden Cache', 'Generous Reward', 'Magical Discovery'],
            'descriptions': [
                'Your efforts have been rewarded with valuable treasure!',
                'You uncover a cache of useful items and gold!',
                'Someone shows their gratitude with generous gifts!',
                'Magic items reveal themselves to worthy adventurers!'
            ]
        }
    }
    
    template = scene_templates.get(scene_type, scene_templates['narrative'])
    title = random.choice(template['titles'])
    description = random.choice(template['descriptions'])
    
    # Create the scene
    scene = {
        'type': scene_type,
        'title': title,
        'description': description,
        'id': f"scene_{st.session_state.gm_session['scene_counter'] + 1}",
        'characters_present': [c['name'] for c in characters[:4]] if characters else []
    }
    
    # Add scene-specific data
    if scene_type == 'combat':
        scene['enemies'] = generate_combat_enemies(characters)
        st.session_state.gm_session['party_status'] = 'in_combat'
    elif scene_type == 'social':
        scene['npcs'] = generate_scene_npcs()
        st.session_state.gm_session['party_status'] = 'social'
        st.session_state.gm_session['active_npcs'].extend(scene['npcs'])
    elif scene_type == 'reward':
        scene['rewards'] = generate_scene_rewards(characters)
        
    # Update session
    st.session_state.gm_session['current_scene'] = scene
    st.session_state.gm_session['scene_counter'] += 1
    st.session_state.gm_session['story_log'].append(scene)

def generate_combat_enemies(characters):
    """Generate appropriate enemies for combat"""
    import random
    
    if not characters:
        return [{'name': 'Goblin Scout', 'hp': 15, 'ac': 12}]
    
    party_level = sum(c.get('level', 1) for c in characters) // len(characters)
    
    enemy_templates = {
        1: [
            {'name': 'Goblin', 'hp': 15, 'ac': 12},
            {'name': 'Wolf', 'hp': 18, 'ac': 13},
            {'name': 'Bandit', 'hp': 20, 'ac': 14}
        ],
        2: [
            {'name': 'Orc Warrior', 'hp': 35, 'ac': 15},
            {'name': 'Hobgoblin', 'hp': 32, 'ac': 16},
            {'name': 'Dire Wolf', 'hp': 42, 'ac': 14}
        ],
        3: [
            {'name': 'Ogre', 'hp': 65, 'ac': 16},
            {'name': 'Owlbear', 'hp': 58, 'ac': 15},
            {'name': 'Veteran Soldier', 'hp': 68, 'ac': 17}
        ]
    }
    
    enemy_tier = min(max(1, party_level), 3)
    possible_enemies = enemy_templates[enemy_tier]
    
    num_enemies = random.randint(1, min(3, len(characters) + 1))
    return random.choices(possible_enemies, k=num_enemies)

def generate_scene_npcs():
    """Generate NPCs for social encounters"""
    import random
    
    npc_templates = [
        {'name': 'Elara the Merchant', 'role': 'Trader', 'disposition': 'friendly'},
        {'name': 'Gruff the Blacksmith', 'role': 'Craftsman', 'disposition': 'neutral'},
        {'name': 'Sister Amelia', 'role': 'Cleric', 'disposition': 'helpful'},
        {'name': 'Captain Roderick', 'role': 'Guard Captain', 'disposition': 'suspicious'},
        {'name': 'Old Henrik', 'role': 'Village Elder', 'disposition': 'wise'},
        {'name': 'Zara the Mysterious', 'role': 'Stranger', 'disposition': 'cryptic'}
    ]
    
    return [random.choice(npc_templates)]

def generate_scene_rewards(characters):
    """Generate appropriate rewards"""
    import random
    
    if not characters:
        return ['50 gold pieces', 'Healing Potion']
    
    party_level = sum(c.get('level', 1) for c in characters) // len(characters)
    
    reward_templates = {
        1: ['Healing Potion', '25 gold pieces', 'Silver Ring', 'Leather Armor'],
        2: ['Greater Healing Potion', '100 gold pieces', 'Magic Weapon (+1)', 'Chain Mail'],
        3: ['Superior Healing Potion', '250 gold pieces', 'Magic Weapon (+2)', 'Plate Armor', 'Wand of Magic Missiles']
    }
    
    reward_tier = min(max(1, party_level), 3)
    possible_rewards = reward_templates[reward_tier]
    
    num_rewards = random.randint(1, 3)
    return random.choices(possible_rewards, k=num_rewards)

def show_gm_combat_scene(scene, characters):
    """Display combat scene interface"""
    st.markdown("### ⚔️ Combat Encounter!")
    
    enemies = scene.get('enemies', [])
    
    if enemies:
        st.markdown("**Enemies encountered:**")
        for enemy in enemies:
            st.markdown(f"• **{enemy['name']}** (HP: {enemy['hp']}, AC: {enemy['ac']})")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🎲 Roll Initiative", key="roll_init"):
            import random
            party_init = random.randint(1, 20) + 2
            enemy_init = random.randint(1, 20) + 1
            
            if party_init >= enemy_init:
                st.success(f"🎉 Party goes first! (Party: {party_init}, Enemies: {enemy_init})")
            else:
                st.warning(f"⚠️ Enemies go first! (Enemies: {enemy_init}, Party: {party_init})")
            
    with col2:
        if st.button("⚔️ Start Combat Manager", key="start_combat"):
            st.session_state.navigation = "⚔️ Combat"
            st.rerun()

def show_gm_social_scene(scene, characters):
    """Display social encounter interface"""
    st.markdown("### 🗣️ Social Encounter")
    
    npcs = scene.get('npcs', [])
    
    if npcs:
        for npc in npcs:
            st.markdown(f"**{npc['name']}** - {npc['role']} ({npc['disposition']})")
    
    response_options = [
        "Approach diplomatically",
        "Ask for information", 
        "Offer assistance",
        "Remain cautious"
    ]
    
    chosen_response = st.selectbox("How do you respond?", response_options)
    
    if st.button("🎭 Make Response"):
        st.success(f"You choose to: {chosen_response.lower()}")
        # Generate NPC reaction
        reactions = [
            "The NPC seems pleased with your approach.",
            "They provide useful information about the area.",
            "They offer to help you in return.",
            "They become more trusting of your party."
        ]
        import random
        st.info(random.choice(reactions))

def show_gm_exploration_scene(scene, characters):
    """Display exploration scene interface"""
    st.markdown("### 🔍 Exploration Challenge")
    
    challenges = [
        "Ancient puzzle mechanism",
        "Hidden trap to disarm", 
        "Locked door to pick",
        "Magical barrier to dispel",
        "Secret passage to find"
    ]
    
    import random
    challenge = random.choice(challenges)
    st.markdown(f"**Challenge:** {challenge}")
    
    skills = ["Investigation", "Perception", "Thieves' Tools", "Arcana", "Athletics"]
    chosen_skill = st.selectbox("Which skill do you use?", skills)
    
    if st.button("🎲 Make Skill Check"):
        roll = random.randint(1, 20)
        total = roll + random.randint(1, 6)  # Simulate modifier
        
        st.markdown(f"**Roll:** {roll} + modifier = **{total}**")
        
        if total >= 15:
            st.success("🎉 Success! You overcome the challenge!")
        elif total >= 10:
            st.warning("⚠️ Partial success - you make progress but face complications.")
        else:
            st.error("❌ The challenge proves too difficult this time.")

def show_gm_reward_scene(scene, characters):
    """Display reward scene interface"""
    st.markdown("### 🎁 Rewards Discovered!")
    
    rewards = scene.get('rewards', [])
    
    if rewards:
        st.markdown("**You have found:**")
        for reward in rewards:
            st.markdown(f"• {reward}")
            
        if st.button("📦 Collect Rewards"):
            # Add to party inventory
            st.session_state.gm_session['inventory_rewards'].extend(rewards)
            st.success("Rewards added to party inventory!")
            
            # Try to add items to character inventories
            for i, character in enumerate(characters[:len(rewards)]):
                try:
                    if add_item_to_character(character['id'], rewards[i]):
                        st.success(f"Added {rewards[i]} to {character['name']}'s inventory!")
                except:
                    st.info(f"Could not add {rewards[i]} directly to inventory - check manually.")

def show_gm_narrative_scene(scene, characters):
    """Display narrative scene interface"""
    st.markdown("### 📖 The Story Continues...")
    
    # Narrative choices
    choices = [
        "Investigate further",
        "Move on cautiously", 
        "Rest and observe",
        "Take immediate action"
    ]
    
    chosen_action = st.selectbox("What does the party do?", choices)
    
    if st.button("➡️ Continue Adventure"):
        st.success(f"The party decides to: {chosen_action.lower()}")
        # Generate consequence
        consequences = [
            "Your careful approach reveals new information.",
            "The party discovers something unexpected.",
            "Your actions attract attention from nearby creatures.",
            "The path ahead becomes clearer."
        ]
        import random
        st.info(random.choice(consequences))

def trigger_combat_encounter(characters):
    """Manually trigger a combat encounter"""
    enemies = generate_combat_enemies(characters)
    
    scene = {
        'type': 'combat',
        'title': 'Combat Triggered!',
        'description': 'The Game Master has initiated a combat encounter!',
        'enemies': enemies,
        'id': f"combat_{st.session_state.gm_session['scene_counter'] + 1}",
        'characters_present': [c['name'] for c in characters[:4]] if characters else []
    }
    
    st.session_state.gm_session['current_scene'] = scene
    st.session_state.gm_session['scene_counter'] += 1
    st.session_state.gm_session['story_log'].append(scene)
    st.session_state.gm_session['party_status'] = 'in_combat'

def trigger_reward_scene(characters):
    """Manually trigger a reward scene"""
    rewards = generate_scene_rewards(characters)
    
    scene = {
        'type': 'reward',
        'title': 'Treasure Discovered!',
        'description': 'The Game Master grants rewards to the party!',
        'rewards': rewards,
        'id': f"reward_{st.session_state.gm_session['scene_counter'] + 1}",
        'characters_present': [c['name'] for c in characters[:4]] if characters else []
    }
    
    st.session_state.gm_session['current_scene'] = scene
    st.session_state.gm_session['scene_counter'] += 1
    st.session_state.gm_session['story_log'].append(scene)

def continue_current_story(characters):
    """Continue the current story with a follow-up scene"""
    if not st.session_state.gm_session.get('current_scene'):
        generate_new_scene(characters)
        return
    
    # Generate a related follow-up scene
    current_type = st.session_state.gm_session['current_scene'].get('type', 'narrative')
    
    # Story progression logic
    next_scenes = {
        'combat': ['rest', 'reward', 'exploration'],
        'social': ['narrative', 'exploration', 'combat'],
        'exploration': ['reward', 'combat', 'social'],
        'reward': ['narrative', 'rest', 'social'],
        'rest': ['narrative', 'exploration', 'social'],
        'narrative': ['combat', 'social', 'exploration']
    }
    
    import random
    next_type = random.choice(next_scenes.get(current_type, ['narrative']))
    
    # Generate new scene with influenced type
    scene_types = [next_type] * 3 + ['narrative']  # Weight toward next_type
    scene_type = random.choice(scene_types)
    
    # Use scene templates from generate_new_scene
    scene_templates = {
        'narrative': {
            'titles': ['The Path Ahead', 'A Strange Discovery', 'Whispers in the Wind', 'An Unexpected Turn'],
            'descriptions': [
                'As the previous events settle, something new catches your attention...',
                'The consequences of your actions become apparent...',
                'A new challenge presents itself...',
                'The adventure continues in an unexpected direction...'
            ]
        },
        'combat': {
            'titles': ['Another Threat!', 'Reinforcements Arrive', 'Danger Returns', 'More Enemies'],
            'descriptions': [
                'Just when you thought it was safe, more enemies appear!',
                'The commotion has attracted additional threats!',
                'Your previous actions have consequences - combat erupts again!',
                'The danger is not over yet!'
            ]
        },
        'social': {
            'titles': ['New Allies', 'Witnesses Arrive', 'Help Appears', 'Curious Onlookers'],
            'descriptions': [
                'Your recent actions have attracted the attention of others...',
                'Someone approaches, having witnessed recent events...',
                'New people arrive who might be helpful or problematic...',
                'The situation draws interested parties...'
            ]
        },
        'exploration': {
            'titles': ['Hidden Consequences', 'New Discoveries', 'What Lies Beyond', 'Deeper Mysteries'],
            'descriptions': [
                'Your actions have revealed new areas to explore...',
                'The results of your choices open new paths...',
                'Hidden aspects of this place become apparent...',
                'There is more here than initially met the eye...'
            ]
        },
        'reward': {
            'titles': ['Well Deserved', 'Additional Treasures', 'Grateful Benefactors', 'Hidden Rewards'],
            'descriptions': [
                'Your recent actions have earned additional rewards!',
                'Hidden treasures reveal themselves after recent events!',
                'Someone wishes to show gratitude for your deeds!',
                'Your efforts continue to bear fruit!'
            ]
        },
        'rest': {
            'titles': ['A Moment of Peace', 'Time to Recover', 'Respite Found', 'Catching Your Breath'],
            'descriptions': [
                'The intensity subsides, allowing time to rest and recover...',
                'A safe space presents itself for the party to regroup...',
                'The immediate danger passes, providing a chance to rest...',
                'Circumstances allow for a brief respite...'
            ]
        }
    }
    
    template = scene_templates.get(scene_type, scene_templates['narrative'])
    title = random.choice(template['titles'])
    description = random.choice(template['descriptions'])
    
    # Create the follow-up scene
    scene = {
        'type': scene_type,
        'title': title,
        'description': description,
        'id': f"scene_{st.session_state.gm_session['scene_counter'] + 1}",
        'characters_present': [c['name'] for c in characters[:4]] if characters else []
    }
    
    # Add scene-specific data
    if scene_type == 'combat':
        scene['enemies'] = generate_combat_enemies(characters)
        st.session_state.gm_session['party_status'] = 'in_combat'
    elif scene_type == 'social':
        scene['npcs'] = generate_scene_npcs()
        st.session_state.gm_session['party_status'] = 'social'
        st.session_state.gm_session['active_npcs'].extend(scene['npcs'])
    elif scene_type == 'reward':
        scene['rewards'] = generate_scene_rewards(characters)
    elif scene_type == 'rest':
        st.session_state.gm_session['party_status'] = 'resting'
    else:
        st.session_state.gm_session['party_status'] = 'exploring'
        
    # Update session
    st.session_state.gm_session['current_scene'] = scene
    st.session_state.gm_session['scene_counter'] += 1
    st.session_state.gm_session['story_log'].append(scene)

def show_story_log():
    """Display the story log"""
    st.markdown("### 📖 Campaign Story Log")
    
    story_log = st.session_state.gm_session.get('story_log', [])
    
    if not story_log:
        st.info("No scenes have been played yet.")
        return
    
    for i, scene in enumerate(story_log, 1):
        scene_type_emoji = {
            'narrative': '📖',
            'combat': '⚔️', 
            'social': '🗣️',
            'exploration': '🔍',
            'rest': '🏕️',
            'reward': '🎁'
        }
        
        emoji = scene_type_emoji.get(scene.get('type', 'narrative'), '📖')
        
        with st.expander(f"{i}. {emoji} {scene.get('title', 'Scene')}"):
            st.markdown(f"**Type:** {scene.get('type', 'narrative').title()}")
            st.markdown(f"**Description:** {scene.get('description', 'No description')}")
            
            if scene.get('characters_present'):
                st.markdown(f"**Characters Present:** {', '.join(scene['characters_present'])}")
            
            if scene.get('enemies'):
                st.markdown("**Enemies:**")
                for enemy in scene['enemies']:
                    st.markdown(f"• {enemy['name']} (HP: {enemy['hp']}, AC: {enemy['ac']})")
            
            if scene.get('npcs'):
                st.markdown("**NPCs:**")
                for npc in scene['npcs']:
                    st.markdown(f"• {npc['name']} - {npc['role']}")
            
            if scene.get('rewards'):
                st.markdown("**Rewards:**")
                for reward in scene['rewards']:
                    st.markdown(f"• {reward}")

if __name__ == "__main__":
    main()