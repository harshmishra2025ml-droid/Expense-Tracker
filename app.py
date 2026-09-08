import os
import subprocess
import sys
import time
import webbrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(BASE_DIR, "backend.py")
UI = os.path.join(BASE_DIR, "ui.py")

if __name__ == "__main__":
    print("=" * 60)
    print("💰 EXPENSE TRACKER")
    print("=" * 60)
    print("Starting FastAPI: http://127.0.0.1:8000")
    backend = subprocess.Popen([sys.executable, BACKEND], cwd=BASE_DIR)
    time.sleep(2)
    print("Starting Streamlit: http://localhost:8501")
    streamlit = subprocess.Popen([sys.executable, "-m", "streamlit", "run", UI, "--server.address", "127.0.0.1", "--server.port", "8501", "--server.headless", "true"], cwd=BASE_DIR)
    time.sleep(3)
    webbrowser.open("http://localhost:8501")
    try:
        backend.wait()
    except KeyboardInterrupt:
        pass
    finally:
        for proc in (streamlit, backend):
            if proc.poll() is None:
                proc.terminate()
