"""
Seed data script — creates a sample .env if not present and validates the setup.
Run: python scripts/seed_data.py
"""
import os
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
BACKEND = ROOT / "backend"
ENV_FILE = BACKEND / ".env"
ENV_EXAMPLE = BACKEND / ".env.example"


def check_env():
    if not ENV_FILE.exists():
        if ENV_EXAMPLE.exists():
            import shutil
            shutil.copy(ENV_EXAMPLE, ENV_FILE)
            print(f"[OK] Created {ENV_FILE} from .env.example")
        else:
            print("[ERROR] backend/.env.example not found")
            sys.exit(1)
    else:
        print(f"[OK] {ENV_FILE} already exists")


def check_python():
    major, minor = sys.version_info[:2]
    if major < 3 or minor < 11:
        print(f"[ERROR] Python 3.11+ required, got {major}.{minor}")
        sys.exit(1)
    print(f"[OK] Python {major}.{minor}")


def check_node():
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        version = result.stdout.strip()
        print(f"[OK] Node.js {version}")
    except FileNotFoundError:
        print("[WARN] Node.js not found — frontend setup will fail")


def check_dependencies():
    req_file = BACKEND / "requirements.txt"
    if not req_file.exists():
        print("[ERROR] backend/requirements.txt not found")
        sys.exit(1)
    print("[OK] requirements.txt found")

    pkg_file = ROOT / "frontend" / "package.json"
    if not pkg_file.exists():
        print("[ERROR] frontend/package.json not found")
        sys.exit(1)
    print("[OK] frontend/package.json found")


def print_next_steps():
    print("\n" + "="*60)
    print("Setup complete! Next steps:")
    print("="*60)
    print()
    print("  1. Install Python dependencies:")
    print("     cd backend && pip install -r requirements.txt")
    print()
    print("  2. Install Node dependencies:")
    print("     cd frontend && npm install")
    print()
    print("  3. Start the backend (terminal 1):")
    print("     cd backend && uvicorn app.main:app --reload")
    print()
    print("  4. Start the frontend (terminal 2):")
    print("     cd frontend && npm run dev")
    print()
    print("  5. Open http://localhost:5173/login")
    print("     Sign in with any demo role (no Azure credentials needed)")
    print()
    print("  Optional: Configure Azure credentials in backend/.env")
    print("  to use live Microsoft Graph data instead of mock data.")
    print()


if __name__ == "__main__":
    print("IPA Corporate — Setup Validator")
    print("-"*40)
    check_python()
    check_node()
    check_dependencies()
    check_env()
    print_next_steps()
