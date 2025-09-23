"""
D&D World Generator Launcher
Desktop application launcher for the D&D campaign management system
"""

import subprocess
import threading
import time
import webbrowser
import os
import sys
from pathlib import Path

def start_flask():
    """Start the Flask backend server"""
    try:
        print("🔧 Starting Flask backend...")
        # Change to the script directory
        script_dir = Path(__file__).parent
        os.chdir(script_dir)
        
        # Start Flask app
        subprocess.run([sys.executable, "app.py"], check=True)
    except Exception as e:
        print(f"❌ Error starting Flask: {e}")

def start_streamlit():
    """Start the Streamlit frontend"""
    try:
        print("🎨 Starting Streamlit frontend...")
        time.sleep(3)  # Give Flask time to start
        
        # Change to the script directory
        script_dir = Path(__file__).parent
        os.chdir(script_dir)
        
        # Start Streamlit app
        subprocess.run([sys.executable, "-m", "streamlit", "run", "streamlit_app.py", "--server.headless", "true"], check=True)
    except Exception as e:
        print(f"❌ Error starting Streamlit: {e}")

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'flask',
        'streamlit', 
        'requests',
        'plotly'
    ]
    
    # Special handling for SQLAlchemy due to Python 3.13 compatibility issues
    sqlalchemy_packages = ['sqlalchemy', 'flask-sqlalchemy', 'flask-migrate']
    
    missing_packages = []
    sqlalchemy_error = False
    
    # Check basic packages first
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    # Check SQLAlchemy with error handling
    try:
        import sqlalchemy
        import flask_sqlalchemy
        import flask_migrate
        print("✅ SQLAlchemy packages are available")
    except ImportError as e:
        missing_packages.extend(sqlalchemy_packages)
        print(f"📦 SQLAlchemy packages need installation")
    except Exception as e:
        print(f"⚠️  SQLAlchemy compatibility issue detected: {str(e)[:100]}...")
        print("🔧 This is likely a Python 3.13 + SQLAlchemy compatibility issue")
        sqlalchemy_error = True
    
    # Install missing packages
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("📦 Installing missing packages...")
        
        try:
            # Install with specific versions for Python 3.13 compatibility
            install_commands = []
            
            if any('sqlalchemy' in pkg for pkg in missing_packages):
                print("🔧 Installing SQLAlchemy with Python 3.13 compatibility...")
                install_commands.extend([
                    [sys.executable, "-m", "pip", "install", "sqlalchemy>=2.0.23"],
                    [sys.executable, "-m", "pip", "install", "flask-sqlalchemy>=3.1.1"],
                    [sys.executable, "-m", "pip", "install", "flask-migrate>=4.0.5"]
                ])
                # Remove sqlalchemy packages from missing_packages to avoid double installation
                missing_packages = [pkg for pkg in missing_packages if 'sqlalchemy' not in pkg and 'migrate' not in pkg]
            
            if missing_packages:
                install_commands.append([sys.executable, "-m", "pip", "install"] + missing_packages)
            
            for cmd in install_commands:
                subprocess.check_call(cmd)
            
            print("✅ All packages installed successfully!")
            
        except subprocess.CalledProcessError:
            print("❌ Failed to install packages. Please install manually:")
            print(f"   pip install {' '.join(missing_packages)}")
            if sqlalchemy_error:
                print("   pip install 'sqlalchemy>=2.0.23' 'flask-sqlalchemy>=3.1.1' 'flask-migrate>=4.0.5'")
            return False
    
    # If there was a SQLAlchemy error but packages are installed, give advice
    if sqlalchemy_error and not missing_packages:
        print("🔧 SQLAlchemy compatibility issue detected!")
        print("💡 Possible solutions:")
        print("   1. Downgrade to Python 3.11 or 3.12")
        print("   2. Update SQLAlchemy: pip install --upgrade 'sqlalchemy>=2.0.23'")
        print("   3. Use Python 3.12 virtual environment")
        print("⚠️  Continuing anyway - Flask app may still work...")
        
        # Ask user if they want to continue
        try:
            response = input("Continue anyway? (y/n): ").lower().strip()
            if response != 'y':
                return False
        except KeyboardInterrupt:
            return False
    
    return True

def main():
    """Main launcher function"""
    print("🐉 D&D World Generator - Desktop Launcher")
    print("=" * 50)
    
    # Check Python version
    python_version = sys.version_info
    print(f"🐍 Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version >= (3, 13):
        print("⚠️  WARNING: Python 3.13+ detected!")
        print("   SQLAlchemy may have compatibility issues with Python 3.13")
        print("   If you encounter errors, consider using Python 3.11 or 3.12")
        print()
    
    # Check dependencies
    if not check_dependencies():
        print("\n💡 Alternative solutions:")
        print("1. Create a Python 3.12 virtual environment:")
        print("   conda create -n dnd python=3.12")
        print("   conda activate dnd")
        print("   pip install -r requirements.txt")
        print()
        print("2. Or try running Flask directly:")
        print("   python app.py")
        print("   (then open http://localhost:5000 in browser)")
        print()
        input("Press Enter to exit...")
        return
    
    print("🚀 Starting application components...")
    
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()
    
    # Start Streamlit in a separate thread
    streamlit_thread = threading.Thread(target=start_streamlit, daemon=True)
    streamlit_thread.start()
    
    # Wait a bit for servers to start
    print("⏳ Waiting for servers to start...")
    time.sleep(8)
    
    # Open browser to Streamlit app
    print("🌐 Opening application in browser...")
    webbrowser.open("http://localhost:8501")
    
    print("\n" + "=" * 50)
    print("🎭 D&D World Generator is now running!")
    print("📱 Streamlit UI: http://localhost:8501")
    print("🔧 Flask Backend: http://localhost:5000")
    print("=" * 50)
    print("\n💡 Instructions:")
    print("1. Use the Streamlit interface for modern UI")
    print("2. Flask backend handles all data operations")
    print("3. Both servers must be running for full functionality")
    print("\n⚠️  To stop the application, close this window or press Ctrl+C")
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down D&D World Generator...")
        print("👋 Goodbye!")

if __name__ == "__main__":
    main()