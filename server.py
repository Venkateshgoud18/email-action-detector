import json
import os
import base64
import hashlib
import hmac
import time
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from ai_models import get_ai_model


BASE_DIR = Path(__file__).resolve().parent
HOST = "127.0.0.1"
PORT = 8001
TOKEN_TTL_SECONDS = 60 * 60
USERS_FILE = BASE_DIR / "users.json"

def get_users():
    if not USERS_FILE.exists():
        expected_username = os.getenv("AUTH_USERNAME", "demo")
        expected_password = os.getenv("AUTH_PASSWORD", "demo123")
        hashed_password = hashlib.sha256(expected_password.encode()).hexdigest()
        users = {expected_username: hashed_password}
        USERS_FILE.write_text(json.dumps(users))
        return users
    return json.loads(USERS_FILE.read_text())

def save_users(users):
    USERS_FILE.write_text(json.dumps(users, indent=2))


def load_env_file():
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        print(f"No .env file found at {env_path}")
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        clean_line = line.strip()
        if not clean_line or clean_line.startswith("#") or "=" not in clean_line:
            continue

        key, value = clean_line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

    if os.getenv("OPENAI_API_KEY"):
        print(f"Loaded OPENAI_API_KEY from {env_path}")
    else:
        print(f".env exists at {env_path}, but OPENAI_API_KEY was not found")


SYSTEM_INSTRUCTIONS = """
You are an AI email triage assistant.

Analyze the email and return only valid JSON with this exact shape:
{
  "priority": "Low | Medium | High",
  "category": "short category name",
  "summary": "2 sentence summary",
  "deadlines": ["deadline 1", "deadline 2"],
  "action_items": ["action 1", "action 2"],
  "suggested_reply": "professional reply email"
}

Rules:
- Do not include markdown.
- Do not include extra text outside JSON.
- If no deadline exists, return an empty deadlines array.
- Action items must be practical and business-focused.
- Suggested reply must be concise and professional.
"""


def base64url_encode(value):
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("utf-8")


def base64url_decode(value):
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def get_jwt_secret():
    return os.getenv("JWT_SECRET", "dev-secret-change-me")


def create_jwt(username):
    now = int(time.time())
    header = {
        "alg": "HS256",
        "typ": "JWT",
    }
    payload = {
        "sub": username,
        "iat": now,
        "exp": now + TOKEN_TTL_SECONDS,
    }

    encoded_header = base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    encoded_payload = base64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    signature = hmac.new(get_jwt_secret().encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{encoded_header}.{encoded_payload}.{base64url_encode(signature)}"


def verify_jwt(token):
    try:
        encoded_header, encoded_payload, encoded_signature = token.split(".")
    except ValueError:
        raise ValueError("Invalid token format.")

    signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    expected_signature = hmac.new(get_jwt_secret().encode("utf-8"), signing_input, hashlib.sha256).digest()
    received_signature = base64url_decode(encoded_signature)

    if not hmac.compare_digest(expected_signature, received_signature):
        raise ValueError("Invalid token signature.")

    payload = json.loads(base64url_decode(encoded_payload))
    if int(time.time()) >= int(payload.get("exp", 0)):
        raise ValueError("Token expired. Please log in again.")

    return payload


def read_json_body(handler):
    content_length = int(handler.headers.get("Content-Length", 0))
    body = handler.rfile.read(content_length).decode("utf-8")
    return json.loads(body or "{}")


def get_bearer_token(headers):
    auth_header = headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise ValueError("Missing Authorization bearer token.")
    return auth_header.removeprefix("Bearer ").strip()


def get_bearer_token(headers):
    auth_header = headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise ValueError("Missing Authorization bearer token.")
    return auth_header.removeprefix("Bearer ").strip()


class EmailTriageHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/api/login":
            self.handle_login()
            return
            
        if self.path == "/api/register":
            self.handle_register()
            return

        if self.path == "/api/analyze":
            self.handle_analyze()
            return

        self.send_error(404, "Not found")

    def handle_login(self):
        try:
            payload = read_json_body(self)
            username = payload.get("username", "").strip()
            password = payload.get("password", "")
            
            users = get_users()
            hashed_password = hashlib.sha256(password.encode()).hexdigest()

            if username not in users or not hmac.compare_digest(users[username], hashed_password):
                self.send_json({"error": "Invalid username or password."}, status=401)
                return

            self.send_json({
                "token": create_jwt(username),
                "username": username,
                "expires_in": TOKEN_TTL_SECONDS,
            })
        except Exception as exc:
            self.send_json({"error": str(exc)}, status=500)

    def handle_register(self):
        try:
            payload = read_json_body(self)
            username = payload.get("username", "").strip()
            password = payload.get("password", "")

            if not username or not password:
                self.send_json({"error": "Username and password are required."}, status=400)
                return

            users = get_users()
            if username in users:
                self.send_json({"error": "Username already exists."}, status=400)
                return

            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            users[username] = hashed_password
            save_users(users)

            self.send_json({
                "token": create_jwt(username),
                "username": username,
                "expires_in": TOKEN_TTL_SECONDS,
            })
        except Exception as exc:
            self.send_json({"error": str(exc)}, status=500)

    def handle_analyze(self):
        try:
            token = get_bearer_token(self.headers)
            verify_jwt(token)
        except Exception as exc:
            self.send_json({"error": str(exc)}, status=401)
            return

        try:
            payload = read_json_body(self)
            email_text = payload.get("email", "").strip()
            if not email_text:
                raise ValueError("Email content is empty.")

            ai_model = get_ai_model()
            result = ai_model.analyze_email(email_text, SYSTEM_INSTRUCTIONS)
            self.send_json(result)
        except Exception as exc:
            self.send_json({"error": str(exc)}, status=500)

    def do_GET(self):
        if self.path == "/api/me":
            try:
                token = get_bearer_token(self.headers)
                payload = verify_jwt(token)
                self.send_json({"username": payload.get("sub"), "expires_at": payload.get("exp")})
            except Exception as exc:
                self.send_json({"error": str(exc)}, status=401)
            return

        return super().do_GET()

    def send_error(self, code, message=None, explain=None):
        if self.path.startswith("/api/"):
            self.send_json({"error": message or "Request failed."}, status=code)
            return
        super().send_error(code, message, explain)

    def send_json(self, payload, status=200):
        response_body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_body)))
        self.end_headers()
        self.wfile.write(response_body)

    def log_message(self, format, *args):
        if self.path.startswith("/api/"):
            return
        super().log_message(format, *args)


def main():
    load_env_file()
    print(f"Using model: {os.getenv('OPENAI_MODEL', 'gpt-4o-mini')}")
    print(f"Auth username: {os.getenv('AUTH_USERNAME', 'demo')}")
    server = ThreadingHTTPServer((HOST, PORT), EmailTriageHandler)
    print(f"AI Email Triage GPT running at http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop.")
    server.serve_forever()


if __name__ == "__main__":
    main()
