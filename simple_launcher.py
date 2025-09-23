"""
Simple D&D World Generator Launcher
Alternative launcher that bypasses dependency checking for Python 3.13 compatibility
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

def install_streamlit_packages():
    """Install Streamlit-specific packages only"""
    streamlit_packages = [
        'streamlit>=1.28.0',
        'plotly>=5.17.0',
        'requests>=2.31.0',
        'pandas>=2.1.0'
    ]
    
    print("📦 Installing Streamlit packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + streamlit_packages)
        print("✅ Streamlit packages installed!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install Streamlit packages")
        return False

def main():
    """Main launcher function"""
    print("🐉 D&D World Generator - Simple Launcher")
    print("=" * 55)
    
    # Check Python version
    python_version = sys.version_info
    print(f"🐍 Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version >= (3, 13):
        print("⚠️  Python 3.13+ detected - using compatibility mode")
    
    # Quick check for Streamlit
    try:
        import streamlit
        print("✅ Streamlit is available")
    except ImportError:
        print("📦 Streamlit not found, installing...")
        if not install_streamlit_packages():
            print("❌ Could not install Streamlit packages")
            print("💡 Try manually: pip install streamlit plotly requests pandas")
            input("Press Enter to exit...")
            return
    
    print("🚀 Starting application components...")
    print("   Note: Flask will start first, then Streamlit after 3 seconds")
    print()
    
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
    
    print("\n" + "=" * 55)
    print("🎭 D&D World Generator is now running!")
    print("📱 Streamlit UI: http://localhost:8501")
    print("🔧 Flask Backend: http://localhost:5000")
    print("=" * 55)
    print("\n💡 Instructions:")
    print("1. Use the Streamlit interface for modern UI")
    print("2. Flask backend handles all data operations")
    print("3. If Streamlit fails, use Flask directly at localhost:5000")
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