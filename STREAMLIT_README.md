# 🐉 D&D World Generator - Streamlit Frontend

A modern, interactive frontend for the D&D World Generator built with Streamlit, providing an enhanced user experience for campaign management.

## 🚀 Quick Start

### Option 1: Desktop Launcher (Recommended)
```bash
python launcher.py
```
This will automatically:
- Install missing dependencies
- Start both Flask backend and Streamlit frontend
- Open the application in your browser

### Option 2: Manual Setup
1. **Install dependencies:**
   ```bash
   pip install -r requirements_streamlit.txt
   ```

2. **Start Flask backend (in one terminal):**
   ```bash
   python app.py
   ```

3. **Start Streamlit frontend (in another terminal):**
   ```bash
   streamlit run streamlit_app.py
   ```

4. **Open your browser to:**
   - Streamlit UI: http://localhost:8501
   - Flask Backend: http://localhost:5000

## 🎯 Features

### 🏠 Dashboard
- **Party Overview**: Visual health status charts
- **Quick Statistics**: Character count, levels, status
- **Activity Tracking**: Recent campaign events

### 👤 Character Management
- **Enhanced Character Creation**: 
  - Multiple ability score generation methods
  - Racial bonus integration
  - Real-time modifier calculation
- **Character Overview**: Visual character cards with all stats
- **Quick Actions**: Direct access to spells, inventory, combat

### ⚔️ Combat System
- **Quick Combat Setup**: Easy combatant selection
- **Initiative Tracking**: Visual turn order management
- **Spatial Combat Grid**: Interactive grid with combatant positions
- **Health Visualization**: Color-coded health status

### 📜 Spell Management
- **Visual Spell Slots**: Interactive slot tracking
- **Spell Library**: Organized by level and class
- **Long Rest Recovery**: One-click spell slot restoration
- **Casting Integration**: Direct spell slot consumption

### 🎲 Advanced Dice Roller
- **Preset Rolls**: Common D&D rolls (advantage, damage, etc.)
- **Custom Notation**: Full dice notation support
- **Multiple Rolls**: Roll the same dice multiple times
- **Visual Results**: Large, clear result display with statistics

### 📚 Story Generator
- **Dynamic Content**: Character-focused story generation
- **Environment Integration**: Location-based content
- **Multiple Types**: Encounters, NPCs, plot hooks
- **Campaign Stats**: Party information integration

## 🛠️ Technical Architecture

### Frontend (Streamlit)
- **Framework**: Streamlit 1.28+
- **Visualizations**: Plotly for interactive charts
- **Styling**: Custom CSS with D&D theme
- **State Management**: Session state for user interactions

### Backend Integration
- **API Communication**: RESTful integration with Flask
- **Real-time Updates**: Automatic data refresh
- **Error Handling**: Graceful degradation on connection issues
- **Caching**: Smart data caching for performance

### Desktop Deployment
- **Launcher Script**: Automated setup and startup
- **PyInstaller Ready**: Package as standalone executable
- **Cross-platform**: Windows, macOS, Linux support

## 📁 File Structure

```
DND_World_Generator/
├── streamlit_app.py           # Main Streamlit application
├── launcher.py                # Desktop launcher script
├── streamlit_config.py        # Configuration settings
├── requirements_streamlit.txt # Streamlit dependencies
├── app.py                     # Flask backend (existing)
├── templates/                 # Flask templates (existing)
├── static/                    # Static assets (existing)
└── ... (other existing files)
```

## ⚙️ Configuration

Edit `streamlit_config.py` to customize:

```python
# UI Settings
APP_TITLE = "🐉 Your Campaign Name"
LAYOUT = "wide"  # or "centered"

# Theme Colors
PRIMARY_COLOR = "#4dabf7"
BACKGROUND_COLOR = "#0f1419"

# Feature Flags
ENABLE_SPATIAL_COMBAT = True
ENABLE_STORY_GENERATOR = True

# Timeouts
API_TIMEOUT_LONG = 15  # seconds
```

## 🎨 User Interface

### Navigation
- **Sidebar Navigation**: Easy switching between features
- **Connection Status**: Real-time Flask backend status
- **Quick Actions**: Common tasks accessible from anywhere

### Visual Elements
- **Dark Theme**: Optimized for long gaming sessions
- **Responsive Layout**: Works on desktop and tablets
- **Interactive Charts**: Click and hover for details
- **Status Indicators**: Color-coded health, spell slots, etc.

### Accessibility
- **Clear Typography**: Easy to read in low light
- **Consistent Navigation**: Intuitive user flow
- **Error Messages**: Helpful error descriptions
- **Loading States**: Visual feedback for operations

## 🔧 Development

### Running in Development Mode
1. **Enable debug mode** in `streamlit_config.py`:
   ```python
   DEBUG_MODE = True
   SHOW_API_RESPONSES = True
   ```

2. **Start with auto-reload**:
   ```bash
   streamlit run streamlit_app.py --server.runOnSave true
   ```

### Adding New Features
1. **Create new page function** in `streamlit_app.py`
2. **Add navigation option** in sidebar
3. **Update routing** in main() function
4. **Add configuration** in `streamlit_config.py`

### API Integration
All Flask API calls use the `requests` library:
```python
def get_characters():
    try:
        response = requests.get(f"{FLASK_URL}/api/characters", timeout=5)
        return response.json() if response.status_code == 200 else []
    except:
        return []
```

## 🚀 Deployment Options

### Desktop Application
Create a standalone executable:
```bash
pip install pyinstaller
pyinstaller --onefile --windowed launcher.py
```

### Web Deployment
Deploy to Streamlit Cloud, Heroku, or other platforms:
1. Push code to GitHub
2. Connect to Streamlit Cloud
3. Deploy with automatic Flask backend

### Local Network
Run on local network for multiplayer:
```bash
streamlit run streamlit_app.py --server.address 0.0.0.0
```

## 🎮 Usage Guide

### First Time Setup
1. **Run the launcher**: `python launcher.py`
2. **Create characters**: Use the Characters tab
3. **Start playing**: All features are now available

### Daily Workflow
1. **Open application**: Double-click launcher or use command line
2. **Check dashboard**: Review party status
3. **Manage sessions**: Use combat, spells, and story features
4. **Track progress**: All data automatically saves to Flask backend

### Tips for DMs
- **Use story generator** for quick inspiration
- **Spatial combat** for tactical encounters
- **Dashboard overview** to track party health
- **Quick dice rolls** for rapid gameplay

### Tips for Players
- **Character sheet** always accessible
- **Spell management** with visual slot tracking
- **Inventory integration** through Flask interface
- **Dice roller** for all your rolling needs

## 🔍 Troubleshooting

### Common Issues

**"Flask backend not running"**
- Ensure `python app.py` is running first
- Check if port 5000 is available
- Verify Flask dependencies are installed

**"Streamlit won't start"**
- Install requirements: `pip install -r requirements_streamlit.txt`
- Check Python version (3.8+ recommended)
- Try: `python -m streamlit run streamlit_app.py`

**"Characters not loading"**
- Verify Flask backend is accessible at http://localhost:5000
- Check database file exists: `instance/dnd_characters.db`
- Run Flask migrations: `flask db upgrade`

**"Dice roller not working"**
- Check Flask dice_utils.py is working
- Verify requests to `/roll_dice` endpoint
- Try simple notation like "1d20"

### Debug Mode
Enable in `streamlit_config.py`:
```python
DEBUG_MODE = True
SHOW_API_RESPONSES = True
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/new-feature`
3. **Add new functionality** following existing patterns
4. **Test thoroughly** with Flask backend
5. **Submit pull request**

## 📝 License

This project maintains the same license as the original D&D World Generator.

---

**🎭 Happy Gaming!** 
*May your rolls be high and your adventures epic!*