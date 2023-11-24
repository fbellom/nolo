from fastapi import APIRouter, HTTPException, status, Depends, Body
from handlers.tts_handler import NoloTTS
from handlers.dep_handler import get_current_active_user
from models.iam_model import User
import logging

# Create Logger
logger = logging.getLogger(__name__)


# Global Vars
MODULE_NAME = "tts"
MODULE_PREFIX = "/tts"
MODULE_TAGS = [MODULE_NAME]
MODULE_DESCRIPTION = ""

router = APIRouter(prefix=MODULE_PREFIX, tags=MODULE_TAGS)


# handler
polly = NoloTTS()

# Dependencies Injection

PROTECTED = Depends(get_current_active_user)


# Routes
@router.get("")
def index():
    return {"mesagge": "Hello World", "module": MODULE_NAME}


@router.get("/ping")
def ping():
    return {"message": "pong", "module": MODULE_NAME}


@router.post(
    "/create",
    summary="Convert Text To Speech",
    dependencies=[PROTECTED],
    status_code=status.HTTP_201_CREATED,
)
async def call_polly(
    text_to_transform: str = Body(...),
    doc_id: str = Body(...),
    filename: str = Body(...),
    page_id: str = Body(...),
    language: str = Body(...),
    gender: str = Body(...),
    user: User = Depends(get_current_active_user),
):
    tts_create_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="TTS Creation failed!",
    )

    new_tts_file = {
        "text": text_to_transform,
        "doc_id": doc_id,
        "page_id": page_id,
        "filename": filename,
        "user_id": user.username,
    }

    response = polly.convert_to_tts(new_tts_file)

    if not response:
        logger.error("Failed to convert to TTS")
        raise tts_create_exception

    return {}
