# Quran Voice Command API (Salem)

A FastAPI service that parses Arabic and English voice commands into structured Quran app actions using **Gemini 3.5 Flash**.

---

## Stack

| Layer | Tool |
|-------|------|
| Framework | FastAPI |
| LLM | Google `gemini-3.5-flash` |
| Server | Uvicorn (ASGI) |
| Env vars | python-dotenv |
| Validation | Pydantic v2 |

---

## Project Structure

```
Salem/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app + routes
│   ├── services/
│   │   ├── __init__.py
│   │   └── intent_parser.py     # Gemini call + system prompt
│   └── models/
│       ├── __init__.py
│       └── schemas.py           # Pydantic request/response models
├── .env                         # GEMINI_API_KEY goes here
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
echo "GEMINI_API_KEY=AIzaSy..." > .env

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
