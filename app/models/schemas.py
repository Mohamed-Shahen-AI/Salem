import re
import unicodedata
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class CommandRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        max_length=500,
        strip_whitespace=True,
        description="Voice command text in Arabic or English",
    )

    @field_validator("text")
    @classmethod
    def must_be_readable_text(cls, v: str) -> str:
        # Reject non-printable / control characters (except normal whitespace)
        for ch in v:
            cat = unicodedata.category(ch)
            if cat.startswith("C") and ch not in ("\n", "\r", "\t"):
                raise ValueError("Input contains non-printable characters and is not valid text")

        # Must contain at least one alphabetic letter (Latin, Arabic, or any Unicode script)
        if not any(unicodedata.category(ch).startswith("L") for ch in v):
            raise ValueError(
                "Input must contain at least one letter. "
                "Numbers, symbols, or empty strings are not valid voice commands."
            )
        return v


# Allowed Gemini action values — anything outside this is rejected
ValidAction = Literal[
    "audio_surah",
    "audio_verse",
    "audio_range",
    "navigation",
    "switch_theme",
    "switch_reciter",
    "repeat_verse",
    "bookmark_verse",
]


class CommandResponse(BaseModel):
    status: bool
    action: Optional[ValidAction] = None
    parameters: dict[str, Any] = {}
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    detected_language: Literal["ar", "en"] = "en"
    original_text: str = ""
