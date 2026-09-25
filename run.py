"""Launch both processes for local development:

- FastAPI backend  -> http://127.0.0.1:8000  (API docs at /docs)
- Streamlit frontend -> http://127.0.0.1:8501

Pure Python. Press Ctrl+C once to stop both.
"""
import os
import subprocess
import sys
import time
import urllib.request
import webbrowser

BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8000
FRONTEND_PORT = 8501
FRONTEND_URL = f"http://{BACKEND_HOST}:{FRONTEND_PORT}"


def wait_healthy(url: str, timeout: float = 30.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False


def main() -> int:
    py = sys.executable
    env = {**os.environ, "API_BASE_URL": f"http://{BACKEND_HOST}:{BACKEND_PORT}"}

    backend = subprocess.Popen(
        [py, "-m", "uvicorn", "app.main:app",
         "--host", BACKEND_HOST, "--port", str(BACKEND_PORT), "--reload"],
        env=env,
    )
    # Give the API a moment to bind before the UI starts calling it.
    time.sleep(2)
    frontend = subprocess.Popen(
        [py, "-m", "streamlit", "run", "streamlit_app.py",
         "--server.port", str(FRONTEND_PORT), "--server.headless", "true"],
        env=env,
    )

    print(f"\n  Backend API : http://{BACKEND_HOST}:{BACKEND_PORT}  (docs: /docs)")
    print(f"  Frontend UI : {FRONTEND_URL}\n")

    if wait_healthy(f"{FRONTEND_URL}/_stcore/health"):
        webbrowser.open(FRONTEND_URL)
    else:
        print(f"  (open {FRONTEND_URL} manually once it finishes starting)")

    procs = [backend, frontend]
    try:
        while all(p.poll() is None for p in procs):
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        for p in procs:
            if p.poll() is None:
                p.terminate()
        for p in procs:
            try:
                p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                p.kill()
    return 0


if __name__ == "__main__":
    sys.exit(main())
