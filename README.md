# 🐉 D&D World Generator v2.0

A modernized, modular Dungeons & Dragons character creation and campaign management system with a clean API backend and Streamlit frontend.

## ✨ Features

- **Character Management**: Create, manage, and level up D&D 5e characters
- **Smart Inventory**: Comprehensive item and equipment management system  
- **AI Story Generation**: LLM-powered story continuation and encounter generation
- **Combat System**: Turn-based combat tracking with initiative and actions
- **Name Generation**: Race-appropriate name generation for characters
- **Modern Architecture**: Clean separation between API and frontend

## 🏗️ Architecture

The codebase has been completely refactored into a modular structure:

```
dnd_world/
├── models/          # Database models (Character, Item, Combat, Enemy)
├── core/            # Business logic (CharacterCreator, EquipmentManager, StorySystem)
├── api/             # REST API routes (Flask blueprints)
├── utils/           # Utilities (dice rolling, database management)
├── frontend/        # Streamlit UI components
└── config.py        # Configuration management
```

## 🚀 Quick Start

### Option 1: Interactive Menu
```bash
python main.py
```

### Option 2: Direct API Server
```bash
python run_api.py
```

### Option 3: Individual Components
```bash
# Start API server
python -m dnd_world.app

# Start Streamlit frontend (in another terminal)
streamlit run dnd_world/frontend/streamlit_app.py
```

## 📦 Installation

1. **Clone the repository**:
```bash
git clone https://github.com/NusretSalli/DND_World_Generator.git
cd DND_World_Generator
```

2. **Create virtual environment**:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Run the application**:
```bash
python main.py
```

## 🔧 Configuration

Configure the application using environment variables:

```bash
# Database
export DATABASE_URL="sqlite:///my_dnd_world.db"

# API Server
export API_HOST="0.0.0.0"
export API_PORT="5000"

# Story Generation
export STORY_MODEL_NAME="distilgpt2"
export ENABLE_AI_STORY_GENERATION="true"

# Environment
export FLASK_ENV="development"  # or "production"
```

## 📡 API Endpoints

The Flask API provides RESTful endpoints:

- `GET /api/health` - Health check
- `GET /api/characters` - List all characters
- `POST /api/characters` - Create new character
- `GET /api/characters/{id}` - Get character details
- `POST /api/story/generate` - Generate story content
- `POST /api/combat/start` - Start combat encounter

## 🎲 Core Systems

### Character Creation
```python
from dnd_world.core.character_creation import CharacterCreator

character = CharacterCreator.create_character(
    name="Aragorn",
    race="human", 
    character_class="ranger",
    gender="male"
)
```

### Equipment Management
```python
from dnd_world.core.equipment_manager import EquipmentManager

# Add items to character
EquipmentManager.add_template_item_to_character(character, "Longsword")
EquipmentManager.equip_item_to_character(character, item_id, "main_hand")
```

### Story Generation
```python
from dnd_world.core.story_generator import StorySystem

story_system = StorySystem()
story = story_system.generate_story_continuation(
    "The party enters a dark forest...",
    character_context="Level 3 Human Ranger"
)
```

## 🧪 Development

### Database Management
```bash
# Setup fresh database
python -c "from dnd_world.app import create_app, setup_database; app = create_app(); setup_database(app)"

# For migrations (if using Flask-Migrate)
export FLASK_APP=dnd_world.app
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

## 📈 Improvements in v2.0

✅ **Modular Architecture**: Clean separation of concerns  
✅ **API-First Design**: RESTful backend, flexible frontend  
✅ **Better Error Handling**: Comprehensive error management  
✅ **Configuration Management**: Environment-based config  
✅ **Streamlined Dependencies**: Removed unnecessary packages  
✅ **Type Safety**: Better code organization and imports  
✅ **Extensible Design**: Easy to add new features  

## 🔮 Roadmap

- [ ] Add comprehensive test suite
- [ ] Implement spell system management
- [ ] Add multi-user support with authentication
- [ ] Create character sheet export (PDF)
- [ ] Add campaign management features
- [ ] Implement real-time combat via WebSockets
- [ ] Add character art generation integration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- Built with Flask, Streamlit, and SQLAlchemy
- Uses the `pynames` library for character name generation
- AI story generation powered by Hugging Face Transformers
- Inspired by D&D 5th Edition rules