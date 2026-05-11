# AI Email Triage GPT

A mini AI workflow automation project that turns an email into:

- priority
- category
- summary
- deadlines
- action items
- suggested reply

The frontend is plain HTML/CSS/JavaScript. The backend is plain Python and calls OpenAI `gpt-4o-mini`.

## Important Security Note

Never commit your real API key to GitHub. Keep it only in `.env`.

If you pasted a key into chat or shared it anywhere, revoke it and create a new one.

## Setup

Create a local `.env` file:

```bash
cp .env.example .env
```

Open `.env` and add your new API key:

```text
OPENAI_API_KEY=your_new_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

## Run

```bash
python3 server.py
```

Open:

```text
http://localhost:8001
```

Paste any email and click **Analyze Email**.

## How It Works

```text
Browser form
→ POST /api/analyze
→ Python server
→ OpenAI gpt-4o-mini
→ JSON response
→ Browser result cards
```
