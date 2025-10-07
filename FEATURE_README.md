# AI Game Master & Story Generator Integration

## Overview
This update combines the AI Game Master and Story Generator into a unified, seamless interface with database cleanup features to prevent clutter and improve performance.

## What's New

### 1. Unified AI Game Master Interface
The AI Game Master now includes both dynamic campaign management and story generation in one place, accessible through a tabbed interface.

#### Dynamic Campaign Tab (🎭)
- **Scene Generation**: Create random scenes with different types (combat, social, exploration, etc.)
- **Interactive Encounters**: Manage combat, social interactions, and exploration challenges
- **Story Log**: Track your campaign history (auto-trimmed to last 10 scenes)
- **Campaign Controls**: View story log, clean old scenes, reset campaign

#### Story Generator Tab (📚)
- **Custom Prompts**: Generate stories from your own descriptions
- **Pre-built Options**: Random encounters, NPC dialogue, location descriptions, plot hooks
- **Character Context**: Link stories to specific characters for personalized content
- **Environment Settings**: Set the scene in forests, dungeons, cities, etc.
- **Quick Ideas**: One-click prompts for instant inspiration

### 2. Seamless Workflow
Generate a story in the Story Generator tab, then click "Create Scene from Story" to instantly convert it into an active scene in your Dynamic Campaign!

```
Story Generator → Generate Story → Create Scene → Dynamic Campaign
```

### 3. Database Cleanup Features

#### Automatic Cleanup
- **Story Log Trimming**: Keeps only the last 10 scenes to prevent session bloat
- Runs automatically when you click "Clean Story Log"

#### Manual Cleanup (Sidebar)
- **🧹 Clean Database**: Removes old combat sessions (7+ days) and orphaned items
- **📊 Database Stats**: View current database usage statistics

#### What Gets Cleaned
- Inactive combat sessions older than 7 days
- Items not associated with any character
- Old scenes from story log (keeps last 10)

#### What Gets Preserved
- All active combat sessions
- Recent combat sessions (< 7 days old)
- All items equipped or carried by characters
- Current and recent story scenes

## Benefits

### User Experience
- **Simpler Navigation**: One less menu item to worry about
- **Better Workflow**: Generate stories and immediately use them in campaigns
- **Less Clutter**: Database cleanup keeps things running smoothly

### Performance
- **Faster Load Times**: Smaller database means faster queries
- **Better Session Management**: Trimmed story logs reduce memory usage
- **Cleaner UI**: No more scrolling through hundreds of old scenes

### Maintenance
- **Automatic Cleanup**: Story log auto-trims to prevent bloat
- **Manual Control**: Clean database on your schedule
- **Transparency**: View database stats anytime

## How to Use

### Accessing the AI Game Master
1. Navigate to **AI Game Master** in the sidebar (no more separate Story Generator!)
2. Choose your tab:
   - **🎭 Dynamic Campaign** for interactive GMing
   - **📚 Story Generator** for creating story content

### Generating and Using Stories
1. Go to the **Story Generator** tab
2. Select a character (optional), story type, and environment
3. Click **✨ Generate Story**
4. Review the generated content
5. Click **🎲 Create Scene from Story** to add it to your campaign
6. Switch to **Dynamic Campaign** tab to see your new scene!

### Maintaining Your Database
1. Click **🧹 Clean Database** in the sidebar to remove old data
2. Click **📊 Database Stats** to view current database usage
3. In Dynamic Campaign, click **🧹 Clean Story Log** to trim old scenes

### Best Practices
- Clean the database weekly to maintain optimal performance
- Use "Create Scene from Story" to integrate generated content
- Review Database Stats periodically to monitor growth
- Clean story log after long sessions to free up memory

## Technical Details

### Files Changed
- `streamlit_app.py`: Unified interface, removed old Story Generator page
- `dnd_world/database.py`: Added cleanup functions
- `dnd_world/backend/routes/system.py`: Added cleanup API endpoints

### New Functions
- `cleanup_old_combat_sessions(days_old=7)`: Clean old combats
- `cleanup_orphaned_items()`: Remove unassociated items
- `get_database_stats()`: Get database statistics
- `create_scene_from_story()`: Convert story to active scene
- `clean_story_log()`: Trim story log to last 10 scenes

### New API Endpoints
- `POST /database/cleanup`: Clean old data
- `GET /database/stats`: Get database statistics

### Database Cleanup Criteria
- **Combat Sessions**: Removes inactive combats older than 7 days
- **Items**: Removes items with no character_id
- **Story Log**: Keeps only last 10 scenes in session state

## Troubleshooting

### Story Generator Tab Not Working
- Ensure Flask backend is running on port 5000
- Check that story generation endpoint is accessible
- Verify character data is loading properly

### Database Cleanup Not Working
- Ensure Flask backend is running
- Check database file permissions
- Verify SQLite database is not locked

### Scene Creation Fails
- Ensure you've generated a story first
- Check that GM session is initialized
- Verify characters are loaded

### Story Log Too Large
- Click "Clean Story Log" to trim to last 10 scenes
- Consider resetting campaign if cleanup isn't enough
- Story log is stored in session state, not database

## Migration Notes

### For Existing Users
- Your existing campaigns and characters are safe
- Old Story Generator bookmark/links will no longer work
- Navigate to AI Game Master instead
- All Story Generator features are in the second tab
- First cleanup may remove old data - this is normal

### Data Safety
- Cleanup only removes inactive/orphaned data
- Active combats are never removed
- Character items are never removed
- Database backup recommended before first cleanup

## Support
If you encounter issues:
1. Check that Flask backend is running
2. Try clicking "Refresh Data" in sidebar
3. Clear cache with "Clear All Cache" (Performance Debug section)
4. Check database stats to verify cleanup worked
5. Restart both Flask and Streamlit if problems persist

## Future Enhancements
- Configurable cleanup periods (not just 7 days)
- Export/import story logs
- More advanced scene templates
- Integration with character progression
- Combat encounter balancing
