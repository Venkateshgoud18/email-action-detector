import os
import json
import urllib.request
import urllib.error

class AIModelWrapper:
    """Base class for AI model wrappers."""
    def analyze_email(self, email_text, system_instructions):
        raise NotImplementedError("Subclasses must implement analyze_email")

class OpenAIModel(AIModelWrapper):
    """OpenAI model wrapper."""
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def _extract_output_text(self, response_data):
        if response_data.get("output_text"):
            return response_data["output_text"]

        for item in response_data.get("output", []):
            if item.get("type") != "message":
                continue
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    return content.get("text", "")

        return ""

    def analyze_email(self, email_text, system_instructions):
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not set. Add it to .env and restart the server.")

        model_input = f"""
Return the analysis as JSON.

Email:
{email_text}
"""

        payload = {
            "model": self.model,
            "instructions": system_instructions,
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
                "Authorization": f"Bearer {self.api_key}",
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

        output_text = self._extract_output_text(response_data)
        if not output_text:
            raise RuntimeError("OpenAI returned no output text.")

        try:
            result = json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"OpenAI returned invalid JSON: {output_text}") from exc

        result["mode"] = "OpenAI GPT"
        result["model"] = self.model
        return result

def get_ai_model():
    """Factory function to get the configured AI model wrapper."""
    provider = os.getenv("AI_PROVIDER", "openai").lower().strip()
    if provider == "openai":
        return OpenAIModel()
    else:
        raise ValueError(f"Unknown AI_PROVIDER: {provider}")

if __name__ == "__main__":
    import sys
    # Helper to load .env when running standalone
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip() and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    
    print("Testing AI Model Wrapper...")
    try:
        ai_model = get_ai_model()
        test_email = "Hi IT, I cannot access my dashboard. Please grant access by 5PM today. Thanks, Bob."
        test_instructions = "Analyze the email and extract priority, category, summary, deadlines, action_items, and suggested_reply in JSON."
        print(f"Using Provider: {ai_model.__class__.__name__}")
        print("Sending request to AI model...")
        result = ai_model.analyze_email(test_email, test_instructions)
        print("Result:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error during test: {e}")
        sys.exit(1)
