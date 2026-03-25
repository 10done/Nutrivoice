# NutriVoice

Voice-first nutrition logging: **FastAPI** backend (JWT auth, meal logs, analytics), **vanilla HTML/JS** frontend (Tailwind CDN). **Speech-to-text** uses the **[SpeechRecognition](https://pypi.org/project/SpeechRecognition/)** library (Google Web Speech API). **Meal parsing** uses the **Groq** chat API (Llama, etc.) when `MOCK_AI=false`. With `MOCK_AI=true` / `MOCK_WHISPER=true`, tests and offline dev need no external APIs.

## Requirements

- **Python 3.13** (recommended; 3.14 may lack wheels for some dependencies)
- **ffmpeg** for decoding browser **WebM/MP4** to WAV. Either install on PATH (`brew install ffmpeg`) or rely on **`imageio-ffmpeg`** (pulled in by `pip install -r requirements.txt`), which bundles a binary and is used when `ffmpeg` is not found.
- Modern browser (HTTPS or `localhost` for microphone)

## Quick start

```bash
cd backend
python3.13 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env     # set GROQ_API_KEY for real LLM parsing; ffmpeg for voice
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open [http://127.0.0.1:8000/login.html](http://127.0.0.1:8000/login.html), register, then use **Home**, **Log**, **Insights**, and **Settings**.

- **API:** `http://127.0.0.1:8000/api/health`
- **Docs:** `http://127.0.0.1:8000/docs`

## Tests

```bash
cd backend
source .venv/bin/activate
pytest -q
```

Tests use an in-memory SQLite database, `MOCK_AI=true`, `MOCK_WHISPER=true`, and no network calls.

## Environment

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | SQLAlchemy URL (default SQLite file `./nutrivoice.db`) |
| `JWT_SECRET` | Signing key for access tokens |
| `GROQ_API_KEY` | **Groq** API key for transcript → structured meal JSON (`MOCK_AI=false`) |
| `GROQ_MODEL` | Groq model id (default `llama-3.3-70b-versatile`) |
| `SPEECH_RECOGNITION_LANGUAGE` | Passed to Google STT (default `en-US`) |
| `MOCK_WHISPER` | `true`: skip STT; use `MOCK_WHISPER_TEXT` |
| `MOCK_AI` | `true`: skip Groq; use built-in food table parser |

Voice pipeline: **upload audio** → **ffmpeg** (stdin → 16 kHz mono WAV, no ffprobe) → **SpeechRecognition** (Google) → **text** → **Groq** chat (JSON meal) → save.

## PostgreSQL (optional)

```bash
docker compose up -d
```

Set `DATABASE_URL=postgresql+psycopg://nutrivoice:nutrivoice@localhost:5432/nutrivoice` and `pip install psycopg[binary]` (add to your environment as needed).

## Project layout

- `backend/app` — FastAPI app, models, services (`agent_service`, `speech_transcription`, `nutrition_tools`)
- `web/` — Static UI (`index.html`, `log.html`, `insights.html`, `settings.html`, `login.html`, `js/`)

The meal “agent” in `agent_service.py` calls **Groq** for JSON extraction when `GROQ_API_KEY` is set and `MOCK_AI=false`; otherwise it uses the rule-based parser and `nutrition_tools`.
# Nutrivoice
