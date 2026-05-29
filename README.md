# Quran Voice Command API (Salem)

A FastAPI service that parses Arabic and English voice commands into structured Quran app actions using **Gemini 1.5 Flash**.

---

## Stack

| Layer | Tool |
|-------|------|
| Framework | FastAPI |
| LLM | Google `gemini-1.5-flash` |
| Server | Uvicorn (ASGI) |
| Env vars | python-dotenv |
| Validation | Pydantic v2 |
| Rate limiting | slowapi |

---

## Project Structure

```
Salem/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app + routes + middleware
│   ├── services/
│   │   ├── __init__.py
│   │   └── intent_parser.py     # Gemini call + system prompt
│   └── models/
│       ├── __init__.py
│       └── schemas.py           # Pydantic request/response models
├── .env                         # Environment variables (create from .env.example)
├── .env.example                 # Example environment variables file
├── requirements.txt
└── README.md
```

---

## Setup

```bash
# 1. Create a virtual environment
python3 -m venv .venv

# 2. Install dependencies
.venv/bin/pip install -r requirements.txt

# 3. Add your Gemini key to .env
cp .env.example .env
# Edit .env and replace your_gemini_api_key_here with your actual key

# 4. Run the dev server
.venv/bin/uvicorn app.main:app --reload --port 3000
```

Interactive Swagger UI → **http://localhost:3000/docs**

---

## Endpoint

### `POST /api/command`

**Request:**
```json
{ "text": "play verses 1 to 7 from surah al fatiha" }
```

**Response:**
```json
{
  "status": true,
  "action": "audio_range",
  "parameters": {
    "surah_number": 1,
    "start_verse": 1,
    "end_verse": 7
  },
  "confidence": 1.0,
  "detected_language": "en",
  "original_text": "play verses 1 to 7 from surah al fatiha"
}
```

### `GET /health`
Returns `{ "status": "ok" }`.

---

## Supported Actions

| Action | Parameters |
|--------|-----------|
| `audio_surah` | `surah_number` |
| `audio_verse` | `surah_number`, `verse_number` |
| `audio_range` | `surah_number`, `start_verse`, `end_verse` |
| `navigation` | `page` OR `surah_number` |
| `switch_theme` | `mode` (`"light"` \| `"dark"`) |
| `switch_reciter` | `reciter_id` |
| `repeat_verse` | `count` |
| `bookmark_verse` | `surah_number`, `verse_number` |

---

## Supported Reciters

| ID | Name |
|----|------|
| 1 | AbdelBaset |
| 2 | Mishary |
| 3 | Maher |
| 4 | Sudais |
| 5 | Husary |

---

## Arabic Command Examples

| Input | Resolved action |
|-------|----------------|
| `اقرأ سورة البقرة` | `audio_surah` → surah 2 |
| `انتقل إلى صفحة 50` | `navigation` → page 50 |
| `غيّر القارئ إلى مشاري` | `switch_reciter` → reciter_id 2 |
| `الوضع الداكن` | `switch_theme` → dark |

---

## Security & Validation

| Layer | What is enforced |
|-------|-----------------|
| **Input length** | `text` must be 1–500 characters |
| **Text content check** | Input must contain at least one letter (Latin, Arabic, or any Unicode script). Rejects digits-only, symbols-only, and binary/non-printable characters |
| **Rate limiting** | 30 requests/min per IP on `POST /api/command`; 60 requests/min globally |
| **CORS** | Only allowed origins can call the API from a browser (configure `allow_origins` in `main.py` before deploying to production) |
| **Output validation** | `action` is constrained to known values; `confidence` must be 0.0–1.0; `detected_language` must be `"ar"` or `"en"` |
| **Prompt injection mitigation** | User content is passed separately from the system prompt in the Gemini API call |
| **Error handling** | JSON decode errors return a graceful fallback; Gemini API failures return `503`; unhandled exceptions return `500` without leaking stack traces |
| **Startup guard** | Server refuses to start if `GEMINI_API_KEY` is missing or empty |
| **Logging** | All requests and errors are logged with timestamp, level, IP, and action |
