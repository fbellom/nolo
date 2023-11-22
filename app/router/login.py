from fastapi import APIRouter, HTTPException, status, Body


# Module specific Libraries


# Global Vars
MODULE_NAME = "login"
MODULE_PREFIX = "/login"
MODULE_TAGS = [MODULE_NAME]
MODULE_DESCRIPTION = ""

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
