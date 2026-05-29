import json
import logging
import os

from google import genai
from google.genai import types
from dotenv import load_dotenv
from fastapi import HTTPException
from pathlib import Path

# ── Logging ────────────────────────────────────────────────────────────────────
logger = logging.getLogger(__name__)

# ── Environment ────────────────────────────────────────────────────────────────
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY is not set. Copy .env.example → .env and add your key."
    )

client = genai.Client(api_key=api_key)


# ── System prompt (kept separate from user content to reduce prompt injection) ─
SYSTEM_PROMPT = """
You are a Quran app voice command classifier.
The user speaks Arabic or English. Classify their intent and return ONLY valid JSON.

Known surah names → numbers (all 114):
al-fatiha=1, al-baqara=2, al-imran=3, an-nisa=4, al-maida=5,
al-anam=6, al-araf=7, al-anfal=8, at-tawba=9, yunus=10,
hud=11, yusuf=12, ar-rad=13, ibrahim=14, al-hijr=15,
an-nahl=16, al-isra=17, al-kahf=18, maryam=19, ta-ha=20,
al-anbiya=21, al-hajj=22, al-muminun=23, an-nur=24, al-furqan=25,
ash-shuara=26, an-naml=27, al-qasas=28, al-ankabut=29, ar-rum=30,
luqman=31, as-sajda=32, al-ahzab=33, saba=34, fatir=35,
ya-sin=36, as-saffat=37, sad=38, az-zumar=39, ghafir=40,
fussilat=41, ash-shura=42, az-zukhruf=43, ad-dukhan=44, al-jathiya=45,
al-ahqaf=46, muhammad=47, al-fath=48, al-hujurat=49, qaf=50,
adh-dhariyat=51, at-tur=52, an-najm=53, al-qamar=54, ar-rahman=55,
al-waqia=56, al-hadid=57, al-mujadila=58, al-hashr=59, al-mumtahana=60,
as-saf=61, al-jumuah=62, al-munafiqun=63, at-taghabun=64, at-talaq=65,
at-tahrim=66, al-mulk=67, al-qalam=68, al-haqqah=69, al-maarij=70,
nuh=71, al-jinn=72, al-muzzammil=73, al-muddaththir=74, al-qiyamah=75,
al-insan=76, al-mursalat=77, an-naba=78, an-naziat=79, abasa=80,
at-takwir=81, al-infitar=82, al-mutaffifin=83, al-inshiqaq=84, al-buruj=85,
at-tariq=86, al-ala=87, al-ghashiyah=88, al-fajr=89, al-balad=90,
ash-shams=91, al-layl=92, ad-duha=93, ash-sharh=94, at-tin=95,
al-alaq=96, al-qadr=97, al-bayyinah=98, az-zalzalah=99, al-adiyat=100,
al-qariah=101, at-takathur=102, al-asr=103, al-humazah=104, al-fil=105,
quraysh=106, al-maun=107, al-kawthar=108, al-kafirun=109, an-nasr=110,
al-masad=111, al-ikhlas=112, al-falaq=113, an-nas=114

Arabic equivalents are also accepted (e.g. الفاتحة=1, البقرة=2, آل عمران=3, etc.)
Fuzzy matching is expected: "baqarah", "al baqara", "البقرة" all resolve to 2.

Known reciters:
AbdelBaset=1, Mishary=2, Maher=3, Sudais=4, Husary=5

Response schema (return ONLY this JSON, no explanation, no markdown):
{
  "status": bool,
  "action": str | null,
  "parameters": dict,
  "confidence": float (0.0 to 1.0),
  "detected_language": "ar" | "en"
}

Available actions:
- "audio_surah"    → parameters: { "surah_number": int }
- "audio_verse"    → parameters: { "surah_number": int, "verse_number": int }
- "audio_range"    → parameters: { "surah_number": int, "start_verse": int, "end_verse": int }
- "navigation"     → parameters: { "page": int } OR { "surah_number": int }
- "switch_theme"   → parameters: { "mode": "light" | "dark" }
- "switch_reciter" → parameters: { "reciter_id": int }
- "repeat_verse"   → parameters: { "count": int }
- "bookmark_verse" → parameters: { "surah_number": int, "verse_number": int }

If the command does not match any action:
{ "status": false, "action": null, "parameters": {}, "confidence": 0.0, "detected_language": "en" }
"""

_FALLBACK = {
    "status": False,
    "action": None,
    "parameters": {},
    "confidence": 0.0,
    "detected_language": "en",
}

MODEL_NAME = "gemini-2.5-flash"

_CONFIG = types.GenerateContentConfig(
    system_instruction=SYSTEM_PROMPT,
    response_mime_type="application/json",
)


async def parse_command(text: str) -> dict:
    try:
        # User content is passed separately from the system prompt to reduce
        # prompt-injection risk. The model receives the system instruction via
        # system_instruction, and only the user's command as the message body.
        response = await client.aio.models.generate_content(
            model=MODEL_NAME,
            contents=f"User command: {text}",
            config=_CONFIG,
        )

        clean_text = response.text.strip()
        result = json.loads(clean_text)
        result["original_text"] = text
        logger.info("Parsed command | action=%s lang=%s text=%r",
                    result.get("action"), result.get("detected_language"), text)
        return result

    except json.JSONDecodeError:
        logger.warning("Gemini returned non-JSON response: %r", response.text[:200])
        return {**_FALLBACK, "original_text": text}

    except Exception as e:
        logger.error("Gemini API error (%s): %s", type(e).__name__, e)
        raise HTTPException(status_code=503, detail=f"AI service error: {type(e).__name__}: {e}")
