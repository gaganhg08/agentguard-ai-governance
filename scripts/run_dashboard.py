import subprocess
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if __name__ == "__main__":
    app_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "app.py")
    subprocess.run([sys.executable, "-m", "streamlit", "run", app_path])
