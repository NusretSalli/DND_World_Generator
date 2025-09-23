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

@st.cache_data(ttl=10, show_spinner=False)  # Cache for 10 seconds
def get_characters():
    """Fetch characters from Flask backend - cached"""
    try:
        response = requests.get(f"{FLASK_URL}/api/characters", timeout=3)
        return response.json() if response.status_code == 200 else []
    except:
        return []

# Manual cache invalidation function
def invalidate_character_cache():
    """Force refresh character data"""
    get_characters.clear()
    if 'characters_last_update' in st.session_state:
        del st.session_state.characters_last_update

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

# Initialize session state
if 'selected_character' not in st.session_state:
    st.session_state.selected_character = None
if 'last_roll' not in st.session_state:
    st.session_state.last_roll = None
if 'generated_scores' not in st.session_state:
    st.session_state.generated_scores = None

# Sidebar navigation
st.sidebar.markdown("# 🐉 D&D Manager")
st.sidebar.markdown("---")

# Check Flask connection
if not check_flask_connection():
    st.sidebar.error("⚠️ Flask backend not running!")
    st.sidebar.info("Please start the Flask app:\n```python app.py```")
else:
    st.sidebar.success("✅ Connected to Flask backend")

# Navigation menu
page = st.sidebar.selectbox(
    "Navigate to:",
    ["🏠 Dashboard", "👤 Characters", "⚔️ Combat", "📜 Spells", "🎲 Dice Roller", "📚 Story Generator"],
    key="navigation"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Quick Actions")

# Quick character count
characters = get_characters()
st.sidebar.metric("Total Characters", len(characters))

if characters:
    alive_count = sum(1 for c in characters if c.get('current_hp', 0) > 0)
    st.sidebar.metric("Characters Alive", alive_count)

# Main content area
def show_dashboard():
    """Dashboard page"""
    st.markdown('<div class="main-header"><h1>🐉 D&D World Generator</h1><p>Enhanced Campaign Management System</p></div>', unsafe_allow_html=True)
    
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
                st.write(f"**Race:** {char['race'].title()}")
                st.write(f"**Class:** {char['character_class'].title()}")
                st.write(f"**Level:** {char['level']}")
                st.write(f"**Gender:** {char['gender'].title()}")
                st.write(f"**Experience:** {char.get('experience', 0)} XP")
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
                
                if st.button("📜 View Spells", key=f"spells_{char['id']}"):
                    st.session_state.selected_character = char['id']
                    st.session_state.navigation = "📜 Spells"
                    st.rerun()
                
                if st.button("🎒 Inventory", key=f"inventory_{char['id']}"):
                    st.info("Opening Flask inventory page...")
                    st.markdown(f"[Open Inventory]({FLASK_URL}/character/{char['id']}/inventory)")
                
                if st.button("⚔️ Combat", key=f"combat_{char['id']}"):
                    st.session_state.selected_character = char['id']
                    st.session_state.navigation = "⚔️ Combat"
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
                            st.session_state.generated_scores = None  # Clear generated scores
                            time.sleep(1)
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
            
            try:
                response = requests.get(f"{FLASK_URL}/combat/{st.session_state.combat_id}/status", timeout=5)
                
                if response.status_code == 200:
                    combat = response.json()
                    
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
                    
                    # Combat actions
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("⚔️ Attack"):
                            st.info("Advanced attack system available in Flask interface")
                    
                    with col2:
                        if st.button("🏃 End Turn"):
                            try:
                                requests.post(f"{FLASK_URL}/combat/{st.session_state.combat_id}/end_turn", timeout=5)
                                st.rerun()
                            except:
                                st.error("Failed to end turn")
                    
                    with col3:
                        if st.button("🏁 End Combat"):
                            del st.session_state.combat_id
                            st.success("Combat ended!")
                            st.rerun()
                else:
                    st.error("Failed to load combat status")
                    if st.button("Clear Combat"):
                        del st.session_state.combat_id
                        st.rerun()
                        
            except Exception as e:
                st.error(f"Error loading combat: {str(e)}")
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
                result = roll_dice(dice_notation)
                if result:
                    st.session_state.last_roll = result
                else:
                    # Fallback for unsupported notation
                    simple_notation = dice_notation.split('k')[0].split('d')[0] + 'd' + dice_notation.split('d')[1].split('k')[0].split('d')[0]
                    if '+' in dice_notation:
                        simple_notation += '+' + dice_notation.split('+')[1]
                    result = roll_dice(simple_notation)
                    if result:
                        st.session_state.last_roll = result
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
                result = roll_dice(custom_dice)
                if result:
                    st.session_state.last_roll = result
                else:
                    st.error("Invalid dice notation or connection error")
        
        with col2b:
            if st.button("🔄 Roll Multiple", use_container_width=True):
                results = []
                for _ in range(5):
                    result = roll_dice(custom_dice)
                    if result:
                        results.append(result['total'])
                
                if results:
                    st.session_state.multiple_rolls = results
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
    
    # Page routing
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

if __name__ == "__main__":
    main()