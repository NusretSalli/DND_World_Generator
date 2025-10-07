# Changes: AI Game Master & Story Generator Integration with Database Cleanup

## Summary
Combined the AI Game Master and Story Generator into a unified interface with database cleanup features to prevent clutter.

## Key Changes

### 1. Unified Interface (streamlit_app.py)
- **Merged Pages**: Combined "AI Game Master" and "Story Generator" into one page
- **Tabbed Interface**: Added two tabs:
  - 🎭 **Dynamic Campaign**: Original AI GM functionality with scene generation, combat, social encounters
  - 📚 **Story Generator**: Integrated story generation tools from the old Story Generator page
- **Cross-Feature Integration**: Added "Create Scene from Story" button to convert generated stories into active campaign scenes
- **Updated Navigation**: Removed separate "Story Generator" menu item

### 2. Database Cleanup Features

#### Backend (dnd_world/database.py)
Added three new utility functions:
- `cleanup_old_combat_sessions(days_old=7)`: Removes inactive combat sessions older than specified days
- `cleanup_orphaned_items()`: Removes items not associated with any character
- `get_database_stats()`: Provides database usage statistics

#### API Endpoints (dnd_world/backend/routes/system.py)
Added two new endpoints:
- `POST /database/cleanup`: Clean up old combat sessions and orphaned items
- `GET /database/stats`: Get database statistics (characters, combats, items, users)

#### UI (streamlit_app.py)
Added database maintenance controls in sidebar:
- **🧹 Clean Database**: Removes old combat sessions (7+ days old) and orphaned items
- **📊 Database Stats**: Shows current database statistics
- **🧹 Clean Story Log**: Keeps only last 10 scenes in GM story log (prevents session state bloat)

## Benefits
1. **Simplified Navigation**: One less menu item, more intuitive workflow
2. **Seamless Integration**: Generate stories and immediately use them in campaigns
3. **Database Hygiene**: Automated cleanup prevents database growth from old/unused data
4. **Better Performance**: Keeping story logs trimmed improves session state performance

## Usage

### AI Game Master & Story Generator
1. Navigate to "AI Game Master" in the sidebar
2. Use **Dynamic Campaign** tab for interactive GMing
3. Use **Story Generator** tab for generating story content
4. Click "Create Scene from Story" to add generated content to your active campaign

### Database Maintenance
1. Click **🧹 Clean Database** in sidebar to remove old data
2. Click **📊 Database Stats** to view current database usage
3. In Dynamic Campaign, click **🧹 Clean Story Log** to trim old scenes

## Technical Details
- Story log cleanup keeps last 10 scenes to balance history with performance
- Combat cleanup only removes inactive combats older than 7 days
- All cleanup operations are safe and preserve active/recent data
- Database operations use proper SQLAlchemy transactions
