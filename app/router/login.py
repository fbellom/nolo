from fastapi import APIRouter, HTTPException, status, Body


# Module specific Libraries
from models.iam_model import UserLoginSchema, UserSchema

# Global Vars
MODULE_NAME = "login"
MODULE_PREFIX = "/login"
MODULE_TAGS = [MODULE_NAME]

# FastAPI Instance
router = APIRouter(prefix=MODULE_PREFIX, tags=MODULE_TAGS)

# Handlers


# Models


# Environment


# Routes
@router.get("/")
def index():
    return {
        "mesagge": f"Hello to module: {MODULE_NAME}",
        "module": MODULE_NAME,
    }, status.HTTP_200_OK


@router.get("/ping")
def ping():
    return {"message": "pong", "module": MODULE_NAME}, status.HTTP_200_OK
