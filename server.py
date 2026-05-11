import json
import os
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
HOST = "127.0.0.1"
PORT = 8001


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


def extract_output_text(response_data):
    if response_data.get("output_text"):
        return response_data["output_text"]

    for item in response_data.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                return content.get("text", "")

    return ""


def analyze_with_openai(email_text):
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to .env and restart the server.")

    model_input = f"""
Return the analysis as JSON.

Email:
{email_text}
"""

    payload = {
        "model": model,
        "instructions": SYSTEM_INSTRUCTIONS,
        "input": model_input,
        "text": {
            "format": {
                "type": "json_object"
            }
        },
    }

    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            response_data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI API error {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error while calling OpenAI: {exc}") from exc

    output_text = extract_output_text(response_data)
    if not output_text:
        raise RuntimeError("OpenAI returned no output text.")

    try:
        result = json.loads(output_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"OpenAI returned invalid JSON: {output_text}") from exc

    result["mode"] = "OpenAI GPT"
    result["model"] = model
    return result


class EmailTriageHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/api/analyze":
            self.send_error(404, "Not found")
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")

        try:
            payload = json.loads(body)
            email_text = payload.get("email", "").strip()
            if not email_text:
                raise ValueError("Email content is empty.")

            result = analyze_with_openai(email_text)
            self.send_json(result)
        except Exception as exc:
            self.send_json({"error": str(exc)}, status=500)

    def send_json(self, payload, status=200):
        response_body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_body)))
        self.end_headers()
        self.wfile.write(response_body)


def main():
    load_env_file()
    print(f"Using model: {os.getenv('OPENAI_MODEL', 'gpt-4o-mini')}")
    server = ThreadingHTTPServer((HOST, PORT), EmailTriageHandler)
    print(f"AI Email Triage GPT running at http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop.")
    server.serve_forever()


if __name__ == "__main__":
    main()
