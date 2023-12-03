import os
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from handlers.ral_handler import NoloRateLimit

# Module specific Libraries
from models.iam_model import User, UserInDB
from models.jwt_model import Token, TokenData
from handlers.tkn_handler import NoloToken
from handlers.db_handler import NoloDBHandler, NoloUserDB
from handlers.dep_handler import get_current_active_user
import logging

# Create Logger
logger = logging.getLogger(__name__)

# Global Vars
MODULE_NAME = "token"
MODULE_PREFIX = "/token"
MODULE_TAGS = [MODULE_NAME]
MODULE_SUMMARY = "Create access and refresh tokens for users"
MAX_CALLS_ALLOWED_PER_MIN=10
MAX_TIME_WAIT_429_IN_SECS=60
MAX_PENALTY_TIME_429_IN_SECS=300

# FastAPI Instance
router = APIRouter(prefix=MODULE_PREFIX, tags=MODULE_TAGS)


# Models

# Rate Limit 10 calls in 60 seconds
rate_limit = NoloRateLimit(MAX_CALLS_ALLOWED_PER_MIN, 
                           MAX_TIME_WAIT_429_IN_SECS, 
                           MAX_PENALTY_TIME_429_IN_SECS)

# Handlers
iam = NoloToken()
user_db = NoloUserDB()

# Environment

# Depends
PROTECTED = Depends(get_current_active_user)
RATE_LIMIT = Depends(rate_limit)


# Utilities Function
def authenticate_user(username: str, password: str):
    user = user_db.get_one_user(username)
    if not user:
        return False
    if not iam.verify_password(password, user.hashed_password):
        return False
    return user


# Routes
@router.post("", summary=MODULE_SUMMARY, response_model=Token, dependencies=[RATE_LIMIT])
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = iam.create_access_token(data={"sub": user.username})
    refresh_token = iam.create_refresh_token(data={"sub": user.username})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
    }

@router.post("/refresh", summary=MODULE_SUMMARY, response_model=Token, dependencies=[RATE_LIMIT])
async def get_refresh_token(current_user: Annotated[User, Depends(get_current_active_user)]):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = iam.create_access_token(data={"sub": current_user.username})
    refresh_token = iam.create_refresh_token(data={"sub": current_user.username})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
    }


@router.get("/me", summary="Get details of current logged in user", response_model=User, dependencies=[RATE_LIMIT])
async def get_me(current_user: Annotated[User, Depends(get_current_active_user)]):
    return current_user
