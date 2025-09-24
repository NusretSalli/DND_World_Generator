"""
Main Entry Point for D&D World Generator
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main entry point with menu for different modes."""
    print("🐉 D&D World Generator v2.0")
    print("=" * 40)
    print("1. Start Flask API Server")
    print("2. Start Streamlit Frontend")
    print("3. Run Database Setup Only")
    print("4. Exit")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == "1":
        start_flask_api()
    elif choice == "2":
        start_streamlit()
    elif choice == "3":
        setup_database_only()
    elif choice == "4":
        print("Goodbye!")
        sys.exit(0)
    else:
        print("Invalid choice. Please try again.")
        main()

def start_flask_api():
    """Start the Flask API server."""
    print("Starting Flask API server...")
    from dnd_world.app import create_app, setup_database
    
    app = create_app()
    setup_database(app)
    
    print("Flask API server starting on http://localhost:5000")
    app.run(debug=True, port=5000)

def start_streamlit():
    """Start the Streamlit frontend."""
    print("Starting Streamlit frontend...")
    print("Make sure Flask API is running on port 5000!")
    
    import subprocess
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", 
        "dnd_world/frontend/streamlit_app.py",
        "--server.port", "8501"
    ])

def setup_database_only():
    """Setup database tables only."""
    print("Setting up database...")
    from dnd_world.app import create_app, setup_database
    
    app = create_app()
    setup_database(app)
    print("Database setup complete!")

if __name__ == "__main__":
    main()