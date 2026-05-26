from pydantic import BaseModel
from typing import Any, Optional


class CommandRequest(BaseModel):
    text: str


class CommandResponse(BaseModel):
    status: bool
    action: Optional[str] = None
    parameters: dict[str, Any] = {}
    confidence: float = 0.0
    detected_language: str = "en"
    original_text: str = ""
