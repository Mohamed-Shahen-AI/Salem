from fastapi import FastAPI, HTTPException
from app.models.schemas import CommandRequest, CommandResponse
from app.services.intent_parser import parse_command

app = FastAPI(
    title="Quran Voice Command API",
    description="Parses Arabic/English voice commands into structured Quran app actions using Gemini 3.5 Flash.",
    version="1.0.0",
)


@app.post("/api/command", response_model=CommandResponse)
async def command(req: CommandRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text field cannot be empty")

    result = await parse_command(req.text)
    return result


@app.get("/health")
async def health():
    return {"status": "ok"}
