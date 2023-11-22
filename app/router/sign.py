import uuid
from fastapi import APIRouter, HTTPException, status, Body
from handlers.db_handler import NoloUserDB
from handlers.tkn_handler import NoloToken
from models.iam_model import User

# Module specific Libraries


# Global Vars
MODULE_NAME = "signup"
MODULE_PREFIX = "/signup"
MODULE_TAGS = [MODULE_NAME]
MODULE_DESCRIPTION = ""

# FastAPI Instance
router = APIRouter(prefix=MODULE_PREFIX, tags=MODULE_TAGS)

# Handlers
user_db = NoloUserDB()
tkn = NoloToken()


# Models


# Environment


# Routes
@router.get("")
def index():
    return {
        "mesagge": f"Hello to module: {MODULE_NAME}",
        "module": MODULE_NAME,
    }, status.HTTP_200_OK


@router.get("/ping")
def ping():
    return {"message": "pong", "module": MODULE_NAME}, status.HTTP_200_OK


@router.post("", summary="Registering new users", status_code=status.HTTP_201_CREATED, response_model=User)
async def sign_up(
    username: str = Body(...), 
    password: str = Body(...),
    full_name: str = Body(...),
    email: str = Body(...)):

    # Exceptions


 

   

   # Get One User
    user = user_db.get_one_user(username=username)

    if user:
        return None


    new_user = {
        "username" : username,
        "email" : email,
        "full_name" : full_name,
        "hashed_password" : tkn.get_password_hash(password),
        "disabled" : False,
        "user_id" : f"{uuid.uuid4().hex}",
    }

    status = user_db.insert_user(new_user)

    if status is not 200:
        raise 

    return new_user