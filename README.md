# D&D World Generator

Modular Dungeons & Dragons toolkit with a Flask REST backend and Streamlit UI. The backend now exposes JSON endpoints only, while the Streamlit dashboard handles all presentation and management flows.

## Architecture

```
DND_World_Generator/
+-- app.py                 # WSGI entrypoint (create_app)
+-- run_all.py             # Helper to launch backend + Streamlit
+-- streamlit_app.py       # Streamlit frontend
+-- dnd_world/
¦   +-- core/              # Domain primitives (items, enemies, spells, story, combat engine)
¦   +-- utils/             # Shared helpers (dice utilities)
¦   +-- models/            # SQLAlchemy models split by concern
¦   +-- backend/
¦   ¦   +-- __init__.py    # Flask app factory
¦   ¦   +-- routes/        # Feature blueprints (system, characters, combat, story)
¦   +-- database.py        # SQLAlchemy extensions + SQLite pragmas
+-- migrations/            # Alembic migrations (unchanged)
```

During startup the backend seeds two things automatically:
- the standard enemy catalogue (`populate_standard_enemies`)
- a **Default Adventurer** character so new installs have something to inspect immediately

## Getting Started

1. **Set up environment**
   ```bash
   python -m venv .venv
   # Windows
   .\.venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run both services**
   ```bash
   python run_all.py
   ```
   The script launches the Flask API on `http://localhost:5000` and the Streamlit UI on `http://localhost:8501`. Press `Ctrl+C` in the terminal to stop both.

3. **Run components manually (optional)**
   ```bash
   python app.py                  # Flask API only
   streamlit run streamlit_app.py # Streamlit dashboard only
   ```

## Backend API Highlights

- `GET /` – health check used by Streamlit to verify connectivity
- `GET /api/characters` – list characters with key stats
- `POST /create_character` – accepts JSON payload to create a character (auto-adds equipment, spell slots)
- `POST /delete_character/<id>` – remove a character
- `GET /character/<id>/inventory` – JSON snapshot of equipped and carried items
- `POST /character/<id>/equip/<item_id>` / `POST /character/<id>/unequip`
- `POST /character/<id>/add_item` – add items by name (predefined or custom)
- `GET /character/<id>/spells`, `POST /character/<id>/cast_spell`, `POST /character/<id>/long_rest`
- `POST /combat/start`, `GET /combat/<id>/status`, `POST /combat/<id>/end_turn`, `POST /combat/<id>/add_enemy`
- `GET /api/spatial/<id>/state`, `POST /api/spatial/<id>/move`, `POST /api/spatial/<id>/attack`
- `POST /generate_story` – generate narrative beats from the story module

All endpoints respond with JSON and are consumed directly by the Streamlit app.

## Streamlit Frontend

The dashboard caches data aggressively (`st.cache_data`) and invalidates caches whenever mutations occur (equip/unequip, create/delete, etc.). Inventory management now reflects live data from the backend rather than relying on the old HTML templates.

Key sections:
- **Dashboard** – overview metrics, quick links
- **Characters** – create, manage inventory/spells, delete
- **Combat** – launch encounters, monitor status, manage initiative + spatial positions
- **Spells** – inspect spell slots and cast
- **Story Generator** – call into the narrative helper for prompts or generated text

## Database Notes

- The database lives at `instance/dnd_characters.db`.
- Models are defined under `dnd_world/models/` and registered via the app factory.
- Use Flask-Migrate commands against `app.py` if schema changes are needed (existing migration guides still apply).

## Next Steps

- Harden error messaging between Streamlit and the API (surface backend error payloads in the UI).
- Expand combat tooling in the UI to cover the newly exposed spatial endpoints.
- Add automated tests around the modular backend (pytest fixtures using `create_app`).

Happy adventuring! ?????
