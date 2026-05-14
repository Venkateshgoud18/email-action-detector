import os
from pathlib import Path


base_dir = Path(__file__).resolve().parent
env_path = base_dir / ".env"

print(f"Project folder: {base_dir}")
print(f".env exists: {env_path.exists()}")

if not env_path.exists():
    print("Create it with: cp .env.example .env")
    raise SystemExit(1)

keys = {}
for line in env_path.read_text(encoding="utf-8").splitlines():
    clean_line = line.strip()
    if not clean_line or clean_line.startswith("#") or "=" not in clean_line:
        continue
    key, value = clean_line.split("=", 1)
    keys[key.strip()] = value.strip()

api_key = keys.get("OPENAI_API_KEY", "")
model = keys.get("OPENAI_MODEL", "")
jwt_secret = keys.get("JWT_SECRET", "")
auth_username = keys.get("AUTH_USERNAME", "")
auth_password = keys.get("AUTH_PASSWORD", "")

print(f"OPENAI_API_KEY present: {bool(api_key)}")
print(f"OPENAI_API_KEY starts with sk-: {api_key.startswith('sk-')}")
print(f"OPENAI_API_KEY length: {len(api_key)}")
print(f"OPENAI_MODEL: {model or 'not set'}")
print(f"JWT_SECRET present: {bool(jwt_secret)}")
print(f"AUTH_USERNAME: {auth_username or 'not set'}")
print(f"AUTH_PASSWORD present: {bool(auth_password)}")

if not api_key or api_key == "your_new_api_key_here":
    print("Fix .env: replace the placeholder with your actual key.")
    raise SystemExit(1)

print("Setup looks ready. Restart server.py after any .env change.")
