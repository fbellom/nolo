import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Body
from handlers.db_handler import NoloUserDB
from handlers.tkn_handler import NoloToken
from handlers.ral_handler import NoloRateLimit
from models.iam_model import User
import logging

# Create Logger
logger = logging.getLogger(__name__)

# Module specific Libraries


# Global Vars
MODULE_NAME = "signup"
MODULE_PREFIX = "/signup"
MODULE_TAGS = [MODULE_NAME]
MODULE_DESCRIPTION = ""
MAX_CALLS_ALLOWED_PER_MIN=5
MAX_TIME_WAIT_429_IN_SECS=60
MAX_PENALTY_TIME_429_IN_SECS=600

# FastAPI Instance
router = APIRouter(prefix=MODULE_PREFIX, tags=MODULE_TAGS)

# Handlers
user_db = NoloUserDB()
tkn = NoloToken()


# Models


# Environment

# Rate Limit 5 calls in 60 seconds
rate_limit = NoloRateLimit(MAX_CALLS_ALLOWED_PER_MIN, 
                           MAX_TIME_WAIT_429_IN_SECS, 
                           MAX_PENALTY_TIME_429_IN_SECS)

RATE_LIMIT = Depends(rate_limit)

# Routes
@router.get("", dependencies=[RATE_LIMIT])
def index():
    return {
        "mesagge": f"Hello to module: {MODULE_NAME}",
        "module": MODULE_NAME,
    }

@router.get("/ping", dependencies=[RATE_LIMIT])
def ping():
    return {"message": "pong", "module": MODULE_NAME}


@router.post(
    "",
    summary="Registering new users",
    status_code=status.HTTP_201_CREATED,
    response_model=User,
    dependencies=[RATE_LIMIT]
)
async def sign_up(
    username: str = Body(...),
    password: str = Body(...),
    full_name: str = Body(...),
    email: str = Body(...),
):
    # Exceptions

    # Get One User
    user = user_db.get_one_user(username=username)

    if user:
        return None

    new_user = {
        "username": username,
        "email": email,
        "full_name": full_name,
        "hashed_password": tkn.get_password_hash(password),
        "disabled": True,
        "user_id": f"{uuid.uuid4().hex}",
    }

    status = user_db.insert_user(new_user)

    if status != 200:
        raise

    return new_user
